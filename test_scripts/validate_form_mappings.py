#!/usr/bin/env python3
"""
Validate all Elementor form endpoints against the webhook_routes.py mappings
"""

# The DOCKSIDE_PROS_SERVICES mapping from webhook_routes.py
DOCKSIDE_PROS_SERVICES = {
    # Boat and Yacht Repair (18 services)
    "boat_yacht_repair": "Boat and Yacht Repair",
    "fiberglass_repair": "Boat and Yacht Repair",
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
    
    # Engines and Generators (9 services)
    "outboard_engine_service": "Engines and Generators",
    "outboard_engine_sales": "Engines and Generators",
    "inboard_engine_service": "Engines and Generators",
    "inboard_engine_sales": "Engines and Generators",
    "diesel_engine_service": "Engines and Generators",
    "diesel_engine_sales": "Engines and Generators",
    "generator_service": "Engines and Generators",
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

# All endpoints provided by the user
endpoints = [
    "email_subscribe",
    "join_network",
    "boat_maintenance",
    "bilge_cleaning",
    "bottom_cleaning",
    "boat_detailing",
    "oil_change",
    "ceramic_coating",
    "boat_yacht_repair",
    "fiberglass_repair",
    "welding_fabrication",
    "carpentry_woodwork",
    "riggers_masts",
    "jet_ski_repair",
    "canvas_upholstery",
    "decking_flooring",
    "buying_selling_boats",
    "boat_broker",
    "boat_insurance",
    "engines_generators",
    "generator_sales",
    "generator_service",
    "engine_service",
    "engine_sales",
    "marine_systems",
    "ac_sales",
    "ac_service",
    "electrical_service",
    "plumbing",
    "dock_seawall_builders",
    "boat_lift_installers",
    "floating_dock_sales",
    "davit_hydraulic",
    "hull_dock_cleaning",
    "emergency_tow",
    "towing_membership",
    "boat_charters_rentals",
    "boat_clubs",
    "yacht_charters",
    "dive_equipment",
    "efoil_kiteboarding",
    "fishing_charters",
    "sailboat_charters",
    "yacht_wifi",
    "provisioning",
    "yacht_parts",
    "boat_salvage",
    "yacht_photography",
    "yacht_videography",
    "yacht_crew",
    "yacht_accounting",
    "maritime_advertising",
    "fuel_delivery",
    "waterfront_homes_sale",
    "sell_waterfront_home",
    "waterfront_developments",
    "maritime_education",
    "dock_slip_rental",
    "rent_my_dock",
    "yacht_management",
    "wholesale_dealer_pricing"
]

def get_direct_service_category(form_identifier: str) -> str:
    """Direct service category mapping - matches logic in webhook_routes.py"""
    form_lower = form_identifier.lower()
    
    # Direct exact matches first
    if form_lower in DOCKSIDE_PROS_SERVICES:
        return DOCKSIDE_PROS_SERVICES[form_lower]
    
    # Keyword matching for partial matches
    for service_key, category in DOCKSIDE_PROS_SERVICES.items():
        if service_key.replace("_", "") in form_lower.replace("_", ""):
            return category
    
    # Default fallback
    return "Boater Resources"

def main():
    print("=== Elementor Form Endpoint Validation ===\n")
    
    # Track discrepancies
    exact_matches = []
    keyword_matches = []
    default_fallbacks = []
    
    for endpoint in endpoints:
        category = get_direct_service_category(endpoint)
        
        # Check if it's an exact match
        if endpoint in DOCKSIDE_PROS_SERVICES:
            exact_matches.append((endpoint, category))
            print(f"✅ EXACT MATCH: {endpoint} → {category}")
        else:
            # Check if it's a keyword match
            matched = False
            for service_key, cat in DOCKSIDE_PROS_SERVICES.items():
                if service_key.replace("_", "") in endpoint.replace("_", ""):
                    keyword_matches.append((endpoint, category, service_key))
                    print(f"🔄 KEYWORD MATCH: {endpoint} → {category} (matched via: {service_key})")
                    matched = True
                    break
            
            if not matched:
                default_fallbacks.append((endpoint, category))
                print(f"⚠️  DEFAULT: {endpoint} → {category}")
    
    # Summary
    print(f"\n=== SUMMARY ===")
    print(f"Total endpoints: {len(endpoints)}")
    print(f"Exact matches: {len(exact_matches)}")
    print(f"Keyword matches: {len(keyword_matches)}")
    print(f"Default fallbacks: {len(default_fallbacks)}")
    
    # Detailed discrepancy report
    if keyword_matches or default_fallbacks:
        print(f"\n=== MAPPING DISCREPANCIES ===")
        
        if keyword_matches:
            print(f"\nKeyword Matches (may need adjustment):")
            for endpoint, category, matched_key in keyword_matches:
                print(f"  - {endpoint} → {category} (matched: {matched_key})")
        
        if default_fallbacks:
            print(f"\nDefault Fallbacks (need mapping):")
            for endpoint, category in default_fallbacks:
                print(f"  - {endpoint} → {category} (DEFAULT)")
                # Suggest possible matches
                suggestions = []
                endpoint_words = endpoint.replace("_", " ").split()
                for service_key in DOCKSIDE_PROS_SERVICES:
                    service_words = service_key.replace("_", " ").split()
                    if any(word in service_words for word in endpoint_words):
                        suggestions.append(service_key)
                if suggestions:
                    print(f"    Possible matches: {', '.join(suggestions[:3])}")

if __name__ == "__main__":
    main()