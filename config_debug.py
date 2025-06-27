#!/usr/bin/env python3
"""
Debug script to check the actual configuration being used by the running application
"""

import sys
import os
import requests
import json
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.getcwd())

def test_live_application_config():
    """Test what configuration the live application is actually using"""
    print("🔍 TESTING LIVE APPLICATION CONFIGURATION")
    print("=" * 60)
    
    # Test if the server is running
    base_url = "http://localhost:8000"
    health_url = f"{base_url}/api/v1/webhooks/health"
    
    try:
        response = requests.get(health_url, timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and responding")
        else:
            print(f"⚠️ Server responded with status {response.status_code}")
    except requests.exceptions.RequestException:
        print("❌ Server is not running or not responding")
        print("   Start the server with: python main_working_final.py")
        return False
    
    return True

def test_config_loading():
    """Test configuration loading in the current process"""
    print("\n🔧 TESTING CONFIG LOADING IN CURRENT PROCESS")
    print("=" * 60)
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        from config import AppConfig
        
        print("📋 Configuration Values from AppConfig:")
        print(f"   🏢 AppConfig.GHL_COMPANY_ID: '{AppConfig.GHL_COMPANY_ID}'")
        print(f"   📍 AppConfig.GHL_LOCATION_ID: '{AppConfig.GHL_LOCATION_ID}'")
        print(f"   🔑 AppConfig.GHL_PRIVATE_TOKEN: {'Set' if AppConfig.GHL_PRIVATE_TOKEN else 'Missing'}")
        print(f"   🏛️ AppConfig.GHL_AGENCY_API_KEY: {'Set' if AppConfig.GHL_AGENCY_API_KEY else 'Missing'}")
        
        # Check if values are correct
        if AppConfig.GHL_COMPANY_ID == "rKXCHVr7vEFLD0e3iDq7":
            print("✅ Company ID is CORRECT in config")
        elif AppConfig.GHL_COMPANY_ID == AppConfig.GHL_LOCATION_ID:
            print("❌ Company ID equals Location ID - THIS IS THE PROBLEM!")
            print(f"   Both are set to: {AppConfig.GHL_COMPANY_ID}")
        else:
            print(f"⚠️ Company ID is unexpected: {AppConfig.GHL_COMPANY_ID}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return False

def test_ghl_api_initialization():
    """Test how GHL API gets initialized with the configuration"""
    print("\n🔌 TESTING GHL API INITIALIZATION")
    print("=" * 60)
    
    try:
        from config import AppConfig
        from api.services.ghl_api import GoHighLevelAPI
        
        print("🔧 Initializing GoHighLevelAPI with AppConfig values...")
        
        ghl_client = GoHighLevelAPI(
            private_token=AppConfig.GHL_PRIVATE_TOKEN,
            location_id=AppConfig.GHL_LOCATION_ID,
            agency_api_key=AppConfig.GHL_AGENCY_API_KEY,
            company_id=AppConfig.GHL_COMPANY_ID
        )
        
        print("📋 GHL API Client Values:")
        print(f"   🏢 ghl_client.company_id: '{ghl_client.company_id}'")
        print(f"   📍 ghl_client.location_id: '{ghl_client.location_id}'")
        print(f"   🔑 ghl_client.private_token: {'Set' if ghl_client.private_token else 'Missing'}")
        print(f"   🏛️ ghl_client.agency_api_key: {'Set' if ghl_client.agency_api_key else 'Missing'}")
        
        # This is the smoking gun - check what the GHL client actually has
        if ghl_client.company_id == "rKXCHVr7vEFLD0e3iDq7":
            print("✅ GHL Client has CORRECT Company ID")
        elif ghl_client.company_id == ghl_client.location_id:
            print("❌ GHL Client Company ID equals Location ID - PROBLEM CONFIRMED!")
            print(f"   Both are: {ghl_client.company_id}")
        else:
            print(f"⚠️ GHL Client has unexpected Company ID: {ghl_client.company_id}")
        
        return ghl_client
        
    except Exception as e:
        print(f"❌ Error initializing GHL API: {e}")
        return None

def test_v2_payload_generation(ghl_client):
    """Test what payload gets generated for V2 API"""
    print("\n📦 TESTING V2 API PAYLOAD GENERATION")
    print("=" * 60)
    
    if not ghl_client:
        print("❌ Cannot test payload - GHL client not available")
        return
    
    # Mock user data for testing
    test_user_data = {
        "firstName": "Test",
        "lastName": "Debug",
        "email": "debug@test.com",
        "phone": "+1234567890",
        "type": "account",
        "role": "user"
    }
    
    try:
        # Check if we can call create_user_v2 method
        if hasattr(ghl_client, 'create_user_v2'):
            print("🔍 Simulating V2 API payload creation...")
            
            # Show what values would be used
            print(f"📋 Values that would be used in V2 payload:")
            print(f"   companyId: '{ghl_client.company_id}'")
            print(f"   locationIds: ['{ghl_client.location_id}']")
            print(f"   firstName: '{test_user_data['firstName']}'")
            print(f"   lastName: '{test_user_data['lastName']}'")
            print(f"   email: '{test_user_data['email']}'")
            
            # This is what would appear in the API request
            if ghl_client.company_id == "rKXCHVr7vEFLD0e3iDq7":
                print("✅ V2 API payload would use CORRECT Company ID")
            else:
                print(f"❌ V2 API payload would use WRONG Company ID: {ghl_client.company_id}")
                print(f"   Should be: rKXCHVr7vEFLD0e3iDq7")
        
    except Exception as e:
        print(f"❌ Error testing payload generation: {e}")

def check_server_startup_logs():
    """Suggest checking server startup logs"""
    print("\n📊 SERVER STARTUP LOG CHECK")
    print("=" * 60)
    
    print("🔍 To check if the server loaded the correct configuration:")
    print("   1. Stop the current server (Ctrl+C)")
    print("   2. Restart with: python main_working_final.py")
    print("   3. Look for these startup logs:")
    print("      📍 GHL_LOCATION_ID: ✅ Loaded")
    print("      🏢 GHL_COMPANY_ID: ✅ Loaded  <- This should appear")
    print("      🔑 GHL_PRIVATE_TOKEN: ✅ Loaded")
    print("")
    print("🎯 If GHL_COMPANY_ID doesn't appear in startup logs,")
    print("   then main_working_final.py isn't logging it properly.")

def main():
    """Run all configuration debugging tests"""
    print("🔍 COMPREHENSIVE CONFIGURATION DEBUG")
    print("=" * 80)
    print("This will help identify exactly where the Company ID issue is occurring")
    print("")
    
    # Test 1: Check if server is running
    server_running = test_live_application_config()
    
    # Test 2: Check configuration loading
    config_ok = test_config_loading()
    
    # Test 3: Check GHL API initialization
    ghl_client = test_ghl_api_initialization()
    
    # Test 4: Check V2 payload generation
    test_v2_payload_generation(ghl_client)
    
    # Test 5: Server startup log guidance
    check_server_startup_logs()
    
    # Summary
    print(f"\n📋 DEBUGGING SUMMARY")
    print("=" * 80)
    
    if config_ok and ghl_client and ghl_client.company_id == "rKXCHVr7vEFLD0e3iDq7":
        print("✅ Configuration appears CORRECT in this test!")
        print("🔄 The issue might be that the server needs to be restarted.")
        print("   Stop the server and restart: python main_working_final.py")
    else:
        print("❌ Configuration issue detected in this test.")
        print("   Check the specific error messages above.")
    
    print(f"\n🎯 NEXT STEPS:")
    print("1. If config looks correct, restart the server completely")
    print("2. Test vendor user creation again")
    print("3. Check the V2 API logs to see if Company ID is now correct")

if __name__ == "__main__":
    main()