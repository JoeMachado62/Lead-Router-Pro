#!/usr/bin/env python3
"""
Test script for webhook payload parsing
Tests both JSON and form-encoded data handling
"""

import asyncio
import requests
import json
from urllib.parse import urlencode

BASE_URL = "http://localhost:8000"

async def test_webhook_parsing():
    """Test the robust webhook payload parsing"""
    
    print("🧪 Testing Webhook Payload Parsing")
    print("=" * 50)
    
    # Test data
    test_data = {
        "firstName": "John",
        "lastName": "Smith",
        "email": "john.test@example.com",
        "phone": "555-123-4567",
        "specific_service_needed": "Ceramic coating test",
        "zip_code_of_service": "33101"
    }
    
    webhook_url = f"{BASE_URL}/api/v1/webhooks/elementor/ceramic_coating"
    
    # Test 1: JSON payload (preferred format)
    print("\n1. Testing JSON payload...")
    try:
        response = requests.post(
            webhook_url,
            headers={"Content-Type": "application/json"},
            json=test_data,
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ JSON test successful!")
            print(f"   Contact ID: {result.get('contact_id', 'N/A')}")
            print(f"   Action: {result.get('action', 'N/A')}")
        else:
            print(f"   ❌ JSON test failed: {response.text}")
            
    except Exception as e:
        print(f"   ❌ JSON test error: {e}")
    
    # Test 2: Form-encoded payload (fallback format)
    print("\n2. Testing form-encoded payload...")
    try:
        # Change email to avoid duplicate
        test_data["email"] = "john.form@example.com"
        
        response = requests.post(
            webhook_url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=urlencode(test_data),
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Form-encoded test successful!")
            print(f"   Contact ID: {result.get('contact_id', 'N/A')}")
            print(f"   Action: {result.get('action', 'N/A')}")
        else:
            print(f"   ❌ Form-encoded test failed: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Form-encoded test error: {e}")
    
    # Test 3: Auto-detection (no content-type header)
    print("\n3. Testing auto-detection...")
    try:
        # Change email to avoid duplicate
        test_data["email"] = "john.auto@example.com"
        
        response = requests.post(
            webhook_url,
            # No Content-Type header - should auto-detect
            json=test_data,
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Auto-detection test successful!")
            print(f"   Contact ID: {result.get('contact_id', 'N/A')}")
            print(f"   Action: {result.get('action', 'N/A')}")
        else:
            print(f"   ❌ Auto-detection test failed: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Auto-detection test error: {e}")
    
    # Test 4: Different form types
    print("\n4. Testing different form types...")
    
    form_tests = [
        {
            "url": f"{BASE_URL}/api/v1/webhooks/elementor/emergency_tow",
            "name": "Emergency Towing",
            "data": {
                "firstName": "Sarah",
                "lastName": "Emergency",
                "email": "sarah.emergency@example.com",
                "phone": "555-911-1234",
                "vessel_location__slip": "Coordinates 25.7617° N, 80.1918° W",
                "special_requests__notes": "Engine failure - need immediate help!"
            }
        },
        {
            "url": f"{BASE_URL}/api/v1/webhooks/elementor/vendor_application",
            "name": "Vendor Application",
            "data": {
                "firstName": "Mike",
                "lastName": "Vendor",
                "email": "mike.vendor@example.com",
                "phone": "555-456-7890",
                "vendor_company_name": "Test Marine Services",
                "services_provided": "Engine repair, electrical work",
                "service_zip_codes": "33101,33139"
            }
        }
    ]
    
    for test in form_tests:
        print(f"\n   Testing {test['name']}...")
        try:
            response = requests.post(
                test["url"],
                headers={"Content-Type": "application/json"},
                json=test["data"],
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ {test['name']} successful!")
                print(f"      Form Type: {result.get('form_type', 'N/A')}")
                print(f"      Service Category: {result.get('service_category', 'N/A')}")
            else:
                print(f"   ❌ {test['name']} failed: {response.text}")
                
        except Exception as e:
            print(f"   ❌ {test['name']} error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Webhook payload parsing tests completed!")
    print("=" * 50)

def main():
    """Main test function"""
    print("Make sure the server is running: python main_working_final.py")
    print("Press Enter to start tests...")
    input()
    
    asyncio.run(test_webhook_parsing())

if __name__ == "__main__":
    main()
