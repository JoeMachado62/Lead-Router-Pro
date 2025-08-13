#!/usr/bin/env python3
"""
Script to generate the update needed for webhook_routes.py to fix the missing mappings
"""

# Missing mappings that need to be added
MISSING_MAPPINGS = {
    # Email/Contact forms
    "email_subscribe": "Boater Resources",
    
    # Boat Maintenance (should map to existing services)
    "boat_maintenance": "Boat Maintenance",
    "bilge_cleaning": "Boat Maintenance",  # maps to boat_bilge_cleaning
    "bottom_cleaning": "Boat Maintenance",  # maps to boat_bottom_cleaning  
    "oil_change": "Boat Maintenance",  # maps to boat_oil_change
    
    # Boat and Yacht Repair
    "canvas_upholstery": "Boat and Yacht Repair",  # maps to boat_canvas_upholstery
    "decking_flooring": "Boat and Yacht Repair",  # maps to boat_decking_yacht_flooring
    
    # Buying or Selling a Boat
    "buying_selling_boats": "Buying or Selling a Boat",
    "boat_broker": "Buying or Selling a Boat",  # maps to boat_brokers
    
    # Engines and Generators
    "engines_generators": "Engines and Generators",
    "engine_service": "Engines and Generators",
    "engine_sales": "Engines and Generators",
    
    # Marine Systems
    "marine_systems": "Marine Systems",
    "ac_sales": "Marine Systems",  # maps to yacht_ac_sales
    "ac_service": "Marine Systems",  # maps to yacht_ac_service
    "electrical_service": "Marine Systems",  # maps to boat_electrical_service
    "plumbing": "Marine Systems",  # maps to yacht_plumbing
    
    # Docks, Seawalls and Lifts
    "dock_seawall_builders": "Docks, Seawalls and Lifts",  # maps to dock_seawall_builders_repair
    "davit_hydraulic": "Docks, Seawalls and Lifts",  # maps to davit_hydraulic_platform
    "hull_dock_cleaning": "Docks, Seawalls and Lifts",
    
    # Boat Towing
    "emergency_tow": "Boat Towing",  # maps to get_emergency_tow
    "towing_membership": "Boat Towing",  # maps to get_towing_membership
    
    # Boat Charters and Rentals
    "dive_equipment": "Boat Charters and Rentals",  # maps to dive_equipment_services
    "efoil_kiteboarding": "Boat Charters and Rentals",  # maps to efoil_kiteboarding_wing_surfing
    
    # Boater Resources
    "yacht_parts": "Boater Resources",  # maps to boat_yacht_parts
    "yacht_crew": "Boater Resources",  # maps to yacht_crew_placement
    "yacht_accounting": "Boater Resources",  # maps to yacht_account_management
    "maritime_advertising": "Boater Resources",
    
    # Waterfront Property
    "waterfront_developments": "Waterfront Property",  # maps to new_waterfront_developments
    
    # Maritime Education and Training
    "maritime_education": "Maritime Education and Training",
}

def generate_update_code():
    print("=== Code to add to DOCKSIDE_PROS_SERVICES in webhook_routes.py ===\n")
    
    # Group by category
    categories = {}
    for key, category in MISSING_MAPPINGS.items():
        if category not in categories:
            categories[category] = []
        categories[category].append(key)
    
    # Generate the code
    for category, services in sorted(categories.items()):
        print(f'    # {category} - Additional mappings')
        for service in sorted(services):
            print(f'    "{service}": "{category}",')
        print()

if __name__ == "__main__":
    generate_update_code()
    
    print("=== Instructions ===")
    print("1. Add the above mappings to the DOCKSIDE_PROS_SERVICES dictionary in webhook_routes.py")
    print("2. This will ensure all 61 endpoints have proper service category mappings")
    print("3. The system will no longer fall back to 'Boater Resources' for these specific services")