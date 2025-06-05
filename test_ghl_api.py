#!/usr/bin/env python3
"""
Test script to verify GHL API connection and troubleshoot the 502 error
"""

import requests
import json
from api.services.ghl_api import GoHighLevelAPI

# Test credentials from config
from config import Config

DSP_GHL_LOCATION_ID = Config.GHL_LOCATION_ID
DSP_GHL_API_KEY = Config.GHL_API_KEY
DSP_LOCATION_PIT = Config.GHL_PRIVATE_TOKEN

def test_ghl_api_connection():
    """Test basic GHL API connection"""
    print("🔍 Testing GHL API Connection...")
    print(f"Location ID: {DSP_GHL_LOCATION_ID}")
    print(f"PIT Token: {DSP_LOCATION_PIT[:20]}...")
    print("🔑 Using GHL PIT Token for authentication (confirmed working)")
    ghl_api = GoHighLevelAPI(private_token=DSP_LOCATION_PIT, location_id=DSP_GHL_LOCATION_ID)
    
    # Test 1: Search contacts (basic API test)
    print("\n--- Test 1: Search Contacts ---")
    try:
        contacts = ghl_api.search_contacts(limit=1)
        if contacts:
            print(f"✅ Successfully retrieved {len(contacts)} contact(s)")
            print(f"Sample contact: {contacts[0].get('id', 'No ID')} - {contacts[0].get('email', 'No email')}")
        else:
            print("⚠️ No contacts found, but API call succeeded")
    except Exception as e:
        print(f"❌ Search contacts failed: {e}")
    
    # Test 2: Get custom fields
    print("\n--- Test 2: Get Custom Fields ---")
    try:
        custom_fields = ghl_api.get_custom_fields()
        if custom_fields:
            print(f"✅ Successfully retrieved {len(custom_fields)} custom field(s)")
            for field in custom_fields[:3]:  # Show first 3
                print(f"  - {field.get('name', 'No name')}: {field.get('fieldKey', 'No key')}")
        else:
            print("⚠️ No custom fields found")
    except Exception as e:
        print(f"❌ Get custom fields failed: {e}")
    
    # Test 3: Try to create a test contact
    print("\n--- Test 3: Create Test Contact ---")
    test_contact_data = {
        "firstName": "Test",
        "lastName": "Contact",
        "email": "test.contact.ghl.api@example.com",
        "phone": "555-123-4567",
        "source": "API Test"
    }
    
    try:
        # First check if test contact already exists
        existing_contacts = ghl_api.search_contacts(query=test_contact_data["email"])
        if existing_contacts:
            for contact in existing_contacts:
                if contact.get('email', '').lower() == test_contact_data["email"].lower():
                    print(f"⚠️ Test contact already exists: {contact.get('id')}")
                    return
        
        # Try to create the contact
        result = ghl_api.create_contact(test_contact_data)
        if result and result.get('id'):
            print(f"✅ Successfully created test contact: {result.get('id')}")
            print(f"Contact details: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Failed to create test contact. Result: {result}")
            
    except Exception as e:
        print(f"❌ Create test contact failed: {e}")

def test_direct_api_call():
    """Test direct API call to GHL to see raw response"""
    print("\n🔍 Testing Direct GHL API Call...")
    
    headers = {
        "Authorization": f"Bearer {DSP_LOCATION_PIT}",
        "Content-Type": "application/json",
        "Version": "2021-07-28"
    }
    
    # Test the contacts endpoint directly
    url = "https://services.leadconnectorhq.com/contacts/"
    params = {
        "locationId": DSP_GHL_LOCATION_ID,
        "limit": 1
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            print("✅ Direct API call successful")
        else:
            print(f"❌ Direct API call failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Direct API call exception: {e}")

def test_contact_creation_payload():
    """Test the exact payload that's failing"""
    print("\n🔍 Testing Vendor Application Payload...")
    
    # This matches the new format that webhook routes now send
    test_vendor_payload = {
        "firstName": "Maria",
        "lastName": "Santos", 
        "email": "maria.santos.test@pristineyachts.com",  # Different email to avoid conflicts
        "phone": "555-456-7890",
        "source": "Detailing Specialist Application Form (DSP)",
        "tags": ["New Vendor Application", "Boat Detailing", "Maintenance Specialist", "DSP Elementor"],
        # Custom fields now use short keys (without contact. prefix)
        "vendor_company_name": "Pristine Yacht Services LLC",
        "years_in_business": "8",
        "services_provided": "Premium yacht detailing, ceramic coating, interior cleaning, waxing, polishing",
        "primary_service_category": "Boat Maintenance",
        "service_zip_codes": "33139, 33154, 33109, 33140, 33141"
    }
    
    # Use PIT token (confirmed working)
    ghl_api = GoHighLevelAPI(private_token=DSP_LOCATION_PIT, location_id=DSP_GHL_LOCATION_ID)
    
    try:
        result = ghl_api.create_contact(test_vendor_payload)
        if result and result.get('id'):
            print(f"✅ Vendor payload test successful: {result.get('id')}")
            print(f"Contact details: {result}")
        else:
            print(f"❌ Vendor payload test failed: {result}")
    except Exception as e:
        print(f"❌ Vendor payload test exception: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("  GHL API CONNECTION TEST")
    print("=" * 60)
    
    test_ghl_api_connection()
    test_direct_api_call()
    test_contact_creation_payload()
    
    print("\n" + "=" * 60)
    print("  TEST COMPLETED")
    print("=" * 60)
