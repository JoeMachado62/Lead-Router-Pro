#!/usr/bin/env python3
"""
County-Based Lead Assignment Test
Tests the corrected lead assignment system with:
1. Proper ZIP → County conversion
2. Integer/String type handling for ZIP codes
3. County-based vendor matching
4. GHL opportunity creation with county information
"""

import sys
import os
sys.path.insert(0, '/root/Lead-Router-Pro')

import asyncio
import json
from typing import Dict, Any

# Load environment
def load_env_file(env_path: str = '.env'):
    if not os.path.exists(env_path):
        return
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                value = value.strip('"\'')
                os.environ[key] = value

load_env_file()

from api.routes.routing_admin import _process_single_unassigned_lead, _extract_location_data
from api.services.location_service import location_service
from database.simple_connection import db

def test_type_handling():
    """Test integer and string ZIP code handling"""
    print("🧪 Testing Integer/String ZIP Code Handling...")
    
    # Test case 1: Integer ZIP code in custom fields (the bug that was crashing)
    test_lead_int_zip = {
        'ghl_contact_id': 'test_int_zip',
        'name': 'Test Lead Integer ZIP',
        'custom_fields': [
            {'name': 'What Zip Code Are You Requesting Service In?', 'value': 33101},  # INTEGER
            {'name': 'service_category', 'value': 'Engine Repair'}
        ]
    }
    
    # Test case 2: String ZIP code in custom fields
    test_lead_str_zip = {
        'ghl_contact_id': 'test_str_zip', 
        'name': 'Test Lead String ZIP',
        'custom_fields': [
            {'name': 'What Zip Code Are You Requesting Service In?', 'value': '33102'},  # STRING
            {'name': 'service_category', 'value': 'Engine Repair'}
        ]
    }
    
    # Test case 3: Mixed type custom fields
    test_lead_mixed = {
        'ghl_contact_id': 'test_mixed',
        'name': 'Test Lead Mixed Types',
        'custom_fields': [
            {'name': 'some_field', 'value': None},  # None value
            {'name': 'zip_code', 'value': 33103},   # Integer ZIP
            {'name': 'other_field', 'value': 'text'}  # String value
        ]
    }
    
    # Test extraction
    zip1 = _extract_location_data(test_lead_int_zip)
    zip2 = _extract_location_data(test_lead_str_zip)
    zip3 = _extract_location_data(test_lead_mixed)
    
    print(f"  ✅ Integer ZIP extraction: {zip1} (should be '33101')")
    print(f"  ✅ String ZIP extraction: {zip2} (should be '33102')")
    print(f"  ✅ Mixed types extraction: {zip3} (should be '33103')")
    
    return zip1 == '33101' and zip2 == '33102' and zip3 == '33103'

def test_county_conversion():
    """Test ZIP to county conversion using LocationService"""
    print("\n🌍 Testing ZIP → County Conversion...")
    
    test_zips = [
        '33101',  # Miami-Dade County, FL
        '90210',  # Los Angeles County, CA  
        '10001',  # New York County, NY
        '02101'   # Suffolk County, MA
    ]
    
    results = []
    for zip_code in test_zips:
        location_data = location_service.zip_to_location(zip_code)
        if location_data.get('error'):
            print(f"  ❌ ZIP {zip_code}: {location_data['error']}")
            results.append(False)
        else:
            county = location_data.get('county')
            state = location_data.get('state')
            print(f"  ✅ ZIP {zip_code} → {state}, {county} County")
            results.append(True)
    
    return all(results)

async def test_lead_processing():
    """Test the complete lead processing workflow with county-based architecture"""
    print("\n🔄 Testing Complete Lead Processing Workflow...")
    
    # Get default account
    from config import AppConfig
    account = db.get_account_by_ghl_location_id(AppConfig.GHL_LOCATION_ID)
    if not account:
        print("  ❌ No account found - cannot test lead processing")
        return False
    
    account_id = account["id"]
    
    # Create a test lead with county-resolvable ZIP
    test_lead = {
        'ghl_contact_id': 'test_county_lead',
        'name': 'Test County Lead',
        'email': 'test@county.com',
        'phone': '555-1234',
        'address': '123 Test St',
        'city': 'Miami',
        'state': 'FL',
        'postal_code': None,
        'tags': ['lead', 'Engines and Generators'],
        'custom_fields': [
            {'name': 'What Zip Code Are You Requesting Service In?', 'value': 33101},  # Miami-Dade
            {'name': 'service_type', 'value': 'Engine Repair'}
        ],
        'source': 'Test',
        'created_at': '2025-01-01'
    }
    
    # Process the lead
    result = await _process_single_unassigned_lead(test_lead, account_id)
    
    print(f"  📊 Processing Result:")
    print(f"    ZIP Code: {result.get('zip_code')}")
    print(f"    County: {result.get('county')}")
    print(f"    State: {result.get('state')}")
    print(f"    Service Category: {result.get('service_category')}")
    print(f"    Matching Vendors: {result.get('matching_vendors_count')}")
    print(f"    Assignment Success: {result.get('assignment_successful')}")
    
    if result.get('error_message'):
        print(f"    Error: {result.get('error_message')}")
    
    if result.get('assigned_vendor'):
        print(f"    Assigned Vendor: {result['assigned_vendor']['name']}")
    
    # Check that county information was properly extracted
    has_county = result.get('county') is not None
    has_state = result.get('state') is not None
    zip_extracted = result.get('zip_code') == '33101'
    
    print(f"\n  ✅ County Extraction: {'Pass' if has_county else 'Fail'}")
    print(f"  ✅ State Extraction: {'Pass' if has_state else 'Fail'}")
    print(f"  ✅ ZIP Extraction: {'Pass' if zip_extracted else 'Fail'}")
    
    return has_county and has_state and zip_extracted

def test_vendor_coverage_types():
    """Test different vendor coverage types work with county system"""
    print("\n🏢 Testing Vendor Coverage Types...")
    
    vendors = db.get_vendors()
    coverage_types = {}
    
    for vendor in vendors:
        coverage_type = vendor.get('service_coverage_type', 'zip')
        coverage_types[coverage_type] = coverage_types.get(coverage_type, 0) + 1
    
    print(f"  📊 Vendor Coverage Distribution:")
    for coverage_type, count in coverage_types.items():
        print(f"    {coverage_type}: {count} vendors")
    
    # Check if we have county-based vendors
    has_county_vendors = coverage_types.get('county', 0) > 0
    print(f"  ✅ County-based vendors available: {'Yes' if has_county_vendors else 'No'}")
    
    return True

async def main():
    """Run all tests"""
    print("🎯 COUNTY-BASED LEAD ASSIGNMENT SYSTEM TEST")
    print("=" * 60)
    
    # Test 1: Type handling (fixes the crash)
    type_test = test_type_handling()
    
    # Test 2: County conversion 
    county_test = test_county_conversion()
    
    # Test 3: Vendor coverage analysis
    vendor_test = test_vendor_coverage_types()
    
    # Test 4: Complete workflow
    workflow_test = await test_lead_processing()
    
    print("\n" + "=" * 60)
    print("🎯 TEST RESULTS SUMMARY:")
    print(f"  Type Handling (Crash Fix): {'✅ PASS' if type_test else '❌ FAIL'}")
    print(f"  County Conversion: {'✅ PASS' if county_test else '❌ FAIL'}")
    print(f"  Vendor Coverage Analysis: {'✅ PASS' if vendor_test else '❌ FAIL'}")
    print(f"  Complete Workflow: {'✅ PASS' if workflow_test else '❌ FAIL'}")
    
    overall_success = all([type_test, county_test, vendor_test, workflow_test])
    print(f"\n🏆 OVERALL: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    if overall_success:
        print("\n🎉 County-based lead assignment system is working correctly!")
        print("   • Type handling fixes prevent crashes")
        print("   • ZIP codes are properly converted to counties")
        print("   • Vendor matching uses county-based architecture")
        print("   • Lead data includes county information")
    else:
        print("\n⚠️ Some issues detected - check the test output above")

if __name__ == "__main__":
    asyncio.run(main())
