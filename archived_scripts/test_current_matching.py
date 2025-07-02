#!/usr/bin/env python3
"""
Test current vendor matching to debug the dashboard issue
"""

import sys
import os
import json

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.simple_connection import db as simple_db_instance
from config import AppConfig

def test_matching_debug():
    """Debug why vendor matching is failing"""
    print("🔍 DEBUGGING VENDOR MATCHING")
    print("=" * 50)
    
    try:
        # Get account with environment variable
        os.environ['GHL_LOCATION_ID'] = 'ilmrtA1Vk6rvcy4BswKg'
        
        account = simple_db_instance.get_account_by_ghl_location_id('ilmrtA1Vk6rvcy4BswKg')
        if not account:
            print("❌ No account found!")
            return
        
        account_id = account['id']
        print(f"✅ Found account: {account['company_name']} ({account_id})")
        
        # Get vendors
        vendors = simple_db_instance.get_vendors(account_id=account_id)
        print(f"📊 Found {len(vendors)} vendors")
        
        for vendor in vendors:
            print(f"\n🔧 Vendor: {vendor['name']}")
            print(f"   Status: {vendor.get('status')}")
            print(f"   Taking work: {vendor.get('taking_new_work')}")
            print(f"   Coverage type: {vendor.get('service_coverage_type')}")
            
            services = vendor.get('services_provided', [])
            if isinstance(services, str):
                try:
                    services = json.loads(services)
                except:
                    services = []
            print(f"   Services: {services}")
            
            counties = vendor.get('service_counties', [])
            if isinstance(counties, str):
                try:
                    counties = json.loads(counties)
                except:
                    counties = []
            print(f"   Counties: {counties}")
        
        # Test the matching logic manually
        print(f"\n🧪 TESTING MATCHING FOR ZIP 33024, SERVICE: Engines and Generators")
        
        # Since location service is broken, let's assume 33024 is in Broward County, FL
        test_zip = "33024"
        test_service = "Engines and Generators"
        target_county = "Broward"
        target_state = "FL"
        
        print(f"   Assuming {test_zip} → {target_county}, {target_state}")
        
        matching_vendors = []
        for vendor in vendors:
            # Check if vendor is active and taking work
            if vendor.get("status") != "active" or not vendor.get("taking_new_work", False):
                print(f"   ❌ {vendor['name']}: Not active or not taking work")
                continue
            
            # Check service matching
            services = vendor.get('services_provided', [])
            if isinstance(services, str):
                try:
                    services = json.loads(services)
                except:
                    services = []
            
            service_match = False
            for service in services:
                if test_service.lower() in service.lower() or service.lower() in test_service.lower():
                    service_match = True
                    break
            
            if not service_match:
                print(f"   ❌ {vendor['name']}: Service mismatch")
                continue
            
            # Check county coverage
            coverage_type = vendor.get('service_coverage_type', 'zip')
            if coverage_type == 'county':
                counties = vendor.get('service_counties', [])
                if isinstance(counties, str):
                    try:
                        counties = json.loads(counties)
                    except:
                        counties = []
                
                county_match = False
                for county_area in counties:
                    if target_county.lower() in county_area.lower() and target_state.lower() in county_area.lower():
                        county_match = True
                        break
                
                if county_match:
                    print(f"   ✅ {vendor['name']}: MATCHES!")
                    matching_vendors.append(vendor)
                else:
                    print(f"   ❌ {vendor['name']}: County mismatch")
            else:
                print(f"   ❌ {vendor['name']}: Wrong coverage type: {coverage_type}")
        
        print(f"\n🎯 RESULT: Found {len(matching_vendors)} matching vendors")
        for vendor in matching_vendors:
            print(f"   - {vendor['name']}")
        
        return len(matching_vendors) > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_matching_debug()
