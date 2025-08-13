#!/usr/bin/env python3
"""
Clear all lead assignments in the local database so you can test the bulk assignment feature
"""

import os
import sys
import json
from datetime import datetime

# Add the Lead-Router-Pro directory to the path
sys.path.insert(0, '/root/Lead-Router-Pro')

# Load environment variables from .env file
def load_env_file(env_path: str = '.env'):
    """Load environment variables from .env file"""
    if not os.path.exists(env_path):
        print(f"❌ .env file not found at {env_path}")
        return
    
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                value = value.strip('"\'')
                os.environ[key] = value

# Load the .env file
load_env_file()

from database.simple_connection import db

def clear_all_lead_assignments():
    """Clear all vendor assignments from leads to prepare for testing"""
    print("=" * 60)
    print("🧹 CLEARING ALL LEAD ASSIGNMENTS FOR TESTING")
    print("=" * 60)
    
    # Get current lead assignments
    conn = db._get_conn()
    cursor = conn.cursor()
    
    # Get count of currently assigned leads
    cursor.execute("SELECT COUNT(*) FROM leads WHERE vendor_id IS NOT NULL")
    assigned_count = cursor.fetchone()[0]
    
    # Get total leads
    cursor.execute("SELECT COUNT(*) FROM leads")
    total_count = cursor.fetchone()[0]
    
    print(f"📊 Current Status:")
    print(f"  Total leads: {total_count}")
    print(f"  Assigned leads: {assigned_count}")
    print(f"  Unassigned leads: {total_count - assigned_count}")
    
    if assigned_count == 0:
        print(f"\n✅ No leads are currently assigned - ready for testing!")
        conn.close()
        return
    
    # Clear all assignments
    print(f"\n🧹 Clearing assignments from {assigned_count} leads...")
    
    cursor.execute("""
        UPDATE leads 
        SET vendor_id = NULL, 
            status = 'new', 
            updated_at = CURRENT_TIMESTAMP
        WHERE vendor_id IS NOT NULL
    """)
    
    cleared_count = cursor.rowcount
    conn.commit()
    conn.close()
    
    print(f"✅ Successfully cleared {cleared_count} lead assignments")
    print(f"\n🎯 **READY FOR TESTING:**")
    print(f"  1. Open the dashboard: Lead Router → Lead Routing tab")
    print(f"  2. Click 'Process Unassigned Leads' button")
    print(f"  3. Watch the system assign leads using the new opportunity method")
    print(f"  4. Check for 'Successfully assigned opportunity...' in logs")

def show_current_assignments():
    """Show current lead assignment status"""
    print("\n" + "=" * 60)
    print("📋 CURRENT LEAD ASSIGNMENT STATUS")
    print("=" * 60)
    
    conn = db._get_conn()
    cursor = conn.cursor()
    
    # Get leads with their assignment status
    cursor.execute("""
        SELECT l.id, l.customer_name, l.service_category, l.status, l.ghl_opportunity_id,
               v.name as vendor_name, v.ghl_user_id
        FROM leads l
        LEFT JOIN vendors v ON l.vendor_id = v.id
        ORDER BY l.created_at DESC
        LIMIT 10
    """)
    
    leads = cursor.fetchall()
    
    if not leads:
        print("📭 No leads found in database")
        conn.close()
        return
    
    print(f"📊 Recent Leads (showing last 10):")
    print(f"{'ID':<8} {'Customer':<20} {'Service':<25} {'Status':<10} {'Assigned To':<20} {'Opp ID':<10}")
    print("-" * 120)
    
    for lead in leads:
        lead_id = lead[0][:8] + "..."
        customer = (lead[1] or "Unknown")[:19]
        service = (lead[2] or "Unknown")[:24]
        status = lead[3] or "new"
        vendor = lead[5] or "UNASSIGNED"
        has_opp = "✅" if lead[4] else "❌"
        has_user_id = "✅" if lead[6] else "❌" if lead[5] else "--"
        
        print(f"{lead_id:<8} {customer:<20} {service:<25} {status:<10} {vendor[:19]:<20} {has_opp:<10}")
    
    # Get summary stats
    cursor.execute("""
        SELECT 
            COUNT(*) as total_leads,
            COUNT(vendor_id) as assigned_leads,
            COUNT(ghl_opportunity_id) as leads_with_opportunities
        FROM leads
    """)
    
    stats = cursor.fetchone()
    conn.close()
    
    print(f"\n📈 Summary:")
    print(f"  Total leads: {stats[0]}")
    print(f"  Assigned leads: {stats[1]}")
    print(f"  Unassigned leads: {stats[0] - stats[1]}")
    print(f"  Leads with opportunity IDs: {stats[2]}")
    
    if stats[2] < stats[0]:
        print(f"  ⚠️  {stats[0] - stats[2]} leads missing opportunity IDs")

def main():
    """Main function"""
    print("🎯 Lead Assignment Management Tool")
    print("\nOptions:")
    print("1. Clear all lead assignments (prepare for testing)")
    print("2. Show current assignment status")
    print("3. Do both")
    
    choice = input("\nEnter your choice (1, 2, or 3): ").strip()
    
    if choice == "1":
        clear_all_lead_assignments()
    elif choice == "2":
        show_current_assignments()
    elif choice == "3":
        show_current_assignments()
        print("\n" + "="*60)
        clear_all_lead_assignments()
    else:
        print("❌ Invalid choice. Please run again and choose 1, 2, or 3.")
        return
    
    print(f"\n🔗 **NEXT STEPS:**")
    print(f"  Dashboard URL: http://localhost:8000/admin-dashboard")
    print(f"  Test endpoint: POST /api/v1/routing/process-unassigned-leads")
    print(f"  Expected result: Opportunities assigned to vendor User IDs")

if __name__ == "__main__":
    main()
