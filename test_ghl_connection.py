#!/usr/bin/env python3
"""
Quick test of GHL API connection to diagnose sync issues
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from config import AppConfig
    print("✅ Config loaded successfully")
    print(f"   GHL Location ID: {AppConfig.GHL_LOCATION_ID}")
    print(f"   Has Private Token: {'Yes' if AppConfig.GHL_PRIVATE_TOKEN else 'No'}")
    print(f"   Has Agency Key: {'Yes' if AppConfig.GHL_AGENCY_API_KEY else 'No'}")
except Exception as e:
    print(f"❌ Config error: {e}")
    sys.exit(1)

try:
    from api.services.ghl_api import GoHighLevelAPI
    print("✅ GHL API import successful")
    
    # Test basic initialization
    ghl_api = GoHighLevelAPI(
        private_token=AppConfig.GHL_PRIVATE_TOKEN,
        location_id=AppConfig.GHL_LOCATION_ID,
        agency_api_key=AppConfig.GHL_AGENCY_API_KEY,
        company_id=AppConfig.GHL_COMPANY_ID
    )
    print("✅ GHL API initialized")
    
    # Test simple API call with timeout
    print("🔍 Testing API connection...")
    contacts = ghl_api.search_contacts(query="test", limit=1)
    print(f"✅ API test successful - found {len(contacts) if contacts else 0} contacts")
    
except Exception as e:
    print(f"❌ GHL API error: {e}")
    import traceback
    traceback.print_exc()
