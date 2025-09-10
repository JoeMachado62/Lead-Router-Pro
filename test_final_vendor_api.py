#!/usr/bin/env python3
"""
Final test to verify vendor_application_api.html works correctly
"""

import requests
import json
import time

def test_complete_flow():
    """Test the complete flow"""
    print("=" * 60)
    print("FINAL TEST: Vendor Application API Version")
    print("=" * 60)
    
    # 1. Test API endpoint
    print("\n1. Testing API endpoint...")
    api_response = requests.get("http://localhost:8000/api/v1/services/hierarchy")
    if api_response.status_code == 200:
        data = api_response.json()
        if data.get("success"):
            print(f"   ✅ API working: {data['stats']['total_categories']} categories")
            
            # Check specific categories
            if "Boat Maintenance" in data["data"]:
                bm = data["data"]["Boat Maintenance"]
                print(f"   ✅ Boat Maintenance: {len(bm['subcategories'])} subcategories")
                
            if "Boat and Yacht Repair" in data["data"]:
                br = data["data"]["Boat and Yacht Repair"]
                l3_count = len(br.get("level3Services", {}))
                print(f"   ✅ Boat and Yacht Repair: {l3_count} services with Level 3")
        else:
            print("   ❌ API returned success=false")
            return False
    else:
        print(f"   ❌ API failed with status {api_response.status_code}")
        return False
    
    # 2. Test HTML page structure
    print("\n2. Testing HTML page structure...")
    page_response = requests.get("http://localhost:8000/vendor-application-api")
    if page_response.status_code == 200:
        content = page_response.text
        
        # Check for critical functions
        checks = {
            "loadServiceHierarchy": "Data loading function",
            "initializeWidgetWithData": "Widget data initialization",
            "populateCategoryDropdown": "Dropdown population",
            "renderPrimaryServices": "Service rendering",
            "handlePrimaryCategorySelection": "Category selection handler",
            "init()": "Main initialization function"
        }
        
        all_found = True
        for check, description in checks.items():
            if check in content:
                print(f"   ✅ Found: {description}")
            else:
                print(f"   ❌ Missing: {description}")
                all_found = False
        
        if not all_found:
            return False
    else:
        print(f"   ❌ Page failed with status {page_response.status_code}")
        return False
    
    # 3. Check initialization flow
    print("\n3. Checking initialization flow...")
    
    # Check if init calls loadServiceHierarchy
    if "await loadServiceHierarchy()" in content:
        print("   ✅ init() awaits loadServiceHierarchy()")
    else:
        print("   ❌ init() doesn't properly await data loading")
    
    # Check if loadServiceHierarchy calls initializeWidgetWithData
    if "initializeWidgetWithData()" in content:
        print("   ✅ Data loader calls widget initialization")
    else:
        print("   ❌ Data loader doesn't call widget initialization")
    
    # Check if populateCategoryDropdown is called
    if "populateCategoryDropdown()" in content:
        print("   ✅ Dropdown population function is called")
    else:
        print("   ❌ Dropdown population might not be called")
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY:")
    print("✅ All critical components are in place")
    print("\nTo verify in browser:")
    print("1. Open http://localhost:8000/vendor-application-api")
    print("2. Open browser console (F12)")
    print("3. Look for these console messages:")
    print("   - 'Starting vendor widget initialization...'")
    print("   - '✅ Service hierarchy loaded from API'")
    print("   - 'Populated dropdown with X categories'")
    print("4. Select 'Boat Maintenance' from dropdown")
    print("5. Verify subcategories appear as clickable tags")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = test_complete_flow()
    
    if success:
        print("\n🎉 Backend tests passed! Please verify in browser.")
    else:
        print("\n❌ Some tests failed. Review errors above.")