#!/usr/bin/env python3
"""
Check webhook logs for specific vendor submission
"""

import sqlite3
import json
from pathlib import Path

def find_vendor_webhook_logs(email="luces1202@gmail.com"):
    """Find webhook logs for a specific vendor by email"""
    
    db_path = Path(__file__).parent / "smart_lead_router.db"
    
    if not db_path.exists():
        print(f"❌ Database not found at: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"🔍 Searching activity logs for email: {email}")
        print("=" * 100)
        
        # Search activity logs
        print("\n\n📋 ACTIVITY LOGS:")
        cursor.execute("""
            SELECT 
                timestamp,
                event_type,
                event_data
            FROM activity_log
            WHERE event_data LIKE ?
            ORDER BY timestamp DESC
            LIMIT 5
        """, (f'%{email}%',))
        
        activities = cursor.fetchall()
        
        for timestamp, event_type, event_data in activities:
            print(f"\n[{timestamp}] {event_type}")
            try:
                data = json.loads(event_data)
                if 'payload_keys' in data:
                    print("   Payload Keys:", data['payload_keys'])
                if 'ghl_contact_id' in data:
                    print("   GHL Contact ID:", data['ghl_contact_id'])
                if 'custom_fields_sent' in data:
                    print("   Custom Fields Sent:", data['custom_fields_sent'])
            except:
                pass
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    find_vendor_webhook_logs()