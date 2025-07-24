#!/usr/bin/env python3
"""
Script to retrieve detailed webhook form submission data
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

def get_detailed_webhook_logs(limit=10):
    """Retrieve detailed webhook logs with full form data"""
    
    # Database path
    db_path = Path(__file__).parent / "smart_lead_router.db"
    
    if not db_path.exists():
        print(f"❌ Database not found at: {db_path}")
        return
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 DETAILED WEBHOOK FORM SUBMISSIONS")
        print("=" * 80)
        
        # Get recent form submissions with full data
        cursor.execute("""
            SELECT 
                timestamp,
                event_type,
                event_data,
                success,
                error_message,
                lead_id
            FROM activity_log
            WHERE event_type LIKE 'clean_webhook_%'
            AND event_type NOT LIKE '%error%'
            AND event_type NOT LIKE '%failure%'
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        logs = cursor.fetchall()
        
        if not logs:
            print("ℹ️ No webhook form submissions found")
            return
        
        print(f"📋 Showing {len(logs)} most recent form submissions:\n")
        
        for idx, log in enumerate(logs, 1):
            timestamp, event_type, event_data, success, error_msg, lead_id = log
            
            print(f"\n{'=' * 80}")
            print(f"📅 Submission #{idx} - {timestamp}")
            print(f"📌 Event: {event_type}")
            print(f"📋 Lead ID: {lead_id if lead_id else 'N/A'}")
            print(f"✅ Success: {'Yes' if success else 'No'}")
            
            if error_msg:
                print(f"❌ Error: {error_msg}")
            
            # Parse and display event data
            try:
                data = json.loads(event_data) if event_data else {}
                
                # Extract key information
                form_name = data.get('form', 'Unknown')
                form_type = data.get('form_type', 'Unknown')
                ghl_contact_id = data.get('ghl_contact_id', 'N/A')
                service_category = data.get('service_category', 'N/A')
                
                print(f"\n📝 FORM DETAILS:")
                print(f"   Form Name: {form_name}")
                print(f"   Form Type: {form_type}")
                print(f"   GHL Contact ID: {ghl_contact_id}")
                print(f"   Service Category: {service_category}")
                
                # Get the actual form payload if stored
                if 'payload_data' in data:
                    print(f"\n📄 FORM FIELDS SUBMITTED:")
                    payload = data['payload_data']
                    
                    # Sort fields for consistent display
                    sorted_fields = sorted(payload.items()) if isinstance(payload, dict) else []
                    
                    for field_name, field_value in sorted_fields:
                        if field_value and str(field_value).strip():
                            # Truncate long values
                            display_value = str(field_value)
                            if len(display_value) > 100:
                                display_value = display_value[:97] + "..."
                            print(f"   • {field_name}: {display_value}")
                
                # Show processing details
                if 'processing_time_seconds' in data:
                    print(f"\n⏱️ Processing Time: {data['processing_time_seconds']}s")
                
                # Show routing information if available
                if 'vendor_assigned' in data:
                    print(f"\n🎯 ROUTING:")
                    print(f"   Vendor Assigned: {data['vendor_assigned']}")
                
            except Exception as e:
                print(f"❌ Error parsing event data: {e}")
        
        # Get form submission statistics
        print(f"\n\n{'=' * 80}")
        print("📊 FORM SUBMISSION STATISTICS")
        print("=" * 80)
        
        # Count submissions by form
        cursor.execute("""
            SELECT 
                json_extract(event_data, '$.form') as form_name,
                COUNT(*) as submission_count,
                MAX(timestamp) as last_submission
            FROM activity_log
            WHERE event_type LIKE 'clean_webhook_%'
            AND json_extract(event_data, '$.form') IS NOT NULL
            GROUP BY form_name
            ORDER BY submission_count DESC
        """)
        
        form_stats = cursor.fetchall()
        
        print("\n📝 Submissions by Form:")
        for form_name, count, last_submission in form_stats:
            print(f"   • {form_name}: {count} submissions (last: {last_submission})")
        
        # Get success/failure rates
        cursor.execute("""
            SELECT 
                success,
                COUNT(*) as count
            FROM activity_log
            WHERE event_type LIKE 'clean_webhook_%'
            GROUP BY success
        """)
        
        success_stats = cursor.fetchall()
        total_submissions = sum(count for _, count in success_stats)
        
        print("\n📈 Success Rate:")
        for success, count in success_stats:
            percentage = (count / total_submissions * 100) if total_submissions > 0 else 0
            status = "Successful" if success else "Failed"
            print(f"   • {status}: {count} ({percentage:.1f}%)")
        
        # Get actual lead records for the most recent submissions
        if logs:
            print(f"\n\n{'=' * 80}")
            print("👥 LEAD DETAILS FROM DATABASE")
            print("=" * 80)
            
            # Get lead IDs from recent logs
            lead_ids = [log[5] for log in logs[:5] if log[5]]  # Get first 5 lead IDs
            
            if lead_ids:
                placeholders = ','.join('?' * len(lead_ids))
                cursor.execute(f"""
                    SELECT 
                        id,
                        service_category,
                        specific_services,
                        service_zip_code,
                        service_city,
                        service_state,
                        service_county,
                        vendor_id,
                        created_at
                    FROM leads
                    WHERE id IN ({placeholders})
                    ORDER BY created_at DESC
                """, lead_ids)
                
                leads = cursor.fetchall()
                
                for lead in leads:
                    lead_id, category, services, zip_code, city, state, county, vendor_id, created = lead
                    
                    print(f"\n📋 Lead: {lead_id}")
                    print(f"   Service: {category}")
                    
                    if services:
                        try:
                            services_list = json.loads(services)
                            if services_list:
                                print(f"   Specific Services: {', '.join(services_list)}")
                        except:
                            pass
                    
                    print(f"   Location: {city}, {state} {zip_code}")
                    if county:
                        print(f"   County: {county}")
                    
                    if vendor_id:
                        # Get vendor details
                        cursor.execute("""
                            SELECT name, company_name 
                            FROM vendors 
                            WHERE id = ?
                        """, (vendor_id,))
                        vendor = cursor.fetchone()
                        if vendor:
                            print(f"   Assigned to: {vendor[0]} ({vendor[1]})")
                    else:
                        print(f"   Assigned to: Not yet assigned")
                    
                    print(f"   Created: {created}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error retrieving logs: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    
    # Allow custom limit
    limit = 10
    
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except:
            pass
    
    get_detailed_webhook_logs(limit=limit)
    
    print(f"\n\n💡 Usage: python get_detailed_webhook_logs.py [limit]")
    print(f"   Example: python get_detailed_webhook_logs.py 20")