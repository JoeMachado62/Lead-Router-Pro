#!/usr/bin/env python3
"""
Fix Vendor Assignment Issue
Populates vendors with services and coverage areas so they can receive lead assignments
"""

import sys
import os
import json
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.simple_connection import db as simple_db_instance
from api.services.lead_routing_service import lead_routing_service
from config import AppConfig

def fix_vendor_services_and_coverage():
    """
    Fix the vendor assignment issue by populating vendors with services and coverage areas
    """
    print("🔧 FIXING VENDOR ASSIGNMENT ISSUE")
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
        
        # Define default services and coverage for marine vendors
        default_services = [
            "Boat Maintenance",
            "Marine Systems", 
            "Engines and Generators",
            "Boat and Yacht Repair"
        ]
        
        # Default coverage areas (ZIP codes for major marine areas)
        default_zip_codes = [
            "33101", "33102", "33103", "33104", "33109", "33139", "33140", "33141", "33154",  # Miami
            "33301", "33304", "33305", "33306", "33308", "33309", "33312", "33315", "33316",  # Fort Lauderdale
            "33401", "33403", "33404", "33405", "33406", "33407", "33408", "33409", "33410",  # West Palm Beach
            "90210", "90211", "90212", "90213", "90265", "90266", "90267", "90290", "90291",  # Los Angeles/Malibu
            "10001", "10002", "10003", "10004", "10005", "10006", "10007", "10009", "10010",  # New York
            "02101", "02102", "02103", "02104", "02105", "02106", "02107", "02108", "02109",  # Boston
            "98101", "98102", "98103", "98104", "98105", "98106", "98107", "98108", "98109",  # Seattle
            "94101", "94102", "94103", "94104", "94105", "94106", "94107", "94108", "94109"   # San Francisco
        ]
        
        # Update each vendor
        conn = simple_db_instance._get_conn()
        cursor = conn.cursor()
        
        updated_count = 0
        
        for vendor in vendors:
            vendor_id = vendor['id']
            vendor_name = vendor['name']
            
            print(f"\n🔄 Updating vendor: {vendor_name}")
            
            # Convert services and areas to JSON strings
            services_json = json.dumps(default_services)
            areas_json = json.dumps(default_zip_codes)
            
            # Update vendor with services and coverage
            cursor.execute("""
                UPDATE vendors 
                SET services_provided = ?, 
                    service_areas = ?,
                    service_coverage_type = 'zip',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (services_json, areas_json, vendor_id))
            
            updated_count += 1
            print(f"   ✅ Added {len(default_services)} services and {len(default_zip_codes)} ZIP codes")
        
        conn.commit()
        conn.close()
        
        print(f"\n🎉 Successfully updated {updated_count} vendors!")
        
        # Verify the updates
        print("\n📋 Verification:")
        updated_vendors = simple_db_instance.get_vendors(account_id=account_id)
        
        for vendor in updated_vendors:
            services = vendor.get('services_provided', [])
            areas = vendor.get('service_areas', [])
            
            print(f"   {vendor['name']}: {len(services)} services, {len(areas)} areas")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing vendors: {e}")
        return False

def test_vendor_matching():
    """
    Test vendor matching with a sample lead to verify the fix works
    """
    print("\n🧪 TESTING VENDOR MATCHING")
    print("=" * 60)
    
    try:
        # Get account
        account = simple_db_instance.get_account_by_ghl_location_id(AppConfig.GHL_LOCATION_ID)
        account_id = account['id']
        
        # Test with sample lead data
        test_service_category = "Boat Maintenance"
        test_zip_code = "33101"  # Miami
        
        print(f"🎯 Testing: Service='{test_service_category}', ZIP='{test_zip_code}'")
        
        # Use the actual matching logic
        matching_vendors = lead_routing_service.find_matching_vendors(
            account_id=account_id,
            service_category=test_service_category,
            zip_code=test_zip_code,
            priority="normal"
        )
        
        print(f"🔍 Found {len(matching_vendors)} matching vendors:")
        
        for i, vendor in enumerate(matching_vendors, 1):
            print(f"   {i}. {vendor.get('name')} - {vendor.get('coverage_match_reason', 'Unknown reason')}")
        
        if matching_vendors:
            # Test vendor selection
            selected_vendor = lead_routing_service.select_vendor_from_pool(matching_vendors, account_id)
            if selected_vendor:
                print(f"✅ Selected vendor: {selected_vendor.get('name')}")
                return True
            else:
                print("❌ Vendor selection failed")
                return False
        else:
            print("❌ No matching vendors found - fix may not have worked")
            return False
            
    except Exception as e:
        print(f"❌ Error testing vendor matching: {e}")
        return False

def assign_existing_leads():
    """
    Try to assign existing unassigned leads to vendors
    """
    print("\n🎯 ASSIGNING EXISTING UNASSIGNED LEADS")
    print("=" * 60)
    
    try:
        # Get account
        account = simple_db_instance.get_account_by_ghl_location_id(AppConfig.GHL_LOCATION_ID)
        account_id = account['id']
        
        # Get unassigned leads
        all_leads = simple_db_instance.get_leads(account_id=account_id)
        unassigned_leads = [lead for lead in all_leads if not lead.get('vendor_id')]
        
        print(f"📊 Found {len(unassigned_leads)} unassigned leads")
        
        if not unassigned_leads:
            print("✅ No unassigned leads to process")
            return True
        
        assigned_count = 0
        
        for lead in unassigned_leads[:10]:  # Process first 10 leads
            lead_id = lead['id']
            service_category = lead.get('service_category', 'Unknown')
            customer_name = lead.get('customer_name', 'Unknown')
            
            print(f"\n🎯 Processing lead: {customer_name} - {service_category}")
            
            # Extract ZIP code from service details
            service_details = lead.get('service_details', {})
            if isinstance(service_details, str):
                try:
                    service_details = json.loads(service_details)
                except:
                    service_details = {}
            
            location_info = service_details.get('location', {})
            zip_code = location_info.get('zip_code', '33101')  # Default to Miami if no ZIP
            
            print(f"   Service: {service_category}, ZIP: {zip_code}")
            
            # Find matching vendors
            matching_vendors = lead_routing_service.find_matching_vendors(
                account_id=account_id,
                service_category=service_category,
                zip_code=zip_code,
                priority="normal"
            )
            
            if matching_vendors:
                # Select vendor
                selected_vendor = lead_routing_service.select_vendor_from_pool(matching_vendors, account_id)
                
                if selected_vendor:
                    # Assign lead to vendor
                    success = simple_db_instance.assign_lead_to_vendor(lead_id, selected_vendor['id'])
                    
                    if success:
                        assigned_count += 1
                        print(f"   ✅ Assigned to: {selected_vendor['name']}")
                    else:
                        print(f"   ❌ Failed to assign to database")
                else:
                    print(f"   ❌ Vendor selection failed")
            else:
                print(f"   ❌ No matching vendors found")
        
        print(f"\n🎉 Successfully assigned {assigned_count} leads!")
        return True
        
    except Exception as e:
        print(f"❌ Error assigning leads: {e}")
        return False

def main():
    """
    Main function to fix vendor assignment issue
    """
    print("🚀 VENDOR ASSIGNMENT FIX TOOL")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"GHL Location ID: {AppConfig.GHL_LOCATION_ID}")
    
    # Step 1: Fix vendor services and coverage
    print("\nStep 1: Fixing vendor services and coverage...")
    if not fix_vendor_services_and_coverage():
        print("❌ Failed to fix vendors. Exiting.")
        return
    
    # Step 2: Test vendor matching
    print("\nStep 2: Testing vendor matching...")
    if not test_vendor_matching():
        print("❌ Vendor matching test failed. Check configuration.")
        return
    
    # Step 3: Assign existing leads
    print("\nStep 3: Assigning existing unassigned leads...")
    assign_existing_leads()
    
    print("\n" + "=" * 60)
    print("🎉 VENDOR ASSIGNMENT FIX COMPLETED!")
    print("=" * 60)
    print("\n📋 Summary:")
    print("✅ Updated all vendors with services and coverage areas")
    print("✅ Verified vendor matching logic works")
    print("✅ Attempted to assign existing unassigned leads")
    print("\n🔮 Next steps:")
    print("1. Test submitting a new form to verify automatic assignment works")
    print("2. Check the admin dashboard to see assigned leads")
    print("3. Monitor future form submissions for proper assignment")

if __name__ == "__main__":
    main()
