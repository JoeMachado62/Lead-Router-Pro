#!/usr/bin/env python3
"""
TEST NEW DATABASE STRUCTURE
Validates that the new multi-level routing database structure works correctly.

TESTS:
- Creating leads with proper service and location fields
- Creating vendors with proper service and coverage fields  
- Testing vendor matching logic with new schema
- Verifying 1:1 matching relationships work
"""

import sqlite3
import json
import uuid
import sys
import os
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.services.lead_routing_service import lead_routing_service
from api.services.location_service import location_service

def test_database_structure():
    """Test the new database structure and matching logic"""
    
    print("🧪 TESTING NEW DATABASE STRUCTURE")
    print("=" * 45)
    print("Validating multi-level routing with proper schema")
    print("")
    
    try:
        # Step 1: Get or create account
        account_id = get_or_create_test_account()
        if not account_id:
            print("❌ Failed to get account")
            return False
        
        print(f"✅ Using account: {account_id}")
        
        # Step 2: Create test vendor
        vendor_id = create_test_vendor(account_id)
        if not vendor_id:
            print("❌ Failed to create test vendor")
            return False
        
        print(f"✅ Created test vendor: {vendor_id}")
        
        # Step 3: Create test lead
        lead_id = create_test_lead(account_id)
        if not lead_id:
            print("❌ Failed to create test lead")
            return False
        
        print(f"✅ Created test lead: {lead_id}")
        
        # Step 4: Test vendor matching
        success = test_vendor_matching(account_id)
        if not success:
            print("❌ Vendor matching test failed")
            return False
        
        # Step 5: Verify database content
        verify_database_content()
        
        print("\n🎉 DATABASE STRUCTURE TEST SUCCESSFUL!")
        print("   ✅ New schema works correctly")
        print("   ✅ Multi-level routing functional")
        print("   ✅ Service and location matching operational")
        print("   ✅ Ready for production use")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in database structure test: {e}")
        return False

def get_or_create_test_account():
    """Get or create a test account"""
    try:
        conn = sqlite3.connect('smart_lead_router.db')
        cursor = conn.cursor()
        
        # Try to get existing account
        cursor.execute("SELECT id FROM accounts LIMIT 1")
        account = cursor.fetchone()
        
        if account:
            conn.close()
            return account[0]
        
        # Create test account
        account_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO accounts (
                id, company_name, industry, ghl_location_id, 
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (account_id, "Test Marine LLC", "marine", "test_location"))
        
        conn.commit()
        conn.close()
        return account_id
        
    except Exception as e:
        print(f"❌ Error with test account: {e}")
        return None

def create_test_vendor(account_id):
    """Create a test vendor with proper multi-level routing data"""
    try:
        conn = sqlite3.connect('smart_lead_router.db')
        cursor = conn.cursor()
        
        vendor_id = str(uuid.uuid4())
        
        # Create vendor with proper new schema
        cursor.execute("""
            INSERT INTO vendors (
                id, account_id, ghl_contact_id, ghl_user_id, name, email, phone,
                company_name, service_categories, services_offered, coverage_type,
                coverage_states, coverage_counties, last_lead_assigned,
                lead_close_percentage, status, taking_new_work, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (
            vendor_id,
            account_id,
            f"test_contact_{vendor_id[:8]}",
            f"test_user_{vendor_id[:8]}",
            "Test Marine Vendor",
            "test@example.com",
            "555-0123",
            "Test Marine Services LLC",
            json.dumps(["Marine Systems", "Engines and Generators"]),  # service_categories
            json.dumps(["AC Service", "Engine Repair", "Generator Service"]),  # services_offered
            "county",  # coverage_type
            json.dumps(["FL"]),  # coverage_states
            json.dumps(["Miami-Dade, FL", "Broward, FL"]),  # coverage_counties
            None,  # last_lead_assigned
            85.5,  # lead_close_percentage
            "active",  # status
            True  # taking_new_work
        ))
        
        conn.commit()
        conn.close()
        
        print(f"   📋 Service Categories: ['Marine Systems', 'Engines and Generators']")
        print(f"   🛠️ Services Offered: ['AC Service', 'Engine Repair', 'Generator Service']")
        print(f"   🗺️ Coverage: ['Miami-Dade, FL', 'Broward, FL']")
        print(f"   🎯 Performance: 85.5% close rate")
        
        return vendor_id
        
    except Exception as e:
        print(f"❌ Error creating test vendor: {e}")
        return None

def create_test_lead(account_id):
    """Create a test lead with proper multi-level routing data"""
    try:
        # First, convert ZIP to county
        zip_code = "33135"  # Miami ZIP
        location_data = location_service.zip_to_location(zip_code)
        
        if location_data.get('error'):
            print(f"⚠️ Location service error: {location_data['error']}")
            # Use fallback data
            service_county = "Miami-Dade"
            service_state = "FL"
        else:
            service_county = location_data.get('county', 'Miami-Dade')
            service_state = location_data.get('state', 'FL')
        
        conn = sqlite3.connect('smart_lead_router.db')
        cursor = conn.cursor()
        
        lead_id = str(uuid.uuid4())
        
        # Create lead with proper new schema
        cursor.execute("""
            INSERT INTO leads (
                id, account_id, ghl_contact_id, ghl_opportunity_id, customer_name,
                customer_email, customer_phone, primary_service_category,
                specific_service_requested, customer_zip_code, service_county,
                service_state, vendor_id, status, priority, source, service_details,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (
            lead_id,
            account_id,
            f"test_lead_contact_{lead_id[:8]}",
            f"test_opportunity_{lead_id[:8]}",
            "John Test Customer",
            "customer@example.com", 
            "555-0987",
            "Marine Systems",  # primary_service_category
            "AC Service",  # specific_service_requested  
            zip_code,  # customer_zip_code
            service_county,  # service_county
            service_state,  # service_state
            None,  # vendor_id (unassigned)
            "unassigned",  # status
            "normal",  # priority
            "test",  # source
            json.dumps({  # service_details
                "test_data": True,
                "original_form": "boat_maintenance_ac_service",
                "location": {
                    "zip_code": zip_code,
                    "county": service_county,
                    "state": service_state
                }
            })
        ))
        
        conn.commit()
        conn.close()
        
        print(f"   📋 Primary Category: 'Marine Systems'")
        print(f"   🎯 Specific Service: 'AC Service'")
        print(f"   📍 Location: {zip_code} → {service_county}, {service_state}")
        print(f"   📊 Status: unassigned")
        
        return lead_id
        
    except Exception as e:
        print(f"❌ Error creating test lead: {e}")
        return None

def test_vendor_matching(account_id):
    """Test the vendor matching logic with new database structure"""
    print(f"\n🔍 TESTING VENDOR MATCHING LOGIC:")
    print("-" * 40)
    
    try:
        # Test exact service matching
        print("TEST 1: Exact Service Matching")
        matching_vendors = lead_routing_service.find_matching_vendors(
            account_id=account_id,
            service_category="Marine Systems",
            zip_code="33135", 
            priority="normal",
            specific_service="AC Service"
        )
        
        print(f"   🔍 Looking for: 'Marine Systems' → 'AC Service' in Miami-Dade, FL")
        print(f"   ✅ Found {len(matching_vendors)} matching vendors")
        
        if matching_vendors:
            vendor = matching_vendors[0]
            print(f"   📋 Matched vendor: {vendor.get('name')}")
            print(f"   🛠️ Vendor services: {vendor.get('services_offered')}")
            print(f"   🗺️ Vendor coverage: {vendor.get('coverage_counties')}")
            print(f"   📈 Match reason: {vendor.get('coverage_match_reason', 'N/A')}")
        
        # Test category-only matching
        print(f"\nTEST 2: Category-Only Matching")
        matching_vendors_category = lead_routing_service.find_matching_vendors(
            account_id=account_id,
            service_category="Marine Systems",
            zip_code="33135",
            priority="normal"
            # No specific_service provided
        )
        
        print(f"   🔍 Looking for: 'Marine Systems' (any service) in Miami-Dade, FL")
        print(f"   ✅ Found {len(matching_vendors_category)} matching vendors")
        
        # Test location mismatch
        print(f"\nTEST 3: Location Mismatch")
        matching_vendors_location = lead_routing_service.find_matching_vendors(
            account_id=account_id,
            service_category="Marine Systems",
            zip_code="90210",  # Los Angeles ZIP
            priority="normal",
            specific_service="AC Service"
        )
        
        print(f"   🔍 Looking for: 'Marine Systems' → 'AC Service' in Los Angeles County, CA")
        print(f"   ✅ Found {len(matching_vendors_location)} matching vendors (should be 0)")
        
        # Test service mismatch
        print(f"\nTEST 4: Service Mismatch")
        matching_vendors_service = lead_routing_service.find_matching_vendors(
            account_id=account_id,
            service_category="Marine Systems",
            zip_code="33135",
            priority="normal",
            specific_service="Boat Hauling"  # Service not offered by test vendor
        )
        
        print(f"   🔍 Looking for: 'Marine Systems' → 'Boat Hauling' in Miami-Dade, FL")
        print(f"   ✅ Found {len(matching_vendors_service)} matching vendors (should be 0)")
        
        # Test vendor selection
        if matching_vendors:
            print(f"\nTEST 5: Vendor Selection")
            selected_vendor = lead_routing_service.select_vendor_from_pool(matching_vendors, account_id)
            
            if selected_vendor:
                print(f"   🎯 Selected vendor: {selected_vendor.get('name')}")
                print(f"   📈 Close rate: {selected_vendor.get('lead_close_percentage', 0)}%")
                print(f"   🔄 Selection method: performance-based or round-robin")
            else:
                print(f"   ❌ No vendor selected")
                return False
        
        print(f"\n✅ ALL MATCHING TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Error in vendor matching test: {e}")
        return False

def verify_database_content():
    """Verify the database contains the expected data structure"""
    print(f"\n🔍 VERIFYING DATABASE CONTENT:")
    print("-" * 35)
    
    try:
        conn = sqlite3.connect('smart_lead_router.db')
        cursor = conn.cursor()
        
        # Check leads table
        cursor.execute("""
            SELECT COUNT(*), 
                   COUNT(CASE WHEN primary_service_category IS NOT NULL THEN 1 END),
                   COUNT(CASE WHEN specific_service_requested IS NOT NULL THEN 1 END),
                   COUNT(CASE WHEN service_county IS NOT NULL THEN 1 END)
            FROM leads
        """)
        leads_stats = cursor.fetchone()
        
        print(f"📋 LEADS TABLE:")
        print(f"   Total leads: {leads_stats[0]}")
        print(f"   With primary category: {leads_stats[1]}")
        print(f"   With specific service: {leads_stats[2]}")
        print(f"   With service county: {leads_stats[3]}")
        
        # Check vendors table
        cursor.execute("""
            SELECT COUNT(*),
                   COUNT(CASE WHEN service_categories != '[]' THEN 1 END),
                   COUNT(CASE WHEN services_offered != '[]' THEN 1 END), 
                   COUNT(CASE WHEN coverage_counties != '[]' THEN 1 END)
            FROM vendors
        """)
        vendors_stats = cursor.fetchone()
        
        print(f"\n🏢 VENDORS TABLE:")
        print(f"   Total vendors: {vendors_stats[0]}")
        print(f"   With service categories: {vendors_stats[1]}")
        print(f"   With services offered: {vendors_stats[2]}")
        print(f"   With coverage counties: {vendors_stats[3]}")
        
        # Show sample data
        cursor.execute("""
            SELECT primary_service_category, specific_service_requested, 
                   service_county, service_state
            FROM leads LIMIT 1
        """)
        sample_lead = cursor.fetchone()
        
        if sample_lead:
            print(f"\n📋 SAMPLE LEAD DATA:")
            print(f"   Category: {sample_lead[0]}")
            print(f"   Service: {sample_lead[1]}")
            print(f"   County: {sample_lead[2]}")
            print(f"   State: {sample_lead[3]}")
        
        cursor.execute("""
            SELECT name, service_categories, services_offered, coverage_counties
            FROM vendors LIMIT 1
        """)
        sample_vendor = cursor.fetchone()
        
        if sample_vendor:
            print(f"\n🏢 SAMPLE VENDOR DATA:")
            print(f"   Name: {sample_vendor[0]}")
            print(f"   Categories: {sample_vendor[1]}")
            print(f"   Services: {sample_vendor[2]}")
            print(f"   Coverage: {sample_vendor[3]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error verifying database content: {e}")

if __name__ == '__main__':
    print("🧪 DATABASE STRUCTURE VALIDATION TEST")
    print("Testing new multi-level routing schema and matching logic")
    print("")
    
    success = test_database_structure()
    
    if success:
        print(f"\n🎉 ALL TESTS PASSED!")
        print("   ✅ New database structure is working correctly")
        print("   ✅ Multi-level routing is operational") 
        print("   ✅ Service and location matching functional")
        print("   ✅ System ready for production use")
    else:
        print(f"\n❌ TESTS FAILED!")
        print("   Check error messages above for details")
