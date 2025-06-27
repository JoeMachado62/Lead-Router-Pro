#!/usr/bin/env python3
"""
Quick test to verify V2 API configuration
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_config():
    print("🧪 Quick V2 API Configuration Test")
    print("=" * 40)
    
    # Check environment variables
    print("📋 Environment Variables:")
    print(f"   🔑 GHL_PRIVATE_TOKEN: {'✅ Set' if os.getenv('GHL_PRIVATE_TOKEN') else '❌ Missing'}")
    print(f"   🏢 GHL_COMPANY_ID: {'✅ Set' if os.getenv('GHL_COMPANY_ID') else '❌ Missing'}")
    print(f"   🏛️ GHL_AGENCY_API_KEY: {'✅ Set' if os.getenv('GHL_AGENCY_API_KEY') else '❌ Missing'}")
    print(f"   📍 GHL_LOCATION_ID: {'✅ Set' if os.getenv('GHL_LOCATION_ID') else '❌ Missing'}")
    print()
    
    # Show actual values (safe parts)
    company_id = os.getenv('GHL_COMPANY_ID', 'NOT_SET')
    location_id = os.getenv('GHL_LOCATION_ID', 'NOT_SET')
    
    print("📋 Values:")
    print(f"   🏢 Company ID: {company_id}")
    print(f"   📍 Location ID: {location_id}")
    print()
    
    # V2 Requirements check
    has_private_token = bool(os.getenv('GHL_PRIVATE_TOKEN'))
    has_company_id = bool(os.getenv('GHL_COMPANY_ID') and os.getenv('GHL_COMPANY_ID') != 'your_company_id_here')
    
    print("🎯 V2 API Requirements:")
    print(f"   Private Token: {'✅' if has_private_token else '❌'}")
    print(f"   Company ID: {'✅' if has_company_id else '❌'}")
    print()
    
    if has_private_token and has_company_id:
        print("✅ V2 API should work! Configuration looks good.")
        print("🎉 Next vendor user creation should use V2 with restricted permissions.")
    else:
        print("❌ V2 API requirements not met - will fall back to V1")
        if not has_private_token:
            print("   Missing: Private Token")
        if not has_company_id:
            print("   Missing: Company ID (or still set to placeholder)")

if __name__ == "__main__":
    test_config()
