#!/usr/bin/env python3
"""
Comprehensive GHL JWT Token Diagnostic Script
Identifies and fixes the 401 JWT authentication issue preventing lead assignment
"""

import os
import sys
import json
import base64
import requests
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Add the Lead-Router-Pro directory to the path
sys.path.insert(0, '/root/Lead-Router-Pro')

# Load environment variables from .env file
def load_env_file(env_path: str = '.env'):
    """Load environment variables from .env file"""
    if not os.path.exists(env_path):
        print(f"❌ .env file not found at {env_path}")
        return
    
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                # Remove quotes if present
                value = value.strip('"\'')
                os.environ[key] = value
    
    print(f"✅ Loaded environment variables from {env_path}")

# Load the .env file
load_env_file()

from config import AppConfig
from api.services.ghl_api import GoHighLevelAPI

def decode_jwt_payload(token: str) -> Optional[Dict[str, Any]]:
    """Decode JWT payload to examine expiration and other details"""
    try:
        # JWT format: header.payload.signature
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        # Decode payload (second part)
        payload_encoded = parts[1]
        # Add padding if needed
        payload_encoded += '=' * (4 - len(payload_encoded) % 4)
        
        payload_decoded = base64.urlsafe_b64decode(payload_encoded)
        payload_json = json.loads(payload_decoded)
        
        return payload_json
    except Exception as e:
        print(f"❌ Error decoding JWT: {e}")
        return None

def check_jwt_expiration(payload: Dict[str, Any]) -> bool:
    """Check if JWT token is expired"""
    try:
        # JWT 'iat' is issued at time, 'exp' is expiration time
        iat = payload.get('iat')
        exp = payload.get('exp')
        
        current_time = datetime.now(timezone.utc).timestamp()
        
        print(f"🔍 JWT Token Analysis:")
        if iat:
            iat_date = datetime.fromtimestamp(iat / 1000 if iat > 2000000000 else iat, tz=timezone.utc)
            print(f"  📅 Issued At: {iat_date}")
        
        if exp:
            exp_date = datetime.fromtimestamp(exp / 1000 if exp > 2000000000 else exp, tz=timezone.utc)
            print(f"  ⏰ Expires At: {exp_date}")
            
            is_expired = current_time > (exp / 1000 if exp > 2000000000 else exp)
            print(f"  {'❌ EXPIRED' if is_expired else '✅ VALID'}")
            return not is_expired
        else:
            print(f"  ⚠️ No expiration time found in token")
            return True
            
    except Exception as e:
        print(f"❌ Error checking expiration: {e}")
        return False

def test_ghl_token_directly(token: str, location_id: str) -> Dict[str, Any]:
    """Test GHL token directly with a simple API call"""
    try:
        url = "https://services.leadconnectorhq.com/contacts/"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Version': '2021-07-28'
        }
        params = {
            'locationId': location_id,
            'limit': 1
        }
        
        print(f"🔍 Testing token directly...")
        print(f"  📍 URL: {url}")
        print(f"  🔑 Token: {token[:20]}...{token[-10:]}")
        print(f"  🏢 Location ID: {location_id}")
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        result = {
            'status_code': response.status_code,
            'success': response.status_code == 200,
            'response_text': response.text,
            'headers': dict(response.headers)
        }
        
        print(f"  📈 Response: {response.status_code}")
        print(f"  {'✅ SUCCESS' if result['success'] else '❌ FAILED'}")
        
        if not result['success']:
            print(f"  📄 Error Response: {response.text}")
        
        return result
        
    except Exception as e:
        print(f"❌ Exception testing token: {e}")
        return {'success': False, 'error': str(e)}

def test_contact_update_endpoint(token: str, location_id: str) -> Dict[str, Any]:
    """Test the specific contact update endpoint that's failing"""
    try:
        # Use a test contact ID (this will fail but we can see the auth error)
        test_contact_id = "test_contact_id"
        url = f'https://services.leadconnectorhq.com/contacts/{test_contact_id}'
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Version': '2021-07-28'
        }
        
        update_data = {
            'customFields': {
                'test_field': 'test_value'
            }
        }
        
        print(f"🔍 Testing contact update endpoint...")
        print(f"  📍 URL: {url}")
        
        response = requests.put(url, json=update_data, headers=headers, timeout=10)
        
        result = {
            'status_code': response.status_code,
            'success': response.status_code in [200, 404],  # 404 is expected for fake contact
            'response_text': response.text,
            'auth_works': response.status_code != 401
        }
        
        print(f"  📈 Response: {response.status_code}")
        print(f"  {'✅ AUTH WORKS' if result['auth_works'] else '❌ AUTH FAILED'}")
        
        if response.status_code == 401:
            print(f"  🚨 401 ERROR: {response.text}")
        elif response.status_code == 404:
            print(f"  ✅ 404 Expected (fake contact ID) - Auth is working")
        
        return result
        
    except Exception as e:
        print(f"❌ Exception testing update endpoint: {e}")
        return {'success': False, 'error': str(e)}

def diagnose_ghl_authentication():
    """Main diagnostic function"""
    print("=" * 80)
    print("🔍 GHL JWT TOKEN DIAGNOSTIC REPORT")
    print("=" * 80)
    
    # 1. Check environment variables
    print("\n1. 📋 Environment Configuration:")
    print(f"   GHL_LOCATION_API: {'✅ SET' if AppConfig.GHL_LOCATION_API else '❌ MISSING'}")
    print(f"   GHL_PRIVATE_TOKEN: {'✅ SET' if AppConfig.GHL_PRIVATE_TOKEN else '❌ MISSING'}")
    print(f"   GHL_LOCATION_ID: {'✅ SET' if AppConfig.GHL_LOCATION_ID else '❌ MISSING'}")
    print(f"   GHL_AGENCY_API_KEY: {'✅ SET' if AppConfig.GHL_AGENCY_API_KEY else '❌ MISSING'}")
    print(f"   GHL_COMPANY_ID: {'✅ SET' if AppConfig.GHL_COMPANY_ID else '❌ MISSING'}")
    
    # 2. Decode and analyze JWT tokens
    print("\n2. 🔍 JWT Token Analysis:")
    
    # Analyze Location API token
    if AppConfig.GHL_LOCATION_API:
        print(f"\n   📍 Location API Token Analysis:")
        payload = decode_jwt_payload(AppConfig.GHL_LOCATION_API)
        if payload:
            print(f"      📋 Payload: {json.dumps(payload, indent=6)}")
            is_valid = check_jwt_expiration(payload)
            if not is_valid:
                print(f"      🚨 LOCATION API TOKEN IS EXPIRED!")
        else:
            print(f"      ❌ Could not decode Location API token")
    
    # Analyze Private Token
    if AppConfig.GHL_PRIVATE_TOKEN:
        print(f"\n   🔐 Private Token Analysis:")
        if AppConfig.GHL_PRIVATE_TOKEN.startswith('pit-'):
            print(f"      ✅ Private Token appears to be a PIT token (correct format)")
        else:
            print(f"      ⚠️ Private Token format unexpected")
    
    # Analyze Agency API Key
    if AppConfig.GHL_AGENCY_API_KEY:
        print(f"\n   🏢 Agency API Key Analysis:")
        payload = decode_jwt_payload(AppConfig.GHL_AGENCY_API_KEY)
        if payload:
            print(f"      📋 Payload: {json.dumps(payload, indent=6)}")
            is_valid = check_jwt_expiration(payload)
            if not is_valid:
                print(f"      🚨 AGENCY API KEY IS EXPIRED!")
        else:
            print(f"      ❌ Could not decode Agency API key")
    
    # 3. Test tokens directly
    print("\n3. 🧪 Token Testing:")
    
    # Test Location API token
    if AppConfig.GHL_LOCATION_API and AppConfig.GHL_LOCATION_ID:
        print(f"\n   📍 Testing Location API Token:")
        result = test_ghl_token_directly(AppConfig.GHL_LOCATION_API, AppConfig.GHL_LOCATION_ID)
        if not result.get('success'):
            print(f"      🚨 Location API token test FAILED")
    
    # Test Private Token
    if AppConfig.GHL_PRIVATE_TOKEN and AppConfig.GHL_LOCATION_ID:
        print(f"\n   🔐 Testing Private Token:")
        result = test_ghl_token_directly(AppConfig.GHL_PRIVATE_TOKEN, AppConfig.GHL_LOCATION_ID)
        if not result.get('success'):
            print(f"      🚨 Private token test FAILED")
    
    # Test Agency API Key
    if AppConfig.GHL_AGENCY_API_KEY and AppConfig.GHL_LOCATION_ID:
        print(f"\n   🏢 Testing Agency API Key:")
        result = test_ghl_token_directly(AppConfig.GHL_AGENCY_API_KEY, AppConfig.GHL_LOCATION_ID)
        if not result.get('success'):
            print(f"      🚨 Agency API key test FAILED")
    
    # 4. Test contact update endpoint specifically
    print("\n4. 🎯 Testing Contact Update Endpoint (the failing one):")
    
    if AppConfig.GHL_LOCATION_API:
        print(f"\n   📍 Testing with Location API token:")
        result = test_contact_update_endpoint(AppConfig.GHL_LOCATION_API, AppConfig.GHL_LOCATION_ID)
        if not result.get('auth_works'):
            print(f"      🚨 Contact update with Location API token FAILED")
    
    if AppConfig.GHL_PRIVATE_TOKEN:
        print(f"\n   🔐 Testing with Private token:")
        result = test_contact_update_endpoint(AppConfig.GHL_PRIVATE_TOKEN, AppConfig.GHL_LOCATION_ID)
        if not result.get('auth_works'):
            print(f"      🚨 Contact update with Private token FAILED")
    
    # 5. Test with GHL API class
    print("\n5. 🔧 Testing with GHL API Class:")
    try:
        ghl_api = GoHighLevelAPI(
            location_api_key=AppConfig.GHL_LOCATION_API,
            private_token=AppConfig.GHL_PRIVATE_TOKEN,
            location_id=AppConfig.GHL_LOCATION_ID,
            agency_api_key=AppConfig.GHL_AGENCY_API_KEY,
            company_id=AppConfig.GHL_COMPANY_ID
        )
        
        test_result = ghl_api.test_location_access()
        print(f"   📈 API Class Test Result: {test_result}")
        
        if test_result.get('can_access'):
            print(f"   ✅ GHL API class can access location")
        else:
            print(f"   ❌ GHL API class cannot access location")
            
    except Exception as e:
        print(f"   ❌ Error testing GHL API class: {e}")
    
    # 6. Recommendations
    print("\n6. 💡 Recommendations:")
    print("   Based on the 401 'Invalid JWT' errors, likely issues:")
    print("   1. 🔄 JWT tokens may be expired (check expiration times above)")
    print("   2. 🔑 Wrong token being used for contact updates")
    print("   3. 🏢 Location ID mismatch")
    print("   4. 📋 Missing scopes/permissions on tokens")
    print("\n   🚀 Next Steps:")
    print("   1. Check GHL dashboard for new/refreshed tokens")
    print("   2. Verify token permissions include contact write access")
    print("   3. Test with different token types (Location API vs Private Token)")
    print("   4. Check if vendor GHL contact IDs are valid")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    diagnose_ghl_authentication()
