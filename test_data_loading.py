#!/usr/bin/env python3
"""
Simple test to check if vendor_application_api.html loads data correctly
"""

import requests
import re
import json

def test_page_structure():
    """Test if the page has the correct structure"""
    print("Testing vendor_application_api.html structure...")
    
    response = requests.get("http://localhost:8000/vendor-application-api")
    if response.status_code != 200:
        print(f"❌ Failed to load page: {response.status_code}")
        return False
    
    content = response.text
    
    # Check for key functions
    checks = {
        "loadServiceHierarchy": "Data loading function",
        "initializeWidgetWithData": "Widget initialization with data",
        "populateCategoryDropdown": "Dropdown population function",
        "renderPrimaryServices": "Service rendering function",
        "SERVICE_CATEGORIES": "Service categories variable"
    }
    
    all_good = True
    for check, description in checks.items():
        if check in content:
            print(f"✅ Found: {description}")
        else:
            print(f"❌ Missing: {description}")
            all_good = False
    
    # Check for the init function
    if "function init()" in content:
        print("✅ Found init function")
        
        # Check if it calls loadServiceHierarchy
        init_match = re.search(r'function init\(\)\s*{([^}]+)}', content, re.DOTALL)
        if init_match:
            init_body = init_match.group(1)
            if "loadServiceHierarchy" in init_body:
                print("✅ init() calls loadServiceHierarchy()")
            else:
                print("❌ init() does NOT call loadServiceHierarchy()")
                all_good = False
    else:
        print("❌ init function not found")
        all_good = False
    
    return all_good

def test_api():
    """Test the API endpoint"""
    print("\nTesting API endpoint...")
    
    response = requests.get("http://localhost:8000/api/v1/services/hierarchy")
    if response.status_code != 200:
        print(f"❌ API failed: {response.status_code}")
        return False
    
    data = response.json()
    if data.get("success"):
        print(f"✅ API working: {data['stats']['total_categories']} categories")
        
        # Check a sample category
        if "Boat Maintenance" in data.get("data", {}):
            bm = data["data"]["Boat Maintenance"]
            print(f"✅ Boat Maintenance has {len(bm.get('subcategories', []))} subcategories")
            return True
    
    print("❌ API returned invalid data")
    return False

def main():
    print("=" * 60)
    print("VENDOR APPLICATION API - DATA LOADING TEST")
    print("=" * 60)
    
    page_ok = test_page_structure()
    api_ok = test_api()
    
    print("\n" + "=" * 60)
    if page_ok and api_ok:
        print("✅ Structure looks good!")
        print("\nPotential issues to check:")
        print("1. Ensure browser console shows no errors")
        print("2. Check if SERVICE_CATEGORIES is populated after page load")
        print("3. Verify dropdown gets populated with categories")
    else:
        print("❌ Issues found - review the errors above")
    print("=" * 60)

if __name__ == "__main__":
    main()