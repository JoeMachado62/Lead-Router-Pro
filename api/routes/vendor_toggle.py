import logging
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional
from database.simple_connection import db as simple_db_instance

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/vendor-toggle", tags=["Vendor Toggle"])

class VendorToggle(BaseModel):
    vendor_id: str
    taking_new_work: bool

class GHLVendorWebhook(BaseModel):
    ghl_contact_id: str
    action: str  # "suspend" or "resume"

# New model to handle full GHL payloads
class GHLWebhookPayload(BaseModel):
    contact: Optional[Dict[str, Any]] = None
    type: Optional[str] = None
    eventData: Optional[Dict[str, Any]] = None
    class Config:
        extra = "allow"  # Allow extra fields from GHL

@router.post("/availability")
async def toggle_vendor_availability(toggle_data: VendorToggle):
    """Toggle vendor availability from dashboard"""
    try:
        vendor_id = toggle_data.vendor_id
        new_availability = toggle_data.taking_new_work
        
        # Verify vendor exists
        vendor = simple_db_instance.get_vendor_by_id(vendor_id)
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")
        
        # Update availability
        success = simple_db_instance.update_vendor_availability(vendor_id, new_availability)
        
        if success:
            # Log the change
            simple_db_instance.log_activity(
                event_type="vendor_availability_toggled",
                event_data={
                    "vendor_id": vendor_id,
                    "vendor_name": vendor.get('name'),
                    "new_availability": new_availability,
                    "source": "dashboard"
                },
                vendor_id=vendor_id,
                success=True
            )
            
            return {
                "status": "success",
                "message": f"Vendor availability updated",
                "vendor_id": vendor_id,
                "taking_new_work": new_availability
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update vendor")
            
    except Exception as e:
        logger.error(f"Error in vendor toggle: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ghl-webhook-debug")
async def debug_ghl_webhook(request: Request):
    """Debug endpoint to see raw GHL payload"""
    try:
        # Get raw body
        body = await request.body()
        body_str = body.decode('utf-8')
        
        # Try to parse as JSON
        import json
        try:
            data = json.loads(body_str)
            logger.info(f"📥 DEBUG - Full GHL payload structure:")
            logger.info(f"Keys at root level: {list(data.keys())}")
            
            # Log first level of data
            for key in list(data.keys())[:10]:  # First 10 keys
                value_type = type(data[key]).__name__
                logger.info(f"  - {key}: {value_type}")
                if key == "contact":
                    logger.info(f"    Contact keys: {list(data[key].keys()) if isinstance(data[key], dict) else 'Not a dict'}")
            
            return {"debug": "Check logs for payload structure", "root_keys": list(data.keys())[:20]}
        except json.JSONDecodeError:
            logger.error(f"❌ Not valid JSON: {body_str[:200]}...")
            return {"error": "Invalid JSON", "preview": body_str[:200]}
            
    except Exception as e:
        logger.error(f"❌ Debug error: {e}")
        return {"error": str(e)}

@router.post("/ghl-webhook")
async def handle_ghl_vendor_webhook(request: Request):
    """Handle GHL webhook for vendor suspension/resume"""
    try:
        # Get raw body and parse it
        body = await request.body()
        body_str = body.decode('utf-8')
        
        import json
        try:
            data = json.loads(body_str)
        except json.JSONDecodeError:
            logger.error(f"❌ Invalid JSON in webhook: {body_str[:200]}...")
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
        logger.info(f"📥 GHL webhook received - payload has keys: {list(data.keys())[:10]}")
        
        # GHL sends a flat structure with field names as keys
        # Extract contact ID directly from root level
        ghl_contact_id = data.get('contact_id')
        if not ghl_contact_id:
            logger.error(f"❌ No contact_id found in webhook. Available keys: {list(data.keys())[:20]}")
            raise HTTPException(status_code=400, detail="No contact_id in webhook")
        
        logger.info(f"🔍 Processing webhook for contact ID: {ghl_contact_id}")
        
        # Extract tags from root level
        tags = data.get('tags', [])
        
        # Also check the "Taking New Work?" field directly
        taking_new_work_field = data.get('Taking New Work?', '')
        logger.info(f"💼 Taking New Work field value: '{taking_new_work_field}'")
            
        logger.info(f"📌 Contact tags: {tags}")
        
        # Determine action based on tags OR the "Taking New Work?" field
        action = None
        
        # First check tags - handle both array and comma-separated string formats
        processed_tags = []
        if isinstance(tags, str):
            # Split comma-separated string into individual tags
            processed_tags = [tag.strip().lower() for tag in tags.split(',') if tag.strip()]
        elif isinstance(tags, list):
            processed_tags = [tag.lower() if isinstance(tag, str) else str(tag).lower() for tag in tags]
        
        logger.info(f"🔄 Processed tags: {processed_tags}")
        
        # Check for suspend/resume in processed tags
        if processed_tags:
            for tag in processed_tags:
                if tag in ['suspend', 'suspend_leads', 'suspend leads']:
                    action = 'suspend'
                    logger.info(f"🎯 Suspend action found in tag: '{tag}'")
                    break
                elif tag in ['resume', 'resume_leads', 'resume leads']:
                    action = 'resume'
                    logger.info(f"🎯 Resume action found in tag: '{tag}'")
                    break
        
        # If no action from tags, check the "Taking New Work?" field
        if not action and taking_new_work_field:
            taking_new_work_lower = str(taking_new_work_field).lower()
            if taking_new_work_lower in ['no', 'false', '0', 'off', 'disabled']:
                action = 'suspend'
                logger.info(f"🎯 Action determined from field: suspend (Taking New Work = '{taking_new_work_field}')")
            elif taking_new_work_lower in ['yes', 'true', '1', 'on', 'enabled']:
                action = 'resume'
                logger.info(f"🎯 Action determined from field: resume (Taking New Work = '{taking_new_work_field}')")
        
        if not action:
            # If no action found, log and return success (don't fail)
            logger.info(f"ℹ️ GHL webhook for contact {ghl_contact_id} - no action determined")
            logger.info(f"   Tags: {tags}")
            logger.info(f"   Taking New Work field: '{taking_new_work_field}'")
            return {"status": "ignored", "reason": "No action determined", "tags": tags, "taking_new_work_field": taking_new_work_field, "contact_id": ghl_contact_id}
        
        logger.info(f"🎯 Action determined: {action}")
        
        # Find vendor by GHL contact ID
        logger.info(f"🔍 Searching for vendor with GHL contact ID: {ghl_contact_id}")
        vendor = simple_db_instance.get_vendor_by_ghl_contact_id(ghl_contact_id)
        if not vendor:
            logger.warning(f"⚠️ Vendor not found for GHL contact {ghl_contact_id}")
            
            # Let's also log all vendors to see if there's a mismatch
            all_vendors = simple_db_instance.get_vendors()
            logger.info(f"🔍 Available vendors with GHL contact IDs:")
            for v in all_vendors[:5]:  # Show first 5
                logger.info(f"   - {v.get('name')} (GHL ID: {v.get('ghl_contact_id')})")
            
            raise HTTPException(status_code=404, detail=f"Vendor not found for GHL contact {ghl_contact_id}")
        
        vendor_id = vendor['id']
        vendor_name = vendor.get('name', 'Unknown')
        current_status = vendor.get('taking_new_work', True)
        new_availability = action == "resume"  # True for resume, False for suspend
        
        logger.info(f"✅ Found vendor: {vendor_name} (ID: {vendor_id})")
        logger.info(f"📊 Current taking_new_work status: {current_status}")
        logger.info(f"🔄 Setting taking_new_work to: {new_availability}")
        
        # Test the database method directly like the dashboard does
        logger.info(f"🧪 Testing database update...")
        success = simple_db_instance.update_vendor_availability(vendor_id, new_availability)
        logger.info(f"💾 Database update result: {success}")
        
        # Verify the change took effect
        if success:
            updated_vendor = simple_db_instance.get_vendor_by_id(vendor_id)
            if updated_vendor:
                actual_new_status = updated_vendor.get('taking_new_work')
                logger.info(f"✅ Verification: vendor status is now {actual_new_status}")
                if actual_new_status != new_availability:
                    logger.error(f"❌ MISMATCH: Expected {new_availability}, got {actual_new_status}")
            else:
                logger.error(f"❌ Could not retrieve vendor for verification")
        
        if success:
            # Log the change
            simple_db_instance.log_activity(
                event_type="vendor_availability_toggled",
                event_data={
                    "vendor_id": vendor_id,
                    "vendor_name": vendor_name,
                    "ghl_contact_id": ghl_contact_id,
                    "action": action,
                    "new_availability": new_availability,
                    "source": "ghl_webhook",
                    "tags": tags
                },
                vendor_id=vendor_id,
                success=True
            )
            
            logger.info(f"✅ GHL webhook: {action} for vendor {vendor_name} ({ghl_contact_id})")
            
            return {
                "status": "success",
                "message": f"Vendor {action}ed successfully",
                "vendor_id": vendor_id,
                "vendor_name": vendor_name,
                "action": action,
                "taking_new_work": new_availability
            }
        else:
            logger.error(f"❌ Failed to update vendor availability for {vendor_name}")
            raise HTTPException(status_code=500, detail="Failed to update vendor")
            
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"❌ Error in GHL webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))