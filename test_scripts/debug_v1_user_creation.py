#!/usr/bin/env python3
"""
Debug script to test V1 API user creation directly
This will help isolate the exact issue with the GHL V1 API
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_v1_user_creation():
    """Test V1 API user creation with minimal payload"""
    
    # Get credentials from environment
    agency_api_key = os.getenv('GHL_AGENCY_API_KEY')
    location_id = os.getenv('GHL_LOCATION_ID')
    
    if not agency_api_key:
        print("❌ GHL_AGENCY_API_KEY not found in environment")
        return False
        
    if not location_id:
        print("❌ GHL_LOCATION_ID not found in environment")
        return False
    
    print(f"🔑 Using Agency API Key: {agency_api_key[:10]}...{agency_api_key[-4:]}")
    print(f"🏢 Using Location ID: {location_id}")
    
    # V1 API endpoint
    url = "https://rest.gohighlevel.com/v1/users/"
    
    # V1 headers
    headers = {
        "Authorization": f"Bearer {agency_api_key}",
        "Content-Type": "application/json"
    }
    
    # Test with minimal payload first
    minimal_payload = {
        "firstName": "Test",
        "lastName": "User", 
        "email": "testuser123@example.com",  # Use a test email
        "password": "TempPass123!",
        "type": "account",
        "role": "user",
        "locationIds": [location_id]
    }
    
    print(f"\n🧪 Testing V1 API with MINIMAL payload:")
    print(f"📋 URL: {url}")
    print(f"📋 Headers: {headers}")
    print(f"📋 Payload: {json.dumps(minimal_payload, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=minimal_payload)
        
        print(f"\n📈 Response Status: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        print(f"📄 Response Text: {response.text}")
        
        if response.status_code == 201:
            print("✅ SUCCESS: Minimal payload worked!")
            
            # Try to get the created user
            try:
                response_data = response.json()
                user_id = response_data.get('user', {}).get('id')
                if user_id:
                    print(f"👤 Created user ID: {user_id}")
                    
                    # Clean up - delete the test user
                    delete_url = f"https://rest.gohighlevel.com/v1/users/{user_id}"
                    delete_response = requests.delete(delete_url, headers=headers)
                    if delete_response.status_code in [200, 204]:
                        print("🧹 Test user cleaned up successfully")
                    else:
                        print(f"⚠️ Failed to delete test user: {delete_response.status_code}")
            except:
                print("⚠️ Could not parse response JSON")
            
            return True
        else:
            print("❌ FAILED: Even minimal payload failed")
            
            # Try to parse error details
            try:
                error_data = response.json()
                print(f"📋 Error JSON: {error_data}")
            except:
                print("📋 Could not parse error as JSON")
            
            return False
            
    except Exception as e:
        print(f"💥 Exception: {e}")
        return False

def test_agency_api_permissions():
    """Test if the agency API key has the right permissions"""
    
    agency_api_key = os.getenv('GHL_AGENCY_API_KEY')
    if not agency_api_key:
        print("❌ GHL_AGENCY_API_KEY not found")
        return False
    
    # Test various V1 endpoints to check permissions
    endpoints_to_test = [
        ("GET", "https://rest.gohighlevel.com/v1/users", {}),
        ("GET", "https://rest.gohighlevel.com/v1/locations", {}),
    ]
    
    headers = {
        "Authorization": f"Bearer {agency_api_key}",
        "Content-Type": "application/json"
    }
    
    print(f"\n🔍 Testing Agency API Key Permissions...")
    
    for method, url, params in endpoints_to_test:
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params)
            else:
                response = requests.request(method, url, headers=headers, json=params)
            
            print(f"📍 {method} {url}: {response.status_code}")
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   ✅ Success - Response keys: {list(data.keys())}")
                except:
                    print(f"   ✅ Success - Response length: {len(response.text)}")
            elif response.status_code == 401:
                print(f"   ❌ Unauthorized - API key may be invalid")
            elif response.status_code == 403:
                print(f"   ❌ Forbidden - API key lacks permissions")
            else:
                print(f"   ⚠️ Other error: {response.text[:100]}")
                
        except Exception as e:
            print(f"   💥 Exception: {e}")

def test_location_id_validity():
    """Test if the location ID is valid"""
    
    location_id = os.getenv('GHL_LOCATION_ID')
    agency_api_key = os.getenv('GHL_AGENCY_API_KEY')
    
    if not location_id or not agency_api_key:
        print("❌ Missing location ID or agency API key")
        return False
    
    print(f"\n🏢 Testing Location ID Validity: {location_id}")
    
    # Try to get location details
    url = f"https://rest.gohighlevel.com/v1/locations/{location_id}"
    headers = {
        "Authorization": f"Bearer {agency_api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"📈 Location lookup response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Location is valid: {data.get('location', {}).get('name', 'Unknown')}")
            return True
        else:
            print(f"❌ Invalid location or no access: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 Exception checking location: {e}")
        return False

def main():
    """Run all debug tests"""
    print("=" * 60)
    print("🔧 GHL V1 API USER CREATION DEBUG")
    print("=" * 60)
    
    # Test 1: Agency API permissions
    permissions_ok = test_agency_api_permissions()
    
    # Test 2: Location ID validity
    location_ok = test_location_id_validity()
    
    # Test 3: Minimal user creation
    if permissions_ok and location_ok:
        creation_ok = test_v1_user_creation()
    else:
        print("\n⚠️ Skipping user creation test due to permission/location issues")
        creation_ok = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 DEBUG SUMMARY")
    print("=" * 60)
    print(f"   🔑 Agency API Permissions: {'✅ OK' if permissions_ok else '❌ FAIL'}")
    print(f"   🏢 Location ID Valid: {'✅ OK' if location_ok else '❌ FAIL'}")
    print(f"   👤 User Creation: {'✅ OK' if creation_ok else '❌ FAIL'}")
    
    if creation_ok:
        print(f"\n🎉 V1 API user creation is working! The issue may be in the payload data.")
    else:
        print(f"\n⚠️ V1 API user creation is failing. Check the logs above for details.")
        
    print(f"\n💡 Next steps:")
    if not permissions_ok:
        print(f"   - Verify GHL_AGENCY_API_KEY has user management permissions")
    if not location_ok:
        print(f"   - Verify GHL_LOCATION_ID is correct and agency has access")
    if permissions_ok and location_ok and not creation_ok:
        print(f"   - Check if there are additional validation requirements")
        print(f"   - Verify the email format and other field validations")

if __name__ == "__main__":
    main()
