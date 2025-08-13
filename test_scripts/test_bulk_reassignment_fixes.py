#!/usr/bin/env python3
"""
Test script to verify bulk lead reassignment fixes
"""
import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "test_key"  # Replace with actual if needed

def test_bulk_reassignment():
    """Test the bulk lead reassignment endpoint"""
    print("\n" + "="*60)
    print("TESTING BULK LEAD REASSIGNMENT FIXES")
    print("="*60)
    
    # Test 1: Check if the service categories are being properly mapped
    print("\n1. Testing service category mapping...")
    response = requests.get(f"{BASE_URL}/api/v1/webhooks/service-categories")
    if response.status_code == 200:
        categories = response.json()
        print(f"✅ Found {len(categories)} service categories")
        # Check if we have the proper categories, not just "Boater Resources"
        unique_categories = set(categories)
        if len(unique_categories) > 5:
            print(f"✅ Good variety of categories: {list(unique_categories)[:5]}...")
        else:
            print(f"⚠️ Limited categories found: {unique_categories}")
    else:
        print(f"❌ Failed to get service categories: {response.status_code}")
    
    # Test 2: Check database leads for proper field population
    print("\n2. Checking database lead fields...")
    response = requests.get(f"{BASE_URL}/api/v1/simple-admin/stats")
    if response.status_code == 200:
        stats = response.json()
        print(f"✅ Database has {stats.get('total_leads', 0)} leads")
        print(f"   Vendors: {stats.get('total_vendors', 0)}")
        print(f"   Unassigned leads: {stats.get('unassigned_leads', 0)}")
    else:
        print(f"❌ Failed to get stats: {response.status_code}")
    
    # Test 3: Test the bulk reassignment endpoint
    print("\n3. Testing bulk lead reassignment endpoint...")
    print("   This will attempt to process unassigned leads...")
    
    # Make the request to trigger bulk reassignment
    response = requests.post(
        f"{BASE_URL}/api/v1/routing/process-unassigned-leads",
        json={}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Bulk reassignment completed!")
        print(f"   Total unassigned: {result.get('total_unassigned', 0)}")
        print(f"   Successfully processed: {result.get('successfully_processed', 0)}")
        print(f"   Failed: {result.get('failed', 0)}")
        
        # Show details of processed leads
        if result.get('lead_results'):
            print("\n   Lead Processing Details:")
            for i, lead in enumerate(result['lead_results'][:5], 1):  # Show first 5
                print(f"   {i}. {lead.get('customer_name', 'Unknown')}:")
                print(f"      - Service Category: {lead.get('service_category', 'None')}")
                print(f"      - ZIP: {lead.get('zip_code', 'None')}")
                print(f"      - Assigned: {lead.get('assignment_successful', False)}")
                if lead.get('assigned_vendor'):
                    print(f"      - Vendor: {lead['assigned_vendor'].get('name', 'Unknown')}")
                if lead.get('error_message'):
                    print(f"      - Error: {lead['error_message']}")
        
        # Check for common errors
        if result.get('lead_results'):
            errors = [lead.get('error_message', '') for lead in result['lead_results'] if lead.get('error_message')]
            if errors:
                print("\n   Common Errors Found:")
                unique_errors = set(errors)
                for error in list(unique_errors)[:5]:
                    count = errors.count(error)
                    print(f"   - {error} (occurred {count} times)")
        
    else:
        print(f"❌ Bulk reassignment failed: {response.status_code}")
        try:
            error_detail = response.json()
            print(f"   Error: {error_detail}")
        except:
            print(f"   Response: {response.text[:200]}")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)

def check_specific_lead():
    """Check a specific lead to see if fields are populated correctly"""
    print("\n4. Checking specific lead data quality...")
    
    # This would need to be implemented with actual database access
    # For now, we'll use the admin stats as a proxy
    
    response = requests.get(f"{BASE_URL}/api/v1/routing/configuration")
    if response.status_code == 200:
        config = response.json()
        print(f"✅ Routing configuration loaded")
        print(f"   Smart routing enabled: {config.get('smart_routing_enabled', False)}")
        print(f"   Use weighted selection: {config.get('use_weighted_selection', False)}")
    else:
        print(f"❌ Failed to get routing configuration")

if __name__ == "__main__":
    print(f"Starting test at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run the tests
    test_bulk_reassignment()
    check_specific_lead()
    
    print(f"\nTest completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")