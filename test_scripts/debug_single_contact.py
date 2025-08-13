#!/usr/bin/env python3
"""
Debug single contact to see service categories field
"""

import sys
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.getcwd())

from config import AppConfig
from api.services.ghl_api import GoHighLevelAPI

def debug_single_contact():
    print("=== SINGLE CONTACT DEBUG ===")
    
    try:
        # Check config values first
        print(f"GHL_PRIVATE_TOKEN: {AppConfig.GHL_PRIVATE_TOKEN[:20]}..." if AppConfig.GHL_PRIVATE_TOKEN else "GHL_PRIVATE_TOKEN: None")
        print(f"GHL_LOCATION_ID: {AppConfig.GHL_LOCATION_ID}")
        print(f"GHL_LOCATION_API: {AppConfig.GHL_LOCATION_API[:20]}..." if AppConfig.GHL_LOCATION_API else "GHL_LOCATION_API: None")
        
        # Initialize GHL API like the working admin function
        ghl_api = GoHighLevelAPI(
            private_token=AppConfig.GHL_PRIVATE_TOKEN,
            location_id=AppConfig.GHL_LOCATION_ID,
            agency_api_key=AppConfig.GHL_AGENCY_API_KEY,
            company_id=AppConfig.GHL_COMPANY_ID
        )
        
        # Get Paul Minnucci contact
        contact_id = 'BaJq7TdXnIcUSBES3POL'
        print(f"Getting contact: {contact_id}")
        
        contact = ghl_api.get_contact_by_id(contact_id)
        if not contact:
            print("❌ No contact found")
            return
        
        print(f"✅ Contact found: {contact.get('firstName')} {contact.get('lastName')} - {contact.get('email')}")
        
        custom_fields = contact.get('customFields', [])
        print(f"Total custom fields: {len(custom_fields)}")
        
        # Look for service categories field specifically
        service_categories_found = False
        for field in custom_fields:
            field_id = field.get('id', '')
            field_value = field.get('value', '') or field.get('fieldValue', '')
            
            if field_id == 'O84LyhN1QjZ8Zz5mteCM':  # Service Category (CORRECT FIELD!)
                service_categories_found = True
                print(f"🎯 SERVICE CATEGORIES FIELD FOUND:")
                print(f"   Field ID: {field_id}")
                print(f"   Value Type: {type(field_value)}")
                print(f"   Value: {repr(field_value)}")
                print(f"   Full Field Structure: {json.dumps(field, indent=2)}")
                break
        
        if not service_categories_found:
            print("❌ Service Categories field (O84LyhN1QjZ8Zz5mteCM) NOT FOUND")
            print("Available field IDs:")
            for field in custom_fields[:10]:
                field_id = field.get('id', '')
                field_value = field.get('value', '') or field.get('fieldValue', '')
                print(f"   - {field_id}: {str(field_value)[:30]}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_single_contact()