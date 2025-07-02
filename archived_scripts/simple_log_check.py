#!/usr/bin/env python3
"""
Simple script to check database logs without importing complex modules
"""

import sqlite3
import json
from datetime import datetime, timedelta

def main():
    print("🔍 INVESTIGATING MYSTERIOUS CONTACT CREATION")
    print("Looking for what created contacts with Jeremy's info...")
    print("=" * 60)
    
    try:
        # Connect directly to the SQLite database
        conn = sqlite3.connect("smart_lead_router.db")
        cursor = conn.cursor()
        
        # First, check if the activity_log table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='activity_log'")
        if not cursor.fetchone():
            print("❌ No activity_log table found in database")
            return
        
        print("✅ Found activity_log table")
        
        # Get total count of logs
        cursor.execute("SELECT COUNT(*) FROM activity_log")
        total_logs = cursor.fetchone()[0]
        print(f"📊 Total activity logs: {total_logs}")
        
        if total_logs == 0:
            print("❌ No activity logs found in database")
            return
        
        # Get the most recent logs (last 2 hours)
        print("\n🕐 RECENT ACTIVITY LOGS (Last 2 hours):")
        print("-" * 50)
        
        # Calculate 2 hours ago
        two_hours_ago = datetime.now() - timedelta(hours=2)
        
        cursor.execute("""
            SELECT id, event_type, event_data_json, related_contact_id, 
                   success, error_message, timestamp
            FROM activity_log 
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
        """, (two_hours_ago.isoformat(),))
        
        recent_logs = cursor.fetchall()
        
        if not recent_logs:
            print("❌ No recent logs found")
            # Show the 10 most recent logs regardless of time
            print("\n📋 Showing 10 most recent logs:")
            cursor.execute("""
                SELECT id, event_type, timestamp, success
                FROM activity_log 
                ORDER BY timestamp DESC 
                LIMIT 10
            """)
            all_recent = cursor.fetchall()
            for log in all_recent:
                print(f"  {log[2]} - {log[1]} (Success: {log[3]})")
        else:
            print(f"✅ Found {len(recent_logs)} recent logs")
            
            for i, log in enumerate(recent_logs):
                log_id, event_type, event_data_json, contact_id, success, error_msg, timestamp = log
                
                print(f"\n📋 LOG [{i+1}] - {timestamp}")
                print(f"   Type: {event_type}")
                print(f"   Contact ID: {contact_id}")
                print(f"   Success: {success}")
                
                if error_msg:
                    print(f"   ❌ Error: {error_msg}")
                
                # Check if this log contains Jeremy's info
                suspicious = False
                if event_data_json:
                    data_lower = event_data_json.lower()
                    if '952' in data_lower or 'jeremy' in data_lower or 'docksidepros' in data_lower:
                        suspicious = True
                        print(f"   🚨 SUSPICIOUS: Contains Jeremy's info!")
                    
                    try:
                        event_data = json.loads(event_data_json)
                        print(f"   📊 Event Data:")
                        for key, value in event_data.items():
                            if suspicious or 'contact' in key.lower() or 'phone' in key.lower() or 'email' in key.lower():
                                print(f"      {key}: {value}")
                    except json.JSONDecodeError:
                        if suspicious:
                            print(f"   📊 Raw Data: {event_data_json}")
        
        # Look specifically for vendor notification events
        print("\n🔍 VENDOR NOTIFICATION EVENTS:")
        print("-" * 50)
        
        cursor.execute("""
            SELECT timestamp, event_data_json, success, error_message
            FROM activity_log 
            WHERE event_type LIKE '%vendor%' OR event_type LIKE '%notification%'
            ORDER BY timestamp DESC 
            LIMIT 5
        """)
        
        vendor_logs = cursor.fetchall()
        if vendor_logs:
            for log in vendor_logs:
                timestamp, event_data_json, success, error_msg = log
                print(f"\n📋 {timestamp} - Success: {success}")
                if event_data_json:
                    print(f"   Data: {event_data_json}")
                if error_msg:
                    print(f"   Error: {error_msg}")
        else:
            print("No vendor notification events found")
        
        # Look for any SMS or contact creation events
        print("\n🔍 SMS/CONTACT CREATION EVENTS:")
        print("-" * 50)
        
        cursor.execute("""
            SELECT timestamp, event_type, event_data_json, success
            FROM activity_log 
            WHERE event_type LIKE '%sms%' 
               OR event_type LIKE '%contact%'
               OR event_type LIKE '%create%'
               OR event_data_json LIKE '%952%'
               OR event_data_json LIKE '%docksidepros%'
            ORDER BY timestamp DESC 
            LIMIT 10
        """)
        
        sms_logs = cursor.fetchall()
        if sms_logs:
            for log in sms_logs:
                timestamp, event_type, event_data_json, success = log
                print(f"\n📋 {timestamp} - {event_type} (Success: {success})")
                if event_data_json:
                    print(f"   Data: {event_data_json}")
        else:
            print("No SMS/contact creation events found")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 INVESTIGATION COMPLETE")

if __name__ == "__main__":
    main()
