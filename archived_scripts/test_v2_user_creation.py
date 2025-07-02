#!/usr/bin/env python3
"""
Test script for V2 OAuth API user creation with V1 fallback
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from api.services.ghl_api import GoHighLevelAPI
from config import AppConfig
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_v2_user_creation():
    """Test the V2 user creation with fallback"""
    
    print("🧪 Testing V2 OAuth API User Creation with V1 Fallback")
    print("=" * 60)
    
    # Check configuration
    print("📋 Configuration Check:")
    print(f"   🔑 Private Token: {'✅ Set' if AppConfig.GHL_PRIVATE_TOKEN else '❌ Missing'}")
    print(f"   🏢 Company ID: {'✅ Set' if AppConfig.GHL_COMPANY_ID else '❌ Missing'}")
    print(f"   🏛️ Agency API Key: {'✅ Set' if AppConfig.GHL_AGENCY_API_KEY else '❌ Missing'}")
    print(f"   📍 Location ID: {'✅ Set' if AppConfig.GHL_LOCATION_ID else '❌ Missing'}")
    print()
    
    if AppConfig.GHL_COMPANY_ID == "your_company_id_here":
        print("⚠️  WARNING: You need to update GHL_COMPANY_ID in your .env file!")
        print("   Please get your Company ID from GoHighLevel and update the .env file.")
        print()
    
    # Initialize API client
    try:
        ghl_client = GoHighLevelAPI(
            private_token=AppConfig.GHL_PRIVATE_TOKEN,
            location_id=AppConfig.GHL_LOCATION_ID,
            agency_api_key=AppConfig.GHL_AGENCY_API_KEY,
            company_id=AppConfig.GHL_COMPANY_ID
        )
        print("✅ GHL API client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize GHL API client: {e}")
        return
    
    # Test data for a fake vendor user
    test_user_data = {
        "firstName": "Test",
        "lastName": "Vendor",
        "email": f"test.vendor.{os.urandom(4).hex()}@example.com",  # Random email to avoid conflicts
        "phone": "+1555123456",
        "type": "account",
        "role": "user"
    }
    
    print(f"🧪 Testing user creation for: {test_user_data['email']}")
    print()
    
    # Test the main create_user method (V2 → V1 fallback)
    try:
        result = ghl_client.create_user(test_user_data)
        
        if result and not result.get("error"):
            print("✅ User creation successful!")
            print(f"   👤 User ID: {result.get('id')}")
            print(f"   📧 Email: {result.get('email')}")
            print(f"   🔒 API Version Used: {result.get('api_version', 'Detected from logs')}")
            
            if 'scopes' in result:
                print(f"   🎯 Scopes Applied: {result.get('scopes', [])}")
            
        else:
            print("❌ User creation failed!")
            print(f"   Error: {result.get('message', 'Unknown error')}")
            if result.get('v2_available') is not None:
                print(f"   V2 Available: {result.get('v2_available')}")
                print(f"   V1 Available: {result.get('v1_available')}")
                print(f"   Recommendation: {result.get('recommendation', 'Check logs')}")
            
    except Exception as e:
        print(f"❌ Exception during user creation test: {e}")
    
    print()
    print()
    print("🔍 Check the logs above to see which API version was used:")
    print("   • Look for 'V2 API user creation successful' for V2 success")
    print("   • Look for 'V1 API user creation successful' for V1 fallback")
    print()
    print("🔒 V2 ULTRA-RESTRICTIVE VENDOR PERMISSIONS:")
    print("   ✅ ALLOWED:")
    print("      • Contacts (assigned only)")
    print("      • Conversations (read + send messages to assigned only)")
    print("      • Opportunities (assigned only)")
    print("      • Calendars (schedule appointments)")
    print("      • Dashboard (basic stats only)")
    print()
    print("   ❌ BLOCKED:")
    print("      • Account Settings")
    print("      • Automation/Workflows")
    print("      • Forms management")
    print("      • Integrations")
    print("      • Marketing/AdManager")
    print("      • QR Codes, Quizzes, Surveys")
    print("      • WordPress")
    print("      • All other admin features")
    print()
    print("📋 Next: Test with a real vendor user to verify permissions in GHL!")

if __name__ == "__main__":
    test_v2_user_creation()
