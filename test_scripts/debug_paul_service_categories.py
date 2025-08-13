#!/usr/bin/env python3
"""
Debug Paul's service categories processing
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

def debug_paul_service_categories():
    print("=== PAUL SERVICE CATEGORIES DEBUG ===")
    
    try:
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
        
        # Extract service category field exactly like the sync function does
        service_categories = None
        services_offered = None
        service_zip_codes = None
        
        for field in custom_fields:
            field_id = field.get('id', '')
            field_value = field.get('value', '') or field.get('fieldValue', '')
            
            if field_id == 'O84LyhN1QjZ8Zz5mteCM':  # Service Category (CORRECT FIELD!)
                service_categories = field_value
                print(f"🎯 FOUND SERVICE CATEGORIES:")
                print(f"   Raw value: {repr(service_categories)}")
                print(f"   Type: {type(service_categories)}")
            elif field_id == 'pAq9WBsIuFUAZuwz3YY4':  # Services Offered
                services_offered = field_value
                print(f"📝 FOUND SERVICES OFFERED:")
                print(f"   Raw value: {repr(services_offered)}")
                print(f"   Type: {type(services_offered)}")
            elif field_id == 'yDcN0FmwI3xacyxAuTWs':  # Service Zip Codes
                service_zip_codes = field_value
                print(f"📍 FOUND SERVICE ZIP CODES:")
                print(f"   Raw value: {repr(service_zip_codes)}")
                print(f"   Type: {type(service_zip_codes)}")
        
        print(f"\n🔍 EXTRACTED VALUES:")
        print(f"   service_categories: {repr(service_categories)}")
        print(f"   services_offered: {repr(services_offered)}")
        print(f"   service_zip_codes: {repr(service_zip_codes)}")
        
        # Now process them exactly like the sync function does
        print(f"\n🔄 PROCESSING SERVICE CATEGORIES:")
        service_categories_json = json.dumps([])
        if service_categories:
            print(f"   service_categories is truthy")
            try:
                # If it's already a list/array from GHL, use it directly
                if isinstance(service_categories, list):
                    service_categories_json = json.dumps(service_categories)
                    print(f"   📋 Got service_categories as array: {service_categories}")
                # If it's a string that looks like JSON array, parse it
                elif isinstance(service_categories, str) and service_categories.startswith('[') and service_categories.endswith(']'):
                    categories_list = json.loads(service_categories)
                    service_categories_json = json.dumps(categories_list)
                    print(f"   📋 Parsed service_categories from JSON string: {categories_list}")
                # If it's a comma-separated string, split it
                elif isinstance(service_categories, str):
                    categories_list = [cat.strip() for cat in service_categories.split(',') if cat.strip()]
                    service_categories_json = json.dumps(categories_list)
                    print(f"   📋 Split service_categories from comma string: {categories_list}")
                else:
                    print(f"   📋 Unknown service_categories type: {type(service_categories)} = {service_categories}")
                    service_categories_json = json.dumps([str(service_categories)])
            except Exception as e:
                print(f"   📋 Error processing service_categories: {e}")
                service_categories_json = json.dumps([str(service_categories)])
        else:
            print(f"   service_categories is falsy: {repr(service_categories)}")
        
        print(f"\n✅ FINAL RESULT:")
        print(f"   service_categories_json: {service_categories_json}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_paul_service_categories()