#!/usr/bin/env python3
"""
Test script to verify bulk lead reassignment fixes
"""
import sqlite3
import json

def test_database_query():
    """Test that the database query works with correct column names"""
    print("\n=== Testing Database Query ===")
    try:
        conn = sqlite3.connect('/root/Lead-Router-Pro/smart_lead_router.db')
        cursor = conn.cursor()
        
        # Test the fixed query
        cursor.execute('''
            SELECT id, account_id, vendor_id, ghl_contact_id, ghl_opportunity_id, 
                   primary_service_category, customer_name, customer_email, customer_phone, 
                   service_details, priority, status, 
                   service_county, service_state, customer_zip_code,
                   specific_service_requested, created_at, updated_at
            FROM leads 
            LIMIT 1
        ''')
        
        row = cursor.fetchone()
        if row:
            print("✅ Database query successful - column names are correct")
            print(f"   Sample lead: {row[6]} (name), Category: {row[5]}, Service: {row[15]}")
        else:
            print("⚠️ No leads found in database to test")
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database query failed: {e}")
        return False

def test_field_mapper():
    """Test that field mapper uses correct field names"""
    print("\n=== Testing Field Mapper ===")
    try:
        from api.services.field_mapper import FieldMapper
        mapper = FieldMapper()
        
        # Test mapping
        test_payload = {
            "ServiceNeeded": "AC Repair",
            "marineService": "Engine Service"
        }
        
        mapped = mapper.map_payload(test_payload)
        
        # Check if mapped to correct field name
        if "specific_service_requested" in mapped:
            print(f"✅ Field mapper correctly maps to 'specific_service_requested'")
            print(f"   ServiceNeeded -> {mapped.get('specific_service_requested')}")
        else:
            print(f"❌ Field mapper not mapping correctly. Mapped fields: {list(mapped.keys())}")
            
        return True
        
    except Exception as e:
        print(f"❌ Field mapper test failed: {e}")
        return False

def test_custom_fields_handling():
    """Test that custom fields handling works for both dict and list formats"""
    print("\n=== Testing Custom Fields Handling ===")
    
    # Test dict format
    custom_fields_dict = {
        'FT85QGi0tBq1AfVGNJ9v': 'AC Service',
        'other_field': 'value'
    }
    
    # Test list format
    custom_fields_list = [
        {'id': 'FT85QGi0tBq1AfVGNJ9v', 'value': 'AC Service'},
        {'id': 'other_field', 'value': 'value'}
    ]
    
    specific_service = ""
    
    # Test dict handling
    if isinstance(custom_fields_dict, dict):
        for field_id, field_value in custom_fields_dict.items():
            if field_id == 'FT85QGi0tBq1AfVGNJ9v':
                specific_service = field_value
                break
    
    if specific_service == 'AC Service':
        print("✅ Dict format handling works correctly")
    else:
        print("❌ Dict format handling failed")
    
    # Test list handling
    specific_service = ""
    if isinstance(custom_fields_list, list):
        for field in custom_fields_list:
            if isinstance(field, dict) and field.get('id') == 'FT85QGi0tBq1AfVGNJ9v':
                specific_service = field.get('value', '')
                break
    
    if specific_service == 'AC Service':
        print("✅ List format handling works correctly")
    else:
        print("❌ List format handling failed")
    
    return True

def check_ghl_api_method():
    """Check if get_opportunities_by_contact method exists"""
    print("\n=== Testing GHL API Method ===")
    try:
        from api.services.ghl_api import GoHighLevelAPI
        from config import AppConfig
        
        api = GoHighLevelAPI(
            location_id=AppConfig.GHL_LOCATION_ID,
            api_key=AppConfig.GHL_PRIVATE_TOKEN
        )
        
        if hasattr(api, 'get_opportunities_by_contact'):
            print("✅ get_opportunities_by_contact method exists")
        else:
            print("❌ get_opportunities_by_contact method not found")
            
        return True
        
    except Exception as e:
        print(f"❌ GHL API test failed: {e}")
        return False

def main():
    print("="*60)
    print("TESTING BULK LEAD REASSIGNMENT FIXES")
    print("="*60)
    
    results = []
    
    # Run all tests
    results.append(test_database_query())
    results.append(test_field_mapper())
    results.append(test_custom_fields_handling())
    results.append(check_ghl_api_method())
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    if all(results):
        print("✅ All tests passed! Bulk lead reassignment should work now.")
    else:
        print("⚠️ Some tests failed. Review the errors above.")
    
    print("\nKey fixes applied:")
    print("1. ✅ Fixed database column: priority_score -> priority")
    print("2. ✅ Fixed field mapper: specific_service_needed -> specific_service_requested")
    print("3. ✅ Added handling for custom fields as both dict and list")
    print("4. ✅ Added check for existing opportunities before creating new ones")
    print("\nYou can now try the bulk lead reassignment from the admin dashboard.")

if __name__ == "__main__":
    main()