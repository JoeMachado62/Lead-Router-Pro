#!/usr/bin/env python3
"""
Test script to verify vendor submission fixes
"""

import requests
import json
import sys

def test_vendor_submission():
    """Test vendor submission with proper field mapping"""
    
    # Test payload that mimics what vendor_widget.html sends
    test_payload = {
        "firstName": "Test",
        "lastName": "Vendor",
        "email": "testvendor@example.com",
        "phone": "305-555-0123",
        "vendor_company_name": "Test Marine Services LLC",
        "coverage_type": "state",
        "coverage_states": ["FL", "GA"],  # Array of state codes
        "service_coverage_area": "FL, GA",  # Human-readable version
        "service_categories": "Boat Maintenance, Engines and Generators",  # Categories selected
        "services_provided": "Boat Detailing, Ceramic Coating, Outboard Engine Service",  # Specific services
        "years_in_business": "5",
        "special_requests__notes": "Test vendor submission with proper field mapping"
    }
    
    # API endpoint
    api_url = "http://localhost:8000/api/v1/webhooks/elementor/vendor_application"
    
    print("🚀 Testing vendor submission with proper field mapping")
    print("=" * 80)
    print("\n📋 TEST PAYLOAD:")
    print(json.dumps(test_payload, indent=2))
    print("\n" + "=" * 80)
    
    try:
        # Make the request
        response = requests.post(
            api_url,
            json=test_payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n📡 Response Status: {response.status_code}")
        
        if response.ok:
            result = response.json()
            print("\n✅ SUCCESS! Response:")
            print(json.dumps(result, indent=2))
            
            if 'contact_id' in result:
                print(f"\n🎯 GHL Contact ID: {result['contact_id']}")
                print("\n💡 Check the database with:")
                print(f"   python check_vendor_data.py {result['contact_id']}")
        else:
            print(f"\n❌ ERROR: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"\n❌ Request failed: {e}")
        print("\n💡 Make sure the FastAPI server is running:")
        print("   python main_working_final.py")

if __name__ == "__main__":
    test_vendor_submission()