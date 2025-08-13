# api/routes/lead_reassignment.py

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from database.simple_connection import db as simple_db_instance
from api.services.lead_routing_service import lead_routing_service
from api.services.ghl_api import GoHighLevelAPI
from config import AppConfig

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/reassignment", tags=["Lead Reassignment"])

class LeadReassignmentRequest(BaseModel):
    """Request model for lead reassignment"""
    contact_id: str = Field(..., description="GHL Contact ID")
    lead_id: Optional[str] = Field(None, description="Lead Router Lead ID (optional)")
    reason: Optional[str] = Field("no_vendor_response", description="Reason for reassignment")
    exclude_vendor_ids: Optional[List[str]] = Field(default_factory=list, description="Vendor IDs to exclude from reassignment")
    force_reassign: bool = Field(False, description="Force reassignment even if vendor was already assigned")

class LeadReassignmentResponse(BaseModel):
    """Response model for lead reassignment"""
    success: bool
    message: str
    contact_id: str
    lead_id: Optional[str]
    previous_vendor_id: Optional[str]
    new_vendor_id: Optional[str]
    vendor_name: Optional[str]
    vendor_email: Optional[str]
    reassignment_count: int

@router.post("/lead", response_model=LeadReassignmentResponse)
async def reassign_lead(request: LeadReassignmentRequest):
    """
    Reassign a lead to a new vendor without creating a new opportunity.
    
    This endpoint is designed for workflow automation where leads need to be
    reassigned after a certain period of vendor inactivity.
    """
    logger.info(f"🔄 Lead reassignment request for contact: {request.contact_id}")
    
    try:
        # Get account configuration
        # For now, we'll use a simple approach - in production, you'd get this from the contact or request
        account = None
        accounts = simple_db_instance.get_vendors()  # This returns all vendors
        if accounts:
            # Get the first account_id from vendors
            account_id = accounts[0].get('account_id')
            if account_id:
                # Create a minimal account object
                account = {
                    'id': account_id,
                    'ghl_location_id': AppConfig.GHL_LOCATION_ID,
                    'ghl_api_key': AppConfig.GHL_PRIVATE_TOKEN
                }
        
        if not account:
            # Use default configuration
            account = {
                'id': 'default',
                'ghl_location_id': AppConfig.GHL_LOCATION_ID,
                'ghl_api_key': AppConfig.GHL_PRIVATE_TOKEN
            }
        
        # Initialize GHL API
        ghl_api = GoHighLevelAPI(
            location_id=account['ghl_location_id'],
            api_key=account.get('ghl_api_key')
        )
        
        # Get contact details from GHL
        contact_response = ghl_api.get_contact(request.contact_id)
        if not contact_response.get('success'):
            raise HTTPException(
                status_code=404, 
                detail=f"Contact {request.contact_id} not found in GHL"
            )
        
        contact = contact_response.get('contact', {})
        
        # Find existing lead in our database
        lead = None
        if request.lead_id:
            lead = simple_db_instance.get_lead_by_id(request.lead_id)
        else:
            # Try to find lead by contact ID
            leads = simple_db_instance.get_leads_by_contact_id(request.contact_id)
            if leads:
                # Get the most recent lead
                lead = max(leads, key=lambda x: x.get('created_at', ''))
        
        if not lead:
            # Create a minimal lead record for tracking
            lead_id = str(uuid.uuid4())
            lead_data = {
                'id': lead_id,
                'account_id': account['id'],
                'ghl_contact_id': request.contact_id,
                'form_identifier': 'reassignment',
                'first_name': contact.get('firstName', ''),
                'last_name': contact.get('lastName', ''),
                'email': contact.get('email', ''),
                'phone': contact.get('phone', ''),
                'service_category': 'Unknown',
                'specific_service': 'Reassignment',
                'reassignment_count': 0,
                'created_at': datetime.utcnow().isoformat()
            }
            
            # Try to extract service info from custom fields
            custom_fields = contact.get('customFields', [])
            for field in custom_fields:
                if field.get('key') == 'service_category':
                    lead_data['service_category'] = field.get('value', 'Unknown')
                elif field.get('key') == 'specific_service':
                    lead_data['specific_service'] = field.get('value', 'Unknown')
            
            lead_id = simple_db_instance.create_lead(lead_data)
            lead = simple_db_instance.get_lead_by_id(lead_id)
        
        # Track previous vendor
        previous_vendor_id = lead.get('vendor_id')
        reassignment_count = lead.get('reassignment_count', 0) + 1
        
        # Build exclude list
        exclude_vendors = set(request.exclude_vendor_ids or [])
        if previous_vendor_id and not request.force_reassign:
            exclude_vendors.add(previous_vendor_id)
        
        # Get lead location info
        zip_code = lead.get('zip_code') or contact.get('address1', '')[:5]
        
        # Find new vendor using routing service
        routing_result = lead_routing_service.route_lead_to_vendor(
            service_category=lead.get('service_category', 'Unknown'),
            specific_service=lead.get('specific_service', 'Unknown'),
            zip_code=zip_code,
            exclude_vendor_ids=list(exclude_vendors)
        )
        
        new_vendor_id = None
        vendor_name = None
        vendor_email = None
        
        if routing_result.get('vendor'):
            vendor = routing_result['vendor']
            new_vendor_id = vendor.get('id')
            vendor_name = vendor.get('business_name')
            vendor_email = vendor.get('email')
            
            # Update lead with new vendor assignment
            update_data = {
                'vendor_id': new_vendor_id,
                'vendor_assigned_at': datetime.utcnow().isoformat(),
                'reassignment_count': reassignment_count,
                'reassignment_reason': request.reason,
                'previous_vendor_id': previous_vendor_id
            }
            simple_db_instance.update_lead(lead['id'], update_data)
            
            # Update contact in GHL with new vendor info
            ghl_update_data = {
                'customFields': [
                    {'key': 'assigned_vendor', 'field_value': vendor_name},
                    {'key': 'vendor_email', 'field_value': vendor_email},
                    {'key': 'reassignment_count', 'field_value': str(reassignment_count)},
                    {'key': 'last_reassignment', 'field_value': datetime.utcnow().isoformat()}
                ]
            }
            
            # Add tag for reassignment tracking
            if contact.get('tags'):
                ghl_update_data['tags'] = contact['tags'] + [f'reassigned_{reassignment_count}']
            else:
                ghl_update_data['tags'] = [f'reassigned_{reassignment_count}']
            
            ghl_api.update_contact(request.contact_id, ghl_update_data)
            
            # Log reassignment event
            event_data = {
                'lead_id': lead['id'],
                'contact_id': request.contact_id,
                'event_type': 'lead_reassigned',
                'previous_vendor_id': previous_vendor_id,
                'new_vendor_id': new_vendor_id,
                'reason': request.reason,
                'reassignment_count': reassignment_count,
                'timestamp': datetime.utcnow().isoformat()
            }
            simple_db_instance.create_lead_event(event_data)
            
            logger.info(f"✅ Successfully reassigned lead {lead['id']} from vendor {previous_vendor_id} to {new_vendor_id}")
            
            return LeadReassignmentResponse(
                success=True,
                message=f"Lead reassigned to {vendor_name}",
                contact_id=request.contact_id,
                lead_id=lead['id'],
                previous_vendor_id=previous_vendor_id,
                new_vendor_id=new_vendor_id,
                vendor_name=vendor_name,
                vendor_email=vendor_email,
                reassignment_count=reassignment_count
            )
        else:
            # No vendor found
            logger.warning(f"⚠️ No available vendor found for reassignment of lead {lead['id']}")
            
            # Update lead to track failed reassignment
            update_data = {
                'reassignment_count': reassignment_count,
                'reassignment_reason': request.reason,
                'reassignment_failed_at': datetime.utcnow().isoformat()
            }
            simple_db_instance.update_lead(lead['id'], update_data)
            
            return LeadReassignmentResponse(
                success=False,
                message="No available vendor found for reassignment",
                contact_id=request.contact_id,
                lead_id=lead['id'],
                previous_vendor_id=previous_vendor_id,
                new_vendor_id=None,
                vendor_name=None,
                vendor_email=None,
                reassignment_count=reassignment_count
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in lead reassignment: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reassign lead: {str(e)}"
        )

@router.get("/history/{contact_id}")
async def get_reassignment_history(contact_id: str):
    """Get the reassignment history for a contact"""
    try:
        # Get all leads for this contact
        leads = simple_db_instance.get_leads_by_contact_id(contact_id)
        
        # Get reassignment events
        history = []
        for lead in leads:
            events = simple_db_instance.get_lead_events(
                lead_id=lead['id'], 
                event_type='lead_reassigned'
            )
            history.extend(events)
        
        # Sort by timestamp
        history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return {
            "success": True,
            "contact_id": contact_id,
            "reassignment_count": len(history),
            "history": history
        }
        
    except Exception as e:
        logger.error(f"Error getting reassignment history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get reassignment history: {str(e)}"
        )

@router.post("/bulk")
async def bulk_reassign_leads(request: Request):
    """Bulk reassign multiple leads"""
    data = await request.json()
    contact_ids = data.get('contact_ids', [])
    reason = data.get('reason', 'bulk_reassignment')
    
    results = []
    for contact_id in contact_ids:
        try:
            result = await reassign_lead(
                LeadReassignmentRequest(
                    contact_id=contact_id,
                    reason=reason
                )
            )
            results.append(result.dict())
        except Exception as e:
            results.append({
                "success": False,
                "contact_id": contact_id,
                "message": str(e)
            })
    
    return {
        "success": True,
        "total": len(contact_ids),
        "successful": sum(1 for r in results if r.get('success')),
        "failed": sum(1 for r in results if not r.get('success')),
        "results": results
    }