#!/usr/bin/env python3
"""
Diagnose why barnacle cleaning leads both went to same GHL user
even though database shows different vendors
"""

import sqlite3
import json
from datetime import datetime

def diagnose_barnacle_assignments():
    """Deep dive into the barnacle cleaning lead assignments"""
    conn = sqlite3.connect('smart_lead_router.db')
    cursor = conn.cursor()
    
    print("=" * 80)
    print("BARNACLE CLEANING LEAD ASSIGNMENT DIAGNOSIS")
    print("=" * 80)
    
    # 1. Get the two barnacle cleaning leads with full details
    print("\n1. LEAD DETAILS AND VENDOR ASSIGNMENTS:")
    print("-" * 40)
    
    query = """
    SELECT 
        l.id,
        l.customer_name,
        l.specific_service_requested,
        l.vendor_id,
        l.ghl_opportunity_id,
        l.created_at,
        l.assigned_at,
        v.company_name,
        v.ghl_user_id,
        v.email
    FROM leads l
    LEFT JOIN vendors v ON l.vendor_id = v.id
    WHERE l.specific_service_requested = 'Barnacle Cleaning'
    ORDER BY l.created_at DESC
    LIMIT 2
    """
    
    cursor.execute(query)
    leads = cursor.fetchall()
    
    lead_details = []
    for lead in leads:
        lead_info = {
            'lead_id': lead[0],
            'customer': lead[1],
            'service': lead[2],
            'vendor_id': lead[3],
            'opportunity_id': lead[4],
            'created': lead[5],
            'assigned': lead[6],
            'vendor_name': lead[7],
            'vendor_ghl_user': lead[8],
            'vendor_email': lead[9]
        }
        lead_details.append(lead_info)
        
        print(f"\nLead: {lead[0]}")
        print(f"  Customer: {lead[1]}")
        print(f"  Service: {lead[2]}")
        print(f"  Created: {lead[5]}")
        print(f"  Assigned At: {lead[6]}")
        print(f"  Vendor ID: {lead[3]}")
        print(f"  Vendor Name: {lead[7]}")
        print(f"  Vendor GHL User ID: {lead[8]}")
        print(f"  Opportunity ID: {lead[4]}")
    
    # 2. Check activity logs for these leads
    print("\n2. ACTIVITY LOGS FOR THESE LEADS:")
    print("-" * 40)
    
    for lead in lead_details:
        print(f"\nActivity for Lead {lead['lead_id']}:")
        
        query = """
        SELECT 
            event_type,
            event_data,
            created_at,
            success
        FROM activity_log
        WHERE 
            (event_data LIKE ? OR event_data LIKE ?)
            AND created_at > datetime('now', '-2 days')
        ORDER BY created_at DESC
        LIMIT 5
        """
        
        cursor.execute(query, (f'%{lead["lead_id"]}%', f'%{lead["opportunity_id"]}%'))
        activities = cursor.fetchall()
        
        if activities:
            for activity in activities:
                event_data = json.loads(activity[1]) if activity[1] else {}
                print(f"  [{activity[2]}] {activity[0]} - Success: {activity[3]}")
                
                # Check for vendor assignment details
                if 'vendor' in str(event_data).lower() or 'assign' in activity[0].lower():
                    print(f"    Data: {json.dumps(event_data, indent=4)}")
        else:
            print("  No activity logs found")
    
    # 3. Check if vendors have correct GHL user IDs
    print("\n3. ALL VENDORS WITH BARNACLE CLEANING SERVICE:")
    print("-" * 40)
    
    query = """
    SELECT 
        id,
        company_name,
        ghl_user_id,
        ghl_contact_id,
        last_lead_assigned,
        status
    FROM vendors
    WHERE services_offered LIKE '%Barnacle Cleaning%'
    ORDER BY company_name
    """
    
    cursor.execute(query)
    vendors = cursor.fetchall()
    
    for vendor in vendors:
        print(f"\nVendor: {vendor[1]}")
        print(f"  ID: {vendor[0]}")
        print(f"  GHL User ID: {vendor[2]}")
        print(f"  GHL Contact ID: {vendor[3]}")
        print(f"  Last Lead: {vendor[4]}")
        print(f"  Status: {vendor[5]}")
    
    # 4. Compare what database says vs what happened
    print("\n4. DISCREPANCY ANALYSIS:")
    print("-" * 40)
    
    if len(lead_details) >= 2:
        lead1 = lead_details[0]
        lead2 = lead_details[1]
        
        print(f"\nLead 1 ({lead1['customer']}):")
        print(f"  Database says vendor: {lead1['vendor_name']} (GHL User: {lead1['vendor_ghl_user']})")
        print(f"  Opportunity ID: {lead1['opportunity_id']}")
        
        print(f"\nLead 2 ({lead2['customer']}):")
        print(f"  Database says vendor: {lead2['vendor_name']} (GHL User: {lead2['vendor_ghl_user']})")
        print(f"  Opportunity ID: {lead2['opportunity_id']}")
        
        print(f"\nYou reported both opportunities in GHL show owner as: zClXcz9UuR3MnTIvDCku")
        print(f"This is the GHL User ID for: {lead2['vendor_name'] if lead2['vendor_ghl_user'] == 'zClXcz9UuR3MnTIvDCku' else 'UNKNOWN'}")
        
        if lead1['vendor_ghl_user'] != lead2['vendor_ghl_user']:
            print(f"\n⚠️ ISSUE DETECTED:")
            print(f"Database shows different vendors assigned, but GHL shows same owner!")
            print(f"This suggests the API call to update opportunity assignment may have failed or used wrong ID")
    
    # 5. Check for any error patterns in activity logs
    print("\n5. CHECKING FOR API ERRORS:")
    print("-" * 40)
    
    query = """
    SELECT 
        event_type,
        event_data,
        error_message,
        created_at
    FROM activity_log
    WHERE 
        success = 0
        AND created_at > datetime('now', '-2 days')
        AND (event_type LIKE '%opportunity%' OR event_type LIKE '%assign%')
    ORDER BY created_at DESC
    LIMIT 10
    """
    
    cursor.execute(query)
    errors = cursor.fetchall()
    
    if errors:
        print("\nRecent errors related to opportunity assignment:")
        for error in errors:
            print(f"\n[{error[3]}] {error[0]}")
            print(f"  Error: {error[2]}")
    else:
        print("\nNo recent errors found")
    
    conn.close()

def check_vendor_ghl_user_consistency():
    """Check if vendor GHL user IDs are unique and consistent"""
    conn = sqlite3.connect('smart_lead_router.db')
    cursor = conn.cursor()
    
    print("\n" + "=" * 80)
    print("VENDOR GHL USER ID CONSISTENCY CHECK")
    print("=" * 80)
    
    # Check for duplicate GHL user IDs
    query = """
    SELECT 
        ghl_user_id,
        GROUP_CONCAT(company_name, ', ') as companies,
        COUNT(*) as count
    FROM vendors
    WHERE ghl_user_id IS NOT NULL
    GROUP BY ghl_user_id
    HAVING COUNT(*) > 1
    """
    
    cursor.execute(query)
    duplicates = cursor.fetchall()
    
    if duplicates:
        print("\n⚠️ WARNING: Found vendors sharing same GHL User ID:")
        for dup in duplicates:
            print(f"\nGHL User ID: {dup[0]}")
            print(f"  Shared by: {dup[1]}")
            print(f"  Count: {dup[2]}")
    else:
        print("\n✅ No duplicate GHL User IDs found")
    
    # Check for vendors without GHL user IDs
    query = """
    SELECT 
        company_name,
        id,
        status
    FROM vendors
    WHERE 
        ghl_user_id IS NULL
        AND status = 'active'
    """
    
    cursor.execute(query)
    missing = cursor.fetchall()
    
    if missing:
        print("\n⚠️ Active vendors without GHL User IDs:")
        for vendor in missing:
            print(f"  - {vendor[0]} (ID: {vendor[1]})")
    else:
        print("\n✅ All active vendors have GHL User IDs")
    
    conn.close()

if __name__ == "__main__":
    diagnose_barnacle_assignments()
    check_vendor_ghl_user_consistency()
    
    print("\n" + "=" * 80)
    print("DIAGNOSIS COMPLETE")
    print("=" * 80)
    print("\nKey finding: Database shows correct vendor assignments but GHL shows")
    print("both opportunities owned by same user (zClXcz9UuR3MnTIvDCku)")
    print("\nPossible causes:")
    print("1. The opportunity update API call failed silently")
    print("2. Wrong vendor GHL user ID was used in the API call")
    print("3. Race condition where both leads picked same vendor")
    print("4. Caching issue with vendor data")
    print("=" * 80)