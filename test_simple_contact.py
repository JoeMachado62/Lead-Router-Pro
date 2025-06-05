#!/usr/bin/env python3
"""
Test script to create a simple contact without custom fields
"""

import requests
import json
from api.services.ghl_api import GoHighLevelAPI
from config import Config

DSP_GHL_LOCATION_ID = Config.GHL_LOCATION_ID
DSP_LOCATION_PIT = Config.GHL_PRIVATE_TOKEN

def test_simple_contact_creation():
    """Test creating a contact with only standard fields"""
    print("🔍 Testing Simple Contact Creation...")
    
    # Use PIT token (confirmed working)
    ghl_api = GoHighLevelAPI(private_token=DSP_LOCATION_PIT, location_id=DSP_GHL_LOCATION_ID)
    
    # Test with only standard fields
    simple_payload = {
        "firstName": "Test",
        "lastName": "Vendor",
        "email": "test.vendor.simple@example.com",
        "phone": "555-999-8888",
        "source": "API Test - Simple",
        "tags": ["Test", "Simple Contact"]
    }
    
    print(f"Payload: {json.dumps(simple_payload, indent=2)}")
    
    try:
        result = ghl_api.create_contact(simple_payload)
        if result and result.get('id'):
            print(f"✅ Simple contact creation successful: {result.get('id')}")
            return result.get('id')
        else:
            print(f"❌ Simple contact creation failed: {result}")
            return None
    except Exception as e:
        print(f"❌ Simple contact creation exception: {e}")
        return None

def test_custom_field_lookup():
    """Check what custom fields actually exist"""
    print("\n🔍 Checking Custom Fields...")
    
    ghl_api = GoHighLevelAPI(private_token=DSP_LOCATION_PIT, location_id=DSP_GHL_LOCATION_ID)
    
    try:
        custom_fields = ghl_api.get_custom_fields()
        print(f"Found {len(custom_fields)} custom fields")
        
        # Look for vendor-related fields
        vendor_fields = []
        for field in custom_fields:
            field_name = field.get('name', '')
            field_key = field.get('fieldKey', '')
            if any(term in field_name.lower() for term in ['vendor', 'company', 'service', 'business']):
                vendor_fields.append({
                    'name': field_name,
                    'fieldKey': field_key,
                    'id': field.get('id'),
                    'dataType': field.get('dataType')
                })
        
        print(f"\nFound {len(vendor_fields)} vendor-related fields:")
        for field in vendor_fields:
            print(f"  - {field['name']}: {field['fieldKey']} ({field['dataType']})")
            
        return vendor_fields
        
    except Exception as e:
        print(f"❌ Custom field lookup failed: {e}")
        return []

def test_contact_with_one_custom_field(contact_id, vendor_fields):
    """Test updating a contact with one custom field at a time"""
    if not contact_id or not vendor_fields:
        print("⏭️ Skipping custom field test - no contact or fields available")
        return
    
    print(f"\n🔍 Testing Custom Field Updates on Contact {contact_id}...")
    
    ghl_api = GoHighLevelAPI(private_token=DSP_LOCATION_PIT, location_id=DSP_GHL_LOCATION_ID)
    
    # Try the vendor company name field
    for field in vendor_fields:
        if 'company' in field['name'].lower():
            field_key = field['fieldKey'].split('contact.')[-1]  # Remove contact. prefix
            
            print(f"Testing field: {field['name']} -> {field_key}")
            
            update_payload = {
                field_key: "Test Company LLC"
            }
            
            try:
                success = ghl_api.update_contact(contact_id, update_payload)
                if success:
                    print(f"✅ Successfully updated {field['name']}")
                else:
                    print(f"❌ Failed to update {field['name']}")
            except Exception as e:
                print(f"❌ Exception updating {field['name']}: {e}")
            
            break  # Only test one field

if __name__ == "__main__":
    print("=" * 60)
    print("  SIMPLE CONTACT CREATION TEST")
    print("=" * 60)
    
    # Step 1: Create simple contact
    contact_id = test_simple_contact_creation()
    
    # Step 2: Check what custom fields exist
    vendor_fields = test_custom_field_lookup()
    
    # Step 3: Test updating with custom fields
    test_contact_with_one_custom_field(contact_id, vendor_fields)
    
    print("\n" + "=" * 60)
    print("  TEST COMPLETED")
    print("=" * 60)
