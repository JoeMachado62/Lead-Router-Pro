"""
Service Mapper Module
Centralizes all service category and service name mappings for the Lead Router Pro system.
Extracted from webhook_routes.py for better modularity and maintainability.
"""

import logging
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

# ============================================================================
# CORE SERVICE CATEGORIES - The 16 main categories from Dockside Pros
# ============================================================================

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

# ============================================================================
# SERVICE MAPPINGS - Maps form identifiers to service categories
# ============================================================================

DOCKSIDE_PROS_SERVICES = {
    # CATEGORY-LEVEL FORM IDENTIFIERS
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
    
    # Boat and Yacht Repair (9 services)
    "boat_yacht_repair": "Boat and Yacht Repair",
    "fiberglass_repair": "Boat and Yacht Repair",
    "welding_metal_fabrication": "Boat and Yacht Repair",
    "welding_fabrication": "Boat and Yacht Repair",
    "carpentry_woodwork": "Boat and Yacht Repair",
    "riggers_masts": "Boat and Yacht Repair",
    "jet_ski_repair": "Boat and Yacht Repair",
    "boat_canvas_upholstery": "Boat and Yacht Repair",
    "boat_decking_yacht_flooring": "Boat and Yacht Repair",
    
    # Boat Charters and Rentals (8 services)
    "boat_charters_rentals": "Boat Charters and Rentals",
    "boat_clubs": "Boat Charters and Rentals",
    "fishing_charters": "Boat Charters and Rentals",
    "yacht_charters": "Boat Charters and Rentals",
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
    "yacht_fire_detection": "Boat Maintenance",
    "yacht_armor": "Boat Maintenance",
    
    # Boat Towing
    "boat_towing_service": "Boat Towing",
    "emergency_towing": "Boat Towing",
    "salvage_services": "Boat Towing",
    
    # Boater Resources
    "email_newsletter": "Boater Resources",
    "maritime_advertising": "Boater Resources",
    "yacht_accounting": "Boater Resources",
    "yacht_crew_management": "Boater Resources",
    
    # Buying or Selling a Boat
    "boat_dealers": "Buying or Selling a Boat",
    "yacht_dealers": "Buying or Selling a Boat",
    "boat_surveyors": "Buying or Selling a Boat",
    "boat_financing": "Buying or Selling a Boat",
    "boat_insurance": "Buying or Selling a Boat",
    "yacht_insurance": "Buying or Selling a Boat",
    "boat_builder": "Buying or Selling a Boat",
    "boat_broker": "Buying or Selling a Boat",
    "yacht_broker": "Buying or Selling a Boat",
    
    # Additional mappings for variations
    "bilge_cleaning": "Boat Maintenance",
    "bottom_cleaning": "Boat Maintenance",
    "oil_change": "Boat Maintenance",
    "emergency_tow": "Boat Towing",
    "towing_membership": "Boat Towing",
    "canvas_upholstery": "Boat and Yacht Repair",
    "decking_flooring": "Boat and Yacht Repair",
    "email_subscribe": "Boater Resources",
    "yacht_accounting": "Boater Resources",
    "yacht_crew": "Boater Resources",
    "yacht_parts": "Boater Resources",
    "buying_selling_boats": "Buying or Selling a Boat",
    "davit_hydraulic": "Docks, Seawalls and Lifts",
    "dock_seawall_builders": "Docks, Seawalls and Lifts",
    "hull_dock_cleaning": "Docks, Seawalls and Lifts",
    "engine_sales": "Engines and Generators",
    "engine_service": "Engines and Generators",
    "ac_sales": "Marine Systems",
    "ac_service": "Marine Systems",
    "electrical_service": "Marine Systems",
    "plumbing": "Marine Systems",
    "maritime_education": "Maritime Education and Training",
    "waterfront_developments": "Waterfront Property"
}

# ============================================================================
# SPECIFIC SERVICE MAPPINGS - Maps form identifiers to specific service names
# ============================================================================

FORM_TO_SPECIFIC_SERVICE = {
    # Boat Maintenance Services
    "barnacle_cleaning": "Barnacle Cleaning",
    "barnacle-cleaning": "Barnacle Cleaning",
    "boat_yacht_maintenance": "Boat and Yacht Maintenance",
    "boat-yacht-maintenance": "Boat and Yacht Maintenance",
    "bilge_cleaning": "Bilge Cleaning",
    "bilge-cleaning": "Bilge Cleaning",
    "boat_bilge_cleaning": "Boat Bilge Cleaning",
    "bottom_cleaning": "Bottom Cleaning",
    "bottom-cleaning": "Bottom Cleaning",
    "boat_bottom_cleaning": "Bottom Cleaning",
    "boat_detailing": "Boat Detailing",
    "boat-detailing": "Boat Detailing",
    "boat_oil_change": "Boat Oil Change",
    "boat-oil-change": "Boat Oil Change",
    "boat_wrapping_marine_protection": "Boat Wrapping and Marine Protection Film",
    "boat_wrapping_marine_protection_film": "Boat Wrapping and Marine Protection Film",
    "boat-wrapping-marine-protection-film": "Boat Wrapping and Marine Protection Film",
    "ceramic_coating": "Ceramic Coating",
    "ceramic-coating": "Ceramic Coating",
    "jet_ski_maintenance": "Jet Ski Maintenance",
    "jet-ski-maintenance": "Jet Ski Maintenance",
    "yacht_fire_detection": "Yacht Fire Detection Systems",
    "yacht_fire_detection_systems": "Yacht Fire Detection Systems",
    "yacht-fire-detection-systems": "Yacht Fire Detection Systems",
    "yacht_armor": "Yacht Armor",
    "yacht-armor": "Yacht Armor",
    
    # Boat Hauling and Yacht Delivery
    "yacht_delivery": "Yacht Delivery",
    "yacht-delivery": "Yacht Delivery",
    "boat_hauling": "Boat Hauling",
    "boat-hauling": "Boat Hauling",
    "boat_hauling_transport": "Boat Hauling",
    "boat-hauling-transport": "Boat Hauling",
    "boat_transport_by_road": "Boat Transport By Road",
    
    # Boat and Yacht Repair Services
    "boat_yacht_repair": "Boat and Yacht Repair",
    "boat-yacht-repair": "Boat and Yacht Repair",
    "fiberglass_repair": "Fiberglass Repair",
    "fiberglass-repair": "Fiberglass Repair",
    "welding_metal_fabrication": "Welding & Metal Fabrication",
    "welding-metal-fabrication": "Welding & Metal Fabrication",
    "carpentry_woodwork": "Carpentry & Woodwork",
    "boat_carpentry_woodwork": "Carpentry & Woodwork",
    "boat-carpentry-woodwork": "Carpentry & Woodwork",
    "riggers_masts": "Riggers & Masts",
    "riggers-masts": "Riggers & Masts",
    "jet_ski_repair": "Jet Ski Repair",
    "jet-ski-repair": "Jet Ski Repair",
    "canvas_upholstery": "Canvas & Upholstery",
    "boat_canvas_upholstery": "Canvas & Upholstery",
    "boat-canvas-upholstery": "Canvas & Upholstery",
    "decking_flooring": "Decking & Flooring",
    "boat_decking_yacht_flooring": "Decking & Flooring",
    "boat-decking-yacht-flooring": "Decking & Flooring",
    "yacht_restoration": "Yacht Restoration",
    
    # Engines and Generators Services
    "engine_generators_sales_service": "Engines and Generators",
    "engine-generators-sales-service": "Engines and Generators",
    "generator_sales_service": "Generator Service",
    "generator-sales-service": "Generator Service",
    "generator_sales": "Generator Sales",
    "generator-sales": "Generator Sales",
    "generator_service": "Generator Service",
    "generator-service": "Generator Service",
    "engine_service_sales": "Engine Service",
    "engine-service-sales": "Engine Service",
    "engine_service": "Engine Service",
    "engine-service": "Engine Service",
    "engine_sales": "Engine Sales",
    "engine-sales": "Engine Sales",
    "diesel_engine_sales": "Diesel Engine Sales",
    "diesel-engine-sales": "Diesel Engine Sales",
    "diesel_engine_service": "Diesel Engine Service",
    "outboard_engine_sales": "Outboard Engine Sales",
    "outboard-engine-sales": "Outboard Engine Sales",
    "outboard_engine_service": "Outboard Engine Service",
    "inboard_engine_sales": "Inboard Engine Sales",
    "inboard-engine-sales": "Inboard Engine Sales",
    "inboard_engine_service": "Inboard Engine Service",
    "marine_exhaust_systems_service": "Marine Exhaust Systems Service",
    "marine-exhaust-systems-service": "Marine Exhaust Systems Service",
    
    # Marine Systems Services
    "marine_systems_install_sales": "Marine Systems Install and Sales",
    "marine-systems-install-sales": "Marine Systems Install and Sales",
    "marine_ac_systems": "Marine AC Systems",
    "marine-ac-systems": "Marine AC Systems",
    "marine_electrical_systems": "Marine Electrical Systems",
    "marine-electrical-systems": "Marine Electrical Systems",
    "marine_plumbing_systems": "Marine Plumbing Systems",
    "marine-plumbing-systems": "Marine Plumbing Systems",
    "marine_refrigeration_systems": "Marine Refrigeration Systems",
    "marine-refrigeration-systems": "Marine Refrigeration Systems",
}

# ============================================================================
# SERVICE MAPPING FUNCTIONS
# ============================================================================

def get_service_category(form_identifier: str) -> str:
    """
    Direct service category mapping - NO AI processing
    Uses dictionary lookup with keyword matching based on actual CSV data
    
    Args:
        form_identifier: The form identifier from the webhook
        
    Returns:
        The mapped service category
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


def get_specific_service(form_identifier: str) -> str:
    """
    Maps form identifier to specific service name
    
    Args:
        form_identifier: The form identifier from the webhook
        
    Returns:
        The specific service name or empty string if not found
    """
    # Normalize the form identifier
    form_lower = form_identifier.lower()
    
    # Check direct mapping
    if form_lower in FORM_TO_SPECIFIC_SERVICE:
        return FORM_TO_SPECIFIC_SERVICE[form_lower]
    
    # Check with hyphens replaced by underscores
    form_normalized = form_lower.replace("-", "_")
    if form_normalized in FORM_TO_SPECIFIC_SERVICE:
        return FORM_TO_SPECIFIC_SERVICE[form_normalized]
    
    # Check with underscores replaced by hyphens
    form_hyphenated = form_lower.replace("_", "-")
    if form_hyphenated in FORM_TO_SPECIFIC_SERVICE:
        return FORM_TO_SPECIFIC_SERVICE[form_hyphenated]
    
    logger.debug(f"No specific service found for form identifier: {form_identifier}")
    return ""


def find_matching_service(specific_service_text: str) -> str:
    """
    Finds the best matching service name from the predefined list
    
    Args:
        specific_service_text: The text to match against service names
        
    Returns:
        The matching service name or the original text if no match
    """
    if not specific_service_text:
        return ""
    
    # Normalize input
    text_lower = specific_service_text.lower().strip()
    
    # First try exact match
    for form_id, service_name in FORM_TO_SPECIFIC_SERVICE.items():
        if service_name.lower() == text_lower:
            return service_name
    
    # Try partial match
    for form_id, service_name in FORM_TO_SPECIFIC_SERVICE.items():
        if text_lower in service_name.lower() or service_name.lower() in text_lower:
            logger.info(f"📌 Matched '{specific_service_text}' to '{service_name}'")
            return service_name
    
    # Try key-based match
    text_key = text_lower.replace(" ", "_").replace("-", "_")
    if text_key in FORM_TO_SPECIFIC_SERVICE:
        return FORM_TO_SPECIFIC_SERVICE[text_key]
    
    # Return original if no match found
    return specific_service_text


def is_valid_category(category: str) -> bool:
    """
    Checks if a category is valid
    
    Args:
        category: The category to validate
        
    Returns:
        True if the category is valid, False otherwise
    """
    return category in DOCKSIDE_PROS_CATEGORIES


def get_all_categories() -> List[str]:
    """
    Returns all valid service categories
    
    Returns:
        List of all service categories
    """
    return DOCKSIDE_PROS_CATEGORIES.copy()


def get_all_services_for_category(category: str) -> List[str]:
    """
    Returns all specific services for a given category
    
    Args:
        category: The service category
        
    Returns:
        List of specific services for the category
    """
    services = []
    
    # Find all services that map to this category
    for form_id, service_name in FORM_TO_SPECIFIC_SERVICE.items():
        # Get the category for this form_id
        service_category = get_service_category(form_id)
        if service_category == category and service_name not in services:
            services.append(service_name)
    
    return sorted(services)