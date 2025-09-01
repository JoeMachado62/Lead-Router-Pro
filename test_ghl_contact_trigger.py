#!/usr/bin/env python3
"""
Test script for the GHL contact trigger endpoint
Tests the /api/v1/webhooks/ghl/process-new-contact endpoint
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"  # Change to your server URL
ENDPOINT = f"{BASE_URL}/api/v1/webhooks/ghl/process-new-contact"

def test_minimal_payload():
    """Test with minimal required payload (just contact ID)"""
    print("\n" + "="*60)
    print("TEST 1: Minimal Payload (Contact ID only)")
    print("="*60)
    
    payload = {
        "contactId": "test_contact_001",
        "type": "ContactCreate"
    }
    
    print(f"Sending payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(ENDPOINT, json=payload, timeout=30)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200 or response.status_code == 404  # 404 if contact not found in GHL
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_full_payload():
    """Test with full GHL webhook payload"""
    print("\n" + "="*60)
    print("TEST 2: Full GHL Webhook Payload")
    print("="*60)
    
    payload = {
        "type": "ContactCreate",
        "locationId": "C2QujeCh8ZnC7al2InWR",
        "contactId": "test_contact_002",
        "contact": {
            "id": "test_contact_002",
            "firstName": "Test",
            "lastName": "User",
            "email": "test@example.com",
            "phone": "+13054567890",
            "customFields": [
                {
                    "id": "service_field_1",
                    "name": "Service Category",
                    "value": "Boat Maintenance"
                },
                {
                    "id": "y3Xo7qsFEQumoFugTeCq",
                    "name": "ZIP Code",
                    "value": "33139"
                },
                {
                    "id": "specific_service",
                    "name": "Specific Service Requested",
                    "value": "Bottom Cleaning"
                }
            ],
            "postalCode": "33139",
            "tags": ["New Lead", "Test"]
        }
    }
    
    print(f"Sending payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(ENDPOINT, json=payload, timeout=30)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200 or response.status_code == 404
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_existing_contact():
    """Test with an existing GHL contact ID"""
    print("\n" + "="*60)
    print("TEST 3: Existing GHL Contact")
    print("="*60)
    
    # Use a real contact ID from your GHL system
    # You can get this from your GHL dashboard or previous webhook logs
    existing_contact_id = input("Enter an existing GHL contact ID (or press Enter to skip): ").strip()
    
    if not existing_contact_id:
        print("Skipping test - no contact ID provided")
        return True
    
    payload = {
        "type": "ContactCreate",
        "contactId": existing_contact_id,
        "locationId": "C2QujeCh8ZnC7al2InWR"
    }
    
    print(f"Sending payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(ENDPOINT, json=payload, timeout=30)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_duplicate_submission():
    """Test idempotent behavior with duplicate submission"""
    print("\n" + "="*60)
    print("TEST 4: Duplicate Submission (Idempotency Test)")
    print("="*60)
    
    payload = {
        "contactId": "test_duplicate_001",
        "type": "ContactCreate"
    }
    
    print("First submission:")
    try:
        response1 = requests.post(ENDPOINT, json=payload, timeout=30)
        print(f"Status Code: {response1.status_code}")
        print(f"Response: {json.dumps(response1.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    print("\nSecond submission (should detect duplicate):")
    try:
        response2 = requests.post(ENDPOINT, json=payload, timeout=30)
        print(f"Status Code: {response2.status_code}")
        response_json = response2.json()
        print(f"Response: {json.dumps(response_json, indent=2)}")
        
        # Check if duplicate was detected
        if response_json.get("duplicate") == True:
            print("✅ Duplicate detection working correctly!")
            return True
        else:
            print("⚠️ Duplicate not detected as expected")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_missing_contact_id():
    """Test error handling when contact ID is missing"""
    print("\n" + "="*60)
    print("TEST 5: Missing Contact ID (Error Handling)")
    print("="*60)
    
    payload = {
        "type": "ContactCreate",
        "locationId": "C2QujeCh8ZnC7al2InWR"
        # contactId is missing
    }
    
    print(f"Sending payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(ENDPOINT, json=payload, timeout=30)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Should return 400 Bad Request
        if response.status_code == 400:
            print("✅ Error handling working correctly!")
            return True
        else:
            print("⚠️ Expected 400 status code for missing contact ID")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("GHL CONTACT TRIGGER ENDPOINT TEST SUITE")
    print(f"Endpoint: {ENDPOINT}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("="*60)
    
    tests = [
        ("Minimal Payload", test_minimal_payload),
        ("Full Payload", test_full_payload),
        ("Existing Contact", test_existing_contact),
        ("Duplicate Submission", test_duplicate_submission),
        ("Missing Contact ID", test_missing_contact_id)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())