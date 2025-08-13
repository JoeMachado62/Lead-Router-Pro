# comprehensive_service_mappings.py
"""
Comprehensive 1:1 mapping dictionary for DockSide Pros service forms
Based on the complete service data dictionary provided
"""

# Main category mappings - Maps form identifiers to primary service categories
DOCKSIDE_PROS_SERVICE_CATEGORIES = {
    # 1. Boat Maintenance
    "boat_maintenance": "Boat Maintenance",
    "ceramic_coating": "Boat Maintenance",
    "boat_detailing": "Boat Maintenance",
    "bottom_cleaning": "Boat Maintenance",
    "boat_and_yacht_maintenance": "Boat Maintenance",
    "boat_oil_change": "Boat Maintenance",
    "bilge_cleaning": "Boat Maintenance",
    "jet_ski_maintenance": "Boat Maintenance",
    "barnacle_cleaning": "Boat Maintenance",
    "yacht_fire_detection_systems": "Boat Maintenance",
    "boat_wrapping_and_marine_protection_film": "Boat Maintenance",
    "boat_wrapping": "Boat Maintenance",
    "marine_protection_film": "Boat Maintenance",
    
    # 2. Boat Hauling and Yacht Delivery
    "boat_hauling_and_yacht_delivery": "Boat Hauling and Yacht Delivery",
    "yacht_delivery": "Boat Hauling and Yacht Delivery",
    "boat_hauling_and_transport": "Boat Hauling and Yacht Delivery",
    "boat_hauling": "Boat Hauling and Yacht Delivery",
    "boat_transport": "Boat Hauling and Yacht Delivery",
    
    # 3. Boat and Yacht Repair
    "boat_and_yacht_repair": "Boat and Yacht Repair",
    "fiberglass_repair": "Boat and Yacht Repair",
    "welding_metal_fabrication": "Boat and Yacht Repair",
    "welding_and_metal_fabrication": "Boat and Yacht Repair",
    "carpentry_woodwork": "Boat and Yacht Repair",
    "carpentry_and_woodwork": "Boat and Yacht Repair",
    "riggers_masts": "Boat and Yacht Repair",
    "riggers_and_masts": "Boat and Yacht Repair",
    "jet_ski_repair": "Boat and Yacht Repair",
    "boat_canvas_and_upholstery": "Boat and Yacht Repair",
    "canvas_upholstery": "Boat and Yacht Repair",
    "boat_decking_and_yacht_flooring": "Boat and Yacht Repair",
    "boat_decking": "Boat and Yacht Repair",
    "yacht_flooring": "Boat and Yacht Repair",
    
    # 4. Buying or Selling a Boat
    "buying_or_selling_a_boat": "Buying or Selling a Boat",
    "buying_selling_boat_yacht": "Buying or Selling a Boat",
    "boat_insurance": "Buying or Selling a Boat",
    "yacht_insurance": "Buying or Selling a Boat",
    "yacht_builder": "Buying or Selling a Boat",
    "yacht_broker": "Buying or Selling a Boat",
    "boat_broker": "Buying or Selling a Boat",
    "boat_builder": "Buying or Selling a Boat",
    "boat_financing": "Buying or Selling a Boat",
    "boat_surveyors": "Buying or Selling a Boat",
    "yacht_dealers": "Buying or Selling a Boat",
    "boat_dealers": "Buying or Selling a Boat",
    
    # 5. Engines and Generators
    "engines_and_generators": "Engines and Generators",
    "engines_generators_sales_service": "Engines and Generators",
    "generator_sales_or_service": "Engines and Generators",
    "generator_sales": "Engines and Generators",
    "generator_service": "Engines and Generators",  # This was missing!
    "generator_service_repair": "Engines and Generators",
    "engine_service_or_sales": "Engines and Generators",
    "engine_service": "Engines and Generators",
    "engine_sales": "Engines and Generators",
    "outboard_engine_service": "Engines and Generators",
    "outboard_engine_sales": "Engines and Generators",
    "inboard_engine_service": "Engines and Generators",
    "inboard_engine_sales": "Engines and Generators",
    "diesel_engine_service": "Engines and Generators",
    "diesel_engine_sales": "Engines and Generators",
    
    # 6. Marine Systems
    "marine_systems": "Marine Systems",
    "marine_systems_install_and_sales": "Marine Systems",
    "yacht_stabilizers_and_seakeepers": "Marine Systems",
    "stabilizers_seakeepers": "Marine Systems",
    "instrument_panel_and_dashboard": "Marine Systems",
    "instrument_panel": "Marine Systems",
    "dashboard": "Marine Systems",
    "yacht_ac_sales": "Marine Systems",
    "yacht_ac_service": "Marine Systems",
    "boat_electrical_service": "Marine Systems",
    "boat_sound_systems": "Marine Systems",
    "yacht_plumbing": "Marine Systems",
    "boat_lighting": "Marine Systems",
    "yacht_refrigeration_and_watermakers": "Marine Systems",
    "yacht_refrigeration": "Marine Systems",
    "watermakers": "Marine Systems",
    
    # 7. Docks, Seawalls and Lifts
    "docks_seawalls_and_lifts": "Docks, Seawalls and Lifts",
    "dock_and_seawall_builders_or_repair": "Docks, Seawalls and Lifts",
    "dock_seawall_builders": "Docks, Seawalls and Lifts",
    "dock_repair": "Docks, Seawalls and Lifts",
    "seawall_repair": "Docks, Seawalls and Lifts",
    "boat_lift_installers": "Docks, Seawalls and Lifts",
    "boat_lift": "Docks, Seawalls and Lifts",
    "floating_dock_sales": "Docks, Seawalls and Lifts",
    "floating_dock": "Docks, Seawalls and Lifts",
    "davit_and_hydraulic_platform": "Docks, Seawalls and Lifts",
    "davit_hydraulic_platform": "Docks, Seawalls and Lifts",
    "hull_dock_seawall_or_piling_cleaning": "Docks, Seawalls and Lifts",
    "hull_cleaning": "Docks, Seawalls and Lifts",
    "piling_cleaning": "Docks, Seawalls and Lifts",
    
    # 8. Boat Towing
    "boat_towing": "Boat Towing",
    "get_emergency_tow": "Boat Towing",
    "emergency_tow": "Boat Towing",
    "get_towing_membership": "Boat Towing",
    "towing_membership": "Boat Towing",
    
    # 9. Boat Charters and Rentals
    "boat_charters_and_rentals": "Boat Charters and Rentals",
    "boat_charters": "Boat Charters and Rentals",
    "boat_rentals": "Boat Charters and Rentals",
    "boat_clubs": "Boat Charters and Rentals",
    "fishing_charters": "Boat Charters and Rentals",  # This was the one that failed!
    "yacht_and_catamaran_charters": "Boat Charters and Rentals",
    "yacht_catamaran_charters": "Boat Charters and Rentals",
    "sailboat_charters": "Boat Charters and Rentals",
    "efoil_kiteboarding_wing_surfing": "Boat Charters and Rentals",
    "efoil_kiteboarding": "Boat Charters and Rentals",
    "wing_surfing": "Boat Charters and Rentals",
    "dive_equipment_and_services": "Boat Charters and Rentals",
    "dive_equipment": "Boat Charters and Rentals",
    "dive_services": "Boat Charters and Rentals",
    
    # 10. Boater Resources
    "boater_resources": "Boater Resources",
    "boat_or_yacht_parts": "Boater Resources",
    "boat_yacht_parts": "Boater Resources",
    "yacht_wifi": "Boater Resources",
    "vessel_wifi": "Boater Resources",
    "provisioning": "Boater Resources",
    "boat_salvage": "Boater Resources",
    "yacht_photography": "Boater Resources",
    "yacht_videography": "Boater Resources",
    "maritime_advertising_pr_and_web_design": "Boater Resources",
    "maritime_advertising": "Boater Resources",
    "yacht_crew_placement": "Boater Resources",
    "yacht_account_management_and_bookkeeping": "Boater Resources",
    "yacht_account_management": "Boater Resources",
    
    # 11. Fuel Delivery
    "fuel_delivery": "Fuel Delivery",
    
    # 12. Waterfront Property
    "waterfront_property": "Waterfront Property",
    "waterfront_homes_for_sale": "Waterfront Property",
    "sell_your_waterfront_home": "Waterfront Property",
    "waterfront_new_developments": "Waterfront Property",
    
    # 13. Maritime Education and Training
    "maritime_education_and_training": "Maritime Education and Training",
    "maritime_education": "Maritime Education and Training",
    "maritime_training": "Maritime Education and Training",
    
    # 14. Dock and Slip Rental
    "dock_and_slip_rental": "Dock and Slip Rental",
    "dock_slip_rental": "Dock and Slip Rental",
    "rent_my_dock": "Dock and Slip Rental",
    
    # 15. Yacht Management
    "yacht_management": "Yacht Management",
    
    # 16. Wholesale or Dealer Product Pricing
    "wholesale_or_dealer_product_pricing": "Wholesale or Dealer Product Pricing",
    "wholesale_dealer_pricing": "Wholesale or Dealer Product Pricing",
    
    # Vendor forms
    "vendor_application": "Vendor Application",
    "join_network": "Vendor Application",
    "provider_signup": "Vendor Application",
    
    # General fallbacks
    "general_inquiry": "Boater Resources",
    "contact": "Boater Resources",
    "quote_request": "Boater Resources"
}

# ZIP code field mappings - Maps various form field names to standardized field name
ZIP_CODE_FIELD_MAPPINGS = {
    # Generic variations
    "What Zip Code Are You Requesting Service In?": "zip_code_of_service",
    "Zip Code": "zip_code_of_service",
    "Service Zip Code": "zip_code_of_service",
    "Location": "zip_code_of_service",
    "ZIP Code": "zip_code_of_service",
    "Postal Code": "zip_code_of_service",
    "Service Location": "zip_code_of_service",
    
    # Category-specific ZIP field names
    "What Zip Code Are You Requesting a Fishing Charter In?": "zip_code_of_service",
    "What Zip Code Are You Requesting a Generator Service In?": "zip_code_of_service",
    "What Zip Code Are You Requesting Engine Service In?": "zip_code_of_service",
    "What Zip Code Are You Requesting Boat Maintenance In?": "zip_code_of_service",
    "What Zip Code Are You Requesting Repair Service In?": "zip_code_of_service",
    "What Zip Code Are You Requesting Marine Systems Service In?": "zip_code_of_service",
    "What Zip Code Are You Requesting Dock Service In?": "zip_code_of_service",
    "What Zip Code Are You Requesting Emergency Tow In?": "zip_code_of_service",
    "What Zip Code Are You Requesting Fuel Delivery In?": "zip_code_of_service",
    "What Zip Code Is Your Vessel Located In?": "zip_code_of_service",
    "What Zip Code Is The Service Needed In?": "zip_code_of_service",
    "Where Do You Need Service? (ZIP Code)": "zip_code_of_service",
    "Service Area ZIP Code": "zip_code_of_service",
    "Vessel Location ZIP Code": "zip_code_of_service",
    
    # Vendor/business ZIP fields
    "Business ZIP Code": "vendor_zip_code",
    "Company ZIP Code": "vendor_zip_code",
    "Service Areas": "service_zip_codes",
    "Coverage ZIP Codes": "service_zip_codes",
    "Areas You Service": "service_zip_codes"
}

# Specific service field mappings
SPECIFIC_SERVICE_FIELD_MAPPINGS = {
    # Generic variations
    "What Specific Service(s) Do You Request?": "specific_service_needed",
    "What Specific Service Do You Request?": "specific_service_needed",
    "Service Needed": "specific_service_needed",
    "Service Request": "specific_service_needed",
    "Services": "specific_service_needed",
    "Specific Service": "specific_service_needed",
    "Service Type": "specific_service_needed",
    
    # Category-specific service fields
    "What Specific Charter Do You Request?": "specific_service_needed",
    "What Specific Maintenance Do You Need?": "specific_service_needed",
    "What Type of Repair Do You Need?": "specific_service_needed",
    "What Generator Service Do You Need?": "specific_service_needed",
    "What Engine Service Do You Need?": "specific_service_needed",
    "What Marine System Do You Need Service On?": "specific_service_needed",
    "What Dock/Lift Service Do You Need?": "specific_service_needed",
    "Type of Service Requested": "specific_service_needed",
    "Service Details": "specific_service_needed",
    
    # Subcategory fields
    "Select Your Specific Service": "specific_service_needed",
    "Choose Service Type": "specific_service_needed",
    "Service Selection": "specific_service_needed"
}

# Specific services by category - Maps dropdown values to categories
SPECIFIC_SERVICES_BY_CATEGORY = {
    "Boat Maintenance": [
        "Ceramic Coating", "Boat Detailing", "Bottom Cleaning", "Oil Change",
        "Bilge Cleaning", "Jet Ski Maintenance", "Barnacle Cleaning",
        "Fire Detection Systems", "Boat Wrapping or Marine Protection Film", "Other"
    ],
    
    "Boat and Yacht Repair": {
        "Main": ["Fiberglass", "Welding or Metal Fabrication", "Carpentry", 
                 "Teak or Woodwork", "Riggers & Masts", "Jet Ski Repair",
                 "Canvas or Upholstery", "Boat Decking", "Other"],
        
        "Fiberglass Repair": ["Hull Crack or Structural Repair", "Gelcoat Repair and Color Matching",
                              "Transom Repair & Reinforcement", "Deck Delamination & Soft Spot Repair",
                              "Stringer & Bulkhead Repair", "Other"],
        
        "Welding & Metal Fabrication": ["Aluminum or Stainless Steel Hull Repairs",
                                        "Custom Railings, Ladders or Boarding Equipment",
                                        "T-Tops, Hardtops or Bimini Frames",
                                        "Fuel or Water Tank Fabrication",
                                        "Exhaust, Engine Bed or Structural Reinforcement", "Other"],
        
        "Carpentry & Woodwork": ["Interior Woodwork and Cabinetry", "Teak Deck Repair or Replacement",
                                 "Varnishing & Wood Finishing", "Structural Wood Repairs",
                                 "Custom Furniture or Fixtures", "Other"],
        
        "Riggers & Masts": ["Standing Rigging Inspection or Replacement",
                            "Running Rigging Replacement", "Mast Stepping & Unstepping",
                            "Mast Repair or Replacement", "Rig Tuning & Load Testing",
                            "Fitting & Hardware Inspection", "Other"],
        
        "Jet Ski Repair": ["Engine Diagnostics & Repair", "Jet Pump Rebuild or Replacement",
                           "Fuel Systems Cleaning or Repair", "Battery or Electrical Repairs",
                           "Cooling System Flush or Repair", "General Maintenance", "Other"],
        
        "Boat Canvas and Upholstery": ["Upholstery", "Canvas or Sunshade", "Trim and Finish",
                                        "Boat Cover or T-Top", "Acrylic or Strataglass Enclosures", "Other"],
        
        "Boat Decking and Yacht Flooring": ["SeaDek", "Real Teak Wood", "Cork", "Synthetic Teak",
                                             "Vinyl Flooring", "Tile Flooring", "Other"]
    },
    
    "Buying or Selling a Boat": {
        "Main": ["Buy", "Sell", "Trade"],
        "Boat Insurance": ["I Just Bought the Vessel", "New Vessel Policy",
                           "Looking For Quotes Before Purchasing Vessel"],
        "Yacht Insurance": ["I Just Bought the Vessel", "New Vessel Policy",
                            "Looking For Quotes Before Purchasing Vessel"],
        "Yacht Broker": ["Buy a New Yacht", "Buy a Pre-Owned Yacht", "Sell a Pre-Owned Yacht",
                         "Trade My Yacht", "Looking to Charter My Yacht", "Looking for Yacht Management"],
        "Boat Broker": ["Buy a New Yacht", "Buy a Pre-Owned Yacht", "Sell a Pre-Owned Yacht",
                        "Trade My Yacht", "Looking to Charter My Yacht", "Looking for Yacht Management"],
        "Boat Financing": ["New Boat Financing", "Used Boat Financing", "Refinancing"],
        "Boat Surveyors": ["Hull & Engine(s)", "Thermal Imaging", "Insurance/Damage",
                           "Hull Only", "Engine(s) Only"]
    },
    
    "Engines and Generators": {
        "Main": ["Outboard Engine Service", "Outboard Engine Sales", "Inboard Engine Service",
                 "Inboard Engine Sales", "Diesel Engine Service", "Diesel Engine Sales",
                 "Generator Service", "Generator Sales"],
        
        "Generator Sales or Service": ["Generator Installation", "Routine Generator Maintenance",
                                       "Electrical System Integration & Transfer Switches",
                                       "Diagnostics & Repairs", "Sound Shielding & Vibration Control",
                                       "Generator Sales"],
        
        "Engine Service or Sales": ["New Engine Sales", "Engine Refit", "Routine Engine Maintenance",
                                    "Cooling System Service", "Fuel System Cleaning & Repair",
                                    "Engine Diagnostics & Troubleshooting",
                                    "Outboard or Inboard Engine Repair or Rebuild",
                                    "Diesel Engine Repair or Rebuild"]
    },
    
    "Marine Systems": {
        "Main": ["Stabilizers or Seakeepers", "Instrument Panel and Dashboard",
                 "AC Sales or Service", "Electrical Service", "Sound System",
                 "Plumbing", "Lighting", "Refrigeration or Watermakers"],
        
        "Yacht Stabilizers and Seakeepers": ["New Seakeeper Install", "Other Stabilizer Install",
                                             "Stabilizer Maintenance", "Stabilizer Retrofit or Upgrades"],
        
        "Instrument Panel and Dashboard": ["Electronic Dashboard Install or Upgrades",
                                           "Instrument Panel Rewiring & Troubleshooting",
                                           "Custom Dashboard Fabrication & Refacing",
                                           "Gauge Replacement & Calibration",
                                           "Backlighting & Switch Panel Modernization"],
        
        "Yacht AC": ["New AC Install or Replacement", "AC Maintenance & Servicing",
                     "Refrigerant Charging & Leak Repair", "Pump & Water Flow Troubleshooting",
                     "Thermostat & Control Panel Upgrades"],
        
        "Boat Electrical Service": ["Battery System Install or Maintenance", "Wiring & Rewiring",
                                    "Shore Power & Inverter Systems", "Lighting Systems",
                                    "Electrical Panel & Breaker", "Navigation & Communication",
                                    "Generator Electrical Integration", "Solar Power & Battery Charging"],
        
        "Boat Sound Systems": ["Marine Audio System Install", "Speaker & Subwoofer Upgrades",
                               "Amplifier Setup & Tuning", "Multi-Zone Audio Configuration",
                               "Troubleshooting & System Repairs"],
        
        "Yacht Plumbing": ["Freshwater System Install or Repair", "Marine Head & Toilet Systems",
                           "Greywater or Blackwater Tank Maintenance",
                           "Bilge Pump Install or Drainage",
                           "Watermaker (Desalinator) Service & Install"],
        
        "Boat Lighting": ["Navigation & Anchor Light Install", "Underwater Lighting",
                          "Interior Cabin Lighting", "Deck, Cockpit & Courtesy Lighting",
                          "Electrical Troubleshooting & Wiring"],
        
        "Yacht Refrigeration and Watermakers": ["Marine Refrigerator & Freezer Install",
                                                "Refrigeration System Repairs & Troubleshooting",
                                                "Watermaker (Desalinator) Install",
                                                "Watermaker Maintenance & Servicing",
                                                "Cold Plate & Evaporator Upgrades"]
    },
    
    "Docks, Seawalls and Lifts": {
        "Dock and Seawall Builders or Repair": ["Seawall Construction or Repair", "New Dock",
                                                "Dock Repair", "Pilings or Structural Support",
                                                "Floating Docks", "Boat Lift",
                                                "Seawall or Piling Cleaning"],
        
        "Boat Lift Installers": ["New Boat Lift", "Boat Lift Installation",
                                 "Lift Motor & Gearbox Repair", "Cable & Pulley Replacement",
                                 "Annual Maintenance & Alignment"],
        
        "Floating Dock Sales": ["New Floating Dock", "Floating Dock Installation",
                                "Floating Dock Repair & Float Replacement",
                                "Custom Modifications & Add-Ons",
                                "Seasonal Maintenance & Dock Repositioning"],
        
        "Davit and Hydraulic Platform": ["New Davit & Hydraulic Platform Sales",
                                         "Davit & Hydraulic Platform Installation",
                                         "Hydraulic Systems Repair & Fluid Service",
                                         "Davit Motor & Winch Servicing",
                                         "Weight Limit Testing & Calibration",
                                         "Annual Maintenance & Safety Inspection"],
        
        "Hull, Dock, Seawall or Piling Cleaning": ["Hull Cleaning", "Seawall Cleaning",
                                                   "Piling Cleaning", "Zinc Replacement",
                                                   "Commercial or Industrial Requests"]
    },
    
    "Boat Charters and Rentals": {
        "Main": ["Weekly or Monthly Yacht or Catamaran Charter", "Daily Yacht or Catamaran Charter",
                 "Sailboat Charter", "Fishing Charter", "Party Boat Charter", "Pontoon Charter",
                 "Jet Ski Rental", "Paddleboard Rental", "Kayak Rental",
                 "eFoil, Kiteboarding or Wing Surfing Lessons", "Boat Club"],
        
        "Boat Clubs": ["Membership Boat Club", "Yacht Club", "Private Fractional Ownership Club",
                       "Sailing Club", "Luxury Boat Membership Club"],
        
        "Fishing Charters": ["Inshore Fishing Charter", "Offshore (Deep Sea) Fishing Charter",
                             "Reef & Wreck Fishing Charter", "Drift Boat Charter",
                             "Freshwater Fishing Charter", "Private Party Boat Charter",
                             "Fishing Resort Vacation"],
        
        "Yacht and Catamaran Charters": ["Day Yacht Charter", "Day Catamaran Charter",
                                         "Group Yacht or Catamaran Charter",
                                         "Weekly or Monthly Catamaran or Yacht Charter", "Other"],
        
        "Sailboat Charters": ["Bareboat Charter (No Captain or Crew)", "Skippered Charter",
                              "Crewed Charter", "Cabin Charter", "Sailing Charter (Learn to Sail)",
                              "Weekly or Monthly Charter"],
        
        "eFoil, Kiteboarding & Wing Surfing": ["eFoil Lessons", "eFoil Equipment",
                                                "Kiteboarding Lessons", "Kiteboarding Equipment",
                                                "Wing Surfing Lessons", "Wing Surfing Equipment"],
        
        "Dive Equipment and Services": ["Private Scuba Diving Charter", "Shared Scuba Diving Charter",
                                        "Scuba Equipment Rental", "Snorkel and Free Diving Charter",
                                        "Night Diving", "Underwater Scooter Rental"]
    },
    
    "Boater Resources": {
        "Main": ["Boat or Yacht Parts", "Vessel WiFi or Communications", "Provisioning",
                 "Boat Salvage", "Photography or Videography", "Crew Management",
                 "Account Management and Bookkeeping", "Marketing or Web Design",
                 "Vessel Management", "Other"],
        
        "Yacht WiFi": ["New WiFi", "WiFi Diagnostics or Troubleshooting", "Boat Network",
                       "Satellite", "Cellular", "Marina Connections"],
        
        "Provisioning": ["Food & Beverage Provisioning", "Galley & Kitchen Supplies",
                         "Crew Provisioning", "Cabin & Guest Comfort Supplies",
                         "Medical & First Aid Provisioning", "Cleaning & Maintenance Supplies",
                         "Floral & Décor Provisioning", "Custom Orders & Luxury Concierge Items",
                         "Fishing, Dive or Watersports Supplies"],
        
        "Boat and Yacht Parts": ["Engine & Propulsion Parts", "Electrical & Battery Systems Parts",
                                 "Steering & Control Systems Parts", "Navigation & Electronics Parts",
                                 "Plumbing & Water Systems Parts", "Hull, Deck & Hardware Parts",
                                 "Safety Equipment and Emergency Gear", "AC, Refrigeration or Watermaker Parts",
                                 "Canvas, Covers or Upholstery Parts", "Paint, Maintenance or Cleaning Supplies",
                                 "Trailer or Towing Components", "Anchoring or Mooring Gear Parts", "Other"],
        
        "Yacht Photography": ["Listing Photography or Videography (Brokerage & Sales)",
                              "Lifestyle & Charter Photography or Videography",
                              "Drone & Aerial Photography or Videography",
                              "Virtual Tours/3D Walkthroughs",
                              "Refit or Restoration Progress Documentation",
                              "Underwater Photography or Videography", "Event Coverage",
                              "Social Media Reels/Short-Form Content"],
        
        "Yacht Videography": ["Listing Photography or Videography (Brokerage & Sales)",
                              "Lifestyle & Charter Photography or Videography",
                              "Drone & Aerial Photography or Videography",
                              "Virtual Tours/3D Walkthroughs",
                              "Refit or Restoration Progress Documentation",
                              "Underwater Photography or Videography", "Event Coverage",
                              "Social Media Reels/Short-Form Content"],
        
        "Maritime Advertising, PR and Web Design": ["Search Engine Optimization (SEO)", "Web Design",
                                                    "PR", "Influencer or Affiliate Marketing",
                                                    "Podcasts", "Sponsorships", "Paid Ads Management",
                                                    "Social Media Marketing", "Email Marketing & Automation",
                                                    "Content Marketing and Blogging", "Video Marketing",
                                                    "CRM Integration & Lead Nurturing"],
        
        "Yacht Crew Placement": ["Captain", "First Mate", "Engineer", "Deckhand", "Chef/Cook",
                                 "Stew", "Bosun", "Purser (Provisioning, Accounting, Logistics, etc)",
                                 "Nanny/Masseuse/Personal Trainer", "Security Officer/Bodyguard"],
        
        "Yacht Account Management and Bookkeeping": ["Operational Expense Tracking",
                                                     "Crew Payroll & Expense Reconciliation",
                                                     "Budget Planning & Forecasting",
                                                     "Charter Income & Expense Reporting",
                                                     "Vendor & Invoice Management",
                                                     "Tax Compliance & VAT Management",
                                                     "Insurance Premium & Policy Accounting",
                                                     "Financial Reporting & Owner Statements"],
        
        "Boat Salvage": ["Emergency Water Removal", "Emergency Boat Recovery",
                         "Sell Boat for Parts", "Mold/Water Remediation"]
    },
    
    "Fuel Delivery": ["Dyed Diesel Fuel (For Boats)", "Regular Diesel Fuel (Landside Business)",
                      "Rec 90 (Ethanol Free Gas)"],
    
    "Waterfront Property": {
        "Main": ["Buy a Waterfront Home or Condo", "Sell a Waterfront Home or Condo",
                 "Buy a Waterfront New Development", "Rent a Waterfront Property"]
    },
    
    "Maritime Education and Training": ["Yacht, Sailboat or Catamaran On Water Training",
                                        "Interested In Buying a Boat/Insurance Signoff",
                                        "Maritime Academy", "Sailing Schools", "Captains License"],
    
    "Dock and Slip Rental": ["Private Dock", "Boat Slip", "Marina", "Mooring Ball"],
    
    "Yacht Management": ["Full Service Vessel Management",
                         "Technical Management (maintenance, repairs, upgrades, etc)",
                         "Crew Management", "Accounting & Financial Management",
                         "Insurance & Risk Management", "Regulatory Compliance",
                         "Maintenance & Refit Management",
                         "Logistical Support (Transportation, Provisioning, Fuel or Dockage)"],
    
    "Wholesale or Dealer Product Pricing": ["Apparel", "Boat Accessories",
                                            "Boat Maintenance & Cleaning Products",
                                            "Boat Safety Products", "Diving Equipment",
                                            "Dock Accessories", "Fishing Gear",
                                            "Personal Watercraft", "Other"]
}

# Combine all field mappings into one comprehensive dictionary
COMPREHENSIVE_FIELD_MAPPINGS = {
    **ZIP_CODE_FIELD_MAPPINGS,
    **SPECIFIC_SERVICE_FIELD_MAPPINGS,
    
    # Add other common field mappings
    "First Name": "firstName",
    "Last Name": "lastName",
    "Email": "email",
    "Email Address": "email",
    "Phone": "phone",
    "Phone Number": "phone",
    "Contact Phone": "phone",
    
    # Vessel information fields
    "Your Vessel Manufacturer?": "vessel_make",
    "Vessel Manufacturer": "vessel_make",
    "Boat Make": "vessel_make",
    "Your Vessel Model or Length of Vessel in Feet?": "vessel_model",
    "Vessel Model": "vessel_model",
    "Boat Model": "vessel_model",
    "Vessel Year": "vessel_year",
    "Boat Year": "vessel_year",
    
    # Timeline fields
    "When Do You Need Service?": "desired_timeline",
    "Desired Timeline": "desired_timeline",
    "Service Timeline": "desired_timeline",
    "When Do You Prefer Your Service?": "desired_timeline",
    
    # Notes/special requests
    "Special Requests or Notes": "special_requests__notes",
    "Additional Notes": "special_requests__notes",
    "Comments": "special_requests__notes",
    "Special Instructions": "special_requests__notes",
    
    # Contact preference
    "How Should We Contact You Back?": "contact_preference",
    "Preferred Contact Method": "contact_preference",
    "Best Way to Reach You": "contact_preference",
    
    # Consent
    "Consent": "consent",
    "I Agree": "consent",
    "Terms Accepted": "consent",
    
    # Preferred partner
    "Preferred Partner": "preferred_partner",
    "Do You Have a Preferred Vendor?": "preferred_partner",
    "Preferred Service Provider": "preferred_partner"
}

def validate_form_identifier(form_identifier: str) -> str:
    """
    Validate and return the correct service category for a form identifier.
    Returns the category or None if not found.
    """
    form_id_lower = form_identifier.lower().strip()
    return DOCKSIDE_PROS_SERVICE_CATEGORIES.get(form_id_lower)

def map_field_name(field_name: str) -> str:
    """
    Map a form field name to its standardized field name.
    Returns the mapped name or the original if not found.
    """
    return COMPREHENSIVE_FIELD_MAPPINGS.get(field_name, field_name)

def get_specific_services_for_category(category: str, subcategory: str = None) -> list:
    """
    Get the list of specific services for a category/subcategory.
    """
    services = SPECIFIC_SERVICES_BY_CATEGORY.get(category, [])
    
    if isinstance(services, dict):
        if subcategory and subcategory in services:
            return services[subcategory]
        elif "Main" in services:
            return services["Main"]
    
    return services if isinstance(services, list) else []