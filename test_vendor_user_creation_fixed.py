#!/usr/bin/env python3
"""
Test script for the FIXED vendor user creation process
Tests the corrected V1 API implementation for GHL user creation
"""

import asyncio
import json
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test configuration
BASE_URL = "http://127.0.0.1:8000"
WEBHOOK_URL = f"{BASE_URL}/api/v1/webhooks/ghl/vendor-user-creation"

def test_fixed_vendor_user_creation():
    """Test the FIXED vendor user creation webhook with V1 API"""
    print("\n🔧 Testing FIXED Vendor User Creation (V1 API)...")
    print(f"🎯 Webhook URL: {WEBHOOK_URL}")
    
    # Test payload simulating GHL workflow webhook
    test_payload = {
        "contact_id": "test_contact_12345",  # Replace with real contact ID for actual test
        "contactId": "test_contact_12345",   # Alternative field name
        "workflow_id": "test_workflow",
        "triggered_by": "vendor_approval_workflow"
    }
    
    print(f"📤 Sending test payload: {json.dumps(test_payload, indent=2)}")
    
    try:
        response = requests.post(WEBHOOK_URL, json=test_payload, timeout=30)
        
        print(f"📈 Response Status: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS: Fixed vendor user creation webhook working!")
            print(f"   🔑 Action: {result.get('action')}")
            print(f"   👤 User ID: {result.get('user_id')}")
            print(f"   📧 Vendor Email: {result.get('vendor_email')}")
            print(f"   🏢 Company: {result.get('vendor_company')}")
            print(f"   ⏱️  Processing Time: {result.get('processing_time_seconds')}s")
            print(f"   📬 Welcome Email Sent: {result.get('welcome_email_sent')}")
            return True
        else:
            print(f"❌ FAILED: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error Details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"   Raw Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"💥 Request Exception: {e}")
        return False

def test_health_check():
    """Test the health check to verify system status"""
    print("\n🏥 Testing Health Check...")
    
    health_url = f"{BASE_URL}/api/v1/webhooks/health"
    
    try:
        response = requests.get(health_url, timeout=10)
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ System Status: {health_data.get('status')}")
            print(f"   🔗 GHL Location ID: {health_data.get('ghl_location_id')}")
            print(f"   🏷️  Custom Fields: {health_data.get('custom_field_mappings')}")
            print(f"   📊 Database Status: {health_data.get('database_status')}")
            print(f"   🗂️  Field Reference: {health_data.get('field_reference_status')}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"💥 Health check error: {e}")
        return False

def check_environment_variables():
    """Check if required environment variables are set"""
    print("\n🔍 Checking Environment Variables...")
    
    required_vars = [
        'GHL_LOCATION_API',
        'GHL_PRIVATE_TOKEN', 
        'GHL_LOCATION_ID',
        'GHL_AGENCY_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values for logging
            masked_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
            print(f"   ✅ {var}: {masked_value}")
        else:
            print(f"   ❌ {var}: NOT SET")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️  Missing required environment variables: {', '.join(missing_vars)}")
        print("   Please set these in your .env file before running the test.")
        return False
    else:
        print(f"\n✅ All required environment variables are set!")
        return True

def main():
    """Main test function"""
    print("=" * 60)
    print("🔧 FIXED GHL V1 API VENDOR USER CREATION TEST")
    print("=" * 60)
    
    # Step 1: Check environment variables
    if not check_environment_variables():
        print("\n❌ Environment check failed. Please fix configuration before proceeding.")
        return
    
    # Step 2: Test health check
    health_ok = test_health_check()
    
    # Step 3: Test vendor user creation webhook
    print("\n" + "="*50)
    print("NOTE: This test uses a sample contact ID.")
    print("For a real test, replace 'test_contact_12345' with an actual GHL contact ID")
    print("that has vendor information (email, firstName, lastName, vendor_company_name).")
    print("="*50)
    
    creation_ok = test_fixed_vendor_user_creation()
    
    # Summary
    print("\n" + "="*60)
    print("📋 TEST SUMMARY")
    print("="*60)
    print(f"   🏥 Health Check: {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"   🔧 User Creation: {'✅ PASS' if creation_ok else '❌ FAIL'}")
    
    if health_ok and creation_ok:
        print(f"\n🎉 All tests passed! The V1 API fixes are working correctly.")
        print(f"   Ready for production use with real GHL contact IDs.")
    else:
        print(f"\n⚠️  Some tests failed. Please check the logs above for details.")
    
    print("\n🔗 Key Changes Made:")
    print("   1. Fixed API base URL to https://rest.gohighlevel.com")
    print("   2. Updated endpoint to /v1/users/")
    print("   3. Corrected payload structure with locationIds array")
    print("   4. Added proper V1 API error handling")
    print("   5. Enhanced webhook response handling")

if __name__ == "__main__":
    main()
