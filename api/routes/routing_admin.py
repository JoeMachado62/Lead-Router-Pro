# api/routes/routing_admin.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
import requests
import json
from database.simple_connection import db
from api.services.lead_routing_service import lead_routing_service
from api.services.ghl_api import GoHighLevelAPI
from config import AppConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/routing", tags=["Lead Routing Administration"])

class RoutingConfigRequest(BaseModel):
    performance_percentage: int

class VendorMatchingRequest(BaseModel):
    zip_code: str
    service_category: str
    specific_service: Optional[str] = None  # NEW: Support for specific service testing

@router.get("/configuration")
async def get_routing_configuration():
    """Get current lead routing configuration"""
    try:
        # Get the default account for this GHL location
        account = db.get_account_by_ghl_location_id(AppConfig.GHL_LOCATION_ID)
        if not account:
            # Create default account if none exists
            account_id = db.create_account(
                company_name="Digital Marine LLC",
                industry="marine",
                ghl_location_id=AppConfig.GHL_LOCATION_ID,
                ghl_private_token=AppConfig.GHL_PRIVATE_TOKEN
            )
        else:
            account_id = account["id"]
        
        # Get routing statistics
        routing_stats = lead_routing_service.get_routing_stats(account_id)
        
        return {
            "status": "success",
            "data": routing_stats,
            "account_id": account_id,
            "message": "Routing configuration retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting routing configuration: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve routing configuration")

@router.post("/configuration")
async def update_routing_configuration(request: RoutingConfigRequest):
    """Update lead routing configuration"""
    try:
        performance_percentage = request.performance_percentage
        
        # Validate percentage
        if not 0 <= performance_percentage <= 100:
            raise HTTPException(status_code=400, detail="Performance percentage must be between 0 and 100")
        
        # Get the default account for this GHL location
        account = db.get_account_by_ghl_location_id(AppConfig.GHL_LOCATION_ID)
        if not account:
            # Create default account if none exists
            account_id = db.create_account(
                company_name="Digital Marine LLC",
                industry="marine",
                ghl_location_id=AppConfig.GHL_LOCATION_ID,
                ghl_private_token=AppConfig.GHL_PRIVATE_TOKEN
            )
        else:
            account_id = account["id"]
        
        # Update routing configuration
        success = lead_routing_service.update_routing_configuration(account_id, performance_percentage)
        
        if success:
            # Get updated stats
            routing_stats = lead_routing_service.get_routing_stats(account_id)
            
            return {
                "status": "success",
                "data": routing_stats,
                "message": f"Routing configuration updated: {performance_percentage}% performance-based, {100 - performance_percentage}% round-robin"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update routing configuration")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating routing configuration: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update routing configuration")

@router.get("/vendors")
async def get_routing_vendors():
    """Get vendors with routing information"""
    try:
        # Get the default account for this GHL location
        account = db.get_account_by_ghl_location_id(AppConfig.GHL_LOCATION_ID)
        if not account:
            return {
                "status": "success",
                "data": [],
                "message": "No account found - no vendors available"
            }
        
        account_id = account["id"]
        vendors = db.get_vendors(account_id)
        
        # Add routing-specific information
        for vendor in vendors:
            vendor['coverage_summary'] = _get_coverage_summary(vendor)
            vendor['routing_eligible'] = (
                vendor.get('status') == 'active' and 
                vendor.get('taking_new_work', False)
            )
        
        return {
            "status": "success",
            "data": vendors,
            "count": len(vendors),
            "message": "Vendors retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting routing vendors: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve vendors")

@router.post("/vendors/{vendor_id}/coverage")
async def update_vendor_coverage(vendor_id: str, coverage_data: Dict[str, Any]):
    """Update vendor coverage configuration"""
    try:
        # Validate coverage data
        coverage_type = coverage_data.get('service_coverage_type', 'zip')
        if coverage_type not in ['global', 'national', 'state', 'county', 'zip']:
            raise HTTPException(status_code=400, detail="Invalid coverage type")
        
        # Update vendor in database
        conn = db._get_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE vendors 
            SET service_coverage_type = ?, 
                service_states = ?, 
                service_counties = ?, 
                service_areas = ?,
                updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (
            coverage_type,
            str(coverage_data.get('service_states', [])),
            str(coverage_data.get('service_counties', [])),
            str(coverage_data.get('service_areas', [])),
            vendor_id
        ))
        
        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="Vendor not found")
        
        conn.commit()
        conn.close()
        
        return {
            "status": "success",
            "message": f"Vendor coverage updated to {coverage_type}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating vendor coverage: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update vendor coverage")

@router.post("/test-matching")
async def test_vendor_matching(request: VendorMatchingRequest):
    """Test vendor matching for a specific location and service"""
    try:
        zip_code = request.zip_code
        service_category = request.service_category
        
        # Get the default account for this GHL location
        account = db.get_account_by_ghl_location_id(AppConfig.GHL_LOCATION_ID)
        if not account:
            return {
                "status": "success",
                "data": {
                    "matching_vendors": [],
                    "selected_vendor": None,
                    "message": "No account found - no vendors available"
                }
            }
        
        account_id = account["id"]
        
        # NEW: Extract specific service parameter for enhanced testing
        specific_service = request.specific_service
        
        # Validate service category and specific service against service hierarchy
        from api.services.service_categories import service_manager
        
        if not service_manager.is_valid_category(service_category):
            return {
                "status": "error",
                "message": f"Invalid service category: {service_category}",
                "available_categories": service_manager.get_all_categories()
            }
        
        # If specific service is provided, validate it
        if specific_service and not service_manager.is_service_in_category(specific_service, service_category):
            return {
                "status": "error", 
                "message": f"Service '{specific_service}' not found in category '{service_category}'",
                "available_services": service_manager.get_services_for_category(service_category)
            }
        
        # Find matching vendors using enhanced multi-level routing
        matching_vendors = lead_routing_service.find_matching_vendors(
            account_id=account_id,
            service_category=service_category,
            zip_code=zip_code,
            specific_service=specific_service  # NEW: Pass specific service for exact matching
        )
        
        # Select vendor using routing logic
        selected_vendor = None
        if matching_vendors:
            selected_vendor = lead_routing_service.select_vendor_from_pool(
                matching_vendors, account_id
            )
        
        # Enhanced response with routing details
        routing_method = "exact_service_match" if specific_service else "category_match"
        
        return {
            "status": "success",
            "data": {
                "zip_code": zip_code,
                "service_category": service_category,
                "specific_service": specific_service,
                "routing_method": routing_method,
                "matching_vendors": matching_vendors,
                "selected_vendor": selected_vendor,
                "match_count": len(matching_vendors)
            },
            "message": f"Found {len(matching_vendors)} matching vendors for {service_category}" + 
                      (f" -> {specific_service}" if specific_service else "") + f" in {zip_code}"
        }
        
    except Exception as e:
        logger.error(f"Error testing vendor matching: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to test vendor matching")

@router.post("/process-unassigned-leads")
async def process_unassigned_leads():
    """
    Enhanced feature: Pull unassigned leads from GoHighLevel and attempt to assign them to vendors
    This replaces the simple test matching with a more useful bulk assignment feature
    """
    try:
        # Get the default account for this GHL location
        account = db.get_account_by_ghl_location_id(AppConfig.GHL_LOCATION_ID)
        if not account:
            return {
                "status": "error",
                "message": "No account found - cannot process leads"
            }
        
        account_id = account["id"]
        
        # Step 1: Get unassigned leads from GoHighLevel
        unassigned_ghl_leads = await _get_unassigned_leads_from_ghl()
        
        if not unassigned_ghl_leads:
            return {
                "status": "success",
                "data": {
                    "processed_leads": 0,
                    "successful_assignments": 0,
                    "failed_assignments": 0,
                    "leads": []
                },
                "message": "No unassigned leads found in GoHighLevel"
            }
        
        # Step 2: Process each unassigned lead
        processed_leads = []
        successful_assignments = 0
        failed_assignments = 0
        
        for ghl_lead in unassigned_ghl_leads:
            lead_result = await _process_single_unassigned_lead(ghl_lead, account_id)
            processed_leads.append(lead_result)
            
            if lead_result["assignment_successful"]:
                successful_assignments += 1
            else:
                failed_assignments += 1
        
        return {
            "status": "success",
            "data": {
                "processed_leads": len(processed_leads),
                "successful_assignments": successful_assignments,
                "failed_assignments": failed_assignments,
                "leads": processed_leads
            },
            "message": f"Processed {len(processed_leads)} unassigned leads: {successful_assignments} assigned, {failed_assignments} failed"
        }
        
    except Exception as e:
        logger.error(f"Error processing unassigned leads: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process unassigned leads")

async def _get_unassigned_leads_from_ghl() -> List[Dict[str, Any]]:
    """
    Fetch unassigned leads from GoHighLevel API
    Returns leads that don't have a vendor assigned in the assignedTo field
    """
    try:
        # Initialize GHL API client
        ghl_api = GoHighLevelAPI(
            location_api_key=AppConfig.GHL_LOCATION_API,
            private_token=AppConfig.GHL_PRIVATE_TOKEN,
            location_id=AppConfig.GHL_LOCATION_ID,
            agency_api_key=AppConfig.GHL_AGENCY_API_KEY,
            company_id=AppConfig.GHL_COMPANY_ID
        )
        
        # Get contacts from GHL that are leads but don't have assigned vendors
        contacts = ghl_api.search_contacts(query="lead", limit=100)
        
        # Filter for unassigned leads (no assignedTo or assignedTo is empty)
        unassigned_leads = []
        for contact in contacts:
            # Check if this contact is a lead and doesn't have an assigned vendor
            assigned_to = contact.get('assignedTo')
            tags = contact.get('tags', [])
            
            # Consider it a lead if it has lead-related tags or is in a lead pipeline
            is_lead = any(tag.lower() in ['lead', 'new lead', 'unassigned'] for tag in tags)
            
            if is_lead and not assigned_to:
                # Extract relevant information for processing
                lead_info = {
                    'ghl_contact_id': contact.get('id'),
                    'name': f"{contact.get('firstName', '')} {contact.get('lastName', '')}".strip(),
                    'email': contact.get('email'),
                    'phone': contact.get('phone'),
                    'address': contact.get('address1'),
                    'city': contact.get('city'),
                    'state': contact.get('state'),
                    'postal_code': contact.get('postalCode'),
                    'tags': tags,
                    'custom_fields': contact.get('customFields', {}),
                    'source': contact.get('source', 'GoHighLevel'),
                    'created_at': contact.get('dateAdded')
                }
                unassigned_leads.append(lead_info)
        
        logger.info(f"Found {len(unassigned_leads)} unassigned leads in GoHighLevel")
        return unassigned_leads
        
    except Exception as e:
        logger.error(f"Error fetching unassigned leads from GHL: {e}")
        return []

async def _process_single_unassigned_lead(ghl_lead: Dict[str, Any], account_id: str) -> Dict[str, Any]:
    """
    Process a single unassigned lead and attempt to assign it to a vendor
    COUNTY-BASED ARCHITECTURE: Now properly converts ZIP → County and uses county-based matching
    """
    lead_result = {
        "ghl_contact_id": ghl_lead.get('ghl_contact_id'),
        "customer_name": ghl_lead.get('name'),
        "assignment_successful": False,
        "assigned_vendor": None,
        "matching_vendors_count": 0,
        "error_message": None,
        "service_category": None,
        "zip_code": None,
        "county": None,
        "state": None,
        "ghl_opportunity_id": None
    }
    
    try:
        # Extract service category from tags or custom fields
        service_category = _extract_service_category(ghl_lead)
        lead_result["service_category"] = service_category
        
        # ENHANCED DEBUG: Extract ZIP code from multiple sources (custom fields first, then standard fields)
        zip_code = _extract_location_data(ghl_lead)
        lead_result["zip_code"] = zip_code
        
        # DEBUG: Log the actual lead data structure for debugging
        logger.info(f"🔍 DEBUG - Lead data structure for {ghl_lead.get('ghl_contact_id')}:")
        logger.info(f"   Standard fields: {list(ghl_lead.keys())}")
        logger.info(f"   postal_code: {ghl_lead.get('postal_code')}")
        logger.info(f"   postalCode: {ghl_lead.get('postalCode')}")
        logger.info(f"   address: {ghl_lead.get('address')}")
        logger.info(f"   custom_fields type: {type(ghl_lead.get('custom_fields'))}")
        if isinstance(ghl_lead.get('custom_fields'), list):
            logger.info(f"   custom_fields sample: {ghl_lead.get('custom_fields')[:2] if ghl_lead.get('custom_fields') else 'empty'}")
        elif isinstance(ghl_lead.get('custom_fields'), dict):
            logger.info(f"   custom_fields keys: {list(ghl_lead.get('custom_fields').keys())}")
        
        if not service_category:
            lead_result["error_message"] = "Could not determine service category"
            return lead_result
        
        if not zip_code:
            lead_result["error_message"] = "Could not determine service location"
            return lead_result
        
        # CRITICAL: Convert ZIP → County using LocationService (ALIGN WITH ARCHITECTURE)
        from api.services.location_service import location_service
        location_data = location_service.zip_to_location(zip_code)
        
        if location_data.get('error'):
            lead_result["error_message"] = f"Could not resolve ZIP {zip_code} to county: {location_data['error']}"
            logger.warning(f"⚠️ Location resolution failed for ZIP {zip_code}: {location_data['error']}")
            return lead_result
        
        county = location_data.get('county')
        state = location_data.get('state')
        lead_result["county"] = county
        lead_result["state"] = state
        
        if not county or not state:
            lead_result["error_message"] = f"ZIP {zip_code} did not resolve to valid county/state"
            return lead_result
        
        logger.info(f"📍 Lead location: {zip_code} → {state}, {county} County")
        
        # NEW: Extract specific service from lead data for multi-level routing
        specific_service = _extract_specific_service(ghl_lead)
        lead_result["specific_service"] = specific_service
        
        logger.info(f"🎯 Enhanced routing: Category='{service_category}', Service='{specific_service}', ZIP='{zip_code}'")
        
        # Find matching vendors using enhanced multi-level routing
        matching_vendors = lead_routing_service.find_matching_vendors(
            account_id=account_id,
            service_category=service_category,
            zip_code=zip_code,  # LeadRoutingService handles ZIP→County conversion internally
            specific_service=specific_service  # NEW: Pass specific service for exact matching
        )
        
        lead_result["matching_vendors_count"] = len(matching_vendors)
        
        if not matching_vendors:
            lead_result["error_message"] = f"No matching vendors found for {service_category} in {county}, {state}"
            return lead_result
        
        # Select vendor using routing logic
        selected_vendor = lead_routing_service.select_vendor_from_pool(matching_vendors, account_id)
        
        if not selected_vendor:
            lead_result["error_message"] = "Vendor selection failed"
            return lead_result
        
        # Create GHL opportunity with COUNTY information (not just ZIP)
        ghl_opportunity_id = await _create_ghl_opportunity_for_contact(
            ghl_lead.get('ghl_contact_id'),
            service_category,
            county,
            state,
            zip_code
        )
        
        if not ghl_opportunity_id:
            lead_result["error_message"] = "Failed to create GHL opportunity"
            return lead_result
        
        lead_result["ghl_opportunity_id"] = ghl_opportunity_id
        
        # Create lead in local database WITH county information
        lead_id = db.create_lead(
            account_id=account_id,
            customer_name=ghl_lead.get('name'),
            customer_email=ghl_lead.get('email'),
            customer_phone=ghl_lead.get('phone'),
            service_category=service_category,
            service_details={
                'location': {
                    'address': ghl_lead.get('address'),
                    'city': ghl_lead.get('city'),
                    'state': state,
                    'county': county,  # CRITICAL: Store county information
                    'zip_code': zip_code
                },
                'source': 'GoHighLevel Unassigned Lead Processing',
                'ghl_contact_id': ghl_lead.get('ghl_contact_id'),
                'ghl_opportunity_id': ghl_opportunity_id
            },
            priority='normal',
            source='ghl_unassigned_processing',
            ghl_opportunity_id=ghl_opportunity_id
        )
        
        # Assign lead to vendor in database
        assignment_success = db.assign_lead_to_vendor(lead_id, selected_vendor['id'])
        
        if assignment_success:
            # Assign the GHL opportunity to the vendor
            ghl_assignment_success = await _update_ghl_opportunity_assignment(
                ghl_opportunity_id,
                selected_vendor
            )
            
            if ghl_assignment_success:
                logger.info(f"✅ Successfully assigned opportunity {ghl_opportunity_id} to vendor {selected_vendor['name']}")
                lead_result["assignment_successful"] = True
                lead_result["assigned_vendor"] = {
                    "id": selected_vendor['id'],
                    "name": selected_vendor['name'],
                    "email": selected_vendor.get('email')
                }
            else:
                logger.warning(f"⚠️ Lead assigned in database but GHL opportunity assignment failed")
                lead_result["error_message"] = "Database assignment successful, but GHL opportunity assignment failed"
        else:
            lead_result["error_message"] = "Failed to assign lead in database"
        
    except Exception as e:
        lead_result["error_message"] = f"Processing error: {str(e)}"
        logger.error(f"Error processing lead {ghl_lead.get('ghl_contact_id')}: {e}")
    
    return lead_result

def _extract_location_data(ghl_lead: Dict[str, Any]) -> Optional[str]:
    """
    ENHANCED: Extract ZIP code from multiple sources with robust type handling
    Fixes integer ZIP code crashes and expands field coverage with intelligent fallbacks
    
    Args:
        ghl_lead: GHL lead data dictionary
        
    Returns:
        ZIP code as string or None if not found
    """
    # Priority 1: Check custom fields for ZIP code (most reliable)
    custom_fields = ghl_lead.get('custom_fields', {})
    
    # Comprehensive custom field names for ZIP codes
    zip_field_names = [
        'service_zip_code', 'zip_code', 'postal_code', 'service_location',
        'what_zip_code_are_you_requesting_service_in', 'service_area_zip',
        'location_zip', 'zip_code_of_service', 'zipcode', 'zip',
        'service_zip', 'delivery_zip', 'installation_zip', 'work_location',
        'job_zip', 'customer_zip', 'billing_zip', 'shipping_zip'
    ]
    
    # Check if any custom field contains ZIP code data
    if isinstance(custom_fields, list):
        # Handle array format custom fields
        for field in custom_fields:
            if not isinstance(field, dict):
                continue
                
            field_id = field.get('id', '')
            field_name = field.get('name', '').lower().replace(' ', '_').replace('?', '').replace(',', '').replace('-', '_')
            field_value = field.get('value')
            
            # CRITICAL FIX: Handle both integer and string values + None values
            if field_value is None:
                continue
            elif isinstance(field_value, (int, float)):
                field_value = str(int(field_value))  # Convert to string, remove decimal
            elif isinstance(field_value, str):
                field_value = field_value.strip()
            else:
                continue  # Skip other types
            
            # CRITICAL FIX: Check for known ZIP code field ID first
            if field_id == 'y3Xo7qsFEQumoFugTeCq':  # Known ZIP code field ID from debug output
                if field_value and len(field_value) == 5 and field_value.isdigit():
                    logger.info(f"📍 Found ZIP from known field ID '{field_id}': {field_value}")
                    return field_value
            
            # Also check field names as fallback
            if field_name and any(zip_name in field_name for zip_name in zip_field_names):
                if field_value and len(field_value) == 5 and field_value.isdigit():
                    logger.info(f"📍 Found ZIP from custom field '{field.get('name')}': {field_value}")
                    return field_value
            
            # ENHANCED: Check any field that contains a 5-digit number as potential ZIP
            if field_value and len(field_value) == 5 and field_value.isdigit():
                # Log potential ZIP codes for debugging
                logger.info(f"📍 Found potential ZIP code in field '{field_id}' (name: '{field.get('name', 'unknown')}'): {field_value}")
                return field_value
    
    elif isinstance(custom_fields, dict):
        # Handle dictionary format custom fields
        for field_key, field_value in custom_fields.items():
            field_key_clean = field_key.lower().replace(' ', '_').replace('?', '').replace(',', '').replace('-', '_')
            
            # CRITICAL FIX: Handle both integer and string values + None values
            if field_value is None:
                continue
            elif isinstance(field_value, (int, float)):
                zip_value = str(int(field_value))  # Convert to string, remove decimal
            elif isinstance(field_value, str):
                zip_value = field_value.strip()
            else:
                continue  # Skip other types
            
            if any(zip_name in field_key_clean for zip_name in zip_field_names):
                if zip_value and len(zip_value) == 5 and zip_value.isdigit():
                    logger.info(f"📍 Found ZIP from custom field '{field_key}': {zip_value}")
                    return zip_value
    
    # Priority 2: Check standard GHL contact fields
    standard_zip_fields = ['postalCode', 'postal_code', 'zipCode', 'zip_code']
    for zip_field in standard_zip_fields:
        standard_zip = ghl_lead.get(zip_field)
        if standard_zip:
            # Handle integer postal codes
            if isinstance(standard_zip, (int, float)):
                standard_zip = str(int(standard_zip))
            elif isinstance(standard_zip, str):
                standard_zip = standard_zip.strip()
            
            if standard_zip and len(standard_zip) == 5 and standard_zip.isdigit():
                logger.info(f"📍 Found ZIP from standard field '{zip_field}': {standard_zip}")
                return standard_zip
    
    # Priority 3: Extract from address field using regex
    address_fields = ['address', 'address1', 'address_1', 'full_address', 'street_address']
    for addr_field in address_fields:
        address = ghl_lead.get(addr_field, '')
        if address and isinstance(address, str):
            import re
            # Match 5-digit ZIP codes, optionally followed by +4
            zip_match = re.search(r'\b(\d{5})(?:-\d{4})?\b', address)
            if zip_match:
                zip_code = zip_match.group(1)
                logger.info(f"📍 Extracted ZIP from address field '{addr_field}' ('{address}'): {zip_code}")
                return zip_code
    
    # Priority 4: Check tags for ZIP codes
    tags = ghl_lead.get('tags', [])
    if isinstance(tags, list):
        for tag in tags:
            if isinstance(tag, str):
                import re
                zip_match = re.search(r'\b(\d{5})\b', tag)
                if zip_match:
                    zip_code = zip_match.group(1)
                    logger.info(f"📍 Extracted ZIP from tag '{tag}': {zip_code}")
                    return zip_code
    
    # Priority 5: Check city/state for major metropolitan areas (fallback)
    city = ghl_lead.get('city', '').lower().strip() if ghl_lead.get('city') else ''
    state = ghl_lead.get('state', '').upper().strip() if ghl_lead.get('state') else ''
    
    if city and state:
        # Major city fallback mapping for common metro areas
        metro_fallbacks = {
            ('miami', 'FL'): '33101', ('miami beach', 'FL'): '33139',
            ('fort lauderdale', 'FL'): '33301', ('hollywood', 'FL'): '33020',
            ('tampa', 'FL'): '33601', ('orlando', 'FL'): '32801',
            ('jacksonville', 'FL'): '32202', ('naples', 'FL'): '34102',
            ('key west', 'FL'): '33040', ('west palm beach', 'FL'): '33401',
            ('new york', 'NY'): '10001', ('manhattan', 'NY'): '10001',
            ('brooklyn', 'NY'): '11201', ('bronx', 'NY'): '10451',
            ('los angeles', 'CA'): '90210', ('san diego', 'CA'): '92101',
            ('san francisco', 'CA'): '94102', ('chicago', 'IL'): '60601',
            ('houston', 'TX'): '77001', ('dallas', 'TX'): '75201',
            ('austin', 'TX'): '78701', ('atlanta', 'GA'): '30301',
            ('seattle', 'WA'): '98101', ('boston', 'MA'): '02101'
        }
        
        fallback_zip = metro_fallbacks.get((city, state))
        if fallback_zip:
            logger.info(f"📍 Using metro area fallback ZIP for {city}, {state}: {fallback_zip}")
            return fallback_zip
    
    # Priority 6: Look for partial matches in location-related text fields
    text_fields = ['description', 'notes', 'message', 'comment', 'details']
    for text_field in text_fields:
        text_content = ghl_lead.get(text_field, '')
        if text_content and isinstance(text_content, str):
            import re
            # Look for patterns like "in 33101" or "ZIP: 33101"
            zip_pattern = re.search(r'(?:zip|postal|area|location|service)[\s:]*(\d{5})\b', text_content.lower())
            if zip_pattern:
                zip_code = zip_pattern.group(1)
                logger.info(f"📍 Extracted ZIP from text field '{text_field}': {zip_code}")
                return zip_code
    
    # Log detailed failure information for debugging
    logger.warning(f"⚠️ Could not extract ZIP code from lead: {ghl_lead.get('ghl_contact_id')}")
    logger.debug(f"   Available fields: {list(ghl_lead.keys())}")
    logger.debug(f"   Custom fields type: {type(custom_fields)}")
    
    if isinstance(custom_fields, list) and custom_fields:
        logger.debug(f"   Custom field names: {[f.get('name') for f in custom_fields if isinstance(f, dict)]}")
    elif isinstance(custom_fields, dict):
        logger.debug(f"   Custom field keys: {list(custom_fields.keys())}")
    
    return None

async def _create_ghl_opportunity_for_contact(contact_id: str, service_category: str, county: str, state: str, zip_code: str) -> Optional[str]:
    """
    COUNTY-BASED ARCHITECTURE: Create a GHL opportunity for the contact with county information
    This aligns with the county-based matching system for consistent location representation
    """
    try:
        # Initialize GHL API client
        ghl_api = GoHighLevelAPI(
            private_token=AppConfig.GHL_PRIVATE_TOKEN,
            location_id=AppConfig.GHL_LOCATION_ID
        )
        
        # COUNTY-BASED: Use county information in opportunity title for consistency
        location_description = f"{county}, {state}" if county and state else zip_code
        
        # Prepare opportunity data with county-based location information
        opportunity_data = {
            'contactId': contact_id,
            'pipelineId': AppConfig.PIPELINE_ID,
            'pipelineStageId': AppConfig.NEW_LEAD_STAGE_ID,
            'title': f"{service_category} Service Request - {location_description}",
            'name': f"{service_category} Service Request",
            'value': 0,  # Default value, can be updated later
            'status': 'open',
            'source': 'Lead Router - County-Based Assignment'
        }
        
        logger.info(f"🔄 Creating GHL opportunity for contact {contact_id}")
        logger.info(f"📊 Pipeline: {AppConfig.PIPELINE_ID}, Stage: {AppConfig.NEW_LEAD_STAGE_ID}")
        logger.info(f"🎯 Service: {service_category}, Location: {location_description} (ZIP: {zip_code})")
        
        # Create opportunity using GHL API
        opportunity_response = ghl_api.create_opportunity(opportunity_data)
        
        if opportunity_response and 'id' in opportunity_response:
            opportunity_id = opportunity_response['id']
            logger.info(f"✅ Successfully created GHL opportunity: {opportunity_id}")
            return opportunity_id
        else:
            logger.error(f"❌ Failed to create GHL opportunity - invalid response: {opportunity_response}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error creating GHL opportunity for contact {contact_id}: {e}")
        return None

def _extract_service_category(ghl_lead: Dict[str, Any]) -> Optional[str]:
    """
    Extract service category from lead tags or custom fields using the new service_manager.
    FIXED: Now uses service_manager instead of removed COMPLETE_SERVICE_CATEGORIES.
    """
    # Import the service manager
    from api.services.service_categories import service_manager
    
    # Check custom fields first
    custom_fields = ghl_lead.get('custom_fields', {})
    if 'service_category' in custom_fields:
        category = custom_fields['service_category']
        # Validate against service hierarchy
        if service_manager.is_valid_category(category):
            return category
    
    # Check tags for service-related keywords
    tags = ghl_lead.get('tags', [])
    
    # Try to find best category match from tags
    for tag in tags:
        # Use service_manager to find best category match
        best_match = service_manager.find_best_category_match(tag)
        if best_match:
            return best_match
    
    # Try combining all tags into search text
    if tags:
        combined_tags = ' '.join(tags)
        best_match = service_manager.find_best_category_match(combined_tags)
        if best_match:
            return best_match
    
    # Default to a category that exists in the service hierarchy
    return 'Boater Resources'

async def _update_ghl_opportunity_assignment(ghl_opportunity_id: str, vendor: Dict[str, Any]) -> bool:
    """
    Update GoHighLevel opportunity with assigned vendor using opportunity API (CORRECT METHOD)
    This assigns the opportunity to the vendor's GHL User ID, making it appear in their pipeline
    """
    try:
        # Use the working Private Token instead of expired Location API token
        working_token = AppConfig.GHL_PRIVATE_TOKEN
        if not working_token:
            logger.error("No working GHL token available for opportunity assignment")
            return False
        
        # Check if vendor has a GHL User ID (required for opportunity assignment)
        vendor_user_id = vendor.get('ghl_user_id')
        if not vendor_user_id:
            logger.error(f"❌ Vendor {vendor.get('name')} has no GHL User ID - cannot assign opportunity")
            return False
        
        # Initialize GHL API client for opportunity update
        ghl_api = GoHighLevelAPI(
            private_token=working_token,
            location_id=AppConfig.GHL_LOCATION_ID
        )
        
        # Prepare opportunity update data
        update_data = {
            'assignedTo': vendor_user_id,  # CORRECT: Use vendor's GHL User ID
            'pipelineId': AppConfig.PIPELINE_ID,
            'pipelineStageId': AppConfig.NEW_LEAD_STAGE_ID,
            'customFields': [
                {
                    'id': 'assignment_method_field_id',  # This would need the actual custom field ID
                    'value': 'Automated Lead Router'
                }
            ]
        }
        
        logger.info(f"🔄 Updating GHL opportunity {ghl_opportunity_id} with vendor {vendor.get('name')}")
        logger.info(f"👤 Assigning to vendor User ID: {vendor_user_id}")
        logger.info(f"📊 Pipeline: {AppConfig.PIPELINE_ID}, Stage: {AppConfig.NEW_LEAD_STAGE_ID}")
        
        # Use the new update_opportunity method
        success = ghl_api.update_opportunity(ghl_opportunity_id, update_data)
        
        if success:
            logger.info(f"✅ Successfully assigned opportunity {ghl_opportunity_id} to vendor {vendor.get('name')}")
            return True
        else:
            logger.error(f"❌ Failed to update GHL opportunity assignment")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error updating GHL opportunity assignment: {e}")
        return False

def _get_coverage_summary(vendor: Dict[str, Any]) -> str:
    """Generate human-readable coverage summary for vendor"""
    coverage_type = vendor.get('service_coverage_type', 'zip')
    
    if coverage_type == 'global':
        return "Global coverage (worldwide)"
    elif coverage_type == 'national':
        return "National coverage (United States)"
    elif coverage_type == 'state':
        states = vendor.get('service_states', [])
        if len(states) == 1:
            return f"State coverage: {states[0]}"
        elif len(states) <= 3:
            return f"State coverage: {', '.join(states)}"
        else:
            return f"State coverage: {len(states)} states"
    elif coverage_type == 'county':
        counties = vendor.get('service_counties', [])
        if len(counties) == 1:
            return f"County coverage: {counties[0]}"
        elif len(counties) <= 3:
            return f"County coverage: {', '.join(counties)}"
        else:
            return f"County coverage: {len(counties)} counties"
    elif coverage_type == 'zip':
        zip_codes = vendor.get('service_areas', [])
        if len(zip_codes) <= 5:
            return f"ZIP code coverage: {', '.join(zip_codes)}"
        else:
            return f"ZIP code coverage: {len(zip_codes)} ZIP codes"
    else:
        return f"Coverage: {coverage_type}"

@router.post("/sync-performance-data")
async def sync_performance_data():
    """
    Sync lead_close_percentage for all vendors from GHL.
    """
    try:
        # Get all vendors
        vendors = db.get_vendors()
        
        # Initialize GHL API client
        ghl_api = GoHighLevelAPI(
            location_api_key=AppConfig.GHL_LOCATION_API,
            private_token=AppConfig.GHL_PRIVATE_TOKEN,
            location_id=AppConfig.GHL_LOCATION_ID,
            agency_api_key=AppConfig.GHL_AGENCY_API_KEY,
            company_id=AppConfig.GHL_COMPANY_ID
        )
        
        updated_count = 0
        for vendor in vendors:
            ghl_contact_id = vendor.get("ghl_contact_id")
            if not ghl_contact_id:
                continue
            
            # Get contact from GHL
            contact = ghl_api.get_contact_by_id(ghl_contact_id)
            if not contact:
                continue
            
            # Get lead_close_percentage from custom fields
            custom_fields = contact.get("customFields", [])
            lead_close_percentage = 0.0
            for field in custom_fields:
                if field.get("name") == "Lead Close %":
                    try:
                        lead_close_percentage = float(field.get("value", 0.0))
                    except (ValueError, TypeError):
                        lead_close_percentage = 0.0
                    break
            
            # Update vendor in database
            conn = db._get_conn()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE vendors SET lead_close_percentage = ? WHERE id = ?",
                (lead_close_percentage, vendor["id"])
            )
            conn.commit()
            conn.close()
            updated_count += 1
            
        return {
            "status": "success",
            "message": f"Successfully updated performance data for {updated_count} vendors."
        }
        
    except Exception as e:
        logger.error(f"Error syncing performance data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to sync performance data")
