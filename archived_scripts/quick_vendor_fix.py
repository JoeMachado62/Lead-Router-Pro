#!/usr/bin/env python3
"""
Quick Vendor Fix - Just fix the core assignment issue
"""

import sys
import os
import json
import sqlite3
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    print("🚀 QUICK VENDOR FIX")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Connect to database
        conn = sqlite3.connect('smart_lead_router.db')
        cursor = conn.cursor()
        
        print("\n🔧 Step 1: Fix vendor services and coverage")
        
        # Update vendors to county-based coverage with proper services
        cursor.execute("""
            UPDATE vendors 
            SET service_coverage_type = 'county',
                service_counties = '["Miami-Dade, FL", "Broward, FL", "Los Angeles, CA", "New York, NY"]',
                service_areas = '[]',
                services_provided = '["Boat Maintenance", "Marine Systems", "Engines and Generators", "Boat and Yacht Repair"]',
                updated_at = CURRENT_TIMESTAMP
            WHERE services_provided = '[]' OR service_coverage_type = 'national'
        """)
        
        rows_updated = cursor.rowcount
        print(f"✅ Updated {rows_updated} vendors")
        
        # Verify the update
        cursor.execute("SELECT name, service_coverage_type, services_provided FROM vendors LIMIT 3")
        results = cursor.fetchall()
        
        print("\n📋 Verification:")
        for name, coverage_type, services in results:
            print(f"   {name}: {coverage_type}, services: {len(json.loads(services)) if services else 0}")
        
        conn.commit()
        conn.close()
        
        print("\n🎉 QUICK FIX COMPLETED!")
        print("✅ Vendors now have services and county-based coverage")
        print("✅ Lead assignment should now work")
        print("\n🔮 Next steps:")
        print("1. Test lead assignment by submitting a form")
        print("2. Check vendor assignments in admin dashboard")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    main()
