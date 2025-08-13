#!/usr/bin/env python3
"""
Test the vendor widget submission with different coverage types
"""

import requests
import json
import sys

def test_vendor_widget_submissions():
    """Test various vendor submission scenarios that the widget might send"""
    
    api_url = "http://localhost:8000/api/v1/webhooks/elementor/vendor_application"
    
    # Test Case 1: State Coverage
    print("=" * 80)
    print("TEST 1: STATE COVERAGE VENDOR")
    print("=" * 80)
    
    state_vendor = {
        "firstName": "John",
        "lastName": "Smith",
        "email": "john.smith@marinepro.com",
        "phone": "305-555-0001",
        "vendor_company_name": "Marine Pro Services FL",
        "coverage_type": "state",
        "coverage_states": ["FL", "GA", "SC"],  # Array format from widget
        "service_coverage_area": "FL, GA, SC",  # Human readable
        "service_categories": "Boat Maintenance, Engines and Generators",
        "services_provided": "Boat Detailing, Ceramic Coating, Outboard Engine Service",
        "years_in_business": "8",
        "special_requests__notes": "Specializing in luxury yacht maintenance"
    }
    
    print("\n📤 Payload:")
    print(json.dumps(state_vendor, indent=2))
    
    try:
        response = requests.post(api_url, json=state_vendor)
        print(f"\n📡 Response Status: {response.status_code}")
        if response.ok:
            print("✅ SUCCESS!")
            result = response.json()
            if 'contact_id' in result:
                print(f"🎯 GHL Contact ID: {result['contact_id']}")
        else:
            print(f"❌ ERROR: {response.text}")
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    # Test Case 2: County Coverage
    print("\n" + "=" * 80)
    print("TEST 2: COUNTY COVERAGE VENDOR")
    print("=" * 80)
    
    county_vendor = {
        "firstName": "Maria",
        "lastName": "Garcia",
        "email": "maria@southfloridamarine.com",
        "phone": "786-555-0002",
        "vendor_company_name": "South Florida Marine Services",
        "coverage_type": "county",
        "coverage_counties": ["Miami-Dade, FL", "Broward, FL", "Monroe, FL"],  # Array format
        "service_coverage_area": "Miami-Dade, FL; Broward, FL; Monroe, FL",  # Human readable
        "service_categories": "Boat and Yacht Repair, Marine Systems",
        "services_provided": "Fiberglass Repair, Yacht AC Service, Marine Systems Install and Sales",
        "years_in_business": "12",
        "special_requests__notes": "24/7 emergency service available"
    }
    
    print("\n📤 Payload:")
    print(json.dumps(county_vendor, indent=2))
    
    try:
        response = requests.post(api_url, json=county_vendor)
        print(f"\n📡 Response Status: {response.status_code}")
        if response.ok:
            print("✅ SUCCESS!")
            result = response.json()
            if 'contact_id' in result:
                print(f"🎯 GHL Contact ID: {result['contact_id']}")
        else:
            print(f"❌ ERROR: {response.text}")
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    # Test Case 3: ZIP Code Coverage
    print("\n" + "=" * 80)
    print("TEST 3: ZIP CODE COVERAGE VENDOR")
    print("=" * 80)
    
    zip_vendor = {
        "firstName": "Robert",
        "lastName": "Johnson",
        "email": "robert@keysmarineservice.com",
        "phone": "305-555-0003",
        "vendor_company_name": "Keys Marine Service",
        "coverage_type": "zip",
        "service_zip_codes": "33037, 33036, 33050, 33040",  # String format
        "service_coverage_area": "33037, 33036, 33050, 33040",  # Human readable
        "service_categories": "Boat Towing, Boat Maintenance",
        "services_provided": "Get Emergency Tow, Boat Bottom Cleaning, Barnacle Cleaning",
        "years_in_business": "5",
        "special_requests__notes": "Specialized in Florida Keys area"
    }
    
    print("\n📤 Payload:")
    print(json.dumps(zip_vendor, indent=2))
    
    try:
        response = requests.post(api_url, json=zip_vendor)
        print(f"\n📡 Response Status: {response.status_code}")
        if response.ok:
            print("✅ SUCCESS!")
            result = response.json()
            if 'contact_id' in result:
                print(f"🎯 GHL Contact ID: {result['contact_id']}")
        else:
            print(f"❌ ERROR: {response.text}")
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    # Test Case 4: National Coverage
    print("\n" + "=" * 80)
    print("TEST 4: NATIONAL COVERAGE VENDOR")
    print("=" * 80)
    
    national_vendor = {
        "firstName": "Sarah",
        "lastName": "Thompson",
        "email": "sarah@nationwideyacht.com",
        "phone": "800-555-0004",
        "vendor_company_name": "Nationwide Yacht Transport",
        "coverage_type": "national",
        "service_coverage_area": "All",  # Human readable
        "service_categories": "Boat Hauling and Yacht Delivery",
        "services_provided": "Yacht Delivery, Boat Hauling and Transport",
        "years_in_business": "15",
        "special_requests__notes": "Licensed and insured for nationwide transport"
    }
    
    print("\n📤 Payload:")
    print(json.dumps(national_vendor, indent=2))
    
    try:
        response = requests.post(api_url, json=national_vendor)
        print(f"\n📡 Response Status: {response.status_code}")
        if response.ok:
            print("✅ SUCCESS!")
            result = response.json()
            if 'contact_id' in result:
                print(f"🎯 GHL Contact ID: {result['contact_id']}")
        else:
            print(f"❌ ERROR: {response.text}")
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    print("\n" + "=" * 80)
    print("🏁 ALL TESTS COMPLETE")
    print("=" * 80)
    print("\n💡 To check vendor data in database, use:")
    print("   python check_vendor_data.py <GHL_CONTACT_ID>")

if __name__ == "__main__":
    print("🚀 Testing vendor widget submissions")
    print("\n⚠️  Make sure the FastAPI server is running:")
    print("   python main_working_final.py\n")
    
    test_vendor_widget_submissions()