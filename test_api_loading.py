#!/usr/bin/env python3
"""
Test script to verify the vendor application API version loads correctly
"""

import requests
import json
import time

def test_api_endpoint():
    """Test the services hierarchy API endpoint"""
    print("Testing /api/v1/services/hierarchy endpoint...")
    
    try:
        response = requests.get("http://localhost:8000/api/v1/services/hierarchy")
        data = response.json()
        
        if data.get("success"):
            print(f"✅ API endpoint working!")
            print(f"   - Total categories: {data['stats']['total_categories']}")
            print(f"   - Categories with Level 3: {data['stats']['categories_with_level3']}")
            
            # Check a sample category
            if "Boat Maintenance" in data.get("data", {}):
                boat_maint = data["data"]["Boat Maintenance"]
                print(f"\n📋 Sample Category: Boat Maintenance")
                print(f"   - Subcategories: {len(boat_maint.get('subcategories', []))}")
                print(f"   - Has Level 3 services: {'level3Services' in boat_maint}")
                
                # Check for specific subcategory
                if "Boat Detailing" in boat_maint.get("subcategories", []):
                    print(f"   ✅ Found 'Boat Detailing' subcategory")
                    
                    # Check Level 3 services
                    if "Boat Detailing" in boat_maint.get("level3Services", {}):
                        level3 = boat_maint["level3Services"]["Boat Detailing"]
                        print(f"   ✅ Level 3 services for Boat Detailing: {level3[:3]}...")
            
            return True
        else:
            print(f"❌ API returned success=false")
            return False
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False

def test_vendor_app_page():
    """Test that the vendor application API page loads"""
    print("\nTesting /vendor-application-api page...")
    
    try:
        response = requests.get("http://localhost:8000/vendor-application-api")
        
        if response.status_code == 200:
            content = response.text
            
            # Check for key functions
            checks = {
                "loadServiceHierarchy": "API loading function",
                "fetch('/api/v1/services/hierarchy')": "API fetch call",
                "initializeWidget": "Widget initialization",
                "FALLBACK_CATEGORIES": "Fallback data"
            }
            
            all_good = True
            for check, description in checks.items():
                if check in content:
                    print(f"   ✅ Found {description}")
                else:
                    print(f"   ❌ Missing {description}")
                    all_good = False
            
            return all_good
        else:
            print(f"❌ Page returned status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing page: {e}")
        return False

def main():
    print("=" * 60)
    print("VENDOR APPLICATION API VERSION TEST")
    print("=" * 60)
    
    # Test API endpoint
    api_ok = test_api_endpoint()
    
    # Test vendor application page
    page_ok = test_vendor_app_page()
    
    print("\n" + "=" * 60)
    if api_ok and page_ok:
        print("✅ ALL TESTS PASSED!")
        print("\nThe vendor application API version is ready to use.")
        print("Access it at: http://localhost:8000/vendor-application-api")
    else:
        print("❌ SOME TESTS FAILED")
        print("Please check the errors above.")
    print("=" * 60)

if __name__ == "__main__":
    main()