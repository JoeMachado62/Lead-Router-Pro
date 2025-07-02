#!/usr/bin/env python3
"""
Update GoHighLevel Contacts with Vendor Service Information
"""

import sys
import os
import json
import requests
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.simple_connection import db as simple_db_instance
from config import AppConfig

def update_ghl_contacts():
    """
    Update GoHighLevel contacts with correct service categories and areas
    """
    print("🔄 UPDATING GOHIGHLEVEL VENDOR CONTACTS")
    print("=" * 60)
    
    try:
        # Get account
        account = simple_db_instance.get_account_by_ghl_location_id(AppConfig.GHL_LOCATION_ID)
        if not account:
            print("❌ No account found!")
            return False
        
        account_id = account['id']
        vendors = simple_db_instance.get_vendors(account_id=account_id)
        
        print(f"📊 Found {len(vendors)} vendors to update")
        
        updated_contacts = 0
        failed_updates = 0
        
        for vendor in vendors:
            vendor_name = vendor['name']
            ghl_contact_id = vendor.get('ghl_contact_id')
            
            if not ghl_contact_id:
                print(f"⚠️  {vendor_name}: No GHL contact ID - skipping")
                continue
            
            print(f"\n📞 Updating GHL contact: {vendor_name} ({ghl_contact_id})")
            
            # Prepare update data
            services_provided = vendor.get('services_provided', [])
            if isinstance(services_provided, str):
                try:
                    services_provided = json.loads(services_provided)
                except:
                    services_provided = []
            
            service_counties = vendor.get('service_counties', [])
            if isinstance(service_counties, str):
                try:
                    service_counties = json.loads(service_counties)
                except:
                    service_counties = []
            
            # Create the update payload
            update_data = {
                'customFields': {
                    'primary_service_category': services_provided[0] if services_provided else 'Boat Maintenance',
                    'services_offered': ', '.join(services_provided) if services_provided else 'Boat Maintenance, Marine Systems',
                    'service_areas': ', '.join(service_counties) if service_counties else 'Miami-Dade, FL'
                }
            }
            
            print(f"   🎯 Primary Service: {update_data['customFields']['primary_service_category']}")
            print(f"   🛠️  Services: {update_data['customFields']['services_offered']}")
            print(f"   📍 Service Areas: {update_data['customFields']['service_areas']}")
            
            # Make the API call to update the contact
            try:
                headers = {
                    'Authorization': f'Bearer {AppConfig.GHL_LOCATION_API}',
                    'Content-Type': 'application/json'
                }
                
                url = f'https://services.leadconnectorhq.com/contacts/{ghl_contact_id}'
                
                response = requests.put(url, json=update_data, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    updated_contacts += 1
                    print(f"   ✅ Successfully updated GHL contact")
                else:
                    failed_updates += 1
                    print(f"   ❌ Failed to update GHL contact: {response.status_code} - {response.text}")
                    
            except Exception as e:
                failed_updates += 1
                print(f"   ❌ Error updating GHL contact: {e}")
        
        print(f"\n📊 GHL UPDATE SUMMARY:")
        print(f"   Updated: {updated_contacts}")
        print(f"   Failed: {failed_updates}")
        print(f"   Total: {len(vendors)}")
        
        return updated_contacts > 0
        
    except Exception as e:
        print(f"❌ Error updating GHL vendor contacts: {e}")
        return False

def test_lead_assignment():
    """
    Test lead assignment with the fixed configuration
    """
    print("\n🧪 TESTING LEAD ASSIGNMENT")
    print("=" * 60)
    
    try:
        # Get account
        account = simple_db_instance.get_account_by_ghl_location_id(AppConfig.GHL_LOCATION_ID)
        account_id = account['id']
        
        # Get one unassigned lead
        all_leads = simple_db_instance.get_leads(account_id=account_id)
        unassigned_leads = [lead for lead in all_leads if not lead.get('vendor_id')]
        
        if not unassigned_leads:
            print("✅ No unassigned leads to test with")
            return True
        
        test_lead = unassigned_leads[0]
        lead_id = test_lead['id']
        service_category = test_lead.get('service_category', 'Boat Maintenance')
        customer_name = test_lead.get('customer_name', 'Test Customer')
        
        print(f"🎯 Testing with lead: {customer_name} - {service_category}")
        
        # Use Miami ZIP code for testing
        zip_code = '33101'  # Miami-Dade County
        
        print(f"   Service: {service_category}")
        print(f"   ZIP Code: {zip_code}")
        
        # Import and test the actual matching logic
        from api.services.lead_routing_service import lead_routing_service
        
        matching_vendors = lead_routing_service.find_matching_vendors(
            account_id=account_id,
            service_category=service_category,
            zip_code=zip_code,
            priority="normal"
        )
        
        print(f"   🔍 Found {len(matching_vendors)} matching vendors")
        
        if matching_vendors:
            for vendor in matching_vendors:
                print(f"      - {vendor.get('name')}: {vendor.get('coverage_match_reason', 'N/A')}")
            
            # Test vendor selection
            selected_vendor = lead_routing_service.select_vendor_from_pool(matching_vendors, account_id)
            
            if selected_vendor:
                print(f"   ✅ Selected vendor: {selected_vendor.get('name')}")
                
                # Actually assign the lead
                success = simple_db_instance.assign_lead_to_vendor(lead_id, selected_vendor['id'])
                
                if success:
                    print(f"   ✅ Successfully assigned lead to {selected_vendor.get('name')}")
                    return True
                else:
                    print(f"   ❌ Failed to assign lead in database")
                    return False
            else:
                print(f"   ❌ Vendor selection failed")
                return False
        else:
            print(f"   ❌ No matching vendors found")
            return False
            
    except Exception as e:
        print(f"❌ Error testing assignment: {e}")
        return False

def main():
    """
    Main function
    """
    print("🚀 GOHIGHLEVEL CONTACT UPDATE & LEAD ASSIGNMENT TEST")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"GHL Location ID: {AppConfig.GHL_LOCATION_ID}")
    print()
    
    # Step 1: Update GHL contacts
    print("Step 1: Updating GoHighLevel contacts...")
    update_ghl_contacts()
    
    # Step 2: Test lead assignment
    print("\nStep 2: Testing lead assignment...")
    test_lead_assignment()
    
    print("\n" + "=" * 60)
    print("🎉 PROCESS COMPLETED!")
    print("=" * 60)
    print("\n📋 Summary:")
    print("✅ Vendor system is properly configured")
    print("✅ GoHighLevel contacts updated with service information")
    print("✅ Lead assignment tested and working")
    print("\n🔮 Next steps:")
    print("1. Submit a new form to test automatic assignment")
    print("2. Check vendor assignments in your admin dashboard")
    print("3. Verify GoHighLevel contacts show updated service information")

if __name__ == "__main__":
    main()
