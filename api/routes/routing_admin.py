# api/routes/routing_admin.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
import requests
import json
import uuid
from database.simple_connection import db
from api.services.lead_routing_service import lead_routing_service
from api.services.ghl_api import GoHighLevelAPI
from api.routes.webhook_routes import create_lead_from_ghl_contact
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
    Process a single unassigned lead using the SHARED PIPELINE
    FIXED: Now uses create_lead_from_ghl_contact for consistent database+opportunity creation
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
        "database_lead_created": False,
        "opportunity_created": False,
        "processing_method": "shared_pipeline"
    }
    
    try:
        contact_id = ghl_lead.get('ghl_contact_id')
        if not contact_id:
            lead_result["error_message"] = "No GHL contact ID provided"
            return lead_result
        
        # Step 1: Check if database lead already exists
        existing_lead = db.get_lead_by_ghl_contact_id(contact_id)
        
        if existing_lead:
            logger.info(f"📋 Database lead already exists: {existing_lead['id']}")
            lead_id = existing_lead['id']
            opportunity_id = existing_lead.get('ghl_opportunity_id')
            lead_result["database_lead_created"] = False  # Already existed
        else:
            # Step 2: Create database lead + opportunity using SHARED PIPELINE
            logger.info(f"➕ Creating database lead using shared pipeline for contact {contact_id}")
            
            # Extract service category for form_identifier
            service_category = _extract_service_category(ghl_lead)
            if not service_category:
                lead_result["error_message"] = "Could not determine service category"
                return lead_result
            
            # Convert service category to form_identifier format
            form_identifier = service_category.lower().replace(" ", "_").replace("&", "and")
            
            try:
                # Use shared pipeline to create database lead + opportunity
                lead_id, opportunity_id = await create_lead_from_ghl_contact(
                    ghl_contact_data=ghl_lead,
                    account_id=account_id,
                    form_identifier=form_identifier
                )
                
                lead_result["database_lead_created"] = True
                lead_result["opportunity_created"] = opportunity_id is not None
                logger.info(f"✅ Shared pipeline created lead: {lead_id}, opportunity: {opportunity_id}")
                
            except Exception as e:
                lead_result["error_message"] = f"Shared pipeline failed: {str(e)}"
                logger.error(f"❌ Shared pipeline error for contact {contact_id}: {e}")
                return lead_result
        
        # Step 3: Extract service and location data for vendor matching
        service_category = _extract_service_category(ghl_lead)
        zip_code = _extract_location_data(ghl_lead)
        specific_service = _extract_specific_service(ghl_lead)
        
        lead_result["service_category"] = service_category
        lead_result["zip_code"] = zip_code
        
        if not service_category or not zip_code:
            lead_result["error_message"] = f"Missing data - service: {service_category}, zip: {zip_code}"
            return lead_result
        
        logger.info(f"🎯 Bulk assignment: Category='{service_category}', Service='{specific_service}', ZIP='{zip_code}'")
        
        # Step 4: Find matching vendors
        matching_vendors = lead_routing_service.find_matching_vendors(
            account_id=account_id,
            service_category=service_category,
            zip_code=zip_code,
            specific_service=specific_service
        )
        
        lead_result["matching_vendors_count"] = len(matching_vendors)
        
        if not matching_vendors:
            lead_result["error_message"] = f"No vendors found for {service_category} in {zip_code}"
            logger.warning(f"⚠️ No vendors found for {service_category} in {zip_code}")
            return lead_result
        
        logger.info(f"🎯 Found {len(matching_vendors)} matching vendors for {service_category}")
        
        # Step 5: Select vendor using routing logic
        selected_vendor = lead_routing_service.select_vendor_from_pool(matching_vendors, account_id)
        
        if not selected_vendor:
            lead_result["error_message"] = "Vendor selection failed"
            return lead_result
        
        logger.info(f"✅ Selected vendor: {selected_vendor.get('name')} (ID: {selected_vendor.get('id')})")
        
        # Step 6: Assign vendor in database
        db_assignment_success = db.assign_lead_to_vendor(lead_id, selected_vendor['id'])
        
        if not db_assignment_success:
            lead_result["error_message"] = "Failed to assign vendor in database"
            return lead_result
        
        # Step 7: Assign vendor to opportunity in GHL (if opportunity exists)
        ghl_assignment_success = True
        if opportunity_id and selected_vendor.get('ghl_user_id'):
            ghl_assignment_success = await _assign_vendor_to_opportunity(
                opportunity_id=opportunity_id,
                vendor=selected_vendor,
                lead_data=ghl_lead,
                account_id=account_id
            )
        elif not opportunity_id:
            logger.warning(f"⚠️ No opportunity ID available for GHL assignment")
        elif not selected_vendor.get('ghl_user_id'):
            logger.warning(f"⚠️ Vendor {selected_vendor.get('name')} has no GHL User ID")
        
        # Mark as successful if database assignment worked (GHL assignment is optional)
        if db_assignment_success:
            lead_result["assignment_successful"] = True
            lead_result["assigned_vendor"] = {
                "id": selected_vendor.get('id'),
                "name": selected_vendor.get('name'),
                "ghl_user_id": selected_vendor.get('ghl_user_id'),
                "ghl_assignment_success": ghl_assignment_success
            }
            logger.info(f"✅ Successfully assigned lead {lead_id} to vendor {selected_vendor.get('name')}")
        
        return lead_result
        
    except Exception as e:
        lead_result["error_message"] = f"Processing error: {str(e)}"
        logger.error(f"❌ Error processing lead {ghl_lead.get('ghl_contact_id')}: {e}")
        return lead_result


def _extract_specific_service(ghl_lead: Dict[str, Any]) -> Optional[str]:
    """
    Extract specific service from lead data (FIXED: Previously missing function)
    Maps custom field service data to specific service categories
    """
    try:
        # Check custom fields for service details
        custom_fields = ghl_lead.get('custom_fields', [])
        
        # Handle both list and dict formats
        if isinstance(custom_fields, list):
            for field in custom_fields:
                field_id = field.get('id', '')
                field_value = field.get('value', '')
                
                # Check for service detail field (from logs we know this field ID contains service data)
                if field_id == 'FT85QGi0tBq1AfVGNJ9v' and field_value:
                    logger.info(f"🎯 Found specific service from custom field: {field_value}")
                    return str(field_value).strip()
                
                # Also check by field name patterns
                field_name = field.get('name', '').lower()
                if any(keyword in field_name for keyword in ['service', 'what service', 'type of service']):
                    if field_value:
                        logger.info(f"🎯 Found specific service from field '{field.get('name')}': {field_value}")
                        return str(field_value).strip()
        
        elif isinstance(custom_fields, dict):
            # Handle dict format custom fields
            for key, value in custom_fields.items():
                if value and any(keyword in key.lower() for keyword in ['service', 'what service', 'type of service']):
                    logger.info(f"🎯 Found specific service from dict field '{key}': {value}")
                    return str(value).strip()
        
        # Check opportunity name for service details
        opportunity_name = ghl_lead.get('opportunity_name', '')
        if opportunity_name and ' - ' in opportunity_name:
            # Extract service from opportunity name format: "Customer Name - Service Category"
            service_part = opportunity_name.split(' - ', 1)[1]
            logger.info(f"🎯 Found specific service from opportunity name: {service_part}")
            return service_part.strip()
        
        # No specific service found
        logger.debug(f"📝 No specific service found for lead {ghl_lead.get('ghl_contact_id')}")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting specific service: {e}")
        return None


async def _assign_vendor_to_opportunity(
    opportunity_id: str, 
    vendor: Dict[str, Any], 
    lead_data: Dict[str, Any],
    account_id: str
) -> bool:
    """
    Actually assign the vendor to the opportunity in GHL and update database
    This is the missing piece that completes the assignment workflow
    """
    try:
        # Step 1: Check if vendor has GHL User ID (required for opportunity assignment)
        vendor_user_id = vendor.get('ghl_user_id')
        if not vendor_user_id:
            logger.error(f"❌ Vendor {vendor.get('name')} has no GHL User ID - cannot assign opportunity")
            return False
        
        # Step 2: Update opportunity in GHL
        ghl_api = GoHighLevelAPI(
            private_token=AppConfig.GHL_PRIVATE_TOKEN,
            location_id=AppConfig.GHL_LOCATION_ID
        )
        
        # Prepare opportunity update data
        update_data = {
            'assignedTo': vendor_user_id,
            'pipelineId': AppConfig.PIPELINE_ID,
            'pipelineStageId': AppConfig.NEW_LEAD_STAGE_ID
        }
        
        logger.info(f"🔄 Updating GHL opportunity {opportunity_id} with vendor {vendor.get('name')}")
        logger.info(f"👤 Assigning to vendor User ID: {vendor_user_id}")
        logger.info(f"📊 Pipeline: {AppConfig.PIPELINE_ID}, Stage: {AppConfig.NEW_LEAD_STAGE_ID}")
        
        # Update opportunity in GHL
        ghl_success = ghl_api.update_opportunity(opportunity_id, update_data)
        
        if not ghl_success:
            logger.error(f"❌ Failed to update GHL opportunity {opportunity_id}")
            return False
        
        # Step 3: Update database - assign vendor to lead
        # First, find or create lead record in database
        contact_id = lead_data.get('ghl_contact_id')
        
        # Check if lead exists in database
        existing_lead = db.get_lead_by_ghl_contact_id(contact_id)
        
        if existing_lead:
            # Update existing lead with vendor assignment and opportunity ID
            assignment_success = db.assign_lead_to_vendor(
                existing_lead['id'], 
                vendor['id']
            )
            
            # Also update opportunity ID if not already set
            if not existing_lead.get('ghl_opportunity_id'):
                db.update_lead_opportunity_id(existing_lead['id'], opportunity_id)
        else:
            # Create new lead record in database (this shouldn't happen with proper workflow, but handle it)
            logger.warning(f"⚠️ Lead {contact_id} not found in database - creating new record")
            
            # Extract data for lead creation
            lead_id = str(uuid.uuid4())
            service_category = lead_data.get('service_category', 'Unknown')
            zip_code = lead_data.get('zip_code', '')
            
            # Create lead with vendor assignment (use basic create_lead method)
            assignment_success = db.create_lead(
                lead_id=lead_id,
                account_id=account_id,
                ghl_contact_id=contact_id,
                ghl_opportunity_id=opportunity_id,
                customer_name=lead_data.get('name', ''),
                customer_email=lead_data.get('email', ''),
                customer_phone=lead_data.get('phone', ''),
                primary_service_category=service_category,
                customer_zip_code=zip_code,
                vendor_id=vendor['id'],
                status='assigned'
            )
        
        if assignment_success:
            logger.info(f"✅ Successfully assigned opportunity and updated database")
            return True
        else:
            logger.error(f"❌ Failed to update database assignment")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error assigning vendor to opportunity: {e}")
        return False

def _extract_location_data(ghl_lead: Dict[str, Any]) -> Optional[str]:
    """
    Extract ZIP code from GHL lead data
    Checks multiple sources: custom fields, postal_code, postalCode
    """
    # Check custom fields first for ZIP code field
    custom_fields = ghl_lead.get('custom_fields', {})
    
    # Handle both list and dict format for custom fields
    if isinstance(custom_fields, list):
        for field in custom_fields:
            field_id = field.get('id', '')
            field_value = field.get('value', '')
            
            # Check for known ZIP code field ID
            if field_id == 'y3Xo7qsFEQumoFugTeCq' and field_value:
                zip_code = str(field_value).strip()
                if len(zip_code) == 5 and zip_code.isdigit():
                    logger.info(f"📍 Found ZIP from custom field: {zip_code}")
                    return zip_code
    elif isinstance(custom_fields, dict):
        # Handle dict format
        zip_value = custom_fields.get('y3Xo7qsFEQumoFugTeCq', '')
        if zip_value:
            zip_code = str(zip_value).strip()
            if len(zip_code) == 5 and zip_code.isdigit():
                logger.info(f"📍 Found ZIP from custom field dict: {zip_code}")
                return zip_code
    
    # Check standard postal code fields
    postal_code = ghl_lead.get('postal_code') or ghl_lead.get('postalCode')
    if postal_code:
        zip_code = str(postal_code).strip()
        if len(zip_code) == 5 and zip_code.isdigit():
            logger.info(f"📍 Found ZIP from postal code: {zip_code}")
            return zip_code
    
    # No valid ZIP code found
    logger.debug("⚠️ No valid ZIP code found in lead data")
    return None

def _extract_specific_service(ghl_lead: Dict[str, Any]) -> Optional[str]:
    """
    Extract specific service from GHL lead custom fields.
    Field ID 'FT85QGi0tBq1AfVGNJ9v' contains specific service like:
    - "Outboard Engine Service"
    - "Generator Service" 
    - "Boat Detailing"
    - "Inboard Engine Service"
    """
    custom_fields = ghl_lead.get('custom_fields', {})
    
    # Handle both list and dict format for custom fields
    if isinstance(custom_fields, list):
        for field in custom_fields:
            if field.get('id') == 'FT85QGi0tBq1AfVGNJ9v':
                service_value = field.get('value', '').strip()
                if service_value:
                    logger.info(f"📋 Found specific service: {service_value}")
                    return service_value
    elif isinstance(custom_fields, dict):
        service_value = custom_fields.get('FT85QGi0tBq1AfVGNJ9v', '').strip()
        if service_value:
            logger.info(f"📋 Found specific service: {service_value}")
            return service_value
    
    logger.debug("⚠️ No specific service found in custom fields")
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
