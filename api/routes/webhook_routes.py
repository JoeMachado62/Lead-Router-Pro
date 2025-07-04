# api/routes/webhook_routes.py

import logging
import json
from typing import Dict, List, Any, Optional
import time
import uuid
import re
from urllib.parse import parse_qs

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks

# --- Corrected Imports - Single Source of Truth ---
from config import AppConfig  # Single source of truth for configuration
from database.simple_connection import db as simple_db_instance
from api.services.ghl_api import GoHighLevelAPI
from api.services.ai_classifier import AIServiceClassifier
from api.services.field_mapper import field_mapper
# Enhanced service classification and storage
from api.services.enhanced_service_classifier import EnhancedServiceClassifier
from database.enhanced_lead_storage import EnhancedLeadStorage

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/webhooks", tags=["Enhanced Elementor Webhooks (DSP)"])
# Initialize enhanced services
enhanced_classifier = EnhancedServiceClassifier()
enhanced_storage = EnhancedLeadStorage()

# --- REMOVED CONFLICTING FIELD REFERENCE LOADING ---
# Now using field_mapper service exclusively for all field operations

async def parse_webhook_payload(request: Request) -> Dict[str, Any]:
    """
    Robust payload parser that handles both JSON and form-encoded data
    Provides fallback support for WordPress/Elementor webhooks that may send either format
    """
    content_type = request.headers.get("content-type", "").lower()
    
    logger.info(f"🔍 PAYLOAD PARSER: Content-Type='{content_type}'")
    
    # Method 1: Try JSON parsing first (preferred format)
    if "application/json" in content_type:
        try:
            payload = await request.json()
            logger.info(f"✅ Successfully parsed JSON payload with {len(payload)} fields")
            return normalize_field_names(payload)
        except Exception as json_error:
            logger.warning(f"⚠️ JSON parsing failed despite JSON content-type: {json_error}")
            # Fall through to form parsing
    
    # Method 2: Try form-encoded parsing
    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        try:
            form_data = await request.form()
            payload = dict(form_data)
            logger.info(f"✅ Successfully parsed form-encoded payload with {len(payload)} fields")
            
            # Log the conversion for debugging
            logger.info(f"🔄 Form-encoded fields: {list(payload.keys())}")
            
            return normalize_field_names(payload)
        except Exception as form_error:
            logger.warning(f"⚠️ Form parsing failed: {form_error}")
    
    # Method 3: Auto-detect fallback - try both methods
    logger.info("🔄 Auto-detecting payload format...")
    
    # Get raw body for inspection
    try:
        body = await request.body()
        body_str = body.decode('utf-8')
        logger.info(f"📄 Raw body preview (first 200 chars): {body_str[:200]}")
        
        # Try to detect format from content
        if body_str.strip().startswith('{') and body_str.strip().endswith('}'):
            # Looks like JSON
            try:
                payload = json.loads(body_str)
                logger.info(f"✅ Auto-detected and parsed JSON payload with {len(payload)} fields")
                return normalize_field_names(payload)
            except Exception as e:
                logger.warning(f"⚠️ Auto-detect JSON parsing failed: {e}")
        
        # Try form-encoded parsing
        if '=' in body_str and ('&' in body_str or len(body_str.split('=')) == 2):
            # Looks like form data
            try:
                # Parse URL-encoded data manually
                parsed_data = parse_qs(body_str, keep_blank_values=True)
                # Convert lists to single values (form data typically has single values)
                payload = {key: (values[0] if values else '') for key, values in parsed_data.items()}
                logger.info(f"✅ Auto-detected and parsed form-encoded payload with {len(payload)} fields")
                return normalize_field_names(payload)
            except Exception as e:
                logger.warning(f"⚠️ Auto-detect form parsing failed: {e}")
        
    except Exception as e:
        logger.error(f"❌ Failed to read request body for auto-detection: {e}")
    
    # Method 4: Last resort - return empty dict with error logging
    logger.error("❌ All payload parsing methods failed - returning empty payload")
    logger.error(f"❌ Content-Type: {content_type}")
    logger.error(f"❌ Headers: {dict(request.headers)}")
    
    # Return empty payload but don't raise exception - let validation handle it
    return {}


def normalize_field_names(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize WordPress/Elementor field names to expected format
    Maps common WordPress field variations to standard field names
    """
    # Field name mapping for WordPress/Elementor forms
    field_mappings = {
        # Name fields
        "First Name": "firstName",
        "first_name": "firstName", 
        "fname": "firstName",
        "Last Name": "lastName",
        "last_name": "lastName",
        "lname": "lastName",
        
        # Email fields
        "Your Contact Email?": "email",
        "Email": "email",
        "email_address": "email",
        "contact_email": "email",
        "Email Address": "email",
        
        # Phone fields
        "Your Contact Phone #?": "phone",
        "Phone": "phone",
        "phone_number": "phone",
        "contact_phone": "phone",
        "Phone Number": "phone",
        
        # Service-specific fields
        "What Zip Code Are You Requesting Service In?": "zip_code_of_service",
        "Zip Code": "zip_code_of_service",
        "Service Zip Code": "zip_code_of_service",
        "Location": "zip_code_of_service",
        
        "What Specific Service(s) Do You Request?": "specific_service_needed",
        "Service Needed": "specific_service_needed",
        "Service Request": "specific_service_needed",
        "Services": "specific_service_needed",
        "What Specific Service(s) Do You Request?": "specific_service_needed",
        
        "Your Vessel Manufacturer? ": "vessel_make",
        "Vessel Make": "vessel_make",
        "Boat Make": "vessel_make",
        "Manufacturer": "vessel_make",
        
        "Your Vessel Model or Length of Vessel in Feet?": "vessel_model",
        "Vessel Model": "vessel_model",
        "Boat Model": "vessel_model",
        "Model": "vessel_model",
        
        "Year of Vessel?": "vessel_year",
        "Vessel Year": "vessel_year",
        "Boat Year": "vessel_year",
        "Year": "vessel_year",
        
        "Is The Vessel On a Dock, At a Marina, or On a Trailer?": "vessel_location__slip",
        "Vessel Location": "vessel_location__slip",
        "Boat Location": "vessel_location__slip",
        "Location Details": "vessel_location__slip",
        
        "When Do You Prefer Service?": "desired_timeline",
        "Timeline": "desired_timeline",
        "Service Timeline": "desired_timeline",
        "Preferred Date": "desired_timeline",
        
        "Any Special Requests or Other Information?": "special_requests__notes",
        "Special Requests": "special_requests__notes",
        "Additional Notes": "special_requests__notes",
        "Comments": "special_requests__notes",
        "Notes": "special_requests__notes",
        
        # Vendor fields
        "What is Your Company Name?": "vendor_company_name",
        "Company Name": "vendor_company_name",
        "Business Name": "vendor_company_name",
        "Services Provided": "services_provided",
        "What Main Service Does Your Company Offer?": "services_provided",
        "Service Areas": "service_zip_codes",
        "Years in Business": "years_in_business",
        
        # Contact preference
        "How Should We Contact You Back? ": "preferred_contact_method",
        "Contact Preference": "preferred_contact_method",
        "Preferred Contact": "preferred_contact_method"
    }
    
    normalized_payload = {}
    
    # First pass: direct mapping
    for original_key, value in payload.items():
        # Skip empty values and system fields
        if not value or value == "" or original_key.startswith("No Label"):
            continue
            
        # Check if we have a mapping for this field
        mapped_key = field_mappings.get(original_key, original_key)
        normalized_payload[mapped_key] = value
    
    # Log the normalization for debugging
    mapped_fields = []
    for original_key in payload.keys():
        if original_key in field_mappings:
            mapped_fields.append(f"{original_key} → {field_mappings[original_key]}")
    
    if mapped_fields:
        logger.info(f"🔄 Field name normalization applied:")
        for mapping in mapped_fields:
            logger.info(f"   {mapping}")
    
    logger.info(f"📋 Normalized payload keys: {list(normalized_payload.keys())}")
    
    return normalized_payload

# Enhanced Service Category Mapping (All 17 Categories)
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
    
    # Check for unexpected fields (informational) - now using field_mapper
    valid_ghl_fields = field_mapper.get_all_ghl_field_keys()
    for field in payload.keys():
        # Check if field maps to a valid GHL field
        mapped_field = field_mapper.get_mapping(field, "marine")
        if mapped_field not in valid_ghl_fields:
            validation_result["unexpected_fields"].append(field)
            validation_result["warnings"].append(f"Field '{field}' maps to '{mapped_field}' which is not a recognized GHL field")
    
    # Validate email format
    email = payload.get("email", "")
    if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        validation_result["errors"].append("Invalid email format")
        validation_result["is_valid"] = False
    
    return validation_result

def process_payload_to_ghl_format(elementor_payload: Dict[str, Any], form_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    CORRECTED: Process Elementor payload into GHL format with proper custom fields array formation
    """
    # Apply field mapping first to convert form field names to GHL field names
    mapped_payload = field_mapper.map_payload(elementor_payload, industry="marine")
    logger.info(f"🔄 Applied field mapping. Original keys: {list(elementor_payload.keys())}, Mapped keys: {list(mapped_payload.keys())}")
    
    final_ghl_payload = {}
    custom_fields_array = []
    
    # Standard GHL contact fields
    standard_fields = {
        "firstName", "lastName", "email", "phone", "companyName", 
        "address1", "city", "state", "postal_code", "name",
        "tags", "notes", "dnd", "country", "source", "website"
    }
    
    # Process each field from mapped payload
    for field_key, field_value in mapped_payload.items():
        # Skip empty values (but allow 0 and False)
        if field_value == "" or field_value is None:
            logger.debug(f"Skipping empty value for field '{field_key}'")
            continue
        
        # Check if it's a valid GHL field using field_mapper
        if field_mapper.is_valid_ghl_field(field_key):
            if field_key in standard_fields:
                # Standard GHL contact fields go directly in main payload
                final_ghl_payload[field_key] = field_value
                logger.debug(f"Added standard field: {field_key} = {field_value}")
            else:
                # CORRECTED: Custom fields go into customFields array using field_mapper
                field_details = field_mapper.get_ghl_field_details(field_key)
                if field_details and field_details.get("id"):
                    custom_fields_array.append({
                        "id": field_details["id"],
                        "value": str(field_value)
                    })
                    logger.debug(f"Added custom field: {field_details['name']} ({field_key}) = {field_value} [ID: {field_details['id']}]")
                else:
                    logger.warning(f"Custom field '{field_key}' is valid but missing GHL field ID mapping")
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
            field_details = field_mapper.get_ghl_field_details(ghl_key)
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
        logger.info(f"✅ Added {len(custom_fields_array)} custom fields to GHL payload")
        
        # VERBOSE DEBUG: Log each custom field being sent
        for i, field in enumerate(custom_fields_array):
            logger.info(f"  Custom Field [{i}]: ID={field['id']}, Value='{field['value']}'")
    else:
        logger.warning("⚠️ No custom fields added to GHL payload - this may indicate a mapping issue")
    
    return final_ghl_payload

# DEBUG GET endpoint to test routing
@router.get("/elementor/{form_identifier}")
@router.get("/elementor/{form_identifier}/")
async def debug_webhook_endpoint(form_identifier: str, request: Request):
    """
    DEBUG: This GET endpoint should help diagnose the redirect issue
    """
    logger.info(f"🔍 DEBUG GET REQUEST: form_identifier={form_identifier}, method={request.method}, url={request.url}")
    return {
        "status": "debug_response",
        "message": f"This is a GET request to the webhook endpoint for form '{form_identifier}'",
        "method_received": request.method,
        "url": str(request.url),
        "headers": dict(request.headers),
        "note": "If you're seeing this, there's likely a redirect converting your POST to GET. Check your webhook URL configuration.",
        "correct_method": "POST",
        "webhook_url": f"/api/v1/webhooks/elementor/{form_identifier}"
    }

@router.post("/elementor/{form_identifier}")
@router.post("/elementor/{form_identifier}/")  # Handle both with and without trailing slash
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
    
    # DEBUG: Log the actual HTTP method and URL
    logger.info(f"🔍 WEBHOOK DEBUG: Method={request.method}, URL={request.url}, Headers={dict(request.headers)}")
    
    try:
        # Parse incoming payload (supports both JSON and form-encoded data)
        elementor_payload = await parse_webhook_payload(request)
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

        # Initialize GHL API client using AppConfig with V2/V1 fallback support
        ghl_api_client = GoHighLevelAPI(
            location_api_key=AppConfig.GHL_LOCATION_API,
            private_token=AppConfig.GHL_PRIVATE_TOKEN, 
            location_id=AppConfig.GHL_LOCATION_ID,
            agency_api_key=AppConfig.GHL_AGENCY_API_KEY,
            company_id=AppConfig.GHL_COMPANY_ID
        )
        logger.info(f"🔑 GHL API client initialized with V2→V1 fallback authentication and enhanced scope control")

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
        else:
            logger.warning("⚠️ No customFields in final payload - this indicates field mapping issues")
        
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

        # Step 1: Search for existing contact by email AND phone (ENHANCED)
        search_email = final_ghl_payload["email"]
        search_phone = final_ghl_payload.get("phone", "")
        
        logger.info(f"🔍 Searching for existing contact with email: {search_email}")
        if search_phone:
            logger.info(f"🔍 Also checking for phone duplicates: {search_phone}")
        
        # Search by email first
        email_search_results = ghl_api_client.search_contacts(query=search_email, limit=10)
        phone_search_results = []
        
        # Search by phone if provided
        if search_phone:
            phone_search_results = ghl_api_client.search_contacts(query=search_phone, limit=10)
        
        # Combine and deduplicate results
        all_search_results = email_search_results or []
        if phone_search_results:
            # Add phone results that aren't already in email results
            existing_ids = {contact.get('id') for contact in all_search_results}
            for phone_contact in phone_search_results:
                if phone_contact.get('id') not in existing_ids:
                    all_search_results.append(phone_contact)
        
        if all_search_results:
            logger.info(f"📋 Search returned {len(all_search_results)} potential matches (email: {len(email_search_results or [])}, phone: {len(phone_search_results or [])})")
            
            for i, contact_result in enumerate(all_search_results):
                contact_id = contact_result.get('id')
                contact_email = contact_result.get('email', '').lower()
                contact_phone = contact_result.get('phone', '')
                
                logger.info(f"  [{i}] Contact: {contact_id} - Email: {contact_email}, Phone: {contact_phone}")
                
                # Check for exact email match
                if contact_email == search_email:
                    existing_ghl_contact = contact_result
                    logger.info(f"✅ Found exact EMAIL match: {existing_ghl_contact.get('id')}")
                    break
                    
                # Check for phone match with normalization
                elif search_phone and contact_phone:
                    # Normalize phone numbers for comparison (remove non-digits)
                    search_phone_normalized = ''.join(filter(str.isdigit, search_phone))
                    contact_phone_normalized = ''.join(filter(str.isdigit, contact_phone))
                    
                    if search_phone_normalized == contact_phone_normalized:
                        existing_ghl_contact = contact_result
                        logger.info(f"✅ Found PHONE match: {existing_ghl_contact.get('id')} (Search: {search_phone} → {search_phone_normalized}, Contact: {contact_phone} → {contact_phone_normalized})")
                        break
        else:
            logger.info("📋 No search results returned for email or phone - contact appears to be new")

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
            
            # If this was a vendor application, create a vendor record in the local database
            if form_config.get("form_type") == "vendor_application":
                try:
                    account = simple_db_instance.get_account_by_ghl_location_id(AppConfig.GHL_LOCATION_ID)
                    if not account:
                        account_id = simple_db_instance.create_account(
                            company_name="Digital Marine LLC",
                            industry="marine",
                            ghl_location_id=AppConfig.GHL_LOCATION_ID,
                            ghl_private_token=AppConfig.GHL_PRIVATE_TOKEN
                        )
                    else:
                        account_id = account["id"]
                    
                    simple_db_instance.create_vendor(
                        account_id=account_id,
                        name=f"{elementor_payload.get('firstName', '')} {elementor_payload.get('lastName', '')}".strip(),
                        email=elementor_payload.get('email', ''),
                        company_name=elementor_payload.get('vendor_company_name', ''),
                        phone=elementor_payload.get('phone', ''),
                        ghl_contact_id=final_ghl_contact_id,
                        status="pending",
                        services_provided=elementor_payload.get('services_provided', ''),
                        service_areas=elementor_payload.get('service_zip_codes', '')
                    )
                except Exception as e:
                    logger.error(f"Error creating local vendor record: {e}")

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
                    "validation_warnings": validation_result.get("warnings", []),
                    "custom_fields_sent": len(final_ghl_payload.get("customFields", []))
                },
                lead_id=final_ghl_contact_id, 
                success=True
            )
            
            # Trigger background tasks based on form type
            if form_config.get("requires_immediate_routing"):
                background_tasks.add_task(
                    trigger_enhanced_lead_routing_workflow, 
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
                "validation_warnings": validation_result.get("warnings", []),
                "custom_fields_processed": len(final_ghl_payload.get("customFields", []))
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
    ghl_contact_id: str, 
    form_identifier: str, 
    form_config: Dict[str, Any],
    form_data: Dict[str, Any]
):
    """
    Enhanced background task for intelligent lead routing with AI classification and opportunity creation
    """
    logger.info(f"🚀 ENHANCED BACKGROUND TASK: Processing lead for contact {ghl_contact_id} from form '{form_identifier}'")
    
    try:
        # Initialize AI classifier for enhanced service classification
        ai_classifier = AIServiceClassifier(industry="marine")
        
        # Perform AI-enhanced service classification
        classification_result = await ai_classifier.classify_service(form_data)
        logger.info(f"🤖 AI Classification for contact {ghl_contact_id}: {classification_result}")
        
        # Get account information for multi-tenant support
        account = simple_db_instance.get_account_by_ghl_location_id(AppConfig.GHL_LOCATION_ID)
        if not account:
            logger.warning(f"⚠️ No account found for GHL Location ID: {AppConfig.GHL_LOCATION_ID}")
            account_id = simple_db_instance.create_account(
                company_name="Digital Marine LLC",
                industry="marine",
                ghl_location_id=AppConfig.GHL_LOCATION_ID,
                ghl_private_token=AppConfig.GHL_PRIVATE_TOKEN
            )
        else:
            account_id = account["id"]
        
        # Enhanced service classification with detailed breakdown
        enhanced_classification = enhanced_classifier.classify_service_detailed(form_data)
        logger.info(f"🔍 Enhanced classification: {enhanced_classification}")
        
        # Extract customer data
        customer_data = {
            "name": f"{form_data.get('firstName', '')} {form_data.get('lastName', '')}".strip(),
            "email": form_data.get("email", ""),
            "phone": form_data.get("phone", "")
        }
        
        # Create lead with enhanced storage
        lead_id = enhanced_storage.create_enhanced_lead(
            customer_data=customer_data,
            classification_result=enhanced_classification,
            account_id=account_id,
            ghl_contact_id=ghl_contact_id,
            source=form_identifier
        )
        
        # Step 2: Create an Opportunity in GHL Pipeline (SKIP FOR VENDOR APPLICATIONS)
        if AppConfig.PIPELINE_ID and AppConfig.NEW_LEAD_STAGE_ID:
            # Check if this is a vendor application by looking for vendor_company_name field
            is_vendor_application = bool(form_data.get("vendor_company_name"))
            
            if is_vendor_application:
                logger.info(f"🏢 Skipping opportunity creation for vendor application: {form_data.get('vendor_company_name')}")
            else:
                logger.info(f"📈 Creating opportunity in pipeline '{AppConfig.PIPELINE_ID}'")
                ghl_api_client = GoHighLevelAPI(private_token=AppConfig.GHL_PRIVATE_TOKEN, location_id=AppConfig.GHL_LOCATION_ID)
                
                customer_name = lead_data["customer_name"]
                service_category = lead_data["service_category"]
                
                # Fetch full contact details to get custom field values for opportunity
                contact_details = ghl_api_client.get_contact_by_id(ghl_contact_id)
                if not contact_details:
                    logger.warning(f"⚠️ Could not fetch contact details for {ghl_contact_id}, proceeding without custom fields")
                    contact_details = {}
                
                # Define the 18 custom fields relevant to leads/clients (from CSV rows 5-22)
                target_custom_field_keys = [
                    "preferred_contact_method", "service_category", "specific_service_needed", 
                    "zip_code_of_service", "vessel_year", "vessel_make", "vessel_model", 
                    "vessel_length_ft", "vessel_location__slip", "_guests__crew", 
                    "desired_timeline", "budget_range", "purchased_yet", "policy_start_date", 
                    "need_emergency_tow", "rental_duration", "training__education_type", 
                    "special_requests__notes"
                ]
                
                # Build custom fields array for opportunity using field_mapper
                opportunity_custom_fields = []
                contact_custom_fields = contact_details.get('customFields', [])
                
                for short_key in target_custom_field_keys:
                    # Get GHL field details using field_mapper
                    field_details = field_mapper.get_ghl_field_details(short_key)
                    if not field_details:
                        logger.debug(f"Custom field key '{short_key}' not found in field_mapper. Skipping.")
                        continue
                    
                    # Get the GHL field ID for this custom field
                    ghl_field_id = field_details['id']
                    
                    # Find the matching custom field in the contact's data
                    for contact_field in contact_custom_fields:
                        if contact_field.get('id') == ghl_field_id:
                            # Handle both 'value' and 'fieldValue' keys from GHL response
                            raw_value = contact_field.get('fieldValue') or contact_field.get('value', '')
                            # Convert to string and strip, handling None, integers, floats, etc.
                            if raw_value is not None and raw_value != '':
                                field_value = str(raw_value).strip()
                                if field_value:  # Only include if there's actually a value after stripping
                                    opportunity_custom_fields.append({
                                        "id": ghl_field_id,
                                        "key": short_key,
                                        "field_value": field_value
                                    })
                                    logger.debug(f"Added custom field to opportunity: {short_key} = {field_value} (type: {type(raw_value)})")
                            break

                logger.info(f"🏷️ Prepared {len(opportunity_custom_fields)} custom fields for opportunity")
                
                opportunity_data = {
                    "name": f"{customer_name} - {service_category}",
                    "pipelineId": AppConfig.PIPELINE_ID,
                    "locationId": AppConfig.GHL_LOCATION_ID,
                    "pipelineStageId": AppConfig.NEW_LEAD_STAGE_ID,
                    "contactId": ghl_contact_id,
                    "status": "open",
                    "monetaryValue": 0,  # Can be enhanced based on service type
                    "assignedTo": None,  # Will be assigned when vendor is matched
                    "source": form_config.get("source", f"{form_identifier} (DSP)")
                }
                
                # Add custom fields if we have any
                if opportunity_custom_fields:
                    opportunity_data["customFields"] = opportunity_custom_fields
                
                opportunity_result = ghl_api_client.create_opportunity(opportunity_data)
                if opportunity_result and opportunity_result.get("id"):
                    opportunity_id = opportunity_result.get("id")
                    logger.info(f"✅ Successfully created opportunity {opportunity_id} for contact {ghl_contact_id} with {len(opportunity_custom_fields)} custom fields")
                    
                    # Update lead record with opportunity ID
                    try:
                        simple_db_instance.update_lead_opportunity_id(lead_id, opportunity_id)
                    except Exception as e:
                        logger.warning(f"⚠️ Could not update lead with opportunity ID: {e}")
                else:
                    error_msg = "Unknown error"
                    if isinstance(opportunity_result, dict) and opportunity_result.get("error"):
                        error_msg = opportunity_result.get("message", str(opportunity_result))
                    logger.error(f"❌ Failed to create GHL opportunity: {error_msg}")
        else:
            logger.warning("⚠️ Skipping opportunity creation: PIPELINE_ID or NEW_LEAD_STAGE_ID not configured in AppConfig.")
        
        # Determine routing priority
        priority = form_config.get("priority", "normal")
        form_type = form_config.get("form_type", "unknown")
        
        # Enhanced vendor matching logic
        if form_type == "client_lead" or form_type == "emergency_service":
            # Find matching vendors for this service category and location using enhanced routing
            available_vendors = lead_routing_service.find_matching_vendors(
                account_id=account_id,
                service_category=enhanced_classification["primary_category"],
                zip_code=enhanced_classification["coverage_area"]["zip_code"],
                priority=priority
            )
            
            if available_vendors:
                logger.info(f"🎯 Found {len(available_vendors)} matching vendors for lead {lead_id}")
                
                # Use enhanced vendor selection with dual routing logic
                selected_vendor = lead_routing_service.select_vendor_from_pool(
                    available_vendors, account_id
                )
                
                # Update lead with vendor assignment
                try:
                    simple_db_instance.assign_lead_to_vendor(lead_id, selected_vendor["id"])
                except Exception as e:
                    logger.warning(f"⚠️ Could not assign lead to vendor: {e}")
                
                # Notify vendor (implement based on your notification preferences)
                await notify_vendor_of_new_lead(
                    vendor=selected_vendor,
                    lead_data=enhanced_classification,  # Pass enhanced classification instead of old lead_data
                    ghl_contact_id=ghl_contact_id
                )
            else:
                logger.warning(f"⚠️ No matching vendors found for service '{enhanced_classification['primary_category']}' in area '{enhanced_classification['coverage_area']['zip_code']}'")
                
                # FIXED: Notify admin of unmatched lead instead of creating new contacts
                await notify_admin_of_unmatched_lead(
                    lead_data=enhanced_classification,
                    ghl_contact_id=ghl_contact_id,
                    service_category=enhanced_classification["primary_category"],
                    location=enhanced_classification["coverage_area"]["zip_code"]
                )
        
        # Log successful routing
        simple_db_instance.log_activity(
            event_type="enhanced_lead_routing_completed",
            event_data={
                "ghl_location_id": AppConfig.GHL_LOCATION_ID,
                "ghl_contact_id": ghl_contact_id,
                "lead_id": lead_id,
                "form_identifier": form_identifier,
                "form_type": form_type,
                "priority": priority,
                "service_category": enhanced_classification["primary_category"],
                "classification_confidence": enhanced_classification.get("confidence", 0),
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
            
            if available_vendors:
                logger.info(f"🎯 Found {len(available_vendors)} matching vendors for lead {lead_id}")
                
                # Use enhanced vendor selection with dual routing logic
                selected_vendor = lead_routing_service.select_vendor_from_pool(
                    available_vendors, account_id
                )
                
                # Update lead with vendor assignment
                try:
                    simple_db_instance.assign_lead_to_vendor(lead_id, selected_vendor["id"])
                except Exception as e:
                    logger.warning(f"⚠️ Could not assign lead to vendor: {e}")
                
                # Notify vendor (implement based on your notification preferences)
                await notify_vendor_of_new_lead(
                    vendor=selected_vendor,
                    lead_data=enhanced_classification,  # Pass enhanced classification instead of old lead_data
                    ghl_contact_id=ghl_contact_id
                )
            else:
                logger.warning(f"⚠️ No matching vendors found for service '{lead_data['service_category']}' in area '{form_data.get('zip_code_of_service', 'Unknown')}'")
                
                # FIXED: Notify admin of unmatched lead instead of creating new contacts
                await notify_admin_of_unmatched_lead(
                    lead_data=lead_data,
                    ghl_contact_id=ghl_contact_id,
                    service_category=lead_data["service_category"],
                    location=form_data.get("zip_code_of_service", "Unknown")
                )
        
        # Log successful routing
        simple_db_instance.log_activity(
            event_type="enhanced_lead_routing_completed",
            event_data={
                "ghl_location_id": AppConfig.GHL_LOCATION_ID,
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


# Import the new lead routing service
from api.services.lead_routing_service import lead_routing_service


async def notify_vendor_of_new_lead(vendor: Dict[str, Any], lead_data: Dict[str, Any], ghl_contact_id: str):
    """
    Notify vendor of new lead assignment
    """
    try:
        # Initialize GHL API for notifications
        ghl_api_client = GoHighLevelAPI(private_token=AppConfig.GHL_PRIVATE_TOKEN, location_id=AppConfig.GHL_LOCATION_ID)
        
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


async def notify_admin_of_unmatched_lead(lead_data: Dict[str, Any], ghl_contact_id: str, service_category: str, location: str):
    """
    Notify admin when no vendors are found for a lead
    Uses existing admin contact ID instead of creating new contacts
    """
    try:
        # Initialize GHL API for notifications
        ghl_api_client = GoHighLevelAPI(private_token=AppConfig.GHL_PRIVATE_TOKEN, location_id=AppConfig.GHL_LOCATION_ID)
        
        # FIXED: Use Jeremy's existing contact ID instead of creating new contacts
        # This should be Jeremy Katz's existing contact ID in GHL
        admin_contact_id = "b69NCeI1P32jooC7ySfw"  # Jeremy's user ID from your message
        
        # Prepare admin notification message
        customer_name = lead_data.get("customer_name", "Customer")
        customer_email = lead_data.get("customer_email", "No email")
        customer_phone = lead_data.get("customer_phone", "No phone")
        
        admin_notification_message = f"""
🚨 UNMATCHED LEAD ALERT - {service_category}

No vendors found for this lead!

Customer: {customer_name}
Email: {customer_email}
Phone: {customer_phone}
Service: {service_category}
Location: {location}
Timeline: {lead_data.get('service_details', {}).get('timeline', 'Not specified')}

Please manually assign this lead or add vendors for this service area.

Lead ID: {ghl_contact_id}

- Dockside Pros Lead Router
        """.strip()
        
        # Send SMS notification to admin using existing contact ID
        sms_sent = ghl_api_client.send_sms(admin_contact_id, admin_notification_message)
        
        if sms_sent:
            logger.info(f"📱 Admin notification sent for unmatched lead {ghl_contact_id}")
        else:
            logger.warning(f"⚠️ Failed to send admin notification for unmatched lead {ghl_contact_id}")
        
        # Log admin notification attempt
        simple_db_instance.log_activity(
            event_type="admin_unmatched_lead_notification",
            event_data={
                "admin_contact_id": admin_contact_id,
                "lead_contact_id": ghl_contact_id,
                "service_category": service_category,
                "location": location,
                "notification_type": "SMS",
                "success": sms_sent
            },
            lead_id=ghl_contact_id,
            success=sms_sent
        )
        
    except Exception as e:
        logger.error(f"Error notifying admin of unmatched lead {ghl_contact_id}: {e}")


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
    
    # Test field reference loading via field_mapper
    field_mapper_stats = field_mapper.get_mapping_stats()
    field_reference_healthy = field_mapper_stats.get("ghl_fields_loaded", 0) > 0
    
    return {
        "status": "healthy" if (db_healthy and field_reference_healthy) else "degraded",
        "webhook_system": "enhanced_dynamic_processing",
        "ghl_location_id": AppConfig.GHL_LOCATION_ID,
        "pipeline_configured": AppConfig.PIPELINE_ID is not None and AppConfig.NEW_LEAD_STAGE_ID is not None,
        "valid_field_count": len(field_mapper.get_all_ghl_field_keys()),
        "custom_field_mappings": field_mapper_stats.get("ghl_fields_loaded", 0),
        "service_categories": len(COMPLETE_SERVICE_CATEGORIES),
        "database_status": "healthy" if db_healthy else "error",
        "database_stats": db_stats,
        "field_reference_status": "loaded" if field_reference_healthy else "missing",
        "field_mapper_stats": field_mapper_stats,
        "supported_form_types": ["client_lead", "vendor_application", "emergency_service", "general_inquiry"],
        "dynamic_routing": "enabled",
        "ai_classification": "enabled",
        "opportunity_creation": "enabled" if AppConfig.PIPELINE_ID else "disabled",
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


# Get field mappings endpoint - UPDATED to use field_mapper
@router.get("/field-mappings")
async def get_field_mappings():
    """Return all available field mappings for form development"""
    
    # Get all valid GHL field keys
    all_ghl_fields = field_mapper.get_all_ghl_field_keys()
    
    # Build custom field mappings with details
    custom_field_mappings = {}
    for field_key in all_ghl_fields:
        field_details = field_mapper.get_ghl_field_details(field_key)
        if field_details:
            custom_field_mappings[field_key] = field_details
    
    return {
        "status": "success",
        "standard_fields": [
            "firstName", "lastName", "email", "phone", "companyName", 
            "address1", "city", "state", "postal_code", "name",
            "tags", "notes", "source", "website"
        ],
        "custom_field_mappings": custom_field_mappings,
        "total_custom_fields": len(custom_field_mappings),
        "field_reference_source": "field_reference.json via field_mapper service",
        "mapping_stats": field_mapper.get_mapping_stats(),
        "message": "Complete field mappings for GHL integration via enhanced field_mapper service"
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
    SECURITY: Requires X-Webhook-API-Key header for authentication.
    """
    start_time = time.time()
    
    try:
        # SECURITY: Validate API key from header with enhanced debugging
        api_key = request.headers.get("X-Webhook-API-Key")
        expected_api_key = AppConfig.GHL_WEBHOOK_API_KEY
        
        # ENHANCED DEBUGGING: Log all request details for troubleshooting
        logger.info(f"🔍 GHL WEBHOOK DEBUG - Request from IP: {request.client.host}")
        logger.info(f"🔍 GHL WEBHOOK DEBUG - All Headers: {dict(request.headers)}")
        logger.info(f"🔍 GHL WEBHOOK DEBUG - Received API Key: '{api_key}' (length: {len(api_key) if api_key else 0})")
        logger.info(f"🔍 GHL WEBHOOK DEBUG - Expected API Key: '{expected_api_key}' (length: {len(expected_api_key) if expected_api_key else 0})")
        
        if not api_key:
            logger.error(f"❌ GHL webhook request missing API key from IP: {request.client.host}")
            logger.error(f"❌ Available headers: {list(request.headers.keys())}")
            raise HTTPException(
                status_code=401, 
                detail="Missing X-Webhook-API-Key header"
            )
        
        if api_key != expected_api_key:
            logger.error(f"❌ GHL webhook API key mismatch from IP: {request.client.host}")
            logger.error(f"❌ Received: '{api_key}' (type: {type(api_key)}, len: {len(api_key)})")
            logger.error(f"❌ Expected: '{expected_api_key}' (type: {type(expected_api_key)}, len: {len(expected_api_key)})")
            logger.error(f"❌ Char-by-char comparison:")
            
            # Character-by-character comparison for debugging
            if api_key and expected_api_key:
                max_len = max(len(api_key), len(expected_api_key))
                for i in range(max_len):
                    rec_char = api_key[i] if i < len(api_key) else "EOF"
                    exp_char = expected_api_key[i] if i < len(expected_api_key) else "EOF"
                    match = "✅" if rec_char == exp_char else "❌"
                    logger.error(f"   [{i:2d}] Received: '{rec_char}' | Expected: '{exp_char}' {match}")
            
            raise HTTPException(
                status_code=401, 
                detail="Invalid API key"
            )
        
        logger.info(f"✅ GHL webhook API key validated successfully")
        
        # Parse incoming GHL workflow webhook payload
        ghl_payload = await request.json()
        logger.info(f"📥 GHL Vendor User Creation Webhook received: {json.dumps(ghl_payload, indent=2)}")
        
        # CORRECTED: Extract vendor information directly from webhook payload (no extra API call needed)
        contact_id = ghl_payload.get("contact_id") or ghl_payload.get("contactId")
        
        # Get vendor information directly from the webhook payload
        vendor_email = ghl_payload.get("email", "")
        vendor_first_name = ghl_payload.get("first_name", "") or ghl_payload.get("firstName", "")
        vendor_last_name = ghl_payload.get("last_name", "") or ghl_payload.get("lastName", "")
        vendor_phone = ghl_payload.get("phone", "")
        vendor_company_name = ghl_payload.get("Vendor Company Name", "") or ghl_payload.get("vendor_company_name", "")
        
        logger.info(f"📋 CORRECTED: Using vendor data directly from webhook payload:")
        logger.info(f"   👤 Contact ID: {contact_id}")
        logger.info(f"   📧 Email: {vendor_email}")
        logger.info(f"   👨 Name: {vendor_first_name} {vendor_last_name}")
        logger.info(f"   📱 Phone: {vendor_phone}")
        logger.info(f"   🏢 Company: {vendor_company_name}")
        
        # Initialize GHL API client with V2/V1 fallback support including company_id
        ghl_api_client = GoHighLevelAPI(
            private_token=AppConfig.GHL_PRIVATE_TOKEN, 
            location_id=AppConfig.GHL_LOCATION_ID,
            agency_api_key=AppConfig.GHL_AGENCY_API_KEY,
            company_id=AppConfig.GHL_COMPANY_ID  # FIXED: Added missing company_id parameter
        )
        
        if not vendor_email:
            logger.error(f"❌ No email found for contact {contact_id}")
            raise HTTPException(status_code=400, detail="Vendor email is required for user creation")
        
        # Check if user already exists
        existing_user = ghl_api_client.get_user_by_email(vendor_email)
        if existing_user:
            logger.info(f"✅ User already exists for {vendor_email}: {existing_user.get('id')}")
            
            # Update vendor record with existing user ID
            vendor_record = simple_db_instance.get_vendor_by_email_and_account(vendor_email, account_id)    
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
        
        # CORRECTED: Create new user data with correct V1 API fields
        user_data = {
            "firstName": vendor_first_name,
            "lastName": vendor_last_name,
            "email": vendor_email,
            "phone": vendor_phone,
            "type": "account",  # FIXED: V1 API requires 'account' or 'agency', NOT 'user'
            "role": "user",     # This is correct - role can be 'user' or 'admin'
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
        
        # FIXED: Handle both success and error responses correctly
        if not created_user:
            logger.error(f"❌ No response from GHL user creation API for {vendor_email}")
            raise HTTPException(status_code=502, detail="No response from GHL user creation API")
        
        # Check if it's an error response
        if isinstance(created_user, dict) and created_user.get("error"):
            # Log detailed error information
            error_details = {
                "api_version": created_user.get("api_version", "V1"),
                "status_code": created_user.get("status_code"),
                "response_text": created_user.get("response_text"),
                "exception": created_user.get("exception"),
                "url": created_user.get("url")
            }
            logger.error(f"❌ GHL V1 API user creation failed with details: {error_details}")
            error_msg = f"GHL V1 API error: {created_user.get('response_text', 'Unknown error')}"
            raise HTTPException(status_code=502, detail=error_msg)
        
        # SUCCESS: Extract user ID from successful response
        user_id = created_user.get("id")
        if not user_id:
            logger.error(f"❌ GHL user creation succeeded but no user ID returned: {created_user}")
            raise HTTPException(status_code=502, detail="User created but no ID returned from GHL")
        
        logger.info(f"✅ Successfully created GHL user: {user_id} for {vendor_email}")

        # CREATE VENDOR RECORD IN LOCAL DATABASE
        try:
            # Get or create account
            account_record = simple_db_instance.get_account_by_ghl_location_id(AppConfig.GHL_LOCATION_ID)
            if not account_record:
                account_id = simple_db_instance.create_account(
                    ghl_location_id=AppConfig.GHL_LOCATION_ID,
                    company_name="DocksidePros",
                    industry="Marine Services"
                )
            else:
                account_id = account_record["id"]

            # Check if vendor already exists
            existing_vendor = simple_db_instance.get_vendor_by_email_and_account(vendor_email, account_id)
            
            if existing_vendor:
                # Update existing vendor with GHL User ID
                simple_db_instance.update_vendor_status(existing_vendor["id"], "active", user_id)
                logger.info(f"✅ Updated existing vendor record: {existing_vendor['id']}")
            else:
                # Create new vendor record
                vendor_db_id = simple_db_instance.create_vendor(
                    account_id=account_id,
                    name=f"{vendor_first_name} {vendor_last_name}".strip(),
                    email=vendor_email,
                    company_name=vendor_company_name,
                    phone=vendor_phone,
                    ghl_contact_id=contact_id,
                    status="active"
                )
                logger.info(f"✅ Created vendor record: {vendor_db_id}")
        except Exception as e:
            logger.error(f"⚠️ Vendor DB creation failed: {e}")
        
        # FIXED: Update the contact record with the GHL User ID
        if contact_id:
            logger.info(f"🔄 Updating contact {contact_id} with GHL User ID: {user_id}")
            
            # Get the GHL User ID field details from field_mapper
            ghl_user_id_field = field_mapper.get_ghl_field_details("ghl_user_id")
            if ghl_user_id_field and ghl_user_id_field.get("id"):
                update_payload = {
                    "customFields": [
                        {
                            "id": ghl_user_id_field["id"],
                            "value": user_id
                        }
                    ]
                }
                
                # Update the contact record
                update_success = ghl_api_client.update_contact(contact_id, update_payload)
                if update_success:
                    logger.info(f"✅ Successfully updated contact {contact_id} with GHL User ID: {user_id}")
                else:
                    logger.warning(f"⚠️ Failed to update contact {contact_id} with GHL User ID")
            else:
                logger.warning(f"⚠️ Could not find GHL User ID field mapping for contact update")
        else:
            logger.warning(f"⚠️ No contact ID provided - cannot update contact record with User ID")
        
        # Update vendor record in database
        vendor_record = simple_db_instance.get_vendor_by_email_and_account(vendor_email, AppConfig.GHL_LOCATION_ID)
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
        
        # NOTE: Welcome email sending removed as GHL handles all vendor communications
        # through its own automation workflows. This prevents conflicts and ensures
        # consistent messaging through the GHL system.
        email_sent = True  # Set to True since GHL handles vendor notifications
        logger.info(f"📧 Vendor notifications handled by GHL automation workflows")
        
        return {
            "status": "success",
            "message": f"Successfully created user for vendor {vendor_email}",
            "user_id": user_id,
            "contact_id": contact_id,
            "vendor_email": vendor_email,
            "vendor_company": vendor_company_name,
            "processing_time_seconds": processing_time,
            "action": "user_created",
            "welcome_email_sent": email_sent
        }
        
    except HTTPException:
        # Re-raise HTTPExceptions directly (don't wrap them)
        raise
    
    except Exception as e:
        processing_time = round(time.time() - start_time, 3)
        logger.exception(f"💥 Critical error processing vendor user creation webhook after {processing_time}s: {e}")
        simple_db_instance.log_activity(
            event_type="vendor_user_creation_error",
            event_data={
                "processing_time_seconds": processing_time,
                "error_class": e.__class__.__name__
            },
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
