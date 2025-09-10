# api/routes/webhook_reassignment_fixed.py

"""
Fixed GHL webhook endpoint for lead reassignment.
Uses the core reassignment logic to ensure proper flow.
"""

import logging
import json
import time
from fastapi import Request, HTTPException

from config import AppConfig
from api.services.lead_reassignment_core import lead_reassignment_core
from database.simple_connection import db as simple_db_instance

logger = logging.getLogger(__name__)

async def handle_lead_reassignment_webhook_fixed(request: Request):
    """
    FIXED: GHL workflow webhook endpoint for lead reassignment.
    Uses core reassignment logic that ensures proper flow:
    1. Opportunity exists or is created
    2. Lead exists with opportunity_id  
    3. Vendor is reassigned
    4. GHL opportunity is updated with assignedTo
    
    This replaces the broken implementation in webhook_routes.py
    """
    start_time = time.time()
    
    try:
        # Validate API key
        api_key = request.headers.get("X-Webhook-API-Key")
        expected_api_key = AppConfig.GHL_WEBHOOK_API_KEY
        
        if not api_key:
            logger.error(f"❌ GHL reassignment webhook missing API key from IP: {request.client.host}")
            raise HTTPException(status_code=401, detail="Missing X-Webhook-API-Key header")
        
        if api_key != expected_api_key:
            logger.error(f"❌ GHL reassignment webhook API key mismatch from IP: {request.client.host}")
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        logger.info(f"✅ GHL reassignment webhook API key validated")
        
        # Parse incoming GHL workflow webhook payload
        ghl_payload = await request.json()
        logger.info(f"📥 GHL Lead Reassignment Webhook received")
        
        # Extract contact and opportunity information
        contact_id = ghl_payload.get("contact_id") or ghl_payload.get("contactId")
        opportunity_id = ghl_payload.get("opportunity_id") or ghl_payload.get("opportunityId")
        
        if not contact_id:
            logger.error(f"❌ No contact ID provided in reassignment webhook")
            raise HTTPException(status_code=400, detail="Contact ID is required for lead reassignment")
        
        logger.info(f"🔄 Processing reassignment for contact: {contact_id}")
        if opportunity_id:
            logger.info(f"📋 Opportunity ID provided: {opportunity_id}")
        
        # Extract reassignment reason if provided
        reason = ghl_payload.get("reason", "webhook_triggered")
        
        # Call core reassignment logic
        result = await lead_reassignment_core.reassign_lead(
            contact_id=contact_id,
            opportunity_id=opportunity_id,
            exclude_previous=True,  # Always exclude previous vendor for reassignments
            reason=reason,
            preserve_source=True  # Always preserve original source
        )
        
        # Log webhook processing time
        processing_time = time.time() - start_time
        
        # Log webhook result
        simple_db_instance.log_activity(
            event_type="reassignment_webhook_processed",
            event_data={
                "contact_id": contact_id,
                "opportunity_id": opportunity_id,
                "success": result.get("success"),
                "processing_time": processing_time,
                "result": result
            },
            lead_id=result.get("lead_id", contact_id),
            success=result.get("success", False),
            error_message=result.get("error", "")
        )
        
        if result.get("success"):
            logger.info(f"✅ Reassignment successful: {result.get('message')}")
            return {
                "status": "success",
                "message": result.get("message"),
                "contact_id": contact_id,
                "lead_id": result.get("lead_id"),
                "opportunity_id": result.get("opportunity_id"),
                "vendor": result.get("vendor_name"),
                "processing_time": processing_time
            }
        else:
            logger.warning(f"⚠️ Reassignment failed: {result.get('error')}")
            return {
                "status": "failed",
                "message": result.get("error"),
                "contact_id": contact_id,
                "processing_time": processing_time
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in reassignment webhook: {str(e)}", exc_info=True)
        
        # Log error
        simple_db_instance.log_activity(
            event_type="reassignment_webhook_error",
            event_data={
                "error": str(e),
                "payload": await request.body() if request else None
            },
            lead_id="webhook_error",
            success=False,
            error_message=str(e)
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Internal error processing reassignment: {str(e)}"
        )