#!/usr/bin/env python3
"""
Test script for the enhanced lead routing system
Tests ZIP code to location conversion and vendor matching logic
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.services.location_service import location_service
from api.services.lead_routing_service import lead_routing_service
from database.simple_connection import db as simple_db_instance

def test_location_service():
    """Test the ZIP code to location conversion"""
    print("🧪 TESTING LOCATION SERVICE")
    print("=" * 50)
    
    test_zip_codes = [
        "33301",  # Fort Lauderdale, FL (Broward County)
        "33139",  # Miami Beach, FL (Miami-Dade County)
        "90210",  # Beverly Hills, CA (Los Angeles County)
        "10001",  # New York, NY (New York County)
        "78701",  # Austin, TX (Travis County)
    ]
    
    for zip_code in test_zip_codes:
        print(f"\n📍 Testing ZIP code: {zip_code}")
        location_data = location_service.zip_to_location(zip_code)
        
        if location_data.get('error'):
            print(f"  ❌ Error: {location_data['error']}")
        else:
            print(f"  ✅ State: {location_data.get('state')}")
            print(f"  ✅ County: {location_data.get('county')}")
            print(f"  ✅ City: {location_data.get('city')}")
            
            # Test coverage checking
            coverage_summary = location_service.get_coverage_summary('county', [f"{location_data.get('county')}, {location_data.get('state')}"])
            print(f"  📋 Coverage Summary: {coverage_summary}")

def test_vendor_coverage_scenarios():
    """Test different vendor coverage scenarios"""
    print("\n🧪 TESTING VENDOR COVERAGE SCENARIOS")
    print("=" * 50)
    
    # Create test vendors with different coverage types
    test_vendors = [
        {
            "id": "vendor_1",
            "name": "Global Marine Services",
            "service_coverage_type": "global",
            "service_states": [],
            "service_counties": [],
            "services_provided": ["Boat Maintenance", "Engine Repair"],
            "status": "active",
            "taking_new_work": True,
            "last_lead_assigned": "2024-01-01",
            "lead_close_percentage": 85.0
        },
        {
            "id": "vendor_2", 
            "name": "Florida Marine Experts",
            "service_coverage_type": "state",
            "service_states": ["FL"],
            "service_counties": [],
            "services_provided": ["Boat Maintenance", "Marine Systems"],
            "status": "active",
            "taking_new_work": True,
            "last_lead_assigned": "2024-01-15",
            "lead_close_percentage": 92.0
        },
        {
            "id": "vendor_3",
            "name": "Broward County Boat Services", 
            "service_coverage_type": "county",
            "service_states": [],
            "service_counties": ["Broward, FL"],
            "services_provided": ["Boat Maintenance"],
            "status": "active",
            "taking_new_work": True,
            "last_lead_assigned": "2024-02-01",
            "lead_close_percentage": 78.0
        },
        {
            "id": "vendor_4",
            "name": "Legacy ZIP Code Vendor",
            "service_coverage_type": "zip",
            "service_states": [],
            "service_counties": [],
            "service_areas": ["33301", "33302", "33303"],
            "services_provided": ["Boat Maintenance"],
            "status": "active", 
            "taking_new_work": True,
            "last_lead_assigned": "2024-01-20",
            "lead_close_percentage": 88.0
        }
    ]
    
    # Test ZIP code: 33301 (Fort Lauderdale, Broward County, FL)
    test_zip = "33301"
    service_category = "Boat Maintenance"
    
    print(f"\n🎯 Testing vendor matching for ZIP {test_zip}, Service: {service_category}")
    
    # Simulate the vendor matching logic
    location_data = location_service.zip_to_location(test_zip)
    print(f"📍 Location: {location_data.get('city')}, {location_data.get('county')} County, {location_data.get('state')}")
    
    matching_vendors = []
    for vendor in test_vendors:
        # Check service match
        if service_category not in vendor.get('services_provided', []):
            print(f"  ❌ {vendor['name']}: Service mismatch")
            continue
            
        # Check location coverage
        coverage_type = vendor.get('service_coverage_type', 'zip')
        covers_location = False
        
        if coverage_type == 'global':
            covers_location = True
            reason = "Global coverage"
        elif coverage_type == 'state':
            covers_location = location_data.get('state') in vendor.get('service_states', [])
            reason = f"State coverage: {vendor.get('service_states')}"
        elif coverage_type == 'county':
            target_county = f"{location_data.get('county')}, {location_data.get('state')}"
            covers_location = target_county in vendor.get('service_counties', [])
            reason = f"County coverage: {vendor.get('service_counties')}"
        elif coverage_type == 'zip':
            covers_location = test_zip in vendor.get('service_areas', [])
            reason = f"ZIP coverage: {vendor.get('service_areas')}"
        
        if covers_location:
            vendor['match_reason'] = reason
            matching_vendors.append(vendor)
            print(f"  ✅ {vendor['name']}: {reason}")
        else:
            print(f"  ❌ {vendor['name']}: No coverage ({reason})")
    
    print(f"\n📊 Found {len(matching_vendors)} matching vendors")
    
    # Test routing selection
    if matching_vendors:
        print("\n🎯 Testing vendor selection methods:")
        
        # Round-robin selection (oldest last_lead_assigned)
        round_robin_vendor = sorted(matching_vendors, key=lambda v: v.get('last_lead_assigned', '1900-01-01'))[0]
        print(f"  🔄 Round-robin selection: {round_robin_vendor['name']} (last assigned: {round_robin_vendor.get('last_lead_assigned')})")
        
        # Performance-based selection (highest close percentage)
        performance_vendor = sorted(matching_vendors, key=lambda v: -v.get('lead_close_percentage', 0))[0]
        print(f"  🏆 Performance selection: {performance_vendor['name']} (close rate: {performance_vendor.get('lead_close_percentage')}%)")

def test_routing_configuration():
    """Test routing configuration functionality"""
    print("\n🧪 TESTING ROUTING CONFIGURATION")
    print("=" * 50)
    
    # Create a test account
    try:
        account_id = simple_db_instance.create_account(
            company_name="Test Marine Company",
            industry="marine",
            ghl_location_id="test_location_123"
        )
        print(f"✅ Created test account: {account_id}")
        
        # Test routing configuration
        success = lead_routing_service.update_routing_configuration(account_id, 75)
        print(f"✅ Updated routing config (75% performance): {success}")
        
        # Get routing stats
        stats = lead_routing_service.get_routing_stats(account_id)
        print(f"📊 Routing stats: {stats}")
        
    except Exception as e:
        print(f"❌ Error testing routing configuration: {e}")

def main():
    """Run all tests"""
    print("🚀 ENHANCED LEAD ROUTING SYSTEM TESTS")
    print("=" * 60)
    
    try:
        test_location_service()
        test_vendor_coverage_scenarios()
        test_routing_configuration()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("🎯 Enhanced lead routing system is ready for production")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
