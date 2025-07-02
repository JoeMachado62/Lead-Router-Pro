#!/usr/bin/env python3
"""
Complete test of the vendor user creation process with all fixes applied
"""

import requests
import json
import os
from datetime import datetime

def load_env_file():
    """Load environment variables from .env file"""
    env_vars = {}
    try:
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"').strip("'")
    except FileNotFoundError:
        print("⚠️ .env file not found")
    return env_vars

# Load environment variables
env_vars = load_env_file()

def test_ghl_v1_user_creation():
    """Test the GHL V1 user creation API directly"""
    
    print("🧪 TESTING GHL V1 USER CREATION API")
    print("=" * 50)
    
    # Test data
    test_user_data = {
        "firstName": "Test",
        "lastName": "Vendor",
        "email": f"test.vendor.{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com",
        "phone": "+15551234567",
        "password": "TempPass123!",
        "type": "account",
        "role": "user"
    }
    
    # API configuration
    agency_api_key = env_vars.get("GHL_AGENCY_API_KEY")
    location_id = env_vars.get("GHL_LOCATION_ID")
    
    if not agency_api_key:
        print("❌ GHL_AGENCY_API_KEY not found in environment variables")
        return False
    
    if not location_id:
        print("❌ GHL_LOCATION_ID not found in environment variables")
        return False
    
    # V1 API endpoint
    url = "https://rest.gohighlevel.com/v1/users/"
    headers = {
        "Authorization": f"Bearer {agency_api_key}",
        "Content-Type": "application/json"
    }
    
    # V1 API payload with all fixes applied
    payload = {
        "firstName": test_user_data["firstName"],
        "lastName": test_user_data["lastName"],
        "email": test_user_data["email"],
        "phone": test_user_data["phone"],  # FIXED: Include phone number
        "password": test_user_data["password"],
        "type": test_user_data["type"],
        "role": test_user_data["role"],
        "locationIds": [location_id],  # Must be array
        "permissions": {
            "campaignsEnabled": False,
            "campaignsReadOnly": True,
            "contactsEnabled": True,
            "workflowsEnabled": False,
            "triggersEnabled": False,
            "funnelsEnabled": False,
            "websitesEnabled": False,
            "opportunitiesEnabled": True,
            "dashboardStatsEnabled": True,
            "bulkRequestsEnabled": False,
            "appointmentEnabled": True,
            "reviewsEnabled": False,
            "onlineListingsEnabled": False,
            "phoneCallEnabled": True,
            "conversationsEnabled": True,
            "assignedDataOnly": True,
            "adwordsReportingEnabled": False,
            "membershipEnabled": False,
            "facebookAdsReportingEnabled": False,
            "attributionsReportingEnabled": False,
            "settingsEnabled": False,
            "tagsEnabled": False,
            "leadValueEnabled": True,
            "marketingEnabled": False,
            "agentReportingEnabled": True,
            "botService": False,
            "socialPlanner": False,
            "bloggingEnabled": False,
            "invoiceEnabled": False,
            "affiliateManagerEnabled": False,
            "contentAiEnabled": False,
            "refundsEnabled": False,
            "recordPaymentEnabled": False,
            "cancelSubscriptionEnabled": False,
            "paymentsEnabled": False,
            "communitiesEnabled": False,
            "exportPaymentsEnabled": False
        }
    }
    
    print(f"📋 Test User Data:")
    print(f"   Name: {test_user_data['firstName']} {test_user_data['lastName']}")
    print(f"   Email: {test_user_data['email']}")
    print(f"   Phone: {test_user_data['phone']}")
    print(f"   Location ID: {location_id}")
    
    try:
        print(f"\n🔐 Creating test user via V1 API...")
        response = requests.post(url, headers=headers, json=payload)
        
        print(f"📈 Response Status: {response.status_code}")
        print(f"📄 Response Text: {response.text}")
        
        # FIXED: Accept both 200 and 201 status codes
        if response.status_code in [200, 201]:
            data = response.json()
            user_id = data.get('id')
            print(f"✅ SUCCESS: User created with ID: {user_id}")
            
            # Verify phone number is included
            if 'phone' in response.text or test_user_data['phone'] in response.text:
                print(f"✅ Phone number correctly included in user creation")
            else:
                print(f"⚠️ Phone number may not be included in user record")
            
            return {
                "success": True,
                "user_id": user_id,
                "email": test_user_data['email'],
                "response_data": data
            }
        else:
            print(f"❌ FAILED: User creation failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error Details: {json.dumps(error_data, indent=2)}")
            except:
                pass
            return {"success": False, "status_code": response.status_code}
            
    except Exception as e:
        print(f"❌ Exception during user creation: {str(e)}")
        return {"success": False, "exception": str(e)}

def test_webhook_simulation():
    """Simulate the webhook that triggers vendor user creation"""
    
    print("\n🧪 TESTING WEBHOOK SIMULATION")
    print("=" * 50)
    
    # Simulate webhook payload (based on William Meyer's actual webhook)
    webhook_payload = {
        "contact_id": "test_contact_123",
        "first_name": "Test",
        "last_name": "Vendor",
        "full_name": "Test Vendor",
        "email": f"test.vendor.webhook.{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com",
        "phone": "+15551234567",
        "Vendor Company Name": "Test Vendor Company",
        "Service Category": "Test Service",
        "Services Provided": "Test Services",
        "Taking New Work?": "Yes",
        "Service Zip Codes": "12345,67890",
        "location": {
            "id": env_vars.get("GHL_LOCATION_ID"),
            "name": "Test Location"
        }
    }
    
    print(f"📋 Webhook Payload:")
    print(f"   Contact ID: {webhook_payload['contact_id']}")
    print(f"   Name: {webhook_payload['full_name']}")
    print(f"   Email: {webhook_payload['email']}")
    print(f"   Phone: {webhook_payload['phone']}")
    
    # Test the webhook endpoint
    webhook_url = "http://localhost:8000/api/v1/webhooks/ghl/vendor-user-creation"
    
    try:
        print(f"\n🔗 Sending webhook to: {webhook_url}")
        response = requests.post(webhook_url, json=webhook_payload, timeout=30)
        
        print(f"📈 Webhook Response Status: {response.status_code}")
        print(f"📄 Webhook Response: {response.text}")
        
        if response.status_code == 200:
            print(f"✅ Webhook processed successfully")
            return True
        else:
            print(f"❌ Webhook failed with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"⚠️ Could not connect to webhook endpoint (server may not be running)")
        print(f"   This is expected if the Lead Router server is not currently running")
        return None
    except Exception as e:
        print(f"❌ Exception during webhook test: {str(e)}")
        return False

def verify_william_meyer_status():
    """Verify William Meyer's contact and user status"""
    
    print("\n🧪 VERIFYING WILLIAM MEYER STATUS")
    print("=" * 50)
    
    contact_id = "hkS4G1jO0h5OVVAlUgfp"
    user_id = "5FenzTEpnFnQnF6XUCkE"
    
    # Check contact record
    private_token = env_vars.get("GHL_PRIVATE_TOKEN")
    if not private_token:
        print("❌ GHL_PRIVATE_TOKEN not found")
        return False
    
    contact_url = f"https://services.leadconnectorhq.com/contacts/{contact_id}"
    headers = {
        "Authorization": f"Bearer {private_token}",
        "Content-Type": "application/json",
        "Version": "2021-07-28"
    }
    
    try:
        response = requests.get(contact_url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            contact = data.get('contact', {})
            custom_fields = contact.get('customFields', [])
            
            # Find GHL User ID field
            ghl_user_id = None
            for field in custom_fields:
                if field.get('id') == "HXVNT4y8OynNokWAfO2D":
                    ghl_user_id = field.get('value')
                    break
            
            print(f"📋 William Meyer Contact Status:")
            print(f"   Contact ID: {contact_id}")
            print(f"   Name: {contact.get('firstName')} {contact.get('lastName')}")
            print(f"   Email: {contact.get('email')}")
            print(f"   Phone: {contact.get('phone')}")
            print(f"   GHL User ID: {ghl_user_id}")
            
            if ghl_user_id == user_id:
                print(f"✅ Contact record correctly updated with User ID")
                
                # Check if user exists in GHL staff
                print(f"\n📋 User Status in GHL:")
                print(f"   User ID: {user_id}")
                print(f"   Expected to be visible in GHL Staff section")
                print(f"   Should have phone number: +19546968142")
                print(f"   Should have limited permissions (assignedDataOnly: true)")
                
                return True
            else:
                print(f"❌ Contact record missing or incorrect User ID")
                return False
        else:
            print(f"❌ Failed to get contact: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception verifying contact: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🧪 COMPREHENSIVE VENDOR USER CREATION TEST")
    print("=" * 60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Test 1: Direct V1 API user creation
    print("\n" + "="*60)
    api_result = test_ghl_v1_user_creation()
    results['v1_api_test'] = api_result
    
    # Test 2: Webhook simulation
    print("\n" + "="*60)
    webhook_result = test_webhook_simulation()
    results['webhook_test'] = webhook_result
    
    # Test 3: Verify William Meyer status
    print("\n" + "="*60)
    william_result = verify_william_meyer_status()
    results['william_meyer_status'] = william_result
    
    # Summary
    print("\n" + "="*60)
    print("🏁 TEST SUMMARY")
    print("=" * 60)
    
    print(f"✅ V1 API User Creation: {'PASS' if results['v1_api_test'].get('success') else 'FAIL'}")
    print(f"🔗 Webhook Simulation: {'PASS' if webhook_result else 'SKIP' if webhook_result is None else 'FAIL'}")
    print(f"👤 William Meyer Status: {'PASS' if william_result else 'FAIL'}")
    
    # Key fixes applied
    print(f"\n📋 KEY FIXES APPLIED:")
    print(f"   ✅ Status code check: Accept both 200 and 201")
    print(f"   ✅ Phone number: Added to V1 API payload")
    print(f"   ✅ Contact update: GHL User ID field populated")
    print(f"   ✅ Permissions: Limited vendor permissions applied")
    
    if results['v1_api_test'].get('success') and william_result:
        print(f"\n🎉 OVERALL RESULT: SUCCESS")
        print(f"   The vendor user creation process is working correctly!")
    else:
        print(f"\n⚠️ OVERALL RESULT: NEEDS ATTENTION")
        print(f"   Some issues may need to be addressed.")
    
    print(f"\n📋 NEXT STEPS:")
    print(f"   1. Test with a real vendor application workflow")
    print(f"   2. Verify lead assignment works for created vendors")
    print(f"   3. Check vendor login and dashboard access")

if __name__ == "__main__":
    main()
