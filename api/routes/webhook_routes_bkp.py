# api/routes/webhook_routes.py

import logging
import json
from typing import Dict, List, Any, Optional
import time
import uuid
import re
from config import AppConfig # Import the final config object

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks

# Using your simple_connection.py (direct SQLite)
from database.simple_connection import db as simple_db_instance 

# GHL API Interaction
from api.services.ghl_api import GoHighLevelAPI

# AI Service Classification
from api.services.ai_classifier import AIServiceClassifier

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/webhooks", tags=["Enhanced Elementor Webhooks (DSP)"])

# --- DSP Specific Configuration ---
from config import Config

DSP_GHL_LOCATION_ID = Config.GHL_LOCATION_ID
DSP_GHL_API_KEY = Config.GHL_API_KEY
DSP_LOCATION_PIT = Config.GHL_PRIVATE_TOKEN
DSP_AGENCY_API_KEY = Config.GHL_AGENCY_API_KEY

# --- Load GHL field mapping from field_reference.json ---
VALID_GHL_PAYLOAD_KEYS = set()
ALL_GHL_FIELDS_MAP_FROM_JSON = {}
FIELD_MAPPING = {}

try:
    with open("field_reference.json", "r") as f:
        FIELD_REFERENCE_DATA = json.load(f)
    ALL_GHL_FIELDS_MAP_FROM_JSON = FIELD_REFERENCE_DATA.get("all_ghl_fields", {})
    
    # Extract all custom field API keys from field_reference.json
    for name, details in ALL_GHL_FIELDS_MAP_FROM_JSON.items():
        if details.get("fieldKey"):
            api_key = details.get("fieldKey").split("contact.")[-1]
            VALID_GHL_PAYLOAD_KEYS.add(api_key)
            # Create reverse mapping for easy lookup
            FIELD_MAPPING[api_key] = {
                "id": details.get("id"),
                "fieldKey": details.get("fieldKey"),
                "name": name,
                "dataType": details.get("dataType")
            }

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

# --- Enhanced Service Category Mapping (All 17 Categories) ---
COMPLETE_SERVICE_CATEGORIES = {
    "boat_maintenance": {
        "name": "Boat Maintenance",
        "keywords": ["ceramic", "detailing", "cleaning", "oil change", "bilge", "maintenance", "wash", "wax", "bottom"],
        "subcategories": ["ceramic_coating", "boat_detailing", "bottom_cleaning", "oil_change", "bilge_cleaning", 
                         "jet_ski_maintenance", "barnacle_cleaning", "fire_detection", "boat_wrapping"]
    },
    "marine_systems": {
        "name": "Marine Systems", 
        "keywords": ["electrical", "plumbing", "hvac", "ac", "systems", "instrument", "lighting", "stabilizers"],
        "subcategories": ["electrical_service", "plumbing", "ac_sales", "ac_service", "sound_systems", 
                         "lighting", "refrigeration", "watermakers", "stabilizers", "dashboard"]
    },
    "engines_generators": {
        "name": "Engines and Generators",
        "keywords": ["engine", "generator", "motor", "outboard", "inboard", "service", "sales"],
        "subcategories": ["engine_service", "engine_sales", "generator_service", "generator_sales"]
    },
    "boat_yacht_repair": {
        "name": "Boat and Yacht Repair", 
        "keywords": ["repair", "fiberglass", "welding", "carpentry", "canvas", "upholstery", "decking", "flooring"],
        "subcategories": ["fiberglass_repair", "welding_fabrication", "carpentry_woodwork", "riggers_masts",
                         "jet_ski_repair", "canvas_upholstery", "decking_flooring"]
    },
    "boat_hauling_delivery": {
        "name": "Boat Hauling and Yacht Delivery",
        "keywords": ["delivery", "transport", "hauling", "yacht_delivery", "boat_transport"],
        "subcategories": ["yacht_delivery", "boat_hauling", "boat_transport"]
    },
    "boat_towing": {
        "name": "Boat Towing", 
        "keywords": ["towing", "emergency", "tow", "breakdown"],
        "subcategories": ["emergency_tow", "towing_membership"]
    },
    "boat_charters_rentals": {
        "name": "Boat Charters and Rentals",
        "keywords": ["charter", "rental", "fishing", "dive", "sailboat", "catamaran", "efoil"],
        "subcategories": ["boat_charters", "boat_clubs", "fishing_charters", "yacht_charters", 
                         "sailboat_charters", "efoil_kiteboarding", "dive_equipment"]
    },
    "buying_selling_boats": {
        "name": "Buying or Selling a Boat",
        "keywords": ["buy", "sell", "broker", "dealer", "insurance", "financing", "surveyor"],
        "subcategories": ["boat_sales", "boat_insurance", "yacht_insurance", "boat_broker", 
                         "yacht_broker", "boat_financing", "boat_surveyors", "yacht_dealers", "boat_dealers"]
    },
    "dock_slip_rental": {
        "name": "Dock and Slip Rental",
        "keywords": ["dock", "slip", "marina", "rent", "rental"],
        "subcategories": ["dock_slip_rental", "rent_my_dock"]
    },
    "docks_seawalls_lifts": {
        "name": "Docks, Seawalls and Lifts",
        "keywords": ["dock build", "seawall", "lift", "floating", "davit", "hydraulic"],
        "subcategories": ["dock_seawall_builders", "boat_lift_installers", "floating_dock_sales",
                         "davit_hydraulic", "hull_dock_cleaning"]
    },
    "fuel_delivery": {
        "name": "Fuel Delivery",
        "keywords": ["fuel", "gas", "diesel", "delivery"],
        "subcategories": ["fuel_delivery"]
    },
    "boater_resources": {
        "name": "Boater Resources", 
        "keywords": ["parts", "wifi", "provisioning", "photography", "crew", "advertising", "accounting"],
        "subcategories": ["yacht_wifi", "provisioning", "yacht_parts", "yacht_photography", 
                         "yacht_videography", "maritime_advertising", "yacht_crew", "yacht_accounting", "boat_salvage"]
    },
    "maritime_education": {
        "name": "Maritime Education and Training",
        "keywords": ["education", "training", "captain", "lessons"],
        "subcategories": ["maritime_education"]
    },
    "waterfront_property": {
        "name": "Waterfront Property",
        "keywords": ["waterfront", "property", "homes", "real estate"],
        "subcategories": ["waterfront_homes_sale", "sell_waterfront_home", "waterfront_developments"]
    },
    "yacht_management": {
        "name": "Yacht Management",
        "keywords": ["management", "yacht_management"],
        "subcategories": ["yacht_management"]
    },
    "wholesale_dealer": {
        "name": "Wholesale or Dealer Product Pricing",
        "keywords": ["wholesale", "dealer", "pricing"],
        "subcategories": ["wholesale_dealer_pricing"]
    },
    "general_forms": {
        "name": "General",
        "keywords": ["subscribe", "email", "network", "contact", "inquiry"],
        "subcategories": ["email_subscribe", "join_network", "general_contact"]
    }
}

def extract_service_category_from_form_identifier(form_identifier: str) -> str:
    """
    Extract service category from form identifier using intelligent matching
    """
    form_lower = form_identifier.lower()
    
    # Direct category matches
    for category_key, category_data in COMPLETE_SERVICE_CATEGORIES.items():
        if category_key in form_lower:
            return category_data["name"]
        
        # Check subcategories
        for subcategory in category_data.get("subcategories", []):
            if subcategory in form_lower:
                return category_data["name"]
        
        # Check keywords
        for keyword in category_data.get("keywords", []):
            if keyword in form_lower:
                return category_data["name"]
    
    # Specific form pattern matching
    if "ceramic" in form_lower or "coating" in form_lower:
        return "Boat Maintenance"
    elif "emergency" in form_lower or "tow" in form_lower:
        return "Boat Towing"
    elif "delivery" in form_lower or "transport" in form_lower:
        return "Boat Hauling and Yacht Delivery"
    elif "engine" in form_lower or "generator" in form_lower:
        return "Engines and Generators"
    elif "vendor" in form_lower or "network" in form_lower:
        return "General"
    elif "maintenance" in form_lower or "detailing" in form_lower:
        return "Boat Maintenance"
    elif "repair" in form_lower:
        return "Boat and Yacht Repair"
    elif "charter" in form_lower or "rental" in form_lower:
        return "Boat Charters and Rentals"
    
    # Default fallback
    return "Boater Resources"

def get_dynamic_form_configuration(form_identifier: str) -> Dict[str, Any]:
    """
    Enhanced dynamic form configuration that handles any form intelligently
    """
    
    # Extract service category
    service_category = extract_service_category_from_form_identifier(form_identifier)
    
    # Determine form type based on identifier patterns
    form_type = "unknown"
    priority = "normal"
    requires_immediate_routing = False
    
    if any(keyword in form_identifier.lower() for keyword in ["vendor", "network", "join", "application"]):
        form_type = "vendor_application"
        requires_immediate_routing = False
        priority = "normal"
    elif any(keyword in form_identifier.lower() for keyword in ["emergency", "tow", "breakdown", "urgent"]):
        form_type = "emergency_service"
        requires_immediate_routing = True
        priority = "high"
    elif any(keyword in form_identifier.lower() for keyword in ["subscribe", "email", "contact", "inquiry"]):
        form_type = "general_inquiry"
        requires_immediate_routing = False
        priority = "low"
    else:
        form_type = "client_lead"
        requires_immediate_routing = True
        priority = "normal"
    
    # Generate appropriate tags
    tags = [service_category, "DSP Elementor"]
    if form_type == "emergency_service":
        tags.extend(["Emergency", "High Priority", "Urgent"])
    elif form_type == "vendor_application":
        tags.extend(["New Vendor Application"])
    else:
        tags.extend(["New Lead"])
    
    # Generate source description
    source_name = form_identifier.replace("_", " ").title()
    if not source_name.endswith("(DSP)"):
        source_name += " (DSP)"
    
    return {
        "form_type": form_type,
        "service_category": service_category,
        "tags": tags,
        "source": source_name,
        "priority": priority,
        "requires_immediate_routing": requires_immediate_routing,
        "expected_fields": get_expected_fields_for_form_type(form_type)
    }

def get_expected_fields_for_form_type(form_type: str) -> List[str]:
    """Return expected fields based on form type"""
    base_fields = ["firstName", "lastName", "email", "phone"]
    
    if form_type == "client_lead":
        return base_fields + ["zip_code_of_service", "specific_service_needed", "desired_timeline", "special_requests__notes"]
    elif form_type == "vendor_application":
        return base_fields + ["vendor_company_name", "services_provided", "service_zip_codes", "years_in_business"]
    elif form_type == "emergency_service":
        return base_fields + ["vessel_location__slip", "special_requests__notes", "zip_code_of_service"]
    else:
        return base_fields

def validate_form_submission(form_identifier: str, payload: Dict[str, Any], form_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhanced validation for any form submission
    """
    validation_result = {
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "missing_expected_fields": [],
        "unexpected_fields": [],
        "field_count": len(payload)
    }
    
    # Check for required fields based on form type
    required_fields = ["email"]  # Email is always required
    form_type = form_config.get("form_type")
    
    if form_type in ["client_lead", "emergency_service"]:
        required_fields.extend(["firstName", "lastName"])
    elif form_type == "vendor_application":
        required_fields.extend(["firstName", "lastName", "vendor_company_name"])
    
    # Validate required fields
    for field in required_fields:
        if not payload.get(field) or str(payload.get(field)).strip() == "":
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
    
    # Validate email format
    email = payload.get("email", "")
    if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        validation_result["errors"].append("Invalid email format")
        validation_result["is_valid"] = False
    
    return validation_result

def process_payload_to_ghl_format(elementor_payload: Dict[str, Any], form_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process Elementor payload into GHL format with custom fields array
    """
    final_ghl_payload = {}
    custom_fields_array = []
    
    # Standard GHL contact fields
    standard_fields = {
        "firstName", "lastName", "email", "phone", "companyName", 
        "address1", "city", "state", "postal_code", "name",
        "tags", "notes", "dnd", "country", "source", "website"
    }
    
    # Process each field from Elementor payload
    for field_key, field_value in elementor_payload.items():
        # Skip empty values (but allow 0 and False)
        if field_value == "" or field_value is None:
            logger.debug(f"Skipping empty value for field '{field_key}'")
            continue
        
        # Check if it's a valid GHL field
        if field_key in VALID_GHL_PAYLOAD_KEYS:
            if field_key in standard_fields:
                # Standard GHL contact fields go directly in main payload
                final_ghl_payload[field_key] = field_value
            else:
                # Custom fields go into customFields array
                field_details = FIELD_MAPPING.get(field_key)
                if field_details and field_details.get("id"):
                    custom_fields_array.append({
                        "id": field_details["id"],
                        "value": str(field_value)
                    })
                    logger.debug(f"Added custom field: {field_details['name']} ({field_key}) = {field_value}")
                else:
                    logger.warning(f"Custom field '{field_key}' found in valid keys but missing field ID mapping")
        else:
            logger.warning(f"Field '{field_key}' from form is not a recognized GHL field. Ignoring.")
    
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
            
        elif ghl_key in standard_fields:
            # Only set standard fields if not already provided by form
            if not final_ghl_payload.get(ghl_key):
                final_ghl_payload[ghl_key] = static_value
        else:
            # Custom field from form config - add to customFields array if not already present
            field_details = FIELD_MAPPING.get(ghl_key)
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
        logger.info(f"Added {len(custom_fields_array)} custom fields to payload")
    
    return final_ghl_payload

@router.post("/elementor/{form_identifier}")
async def handle_enhanced_elementor_webhook(
    form_identifier: str, 
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Enhanced dynamic webhook handler for ALL Elementor form submissions.
    Handles 79+ forms intelligently without hardcoding each one.
    """
    start_time = time.time()
    
    try:
        # Parse incoming JSON payload
        elementor_payload = await request.json()
        logger.info(f"📥 Enhanced Elementor Webhook received for form '{form_identifier}': {json.dumps(elementor_payload, indent=2)}")

        # Get dynamic form configuration
        form_config = get_dynamic_form_configuration(form_identifier)
        logger.info(f"📋 Dynamic form config for '{form_identifier}': {form_config}")

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

        # Initialize GHL API client
        ghl_api_client = GoHighLevelAPI(private_token=AppConfig.GHL_PRIVATE_TOKEN, location_id=AppConfig.GHL_LOCATION_ID)
         logger.info(f"🔑 Using GHL PIT Token for authentication")

        # Process payload into GHL format
        final_ghl_payload = process_payload_to_ghl_format(elementor_payload, form_config)
        
        # VERBOSE DEBUG: Check custom fields structure before sending to GHL
        if 'customFields' in final_ghl_payload:
            custom_fields = final_ghl_payload['customFields']
            logger.info(f"🔍 WEBHOOK CUSTOM FIELDS DEBUG:")
            logger.info(f"  🏷️  Type: {type(custom_fields)}")
            if isinstance(custom_fields, list):
                logger.info(f"  ✅ CustomFields is correctly formatted as ARRAY")
                logger.info(f"  📊 Array length: {len(custom_fields)}")
                for i, field in enumerate(custom_fields):
                    logger.info(f"    [{i}] {field}")
            else:
                logger.error(f"  ❌ CRITICAL: CustomFields is {type(custom_fields)}, should be array!")
                logger.error(f"  ❌ Content: {custom_fields}")
        
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
            
            # Check if creation was successful (either valid contact or error details)
            if created_contact_response and isinstance(created_contact_response, dict):
                if not created_contact_response.get("error") and created_contact_response.get("id"):
                    # SUCCESS: Contact created successfully
                    final_ghl_contact_id = created_contact_response["id"]
                    operation_successful = True
                    logger.info(f"✅ Successfully created new GHL contact {final_ghl_contact_id}")
                else:
                    # FAILED: Creation failed with detailed error info
                    logger.error(f"❌ GHL contact creation failed with details: {created_contact_response}")
                    api_response_details = created_contact_response
                    
                    # Log detailed error information for debugging
                    if created_contact_response.get("error"):
                        logger.error(f"  📋 Error Type: {created_contact_response.get('exception_type', 'HTTP Error')}")
                        logger.error(f"  📋 Status Code: {created_contact_response.get('status_code', 'Unknown')}")
                        logger.error(f"  📋 Response Text: {created_contact_response.get('response_text', 'No response text')}")
                        if created_contact_response.get("error_json"):
                            logger.error(f"  📋 GHL Error JSON: {created_contact_response.get('error_json')}")
            else:
                # NULL/INVALID RESPONSE: Unexpected response format
                logger.error(f"❌ Unexpected response from GHL API create_contact: {created_contact_response}")
                api_response_details = {"error": True, "unexpected_response": created_contact_response}
                
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
                    "service_category": form_config.get("service_category"),
                    "processing_time_seconds": processing_time,
                    "validation_warnings": validation_result.get("warnings", [])
                },
                lead_id=final_ghl_contact_id, 
                success=True
            )
            
            # Trigger background tasks based on form type
            if form_config.get("requires_immediate_routing"):
                background_tasks.add_task(
                    trigger_enhanced_lead_routing_workflow, 
                    ghl_location_id=DSP_GHL_LOCATION_ID,
                    ghl_contact_id=final_ghl_contact_id,
                    form_identifier=form_identifier,
                    form_config=form_config,
                    form_data=elementor_payload
                )
            
            return {
                "status": "success", 
                "message": f"Webhook processed successfully. GHL contact {final_ghl_contact_id} {action_taken}.",
                "contact_id": final_ghl_contact_id,
                "action": action_taken,
                "form_type": form_config.get("form_type"),
                "service_category": form_config.get("service_category"),
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
        logger.exception(f"💥 Critical error processing Enhanced Elementor webhook for form '{form_identifier}' after {processing_time}s: {e}")
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


async def trigger_enhanced_lead_routing_workflow(
    ghl_location_id: str, 
    ghl_contact_id: str, 
    form_identifier: str, 
    form_config: Dict[str, Any],
    form_data: Dict[str, Any]
):
    """
    Enhanced background task for intelligent lead routing with AI classification
    """
    logger.info(f"🚀 ENHANCED BACKGROUND TASK: Processing lead for contact {ghl_contact_id} from form '{form_identifier}'")
    
    try:
        # Initialize AI classifier for enhanced service classification
        ai_classifier = AIServiceClassifier(industry="marine")
        
        # Perform AI-enhanced service classification
        classification_result = await ai_classifier.classify_service(form_data)
        
        # Get account information for multi-tenant support
        account = simple_db_instance.get_account_by_ghl_location_id(ghl_location_id)
        if not account:
            logger.warning(f"⚠️ No account found for GHL Location ID: {ghl_location_id}")
            account_id = simple_db_instance.create_account(
                company_name="Digital Marine LLC",
                industry="marine",
                ghl_location_id=ghl_location_id,
                ghl_private_token=DSP_LOCATION_PIT
            )
        else:
            account_id = account["id"]
        
        # Prepare lead data for database
        lead_data = {
            "service_category": classification_result.get("category", form_config.get("service_category")),
            "customer_name": f"{form_data.get('firstName', '')} {form_data.get('lastName', '')}".strip(),
            "customer_email": form_data.get("email", ""),
            "customer_phone": form_data.get("phone", ""),
            "service_details": {
                "form_identifier": form_identifier,
                "service_requested": form_data.get("specific_service_needed", ""),
                "vessel_info": {
                    "make": form_data.get("vessel_make", ""),
                    "model": form_data.get("vessel_model", ""),
                    "year": form_data.get("vessel_year", ""),
                    "length_ft": form_data.get("vessel_length_ft", "")
                },
                "location": {
                    "zip_code": form_data.get("zip_code_of_service", ""),
                    "vessel_location": form_data.get("vessel_location__slip", "")
                },
                "timeline": form_data.get("desired_timeline", ""),
                "budget_range": form_data.get("budget_range", ""),
                "special_requests": form_data.get("special_requests__notes", ""),
                "classification": classification_result
            }
        }
        
        # Create lead in database
        lead_id = simple_db_instance.create_lead(
            service_category=lead_data["service_category"],
            customer_name=lead_data["customer_name"],
            customer_email=lead_data["customer_email"],
            customer_phone=lead_data["customer_phone"],
            service_details=lead_data["service_details"],
            account_id=account_id,
            ghl_contact_id=ghl_contact_id
        )
        
        # Determine routing priority
        priority = form_config.get("priority", "normal")
        form_type = form_config.get("form_type", "unknown")
        
        # Enhanced vendor matching logic
        if form_type == "client_lead" or form_type == "emergency_service":
            # Find matching vendors for this service category and location
            available_vendors = find_matching_vendors(
                account_id=account_id,
                service_category=lead_data["service_category"],
                zip_code=form_data.get("zip_code_of_service", ""),
                priority=priority
            )
            
            if available_vendors:
                logger.info(f"🎯 Found {len(available_vendors)} matching vendors for lead {lead_id}")
                
                # Assign to best matching vendor (for now, first available)
                selected_vendor = available_vendors[0]
                
                # Update lead with vendor assignment
                # Note: You would need to add this method to simple_connection.py
                # simple_db_instance.assign_lead_to_vendor(lead_id, selected_vendor["id"])
                
                # Notify vendor (implement based on your notification preferences)
                await notify_vendor_of_new_lead(
                    vendor=selected_vendor,
                    lead_data=lead_data,
                    ghl_contact_id=ghl_contact_id
                )
            else:
                logger.warning(f"⚠️ No matching vendors found for service '{lead_data['service_category']}' in area '{form_data.get('zip_code_of_service', 'Unknown')}'")
        
        # Log successful routing
        simple_db_instance.log_activity(
            event_type="enhanced_lead_routing_completed",
            event_data={
                "ghl_location_id": ghl_location_id,
                "ghl_contact_id": ghl_contact_id,
                "lead_id": lead_id,
                "form_identifier": form_identifier,
                "form_type": form_type,
                "priority": priority,
                "service_category": lead_data["service_category"],
                "classification_confidence": classification_result.get("confidence", 0),
                "timestamp": time.time()
            },
            lead_id=ghl_contact_id,
            success=True
        )
        
        logger.info(f"✅ Enhanced lead routing completed for {ghl_contact_id} with priority: {priority}")
        
    except Exception as e:
        logger.error(f"❌ Error in enhanced lead routing workflow for {ghl_contact_id}: {e}")
        simple_db_instance.log_activity(
            event_type="enhanced_lead_routing_error",
            event_data={
                "ghl_contact_id": ghl_contact_id,
                "form_identifier": form_identifier,
                "error": str(e)
            },
            lead_id=ghl_contact_id,
            success=False,
            error_message=str(e)
        )


def find_matching_vendors(account_id: str, service_category: str, zip_code: str, priority: str) -> List[Dict[str, Any]]:
    """
    Find vendors that match the service category and location
    """
    try:
        # Get all active vendors for this account
        vendors = simple_db_instance.get_vendors(account_id=account_id)
        
        matching_vendors = []
        for vendor in vendors:
            # Check if vendor is active and taking new work
            if vendor.get("status") != "active" or not vendor.get("taking_new_work", False):
                continue
            
            # Check if vendor provides this service category
            services_provided = vendor.get("services_provided", [])
            if isinstance(services_provided, str):
                services_provided = [s.strip() for s in services_provided.split(',')]
            
            # Simple service matching (can be enhanced with AI later)
            service_match = False
            for service in services_provided:
                if service_category.lower() in service.lower() or service.lower() in service_category.lower():
                    service_match = True
                    break
            
            if not service_match:
                continue
            
            # Check service area (if vendor has specified zip codes)
            service_areas = vendor.get("service_areas", [])
            if isinstance(service_areas, str):
                service_areas = [s.strip() for s in service_areas.split(',')]
            
            # If vendor has no specified service areas, assume they serve all areas
            if service_areas and zip_code:
                area_match = any(zip_code in area or area in zip_code for area in service_areas)
                if not area_match:
                    continue
            
            # Add vendor to matching list with priority score
            vendor_score = calculate_vendor_score(vendor, service_category, priority)
            vendor["match_score"] = vendor_score
            matching_vendors.append(vendor)
        
        # Sort by match score (highest first)
        matching_vendors.sort(key=lambda v: v.get("match_score", 0), reverse=True)
        
        return matching_vendors
        
    except Exception as e:
        logger.error(f"Error finding matching vendors: {e}")
        return []


def calculate_vendor_score(vendor: Dict[str, Any], service_category: str, priority: str) -> float:
    """
    Calculate a matching score for vendor selection
    """
    score = 0.0
    
    # Base score from performance rating
    performance_score = vendor.get("performance_score", 0.8)
    score += performance_score * 40  # 40 points max for performance
    
    # Bonus for recent activity (placeholder - you'd need to track this)
    # score += recent_activity_bonus
    
    # Penalty for high current workload (placeholder - you'd need to track this)
    # score -= workload_penalty
    
    # Bonus for emergency priority if vendor is marked as emergency-capable
    if priority == "high":
        # You could add a field to track emergency capability
        score += 10
    
    # Bonus for specialization match (enhanced matching could go here)
    score += 10  # Base specialization bonus
    
    return score


async def notify_vendor_of_new_lead(vendor: Dict[str, Any], lead_data: Dict[str, Any], ghl_contact_id: str):
    """
    Notify vendor of new lead assignment
    """
    try:
        # Initialize GHL API for notifications
        ghl_api_client = GoHighLevelAPI(private_token=DSP_LOCATION_PIT, location_id=DSP_GHL_LOCATION_ID)
        
        vendor_contact_id = vendor.get("ghl_contact_id")
        if not vendor_contact_id:
            logger.warning(f"⚠️ Vendor {vendor.get('name')} has no GHL contact ID for notifications")
            return
        
        # Prepare notification message
        service_category = lead_data.get("service_category", "Service Request")
        customer_name = lead_data.get("customer_name", "Customer")
        location = lead_data.get("service_details", {}).get("location", {}).get("zip_code", "Unknown")
        
        notification_message = f"""
🚤 NEW LEAD ALERT - {service_category}

Customer: {customer_name}
Service: {lead_data.get('service_details', {}).get('service_requested', service_category)}
Location: {location}
Timeline: {lead_data.get('service_details', {}).get('timeline', 'Not specified')}

Please respond quickly to secure this lead!
Contact customer: {lead_data.get('customer_phone', 'No phone provided')}

- Dockside Pros Lead Router
        """.strip()
        
        # Send SMS notification
        sms_sent = ghl_api_client.send_sms(vendor_contact_id, notification_message)
        
        if sms_sent:
            logger.info(f"📱 SMS notification sent to vendor {vendor.get('name')} for lead {ghl_contact_id}")
        else:
            logger.warning(f"⚠️ Failed to send SMS notification to vendor {vendor.get('name')}")
        
        # Log notification attempt
        simple_db_instance.log_activity(
            event_type="vendor_notification_sent",
            event_data={
                "vendor_id": vendor.get("id"),
                "vendor_name": vendor.get("name"),
                "lead_contact_id": ghl_contact_id,
                "notification_type": "SMS",
                "success": sms_sent
            },
            vendor_id=vendor.get("id"),
            success=sms_sent
        )
        
    except Exception as e:
        logger.error(f"Error notifying vendor {vendor.get('name', 'Unknown')}: {e}")


# Health check endpoint for enhanced webhook system
@router.get("/health")
async def enhanced_webhook_health_check():
    """Enhanced health check for webhook system"""
    try:
        # Test database connection
        db_stats = simple_db_instance.get_stats()
        db_healthy = True
    except Exception as e:
        db_stats = {"error": str(e)}
        db_healthy = False
    
    # Test field reference loading
    field_reference_healthy = len(ALL_GHL_FIELDS_MAP_FROM_JSON) > 0
    
    return {
        "status": "healthy" if (db_healthy and field_reference_healthy) else "degraded",
        "webhook_system": "enhanced_dynamic_processing",
        "ghl_location_id": DSP_GHL_LOCATION_ID,
        "valid_field_count": len(VALID_GHL_PAYLOAD_KEYS),
        "custom_field_mappings": len(FIELD_MAPPING),
        "service_categories": len(COMPLETE_SERVICE_CATEGORIES),
        "database_status": "healthy" if db_healthy else "error",
        "database_stats": db_stats,
        "field_reference_status": "loaded" if field_reference_healthy else "missing",
        "supported_form_types": ["client_lead", "vendor_application", "emergency_service", "general_inquiry"],
        "dynamic_routing": "enabled",
        "ai_classification": "enabled",
        "message": "Enhanced webhook system ready for dynamic processing of all form types"
    }


# Get service categories endpoint
@router.get("/service-categories")
async def get_service_categories():
    """Return all supported service categories and their details"""
    
    categories_info = {}
    for category_key, category_data in COMPLETE_SERVICE_CATEGORIES.items():
        categories_info[category_key] = {
            "name": category_data["name"],
            "subcategories": category_data.get("subcategories", []),
            "keywords": category_data.get("keywords", []),
            "example_webhook_url": f"https://dockside.life/api/v1/webhooks/elementor/{category_key}_example"
        }
    
    return {
        "status": "success",
        "service_categories": categories_info,
        "total_categories": len(COMPLETE_SERVICE_CATEGORIES),
        "dynamic_form_processing": "enabled",
        "message": "All 17 marine service categories supported with dynamic form handling"
    }


# Get field mappings endpoint
@router.get("/field-mappings")
async def get_field_mappings():
    """Return all available field mappings for form development"""
    
    return {
        "status": "success",
        "standard_fields": [
            "firstName", "lastName", "email", "phone", "companyName", 
            "address1", "city", "state", "postal_code", "name",
            "tags", "notes", "source", "website"
        ],
        "custom_field_mappings": FIELD_MAPPING,
        "total_custom_fields": len(FIELD_MAPPING),
        "field_reference_source": "field_reference.json",
        "message": "Complete field mappings for GHL integration"
    }


# Dynamic form testing endpoint
@router.post("/test/{form_identifier}")
async def test_form_configuration(form_identifier: str):
    """Test endpoint to see how any form identifier would be configured"""
    
    try:
        form_config = get_dynamic_form_configuration(form_identifier)
        
        return {
            "status": "success",
            "form_identifier": form_identifier,
            "generated_configuration": form_config,
            "webhook_url": f"https://dockside.life/api/v1/webhooks/elementor/{form_identifier}",
            "message": f"Dynamic configuration generated for form '{form_identifier}'"
        }
    except Exception as e:
        return {
            "status": "error",
            "form_identifier": form_identifier,
            "error": str(e),
            "message": "Failed to generate configuration"
        }


# Legacy vendor user creation webhook (maintained for compatibility)
@router.post("/ghl/vendor-user-creation")
async def handle_vendor_user_creation_webhook(request: Request):
    """
    Legacy webhook endpoint for GHL workflow to trigger vendor user creation.
    Maintained for backward compatibility with existing workflows.
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
        
        # Create new user data with vendor-specific permissions
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
        
        # Send welcome email to vendor
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
