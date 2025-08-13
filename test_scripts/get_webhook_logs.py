#!/usr/bin/env python3
"""
Script to retrieve recent webhook logs from the Lead Router Pro database
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path

def get_webhook_logs(hours=24, limit=100):
    """Retrieve recent webhook logs from the activity_log table"""
    
    # Database path
    db_path = Path(__file__).parent / "smart_lead_router.db"
    
    if not db_path.exists():
        print(f"❌ Database not found at: {db_path}")
        return
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if activity_log table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='activity_log'")
        if not cursor.fetchone():
            print("❌ No activity_log table found in database")
            return
        
        print("✅ Connected to database")
        print(f"📊 Retrieving webhook logs from the last {hours} hours...\n")
        
        # Calculate time threshold
        time_threshold = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        
        # Get webhook-related logs
        query = """
            SELECT 
                id,
                event_type,
                event_data,
                success,
                error_message,
                timestamp,
                lead_id,
                vendor_id
            FROM activity_log
            WHERE (
                event_type LIKE '%webhook%' 
                OR event_type LIKE 'elementor_%'
                OR event_type LIKE 'clean_webhook_%'
                OR event_type LIKE 'vendor_user_creation%'
                OR event_type LIKE 'lead_reassignment%'
            )
            AND timestamp > ?
            ORDER BY timestamp DESC
            LIMIT ?
        """
        
        cursor.execute(query, (time_threshold, limit))
        logs = cursor.fetchall()
        
        if not logs:
            print(f"ℹ️ No webhook logs found in the last {hours} hours")
            
            # Check if there are any webhook logs at all
            cursor.execute("""
                SELECT COUNT(*) FROM activity_log 
                WHERE event_type LIKE '%webhook%' 
                OR event_type LIKE 'elementor_%'
            """)
            total_webhook_logs = cursor.fetchone()[0]
            print(f"📊 Total webhook logs in database: {total_webhook_logs}")
            
            if total_webhook_logs > 0:
                # Get the most recent webhook log
                cursor.execute("""
                    SELECT timestamp FROM activity_log 
                    WHERE event_type LIKE '%webhook%' 
                    OR event_type LIKE 'elementor_%'
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """)
                last_log = cursor.fetchone()
                if last_log:
                    print(f"📅 Most recent webhook log: {last_log[0]}")
            
            return
        
        print(f"📋 Found {len(logs)} webhook logs:\n")
        print("-" * 120)
        
        # Display logs
        for log in logs:
            log_id, event_type, event_data, success, error_msg, timestamp, lead_id, vendor_id = log
            
            # Parse event_data JSON
            try:
                event_data_dict = json.loads(event_data) if event_data else {}
            except:
                event_data_dict = {}
            
            # Determine status icon
            status_icon = "✅" if success else "❌"
            
            print(f"{status_icon} {timestamp} - {event_type}")
            
            # Show relevant details based on event type
            if "elementor" in event_type.lower():
                form = event_data_dict.get('form', 'Unknown')
                form_type = event_data_dict.get('form_type', 'Unknown')
                print(f"   📝 Form: {form} (Type: {form_type})")
                
                if 'ghl_contact_id' in event_data_dict:
                    print(f"   👤 GHL Contact: {event_data_dict['ghl_contact_id']}")
                
                if 'service_category' in event_data_dict:
                    print(f"   🛠️ Service: {event_data_dict['service_category']}")
                
                if 'validation_errors' in event_data_dict:
                    print(f"   ⚠️ Validation Errors: {event_data_dict['validation_errors']}")
            
            elif "vendor_user_creation" in event_type:
                contact_id = event_data_dict.get('contact_id', 'Unknown')
                vendor_email = event_data_dict.get('vendor_email', 'Unknown')
                print(f"   👤 Contact ID: {contact_id}")
                print(f"   📧 Vendor Email: {vendor_email}")
                
                if 'user_id' in event_data_dict:
                    print(f"   🔑 User ID: {event_data_dict['user_id']}")
            
            elif "lead_reassignment" in event_type:
                contact_id = event_data_dict.get('contact_id', 'Unknown')
                print(f"   👤 Contact ID: {contact_id}")
                
                if 'from_vendor' in event_data_dict:
                    print(f"   ⬅️ From: {event_data_dict['from_vendor']}")
                
                if 'to_vendor' in event_data_dict:
                    print(f"   ➡️ To: {event_data_dict['to_vendor']}")
            
            # Show processing time if available
            if 'processing_time_seconds' in event_data_dict:
                print(f"   ⏱️ Processing Time: {event_data_dict['processing_time_seconds']}s")
            
            # Show error message if failed
            if not success and error_msg:
                print(f"   ❌ Error: {error_msg}")
            
            # Show lead/vendor IDs if available
            if lead_id:
                print(f"   📋 Lead ID: {lead_id}")
            if vendor_id:
                print(f"   👔 Vendor ID: {vendor_id}")
            
            print("-" * 120)
        
        # Get summary statistics
        print("\n📊 WEBHOOK ACTIVITY SUMMARY:")
        print("-" * 60)
        
        # Count by event type
        cursor.execute("""
            SELECT event_type, COUNT(*), SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END)
            FROM activity_log
            WHERE (
                event_type LIKE '%webhook%' 
                OR event_type LIKE 'elementor_%'
                OR event_type LIKE 'clean_webhook_%'
            )
            AND timestamp > ?
            GROUP BY event_type
            ORDER BY COUNT(*) DESC
        """, (time_threshold,))
        
        event_counts = cursor.fetchall()
        
        for event_type, total, successful in event_counts:
            success_rate = (successful / total * 100) if total > 0 else 0
            print(f"   {event_type}: {total} total, {successful} successful ({success_rate:.1f}% success rate)")
        
        # Get form submission counts
        cursor.execute("""
            SELECT 
                json_extract(event_data, '$.form') as form_name,
                COUNT(*) as submission_count
            FROM activity_log
            WHERE event_type LIKE '%elementor%'
            AND timestamp > ?
            AND json_extract(event_data, '$.form') IS NOT NULL
            GROUP BY form_name
            ORDER BY submission_count DESC
        """, (time_threshold,))
        
        form_counts = cursor.fetchall()
        
        if form_counts:
            print("\n📝 FORM SUBMISSIONS:")
            for form_name, count in form_counts:
                print(f"   {form_name}: {count} submissions")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error retrieving logs: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    
    # Allow custom time range
    hours = 24
    limit = 100
    
    if len(sys.argv) > 1:
        try:
            hours = int(sys.argv[1])
        except:
            pass
    
    if len(sys.argv) > 2:
        try:
            limit = int(sys.argv[2])
        except:
            pass
    
    print("🔍 LEAD ROUTER PRO - WEBHOOK LOG VIEWER")
    print("=" * 60)
    
    get_webhook_logs(hours=hours, limit=limit)
    
    print("\n💡 Usage: python get_webhook_logs.py [hours] [limit]")
    print("   Example: python get_webhook_logs.py 48 200")