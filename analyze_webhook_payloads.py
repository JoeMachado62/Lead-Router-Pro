#!/usr/bin/env python3
"""
Comprehensive webhook payload analysis script
Extracts raw webhook data from both activity logs and leads table
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
import sys

def analyze_webhook_payloads(limit=10):
    """Analyze webhook payloads from multiple sources"""
    
    # Database path
    db_path = Path(__file__).parent / "smart_lead_router.db"
    
    if not db_path.exists():
        print(f"❌ Database not found at: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 WEBHOOK PAYLOAD ANALYSIS")
        print("=" * 80)
        
        # Get webhook logs with field keys
        cursor.execute("""
            SELECT 
                timestamp,
                event_type,
                event_data,
                lead_id
            FROM activity_log
            WHERE event_type LIKE '%webhook%'
            AND event_data LIKE '%payload_keys%'
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        webhook_logs = cursor.fetchall()
        
        if not webhook_logs:
            print("ℹ️ No webhook logs with payload keys found")
            return
        
        print(f"📋 Found {len(webhook_logs)} webhook submissions with payload data:")
        
        for idx, (timestamp, event_type, event_data, lead_id) in enumerate(webhook_logs, 1):
            print(f"\n{'='*80}")
            print(f"📅 WEBHOOK #{idx} - {timestamp}")
            print(f"📌 Event: {event_type}")
            print(f"📋 Lead ID: {lead_id}")
            
            # Parse webhook log data
            try:
                log_data = json.loads(event_data)
                form_name = log_data.get('form', 'Unknown')
                form_type = log_data.get('form_type', 'Unknown')
                
                print(f"📝 Form: {form_name} (Type: {form_type})")
                
                # Show field keys that were in the original payload
                if 'elementor_payload_keys' in log_data:
                    payload_keys = log_data['elementor_payload_keys']
                    print(f"\n📄 ORIGINAL FORM FIELD KEYS ({len(payload_keys)} fields):")
                    for i, key in enumerate(payload_keys, 1):
                        print(f"   {i:2d}. {key}")
                
                # Show validation warnings (field mapping issues)
                if 'validation_warnings' in log_data:
                    warnings = log_data['validation_warnings']
                    print(f"\n⚠️  FIELD MAPPING WARNINGS ({len(warnings)} warnings):")
                    
                    # Group warnings by type
                    missing_fields = []
                    unmapped_fields = []
                    
                    for warning in warnings:
                        if "is missing" in warning:
                            missing_fields.append(warning)
                        elif "is not a recognized GHL field" in warning:
                            unmapped_fields.append(warning)
                    
                    if missing_fields:
                        print(f"   📋 Missing Expected Fields ({len(missing_fields)}):")
                        for warning in missing_fields:
                            field_name = warning.split("'")[1]
                            print(f"      - {field_name}")
                    
                    if unmapped_fields:
                        print(f"   🔧 Unmapped Fields ({len(unmapped_fields)}):")
                        for warning in unmapped_fields:
                            field_name = warning.split("'")[1]
                            print(f"      - {field_name}")
                
                # Get processing details
                processing_time = log_data.get('processing_time_seconds', 'N/A')
                custom_fields_sent = log_data.get('custom_fields_sent', 'N/A')
                
                print(f"\n📊 Processing Details:")
                print(f"   ⏱️  Processing Time: {processing_time}s")
                print(f"   📤 Custom Fields Sent to GHL: {custom_fields_sent}")
                
            except Exception as e:
                print(f"❌ Error parsing webhook log: {e}")
            
            # Get corresponding lead data if available
            if lead_id:
                try:
                    cursor.execute("""
                        SELECT 
                            primary_service_category,
                            specific_service_requested,
                            service_zip_code,
                            service_county,
                            service_details,
                            created_at
                        FROM leads
                        WHERE id = ?
                    """, (lead_id,))
                    
                    lead_data = cursor.fetchone()
                    
                    if lead_data:
                        category, service, zip_code, county, details_json, created = lead_data
                        
                        print(f"\n👥 LEAD DATA:")
                        print(f"   🛠️  Service Category: {category}")
                        print(f"   📋 Specific Service: {service}")
                        print(f"   📍 Service ZIP: {zip_code}")
                        print(f"   🌍 Service County: {county}")
                        print(f"   📅 Created: {created}")
                        
                        # Parse and show actual field values
                        if details_json:
                            try:
                                details = json.loads(details_json)
                                print(f"\n📄 ACTUAL FIELD VALUES:")
                                
                                # Sort fields for consistent display
                                sorted_fields = sorted(details.items())
                                
                                for field_name, field_value in sorted_fields:
                                    if field_value and str(field_value).strip():
                                        # Truncate long values
                                        display_value = str(field_value)
                                        if len(display_value) > 80:
                                            display_value = display_value[:77] + "..."
                                        print(f"   • {field_name}: {display_value}")
                                
                            except Exception as e:
                                print(f"   ❌ Error parsing service details: {e}")
                
                except Exception as e:
                    print(f"❌ Error retrieving lead data: {e}")
        
        # Analyze field mapping patterns
        print(f"\n\n{'='*80}")
        print("📊 FIELD MAPPING ANALYSIS")
        print("="*80)
        
        # Get all unique field names from recent webhooks
        cursor.execute("""
            SELECT event_data
            FROM activity_log
            WHERE event_type LIKE '%webhook%'
            AND event_data LIKE '%payload_keys%'
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit * 2,))
        
        all_logs = cursor.fetchall()
        
        all_field_names = set()
        form_field_patterns = {}
        
        for (event_data,) in all_logs:
            try:
                log_data = json.loads(event_data)
                form_name = log_data.get('form', 'unknown')
                
                if 'elementor_payload_keys' in log_data:
                    payload_keys = log_data['elementor_payload_keys']
                    
                    # Track fields by form
                    if form_name not in form_field_patterns:
                        form_field_patterns[form_name] = set()
                    
                    for key in payload_keys:
                        all_field_names.add(key)
                        form_field_patterns[form_name].add(key)
                        
            except Exception as e:
                continue
        
        print(f"\n📋 FORM FIELD PATTERNS:")
        for form_name, fields in form_field_patterns.items():
            print(f"\n📝 {form_name.upper()} FORM ({len(fields)} fields):")
            for field in sorted(fields):
                print(f"   • {field}")
        
        # Analyze service categories and services patterns
        print(f"\n\n{'='*80}")
        print("🛠️  SERVICE CATEGORY ANALYSIS")
        print("="*80)
        
        # Get service categories from leads
        cursor.execute("""
            SELECT 
                primary_service_category,
                COUNT(*) as count,
                GROUP_CONCAT(DISTINCT source) as sources
            FROM leads
            GROUP BY primary_service_category
            ORDER BY count DESC
        """)
        
        service_stats = cursor.fetchall()
        
        print(f"\n📊 Service Categories Found:")
        for category, count, sources in service_stats:
            print(f"   • {category}: {count} leads (sources: {sources})")
        
        # Look for service array issues
        print(f"\n\n{'='*80}")
        print("🔍 SERVICE ARRAY ANALYSIS")
        print("="*80)
        
        # Check for service-related fields in service_details
        cursor.execute("""
            SELECT 
                primary_service_category,
                service_details
            FROM leads
            WHERE service_details LIKE '%service%'
            OR service_details LIKE '%Service%'
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
        service_detail_logs = cursor.fetchall()
        
        print(f"\n📋 Service-related fields in lead details:")
        
        for category, details_json in service_detail_logs:
            try:
                details = json.loads(details_json)
                
                service_fields = {}
                for key, value in details.items():
                    if 'service' in key.lower() or 'Service' in key:
                        service_fields[key] = value
                
                if service_fields:
                    print(f"\n🛠️  {category}:")
                    for field, value in service_fields.items():
                        print(f"   • {field}: {value}")
                        
            except Exception as e:
                continue
        
        conn.close()
        
        print(f"\n\n💡 SUMMARY:")
        print(f"   • Total webhook submissions analyzed: {len(webhook_logs)}")
        print(f"   • Unique field names found: {len(all_field_names)}")
        print(f"   • Forms with field patterns: {len(form_field_patterns)}")
        print(f"   • Service categories found: {len(service_stats)}")
        
    except Exception as e:
        print(f"❌ Error analyzing webhook payloads: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    limit = 10
    
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except:
            pass
    
    analyze_webhook_payloads(limit=limit)
    
    print(f"\n💡 Usage: python analyze_webhook_payloads.py [limit]")
    print(f"   Example: python analyze_webhook_payloads.py 20")