# api/routes/routing_admin.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
import requests
import json
from database.simple_connection import db
from api.services.lead_routing_service import lead_routing_service
from config import AppConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/routing", tags=["Lead Routing Administration"])

class RoutingConfigRequest(BaseModel):
    performance_percentage: int

class VendorMatchingRequest(BaseModel):
    zip_code: str
    service_category: str

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
        
        # Find matching vendors
        matching_vendors = lead_routing_service.find_matching_vendors(
            account_id=account_id,
            service_category=service_category,
            zip_code=zip_code
        )
        
        # Select vendor using routing logic
        selected_vendor = None
        if matching_vendors:
            selected_vendor = lead_routing_service.select_vendor_from_pool(
                matching_vendors, account_id
            )
        
        return {
            "status": "success",
            "data": {
                "zip_code": zip_code,
                "service_category": service_category,
                "matching_vendors": matching_vendors,
                "selected_vendor": selected_vendor,
                "match_count": len(matching_vendors)
            },
            "message": f"Found {len(matching_vendors)} matching vendors for {service_category} in {zip_code}"
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
        headers = {
            'Authorization': f'Bearer {AppConfig.GHL_LOCATION_API}',
            'Content-Type': 'application/json',
            'Version': '2021-07-28'
        }
        
        # Get contacts from GHL that are leads but don't have assigned vendors
        url = 'https://services.leadconnectorhq.com/contacts/'
        params = {
            'limit': 100,  # Process up to 100 unassigned leads at a time
            'query': 'lead'  # Filter for leads
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch leads from GHL: {response.status_code} - {response.text}")
            return []
        
        data = response.json()
        contacts = data.get('contacts', [])
        
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
    """
    lead_result = {
        "ghl_contact_id": ghl_lead.get('ghl_contact_id'),
        "customer_name": ghl_lead.get('name'),
        "assignment_successful": False,
        "assigned_vendor": None,
        "matching_vendors_count": 0,
        "error_message": None,
        "service_category": None,
        "zip_code": None
    }
    
    try:
        # Extract service category from tags or custom fields
        service_category = _extract_service_category(ghl_lead)
        lead_result["service_category"] = service_category
        
        # Extract ZIP code from address
        zip_code = ghl_lead.get('postal_code') or '33101'  # Default to Miami if no ZIP
        lead_result["zip_code"] = zip_code
        
        if not service_category:
            lead_result["error_message"] = "Could not determine service category"
            return lead_result
        
        # Find matching vendors
        matching_vendors = lead_routing_service.find_matching_vendors(
            account_id=account_id,
            service_category=service_category,
            zip_code=zip_code
        )
        
        lead_result["matching_vendors_count"] = len(matching_vendors)
        
        if not matching_vendors:
            lead_result["error_message"] = "No matching vendors found"
            return lead_result
        
        # Select vendor using routing logic
        selected_vendor = lead_routing_service.select_vendor_from_pool(matching_vendors, account_id)
        
        if not selected_vendor:
            lead_result["error_message"] = "Vendor selection failed"
            return lead_result
        
        # Create lead in local database
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
                    'state': ghl_lead.get('state'),
                    'zip_code': zip_code
                },
                'source': 'GoHighLevel Unassigned Lead Processing',
                'ghl_contact_id': ghl_lead.get('ghl_contact_id')
            },
            priority='normal',
            source='ghl_unassigned_processing'
        )
        
        # Assign lead to vendor
        assignment_success = db.assign_lead_to_vendor(lead_id, selected_vendor['id'])
        
        if assignment_success:
            # Update GoHighLevel contact with assigned vendor
            await _update_ghl_contact_assignment(
                ghl_lead.get('ghl_contact_id'),
                selected_vendor
            )
            
            lead_result["assignment_successful"] = True
            lead_result["assigned_vendor"] = {
                "id": selected_vendor['id'],
                "name": selected_vendor['name'],
                "email": selected_vendor.get('email')
            }
        else:
            lead_result["error_message"] = "Failed to assign lead in database"
        
    except Exception as e:
        lead_result["error_message"] = f"Processing error: {str(e)}"
        logger.error(f"Error processing lead {ghl_lead.get('ghl_contact_id')}: {e}")
    
    return lead_result

def _extract_service_category(ghl_lead: Dict[str, Any]) -> Optional[str]:
    """
    Extract service category from lead tags or custom fields
    """
    # Check custom fields first
    custom_fields = ghl_lead.get('custom_fields', {})
    if 'service_category' in custom_fields:
        return custom_fields['service_category']
    
    # Check tags for service-related keywords
    tags = ghl_lead.get('tags', [])
    service_keywords = {
        'boat maintenance': 'Boat Maintenance',
        'marine systems': 'Marine Systems',
        'engine': 'Engines and Generators',
        'generator': 'Engines and Generators',
        'repair': 'Boat and Yacht Repair',
        'yacht': 'Boat and Yacht Repair'
    }
    
    for tag in tags:
        tag_lower = tag.lower()
        for keyword, category in service_keywords.items():
            if keyword in tag_lower:
                return category
    
    # Default to most common service
    return 'Boat Maintenance'

async def _update_ghl_contact_assignment(ghl_contact_id: str, vendor: Dict[str, Any]) -> bool:
    """
    Update GoHighLevel contact with assigned vendor information
    """
    try:
        headers = {
            'Authorization': f'Bearer {AppConfig.GHL_LOCATION_API}',
            'Content-Type': 'application/json',
            'Version': '2021-07-28'
        }
        
        # Update contact with assigned vendor
        url = f'https://services.leadconnectorhq.com/contacts/{ghl_contact_id}'
        update_data = {
            'assignedTo': vendor.get('ghl_contact_id'),  # Assign to vendor's GHL contact ID
            'customFields': {
                'assigned_vendor_name': vendor.get('name'),
                'assigned_vendor_email': vendor.get('email'),
                'assignment_date': json.dumps({'date': 'now'}),
                'assignment_method': 'Automated Lead Router'
            }
        }
        
        response = requests.put(url, json=update_data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            logger.info(f"Successfully updated GHL contact {ghl_contact_id} with vendor assignment")
            return True
        else:
            logger.error(f"Failed to update GHL contact assignment: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error updating GHL contact assignment: {e}")
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
