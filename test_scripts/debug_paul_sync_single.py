#!/usr/bin/env python3
"""
Debug Paul's sync processing in isolation
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
from database.simple_connection import db as simple_db_instance

async def debug_paul_sync():
    print("=== PAUL SYNC DEBUG ===")
    
    try:
        # Initialize GHL API like the admin function
        ghl_api = GoHighLevelAPI(
            private_token=AppConfig.GHL_PRIVATE_TOKEN,
            location_id=AppConfig.GHL_LOCATION_ID,
            agency_api_key=AppConfig.GHL_AGENCY_API_KEY,
            company_id=AppConfig.GHL_COMPANY_ID
        )
        
        # Get account (same as admin function)
        account_record = simple_db_instance.get_account_by_ghl_location_id(AppConfig.GHL_LOCATION_ID)
        if not account_record:
            print("❌ No account found")
            return
        
        account_id = account_record["id"]
        print(f"✅ Account ID: {account_id}")
        
        # Get Paul Minnucci contact
        contact_id = 'BaJq7TdXnIcUSBES3POL'
        print(f"Getting contact: {contact_id}")
        
        contact = ghl_api.get_contact_by_id(contact_id)
        if not contact:
            print("❌ No contact found")
            return
        
        print(f"✅ Contact found: {contact.get('firstName')} {contact.get('lastName')} - {contact.get('email')}")
        
        # Extract fields exactly like admin function
        custom_fields = contact.get('customFields', [])
        
        ghl_user_id = None
        vendor_company_name = None
        service_categories = None
        services_offered = None
        service_zip_codes = None
        
        for field in custom_fields:
            field_id = field.get('id', '')
            field_value = field.get('value', '') or field.get('fieldValue', '')
            
            if field_id == 'HXVNT4y8OynNokWAfO2D':  # GHL User ID
                ghl_user_id = field_value
            elif field_id == 'JexVrg2VNhnwIX7YlyJV':  # Vendor Company Name
                vendor_company_name = field_value
            elif field_id == 'O84LyhN1QjZ8Zz5mteCM':  # Service Category (CORRECT FIELD!)
                service_categories = field_value
            elif field_id == 'pAq9WBsIuFUAZuwz3YY4':  # Services Offered
                services_offered = field_value
            elif field_id == 'yDcN0FmwI3xacyxAuTWs':  # Service Zip Codes
                service_zip_codes = field_value
        
        print(f"\n🔍 EXTRACTED VALUES:")
        print(f"   ghl_user_id: {ghl_user_id}")
        print(f"   vendor_company_name: {vendor_company_name}")
        print(f"   service_categories: {service_categories}")
        print(f"   services_offered: {services_offered}")
        print(f"   service_zip_codes: {service_zip_codes}")
        
        # Check if this would be processed as vendor
        if ghl_user_id or vendor_company_name or service_categories:
            print(f"\n✅ WOULD BE PROCESSED AS VENDOR")
            
            # Check existing vendor
            vendor_email = contact.get('email', '')
            existing_vendor = simple_db_instance.get_vendor_by_email_and_account(vendor_email, account_id)
            
            print(f"\n🔍 VENDOR LOOKUP:")
            print(f"   vendor_email: {vendor_email}")
            print(f"   account_id: {account_id}")
            print(f"   existing_vendor found: {existing_vendor is not None}")
            
            if existing_vendor:
                print(f"   existing_vendor ID: {existing_vendor.get('id')}")
                print(f"   existing service_categories: {existing_vendor.get('service_categories')}")
                print(f"   existing services_offered: {existing_vendor.get('services_offered')}")
                
                # Process service categories like admin function
                service_categories_json = json.dumps([])
                if service_categories:
                    if isinstance(service_categories, str):
                        categories_list = [cat.strip() for cat in service_categories.split(',') if cat.strip()]
                        service_categories_json = json.dumps(categories_list)
                
                print(f"\n🔄 WOULD UPDATE WITH:")
                print(f"   service_categories_json: {service_categories_json}")
                
                # Test the actual update
                print(f"\n🧪 TESTING UPDATE...")
                import sqlite3
                conn = sqlite3.connect('smart_lead_router.db')
                cursor = conn.cursor()
                
                # Update vendor with synced data from GHL
                cursor.execute("""
                    UPDATE vendors SET 
                        service_categories = ?,
                        updated_at = datetime('now')
                    WHERE id = ?
                """, (service_categories_json, existing_vendor['id']))
                
                rows_affected = cursor.rowcount
                conn.commit()
                conn.close()
                
                print(f"   Rows affected: {rows_affected}")
                
                # Check the result
                updated_vendor = simple_db_instance.get_vendor_by_email_and_account(vendor_email, account_id)
                print(f"   Updated service_categories: {updated_vendor.get('service_categories')}")
                
            else:
                print("   Would create new vendor")
        else:
            print(f"\n❌ WOULD NOT BE PROCESSED AS VENDOR")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(debug_paul_sync())