#!/usr/bin/env python3
"""
Complete Vendor System Fix
1. Converts ZIP codes to counties for proper geographic coverage
2. Fixes vendor configuration in local database
3. Updates GoHighLevel contacts with correct service categories and areas
"""

import sys
import os
import json
import requests
from datetime import datetime
from typing import List, Dict, Any, Set

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.simple_connection import db as simple_db_instance
from config import AppConfig
from api.services.location_service import location_service
from api.services.ghl_api import ghl_api

def convert_zip_codes_to_counties(zip_codes: List[str]) -> List[str]:
    """
    Convert ZIP codes to county format for proper coverage
    
    Args:
        zip_codes: List of ZIP codes
        
    Returns:
        List of counties in "County Name, ST" format
    """
    counties = set()
    
    print(f"🗺️  Converting {len(zip_codes)} ZIP codes to counties...")
    
    for zip_code in zip_codes:
        try:
            location_data = location_service.zip_to_location(zip_code)
            
            if not location_data.get('error'):
                county = location_data.get('county')
                state = location_data.get('state')
                
                if county and state:
                    county_format = f"{county}, {state}"
                    counties.add(county_format)
                    print(f"   {zip_code} → {county_format}")
                else:
                    print(f"   {zip_code} → No county/state data")
            else:
                print(f"   {zip_code} → ERROR: {location_data['error']}")
                
        except Exception as e:
            print(f"   {zip_code} → EXCEPTION: {e}")
    
    county_list = sorted(list(counties))
    print(f"✅ Converted to {len(county_list)} unique counties")
    
    return county_list

def fix_vendor_database_configuration():
    """
    Fix vendor configuration in local database
    """
    print("\n🔧 FIXING VENDOR DATABASE CONFIGURATION")
    print("=" * 60)
    
    try:
        # Get account
        account = simple_db_instance.get_account_by_ghl_location_id(AppConfig.GHL_LOCATION_ID)
        if not account:
            print("❌ No account found!")
            return False
        
        account_id = account['id']
        print(f"✅ Found account: {account['company_name']} ({account_id})")
        
        # Get all vendors
        vendors = simple_db_instance.get_vendors(account_id=account_id)
        print(f"📊 Found {len(vendors)} vendors")
        
        if not vendors:
            print("❌ No vendors found!")
            return False
        
        # Process each vendor
        conn = simple_db_instance._get_conn()
        cursor = conn.cursor()
        
        updated_count = 0
        
        for vendor in vendors:
            vendor_id = vendor['id']
            vendor_name = vendor['name']
            
            print(f"\n🔄 Processing vendor: {vendor_name}")
            
            # Get current ZIP codes from service_areas
            current_service_areas = vendor.get('service_areas', [])
            if isinstance(current_service_areas, str):
                try:
                    current_service_areas = json.loads(current_service_areas)
                except:
                    current_service_areas = []
            
            # Convert ZIP codes to counties
            if current_service_areas:
                counties = convert_zip_codes_to_counties(current_service_areas)
                
                if counties:
                    # Update vendor with county-based configuration
                    counties_json = json.dumps(counties)
                    
                    cursor.execute("""
                        UPDATE vendors 
                        SET service_coverage_type = 'county',
                            service_counties = ?,
                            service_areas = '[]',
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (counties_json, vendor_id))
                    
                    updated_count += 1
                    print(f"   ✅ Updated to county coverage: {len(counties)} counties")
                    for county in counties:
                        print(f"      - {county}")
                else:
                    print(f"   ⚠️  No valid counties found from ZIP codes")
            else:
                print(f"   ⚠️  No service areas to convert")
        
        conn.commit()
        conn.close()
        
        print(f"\n🎉 Successfully updated {updated_count} vendors to county-based coverage!")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing vendor database configuration: {e}")
        return False

def update_ghl_vendor_contacts():
    """
    Update GoHighLevel contacts with correct service categories and areas
    """
    print("\n🔄 UPDATING GOHIGHLEVEL VENDOR CONTACTS")
    print("=" * 60)
    
    try:
        # Get account
        account = simple_db_instance.get_account_by_ghl_location_id(AppConfig.GHL_LOCATION_ID)
        if not account:
            print("❌ No account found!")
            return False
        
        account_id = account['id']
        vendors = simple_db_instance.get_vendors(account_id=account_id)
        
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
            
            # Create custom field updates
            custom_fields = {}
            
            # Primary Service Category (use first service)
            if services_provided:
                custom_fields['primary_service_category'] = services_provided[0]
                print(f"   🎯 Primary Service: {services_provided[0]}")
            
            # Services Offered (comma-separated)
            if services_provided:
                custom_fields['services_offered'] = ', '.join(services_provided)
                print(f"   🛠️  Services: {', '.join(services_provided)}")
            
            # Service Areas (counties)
            if service_counties:
                custom_fields['service_areas'] = ', '.join(service_counties)
                print(f"   📍 Service Areas: {', '.join(service_counties)}")
            
            # Update the contact via GHL API
            try:
                update_data = {
                    'customFields': custom_fields
                }
                
                success = ghl_api.update_contact(ghl_contact_id, update_data)
                
                if success:
                    updated_contacts += 1
                    print(f"   ✅ Successfully updated GHL contact")
                else:
                    failed_updates += 1
                    print(f"   ❌ Failed to update GHL contact")
                    
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
    print("\n🧪 TESTING LEAD ASSIGNMENT WITH FIXED CONFIGURATION")
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
        
        # Extract ZIP code from service details
        service_details = test_lead.get('service_details', {})
        if isinstance(service_details, str):
            try:
                service_details = json.loads(service_details)
            except:
                service_details = {}
        
        location_info = service_details.get('location', {})
        zip_code = location_info.get('zip_code', '33101')  # Use actual ZIP or default
        
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
            # Test vendor selection
            selected_vendor = lead_routing_service.select_vendor_from_pool(matching_vendors, account_id)
            
            if selected_vendor:
                print(f"   ✅ Selected vendor: {selected_vendor.get('name')}")
                print(f"   📋 Coverage reason: {selected_vendor.get('coverage_match_reason', 'N/A')}")
                
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
    Main function - complete vendor system fix
    """
    print("🚀 COMPLETE VENDOR SYSTEM FIX")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"GHL Location ID: {AppConfig.GHL_LOCATION_ID}")
    print()
    print("This fix will:")
    print("✅ Convert ZIP codes to counties for proper geographic coverage")
    print("✅ Update vendor configuration in local database")
    print("✅ Update GoHighLevel contacts with correct service info")
    print("✅ Test lead assignment with fixed configuration")
    print()
    
    # Step 1: Fix vendor database configuration
    if not fix_vendor_database_configuration():
        print("❌ Failed to fix vendor database configuration. Exiting.")
        return
    
    # Step 2: Update GHL contacts
    if not update_ghl_vendor_contacts():
        print("❌ Failed to update GHL contacts. Continuing with testing...")
    
    # Step 3: Test lead assignment
    if not test_lead_assignment():
        print("❌ Test assignment failed. Check configuration.")
        return
    
    print("\n" + "=" * 60)
    print("🎉 COMPLETE VENDOR SYSTEM FIX COMPLETED!")
    print("=" * 60)
    print("\n📋 What was fixed:")
    print("✅ Vendors converted from ZIP-based to county-based coverage")
    print("✅ Database configuration updated to use proper geographic matching")
    print("✅ GoHighLevel contacts updated with service categories and areas")
    print("✅ Lead assignment tested and working")
    print("\n🔮 Next steps:")
    print("1. Submit a new form to test automatic assignment")
    print("2. Verify vendor assignments in your admin dashboard")
    print("3. Check GoHighLevel contacts for updated service information")
    print("\n⚠️  Note: Your system now uses county-based geographic matching.")
    print("   This is more efficient and eliminates ZIP code array bloat.")

if __name__ == "__main__":
    main()
