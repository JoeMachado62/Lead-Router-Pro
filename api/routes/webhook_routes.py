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
from config import Config

DSP_GHL_LOCATION_ID = Config.GHL_LOCATION_ID
DSP_GHL_API_KEY = Config.GHL_API_KEY
DSP_LOCATION_PIT = Config.GHL_PRIVATE_TOKEN
DSP_AGENCY_API_KEY = Config.GHL_AGENCY_API_KEY

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


def get_form_configuration(form_identifier: str) -> Dict[str, Any]:
    """
    Enhanced form configuration that returns both static data and form metadata.
    This is where you define the behavior for each specific form type.
    """
    
    # CLIENT LEAD FORMS
    if form_identifier == "ceramic_coating_request":
        return {
            "form_type": "client_lead",
            "service_category": "Boat Maintenance",
            "tags": ["New Lead", "Ceramic Coating Request", "DSP Elementor"],
            "source": "Ceramic Coating Request Form (DSP)",
            "priority": "normal",
            "requires_immediate_routing": True,
            "expected_fields": ["firstName", "lastName", "email", "phone", "vessel_make", "vessel_model", "specific_service_needed"]
        }
    elif form_identifier == "yacht_delivery_request":
        return {
            "form_type": "client_lead",
            "service_category": "Boat Hauling and Yacht Delivery",
            "tags": ["New Lead", "Yacht Delivery", "DSP Elementor"],
            "source": "Yacht Delivery Request Form (DSP)",
            "priority": "normal",
            "requires_immediate_routing": True,
            "expected_fields": ["firstName", "lastName", "email", "phone", "vessel_make", "vessel_length_ft", "desired_timeline"]
        }
    elif form_identifier == "emergency_tow_request":
        return {
            "form_type": "client_lead",
            "service_category": "Boat Towing",
            "tags": ["New Lead", "Emergency Tow", "High Priority", "Urgent", "DSP Elementor"],
            "source": "Emergency Tow Request Form (DSP)",
            "priority": "high",
            "requires_immediate_routing": True,
            "expected_fields": ["firstName", "lastName", "email", "phone", "vessel_location__slip", "special_requests__notes"]
        }
    elif form_identifier == "boat_maintenance_request":
        return {
            "form_type": "client_lead",
            "service_category": "Boat Maintenance",
            "tags": ["New Lead", "Boat Maintenance", "DSP Elementor"],
            "source": "Boat Maintenance Request Form (DSP)",
            "priority": "normal",
            "requires_immediate_routing": True,
            "expected_fields": ["firstName", "lastName", "email", "phone", "vessel_make", "specific_service_needed"]
        }
    elif form_identifier == "engine_repair_request":
        return {
            "form_type": "client_lead",
            "service_category": "Engines and Generators",
            "tags": ["New Lead", "Engine Repair", "DSP Elementor"],
            "source": "Engine Repair Request Form (DSP)",
            "priority": "normal",
            "requires_immediate_routing": True,
            "expected_fields": ["firstName", "lastName", "email", "phone", "vessel_make", "vessel_model", "specific_service_needed"]
        }
    
    # VENDOR APPLICATION FORMS
    elif form_identifier == "vendor_application_general":
        return {
            "form_type": "vendor_application",
            "tags": ["New Vendor Application", "General Services", "DSP Elementor"],
            "source": "General Vendor Application Form (DSP)",
            "priority": "normal",
            "requires_immediate_routing": False,
            "expected_fields": ["firstName", "lastName", "email", "phone", "vendor_company_name", "services_provided", "years_in_business"]
        }
    elif form_identifier == "vendor_application_marine_mechanic":
        return {
            "form_type": "vendor_application",
            "primary_service_category": "Engines and Generators",
            "tags": ["New Vendor Application", "Marine Mechanic", "Engine Specialist", "DSP Elementor"],
            "source": "Marine Mechanic Application Form (DSP)",
            "priority": "normal",
            "requires_immediate_routing": False,
            "expected_fields": ["firstName", "lastName", "email", "phone", "vendor_company_name", "services_provided", "years_in_business", "licences__certifications"]
        }
    elif form_identifier == "vendor_application_boat_detailing" or form_identifier == "vendor_application_detailing_specialist":
        return {
            "form_type": "vendor_application", 
            "primary_service_category": "Boat Maintenance",
            "tags": ["New Vendor Application", "Boat Detailing", "Maintenance Specialist", "DSP Elementor"],
            "source": "Boat Detailing Vendor Application Form (DSP)",
            "priority": "normal",
            "requires_immediate_routing": False,
            "expected_fields": ["firstName", "lastName", "email", "phone", "vendor_company_name", "services_provided", "service_zip_codes"]
        }
    elif form_identifier == "join_network_pros":  # Legacy form name - keeping for compatibility
        return {
            "form_type": "vendor_application",
            "tags": ["New Vendor Application", "Network Pros", "DSP Elementor"],
            "source": "Join Network Pros Application Form (DSP)",
            "priority": "normal", 
            "requires_immediate_routing": False,
            "expected_fields": ["firstName", "lastName", "email", "phone", "vendor_company_name", "services_provided"]
        }
    
    # CONTACT/INQUIRY FORMS
    elif form_identifier == "general_contact_inquiry":
        return {
            "form_type": "general_inquiry",
            "tags": ["General Inquiry", "Contact Form", "DSP Elementor"],
            "source": "General Contact Inquiry Form (DSP)",
            "priority": "low",
            "requires_immediate_routing": False,
            "expected_fields": ["firstName", "lastName", "email", "phone", "special_requests__notes"]
        }
    
    # Fallback for unmapped forms - treat as general inquiry
    else:
        logger.warning(f"Unknown form_identifier '{form_identifier}' - using fallback configuration")
        return {
            "form_type": "unknown",
            "tags": ["DSP Elementor", "Unknown Form", form_identifier],
            "source": f"{form_identifier.replace('_', ' ').title()} (DSP)",
            "priority": "low",
            "requires_immediate_routing": False,
            "expected_fields": ["firstName", "lastName", "email"]
        }


def validate_form_submission(form_identifier: str, payload: Dict[str, Any], form_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate form submission against expected fields and requirements.
    Returns validation results and any warnings.
    """
    validation_result = {
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "missing_expected_fields": [],
        "unexpected_fields": [],
        "field_count": len(payload)
    }
    
    # Check for required fields
    required_fields = ["email"]  # Email is always required
    if form_config.get("form_type") == "client_lead":
        required_fields.extend(["firstName", "lastName"])
    elif form_config.get("form_type") == "vendor_application":
        required_fields.extend(["firstName", "lastName", "vendor_company_name"])
    
    for field in required_fields:
        if not payload.get(field):
            validation_result["errors"].append(f"Required field '{field}' is missing or empty")
            validation_result["is_valid"] = False
    
    # Check for expected fields (warnings only)
    expected_fields = form_config.get("expected_fields", [])
    for field in expected_fields:
        if not payload.get(field):
            validation_result["missing_expected_fields"].append(field)
            validation_result["warnings"].append(f"Expected field '{field}' is missing - form may be incomplete")
    
    # Check for unexpected fields (informational)
    for field in payload.keys():
        if field not in VALID_GHL_PAYLOAD_KEYS:
            validation_result["unexpected_fields"].append(field)
            validation_result["warnings"].append(f"Field '{field}' is not recognized and will be ignored")
    
    return validation_result


@router.post("/elementor/{form_identifier}")
async def handle_dsp_elementor_webhook(
    form_identifier: str, 
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Enhanced webhook handler for form-specific Elementor submissions.
    Each form type can have its own configuration, validation, and processing logic.
    """
    start_time = time.time()
    
    try:
        # Parse incoming JSON payload
        elementor_payload = await request.json()
        logger.info(f"📥 DSP Elementor Webhook received for form '{form_identifier}': {json.dumps(elementor_payload, indent=2)}")

        # Get form-specific configuration
        form_config = get_form_configuration(form_identifier)
        logger.info(f"📋 Form config for '{form_identifier}': {form_config}")

        # Validate form submission
        validation_result = validate_form_submission(form_identifier, elementor_payload, form_config)
        if not validation_result["is_valid"]:
            logger.error(f"❌ Form validation failed for '{form_identifier}': {validation_result['errors']}")
            simple_db_instance.log_activity(
                event_type="elementor_webhook_validation_error",
                event_data={
                    "form": form_identifier,
                    "validation_errors": validation_result["errors"],
                    "payload_keys": list(elementor_payload.keys())
                },
                success=False,
                error_message=f"Validation failed: {', '.join(validation_result['errors'])}"
            )
            raise HTTPException(status_code=400, detail=f"Form validation failed: {', '.join(validation_result['errors'])}")
        
        # Log any warnings
        if validation_result["warnings"]:
            logger.warning(f"⚠️ Form validation warnings for '{form_identifier}': {validation_result['warnings']}")

        # Initialize GHL API client using PIT token (confirmed working for contact creation)
        ghl_api_client = GoHighLevelAPI(private_token=DSP_LOCATION_PIT, location_id=DSP_GHL_LOCATION_ID)
        logger.info(f"🔑 Using GHL PIT Token for authentication")

        # Process payload into GHL format - use customFields array
        final_ghl_payload = {}
        custom_fields_array = []
        
        # Create field mapping from field_reference.json (short_key -> field_details)
        field_mapping = {}
        for name, details in ALL_GHL_FIELDS_MAP_FROM_JSON.items():
            if details.get("fieldKey"):
                short_key = details.get("fieldKey").split("contact.")[-1]
                field_mapping[short_key] = {
                    "id": details.get("id"),
                    "fieldKey": details.get("fieldKey"),
                    "name": name
                }

        # Process each field from Elementor payload
        for field_key, field_value in elementor_payload.items():
            # Skip empty values (but allow 0 and False)
            if field_value == "" or field_value is None:
                logger.debug(f"Skipping empty value for field '{field_key}'")
                continue

            # Check if it's a valid GHL field
            if field_key in VALID_GHL_PAYLOAD_KEYS:
                # Standard GHL contact fields go directly in main payload
                if field_key in ["firstName", "lastName", "email", "phone", "companyName", 
                               "address1", "city", "state", "postal_code", "name", 
                               "tags", "notes", "dnd", "country", "source", "website"]:
                    final_ghl_payload[field_key] = field_value
                else:
                    # Custom fields go into customFields array
                    field_details = field_mapping.get(field_key)
                    if field_details and field_details.get("id"):
                        custom_fields_array.append({
                            "id": field_details["id"],
                            "value": str(field_value)
                        })
                        logger.debug(f"Added custom field: {field_details['name']} ({field_key}) = {field_value}")
                    else:
                        logger.warning(f"🚫 Custom field '{field_key}' found in valid keys but missing field ID mapping")
            else:
                logger.warning(f"🚫 Field '{field_key}' from form '{form_identifier}' is not a recognized GHL field. Ignoring.")
        
        # Add form-specific static data from configuration
        for ghl_key, static_value in form_config.items():
            # Skip non-field configuration items
            if ghl_key in ["form_type", "priority", "requires_immediate_routing", "expected_fields"]:
                continue
                
            if ghl_key == "tags":
                # Handle tags merging carefully
                current_tags = final_ghl_payload.get("tags", [])
                if isinstance(current_tags, str):
                    current_tags = [t.strip() for t in current_tags.split(',') if t.strip()]
                elif not isinstance(current_tags, list):
                    current_tags = []
                
                new_tags = static_value if isinstance(static_value, list) else [static_value]
                # Merge and deduplicate tags
                final_ghl_payload["tags"] = list(set(current_tags + new_tags))
                
            elif ghl_key in ["firstName", "lastName", "email", "phone", "companyName", 
                           "address1", "city", "state", "postal_code", "name", 
                           "notes", "dnd", "country", "source", "website"]:
                # Only set standard fields if not already provided by form
                if not final_ghl_payload.get(ghl_key):
                    final_ghl_payload[ghl_key] = static_value
            else:
                # Custom field from form config - add to customFields array if not already present
                field_details = field_mapping.get(ghl_key)
                if field_details and field_details.get("id"):
                    # Check if this field is already in the custom fields array
                    field_exists = any(cf["id"] == field_details["id"] for cf in custom_fields_array)
                    if not field_exists:
                        custom_fields_array.append({
                            "id": field_details["id"],
                            "value": str(static_value)
                        })
                        logger.debug(f"Added static custom field: {field_details['name']} ({ghl_key}) = {static_value}")
        
        # Add customFields array to payload if we have any custom fields
        if custom_fields_array:
            final_ghl_payload["customFields"] = custom_fields_array
            logger.info(f"📝 Added {len(custom_fields_array)} custom fields to payload")
        
        # Ensure email is present and normalized
        if not final_ghl_payload.get("email"):
            logger.error(f"❌ No email provided in payload for form {form_identifier}")
            raise HTTPException(status_code=400, detail="Email is required for processing this form.")

        final_ghl_payload["email"] = final_ghl_payload["email"].lower().strip()

        logger.info(f"🎯 Prepared Final GHL Payload for '{form_identifier}': {json.dumps(final_ghl_payload, indent=2)}")

        # --- GHL API OPERATIONS: Create or Update Contact ---
        existing_ghl_contact = None
        final_ghl_contact_id = None
        operation_successful = False
        action_taken = ""
        api_response_details = None

        # Step 1: Search for existing contact by email
        search_results = ghl_api_client.search_contacts(query=final_ghl_payload["email"], limit=5)
        if search_results:
            for contact_result in search_results:
                if contact_result.get('email', '').lower() == final_ghl_payload["email"]:
                    existing_ghl_contact = contact_result
                    logger.info(f"🔍 Found existing contact via email: {existing_ghl_contact.get('id')}")
                    break

        # Step 2: Update existing contact or create new one
        if existing_ghl_contact:
            # UPDATE EXISTING CONTACT
            final_ghl_contact_id = existing_ghl_contact["id"]
            action_taken = "updated"
            logger.info(f"🔄 Updating existing GHL contact {final_ghl_contact_id} for email {final_ghl_payload.get('email')}")
            
            # Prepare update payload (remove fields not allowed in update)
            update_payload = final_ghl_payload.copy()
            update_payload.pop("locationId", None) 
            update_payload.pop("id", None)

            operation_successful = ghl_api_client.update_contact(final_ghl_contact_id, update_payload)
            if not operation_successful:
                api_response_details = "Update call returned false - check GHL API logs"
                logger.error(f"❌ Failed to update GHL contact {final_ghl_contact_id}")
        else:
            # CREATE NEW CONTACT
            action_taken = "created"
            logger.info(f"➕ Creating new GHL contact for email {final_ghl_payload.get('email')}")
            
            created_contact_response = ghl_api_client.create_contact(final_ghl_payload)
            
            if created_contact_response and not created_contact_response.get("error") and created_contact_response.get("id"):
                final_ghl_contact_id = created_contact_response["id"]
                operation_successful = True
                logger.info(f"✅ Successfully created new GHL contact {final_ghl_contact_id}")
            else:
                # Creation failed - log details and try fallback search
                logger.error(f"❌ Initial GHL contact creation failed: {created_contact_response}")
                api_response_details = created_contact_response
                
                # Fallback: Search again in case of race condition
                logger.info(f"🔄 Attempting fallback search for {final_ghl_payload['email']} after create failure")
                time.sleep(2)  # Brief delay before retry
                
                search_results_after_fail = ghl_api_client.search_contacts(query=final_ghl_payload["email"], limit=1)
                if search_results_after_fail and search_results_after_fail[0].get('email', '').lower() == final_ghl_payload["email"]:
                    # Found contact that may have been created despite error response
                    existing_ghl_contact = search_results_after_fail[0]
                    final_ghl_contact_id = existing_ghl_contact["id"]
                    action_taken = "found_after_apparent_create_fail"
                    logger.info(f"🔍 Found contact {final_ghl_contact_id} via search after initial create appeared to fail")
                    
                    # Try to update it with full payload
                    update_payload = final_ghl_payload.copy()
                    update_payload.pop("locationId", None)
                    update_payload.pop("id", None)
                    
                    operation_successful = ghl_api_client.update_contact(final_ghl_contact_id, update_payload)
                    if not operation_successful:
                        action_taken = "update_after_found_fail"
                        api_response_details = "Update call after finding contact (post-create-fail) returned false"

        # Step 3: Handle success/failure and log results
        processing_time = round(time.time() - start_time, 3)
        
        if operation_successful and final_ghl_contact_id:
            logger.info(f"✅ Successfully {action_taken} GHL contact {final_ghl_contact_id} for form '{form_identifier}' in {processing_time}s")
            
            # Log successful activity to database
            simple_db_instance.log_activity(
                event_type=f"elementor_webhook_{action_taken}",
                event_data={
                    "form": form_identifier,
                    "form_type": form_config.get("form_type"),
                    "ghl_contact_id": final_ghl_contact_id,
                    "elementor_payload_keys": list(elementor_payload.keys()),
                    "service_category": final_ghl_payload.get("customField", {}).get("service_category", form_config.get("service_category")),
                    "processing_time_seconds": processing_time,
                    "validation_warnings": validation_result.get("warnings", [])
                },
                lead_id=final_ghl_contact_id, 
                success=True
            )
            
            # Trigger background tasks based on form type
            if form_config.get("requires_immediate_routing"):
                background_tasks.add_task(
                    trigger_lead_routing_workflow, 
                    ghl_location_id=DSP_GHL_LOCATION_ID,
                    ghl_contact_id=final_ghl_contact_id,
                    form_identifier=form_identifier,
                    form_config=form_config
                )
            
            return {
                "status": "success", 
                "message": f"Webhook processed successfully. GHL contact {final_ghl_contact_id} {action_taken}.",
                "contact_id": final_ghl_contact_id,
                "action": action_taken,
                "form_type": form_config.get("form_type"),
                "processing_time_seconds": processing_time,
                "validation_warnings": validation_result.get("warnings", [])
            }
        else:
            # Operation failed
            error_message = f"Failed to {action_taken} GHL contact for form '{form_identifier}'"
            logger.error(f"❌ {error_message}. API Response: {api_response_details}")
            
            # Log failed activity to database
            simple_db_instance.log_activity(
                event_type="elementor_webhook_ghl_failure",
                event_data={
                    "form": form_identifier,
                    "form_type": form_config.get("form_type"),
                    "error_details": api_response_details,
                    "action_attempted": action_taken,
                    "elementor_payload_keys": list(elementor_payload.keys()),
                    "processing_time_seconds": processing_time
                },
                success=False,
                error_message=f"GHL API interaction failed during contact {action_taken}"
            )
            
            raise HTTPException(
                status_code=502, 
                detail=f"GHL API interaction failed. Could not {action_taken} contact. Details: {api_response_details}"
            )

    except json.JSONDecodeError:
        logger.error(f"❌ Invalid JSON received for Elementor webhook form '{form_identifier}'")
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
        processing_time = round(time.time() - start_time, 3)
        logger.exception(f"💥 Critical error processing DSP Elementor webhook for form '{form_identifier}' after {processing_time}s: {e}")
        simple_db_instance.log_activity(
            event_type="elementor_webhook_exception",
            event_data={
                "form": form_identifier,
                "processing_time_seconds": processing_time,
                "error_class": e.__class__.__name__
            },
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


async def trigger_lead_routing_workflow(ghl_location_id: str, ghl_contact_id: str, form_identifier: str, form_config: Dict[str, Any]):
    """
    Enhanced background task to trigger lead routing workflow based on form type.
    This prepares leads for AI classification and vendor routing.
    """
    logger.info(f"🚀 BACKGROUND TASK: Triggering lead routing for contact {ghl_contact_id} from form '{form_identifier}'")
    
    try:
        # Determine routing priority based on form config
        priority = form_config.get("priority", "normal")
        form_type = form_config.get("form_type", "unknown")
        
        # Log to database for tracking and future processing
        simple_db_instance.log_activity(
            event_type="lead_routing_initiated",
            event_data={
                "ghl_location_id": ghl_location_id,
                "ghl_contact_id": ghl_contact_id,
                "form_identifier": form_identifier,
                "form_type": form_type,
                "priority": priority,
                "service_category": form_config.get("service_category"),
                "timestamp": time.time()
            },
            lead_id=ghl_contact_id,
            success=True
        )
        
        # Future implementation would:
        # 1. Fetch full contact details from GHL using ghl_contact_id
        # 2. Run AI service classification (using ai_classifier.py)
        # 3. Find matching vendors based on service category and location
        # 4. Create opportunities in GHL pipeline
        # 5. Notify vendors via SMS/Email
        # 6. Set up follow-up workflows
        
        logger.info(f"✅ Lead routing workflow initiated for {ghl_contact_id} with priority: {priority}")
        
    except Exception as e:
        logger.error(f"❌ Error in lead routing workflow for {ghl_contact_id}: {e}")
        simple_db_instance.log_activity(
            event_type="lead_routing_workflow_error",
            event_data={
                "ghl_contact_id": ghl_contact_id,
                "form_identifier": form_identifier,
                "error": str(e)
            },
            lead_id=ghl_contact_id,
            success=False,
            error_message=str(e)
        )


# Health check endpoint for webhook system
@router.get("/health")
async def webhook_health_check():
    """Enhanced health check for webhook system"""
    try:
        # Test database connection
        db_stats = simple_db_instance.get_stats()
        db_healthy = True
    except Exception as e:
        db_stats = {"error": str(e)}
        db_healthy = False
    
    return {
        "status": "healthy" if db_healthy else "degraded",
        "webhook_system": "operational",
        "ghl_location_id": DSP_GHL_LOCATION_ID,
        "valid_field_count": len(VALID_GHL_PAYLOAD_KEYS),
        "database_status": "healthy" if db_healthy else "error",
        "database_stats": db_stats,
        "supported_form_types": ["client_lead", "vendor_application", "general_inquiry"],
        "message": "Webhook system ready to receive form-specific Elementor submissions"
    }


# Get supported forms endpoint for documentation
@router.get("/supported-forms")
async def get_supported_forms():
    """Return list of supported form identifiers and their configurations"""
    
    # Get sample configurations for documentation
    sample_forms = [
        "ceramic_coating_request",
        "yacht_delivery_request", 
        "emergency_tow_request",
        "vendor_application_general",
        "vendor_application_marine_mechanic"
    ]
    
    configurations = {}
    for form_id in sample_forms:
        config = get_form_configuration(form_id)
        # Remove sensitive details for public endpoint
        public_config = {
            "form_type": config.get("form_type"),
            "service_category": config.get("service_category"),
            "priority": config.get("priority"),
            "expected_fields": config.get("expected_fields", []),
            "webhook_url": f"/api/v1/webhooks/elementor/{form_id}"
        }
        configurations[form_id] = public_config
    
    return {
        "status": "success",
        "supported_forms": configurations,
        "total_supported": len(configurations),
        "webhook_url_pattern": "/api/v1/webhooks/elementor/{form_identifier}",
        "message": "These are examples of supported form configurations. Contact admin to add new forms."
    }


# GHL Workflow Webhook for Vendor User Creation
@router.post("/ghl/vendor-user-creation")
async def handle_vendor_user_creation_webhook(request: Request):
    """
    Webhook endpoint for GHL workflow to trigger vendor user creation.
    This should be called from the "Vendor Submission : 1749074973147" workflow
    when a vendor application is approved.
    """
    start_time = time.time()
    
    try:
        # Parse incoming GHL workflow webhook payload
        ghl_payload = await request.json()
        logger.info(f"📥 GHL Vendor User Creation Webhook received: {json.dumps(ghl_payload, indent=2)}")
        
        # Extract contact information from GHL payload
        contact_id = ghl_payload.get("contact_id") or ghl_payload.get("contactId")
        if not contact_id:
            logger.error("❌ No contact ID provided in GHL webhook payload")
            raise HTTPException(status_code=400, detail="Contact ID is required")
        
        # Initialize GHL API client with Agency API key for user creation
        ghl_api_client = GoHighLevelAPI(
            private_token=DSP_LOCATION_PIT, 
            location_id=DSP_GHL_LOCATION_ID,
            agency_api_key=DSP_AGENCY_API_KEY
        )
        
        # Get full contact details from GHL
        contact_details = ghl_api_client.get_contact_by_id(contact_id)
        if not contact_details:
            logger.error(f"❌ Could not retrieve contact details for ID: {contact_id}")
            raise HTTPException(status_code=404, detail=f"Contact {contact_id} not found in GHL")
        
        logger.info(f"📋 Retrieved contact details for: {contact_details.get('email')}")
        
        # Extract vendor information from contact
        vendor_email = contact_details.get("email")
        vendor_first_name = contact_details.get("firstName", "")
        vendor_last_name = contact_details.get("lastName", "")
        vendor_phone = contact_details.get("phone", "")
        
        # Extract custom fields for vendor company info
        custom_fields = contact_details.get("customFields", [])
        vendor_company_name = ""
        
        for field in custom_fields:
            if field.get("id") == "JexVrg2VNhnwIX7YlyJV":  # Vendor Company Name field ID
                vendor_company_name = field.get("value", "")
                break
        
        if not vendor_email:
            logger.error(f"❌ No email found for contact {contact_id}")
            raise HTTPException(status_code=400, detail="Vendor email is required for user creation")
        
        # Check if user already exists
        existing_user = ghl_api_client.get_user_by_email(vendor_email)
        if existing_user:
            logger.info(f"✅ User already exists for {vendor_email}: {existing_user.get('id')}")
            
            # Update vendor record with existing user ID
            vendor_record = simple_db_instance.get_vendor_by_email_and_account(vendor_email, DSP_GHL_LOCATION_ID)
            if vendor_record:
                simple_db_instance.update_vendor_status(
                    vendor_record["id"], 
                    "active", 
                    existing_user.get("id")
                )
            
            return {
                "status": "success",
                "message": f"User already exists for vendor {vendor_email}",
                "user_id": existing_user.get("id"),
                "contact_id": contact_id,
                "action": "existing_user_found"
            }
        
        # Create new user data
        user_data = {
            "firstName": vendor_first_name,
            "lastName": vendor_last_name,
            "email": vendor_email,
            "phone": vendor_phone,
            "type": "user",
            "role": "user",
            # Vendor-specific permissions (limited access)
            "permissions": {
                "campaignsEnabled": False,
                "campaignsReadOnly": True,
                "contactsEnabled": True,
                "workflowsEnabled": False,
                "triggersEnabled": False,
                "funnelsEnabled": False,
                "websitesEnabled": False,
                "opportunitiesEnabled": True,
                "dashboardStatsEnabled": True,
                "bulkRequestsEnabled": False,
                "appointmentEnabled": True,
                "reviewsEnabled": False,
                "onlineListingsEnabled": False,
                "phoneCallEnabled": True,
                "conversationsEnabled": True,
                "assignedDataOnly": True,  # Only see their assigned leads
                "adwordsReportingEnabled": False,
                "membershipEnabled": False,
                "facebookAdsReportingEnabled": False,
                "attributionsReportingEnabled": False,
                "settingsEnabled": False,
                "tagsEnabled": False,
                "leadValueEnabled": True,
                "marketingEnabled": False,
                "agentReportingEnabled": True,
                "botService": False,
                "socialPlanner": False,
                "bloggingEnabled": False,
                "invoiceEnabled": False,
                "affiliateManagerEnabled": False,
                "contentAiEnabled": False,
                "refundsEnabled": False,
                "recordPaymentEnabled": False,
                "cancelSubscriptionEnabled": False,
                "paymentsEnabled": False,
                "communitiesEnabled": False,
                "exportPaymentsEnabled": False
            }
        }
        
        # Create user in GHL
        logger.info(f"🔐 Creating GHL user for vendor: {vendor_email}")
        created_user = ghl_api_client.create_user(user_data)
        
        if not created_user or not created_user.get("id"):
            logger.error(f"❌ Failed to create GHL user for {vendor_email}")
            raise HTTPException(status_code=502, detail="Failed to create user in GHL")
        
        user_id = created_user.get("id")
        logger.info(f"✅ Successfully created GHL user: {user_id} for {vendor_email}")
        
        # Update vendor record in database
        vendor_record = simple_db_instance.get_vendor_by_email_and_account(vendor_email, DSP_GHL_LOCATION_ID)
        if vendor_record:
            simple_db_instance.update_vendor_status(vendor_record["id"], "active", user_id)
            logger.info(f"✅ Updated vendor record with user ID: {user_id}")
        else:
            logger.warning(f"⚠️ No vendor record found for {vendor_email} - user created but not linked")
        
        # Log successful activity
        processing_time = round(time.time() - start_time, 3)
        simple_db_instance.log_activity(
            event_type="vendor_user_created",
            event_data={
                "contact_id": contact_id,
                "user_id": user_id,
                "vendor_email": vendor_email,
                "vendor_company": vendor_company_name,
                "processing_time_seconds": processing_time
            },
            lead_id=contact_id,
            success=True
        )
        
        # Send welcome email to vendor (optional)
        welcome_subject = f"Welcome to Dockside Pros - Your Account is Ready!"
        welcome_message = f"""
        <h2>Welcome to Dockside Pros, {vendor_first_name}!</h2>
        
        <p>Your vendor account has been approved and your user credentials have been created.</p>
        
        <p><strong>Company:</strong> {vendor_company_name}</p>
        <p><strong>Email:</strong> {vendor_email}</p>
        
        <p>You can now log in to your vendor portal to:</p>
        <ul>
            <li>View and manage your assigned leads</li>
            <li>Update your availability status</li>
            <li>Communicate with clients</li>
            <li>Track your performance metrics</li>
        </ul>
        
        <p>If you have any questions, please contact our support team.</p>
        
        <p>Welcome aboard!</p>
        <p>The Dockside Pros Team</p>
        """
        
        try:
            ghl_api_client.send_email(contact_id, welcome_subject, welcome_message)
            logger.info(f"📧 Welcome email sent to {vendor_email}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to send welcome email to {vendor_email}: {e}")
        
        return {
            "status": "success",
            "message": f"Successfully created user account for vendor {vendor_email}",
            "user_id": user_id,
            "contact_id": contact_id,
            "vendor_email": vendor_email,
            "vendor_company": vendor_company_name,
            "action": "user_created",
            "processing_time_seconds": processing_time
        }
        
    except json.JSONDecodeError:
        logger.error("❌ Invalid JSON received for vendor user creation webhook")
        simple_db_instance.log_activity(
            event_type="vendor_user_creation_bad_json",
            event_data={},
            success=False,
            error_message="Invalid JSON payload"
        )
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    except HTTPException:
        # Re-raise HTTPExceptions directly
        raise
    
    except Exception as e:
        processing_time = round(time.time() - start_time, 3)
        logger.exception(f"💥 Critical error in vendor user creation webhook after {processing_time}s: {e}")
        simple_db_instance.log_activity(
            event_type="vendor_user_creation_exception",
            event_data={
                "processing_time_seconds": processing_time,
                "error_class": e.__class__.__name__
            },
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
