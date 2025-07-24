#!/usr/bin/env python3
"""
Robust version: Add smart category lookup with flexible pattern matching
"""

import os
import sys

def add_smart_lookup_function():
    """Add the smart lookup function to the file"""
    
    routing_file = "api/routes/routing_admin.py"
    
    if not os.path.exists(routing_file):
        print(f"❌ File not found: {routing_file}")
        return False
    
    print("🔧 ADDING SMART CATEGORY LOOKUP FUNCTION")
    print("=" * 50)
    
    # Read the current file
    with open(routing_file, 'r') as f:
        content = f.read()
    
    # Check if function already exists
    if "def find_category_from_specific_service" in content:
        print("ℹ️  Smart lookup function already exists")
        return True
    
    # Create backup
    backup_file = routing_file + ".smart_function_backup"
    with open(backup_file, 'w') as f:
        f.write(content)
    print(f"✅ Created backup: {backup_file}")
    
    # The smart lookup function
    smart_function = '''
def find_category_from_specific_service(specific_service: str) -> str:
    """
    Smart category lookup: derive primary category from specific service
    Uses DockSide Pros service dictionary to avoid defaulting to "Boater Resources"
    
    Example: "Outboard Engine Repair" → "Engines and Generators"
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if not specific_service:
        return "Boater Resources"
    
    # DockSide Pros Service Dictionary
    SERVICE_CATEGORY_MAPPINGS = {
        "Engines and Generators": [
            "Engines and Generators Sales/Service", "Generator Sales or Service",
            "Engine Service or Sales", "Outboard Engine Service", "Inboard Engine Service", 
            "Outboard Engine Repair", "Inboard Engine Repair", "Generator Repair",
            "Motor Repair", "Engine Installation", "Generator Installation",
            "Diesel Engine Service", "Gas Engine Service", "Marine Engine Repair",
            "Outboard Engine Service", "Inboard Engine Service"
        ],
        
        "Boat Maintenance": [
            "Ceramic Coating", "Boat Detailing", "Bottom Cleaning",
            "Boat and Yacht Maintenance", "Boat Oil Change", "Bilge Cleaning",
            "Jet Ski Maintenance", "Barnacle Cleaning", "Yacht Fire Detection Systems",
            "Boat Wrapping and Marine Protection Film", "Boat Cleaning", "Boat Washing"
        ],
        
        "Marine Systems": [
            "Marine Systems Install and Sales", "Yacht Stabilizers and Seakeepers",
            "Instrument Panel and Dashboard", "Yacht AC Sales", "Yacht AC Service",
            "Boat Electrical Service", "Boat Sound Systems", "Yacht Plumbing",
            "Boat Lighting", "Yacht Refrigeration and Watermakers", "Marine Electronics"
        ],
        
        "Boat and Yacht Repair": [
            "Boat and Yacht Repair", "Fiberglass Repair", "Welding & Metal Fabrication",
            "Carpentry & Woodwork", "Riggers & Masts", "Jet Ski Repair",
            "Boat Canvas and Upholstery", "Boat Decking and Yacht Flooring"
        ]
    }
    
    # Keyword mappings for partial matches
    KEYWORD_MAPPINGS = {
        "engine": "Engines and Generators",
        "motor": "Engines and Generators", 
        "generator": "Engines and Generators",
        "outboard": "Engines and Generators",
        "inboard": "Engines and Generators",
        "diesel": "Engines and Generators",
        "detailing": "Boat Maintenance",
        "cleaning": "Boat Maintenance",
        "maintenance": "Boat Maintenance",
        "ceramic": "Boat Maintenance",
        "repair": "Boat and Yacht Repair",
        "fiberglass": "Boat and Yacht Repair",
        "electrical": "Marine Systems",
        "plumbing": "Marine Systems",
        "ac service": "Marine Systems"
    }
    
    specific_lower = specific_service.lower().strip()
    
    # Method 1: Exact match
    for category, services in SERVICE_CATEGORY_MAPPINGS.items():
        for service in services:
            if specific_lower == service.lower():
                logger.info(f"🎯 Exact service match: '{specific_service}' → {category}")
                return category
    
    # Method 2: Partial match
    for category, services in SERVICE_CATEGORY_MAPPINGS.items():
        for service in services:
            if specific_lower in service.lower() or service.lower() in specific_lower:
                logger.info(f"🎯 Partial service match: '{specific_service}' → {category} (matched: {service})")
                return category
    
    # Method 3: Keyword match
    for keyword, category in KEYWORD_MAPPINGS.items():
        if keyword in specific_lower:
            logger.info(f"🎯 Keyword match: '{specific_service}' → {category} (keyword: {keyword})")
            return category
    
    # Default fallback
    logger.warning(f"⚠️ No category match found for '{specific_service}' - defaulting to Boater Resources")
    return "Boater Resources"

'''
    
    # Find a good place to insert the function - look for the first function definition
    function_patterns = [
        "async def _process_single_unassigned_lead",
        "async def _get_unassigned_leads_from_ghl", 
        "def extract_location_data",
        "@router.post"
    ]
    
    insertion_point = 0
    for pattern in function_patterns:
        if pattern in content:
            insertion_point = content.find(pattern)
            break
    
    if insertion_point == 0:
        # Just insert at the beginning after imports
        import_end = content.find('\n\n')
        if import_end != -1:
            insertion_point = import_end + 2
    
    # Insert the function
    new_content = content[:insertion_point] + smart_function + '\n' + content[insertion_point:]
    
    # Write the updated content
    with open(routing_file, 'w') as f:
        f.write(new_content)
    
    print("✅ Added smart category lookup function")
    return True

def update_service_assignment():
    """Update the service assignment logic to use smart lookup"""
    
    routing_file = "api/routes/routing_admin.py"
    
    with open(routing_file, 'r') as f:
        content = f.read()
    
    # Look for any service_category assignment
    patterns_to_find = [
        'service_category = "Boater Resources"',
        "service_category = 'Boater Resources'",
        'service_category = "Boater Resources"  # Default'
    ]
    
    replacement_found = False
    for pattern in patterns_to_find:
        if pattern in content:
            # Replace with smart lookup
            new_assignment = '''# Smart category lookup from specific service
                if specific_service:
                    service_category = find_category_from_specific_service(specific_service)
                    logger.info(f"🧠 Smart lookup: '{specific_service}' → {service_category}")
                else:
                    service_category = "Boater Resources"  # Final fallback'''
            
            content = content.replace(pattern, new_assignment)
            replacement_found = True
            print(f"✅ Replaced: {pattern}")
            break
    
    if not replacement_found:
        print("ℹ️  Could not find exact pattern - will provide manual instructions")
        return False
    
    # Write the updated content
    with open(routing_file, 'w') as f:
        f.write(content)
    
    return True

def provide_manual_instructions():
    """Provide manual instructions for the update"""
    
    print("\n📝 MANUAL UPDATE INSTRUCTIONS:")
    print("=" * 50)
    print("Since automatic replacement failed, please manually:")
    print("")
    print("1. Open: api/routes/routing_admin.py")
    print("2. Find this line:")
    print('   service_category = "Boater Resources"  # Default')
    print("")
    print("3. Replace it with:")
    print("""   # Smart category lookup from specific service
   if specific_service:
       service_category = find_category_from_specific_service(specific_service)
       logger.info(f"🧠 Smart lookup: '{specific_service}' → {service_category}")
   else:
       service_category = "Boater Resources"  # Final fallback""")
    print("")
    print("4. Save the file")
    print("")
    print("📍 Location: Look for where custom_fields are processed")
    print("📍 Context: Should be near where specific_service is extracted")

def main():
    """Main execution function"""
    print("🚀 LEAD ROUTER PRO - ROBUST SMART LOOKUP")
    print("=" * 55)
    
    # Step 1: Add the smart lookup function
    function_added = add_smart_lookup_function()
    
    if not function_added:
        print("❌ Failed to add smart lookup function")
        return
    
    # Step 2: Update the service assignment logic
    assignment_updated = update_service_assignment()
    
    print("\n" + "=" * 55)
    if function_added and assignment_updated:
        print("✅ SMART CATEGORY LOOKUP COMPLETED!")
        print("\n🧠 ENHANCEMENT READY:")
        print("   → 'Outboard Engine Repair' → 'Engines and Generators'")
        print("   → 'AC Service' → 'Marine Systems'") 
        print("   → 'Boat Detailing' → 'Boat Maintenance'")
        print("\n🔗 Test bulk assignment - should now categorize correctly!")
    elif function_added:
        print("✅ SMART LOOKUP FUNCTION ADDED")
        provide_manual_instructions()
    else:
        print("❌ SMART LOOKUP SETUP FAILED")

if __name__ == "__main__":
    main()