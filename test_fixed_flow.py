#!/usr/bin/env python3
"""
Test script to verify the fixed vendor assignment flow
"""
import os
import sys
import sqlite3
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import AppConfig
from api.services.ghl_api_v2_optimized import OptimizedGoHighLevelAPI

def check_recent_lead_assignments():
    """Check recent leads to see if they have proper opportunity assignments"""
    print("=" * 80)
    print("CHECKING RECENT LEAD ASSIGNMENTS")
    print("=" * 80)
    
    conn = sqlite3.connect('smart_lead_router.db')
    cursor = conn.cursor()
    
    # Get recent leads with opportunities
    cursor.execute("""
        SELECT 
            l.id,
            l.customer_name,
            l.ghl_opportunity_id,
            l.specific_service_requested,
            l.service_county,
            l.vendor_id,
            v.company_name,
            v.ghl_user_id,
            l.status,
            l.created_at
        FROM leads l
        LEFT JOIN vendors v ON l.vendor_id = v.id
        WHERE l.created_at > datetime('now', '-1 day')
        ORDER BY l.created_at DESC
        LIMIT 5
    """)
    
    results = cursor.fetchall()
    
    if not results:
        print("No recent leads found")
        conn.close()
        return
    
    print("\nRecent Leads:")
    print("-" * 80)
    
    ghl_api = OptimizedGoHighLevelAPI(
        private_token=AppConfig.GHL_PRIVATE_TOKEN,
        location_id=AppConfig.GHL_LOCATION_ID,
        agency_api_key=AppConfig.GHL_AGENCY_API_KEY
    )
    
    for row in results:
        lead_id = row[0][:8]
        customer = row[1] or "Unknown"
        opp_id = row[2]
        service = row[3] or "Unknown"
        location = row[4] or "Unknown"
        vendor_id = row[5]
        vendor_name = row[6] or "No Vendor"
        vendor_ghl_user = row[7]
        status = row[8]
        created = row[9]
        
        print(f"\nLead: {lead_id} - {customer}")
        print(f"  Status: {status}")
        print(f"  Service: {service}")
        print(f"  Location: {location}")
        print(f"  Created: {created}")
        
        if opp_id:
            print(f"  Opportunity: {opp_id[:20]}...")
            
            # Check GHL opportunity assignment
            try:
                opp = ghl_api.get_opportunity_by_id(opp_id)
                if opp:
                    assigned_to = opp.get('assignedTo', '')
                    if assigned_to:
                        print(f"  GHL Assigned To: {assigned_to}")
                        if vendor_ghl_user and assigned_to == vendor_ghl_user:
                            print(f"  ✅ CORRECT - Matches vendor {vendor_name}")
                        elif vendor_ghl_user:
                            print(f"  ❌ MISMATCH - Should be {vendor_ghl_user} for {vendor_name}")
                        else:
                            print(f"  ⚠️ Vendor has no GHL User ID")
                    else:
                        print(f"  ❌ NOT ASSIGNED in GHL")
                        if vendor_ghl_user:
                            print(f"     Should be assigned to: {vendor_ghl_user} ({vendor_name})")
            except Exception as e:
                print(f"  ⚠️ Error checking GHL: {e}")
        else:
            print(f"  ⚠️ No opportunity ID")
        
        if vendor_id:
            print(f"  DB Vendor: {vendor_name}")
        else:
            print(f"  ⚠️ No vendor assigned in DB")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("""
Expected flow after fix:
1. Opportunity created FIRST with ID
2. Lead created WITH opportunity_id 
3. Vendor selected based on service & location
4. Lead updated with vendor_id
5. GHL opportunity updated with vendor's assignedTo

Check the above results to verify this flow is working correctly.
""")

def check_lead_status_distribution():
    """Check distribution of lead statuses"""
    conn = sqlite3.connect('smart_lead_router.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM leads
        WHERE created_at > datetime('now', '-7 days')
        GROUP BY status
        ORDER BY count DESC
    """)
    
    print("\nLead Status Distribution (Last 7 Days):")
    print("-" * 40)
    for row in cursor.fetchall():
        status = row[0] or "NULL"
        count = row[1]
        print(f"  {status:20} : {count}")
    
    conn.close()

if __name__ == "__main__":
    check_recent_lead_assignments()
    check_lead_status_distribution()