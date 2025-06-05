# api/routes/webhook_routes.py

import logging
import json
from typing import Dict, List, Any, Optional
import time
import uuid

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks

# Using your simple_connection.py (direct SQLite)
from database.simple_connection import db as simple_db_instance 

# GHL API Interaction
from api.services.ghl_api import GoHighLevelAPI

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/webhooks", tags=["Elementor Webhooks (DSP)"])

# --- DSP Specific Configuration ---
DSP_GHL_LOCATION_ID = 'ilmrtA1Vk6rvcy4BswKg'
DSP_LOCATION_PIT = 'pit-c361d89c-d943-4812-9839-8e3223c2f31a'

# --- Load GHL field mapping from field_reference.json ---
VALID_GHL_PAYLOAD_KEYS = set()

try:
    with open("field_reference.json", "r") as f:
        FIELD_REFERENCE_DATA = json.load(f)
    ALL_GHL_FIELDS_MAP_FROM_JSON = FIELD_REFERENCE_DATA.get("all_ghl_fields", {})
    
    # Extract all custom field API keys from field_reference.json
    for name, details in ALL_GHL_FIELDS_MAP_FROM_JSON.items():
        if details.get("fieldKey"):
            api_key = details.get("fieldKey").split("contact.")[-1]
            VALID_GHL_PAYLOAD_KEYS.add(api_key)

    # Add standard GHL contact fields
    standard_ghl_fields = {
        "firstName", "lastName", "email", "phone", "companyName", 
        "address1", "city", "state", "postal_code", "name",
        "tags", "notes", "dnd", "country", "source", "website"
    }
    VALID_GHL_PAYLOAD_KEYS.update(standard_ghl_fields)
    
    logger.info(f"Loaded {len(VALID_GHL_PAYLOAD_KEYS)} valid GHL field keys from field_reference.json")
    
except FileNotFoundError:
    logger.error("CRITICAL: field_reference.json not found! Webhook field mapping will be severely impaired.")
    # Add minimal fallback fields
    VALID_GHL_PAYLOAD_KEYS = {
        "firstName", "lastName", "email", "phone", "companyName", 
        "address1", "city", "state", "postal_code", "name",
        "tags", "notes", "source", "service_category"
    }
except Exception as e:
    logger.error(f"Error loading or processing field_reference.json: {e}")
    # Add minimal fallback fields
    VALID_GHL_PAYLOAD_KEYS = {
        "firstName", "lastName", "email", "phone", "companyName", 
        "address1", "city", "state", "postal_code", "name",
        "tags", "notes", "source", "service_category"
    }

def get_static_data_for_form(form_identifier: str) -> Dict[str, Any]:
    """
    Returns static data to be merged into the GHL payload.
    Keys here MUST be the GHL API payload keys.
    """
    
    if form_identifier == "ceramic_coating_request":
        return {
            "service_category": "Boat Maintenance", 
            "tags": ["New Lead", "Ceramic Coating Request", "DSP Elementor"],
            "source": "Ceramic Coating Lead Form (DSP)"
        }
    elif form_identifier == "join_network_pros":  # Vendor Application
        return {
            "tags": ["New Vendor Application", "DSP Elementor"],
            "source": "Vendor Network Application Form (DSP)"
        }
    elif form_identifier == "yacht_delivery_request":
        return {
            "service_category": "Boat Hauling and Yacht Delivery",
            "tags": ["New Lead", "Yacht Delivery Request", "DSP Elementor"],
            "source": "Yacht Delivery Request Form (DSP)"
        }
    elif form_identifier == "boat_maintenance_request":
        return {
            "service_category": "Boat Maintenance",
            "tags": ["New Lead", "Boat Maintenance Request", "DSP Elementor"],
            "source": "Boat Maintenance Request Form (DSP)"
        }
    elif form_identifier == "emergency_tow_request":
        return {
            "service_category": "Boat Towing",
            "tags": ["New Lead", "Emergency Tow", "High Priority", "DSP Elementor"],
            "source": "Emergency Tow Request Form (DSP)"
        }
    
    # Fallback for unmapped forms
    return {
        "tags": ["DSP Elementor", form_identifier], 
        "source": f"{form_identifier.replace('_', ' ').title()} (DSP)"
    }


@router.post("/elementor/{form_identifier}")
async def handle_dsp_elementor_webhook(
    form_identifier: str, 
    request: Request,
    background_tasks: BackgroundTasks
):
    try:
        elementor_payload = await request.json()
        logger.info(f"DSP Elementor Webhook received for form '{form_identifier}': {json.dumps(elementor_payload, indent=2)}")

        # Initialize GHL API client
        ghl_api_client = GoHighLevelAPI(private_token=DSP_LOCATION_PIT, location_id=DSP_GHL_LOCATION_ID)

        ghl_payload_standard_fields = {} 
        ghl_payload_custom_fields = {} 

        # Process Elementor payload - keys should already be GHL API keys thanks to Custom ID setup
        for field_key, field_value in elementor_payload.items():
            # Skip empty values (but allow 0)
            if not field_value and field_value != 0:
                logger.debug(f"Skipping empty value for Elementor key '{field_key}'")
                continue

            # Check if it's a valid GHL field
            if field_key in VALID_GHL_PAYLOAD_KEYS:
                # Standard GHL contact fields go directly in main payload
                if field_key in ["firstName", "lastName", "email", "phone", "companyName", 
                               "address1", "city", "state", "postal_code", "name", 
                               "tags", "notes", "dnd", "country", "source", "website"]:
                    ghl_payload_standard_fields[field_key] = field_value
                else:
                    # Custom fields go in customField object and should be strings
                    ghl_payload_custom_fields[field_key] = str(field_value)
            else:
                logger.warning(f"Elementor key '{field_key}' from form '{form_identifier}' is not a recognized GHL field. It will be ignored.")
        
        # Add static data for this specific form type
        static_data = get_static_data_for_form(form_identifier)
        for ghl_key, static_value in static_data.items():
            if ghl_key == "tags":
                # Handle tags merging carefully
                current_tags = ghl_payload_standard_fields.get("tags", [])
                if isinstance(current_tags, str):
                    current_tags = [t.strip() for t in current_tags.split(',') if t.strip()]
                elif not isinstance(current_tags, list):
                    current_tags = []
                
                new_tags = static_value if isinstance(static_value, list) else [static_value]
                # Merge and deduplicate tags
                ghl_payload_standard_fields["tags"] = list(set(current_tags + new_tags))
                
            elif ghl_key in ["firstName", "lastName", "email", "phone", "companyName", 
                           "address1", "city", "state", "postal_code", "name", 
                           "notes", "dnd", "country", "source", "website"]:
                # Only set standard fields if not already provided by form
                if not ghl_payload_standard_fields.get(ghl_key):
                    ghl_payload_standard_fields[ghl_key] = static_value
            else:
                # Custom field - only set if not already provided by form
                if not ghl_payload_custom_fields.get(ghl_key):
                    ghl_payload_custom_fields[ghl_key] = str(static_value)
        
        # Build final GHL payload structure
        final_ghl_payload = ghl_payload_standard_fields.copy()
        if ghl_payload_custom_fields:
            final_ghl_payload["customField"] = ghl_payload_custom_fields
        
        # Validate required email field
        if not final_ghl_payload.get("email"):
            logger.error(f"No email provided in payload for form {form_identifier}. Cannot reliably create/update contact.")
            simple_db_instance.log_activity(
                event_type="elementor_webhook_error",
                event_data={
                    "form": form_identifier, 
                    "error": "Missing email in payload", 
                    "payload_preview": {k: v for k, v in elementor_payload.items() if k in ['firstName', 'lastName']}
                },
                success=False, 
                error_message="Missing email in payload"
            )
            raise HTTPException(status_code=400, detail="Email is required for processing this form.")

        # Normalize email
        final_ghl_payload["email"] = final_ghl_payload["email"].lower().strip()

        logger.info(f"Prepared Final GHL Payload for '{form_identifier}': {json.dumps(final_ghl_payload, indent=2)}")

        # --- GHL API OPERATIONS: Create or Update Contact ---
        existing_ghl_contact = None
        final_ghl_contact_id = None
        operation_successful = False
        action_taken = ""
        api_response_details = None

        # Step 1: Search for existing contact by email
        if final_ghl_payload.get("email"):
            search_results = ghl_api_client.search_contacts(query=final_ghl_payload["email"], limit=5)
            if search_results:
                for contact_result in search_results:
                    if contact_result.get('email', '').lower() == final_ghl_payload["email"]:
                        existing_ghl_contact = contact_result
                        logger.info(f"Found existing contact via email: {existing_ghl_contact.get('id')}")
                        break

        # Step 2: Update existing contact or create new one
        if existing_ghl_contact:
            # UPDATE EXISTING CONTACT
            final_ghl_contact_id = existing_ghl_contact["id"]
            action_taken = "updated"
            logger.info(f"Updating existing GHL contact {final_ghl_contact_id} for email {final_ghl_payload.get('email')}")
            
            # Prepare update payload (remove fields not allowed in update)
            update_payload = final_ghl_payload.copy()
            update_payload.pop("locationId", None) 
            update_payload.pop("id", None)

            operation_successful = ghl_api_client.update_contact(final_ghl_contact_id, update_payload)
            if not operation_successful:
                api_response_details = "Update call returned false - check GHL API logs"
                logger.error(f"Failed to update GHL contact {final_ghl_contact_id}")
        else:
            # CREATE NEW CONTACT
            action_taken = "created"
            logger.info(f"Creating new GHL contact for email {final_ghl_payload.get('email')}")
            
            created_contact_response = ghl_api_client.create_contact(final_ghl_payload)
            
            if created_contact_response and not created_contact_response.get("error") and created_contact_response.get("id"):
                final_ghl_contact_id = created_contact_response["id"]
                operation_successful = True
                logger.info(f"Successfully created new GHL contact {final_ghl_contact_id}")
            else:
                # Creation failed - log details and try fallback search
                logger.error(f"Initial GHL contact creation failed: {created_contact_response}")
                api_response_details = created_contact_response
                
                # Fallback: Search again in case of race condition
                logger.info(f"Attempting fallback search for {final_ghl_payload['email']} after create failure")
                time.sleep(2)  # Brief delay before retry
                
                search_results_after_fail = ghl_api_client.search_contacts(query=final_ghl_payload["email"], limit=1)
                if search_results_after_fail and search_results_after_fail[0].get('email', '').lower() == final_ghl_payload["email"]:
                    # Found contact that may have been created despite error response
                    existing_ghl_contact = search_results_after_fail[0]
                    final_ghl_contact_id = existing_ghl_contact["id"]
                    action_taken = "found_after_apparent_create_fail"
                    logger.info(f"Found contact {final_ghl_contact_id} via search after initial create appeared to fail")
                    
                    # Try to update it with full payload
                    update_payload = final_ghl_payload.copy()
                    update_payload.pop("locationId", None)
                    update_payload.pop("id", None)
                    
                    operation_successful = ghl_api_client.update_contact(final_ghl_contact_id, update_payload)
                    if not operation_successful:
                        action_taken = "update_after_found_fail"
                        api_response_details = "Update call after finding contact (post-create-fail) returned false"

        # Step 3: Handle success/failure and log results
        if operation_successful and final_ghl_contact_id:
            logger.info(f"✅ Successfully {action_taken} GHL contact {final_ghl_contact_id} for form '{form_identifier}'")
            
            # Log successful activity to database
            simple_db_instance.log_activity(
                event_type=f"elementor_webhook_{action_taken}",
                event_data={
                    "form": form_identifier, 
                    "ghl_contact_id": final_ghl_contact_id, 
                    "elementor_payload_keys": list(elementor_payload.keys()),
                    "service_category": final_ghl_payload.get("customField", {}).get("service_category", "Unknown")
                },
                lead_id=final_ghl_contact_id, 
                success=True
            )
            
            # Optional: Trigger background task for lead routing
            # This would be called later by GHL workflow webhooks back to your system
            if "New Lead" in final_ghl_payload.get("tags", []):
                background_tasks.add_task(
                    log_lead_for_routing, 
                    ghl_location_id=DSP_GHL_LOCATION_ID,
                    ghl_contact_id=final_ghl_contact_id,
                    form_identifier=form_identifier
                )
            
            return {
                "status": "success", 
                "message": f"Webhook processed successfully. GHL contact {final_ghl_contact_id} {action_taken}.",
                "contact_id": final_ghl_contact_id,
                "action": action_taken
            }
        else:
            # Operation failed
            error_message = f"Failed to {action_taken} GHL contact for form '{form_identifier}'"
            logger.error(f"{error_message}. API Response: {api_response_details}")
            
            # Log failed activity to database
            simple_db_instance.log_activity(
                event_type="elementor_webhook_ghl_failure",
                event_data={
                    "form": form_identifier, 
                    "error_details": api_response_details, 
                    "action_attempted": action_taken, 
                    "elementor_payload_keys": list(elementor_payload.keys())
                },
                success=False,
                error_message=f"GHL API interaction failed during contact {action_taken}"
            )
            
            raise HTTPException(
                status_code=502, 
                detail=f"GHL API interaction failed. Could not {action_taken} contact. Details: {api_response_details}"
            )

    except json.JSONDecodeError:
        logger.error(f"Invalid JSON received for Elementor webhook form '{form_identifier}'")
        simple_db_instance.log_activity(
            event_type="elementor_webhook_bad_json",
            event_data={"form": form_identifier},
            success=False,
            error_message="Invalid JSON payload"
        )
        raise HTTPException(status_code=400, detail="Invalid JSON payload.")
    
    except HTTPException:
        # Re-raise HTTPExceptions directly (don't wrap them)
        raise
    
    except Exception as e:
        logger.exception(f"Critical error processing DSP Elementor webhook for form '{form_identifier}': {e}")
        simple_db_instance.log_activity(
            event_type="elementor_webhook_exception",
            event_data={"form": form_identifier},
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


async def log_lead_for_routing(ghl_location_id: str, ghl_contact_id: str, form_identifier: str):
    """
    Background task to log lead information for potential routing.
    In a full implementation, this might trigger AI classification and vendor routing.
    """
    logger.info(f"BACKGROUND TASK: Logging lead {ghl_contact_id} from form '{form_identifier}' for potential routing")
    
    try:
        # Log to database for tracking
        simple_db_instance.log_activity(
            event_type="lead_ready_for_routing",
            event_data={
                "ghl_location_id": ghl_location_id,
                "ghl_contact_id": ghl_contact_id,
                "form_identifier": form_identifier,
                "timestamp": time.time()
            },
            lead_id=ghl_contact_id,
            success=True
        )
        
        # In the future, this is where you might:
        # 1. Fetch full contact details from GHL
        # 2. Run AI service classification
        # 3. Find matching vendors
        # 4. Create opportunities in GHL
        # 5. Notify vendors
        
    except Exception as e:
        logger.error(f"Error in lead routing background task: {e}")


# Optional: Health check endpoint for webhooks
@router.get("/health")
async def webhook_health_check():
    """Health check for webhook system"""
    return {
        "status": "healthy",
        "webhook_system": "operational",
        "ghl_location_id": DSP_GHL_LOCATION_ID,
        "valid_field_count": len(VALID_GHL_PAYLOAD_KEYS),
        "message": "Webhook system ready to receive Elementor form submissions"
    }