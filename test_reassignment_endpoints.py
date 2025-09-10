#!/usr/bin/env python3
'''
Test script to verify reassignment endpoints are working correctly
'''

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_api_reassignment():
    '''Test the fixed API reassignment endpoint'''
    print("\n🧪 Testing API reassignment endpoint...")
    
    # Test data - you'll need to update with a real contact_id
    test_data = {
        "contact_id": "YOUR_TEST_CONTACT_ID",
        "reason": "test_reassignment",
        "exclude_previous": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/reassignment/lead/fixed",
            json=test_data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print(f"✅ Reassignment successful: {result.get('message')}")
                print(f"   Lead ID: {result.get('lead_id')}")
                print(f"   Opportunity ID: {result.get('opportunity_id')}")
                print(f"   New Vendor: {result.get('vendor_name')}")
            else:
                print(f"⚠️ Reassignment failed: {result.get('message')}")
        else:
            print(f"❌ API error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

def test_webhook_reassignment():
    '''Test the webhook reassignment endpoint'''
    print("\n🧪 Testing webhook reassignment endpoint...")
    
    # Test webhook payload
    test_payload = {
        "contact_id": "YOUR_TEST_CONTACT_ID",
        "opportunity_id": None,  # Will create if needed
        "reason": "webhook_test"
    }
    
    headers = {
        "X-Webhook-API-Key": "YOUR_WEBHOOK_API_KEY",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/webhooks/ghl/reassign-lead",
            json=test_payload,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Webhook processed: {result.get('status')}")
            print(f"   Message: {result.get('message')}")
        else:
            print(f"❌ Webhook error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

def test_history():
    '''Test reassignment history endpoint'''
    print("\n🧪 Testing reassignment history...")
    
    contact_id = "YOUR_TEST_CONTACT_ID"
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/reassignment/history/{contact_id}"
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ History retrieved successfully")
            print(f"   Lead ID: {result.get('lead_id')}")
            print(f"   Original Source: {result.get('original_source')}")
            print(f"   Reassignment Count: {result.get('reassignment_count')}")
        else:
            print(f"❌ History error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("REASSIGNMENT ENDPOINT TESTS")
    print("=" * 60)
    print("\n⚠️  Update the test contact IDs before running!")
    print("⚠️  Make sure the application is running on localhost:8000")
    
    # Uncomment to run tests
    # test_api_reassignment()
    # test_webhook_reassignment() 
    # test_history()
    
    print("\n" + "=" * 60)
