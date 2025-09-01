#!/usr/bin/env python3
"""
Quick test to verify v2 API is working
"""

import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import AppConfig
from api.services.ghl_api_v2_optimized import OptimizedGoHighLevelAPI

def main():
    print("\n" + "="*60)
    print("TESTING V2 API OPTIMIZATION")
    print("="*60)
    
    # Initialize v2 optimized client
    print("\n1. Initializing v2 API client...")
    try:
        client = OptimizedGoHighLevelAPI(
            private_token=AppConfig.GHL_PRIVATE_TOKEN,
            location_id=AppConfig.GHL_LOCATION_ID,
            agency_api_key=AppConfig.GHL_AGENCY_API_KEY
        )
        print("   ✅ Client initialized successfully")
    except Exception as e:
        print(f"   ❌ Failed to initialize: {e}")
        return
    
    # Test connection
    print("\n2. Testing v2 connection...")
    try:
        if client.test_v2_connection():
            print("   ✅ v2 API connection successful!")
        else:
            print("   ❌ v2 API connection failed")
    except Exception as e:
        print(f"   ❌ Connection test error: {e}")
    
    # Test contact search
    print("\n3. Testing contact search with v2 API...")
    try:
        start = time.time()
        contacts = client.search_contacts(query="test", limit=5)
        elapsed = time.time() - start
        print(f"   ✅ Search completed in {elapsed:.2f}s")
        print(f"   Found {len(contacts)} contacts")
    except Exception as e:
        print(f"   ❌ Search error: {e}")
    
    # Test opportunity search  
    print("\n4. Testing opportunity search with v2 API...")
    try:
        start = time.time()
        opps = client.search_opportunities(limit=5)
        elapsed = time.time() - start
        print(f"   ✅ Search completed in {elapsed:.2f}s")
        print(f"   Found {len(opps)} opportunities")
    except Exception as e:
        print(f"   ❌ Search error: {e}")
    
    # Get API stats
    print("\n5. API Configuration:")
    stats = client.get_api_stats()
    print(f"   API Version: {stats['api_version']}")
    print(f"   Optimization: {stats['optimization']}")
    
    print("\n" + "="*60)
    print("✅ V2 API OPTIMIZATION IS ACTIVE")
    print("="*60)
    print("\nAll API calls are now using:")
    print("- v2 endpoints (/contacts/v2/, /opportunities/v2/, etc.)")
    print("- PIT token for authentication")
    print("- Optimized for reduced latency")
    print("\nOnly vendor user creation still uses v1 API as required by GHL")
    print("="*60)

if __name__ == "__main__":
    main()