#!/usr/bin/env python3
"""
Script to investigate database logs and find what created the mysterious contacts
"""

import sqlite3
import json
from datetime import datetime, timedelta
import sys
import os

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.simple_connection import db as simple_db_instance

def investigate_activity_logs():
    """
    Query the activity_log table for events around 1 hour ago (9:25 PM)
    """
    print("🕵️ INVESTIGATING ACTIVITY LOGS")
    print("=" * 50)
    
    # Calculate time range (1 hour ago +/- 30 minutes)
    current_time = datetime.now()
    target_time = current_time - timedelta(hours=1)
    start_time = target_time - timedelta(minutes=30)
    end_time = target_time + timedelta(minutes=30)
    
    print(f"🕐 Current time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Target time (1 hour ago): {target_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 Search range: {start_time.strftime('%H:%M:%S')} - {end_time.strftime('%H:%M:%S')}")
    print()
    
    try:
        # Connect to database directly
        conn = sqlite3.connect("smart_lead_router.db")
        cursor = conn.cursor()
        
        # Query activity logs in the time range
        cursor.execute("""
            SELECT id, event_type, event_data_json, related_contact_id, related_vendor_id, 
                   success, error_message, timestamp
            FROM activity_log 
            WHERE timestamp >= ? AND timestamp <= ?
            ORDER BY timestamp DESC
        """, (start_time.isoformat(), end_time.isoformat()))
        
        logs = cursor.fetchall()
        
        if not logs:
            print("❌ No activity logs found in the specified time range")
            
            # Check if there are any logs at all
            cursor.execute("SELECT COUNT(*) FROM activity_log")
            total_logs = cursor.fetchone()[0]
            print(f"📊 Total logs in database: {total_logs}")
            
            if total_logs > 0:
                # Show the most recent logs
                cursor.execute("""
                    SELECT id, event_type, timestamp
                    FROM activity_log 
                    ORDER BY timestamp DESC 
                    LIMIT 10
                """)
                recent_logs = cursor.fetchall()
                print("\n📋 Most recent 10 log entries:")
                for log in recent_logs:
                    print(f"  {log[2]} - {log[1]} (ID: {log[0]})")
        else:
            print(f"✅ Found {len(logs)} activity log entries in time range")
            print()
            
            for i, log in enumerate(logs):
                log_id, event_type, event_data_json, contact_id, vendor_id, success, error_msg, timestamp = log
                
                print(f"📋 LOG ENTRY [{i+1}]:")
                print(f"   🆔 ID: {log_id}")
                print(f"   📅 Time: {timestamp}")
                print(f"   🏷️  Type: {event_type}")
                print(f"   👤 Contact ID: {contact_id}")
                print(f"   🏢 Vendor ID: {vendor_id}")
                print(f"   ✅ Success: {success}")
                
                if error_msg:
                    print(f"   ❌ Error: {error_msg}")
                
                if event_data_json:
                    try:
                        event_data = json.loads(event_data_json)
                        print(f"   📊 Event Data:")
                        for key, value in event_data.items():
                            print(f"      {key}: {value}")
                    except json.JSONDecodeError:
                        print(f"   📊 Raw Event Data: {event_data_json}")
                
                print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error querying activity logs: {e}")

def check_for_contact_creation_logs():
    """
    Look specifically for any contact creation or notification events
    """
    print("\n🔍 CHECKING FOR CONTACT CREATION EVENTS")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect("smart_lead_router.db")
        cursor = conn.cursor()
        
        # Look for any events that might involve contact creation
        suspicious_event_types = [
            'vendor_notification_sent',
            'admin_notification_sent', 
            'contact_created',
            'sms_sent',
            'email_sent',
            'elementor_webhook_created',
            'elementor_webhook_updated'
        ]
        
        for event_type in suspicious_event_types:
            cursor.execute("""
                SELECT id, event_data_json, timestamp, success, error_message
                FROM activity_log 
                WHERE event_type = ?
                ORDER BY timestamp DESC 
                LIMIT 5
            """, (event_type,))
            
            events = cursor.fetchall()
            if events:
                print(f"\n📋 Recent '{event_type}' events:")
                for event in events:
                    log_id, event_data_json, timestamp, success, error_msg = event
                    print(f"   {timestamp} - Success: {success}")
                    if event_data_json:
                        try:
                            event_data = json.loads(event_data_json)
                            # Look for phone numbers or emails that match Jeremy's info
                            data_str = str(event_data).lower()
                            if '952' in data_str or 'jeremy' in data_str or 'docksidepros' in data_str:
                                print(f"   🚨 SUSPICIOUS: Contains Jeremy's info!")
                                print(f"      Data: {event_data}")
                        except:
                            pass
                    if error_msg:
                        print(f"   ❌ Error: {error_msg}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking contact creation logs: {e}")

def check_ghl_api_logs():
    """
    Look for any GHL API related logs that might show contact creation
    """
    print("\n🔍 CHECKING FOR GHL API LOGS")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect("smart_lead_router.db")
        cursor = conn.cursor()
        
        # Look for any events with GHL in the name or data
        cursor.execute("""
            SELECT id, event_type, event_data_json, timestamp, success, error_message
            FROM activity_log 
            WHERE event_type LIKE '%ghl%' 
               OR event_data_json LIKE '%ghl%'
               OR event_data_json LIKE '%contact%'
               OR event_data_json LIKE '%952%'
               OR event_data_json LIKE '%docksidepros%'
            ORDER BY timestamp DESC 
            LIMIT 10
        """)
        
        events = cursor.fetchall()
        if events:
            print(f"Found {len(events)} potentially relevant events:")
            for event in events:
                log_id, event_type, event_data_json, timestamp, success, error_msg = event
                print(f"\n📋 {timestamp} - {event_type}")
                print(f"   Success: {success}")
                if event_data_json:
                    print(f"   Data: {event_data_json}")
                if error_msg:
                    print(f"   Error: {error_msg}")
        else:
            print("No GHL-related logs found")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking GHL API logs: {e}")

if __name__ == "__main__":
    print("🔍 INVESTIGATING MYSTERIOUS CONTACT CREATION")
    print("Looking for what created contacts with Jeremy's info...")
    print()
    
    investigate_activity_logs()
    check_for_contact_creation_logs()
    check_ghl_api_logs()
    
    print("\n" + "=" * 50)
    print("🎯 INVESTIGATION COMPLETE")
    print("Look for any suspicious entries above that might explain")
    print("how contacts with Jeremy's phone (952) 393-3536 and")
    print("email info@docksidepros.com were created.")
