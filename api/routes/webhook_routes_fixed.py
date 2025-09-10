# api/routes/webhook_routes_fixed.py

"""
FIXED VERSION: Corrected lead routing flow
1. Create GHL contact
2. Create opportunity FIRST
3. Create lead WITH opportunity_id
4. Trigger vendor selection AFTER lead creation
5. Update opportunity with selected vendor
"""

import logging
import json
from typing import Dict, List, Any, Optional
import time
import uuid
import re
import asyncio
from urllib.parse import parse_qs

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

# --- Core Service Imports ---
from config import AppConfig
from database.simple_connection import db as simple_db_instance
from api.services.ghl_api_v2_optimized import OptimizedGoHighLevelAPI
from api.services.field_mapper import field_mapper
from api.services.lead_routing_service import lead_routing_service
from api.services.location_service import location_service
from api.services.service_mapper import (
    get_service_category as get_direct_service_category,
    get_specific_service as get_specific_service_from_form,
)

logger = logging.getLogger(__name__)

async def process_lead_and_assign_vendor(
    lead_id: str,
    account_id: str,
    ghl_opportunity_id: str,
    specific_service_requested: str,
    service_county: str,
    service_state: str,
    service_zip_code: str,
    priority: str = "normal",
    preferred_vendor_id: Optional[str] = None  # For future use
):
    """
    Process lead and assign vendor AFTER lead creation with opportunity_id
    This follows the correct flow:
    1. Lead already exists with opportunity_id
    2. Find matching vendors based on service and location
    3. Select vendor via algorithm
    4. Update lead with vendor assignment
    5. Update GHL opportunity with vendor's GHL User ID
    """
    try:
        logger.info(f"🚀 Starting vendor assignment for lead {lead_id}")
        logger.info(f"   Service: {specific_service_requested}")
        logger.info(f"   Location: {service_county}, {service_state} {service_zip_code}")
        logger.info(f"   Opportunity: {ghl_opportunity_id}")
        
        # Check for preferred vendor (future feature)
        if preferred_vendor_id:
            logger.info(f"📌 Preferred vendor specified: {preferred_vendor_id}")
            # TODO: Implement preferred vendor logic
            # For now, continue with normal selection
        
        # Step 1: Find matching vendors
        matching_vendors = lead_routing_service.find_matching_vendors(
            account_id=account_id,
            service_category=specific_service_requested.split(" - ")[0] if " - " in specific_service_requested else specific_service_requested,
            zip_code=service_zip_code,
            priority=priority,
            specific_service=specific_service_requested
        )
        
        if not matching_vendors:
            logger.warning(f"⚠️ No vendors found for {specific_service_requested} in {service_county}, {service_state}")
            # Could notify admin here
            return {
                "success": False,
                "reason": "no_vendors_found",
                "lead_id": lead_id
            }
        
        logger.info(f"✅ Found {len(matching_vendors)} matching vendors")
        
        # Step 2: Select vendor using configured algorithm
        selected_vendor = lead_routing_service.select_vendor_from_pool(
            matching_vendors, 
            account_id
        )
        
        if not selected_vendor:
            logger.error(f"❌ Vendor selection failed despite having {len(matching_vendors)} matches")
            return {
                "success": False,
                "reason": "selection_failed",
                "lead_id": lead_id
            }
        
        vendor_id = selected_vendor['id']
        vendor_ghl_user_id = selected_vendor.get('ghl_user_id')
        vendor_name = selected_vendor.get('company_name', selected_vendor.get('name', 'Unknown'))
        
        logger.info(f"🎯 Selected vendor: {vendor_name} (ID: {vendor_id}, GHL User: {vendor_ghl_user_id})")
        
        # Step 3: Update lead with vendor assignment in database
        db_assignment_success = simple_db_instance.assign_lead_to_vendor(lead_id, vendor_id)
        
        if not db_assignment_success:
            logger.error(f"❌ Failed to update lead {lead_id} with vendor {vendor_id} in database")
            return {
                "success": False,
                "reason": "database_update_failed",
                "lead_id": lead_id
            }
        
        logger.info(f"✅ Updated lead {lead_id} with vendor {vendor_id} in database")
        
        # Step 4: Update GHL opportunity with vendor assignment
        if vendor_ghl_user_id and ghl_opportunity_id:
            try:
                ghl_api = OptimizedGoHighLevelAPI(
                    private_token=AppConfig.GHL_PRIVATE_TOKEN,
                    location_id=AppConfig.GHL_LOCATION_ID,
                    agency_api_key=AppConfig.GHL_AGENCY_API_KEY
                )
                
                # Update opportunity with vendor assignment
                update_data = {
                    'assignedTo': vendor_ghl_user_id,
                    # Keep existing pipeline and stage
                    'pipelineId': AppConfig.PIPELINE_ID,
                    'pipelineStageId': AppConfig.NEW_LEAD_STAGE_ID
                }
                
                assignment_success = ghl_api.update_opportunity(ghl_opportunity_id, update_data)
                
                if assignment_success:
                    logger.info(f"✅ Successfully assigned GHL opportunity {ghl_opportunity_id} to vendor {vendor_name}")
                    
                    # Log successful assignment
                    simple_db_instance.log_activity(
                        event_type="vendor_assignment_complete",
                        event_data={
                            "lead_id": lead_id,
                            "vendor_id": vendor_id,
                            "vendor_name": vendor_name,
                            "vendor_ghl_user_id": vendor_ghl_user_id,
                            "opportunity_id": ghl_opportunity_id,
                            "service": specific_service_requested,
                            "location": f"{service_county}, {service_state}"
                        },
                        lead_id=lead_id,
                        success=True
                    )
                    
                    return {
                        "success": True,
                        "lead_id": lead_id,
                        "vendor_id": vendor_id,
                        "vendor_name": vendor_name,
                        "opportunity_id": ghl_opportunity_id
                    }
                else:
                    logger.error(f"❌ Failed to update GHL opportunity {ghl_opportunity_id}")
                    # Lead is assigned in DB but not in GHL - this is the issue you were seeing
                    return {
                        "success": False,
                        "reason": "ghl_update_failed",
                        "lead_id": lead_id,
                        "vendor_id": vendor_id  # Vendor was assigned in DB
                    }
                    
            except Exception as e:
                logger.error(f"❌ Error updating GHL opportunity: {e}")
                return {
                    "success": False,
                    "reason": "ghl_error",
                    "error": str(e),
                    "lead_id": lead_id,
                    "vendor_id": vendor_id
                }
        else:
            if not vendor_ghl_user_id:
                logger.warning(f"⚠️ Vendor {vendor_name} has no GHL User ID - cannot assign in GHL")
            if not ghl_opportunity_id:
                logger.warning(f"⚠️ Lead has no opportunity ID - cannot assign in GHL")
            
            return {
                "success": False,
                "reason": "missing_ids",
                "lead_id": lead_id,
                "vendor_id": vendor_id
            }
            
    except Exception as e:
        logger.error(f"❌ Error in vendor assignment process: {e}")
        return {
            "success": False,
            "reason": "process_error",
            "error": str(e),
            "lead_id": lead_id
        }

async def trigger_lead_routing_workflow(
    ghl_contact_id: str,
    form_identifier: str,
    form_config: Dict[str, Any],
    form_data: Dict[str, Any]
):
    """
    CORRECTED FLOW: Background task for lead routing
    1. Contact already exists
    2. Create opportunity FIRST
    3. Create lead WITH opportunity_id
    4. Trigger vendor assignment
    """
    logger.info(f"🚀 BACKGROUND TASK: Processing lead for contact {ghl_contact_id}")
    
    try:
        # Get account ID
        account_id = AppConfig.GHL_LOCATION_ID
        
        # Map form data
        mapped_payload = field_mapper.map_payload(form_data, industry="marine")
        
        # Extract customer data
        customer_data = {
            "name": f"{mapped_payload.get('first_name', '')} {mapped_payload.get('last_name', '')}".strip(),
            "email": mapped_payload.get("email", ""),
            "phone": mapped_payload.get("phone", "")
        }
        
        # Get service details
        service_category = get_direct_service_category(form_identifier)
        specific_service = mapped_payload.get("specific_service_needed", "")
        if not specific_service:
            specific_service = get_specific_service_from_form(form_identifier)
        
        # Get location details
        zip_code = mapped_payload.get("zip_code_of_service", "")
        service_county = ""
        service_state = ""
        
        if zip_code:
            location_data = location_service.zip_to_location(zip_code)
            if not location_data.get('error'):
                service_county = location_data.get('county', '')
                service_state = location_data.get('state', '')
                logger.info(f"📍 Resolved location: {zip_code} → {service_county}, {service_state}")
        
        # STEP 1: Create opportunity FIRST (before lead)
        opportunity_id = None
        form_type = form_config.get("form_type", "unknown")
        
        if form_type in ["client_lead", "emergency_service"]:
            if AppConfig.PIPELINE_ID and AppConfig.NEW_LEAD_STAGE_ID:
                logger.info(f"📈 Creating opportunity for {service_category} lead")
                
                ghl_api = OptimizedGoHighLevelAPI(
                    private_token=AppConfig.GHL_PRIVATE_TOKEN,
                    location_id=AppConfig.GHL_LOCATION_ID,
                    agency_api_key=AppConfig.GHL_AGENCY_API_KEY
                )
                
                opportunity_data = {
                    'contactId': ghl_contact_id,
                    'pipelineId': AppConfig.PIPELINE_ID,
                    'pipelineStageId': AppConfig.NEW_LEAD_STAGE_ID,
                    'name': f"{customer_data['name']} - {service_category}",
                    'monetaryValue': 0,
                    'status': 'open',
                    'source': f"{form_identifier} (DSP)",
                    'locationId': AppConfig.GHL_LOCATION_ID,
                    # Note: NOT setting assignedTo here - will be set after vendor selection
                }
                
                opportunity_response = ghl_api.create_opportunity(opportunity_data)
                
                if opportunity_response and opportunity_response.get('id'):
                    opportunity_id = opportunity_response['id']
                    logger.info(f"✅ Created opportunity: {opportunity_id}")
                else:
                    logger.error(f"❌ Failed to create opportunity")
                    return
        
        # STEP 2: Create lead WITH opportunity_id
        lead_id = str(uuid.uuid4())
        
        try:
            conn = simple_db_instance.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO leads (
                    id, account_id, ghl_contact_id, ghl_opportunity_id, customer_name,
                    customer_email, customer_phone, primary_service_category, specific_service_requested,
                    customer_zip_code, service_county, service_state, vendor_id, 
                    assigned_at, status, priority, source, service_details, 
                    service_zip_code, service_city, specific_services,
                    service_complexity, estimated_duration, requires_emergency_response, 
                    classification_confidence, classification_reasoning
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                lead_id,
                account_id,
                ghl_contact_id,
                opportunity_id,  # NOW we have the opportunity_id!
                customer_data.get("name", ""),
                customer_data.get("email", ""),
                customer_data.get("phone", ""),
                service_category,
                specific_service,  # Critical for vendor matching
                zip_code,
                service_county,    # Critical for vendor matching
                service_state,
                None,  # vendor_id - will be set by vendor assignment
                None,  # assigned_at - will be set by vendor assignment
                "pending_assignment",  # status - indicates awaiting vendor
                form_config.get("priority", "normal"),
                f"{form_identifier} (DSP)",
                json.dumps({}),
                zip_code,
                "",
                "[]",
                "simple",
                "medium",
                form_type == "emergency_service",
                1.0,
                "Direct form mapping"
            ))
            
            conn.commit()
            logger.info(f"✅ Lead created with ID: {lead_id} and opportunity_id: {opportunity_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to create lead: {e}")
            if conn:
                conn.close()
            return
        finally:
            if conn:
                conn.close()
        
        # STEP 3: Trigger vendor assignment (only if we have required data)
        if opportunity_id and specific_service and (service_county or zip_code):
            logger.info(f"🎯 Triggering vendor assignment for lead {lead_id}")
            
            # Check for preferred vendor in form data
            preferred_vendor = mapped_payload.get("preferred_vendor_id")
            
            # Run vendor assignment
            assignment_result = await process_lead_and_assign_vendor(
                lead_id=lead_id,
                account_id=account_id,
                ghl_opportunity_id=opportunity_id,
                specific_service_requested=specific_service,
                service_county=service_county,
                service_state=service_state,
                service_zip_code=zip_code,
                priority=form_config.get("priority", "normal"),
                preferred_vendor_id=preferred_vendor
            )
            
            if assignment_result['success']:
                logger.info(f"✅ Lead routing completed successfully for {ghl_contact_id}")
            else:
                logger.warning(f"⚠️ Lead routing completed with issues: {assignment_result.get('reason')}")
        else:
            logger.warning(f"⚠️ Missing required data for vendor assignment:")
            logger.warning(f"   Opportunity ID: {opportunity_id}")
            logger.warning(f"   Specific Service: {specific_service}")
            logger.warning(f"   Service County: {service_county}")
            logger.warning(f"   ZIP Code: {zip_code}")
            
    except Exception as e:
        logger.error(f"❌ Error in lead routing workflow: {e}")
        simple_db_instance.log_activity(
            event_type="lead_routing_error",
            event_data={
                "ghl_contact_id": ghl_contact_id,
                "form_identifier": form_identifier,
                "error": str(e)
            },
            lead_id=ghl_contact_id,
            success=False,
            error_message=str(e)
        )