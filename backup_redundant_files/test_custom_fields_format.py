#!/usr/bin/env python3
"""
Test different custom field formats for GHL API
"""

import requests
import json
from api.services.ghl_api import GoHighLevelAPI
from config import Config

DSP_GHL_LOCATION_ID = Config.GHL_LOCATION_ID
DSP_LOCATION_PIT = Config.GHL_PRIVATE_TOKEN

def test_custom_fields_array_format():
    """Test using customFields array format"""
    print("🔍 Testing Custom Fields Array Format...")
    
    ghl_api = GoHighLevelAPI(private_token=DSP_LOCATION_PIT, location_id=DSP_GHL_LOCATION_ID)
    
    # Test payload with customFields array
    test_payload = {
        "firstName": "Maria",
        "lastName": "Santos",
        "email": "maria.santos.array.test@pristineyachts.com",
        "phone": "555-456-7890",
        "source": "Detailing Specialist Application Form (DSP)",
        "tags": ["New Vendor Application", "Boat Detailing", "Maintenance Specialist", "DSP Elementor"],
        "customFields": [
            {
                "id": "JexVrg2VNhnwIX7YlyJV",  # Vendor Company Name field ID
                "value": "Pristine Yacht Services LLC"
            },
            {
                "id": "YNkqNHJvW5OblIHd8RqL",  # Years in Business field ID  
                "value": "8"
            },
            {
                "id": "pAq9WBsIuFUAZuwz3YY4",  # Services Provided field ID
                "value": "Premium yacht detailing, ceramic coating, interior cleaning"
            }
        ]
    }
    
    print(f"Payload: {json.dumps(test_payload, indent=2)}")
    
    try:
        result = ghl_api.create_contact(test_payload)
        if result and result.get('id'):
            print(f"✅ Custom fields array format successful: {result.get('id')}")
            return result.get('id')
        else:
            print(f"❌ Custom fields array format failed: {result}")
            return None
    except Exception as e:
        print(f"❌ Custom fields array format exception: {e}")
        return None

def test_direct_api_call_with_custom_fields():
    """Test direct API call with custom fields"""
    print("\n🔍 Testing Direct API Call with Custom Fields...")
    
    headers = {
        "Authorization": f"Bearer {DSP_LOCATION_PIT}",
        "Content-Type": "application/json",
        "Version": "2021-07-28"
    }
    
    # Test payload with customFields array
    test_payload = {
        "locationId": DSP_GHL_LOCATION_ID,
        "firstName": "Carlos",
        "lastName": "Rodriguez",
        "email": "carlos.direct.test@boatshinedetailing.com",
        "phone": "555-789-0123",
        "source": "Direct API Test",
        "customFields": [
            {
                "id": "JexVrg2VNhnwIX7YlyJV",  # Vendor Company Name
                "value": "BoatShine Detailing Services"
            },
            {
                "id": "YNkqNHJvW5OblIHd8RqL",  # Years in Business
                "value": "3"
            }
        ]
    }
    
    url = "https://services.leadconnectorhq.com/contacts/"
    
    try:
        response = requests.post(url, headers=headers, json=test_payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            data = response.json()
            contact_id = data.get('contact', {}).get('id')
            print(f"✅ Direct API call successful: {contact_id}")
            return contact_id
        else:
            print(f"❌ Direct API call failed with status {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Direct API call exception: {e}")
        return None

def test_update_with_custom_fields(contact_id):
    """Test updating existing contact with custom fields"""
    if not contact_id:
        print("⏭️ Skipping update test - no contact ID")
        return
        
    print(f"\n🔍 Testing Update with Custom Fields on {contact_id}...")
    
    headers = {
        "Authorization": f"Bearer {DSP_LOCATION_PIT}",
        "Content-Type": "application/json",
        "Version": "2021-07-28"
    }
    
    update_payload = {
        "customFields": [
            {
                "id": "HRqfv0HnUydNRLKWhk27",  # Primary Service Category
                "value": "Boat Maintenance"
            }
        ]
    }
    
    url = f"https://services.leadconnectorhq.com/contacts/{contact_id}"
    
    try:
        response = requests.put(url, headers=headers, json=update_payload, timeout=10)
        print(f"Update Status Code: {response.status_code}")
        print(f"Update Response: {response.text}")
        
        if response.status_code == 200:
            print(f"✅ Update with custom fields successful")
        else:
            print(f"❌ Update with custom fields failed")
            
    except Exception as e:
        print(f"❌ Update exception: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("  CUSTOM FIELDS FORMAT TEST")
    print("=" * 60)
    
    # Test 1: Array format via our API wrapper
    contact_id1 = test_custom_fields_array_format()
    
    # Test 2: Direct API call
    contact_id2 = test_direct_api_call_with_custom_fields()
    
    # Test 3: Update existing contact
    test_update_with_custom_fields(contact_id1 or contact_id2)
    
    print("\n" + "=" * 60)
    print("  TEST COMPLETED")
    print("=" * 60)
