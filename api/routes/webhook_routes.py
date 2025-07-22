# api/routes/webhook_routes.py

import logging
import json
from typing import Dict, List, Any, Optional
import time
import uuid
import re
from urllib.parse import parse_qs

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks

# --- Core Service Imports - Direct Processing Only ---
from config import AppConfig
from database.simple_connection import db as simple_db_instance
from api.services.ghl_api import GoHighLevelAPI
from api.services.field_mapper import field_mapper
from api.services.lead_routing_service import lead_routing_service
from api.services.location_service import location_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/webhooks", tags=["Clean Elementor Webhooks - Direct Processing"])

# Location services router for widget integration
location_router = APIRouter(prefix="/api/v1/locations", tags=["Location Services"])

@location_router.get("/states/{state_code}/counties")
async def get_counties_by_state(state_code: str):
    """Return all counties for a given state"""
    try:
        counties = location_service.get_state_counties(state_code.upper())
        return {
            "status": "success",
            "state": state_code.upper(),
            "counties": counties,
            "count": len(counties)
        }
    except Exception as e:
        logger.error(f"Error getting counties for state {state_code}: {e}")
        return {
            "status": "error",
            "message": "Failed to retrieve counties",
            "state": state_code.upper(),
            "counties": []
        }

async def create_lead_from_ghl_contact(
    ghl_contact_data: Dict[str, Any],
    account_id: str,
    form_identifier: str = "bulk_assignment"
) -> tuple[str, Optional[str]]:
    """
    SHARED PIPELINE: Convert GHL contact to database lead + opportunity
    Used by both webhook and bulk assignment workflows for consistency
    
    Returns: (lead_id, opportunity_id)
    """
    try:
        # Step 1: Extract customer data (reuse webhook logic)
        customer_data = {
            "name": f"{ghl_contact_data.get('firstName', '')} {ghl_contact_data.get('lastName', '')}".strip(),
            "email": ghl_contact_data.get("email", ""),
            "phone": ghl_contact_data.get("phone", "")
        }
        
        # Step 2: Apply field mapping (same as webhook system)
        mapped_payload = field_mapper.map_payload(ghl_contact_data, industry="marine")
        logger.info(f"🔄 Shared pipeline field mapping. Original keys: {list(ghl_contact_data.keys())}, Mapped keys: {list(mapped_payload.keys())}")
        
        # Step 3: Service classification (reuse webhook logic)
        service_category = get_direct_service_category(form_identifier)
        
        # Step 4: ZIP → County conversion (critical for routing)
        zip_code = mapped_payload.get("zip_code_of_service", "")
        service_county = ""
        service_state = ""
        
        if zip_code and len(zip_code) == 5 and zip_code.isdigit():
            logger.info(f"🗺️ Converting ZIP {zip_code} to county using shared pipeline")
            location_data = location_service.zip_to_location(zip_code)
            
            if not location_data.get('error'):
                county = location_data.get('county', '')
                state = location_data.get('state', '')
                if county and state:
                    service_county = f"{county}, {state}"
                    service_state = state
                    logger.info(f"✅ Shared pipeline ZIP {zip_code} → {service_county}")
                else:
                    logger.warning(f"⚠️ Shared pipeline ZIP {zip_code} conversion incomplete: county={county}, state={state}")
            else:
                logger.warning(f"⚠️ Shared pipeline could not convert ZIP {zip_code}: {location_data['error']}")
        else:
            logger.warning(f"⚠️ Shared pipeline invalid ZIP code format: '{zip_code}'")

        # Step 5: Create database lead using correct schema
        lead_id_str = str(uuid.uuid4())
        
        # Build service_details from all mapped fields
        service_details = {}
        standard_lead_fields = {
            "firstName", "lastName", "email", "phone", "primary_service_category",
            "customer_zip_code", "specific_service_requested"
        }
        
        for field_key, field_value in mapped_payload.items():
            if field_value and field_value != "" and field_key not in standard_lead_fields:
                service_details[field_key] = field_value
                
        service_details.update({
            "form_source": form_identifier,
            "processing_method": "shared_pipeline",
            "created_via": "create_lead_from_ghl_contact"
        })
        
        # Database INSERT using correct schema
        conn = None
        try:
            conn = simple_db_instance._get_conn()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO leads (
                    id, account_id, ghl_contact_id, ghl_opportunity_id, customer_name,
                    customer_email, customer_phone, primary_service_category, specific_service_requested,
                    service_zip_code, service_county, service_state, vendor_id, 
                    status, priority, source, service_details, 
                    created_at, updated_at, service_city, 
                    service_complexity, estimated_duration, requires_emergency_response, 
                    classification_confidence, classification_reasoning
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?)
            ''', (
                lead_id_str,                                                # id
                account_id,                                                 # account_id
                ghl_contact_data.get('id'),                                 # ghl_contact_id
                None,                                                       # ghl_opportunity_id (will be updated)
                customer_data.get("name", ""),                              # customer_name
                customer_data.get("email", "").lower().strip() if customer_data.get("email") else None,  # customer_email
                customer_data.get("phone", ""),                             # customer_phone
                service_category,                                           # primary_service_category (FIXED)
                mapped_payload.get("specific_service_needed", ""),                # specific_service_requested (FIXED)
                zip_code,                                                   # service_zip_code (FIXED)
                service_county,                                             # service_county
                service_state,                                              # service_state
                None,                                                       # vendor_id (unassigned)
                "unassigned",                                               # status
                "normal",                                                   # priority
                form_identifier,                                            # source
                json.dumps(service_details),                                # service_details
                "",                                                         # service_city
                "simple",                                                   # service_complexity
                "medium",                                                   # estimated_duration
                False,                                                      # requires_emergency_response
                1.0,                                                        # classification_confidence
                f"Created via shared pipeline from {form_identifier}"       # classification_reasoning
            ))
            
            conn.commit()
            logger.info(f"✅ Shared pipeline created lead: {lead_id_str}")
            
        except Exception as e:
            logger.error(f"❌ Shared pipeline lead creation error: {e}")
            raise
        finally:
            if conn:
                conn.close()
        
        # Step 6: Create opportunity if needed
        opportunity_id = None
        if AppConfig.PIPELINE_ID and AppConfig.NEW_LEAD_STAGE_ID:
            logger.info(f"📈 Shared pipeline creating opportunity for {service_category} lead")
            
            ghl_api_client = GoHighLevelAPI(
                private_token=AppConfig.GHL_PRIVATE_TOKEN,
                location_id=AppConfig.GHL_LOCATION_ID
            )
            
            customer_name = customer_data["name"]
            
            opportunity_data = {
                'contactId': ghl_contact_data.get('id'),
                'pipelineId': AppConfig.PIPELINE_ID,
                'pipelineStageId': AppConfig.NEW_LEAD_STAGE_ID,
                'name': f"{customer_name} - {service_category}",
                'monetaryValue': 0,
                'status': 'open',
                'source': f"{form_identifier} (DSP Shared Pipeline)",
                'locationId': AppConfig.GHL_LOCATION_ID,
            }
            
            opportunity_response = ghl_api_client.create_opportunity(opportunity_data)
            
            if opportunity_response and opportunity_response.get('id'):
                opportunity_id = opportunity_response['id']
                logger.info(f"✅ Shared pipeline created opportunity: {opportunity_id}")
                
                # Update lead with opportunity ID
                try:
                    simple_db_instance.update_lead_opportunity_id(lead_id_str, opportunity_id)
                    logger.info(f"✅ Shared pipeline linked opportunity {opportunity_id} to lead {lead_id_str}")
                except Exception as e:
                    logger.warning(f"⚠️ Shared pipeline could not link opportunity ID: {e}")
            else:
                logger.error(f"❌ Shared pipeline failed to create opportunity: {opportunity_response}")
        else:
            logger.warning("⚠️ Shared pipeline: Pipeline not configured - skipping opportunity creation")
        
        return lead_id_str, opportunity_id
        
    except Exception as e:
        logger.error(f"❌ Shared pipeline error for contact {ghl_contact_data.get('id', 'unknown')}: {e}")
        raise

# --- CORRECT SERVICE CATEGORIES AND SERVICES FROM CSV ---
# 16 Categories with their specific services
DOCKSIDE_PROS_CATEGORIES = [
    "Boat and Yacht Repair",
    "Boat Charters and Rentals", 
    "Boat Hauling and Yacht Delivery",
    "Boat Maintenance",
    "Boat Towing",
    "Boater Resources",
    "Buying or Selling a Boat",
    "Docks, Seawalls and Lifts",
    "Dock and Slip Rental",
    "Engines and Generators",
    "Fuel Delivery",
    "Marine Systems",
    "Maritime Education and Training",
    "Waterfront Property",
    "Wholesale or Dealer Product Pricing",
    "Yacht Management"
]

DOCKSIDE_PROS_SERVICES = {
    # CATEGORY-LEVEL FORM IDENTIFIERS (ADDED - FIXES engines_generators ISSUE)
    "engines_generators": "Engines and Generators",
    "boat_and_yacht_repair": "Boat and Yacht Repair",
    "boat_charters_and_rentals": "Boat Charters and Rentals",
    "boat_hauling_and_yacht_delivery": "Boat Hauling and Yacht Delivery",
    "boat_maintenance": "Boat Maintenance",
    "boat_towing": "Boat Towing",
    "boater_resources": "Boater Resources",
    "buying_or_selling_a_boat": "Buying or Selling a Boat",
    "docks_seawalls_and_lifts": "Docks, Seawalls and Lifts",
    "dock_and_slip_rental": "Dock and Slip Rental",
    "fuel_delivery": "Fuel Delivery",
    "marine_systems": "Marine Systems",
    "maritime_education_and_training": "Maritime Education and Training",
    "waterfront_property": "Waterfront Property",
    "wholesale_or_dealer_product_pricing": "Wholesale or Dealer Product Pricing",
    "yacht_management": "Yacht Management",
    
    # Boat and Yacht Repair (7 services)
    "fiberglass_repair": "Boat and Yacht Repair",
    "welding_metal_fabrication": "Boat and Yacht Repair",
    "carpentry_woodwork": "Boat and Yacht Repair",
    "riggers_masts": "Boat and Yacht Repair",
    "jet_ski_repair": "Boat and Yacht Repair",
    "boat_canvas_upholstery": "Boat and Yacht Repair",
    "boat_decking_yacht_flooring": "Boat and Yacht Repair",
    
    # Boat Charters and Rentals (7 services)
    "boat_charters_rentals": "Boat Charters and Rentals",
    "boat_clubs": "Boat Charters and Rentals",
    "fishing_charters": "Boat Charters and Rentals",
    "yacht_catamaran_charters": "Boat Charters and Rentals",
    "sailboat_charters": "Boat Charters and Rentals",
    "efoil_kiteboarding_wing_surfing": "Boat Charters and Rentals",
    "dive_equipment_services": "Boat Charters and Rentals",
    
    # Boat Hauling and Yacht Delivery (2 services)
    "yacht_delivery": "Boat Hauling and Yacht Delivery",
    "boat_hauling_transport": "Boat Hauling and Yacht Delivery",
    
    # Boat Maintenance (11 services)
    "barnacle_cleaning": "Boat Maintenance",
    "boat_yacht_maintenance": "Boat Maintenance",
    "boat_bilge_cleaning": "Boat Maintenance",
    "boat_bottom_cleaning": "Boat Maintenance",
    "boat_detailing": "Boat Maintenance",
    "boat_oil_change": "Boat Maintenance",
    "boat_wrapping_marine_protection": "Boat Maintenance",
    "ceramic_coating": "Boat Maintenance",
    "jet_ski_maintenance": "Boat Maintenance",
    "yacht_armor": "Boat Maintenance",
    "yacht_fire_detection": "Boat Maintenance",
    
    # Boat Towing (2 services)
    "get_emergency_tow": "Boat Towing",
    "get_towing_membership": "Boat Towing",
    
    # Boater Resources (8 services)
    "yacht_wifi": "Boater Resources",
    "provisioning": "Boater Resources",
    "boat_yacht_parts": "Boater Resources",
    "boat_salvage": "Boater Resources",
    "yacht_photography": "Boater Resources",
    "yacht_videography": "Boater Resources",
    "yacht_crew_placement": "Boater Resources",
    "yacht_account_management": "Boater Resources",
    
    # Buying or Selling a Boat (10 services)
    "boat_dealers": "Buying or Selling a Boat",
    "yacht_dealers": "Buying or Selling a Boat",
    "boat_surveyors": "Buying or Selling a Boat",
    "boat_financing": "Buying or Selling a Boat",
    "boat_builders": "Buying or Selling a Boat",
    "boat_brokers": "Buying or Selling a Boat",
    "yacht_brokers": "Buying or Selling a Boat",
    "yacht_builders": "Buying or Selling a Boat",
    "boat_insurance": "Buying or Selling a Boat",
    "yacht_insurance": "Buying or Selling a Boat",
    
    # Docks, Seawalls and Lifts (4 services)
    "dock_seawall_builders_repair": "Docks, Seawalls and Lifts",
    "boat_lift_installers": "Docks, Seawalls and Lifts",
    "floating_dock_sales": "Docks, Seawalls and Lifts",
    "davit_hydraulic_platform": "Docks, Seawalls and Lifts",
    
    # Dock and Slip Rental (2 services)
    "dock_slip_rental": "Dock and Slip Rental",
    "rent_my_dock": "Dock and Slip Rental",
    
    # Engines and Generators (8 services)
    "outboard_engine_service": "Engines and Generators",
    "outboard_engine_sales": "Engines and Generators",
    "inboard_engine_service": "Engines and Generators",
    "inboard_engine_sales": "Engines and Generators",
    "diesel_engine_service": "Engines and Generators",
    "diesel_engine_sales": "Engines and Generators",
    "generator_service_repair": "Engines and Generators",
    "generator_sales": "Engines and Generators",
    
    # Fuel Delivery (1 service)
    "fuel_delivery": "Fuel Delivery",
    
    # Marine Systems (8 services)
    "yacht_ac_sales": "Marine Systems",
    "yacht_ac_service": "Marine Systems",
    "boat_electrical_service": "Marine Systems",
    "yacht_plumbing": "Marine Systems",
    "boat_sound_systems": "Marine Systems",
    "boat_lighting": "Marine Systems",
    "yacht_stabilizers_seakeepers": "Marine Systems",
    "yacht_refrigeration_watermakers": "Marine Systems",
    
    # Maritime Education and Training (4 services)
    "maritime_certification": "Maritime Education and Training",
    "maritime_academy": "Maritime Education and Training",
    "sailing_schools": "Maritime Education and Training",
    "yacht_training": "Maritime Education and Training",
    
    # Waterfront Property (3 services)
    "waterfront_homes_sale": "Waterfront Property",
    "sell_waterfront_home": "Waterfront Property",
    "new_waterfront_developments": "Waterfront Property",
    
    # Wholesale or Dealer Product Pricing (1 service)
    "wholesale_dealer_pricing": "Wholesale or Dealer Product Pricing",
    
    # Yacht Management (1 service)
    "yacht_management": "Yacht Management",
    
    # Vendor Applications (form type detection)
    "vendor_application": "Vendor Application",
    "network_application": "Vendor Application",
    "join_network": "Vendor Application",
    "provider_signup": "Vendor Application",
    
    # General fallback
    "general_inquiry": "Boater Resources",
    "contact": "Boater Resources",
    "quote_request": "Boater Resources"
}

def get_direct_service_category(form_identifier: str) -> str:
    """
    Direct service category mapping - NO AI processing
    Uses dictionary lookup with keyword matching based on actual CSV data
    """
    form_lower = form_identifier.lower()
    
    # Direct exact matches first
    if form_lower in DOCKSIDE_PROS_SERVICES:
        category = DOCKSIDE_PROS_SERVICES[form_lower]
        logger.info(f"🎯 Direct service mapping: {form_identifier} → {category}")
        return category
    
    # Keyword matching for partial matches
    for service_key, category in DOCKSIDE_PROS_SERVICES.items():
        if service_key.replace("_", "") in form_lower.replace("_", ""):
            logger.info(f"🎯 Keyword service mapping: {form_identifier} → {category} (matched: {service_key})")
            return category
    
    # Default fallback
    default_category = "Boater Resources"
    logger.info(f"🎯 Default service mapping: {form_identifier} → {default_category}")
    return default_category


def find_matching_service(specific_service_text: str) -> str:
    """
    Find the best matching service from the specific service text
    This is used for vendor matching (specific service, not category)
    """
    if not specific_service_text:
        return "boat_yacht_maintenance"  # Default fallback
    
    service_lower = specific_service_text.lower()
    
    # Direct service name matching
    for service_key in DOCKSIDE_PROS_SERVICES.keys():
        service_name = service_key.replace("_", " ")
        if service_name in service_lower or service_key in service_lower:
            logger.info(f"🎯 Direct service match: '{specific_service_text}' → {service_key}")
            return service_key
    
    # Fallback to maintenance
    logger.info(f"🎯 Service fallback: '{specific_service_text}' → boat_yacht_maintenance")
    return "boat_yacht_maintenance"

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
        
        "Your Vessel Manufacturer? ": "vessel_make",
        "Vessel Make": "vessel_make",
        "Boat Make": "vessel_make",
        "Manufacturer": "vessel_make",
        
        "Your Vessel Model": "vessel_model",
        "Vessel Model": "vessel_model", 
        "Your Vessel Length": "vessel_length_ft",
        "Vessel Length (ft)": "vessel_length_ft",
        "Length of Vessel in Feet": "vessel_length_ft",
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
        
        # Vendor category and service fields
        "service_categories_selected": "service_categories_selected",  # No change needed
        "service_categorires_selected": "service_categories_selected",  # Fix typo if it exists
        
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

def get_form_configuration(form_identifier: str) -> Dict[str, Any]:
    """
    Direct form configuration - NO AI processing
    Returns configuration based on form identifier patterns
    """
    
    # Extract service category using direct mapping
    service_category = get_direct_service_category(form_identifier)
    
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
    Direct validation for form submissions - NO AI processing
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
    
    # Check for unexpected fields (informational) - using field_mapper
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
    Process Elementor payload into GHL format - PRESERVE ALL FIELDS
    Direct field mapping only - NO AI processing
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
    
    # Process each field from mapped payload - PRESERVE EVERYTHING
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
                # Custom fields go into customFields array using field_mapper
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
        # Skip non-field configuration items and service_category for vendor applications
        if ghl_key in ["form_type", "priority", "requires_immediate_routing", "expected_fields"]:
            continue
        
        # Don't override service_category for vendor applications - let form data take precedence
        if ghl_key == "service_category" and form_config.get("form_type") == "vendor_application":
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

    # SPECIAL HANDLING: For vendor applications, ensure all vendor-specific fields are properly mapped
    if form_config.get("form_type") == "vendor_application":
        # 1. Handle NEW multi-step service category structure
        # Primary service category (single selection)
        primary_service_category = elementor_payload.get('primary_service_category', '')
        if primary_service_category:
            primary_category_field = field_mapper.get_ghl_field_details("primary_service_category")
            if primary_category_field and primary_category_field.get("id"):
                field_exists = any(cf["id"] == primary_category_field["id"] for cf in custom_fields_array)
                if not field_exists:
                    custom_fields_array.append({
                        "id": primary_category_field["id"],
                        "value": primary_service_category
                    })
                    logger.info(f"✅ Added Primary Service Category field: {primary_service_category}")
        
        # Combined service categories (primary + additional, max 3 total)
        combined_categories = []
        if primary_service_category:
            combined_categories.append(primary_service_category)
        
        # Add additional categories (up to 2 more)
        additional_categories = elementor_payload.get('additional_categories', [])
        if isinstance(additional_categories, list):
            combined_categories.extend(additional_categories[:2])  # Max 2 additional
        elif isinstance(additional_categories, str) and additional_categories:
            # Handle comma-separated string
            additional_list = [cat.strip() for cat in additional_categories.split(',')]
            combined_categories.extend(additional_list[:2])
        
        # Store combined categories in the general service_category field for backward compatibility
        if combined_categories:
            service_category_field = field_mapper.get_ghl_field_details("service_category")
            if service_category_field and service_category_field.get("id"):
                field_exists = any(cf["id"] == service_category_field["id"] for cf in custom_fields_array)
                if not field_exists:
                    combined_categories_str = ', '.join(combined_categories)
                    custom_fields_array.append({
                        "id": service_category_field["id"],
                        "value": combined_categories_str
                    })
                    logger.info(f"✅ Added Combined Service Categories field: {combined_categories_str}")
            else:
                logger.warning(f"⚠️ Could not find Service Category field details in field_mapper")
        
        # 2. Handle services provided (from multi-step selection)
        # Combine primary services and additional services
        all_services = []
        
        # Primary services from the primary category
        primary_services = elementor_payload.get('primary_services', [])
        if isinstance(primary_services, list):
            all_services.extend(primary_services)
        elif isinstance(primary_services, str) and primary_services:
            primary_list = [svc.strip() for svc in primary_services.split(',')]
            all_services.extend(primary_list)
        
        # Additional services from additional categories
        additional_services = elementor_payload.get('additional_services', [])
        if isinstance(additional_services, list):
            all_services.extend(additional_services)
        elif isinstance(additional_services, str) and additional_services:
            additional_list = [svc.strip() for svc in additional_services.split(',')]
            all_services.extend(additional_list)
        
        # Store combined services
        if all_services:
            services_provided_field = field_mapper.get_ghl_field_details("services_provided")
            if services_provided_field and services_provided_field.get("id"):
                field_exists = any(cf["id"] == services_provided_field["id"] for cf in custom_fields_array)
                if not field_exists:
                    combined_services_str = ', '.join(all_services)
                    custom_fields_array.append({
                        "id": services_provided_field["id"],
                        "value": combined_services_str
                    })
                    logger.info(f"✅ Added Combined Services Provided field: {combined_services_str}")
        
        # Also check for legacy services_provided field for backward compatibility
        legacy_services = elementor_payload.get('services_provided', '')
        if legacy_services and not all_services:
            services_provided_field = field_mapper.get_ghl_field_details("services_provided")
            if services_provided_field and services_provided_field.get("id"):
                field_exists = any(cf["id"] == services_provided_field["id"] for cf in custom_fields_array)
                if not field_exists:
                    custom_fields_array.append({
                        "id": services_provided_field["id"],
                        "value": legacy_services
                    })
                    logger.info(f"✅ Added Legacy Services Provided field: {legacy_services}")
        
        # 3. Handle service ZIP codes (use existing service_zip_codes field)
        # Store coverage data in service_zip_codes field based on coverage type
        coverage_type = elementor_payload.get('coverage_type', 'county')
        service_coverage_area = elementor_payload.get('service_coverage_area', '')
        
        # Get the service_zip_codes field which exists in GHL
        service_zip_codes_field = field_mapper.get_ghl_field_details("service_zip_codes")
        if service_zip_codes_field and service_zip_codes_field.get("id"):
            field_exists = any(cf["id"] == service_zip_codes_field["id"] for cf in custom_fields_array)
            if not field_exists:
                # Format the coverage data appropriately
                coverage_value = ""
                
                if coverage_type == "global":
                    coverage_value = "GLOBAL COVERAGE"
                elif coverage_type == "national":
                    coverage_value = "NATIONAL COVERAGE (USA)"
                elif coverage_type == "state":
                    coverage_states = elementor_payload.get('coverage_states', [])
                    if coverage_states:
                        coverage_value = f"STATES: {', '.join(coverage_states)}"
                elif coverage_type == "county":
                    coverage_counties = elementor_payload.get('coverage_counties', [])
                    if coverage_counties:
                        coverage_value = f"COUNTIES: {'; '.join(coverage_counties)}"
                elif coverage_type == "zip":
                    zip_codes = elementor_payload.get('service_zip_codes', '')
                    if zip_codes:
                        coverage_value = f"ZIP CODES: {zip_codes}"
                
                # If we have coverage data, add it to the field
                if coverage_value:
                    custom_fields_array.append({
                        "id": service_zip_codes_field["id"],
                        "value": coverage_value
                    })
                    logger.info(f"✅ Added Service Coverage to service_zip_codes field: {coverage_value}")
        
        # 4. Add taking new work field
        taking_new_work = elementor_payload.get('taking_new_work', '')
        if taking_new_work:
            taking_work_field = field_mapper.get_ghl_field_details("taking_new_work")
            if taking_work_field and taking_work_field.get("id"):
                field_exists = any(cf["id"] == taking_work_field["id"] for cf in custom_fields_array)
                if not field_exists:
                    custom_fields_array.append({
                        "id": taking_work_field["id"],
                        "value": taking_new_work
                    })
                    logger.info(f"✅ Added Taking New Work field: {taking_new_work}")
        
        # 5. Add reviews URL field
        reviews_url = elementor_payload.get('reviews__google_profile_url', '')
        if reviews_url:
            reviews_field = field_mapper.get_ghl_field_details("reviews__google_profile_url")
            if reviews_field and reviews_field.get("id"):
                field_exists = any(cf["id"] == reviews_field["id"] for cf in custom_fields_array)
                if not field_exists:
                    custom_fields_array.append({
                        "id": reviews_field["id"],
                        "value": reviews_url
                    })
                    logger.info(f"✅ Added Reviews URL field: {reviews_url}")
        
        # 6. Add vendor preferred contact method
        contact_method = elementor_payload.get('vendor_preferred_contact_method', '')
        if contact_method:
            contact_method_field = field_mapper.get_ghl_field_details("vendor_preferred_contact_method")
            if contact_method_field and contact_method_field.get("id"):
                field_exists = any(cf["id"] == contact_method_field["id"] for cf in custom_fields_array)
                if not field_exists:
                    custom_fields_array.append({
                        "id": contact_method_field["id"],
                        "value": contact_method
                    })
                    logger.info(f"✅ Added Vendor Preferred Contact Method field: {contact_method}")
        
        # 7. Add vendor address information if available
        if elementor_payload.get('address1'):
            vendor_address_field = field_mapper.get_ghl_field_details("vendor_address")
            if vendor_address_field and vendor_address_field.get("id"):
                field_exists = any(cf["id"] == vendor_address_field["id"] for cf in custom_fields_array)
                if not field_exists:
                    custom_fields_array.append({
                        "id": vendor_address_field["id"],
                        "value": elementor_payload.get('address1', '')
                    })
                    logger.info(f"✅ Added Vendor Address field")

    # Add customFields array to payload if we have any custom fields
    if custom_fields_array:
        final_ghl_payload["customFields"] = custom_fields_array
        logger.info(f"✅ Added {len(custom_fields_array)} custom fields to GHL payload")
        
        # Log each custom field being sent
        for i, field in enumerate(custom_fields_array):
            logger.info(f"  Custom Field [{i}]: ID={field['id']}, Value='{field['value']}'")
    else:
        logger.warning("⚠️ No custom fields added to GHL payload - this may indicate a mapping issue")
    
    return final_ghl_payload

def convert_service_areas_to_counties(zip_codes_input) -> Dict[str, Any]:
    """
    Convert ZIP codes to counties for vendor applications
    Direct location service conversion - NO AI processing
    Handles both string and list input formats
    """
    if not zip_codes_input:
        return {"counties": [], "zip_codes": [], "conversion_success": False}
    
    # Handle both list and string input
    if isinstance(zip_codes_input, list):
        # If it's already a list, use it directly but clean up each entry
        zip_codes = [zip_code.strip() for zip_code in zip_codes_input if zip_code and zip_code.strip()]
    elif isinstance(zip_codes_input, str):
        # If it's a string, split by comma
        zip_codes = [zip_code.strip() for zip_code in zip_codes_input.split(',') if zip_code.strip()]
    else:
        # Unknown format
        return {"counties": [], "zip_codes": [], "conversion_success": False}
    
    if not zip_codes:
        return {"counties": [], "zip_codes": [], "conversion_success": False}
    
    # Convert ZIP codes to counties using location service
    counties = []
    successful_conversions = 0
    conversion_details = []
    
    for zip_code in zip_codes:
        zip_str = zip_code.strip()
        
        # Validate ZIP code format
        if len(zip_str) == 5 and zip_str.isdigit():
            location_data = location_service.zip_to_location(zip_str)
            
            if not location_data.get('error'):
                county = location_data.get('county')
                state = location_data.get('state')
                city = location_data.get('city')
                
                if county and state:
                    county_entry = f"{county}, {state}"
                    if county_entry not in counties:
                        counties.append(county_entry)
                    
                    conversion_details.append({
                        "zip_code": zip_str,
                        "county": county,
                        "state": state,
                        "city": city,
                        "success": True
                    })
                    successful_conversions += 1
                    logger.info(f"🗺️ Vendor Application: ZIP {zip_str} → {county_entry}")
                else:
                    conversion_details.append({
                        "zip_code": zip_str,
                        "error": "No county/state data",
                        "success": False
                    })
                    logger.warning(f"⚠️ Vendor Application: ZIP {zip_str} resolved but missing county/state")
            else:
                conversion_details.append({
                    "zip_code": zip_str,
                    "error": location_data['error'],
                    "success": False
                })
                logger.warning(f"⚠️ Vendor Application: Could not convert ZIP {zip_str}: {location_data['error']}")
        else:
            conversion_details.append({
                "zip_code": zip_str,
                "error": "Invalid ZIP code format",
                "success": False
            })
            logger.warning(f"⚠️ Vendor Application: Invalid ZIP code format: '{zip_str}'")
    
    conversion_rate = (successful_conversions / len(zip_codes)) * 100 if zip_codes else 0
    
    return {
        "counties": counties,
        "zip_codes": zip_codes,
        "conversion_success": successful_conversions > 0,
        "conversion_rate": conversion_rate,
        "conversion_details": conversion_details,
        "successful_conversions": successful_conversions,
        "total_zip_codes": len(zip_codes)
    }

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
@router.post("/elementor/{form_identifier}/")
async def handle_clean_elementor_webhook(
    form_identifier: str, 
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Clean webhook handler for ALL Elementor form submissions.
    Direct processing only - NO AI interference.
    Preserves ALL form data exactly as received from WordPress.
    """
    start_time = time.time()
    
    try:
        # Parse incoming payload (supports both JSON and form-encoded data)
        elementor_payload = await parse_webhook_payload(request)
        logger.info(f"📥 Clean Elementor Webhook received for form '{form_identifier}': {json.dumps(elementor_payload, indent=2)}")
        
        # Debug logging for key vendor fields
        logger.info(f"📋 Key vendor fields in normalized payload:")
        logger.info(f"   - vendor_company_name: '{elementor_payload.get('vendor_company_name')}'")
        logger.info(f"   - service_categories_selected: '{elementor_payload.get('service_categories_selected')}'")
        logger.info(f"   - services_provided: '{elementor_payload.get('services_provided')}'")
        logger.info(f"   - service_zip_codes: '{elementor_payload.get('service_zip_codes')}'")

        # Get direct form configuration - NO AI
        form_config = get_form_configuration(form_identifier)
        logger.info(f"📋 Direct form config for '{form_identifier}': {form_config}")

        # Validate form submission - Direct validation only
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
        ghl_api_client = GoHighLevelAPI(
            location_api_key=AppConfig.GHL_LOCATION_API,
            private_token=AppConfig.GHL_PRIVATE_TOKEN, 
            location_id=AppConfig.GHL_LOCATION_ID,
            agency_api_key=AppConfig.GHL_AGENCY_API_KEY,
            company_id=AppConfig.GHL_COMPANY_ID
        )
        logger.info(f"🔑 GHL API client initialized")

        # Process payload into GHL format - PRESERVE ALL FIELDS
        final_ghl_payload = process_payload_to_ghl_format(elementor_payload, form_config)
        
        # Handle vendor application specific coverage data processing
        if form_config.get("form_type") == "vendor_application":
            coverage_type = elementor_payload.get('coverage_type', 'county')
            
            # For ZIP code coverage type, attempt to convert to counties
            if coverage_type == 'zip':
                service_zip_codes = elementor_payload.get('service_zip_codes', '')
                
                if service_zip_codes:
                    logger.info(f"🔄 Converting service ZIP codes to counties for vendor application")
                    
                    county_conversion = convert_service_areas_to_counties(service_zip_codes)
                    
                    if county_conversion['conversion_success']:
                        counties_str = ', '.join(county_conversion['counties'])
                        
                        # Add county information to GHL payload
                        service_counties_field = field_mapper.get_ghl_field_details("service_counties")
                        
                        if not final_ghl_payload.get("customFields"):
                            final_ghl_payload["customFields"] = []
                        
                        if service_counties_field and service_counties_field.get("id"):
                            # Check if field already exists
                            field_exists = any(cf["id"] == service_counties_field["id"] for cf in final_ghl_payload["customFields"])
                            if not field_exists:
                                final_ghl_payload["customFields"].append({
                                    "id": service_counties_field["id"],
                                    "value": counties_str
                                })
                                logger.info(f"✅ Added service_counties to GHL payload: {counties_str}")
                        
                        logger.info(f"✅ Vendor Application: Converted {county_conversion['successful_conversions']}/{county_conversion['total_zip_codes']} ZIP codes")
                        logger.info(f"📍 Vendor Application: Service counties: {', '.join(county_conversion['counties'])}")
                        
                        # Store the county conversion result in the elementor_payload for database storage
                        elementor_payload['_converted_counties'] = county_conversion['counties']
                    else:
                        logger.warning(f"⚠️ Vendor Application: Could not convert any ZIP codes to counties")
            
            # Log what coverage data we have for debugging
            logger.info(f"🌍 Vendor coverage processing complete:")
            logger.info(f"   Coverage Type: {coverage_type}")
            logger.info(f"   Coverage Area: {elementor_payload.get('service_coverage_area', 'Not specified')}")
            logger.info(f"   Coverage States: {elementor_payload.get('coverage_states', [])}")
            logger.info(f"   Coverage Counties: {elementor_payload.get('coverage_counties', [])}")
            logger.info(f"   Service ZIP Codes: {elementor_payload.get('service_zip_codes', 'Not specified')}")
        
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

        # Search for existing contact by email AND phone
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
            existing_ids = {contact.get('id') for contact in all_search_results}
            for phone_contact in phone_search_results:
                if phone_contact.get('id') not in existing_ids:
                    all_search_results.append(phone_contact)
        
        if all_search_results:
            logger.info(f"📋 Search returned {len(all_search_results)} potential matches")
            
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
                        logger.info(f"✅ Found PHONE match: {existing_ghl_contact.get('id')}")
                        break
        else:
            logger.info("📋 No search results returned for email or phone - contact appears to be new")

        # Create or update contact
        if existing_ghl_contact:
            # UPDATE EXISTING CONTACT
            final_ghl_contact_id = existing_ghl_contact["id"]
            action_taken = "updated"
            logger.info(f"🔄 Updating existing GHL contact {final_ghl_contact_id}")
            
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
            
            if created_contact_response and isinstance(created_contact_response, dict):
                if not created_contact_response.get("error") and created_contact_response.get("id"):
                    final_ghl_contact_id = created_contact_response["id"]
                    operation_successful = True
                    logger.info(f"✅ Successfully created new GHL contact {final_ghl_contact_id}")
                else:
                    logger.error(f"❌ GHL contact creation failed: {created_contact_response}")
                    api_response_details = created_contact_response
            else:
                logger.error(f"❌ Unexpected response from GHL API: {created_contact_response}")
                api_response_details = {"error": True, "unexpected_response": created_contact_response}

        # Handle success/failure and log results
        processing_time = round(time.time() - start_time, 3)
        
        if operation_successful and final_ghl_contact_id:
            logger.info(f"✅ Successfully {action_taken} GHL contact {final_ghl_contact_id} for form '{form_identifier}' in {processing_time}s")
            
            # Log successful activity to database
            simple_db_instance.log_activity(
                event_type=f"clean_webhook_{action_taken}",
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
            
            # Create vendor record in database
            if form_config.get("form_type") == "vendor_application" and final_ghl_contact_id:
                try:
                    # Extract vendor data from payload
                    vendor_company_name = elementor_payload.get('vendor_company_name', '')
                    vendor_first_name = elementor_payload.get('firstName', '')
                    vendor_last_name = elementor_payload.get('lastName', '')
                    vendor_email = elementor_payload.get('email', '')
                    vendor_phone = elementor_payload.get('phone', '')
                    
                    # Process service categories - NEW LOGIC for primary + additional structure
                    primary_service_category = elementor_payload.get('primary_service_category', '')
                    service_categories = elementor_payload.get('service_categories', '')
                    
                    # Build final categories list (primary + additional up to 3 total)
                    categories_list = []
                    if primary_service_category:
                        categories_list.append(primary_service_category)
                        logger.info(f"📋 Primary service category: {primary_service_category}")
                    
                    if service_categories:
                        # Parse additional categories from service_categories field
                        additional_categories = [s.strip() for s in service_categories.split(',') if s.strip() and s.strip() != primary_service_category]
                        categories_list.extend(additional_categories[:2])  # Max 2 additional
                        logger.info(f"📋 Service categories: {service_categories}")
                        logger.info(f"📋 Final categories list: {categories_list}")
                    
                    # Create JSON for database storage
                    if categories_list:
                        service_categories_json = json.dumps(categories_list)
                        logger.info(f"📋 Final service categories JSON: {service_categories_json}")
                    else:
                        # Fallback if no categories provided
                        service_categories_json = json.dumps(['General Services'])
                        logger.warning(f"📋 No categories provided, using fallback")
                    
                    # Extract specific services offered
                    services_provided = elementor_payload.get('services_provided', '')
                    if services_provided:
                        # These are the specific services (Boat Detailing, Ceramic Coating, etc.)
                        services_list = [s.strip() for s in services_provided.split(',') if s.strip()]
                        services_offered_json = json.dumps(services_list)
                        logger.info(f"📋 Services provided: {services_provided}")
                        logger.info(f"📋 Parsed services: {services_list}")
                    else:
                        services_offered_json = json.dumps([])
                        logger.info(f"📋 No specific services provided")
                    
                    # Extract coverage type and coverage areas
                    coverage_type = elementor_payload.get('coverage_type', 'county')
                    logger.info(f"📋 Coverage type: {coverage_type}")
                    
                    # Handle coverage states (for state-level coverage)
                    coverage_states = elementor_payload.get('coverage_states', [])
                    if isinstance(coverage_states, list):
                        coverage_states_json = json.dumps(coverage_states)
                        logger.info(f"📋 Coverage states: {coverage_states}")
                    elif isinstance(coverage_states, str) and coverage_states:
                        # If it's a comma-separated string
                        states_list = [s.strip() for s in coverage_states.split(',') if s.strip()]
                        coverage_states_json = json.dumps(states_list)
                        logger.info(f"📋 Coverage states parsed from string: {states_list}")
                    else:
                        coverage_states_json = json.dumps([])
                    
                    # Handle coverage data based on coverage type
                    service_coverage_area = elementor_payload.get('service_coverage_area', '')
                    coverage_counties_json = json.dumps([])
                    
                    # Process coverage data based on type
                    if coverage_type == 'state':
                        # Already handled above in coverage_states
                        pass
                    
                    elif coverage_type == 'county':
                        # Handle county coverage from the widget
                        coverage_counties = elementor_payload.get('coverage_counties', [])
                        if isinstance(coverage_counties, list) and coverage_counties:
                            coverage_counties_json = json.dumps(coverage_counties)
                            logger.info(f"📋 Coverage counties: {coverage_counties}")
                        elif isinstance(coverage_counties, str) and coverage_counties:
                            # Parse comma-separated counties
                            counties_list = [c.strip() for c in coverage_counties.split(',') if c.strip()]
                            coverage_counties_json = json.dumps(counties_list)
                            logger.info(f"📋 Parsed coverage counties: {counties_list}")
                    
                    elif coverage_type == 'zip':
                        # Handle ZIP code coverage
                        service_zip_codes = elementor_payload.get('service_zip_codes', '')
                        if service_zip_codes:
                            # Check if we have converted counties from earlier ZIP conversion
                            converted_counties = elementor_payload.get('_converted_counties', [])
                            if converted_counties:
                                coverage_counties_json = json.dumps(converted_counties)
                                logger.info(f"📋 Using converted counties from ZIP codes: {converted_counties}")
                            else:
                                # Store ZIP codes as coverage
                                if isinstance(service_zip_codes, str):
                                    zips_list = [z.strip() for z in service_zip_codes.split(',') if z.strip()]
                                    coverage_counties_json = json.dumps(zips_list)
                                    logger.info(f"📋 Storing ZIP codes as coverage: {zips_list}")
                    
                    elif coverage_type in ['global', 'national']:
                        # For global/national, we store empty counties but note in service_coverage_area
                        coverage_counties_json = json.dumps([])
                        logger.info(f"🌍 {coverage_type.title()} coverage - no specific counties")
                    
                    logger.info(f"🗺️ Final coverage data:")
                    logger.info(f"   Coverage Type: {coverage_type}")
                    logger.info(f"   Coverage States: {coverage_states_json}")
                    logger.info(f"   Coverage Counties: {coverage_counties_json}")
                    logger.info(f"   Service Categories: {service_categories_json}")
                    logger.info(f"   Services Offered: {services_offered_json}")
                    
                    # Get account
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
                        logger.info(f"📋 Vendor already exists: {existing_vendor['id']}")
                        vendor_id = existing_vendor['id']
                        
                        # Update existing vendor with new information
                        try:
                            # Update service categories and coverage if provided
                            update_data = {}
                            if service_categories_json != json.dumps(['General Services']):
                                update_data['service_categories'] = service_categories_json
                            if coverage_counties_json != json.dumps([]):
                                update_data['coverage_counties'] = coverage_counties_json
                            
                            if update_data:
                                # You may need to add an update_vendor method to simple_db_instance
                                logger.info(f"🔄 Would update vendor {vendor_id} with: {update_data}")
                        except Exception as update_error:
                            logger.warning(f"⚠️ Failed to update existing vendor: {update_error}")
                    else:
                        # Create new vendor record
                        primary_category = elementor_payload.get('primary_service_category', '')
                        taking_work = elementor_payload.get('taking_new_work', 'Yes') == 'Yes'
                        
                        vendor_id = simple_db_instance.create_vendor(
                            account_id=account_id,
                            name=f"{vendor_first_name} {vendor_last_name}".strip(),
                            email=vendor_email,
                            company_name=vendor_company_name,
                            phone=vendor_phone,
                            ghl_contact_id=final_ghl_contact_id,
                            status='pending',  # Start as pending until approved
                            service_categories=service_categories_json,  # Categories like "Boat Maintenance"
                            services_offered=services_offered_json,      # Specific services like "Boat Detailing"
                            coverage_type=coverage_type,                 # state, county, zip, etc.
                            coverage_states=coverage_states_json,        # ["FL", "GA"] for state coverage
                            coverage_counties=coverage_counties_json,    # Counties or ZIP codes
                            primary_service_category=primary_category,   # Primary category from multi-step flow
                            taking_new_work=taking_work                  # Boolean for taking new work
                        )
                        logger.info(f"✅ Created vendor record: {vendor_id}")
                        logger.info(f"   Company: {vendor_company_name}")
                        logger.info(f"   Name: {vendor_first_name} {vendor_last_name}")
                        logger.info(f"   Email: {vendor_email}")
                        logger.info(f"   Services: {service_categories_json}")
                        logger.info(f"   Coverage: {coverage_counties_json}")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to create vendor record: {str(e)}")
                    logger.error(f"   Error type: {type(e).__name__}")
                    logger.error(f"   Service categories selected: {elementor_payload.get('service_categories_selected', 'NOT_FOUND')}")
                    logger.error(f"   Vendor company name: {elementor_payload.get('vendor_company_name', 'NOT_FOUND')}")
                    logger.error(f"   Service zip codes: {elementor_payload.get('service_zip_codes', 'NOT_FOUND')}")
                    
                    # Log the full elementor payload for debugging
                    logger.error(f"   Full payload keys: {list(elementor_payload.keys())}")
                    
                    # Continue processing even if vendor record fails - don't break the webhook
                    pass
            
            # Trigger background tasks based on form type
            if form_config.get("requires_immediate_routing"):
                background_tasks.add_task(
                    trigger_clean_lead_routing_workflow, 
                    ghl_contact_id=final_ghl_contact_id,
                    form_identifier=form_identifier,
                    form_config=form_config,
                    form_data=elementor_payload
                )
            
            # NOTE: Opportunity creation now handled in background task for client leads
            logger.info("ℹ️ Opportunity creation will be handled by background task if needed")

            return {
                "status": "success", 
                "message": f"Clean webhook processed successfully. GHL contact {final_ghl_contact_id} {action_taken}.",
                "contact_id": final_ghl_contact_id,
                "action": action_taken,
                "form_type": form_config.get("form_type"),
                "service_category": form_config.get("service_category"),
                "processing_time_seconds": processing_time,
                "validation_warnings": validation_result.get("warnings", []),
                "custom_fields_processed": len(final_ghl_payload.get("customFields", [])),
                "processing_method": "direct_only_no_ai"
            }
        else:
            # Operation failed
            error_message = f"Failed to {action_taken} GHL contact for form '{form_identifier}'"
            logger.error(f"❌ {error_message}. API Response: {api_response_details}")
            
            simple_db_instance.log_activity(
                event_type="clean_webhook_ghl_failure",
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
            event_type="clean_webhook_bad_json",
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
        logger.exception(f"💥 Critical error processing Clean Elementor webhook for form '{form_identifier}' after {processing_time}s: {e}")
        simple_db_instance.log_activity(
            event_type="clean_webhook_exception",
            event_data={
                "form": form_identifier,
                "processing_time_seconds": processing_time,
                "error_class": e.__class__.__name__
            },
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

async def trigger_clean_lead_routing_workflow(
    ghl_contact_id: str, 
    form_identifier: str, 
    form_config: Dict[str, Any],
    form_data: Dict[str, Any]
):
    """
    Clean background task for lead routing - NO AI processing
    Direct vendor matching using existing lead_routing_service
    """
    logger.info(f"🚀 CLEAN BACKGROUND TASK: Processing lead for contact {ghl_contact_id} from form '{form_identifier}'")
    
    try:
        # Get account information
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
 
        # Direct service classification (NO AI)
        service_category = form_config.get("service_category", "No Category")
        
        # Extract customer data directly from form (NO PHONE)
        customer_data = {
            "name": f"{form_data.get('firstName', '')} {form_data.get('lastName', '')}".strip(),
            "email": form_data.get("email", ""),
            "phone": form_data.get("phone", "")
        }
        
        # FIXED CODE - Use field mapping system like contact creation (works for all 16 form types)
        mapped_payload = field_mapper.map_payload(form_data, industry="marine")
        logger.info(f"🔄 Lead creation using field mapping. Original keys: {list(form_data.keys())}, Mapped keys: {list(mapped_payload.keys())}")
        
        # Create service_details from ALL mapped fields (preserves all form data)
        service_details = {}
        
        # Standard fields that have dedicated database columns (don't duplicate in service_details)
        standard_lead_fields = {
            "firstName", "lastName", "email", "phone", "primary_service_category",
            "customer_zip_code", "specific_service_requested"
        }
        
        # Store ALL other fields in service_details (preserves all 16 form types)
        for field_key, field_value in mapped_payload.items():
            # Skip empty values and standard fields (those go in dedicated columns)
            if field_value == "" or field_value is None or field_key in standard_lead_fields:
                continue
                
            service_details[field_key] = field_value
            
        # Add form metadata (NO PHONE)
        service_details.update({
            "form_source": form_identifier,
            "submission_time": form_data.get("Time", ""),
            "submission_date": form_data.get("Date", ""),
            "processing_method": "direct_mapping"
        })
        
        logger.info(f"📦 Created service_details with {len(service_details)} fields from mapped payload")

        # FIXED: Convert ZIP to county for lead routing (CRITICAL FIX FOR VENDOR MATCHING)
        zip_code = mapped_payload.get("zip_code_of_service", "")
        service_county = ""
        service_state = ""
        
        if zip_code and len(zip_code) == 5 and zip_code.isdigit():
            logger.info(f"🗺️ Converting ZIP {zip_code} to county for lead routing")
            location_data = location_service.zip_to_location(zip_code)
            
            if not location_data.get('error'):
                county = location_data.get('county', '')
                state = location_data.get('state', '')
                if county and state:
                    service_county = f"{county}, {state}"  # Format: "Miami-Dade, FL"
                    service_state = state
                    logger.info(f"✅ ZIP {zip_code} → {service_county}")
                else:
                    logger.warning(f"⚠️ ZIP {zip_code} conversion incomplete: county={county}, state={state}")
            else:
                logger.warning(f"⚠️ Could not convert ZIP {zip_code}: {location_data['error']}")
        else:
            logger.warning(f"⚠️ Invalid ZIP code format: '{zip_code}' - service_county will remain NULL")

        # FIXED: Direct database INSERT using actual available variables
        conn = None
        lead_id = None  # Initialize lead_id to prevent UnboundLocalError
        try:
            lead_id = str(uuid.uuid4())  # Set lead_id early so it can be used
            conn = simple_db_instance._get_conn()
            cursor = conn.cursor()
            
            # Get service values from mapped payload (mapped from GHL custom fields)
            specific_service_requested = mapped_payload.get("specific_service_needed", "")  # From GHL field FT85QGi0tBq1AfVGNJ9v
            
            # FIXED: INSERT using actual database schema field names (26 fields)
            cursor.execute('''
            INSERT INTO leads (
                id, account_id, ghl_contact_id, ghl_opportunity_id, customer_name,
                customer_email, customer_phone, primary_service_category, specific_service_requested,
                customer_zip_code, service_county, service_state, vendor_id, 
                assigned_at, status, priority, source, service_details, 
                service_zip_code, service_city, specific_service_requested,
                service_complexity, estimated_duration, requires_emergency_response, 
                classification_confidence, classification_reasoning
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            lead_id,                                                      # id
            account_id,                                                   # account_id  
            ghl_contact_id,                                               # ghl_contact_id
            None,                                                         # ghl_opportunity_id (set later)
            customer_data.get("name", ""),                                # customer_name
            customer_data.get("email", "").lower().strip() if customer_data.get("email") else None,  # customer_email
            customer_data.get("phone", ""),                               # customer_phone
            service_category,                                             # primary_service_category (from form_config)
            specific_service_requested,                                   # specific_service_requested (from GHL field)
            zip_code,                                                     # customer_zip_code
            service_county,                                               # service_county
            service_state,                                                # service_state
            None,                                                         # vendor_id (NULL initially)
            None,                                                         # assigned_at (NULL initially)
            "unassigned",                                                 # status
            "normal",                                                     # priority  
            f"{form_identifier} (DSP)",                                   # source
            json.dumps(service_details),                                  # service_details
            zip_code,                                                     # service_zip_code 
            "",                                                           # service_city
            "[]",                                                         # specific_services (JSON array)
            "simple",                                                     # service_complexity
            "medium",                                                     # estimated_duration
            False,                                                        # requires_emergency_response
            1.0,                                                          # classification_confidence
            "Direct form mapping"                                         # classification_reasoning
        ))
            
            conn.commit()
            logger.info(f"✅ Lead created with ID: {lead_id}")
            
        except Exception as e:
            logger.error(f"❌ Lead creation error: {e}")
            raise
        finally:
            if conn:
                conn.close()
        
        # Create opportunity for client leads (self-contained - no routing_admin dependency)
        opportunity_id = None
        form_type = form_config.get("form_type", "unknown")
        if form_type == "client_lead" or form_type == "emergency_service":
            if AppConfig.PIPELINE_ID and AppConfig.NEW_LEAD_STAGE_ID:
                logger.info(f"📈 Creating opportunity for {service_category} lead")
                
                # Initialize GHL API client for opportunity creation
                ghl_api_client = GoHighLevelAPI(
                    private_token=AppConfig.GHL_PRIVATE_TOKEN,
                    location_id=AppConfig.GHL_LOCATION_ID
                )
                
                customer_name = customer_data["name"]
                location_info = mapped_payload.get("zip_code_of_service", "Unknown Location")  # ✅ FIXED
                
                # Create opportunity data (FIXED for GHL V2 API)
                opportunity_data = {
                'contactId': ghl_contact_id,
                'pipelineId': AppConfig.PIPELINE_ID,
                'pipelineStageId': AppConfig.NEW_LEAD_STAGE_ID,
                'name': f"{customer_name} - {service_category}",
                'monetaryValue': 0,  # ✅ CHANGED: GHL V2 expects 'monetaryValue' not 'value'
                'status': 'open',
                'source': f"{form_identifier} (DSP)",
                'locationId': AppConfig.GHL_LOCATION_ID,
}
                
                # Create opportunity
                opportunity_response = ghl_api_client.create_opportunity(opportunity_data)
                
                if opportunity_response and opportunity_response.get('id'):
                    opportunity_id = opportunity_response['id']
                    logger.info(f"✅ Created opportunity in background task: {opportunity_id}")
                    
                    # Store opportunity ID in lead record
                    try:
                        simple_db_instance.update_lead_opportunity_id(lead_id, opportunity_id)
                        logger.info(f"✅ Stored opportunity ID {opportunity_id} with lead {lead_id}")
                    except Exception as e:
                        logger.warning(f"⚠️ Could not store opportunity ID: {e}")
                    
                    # Log successful opportunity creation
                    simple_db_instance.log_activity(
                        event_type="opportunity_created_background_task",
                        event_data={
                            "opportunity_id": opportunity_id,
                            "contact_id": ghl_contact_id,
                            "lead_id": lead_id,
                            "form_identifier": form_identifier,
                            "service_category": service_category,
                            "processing_method": "direct_only_no_ai"
                        },
                        lead_id=ghl_contact_id,
                        success=True
                    )
                else:
                    logger.error(f"❌ Failed to create opportunity in background task: {opportunity_response}")
            else:
                logger.warning("⚠️ Pipeline not configured - skipping opportunity creation")
        
        # Direct vendor matching for client leads (NO AI)
        form_type = form_config.get("form_type", "unknown")
        priority = form_config.get("priority", "normal")
        
        if form_type == "client_lead" or form_type == "emergency_service":
            zip_code = mapped_payload.get("zip_code_of_service", "")
            specific_service = mapped_payload.get("specific_service_needed", "")
            
            logger.info(f"🎯 Direct lead routing: Category='{service_category}', Specific Service='{specific_service}', ZIP='{zip_code}'")
            
            if zip_code and service_category:
                # Find matching vendors using lead_routing_service
                available_vendors = lead_routing_service.find_matching_vendors(
                    account_id=account_id,
                    service_category=service_category,
                    zip_code=zip_code,
                    priority=priority,
                    specific_service=specific_service
                )
                
                if available_vendors:
                    logger.info(f"🎯 Found {len(available_vendors)} matching vendors for lead {lead_id}")
                    
                    # Select vendor using existing logic
                    selected_vendor = lead_routing_service.select_vendor_from_pool(
                        available_vendors, account_id
                    )
                    
                    if selected_vendor:
                        # Update database with vendor assignment
                        db_assignment_success = simple_db_instance.assign_lead_to_vendor(lead_id, selected_vendor['id'])
                        
                        if db_assignment_success:
                            logger.info(f"✅ Successfully assigned lead {lead_id} to vendor {selected_vendor['name']} in database")
                            
                            # Assign opportunity to vendor using self-contained GHL API call
                            vendor_ghl_user_id = selected_vendor.get("ghl_user_id")
                            if vendor_ghl_user_id and opportunity_id:
                                logger.info(f"🎯 Assigning opportunity {opportunity_id} to vendor GHL User ID: {vendor_ghl_user_id}")
                                
                                # Self-contained opportunity assignment (no routing_admin dependency)
                                try:
                                    ghl_api_client = GoHighLevelAPI(
                                        private_token=AppConfig.GHL_PRIVATE_TOKEN,
                                        location_id=AppConfig.GHL_LOCATION_ID
                                    )
                                    
                                    # Update opportunity with vendor assignment
                                    update_data = {
                                        'assignedTo': vendor_ghl_user_id,
                                        'pipelineId': AppConfig.PIPELINE_ID,
                                        'pipelineStageId': AppConfig.NEW_LEAD_STAGE_ID
                                    }
                                    
                                    assignment_success = ghl_api_client.update_opportunity(opportunity_id, update_data)
                                    
                                    if assignment_success:
                                        logger.info(f"✅ Successfully assigned opportunity to vendor {selected_vendor['name']} - GHL workflows will handle notifications")
                                    else:
                                        logger.error(f"❌ Failed to assign opportunity to vendor {selected_vendor['name']}")
                                        
                                except Exception as e:
                                    logger.error(f"❌ Error assigning opportunity to vendor: {e}")
                                    
                            elif not vendor_ghl_user_id:
                                logger.warning(f"⚠️ Vendor {selected_vendor['name']} has no GHL User ID - cannot assign opportunity")
                            elif not opportunity_id:
                                logger.warning(f"⚠️ No opportunity ID available - cannot assign to vendor")
                        else:
                            logger.error(f"❌ Failed to assign lead in database")
                    else:
                        logger.warning(f"⚠️ Vendor selection failed")
                else:
                    logger.warning(f"⚠️ No matching vendors found for service '{service_category}' in area '{zip_code}'")
                    
                    # FIXED: Create proper data structure for notification
                    unmatched_lead_data = {
                        "customer_data": customer_data,
                        "service_details": service_details,
                        "zip_code": zip_code,
                        "timeline": service_details.get("timeline", "Not specified")
                    }
                    
                    # Notify admin of unmatched lead
                    await notify_admin_of_unmatched_lead(
                        lead_data=unmatched_lead_data,  # ✅ FIXED
                        ghl_contact_id=ghl_contact_id,
                        service_category=service_category,
                        location=zip_code
                    )
            else:
                logger.error(f"❌ Cannot route lead: missing ZIP code ('{zip_code}') or service category ('{service_category}')")
        
        # Log successful routing
        simple_db_instance.log_activity(
            event_type="clean_lead_routing_completed",
            event_data={
                "ghl_location_id": AppConfig.GHL_LOCATION_ID,
                "ghl_contact_id": ghl_contact_id,
                "lead_id": lead_id,
                "form_identifier": form_identifier,
                "form_type": form_type,
                "priority": priority,
                "service_category": service_category,
                "processing_method": "direct_only_no_ai",
                "timestamp": time.time()
            },
            lead_id=ghl_contact_id,
            success=True
        )
        
        logger.info(f"✅ Clean lead routing completed for {ghl_contact_id} with priority: {priority}")
        
    except Exception as e:
        logger.error(f"❌ Error in clean lead routing workflow for {ghl_contact_id}: {e}")
        simple_db_instance.log_activity(
            event_type="clean_lead_routing_error",
            event_data={
                "ghl_contact_id": ghl_contact_id,
                "form_identifier": form_identifier,
                "error": str(e)
            },
            lead_id=ghl_contact_id,
            success=False,
            error_message=str(e)
        )

async def notify_admin_of_unmatched_lead(lead_data: Dict[str, Any], ghl_contact_id: str, service_category: str, location: str):
    """
    Notify admin when no vendors are found for a lead
    Direct notification - NO AI processing
    """
    try:
        ghl_api_client = GoHighLevelAPI(private_token=AppConfig.GHL_PRIVATE_TOKEN, location_id=AppConfig.GHL_LOCATION_ID)
        
        # Use existing admin contact ID
        admin_contact_id = "b69NCeI1P32jooC7ySfw"  # Jeremy's contact ID
        
        customer_name = lead_data.get("customer_data", {}).get("name", "Customer")
        customer_email = lead_data.get("customer_data", {}).get("email", "No email")
        customer_phone = lead_data.get("customer_data", {}).get("phone", "No phone")
        
        admin_notification_message = f"""
🚨 UNMATCHED LEAD ALERT - {service_category}

No vendors found for this lead!

Customer: {customer_name}
Email: {customer_email}
Phone: {customer_phone}
Service: {service_category}
Location: {location}
Timeline: {lead_data.get('timeline', 'Not specified')}

Please manually assign this lead or add vendors for this service area.

Lead ID: {ghl_contact_id}

- Dockside Pros Lead Router (CLEAN/DIRECT)
        """.strip()
        
        # Send SMS notification to admin
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
                "success": sms_sent,
                "processing_method": "direct_only_no_ai"
            },
            lead_id=ghl_contact_id,
            success=sms_sent
        )
        
    except Exception as e:
        logger.error(f"Error notifying admin of unmatched lead {ghl_contact_id}: {e}")

# Legacy vendor user creation webhook (maintained for compatibility)
@router.post("/ghl/vendor-user-creation")
async def handle_vendor_user_creation_webhook(request: Request):
    """
    Legacy webhook endpoint for GHL workflow to trigger vendor user creation.
    Direct processing only - NO AI.
    """
    start_time = time.time()
    
    try:
        # Validate API key
        api_key = request.headers.get("X-Webhook-API-Key")
        expected_api_key = AppConfig.GHL_WEBHOOK_API_KEY
        
        if not api_key:
            logger.error(f"❌ GHL webhook request missing API key from IP: {request.client.host}")
            raise HTTPException(status_code=401, detail="Missing X-Webhook-API-Key header")
        
        if api_key != expected_api_key:
            logger.error(f"❌ GHL webhook API key mismatch from IP: {request.client.host}")
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        logger.info(f"✅ GHL webhook API key validated successfully")
        
        # Parse incoming GHL workflow webhook payload
        ghl_payload = await request.json()
        logger.info(f"📥 GHL Vendor User Creation Webhook received: {json.dumps(ghl_payload, indent=2)}")
        
        # Extract vendor information directly from webhook payload
        contact_id = ghl_payload.get("contact_id") or ghl_payload.get("contactId")
        vendor_email = ghl_payload.get("email", "")
        vendor_first_name = ghl_payload.get("first_name", "") or ghl_payload.get("firstName", "")
        vendor_last_name = ghl_payload.get("last_name", "") or ghl_payload.get("lastName", "")
        vendor_phone = ghl_payload.get("phone", "")
        vendor_company_name = ghl_payload.get("Vendor Company Name", "") or ghl_payload.get("vendor_company_name", "")
        
        logger.info(f"📋 Using vendor data directly from webhook payload:")
        logger.info(f"   👤 Contact ID: {contact_id}")
        logger.info(f"   📧 Email: {vendor_email}")
        logger.info(f"   👨 Name: {vendor_first_name} {vendor_last_name}")
        logger.info(f"   📱 Phone: {vendor_phone}")
        logger.info(f"   🏢 Company: {vendor_company_name}")
        
        # Initialize GHL API client
        ghl_api_client = GoHighLevelAPI(
            private_token=AppConfig.GHL_PRIVATE_TOKEN, 
            location_id=AppConfig.GHL_LOCATION_ID,
            agency_api_key=AppConfig.GHL_AGENCY_API_KEY,
            company_id=AppConfig.GHL_COMPANY_ID
        )
        
        if not vendor_email:
            logger.error(f"❌ No email found for contact {contact_id}")
            raise HTTPException(status_code=400, detail="Vendor email is required for user creation")
        
        # Check if user already exists
        existing_user = ghl_api_client.get_user_by_email(vendor_email)
        if existing_user:
            logger.info(f"✅ User already exists for {vendor_email}: {existing_user.get('id')}")
            
            # Get account and update vendor record
            account_record = simple_db_instance.get_account_by_ghl_location_id(AppConfig.GHL_LOCATION_ID)
            if account_record:
                vendor_record = simple_db_instance.get_vendor_by_email_and_account(vendor_email, account_record["id"])    
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
            "type": "account",
            "role": "user",
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
                "assignedDataOnly": True,
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
        
        if not created_user:
            logger.error(f"❌ No response from GHL user creation API for {vendor_email}")
            raise HTTPException(status_code=502, detail="No response from GHL user creation API")
        
        if isinstance(created_user, dict) and created_user.get("error"):
            error_details = {
                "api_version": created_user.get("api_version", "V1"),
                "status_code": created_user.get("status_code"),
                "response_text": created_user.get("response_text"),
                "exception": created_user.get("exception"),
                "url": created_user.get("url")
            }
            logger.error(f"❌ GHL V1 API user creation failed: {error_details}")
            error_msg = f"GHL V1 API error: {created_user.get('response_text', 'Unknown error')}"
            raise HTTPException(status_code=502, detail=error_msg)
        
        user_id = created_user.get("id")
        if not user_id:
            logger.error(f"❌ GHL user creation succeeded but no user ID returned: {created_user}")
            raise HTTPException(status_code=502, detail="User created but no ID returned from GHL")
        
        logger.info(f"✅ Successfully created GHL user: {user_id} for {vendor_email}")
        
        # Wait for GHL user propagation
        import asyncio
        logger.info(f"⏳ Waiting 10 seconds for GHL user propagation...")
        await asyncio.sleep(10)
        logger.info(f"✅ User propagation delay complete")
        
        # FIXED: Ensure vendor record exists when GHL User ID is assigned
        try:
            # Get account info
            account_record = simple_db_instance.get_account_by_ghl_location_id(AppConfig.GHL_LOCATION_ID)
            if not account_record:
                logger.error("❌ No account found for location")
                raise HTTPException(status_code=500, detail="Account configuration error")
            
            # Try to find existing vendor by email
            existing_vendor = simple_db_instance.get_vendor_by_email_and_account(vendor_email, account_record['id'])
            
            if existing_vendor:
                # Update existing vendor with GHL User ID
                simple_db_instance.update_vendor_ghl_user_id(existing_vendor['id'], user_id)
                logger.info(f"✅ Updated existing vendor {existing_vendor['id']} with GHL User ID: {user_id}")
            else:
                # Create vendor record if it doesn't exist (fallback scenario)
                logger.warning(f"⚠️ No vendor record found for {vendor_email}, creating one...")
                
                # Extract what data we can from the webhook
                vendor_name = f"{vendor_first_name} {vendor_last_name}".strip()
                
                # Create minimal vendor record
                vendor_id = simple_db_instance.create_vendor(
                    account_id=account_record['id'],
                    name=vendor_name,
                    email=vendor_email,
                    company_name=vendor_company_name or '',
                    phone=vendor_phone or '',
                    ghl_contact_id=contact_id,
                    status='active',  # They're getting user access, so mark as active
                    service_categories=json.dumps(['General Services']),  # Default
                    services_offered=json.dumps([]),  # Will be updated later
                    coverage_type='county',  # Default coverage type
                    coverage_states=json.dumps([]),  # Will be updated later
                    coverage_counties=json.dumps([])  # Will be updated later
                )
                
                # Update the new vendor record with GHL User ID
                simple_db_instance.update_vendor_ghl_user_id(vendor_id, user_id)
                
                logger.info(f"✅ Created fallback vendor record: {vendor_id}")
                logger.info(f"   Name: {vendor_name}")
                logger.info(f"   Company: {vendor_company_name}")
                logger.info(f"   GHL User ID: {user_id}")
        
        except Exception as e:
            logger.error(f"❌ Failed to link vendor with GHL User ID: {str(e)}")
            # Don't fail the webhook - the user was created successfully

        # Get account ID for remaining operations
        account_record = simple_db_instance.get_account_by_ghl_location_id(AppConfig.GHL_LOCATION_ID)
        if not account_record:
            account_id = simple_db_instance.create_account(
                ghl_location_id=AppConfig.GHL_LOCATION_ID,
                company_name="DocksidePros",
                industry="Marine Services"
            )
        else:
            account_id = account_record["id"]
        
        # Update the contact record with the GHL User ID
        if contact_id:
            logger.info(f"🔄 Updating contact {contact_id} with GHL User ID: {user_id}")
            
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
                
                update_success = ghl_api_client.update_contact(contact_id, update_payload)
                if update_success:
                    logger.info(f"✅ Successfully updated contact {contact_id} with GHL User ID: {user_id}")
                else:
                    logger.warning(f"⚠️ Failed to update contact {contact_id} with GHL User ID")
            else:
                logger.warning(f"⚠️ Could not find GHL User ID field mapping for contact update")
        
        # Update vendor record in database
        vendor_record = simple_db_instance.get_vendor_by_email_and_account(vendor_email, account_id)
        if vendor_record:
            simple_db_instance.update_vendor_status(vendor_record["id"], "active", user_id)
            logger.info(f"✅ Updated vendor record with user ID: {user_id}")
        else:
            logger.warning(f"⚠️ No vendor record found for {vendor_email} - user created but not linked")
        
        # Log successful activity
        processing_time = round(time.time() - start_time, 3)
        simple_db_instance.log_activity(
            event_type="vendor_user_created_clean",
            event_data={
                "contact_id": contact_id,
                "user_id": user_id,
                "vendor_email": vendor_email,
                "vendor_company": vendor_company_name,
                "processing_time_seconds": processing_time,
                "processing_method": "direct_only_no_ai"
            },
            lead_id=contact_id,
            success=True
        )
        
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
            "processing_method": "direct_only_no_ai"
        }
        
    except HTTPException:
        raise
    
    except Exception as e:
        processing_time = round(time.time() - start_time, 3)
        logger.exception(f"💥 Critical error processing vendor user creation webhook after {processing_time}s: {e}")
        simple_db_instance.log_activity(
            event_type="vendor_user_creation_error_clean",
            event_data={
                "processing_time_seconds": processing_time,
                "error_class": e.__class__.__name__,
                "processing_method": "direct_only_no_ai"
            },
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Health check endpoint
@router.get("/health")
async def clean_webhook_health_check():
    """Clean health check for webhook system - NO AI dependencies"""
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
        "webhook_system": "clean_direct_processing_no_ai",
        "ghl_location_id": AppConfig.GHL_LOCATION_ID,
        "pipeline_configured": AppConfig.PIPELINE_ID is not None and AppConfig.NEW_LEAD_STAGE_ID is not None,
        "valid_field_count": len(field_mapper.get_all_ghl_field_keys()),
        "custom_field_mappings": field_mapper_stats.get("ghl_fields_loaded", 0),
        "service_categories": len(DOCKSIDE_PROS_SERVICES),
        "database_status": "healthy" if db_healthy else "error",
        "database_stats": db_stats,
        "field_reference_status": "loaded" if field_reference_healthy else "missing",
        "field_mapper_stats": field_mapper_stats,
        "supported_form_types": ["client_lead", "vendor_application", "emergency_service", "general_inquiry"],
        "routing_method": "direct_vendor_matching_no_ai",
        "ai_processing": "completely_disabled",
        "opportunity_creation": "enabled" if AppConfig.PIPELINE_ID else "disabled",
        "message": "Clean webhook system ready for direct processing - NO AI interference"
    }

# Get service categories endpoint
@router.get("/service-categories")
async def get_clean_service_categories():
    """Return all supported service categories - Direct mapping only"""
    
    # Group categories by type
    categories_by_type = {}
    for form_key, category in DOCKSIDE_PROS_SERVICES.items():
        if category not in categories_by_type:
            categories_by_type[category] = []
        categories_by_type[category].append(form_key)
    
    return {
        "status": "success",
        "service_categories": categories_by_type,
        "total_categories": len(set(DOCKSIDE_PROS_SERVICES.values())),
        "total_form_identifiers": len(DOCKSIDE_PROS_SERVICES),
        "processing_method": "direct_mapping_no_ai",
        "ai_processing": "disabled",
        "message": f"All {len(set(DOCKSIDE_PROS_SERVICES.values()))} marine service categories supported with direct form handling - NO AI"
    }

# Get field mappings endpoint
@router.get("/field-mappings")
async def get_clean_field_mappings():
    """Return all available field mappings for form development - Direct only"""
    
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
        "processing_method": "direct_field_mapping_no_ai",
        "ai_processing": "disabled",
        "message": "Complete field mappings for GHL integration - Direct processing only"
    }

# Dynamic form testing endpoint
@router.post("/test/{form_identifier}")
async def test_clean_form_configuration(form_identifier: str):
    """Test endpoint to see how any form identifier would be configured - Direct only"""
    
    try:
        form_config = get_form_configuration(form_identifier)
        
        return {
            "status": "success",
            "form_identifier": form_identifier,
            "generated_configuration": form_config,
            "webhook_url": f"https://dockside.life/api/v1/webhooks/elementor/{form_identifier}",
            "processing_method": "direct_configuration_no_ai",
            "ai_processing": "disabled",
            "message": f"Direct configuration generated for form '{form_identifier}' - NO AI processing"
        }
    except Exception as e:
        return {
            "status": "error",
            "form_identifier": form_identifier,
            "error": str(e),
            "message": "Failed to generate configuration"
        }

@router.post("/ghl/reassign-lead")
async def handle_lead_reassignment_webhook(request: Request):
    """
    GHL workflow webhook endpoint for lead reassignment.
    Triggered when tags like "reassign lead" are added to contacts.
    Overwrites existing assignments and finds new vendors.
    FIXED: Creates opportunities when none exist, uses correct database schema.
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
        logger.info(f"📥 GHL Lead Reassignment Webhook received: {json.dumps(ghl_payload, indent=2)}")
        
        # Extract contact information from payload
        contact_id = ghl_payload.get("contact_id") or ghl_payload.get("contactId")
        opportunity_id = ghl_payload.get("opportunity_id") or ghl_payload.get("opportunityId")
        
        if not contact_id:
            logger.error(f"❌ No contact ID provided in reassignment webhook")
            raise HTTPException(status_code=400, detail="Contact ID is required for lead reassignment")
        
        logger.info(f"🔄 Processing lead reassignment for contact: {contact_id}")
        if opportunity_id:
            logger.info(f"📋 Existing opportunity ID: {opportunity_id}")
        else:
            logger.info(f"📋 No opportunity ID provided - will create if needed")
        
        # Initialize GHL API client
        ghl_api_client = GoHighLevelAPI(
            private_token=AppConfig.GHL_PRIVATE_TOKEN,
            location_id=AppConfig.GHL_LOCATION_ID,
            agency_api_key=AppConfig.GHL_AGENCY_API_KEY,
            company_id=AppConfig.GHL_COMPANY_ID
        )
        
        # Get contact details from GHL
        contact_details = ghl_api_client.get_contact_by_id(contact_id)
        if not contact_details:
            logger.error(f"❌ Could not fetch contact details for {contact_id}")
            raise HTTPException(status_code=404, detail="Contact not found in GHL")
        
        # Extract service and location information for reassignment using field mapping
        service_category = await _extract_service_category_from_contact(contact_details)
        zip_code = await _extract_zip_code_from_contact(contact_details)
        
        if not service_category:
            logger.error(f"❌ Could not determine service category for contact {contact_id}")
            raise HTTPException(status_code=400, detail="Cannot determine service category for reassignment")
        
        if not zip_code:
            logger.error(f"❌ Could not determine service location for contact {contact_id}")
            raise HTTPException(status_code=400, detail="Cannot determine service location for reassignment")
        
        logger.info(f"🎯 Reassignment criteria: Service='{service_category}', Location='{zip_code}'")
        
        # Get account information
        account = simple_db_instance.get_account_by_ghl_location_id(AppConfig.GHL_LOCATION_ID)
        if not account:
            logger.error(f"❌ No account found for GHL Location ID: {AppConfig.GHL_LOCATION_ID}")
            raise HTTPException(status_code=500, detail="Account configuration error")
        
        account_id = account["id"]
        
        # Find existing lead assignment in database
        existing_lead = simple_db_instance.get_lead_by_ghl_contact_id(contact_id)
        if existing_lead:
            logger.info(f"📋 Found existing lead record: {existing_lead['id']}")
            
            # OVERWRITE: Remove current vendor assignment
            if existing_lead.get('vendor_id'):
                logger.info(f"🔄 Removing existing vendor assignment: {existing_lead['vendor_id']}")
                simple_db_instance.unassign_lead_from_vendor(existing_lead['id'])
        else:
            # FIXED: Create new lead record using correct database schema
            customer_name = f"{contact_details.get('firstName', '')} {contact_details.get('lastName', '')}".strip()
            customer_email = contact_details.get('email', '')
            customer_phone = contact_details.get('phone', '')
            
            # Apply field mapping to contact data
            mapped_contact_data = field_mapper.map_payload(contact_details, industry="marine")
            
            # Create service_details from mapped contact data
            service_details = {
                'location': {'zip_code': zip_code},
                'source': 'GHL Reassignment Workflow',
                'ghl_contact_id': contact_id,
                'ghl_opportunity_id': opportunity_id,
                'processing_method': 'reassignment_webhook',
                'reassignment_reason': 'Manual reassignment triggered'
            }
            
            # Add any additional mapped fields to service_details
            standard_fields = {"firstName", "lastName", "email", "phone", "primary_service_category"}
            for field_key, field_value in mapped_contact_data.items():
                if field_key not in standard_fields and field_value:
                    service_details[field_key] = field_value
            
            # FIXED: Convert ZIP to county for reassignment lead routing
            reassignment_service_county = ""
            reassignment_service_state = ""
            
            if zip_code and len(zip_code) == 5 and zip_code.isdigit():
                logger.info(f"🗺️ Converting ZIP {zip_code} to county for reassignment lead")
                location_data = location_service.zip_to_location(zip_code)
                
                if not location_data.get('error'):
                    county = location_data.get('county', '')
                    state = location_data.get('state', '')
                    if county and state:
                        reassignment_service_county = f"{county}, {state}"  # Format: "Miami-Dade, FL"
                        reassignment_service_state = state
                        logger.info(f"✅ Reassignment ZIP {zip_code} → {reassignment_service_county}")
                    else:
                        logger.warning(f"⚠️ Reassignment ZIP {zip_code} conversion incomplete: county={county}, state={state}")
                else:
                    logger.warning(f"⚠️ Could not convert reassignment ZIP {zip_code}: {location_data['error']}")
            else:
                logger.warning(f"⚠️ Invalid reassignment ZIP code format: '{zip_code}' - service_county will remain NULL")

            # FIXED: Direct database INSERT using correct schema
            conn = None
            try:
                lead_id_str = str(uuid.uuid4())
                conn = simple_db_instance._get_conn()
                cursor = conn.cursor()
                
                # INSERT using CORRECT Leads table schema field names
                cursor.execute('''
                    INSERT INTO leads (
                        id, account_id, ghl_contact_id, ghl_opportunity_id, customer_name,
                        customer_email, customer_phone, primary_service_category, specific_service_requested,
                        customer_zip_code, service_county, service_state, vendor_id, 
                        assigned_at, status, priority, source, service_details, 
                        created_at, updated_at, service_zip_code, service_city, 
                        service_complexity, estimated_duration, requires_emergency_response, 
                        classification_confidence, classification_reasoning
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    lead_id_str,                              # id
                    account_id,                               # account_id
                    contact_id,                               # ghl_contact_id
                    opportunity_id,                           # ghl_opportunity_id
                    customer_name,                            # customer_name
                    customer_email,                           # customer_email
                    customer_phone,                           # customer_phone ✅
                    service_category,                         # primary_service_category ✅
                    "",                                       # specific_service_requested
                    zip_code,                                 # customer_zip_code
                    reassignment_service_county,              # service_county ✅ FIXED! (now properly populated)
                    reassignment_service_state,               # service_state ✅ FIXED! (now properly populated)
                    None,                                     # vendor_id (unassigned)
                    None,                                     # assigned_at
                    "unassigned",                             # status
                    "high",                                   # priority (reassignments are high priority)
                    "ghl_reassignment_webhook",               # source
                    json.dumps(service_details),              # service_details
                    zip_code,                                 # service_zip_code
                    "",                                       # service_city
                    "simple",                                 # service_complexity
                    "medium",                                 # estimated_duration
                    False,                                    # requires_emergency_response
                    1.0,                                      # classification_confidence ✅
                    f"Lead created via reassignment webhook" # classification_reasoning
                ))
                
                conn.commit()
                existing_lead = {'id': lead_id_str, 'vendor_id': None}
                logger.info(f"➕ Created new lead record for reassignment: {lead_id_str}")
                
            except Exception as e:
                logger.error(f"❌ Lead creation error: {e}")
                raise
            finally:
                if conn:
                    conn.close()
        
        # Find matching vendors using enhanced routing
        available_vendors = lead_routing_service.find_matching_vendors(
            account_id=account_id,
            service_category=service_category,
            zip_code=zip_code,
            priority='high'  # High priority for reassignments
        )
        
        if not available_vendors:
            logger.warning(f"⚠️ No matching vendors found for reassignment")
            
            # Log failed reassignment
            simple_db_instance.log_activity(
                event_type="lead_reassignment_failed",
                event_data={
                    "contact_id": contact_id,
                    "service_category": service_category,
                    "zip_code": zip_code,
                    "reason": "No matching vendors",
                    "processing_method": "reassignment_webhook_fixed"
                },
                lead_id=contact_id,
                success=False,
                error_message="No matching vendors found for reassignment"
            )
            
            return {
                "status": "failed",
                "message": "No matching vendors found for reassignment",
                "contact_id": contact_id,
                "service_category": service_category,
                "location": zip_code
            }
        
        # EXCLUDE previously assigned vendor to avoid reassigning to same vendor
        previous_vendor_id = existing_lead.get('vendor_id')
        if previous_vendor_id:
            available_vendors = [v for v in available_vendors if v['id'] != previous_vendor_id]
            logger.info(f"🚫 Excluded previous vendor {previous_vendor_id} from reassignment pool")
        
        if not available_vendors:
            logger.warning(f"⚠️ No alternative vendors available (only previous vendor matched)")
            
            simple_db_instance.log_activity(
                event_type="lead_reassignment_failed",
                event_data={
                    "contact_id": contact_id,
                    "service_category": service_category,
                    "zip_code": zip_code,
                    "reason": "Only previous vendor available - no alternatives",
                    "previous_vendor_id": previous_vendor_id,
                    "processing_method": "reassignment_webhook_fixed"
                },
                lead_id=contact_id,
                success=False
            )
            
            return {
                "status": "failed",
                "message": "No alternative vendors available for reassignment",
                "contact_id": contact_id,
                "previous_vendor_excluded": previous_vendor_id
            }
        
        # Select new vendor using routing logic
        selected_vendor = lead_routing_service.select_vendor_from_pool(available_vendors, account_id)
        
        if not selected_vendor:
            logger.error(f"❌ Vendor selection failed during reassignment")
            raise HTTPException(status_code=500, detail="Vendor selection logic failed")
        
        # Assign lead to new vendor in database
        assignment_success = simple_db_instance.assign_lead_to_vendor(existing_lead['id'], selected_vendor['id'])
        
        if not assignment_success:
            logger.error(f"❌ Failed to assign lead to new vendor in database")
            raise HTTPException(status_code=500, detail="Database assignment failed")
        
        logger.info(f"✅ Successfully reassigned lead {existing_lead['id']} to vendor {selected_vendor['name']}")
        
        # FIXED: Handle opportunity creation/assignment
        if selected_vendor.get('ghl_user_id'):
            if opportunity_id:
                # Update existing opportunity assignment
                logger.info(f"🎯 Updating existing opportunity {opportunity_id} assignment to vendor {selected_vendor['ghl_user_id']}")
                
                try:
                    update_data = {
                        'assignedTo': selected_vendor['ghl_user_id'],
                        'pipelineId': AppConfig.PIPELINE_ID,
                        'pipelineStageId': AppConfig.NEW_LEAD_STAGE_ID
                    }
                    
                    ghl_assignment_success = ghl_api_client.update_opportunity(opportunity_id, update_data)
                    
                    if ghl_assignment_success:
                        logger.info(f"✅ Successfully updated existing opportunity assignment")
                    else:
                        logger.warning(f"⚠️ Failed to update existing opportunity assignment")
                        
                except Exception as e:
                    logger.error(f"❌ Error updating existing opportunity assignment: {e}")
            else:
                # FIXED: Create new opportunity when none exists
                logger.info(f"📈 No opportunity exists - creating one for reassigned lead")
                
                try:
                    # Create opportunity data with correct field names
                    opportunity_data = {
                        'contactId': contact_id,
                        'pipelineId': AppConfig.PIPELINE_ID,
                        'pipelineStageId': AppConfig.NEW_LEAD_STAGE_ID,
                        'name': f"{customer_name} - {service_category}",
                        'monetaryValue': 0,  # ✅ FIXED: Use 'monetaryValue' not 'value'
                        'status': 'open',
                        'source': f"Lead Reassignment (DSP)",
                        'locationId': AppConfig.GHL_LOCATION_ID,
                        'assignedTo': selected_vendor['ghl_user_id']  # Assign directly to vendor
                    }
                    
                    # Create opportunity
                    opportunity_response = ghl_api_client.create_opportunity(opportunity_data)
                    
                    if opportunity_response and opportunity_response.get('id'):
                        opportunity_id = opportunity_response['id']
                        logger.info(f"✅ Created new opportunity for reassigned lead: {opportunity_id}")
                        
                        # Update lead record with opportunity ID
                        simple_db_instance.update_lead_opportunity_id(existing_lead['id'], opportunity_id)
                        
                        # Log successful opportunity creation
                        simple_db_instance.log_activity(
                            event_type="opportunity_created_reassignment",
                            event_data={
                                "opportunity_id": opportunity_id,
                                "contact_id": contact_id,
                                "lead_id": existing_lead['id'],
                                "vendor_id": selected_vendor['id'],
                                "service_category": service_category,
                                "processing_method": "reassignment_webhook_fixed"
                            },
                            lead_id=contact_id,
                            success=True
                        )
                    else:
                        logger.error(f"❌ Failed to create opportunity for reassigned lead: {opportunity_response}")
                        
                except Exception as e:
                    logger.error(f"❌ Error creating opportunity for reassigned lead: {e}")
        else:
            logger.warning(f"⚠️ Vendor {selected_vendor['name']} has no GHL User ID - cannot assign opportunity")
        
        # Remove reassignment tag from contact
        await _remove_reassignment_tag(ghl_api_client, contact_id)
        
        # Log successful reassignment
        processing_time = round(time.time() - start_time, 3)
        simple_db_instance.log_activity(
            event_type="lead_reassignment_successful",
            event_data={
                "contact_id": contact_id,
                "opportunity_id": opportunity_id,
                "opportunity_created": opportunity_id is not None and not ghl_payload.get("opportunity_id"),
                "previous_vendor_id": previous_vendor_id,
                "new_vendor_id": selected_vendor['id'],
                "new_vendor_name": selected_vendor['name'],
                "service_category": service_category,
                "zip_code": zip_code,
                "processing_time_seconds": processing_time,
                "processing_method": "reassignment_webhook_fixed"
            },
            lead_id=contact_id,
            success=True
        )
        
        return {
            "status": "success",
            "message": f"Lead successfully reassigned to {selected_vendor['name']}",
            "contact_id": contact_id,
            "opportunity_id": opportunity_id,
            "opportunity_created": opportunity_id is not None and not ghl_payload.get("opportunity_id"),
            "previous_vendor_id": previous_vendor_id,
            "new_vendor": {
                "id": selected_vendor['id'],
                "name": selected_vendor['name'],
                "email": selected_vendor.get('email')
            },
            "service_category": service_category,
            "location": zip_code,
            "processing_time_seconds": processing_time,
            "ghl_opportunity_updated": True
        }
        
    except HTTPException:
        raise
    
    except Exception as e:
        processing_time = round(time.time() - start_time, 3)
        logger.exception(f"💥 Critical error processing lead reassignment webhook after {processing_time}s: {e}")
        simple_db_instance.log_activity(
            event_type="lead_reassignment_error",
            event_data={
                "processing_time_seconds": processing_time,
                "error_class": e.__class__.__name__,
                "processing_method": "reassignment_webhook_fixed"
            },
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Helper functions for reassignment endpoint

async def _extract_service_category_from_contact(contact_details: Dict[str, Any]) -> Optional[str]:
    """Extract service category from GHL contact using direct mapping"""
    # Check tags first
    tags = contact_details.get('tags', [])
    for tag in tags:
        tag_lower = tag.lower()
        for keyword, category in DOCKSIDE_PROS_SERVICES.items():
            if keyword in tag_lower:
                logger.info(f"🎯 Found service category from tag '{tag}': {category}")
                return category
    
    # Check custom fields
    custom_fields = contact_details.get('customFields', [])
    for field in custom_fields:
        if field.get('name', '').lower() in ['service category', 'service_category']:
            category = field.get('value', '')
            if category in DOCKSIDE_PROS_CATEGORIES:
                logger.info(f"🎯 Found service category from custom field: {category}")
                return category
    
    # FIXED: Default fallback
    return "No Category"  # ✅ Changed from "Boater Resources"

async def _extract_zip_code_from_contact(contact_details: Dict[str, Any]) -> Optional[str]:
    """Extract ZIP code from GHL contact using the same logic as routing_admin"""
    # Check custom fields first
    custom_fields = contact_details.get('customFields', [])
    for field in custom_fields:
        field_id = field.get('id', '')
        field_value = field.get('value', '')
        
        # Check for known ZIP code field ID (from your routing_admin logic)
        if field_id == 'y3Xo7qsFEQumoFugTeCq':  # Known ZIP code field ID
            if field_value and str(field_value).strip().isdigit() and len(str(field_value).strip()) == 5:
                zip_code = str(field_value).strip()
                logger.info(f"📍 Found ZIP from custom field ID '{field_id}': {zip_code}")
                return zip_code
    
    # Check standard fields
    postal_code = contact_details.get('postalCode') or contact_details.get('postal_code')
    if postal_code and str(postal_code).strip().isdigit() and len(str(postal_code).strip()) == 5:
        zip_code = str(postal_code).strip()
        logger.info(f"📍 Found ZIP from postal code field: {zip_code}")
        return zip_code
    
    return None

async def _remove_reassignment_tag(ghl_api_client: GoHighLevelAPI, contact_id: str):
    """Remove reassignment trigger tags from contact"""
    try:
        # Get current contact to see existing tags
        contact = ghl_api_client.get_contact_by_id(contact_id)
        if not contact:
            return
        
        current_tags = contact.get('tags', [])
        
        # Remove reassignment-related tags
        reassignment_tags = ['reassign lead', 'reassign_lead', 'Reassign Lead', 'REASSIGN', 'reassign']
        updated_tags = [tag for tag in current_tags if tag not in reassignment_tags]
        
        if len(updated_tags) != len(current_tags):
            # Tags were removed, update contact
            update_success = ghl_api_client.update_contact(contact_id, {"tags": updated_tags})
            if update_success:
                logger.info(f"✅ Removed reassignment tags from contact {contact_id}")
            else:
                logger.warning(f"⚠️ Failed to remove reassignment tags from contact {contact_id}")
        
    except Exception as e:
        logger.error(f"Error removing reassignment tag from contact {contact_id}: {e}")
