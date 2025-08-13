#!/usr/bin/env python3
"""
Validate all Elementor form endpoints against the UPDATED webhook_routes.py mappings
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the actual DOCKSIDE_PROS_SERVICES from webhook_routes.py
from api.routes.webhook_routes import DOCKSIDE_PROS_SERVICES, get_direct_service_category

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

def main():
    print("=== Elementor Form Endpoint Validation (Updated) ===\n")
    print(f"Total mappings in DOCKSIDE_PROS_SERVICES: {len(DOCKSIDE_PROS_SERVICES)}\n")
    
    # Track discrepancies
    exact_matches = []
    keyword_matches = []
    default_fallbacks = []
    
    for endpoint in endpoints:
        # Use the actual function from webhook_routes.py
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
    
    if len(exact_matches) == len(endpoints):
        print("\n✅ SUCCESS: All endpoints are now properly mapped!")
    else:
        print(f"\n⚠️  WARNING: {len(default_fallbacks)} endpoints still using default fallback")

if __name__ == "__main__":
    main()