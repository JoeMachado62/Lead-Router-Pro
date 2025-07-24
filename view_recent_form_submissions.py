#!/usr/bin/env python3
"""
View recent form submissions from WordPress Elementor webhooks
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path

def view_recent_submissions(hours=24, show_details=True):
    """View recent form submissions with details"""
    
    db_path = Path(__file__).parent / "smart_lead_router.db"
    
    if not db_path.exists():
        print(f"❌ Database not found at: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 WORDPRESS ELEMENTOR FORM SUBMISSIONS")
        print("=" * 100)
        print(f"📅 Showing submissions from the last {hours} hours")
        print("=" * 100)
        
        # Calculate time threshold
        time_threshold = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        
        # Get webhook submissions
        cursor.execute("""
            SELECT 
                timestamp,
                event_type,
                event_data,
                lead_id,
                success,
                error_message
            FROM activity_log
            WHERE (
                event_type LIKE 'clean_webhook_created'
                OR event_type LIKE 'clean_webhook_updated'
                OR event_type LIKE 'elementor_webhook_%'
            )
            AND timestamp > ?
            ORDER BY timestamp DESC
        """, (time_threshold,))
        
        submissions = cursor.fetchall()
        
        if not submissions:
            print(f"\nℹ️ No form submissions found in the last {hours} hours")
            
            # Check total submissions
            cursor.execute("""
                SELECT COUNT(*), MAX(timestamp) 
                FROM activity_log 
                WHERE event_type LIKE '%webhook%created%' 
                OR event_type LIKE '%webhook%updated%'
            """)
            total, last_submission = cursor.fetchone()
            if total:
                print(f"📊 Total submissions in database: {total}")
                print(f"📅 Last submission: {last_submission}")
            return
        
        print(f"\n📋 Found {len(submissions)} form submissions\n")
        
        # Process each submission
        for idx, submission in enumerate(submissions, 1):
            timestamp, event_type, event_data, lead_id, success, error_msg = submission
            
            # Parse event data
            try:
                data = json.loads(event_data) if event_data else {}
            except:
                data = {}
            
            # Display submission header
            status_icon = "✅" if success else "❌"
            action = "Created" if "created" in event_type else "Updated"
            
            print(f"\n{'-' * 100}")
            print(f"#{idx} {status_icon} {action} at {timestamp}")
            print(f"Lead ID: {lead_id if lead_id else 'N/A'}")
            
            # Extract form information
            form_name = data.get('form', 'Unknown')
            form_type = data.get('form_type', 'Unknown')
            ghl_contact_id = data.get('ghl_contact_id', 'N/A')
            service_category = data.get('service_category', 'N/A')
            processing_time = data.get('processing_time_seconds', 'N/A')
            
            print(f"\n📝 FORM: {form_name}")
            print(f"   Type: {form_type}")
            print(f"   Service Category: {service_category}")
            print(f"   GHL Contact: {ghl_contact_id}")
            print(f"   Processing Time: {processing_time}s")
            
            # If we have a lead_id, get lead details
            if lead_id and show_details:
                cursor.execute("""
                    SELECT 
                        customer_name,
                        customer_email,
                        customer_phone,
                        primary_service_category,
                        specific_service_requested,
                        customer_zip_code,
                        service_county,
                        service_state,
                        vendor_id,
                        status,
                        priority,
                        created_at
                    FROM leads
                    WHERE id = ?
                """, (lead_id,))
                
                lead = cursor.fetchone()
                if lead:
                    (name, email, phone, category, service, zip_code, 
                     county, state, vendor_id, status, priority, created) = lead
                    
                    print(f"\n👤 CUSTOMER DETAILS:")
                    print(f"   Name: {name if name else 'N/A'}")
                    print(f"   Email: {email if email else 'N/A'}")
                    print(f"   Phone: {phone if phone else 'N/A'}")
                    print(f"   Location: {zip_code} ({county}, {state})" if county else f"   Location: {zip_code}")
                    
                    print(f"\n🛠️ SERVICE DETAILS:")
                    print(f"   Category: {category}")
                    print(f"   Service Requested: {service if service else 'N/A'}")
                    print(f"   Priority: {priority}")
                    print(f"   Status: {status}")
                    
                    # Get vendor details if assigned
                    if vendor_id:
                        cursor.execute("""
                            SELECT name, company_name, email, phone
                            FROM vendors
                            WHERE id = ?
                        """, (vendor_id,))
                        vendor = cursor.fetchone()
                        if vendor:
                            v_name, v_company, v_email, v_phone = vendor
                            print(f"\n👔 ASSIGNED VENDOR:")
                            print(f"   Name: {v_name}")
                            print(f"   Company: {v_company}")
                            print(f"   Email: {v_email}")
                            print(f"   Phone: {v_phone}")
                    else:
                        print(f"\n⚠️ VENDOR: Not yet assigned")
            
            if error_msg:
                print(f"\n❌ ERROR: {error_msg}")
        
        # Summary statistics
        print(f"\n\n{'=' * 100}")
        print("📊 SUBMISSION SUMMARY")
        print("=" * 100)
        
        # Count by form type
        cursor.execute("""
            SELECT 
                json_extract(event_data, '$.form') as form_name,
                COUNT(*) as count,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful
            FROM activity_log
            WHERE event_type LIKE '%webhook%created%'
            AND timestamp > ?
            AND json_extract(event_data, '$.form') IS NOT NULL
            GROUP BY form_name
            ORDER BY count DESC
        """, (time_threshold,))
        
        form_stats = cursor.fetchall()
        
        if form_stats:
            print("\n📝 Submissions by Form Type:")
            for form_name, total, successful in form_stats:
                success_rate = (successful / total * 100) if total > 0 else 0
                print(f"   • {form_name}: {total} submissions ({successful} successful - {success_rate:.0f}%)")
        
        # Service category breakdown
        cursor.execute("""
            SELECT 
                json_extract(event_data, '$.service_category') as category,
                COUNT(*) as count
            FROM activity_log
            WHERE event_type LIKE '%webhook%created%'
            AND timestamp > ?
            AND json_extract(event_data, '$.service_category') IS NOT NULL
            GROUP BY category
            ORDER BY count DESC
        """, (time_threshold,))
        
        category_stats = cursor.fetchall()
        
        if category_stats:
            print("\n🛠️ Submissions by Service Category:")
            for category, count in category_stats:
                print(f"   • {category}: {count} submissions")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    hours = 24
    show_details = True
    
    if len(sys.argv) > 1:
        try:
            hours = int(sys.argv[1])
        except:
            pass
    
    if len(sys.argv) > 2:
        show_details = sys.argv[2].lower() != 'false'
    
    view_recent_submissions(hours=hours, show_details=show_details)
    
    print(f"\n\n💡 Usage: python view_recent_form_submissions.py [hours] [show_details]")
    print(f"   Example: python view_recent_form_submissions.py 48 true")
    print(f"   Example: python view_recent_form_submissions.py 168 false  # Last week, summary only")