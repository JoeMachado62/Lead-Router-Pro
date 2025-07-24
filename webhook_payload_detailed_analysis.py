#!/usr/bin/env python3
"""
Detailed analysis of webhook payloads showing actual field values
Focus on service categories and services offered fields to identify array issues
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
import sys

def analyze_webhook_payload_values(limit=10):
    """Get actual field values from webhook payloads"""
    
    # Database path
    db_path = Path(__file__).parent / "smart_lead_router.db"
    
    if not db_path.exists():
        print(f"❌ Database not found at: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 WEBHOOK PAYLOAD DETAILED FIELD VALUES ANALYSIS")
        print("=" * 80)
        
        # Get leads with service details to see actual field values
        cursor.execute("""
            SELECT 
                l.id,
                l.primary_service_category,
                l.service_details,
                l.created_at,
                l.source
            FROM leads l
            WHERE l.service_details IS NOT NULL
            ORDER BY l.created_at DESC
            LIMIT ?
        """, (limit,))
        
        lead_data = cursor.fetchall()
        
        if not lead_data:
            print("ℹ️ No leads with service details found")
            return
        
        print(f"📋 Found {len(lead_data)} leads with detailed field values:\n")
        
        for idx, (lead_id, category, details_json, created_at, source) in enumerate(lead_data, 1):
            print(f"{'='*80}")
            print(f"📅 LEAD #{idx} - {created_at}")
            print(f"📋 Lead ID: {lead_id}")
            print(f"🛠️  Category: {category}")
            print(f"📝 Source: {source}")
            
            # Get corresponding webhook log if available
            cursor.execute("""
                SELECT event_data
                FROM activity_log
                WHERE lead_id = ? AND event_type LIKE '%webhook%'
                ORDER BY timestamp DESC
                LIMIT 1
            """, (lead_id,))
            
            webhook_log = cursor.fetchone()
            original_fields = []
            
            if webhook_log:
                try:
                    log_data = json.loads(webhook_log[0])
                    if 'elementor_payload_keys' in log_data:
                        original_fields = log_data['elementor_payload_keys']
                        print(f"📄 Original Form Fields: {len(original_fields)} fields")
                except:
                    pass
            
            # Parse service details to get actual values
            if details_json:
                try:
                    details = json.loads(details_json)
                    
                    print(f"\n📄 ACTUAL FIELD VALUES AND TYPES:")
                    
                    # Focus on service-related fields
                    service_related_fields = {}
                    other_fields = {}
                    
                    for field_name, field_value in details.items():
                        if field_value and str(field_value).strip():
                            field_lower = field_name.lower()
                            
                            # Check if it's a service-related field
                            if any(keyword in field_lower for keyword in ['service', 'category', 'offer', 'provide']):
                                service_related_fields[field_name] = field_value
                            else:
                                other_fields[field_name] = field_value
                    
                    # Display service-related fields first
                    if service_related_fields:
                        print(f"\n   🛠️  SERVICE-RELATED FIELDS:")
                        for field_name, field_value in sorted(service_related_fields.items()):
                            value_type = type(field_value).__name__
                            
                            # Handle different data types
                            if isinstance(field_value, str):
                                # Check if it looks like a comma-separated list
                                if ',' in field_value:
                                    items = [item.strip() for item in field_value.split(',')]
                                    print(f"      • {field_name} ({value_type}): {field_value}")
                                    print(f"        → Parsed as list: {items}")
                                else:
                                    print(f"      • {field_name} ({value_type}): {field_value}")
                            elif isinstance(field_value, list):
                                print(f"      • {field_name} ({value_type}): {field_value}")
                            else:
                                print(f"      • {field_name} ({value_type}): {field_value}")
                    
                    # Display other important fields
                    if other_fields:
                        print(f"\n   📋 OTHER FIELDS:")
                        for field_name, field_value in sorted(other_fields.items()):
                            value_type = type(field_value).__name__
                            
                            # Truncate long values
                            display_value = str(field_value)
                            if len(display_value) > 60:
                                display_value = display_value[:57] + "..."
                            
                            print(f"      • {field_name} ({value_type}): {display_value}")
                    
                except Exception as e:
                    print(f"❌ Error parsing service details: {e}")
            
            print()
        
        # Analyze service categories specifically
        print(f"\n{'='*80}")
        print("🛠️  SERVICE CATEGORIES ANALYSIS")
        print("="*80)
        
        # Get vendor records to see how services are stored
        cursor.execute("""
            SELECT 
                name,
                company_name,
                service_categories,
                services_offered,
                coverage_counties,
                created_at
            FROM vendors
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
        vendors = cursor.fetchall()
        
        if vendors:
            print(f"\n📋 VENDOR SERVICE CATEGORIES ({len(vendors)} vendors):")
            
            for name, company, categories_json, services_json, counties_json, created in vendors:
                print(f"\n👔 {name} ({company})")
                print(f"   📅 Created: {created}")
                
                # Parse service categories
                try:
                    if categories_json:
                        categories = json.loads(categories_json)
                        print(f"   🛠️  Service Categories ({type(categories).__name__}): {categories}")
                    else:
                        print(f"   🛠️  Service Categories: None")
                except Exception as e:
                    print(f"   🛠️  Service Categories (parse error): {categories_json}")
                
                # Parse services offered
                try:
                    if services_json:
                        services = json.loads(services_json)
                        print(f"   📋 Services Offered ({type(services).__name__}): {services}")
                    else:
                        print(f"   📋 Services Offered: None")
                except Exception as e:
                    print(f"   📋 Services Offered (parse error): {services_json}")
                
                # Parse coverage areas
                try:
                    if counties_json:
                        counties = json.loads(counties_json)
                        print(f"   📍 Coverage Areas ({type(counties).__name__}): {counties}")
                    else:
                        print(f"   📍 Coverage Areas: None")
                except Exception as e:
                    print(f"   📍 Coverage Areas (parse error): {counties_json}")
        
        # Check for webhook processing issues
        print(f"\n{'='*80}")
        print("⚠️  WEBHOOK PROCESSING ISSUES")
        print("="*80)
        
        # Look for common field mapping issues
        cursor.execute("""
            SELECT 
                event_data,
                timestamp
            FROM activity_log
            WHERE event_type LIKE '%webhook%'
            AND (
                event_data LIKE '%service_categories_selected%'
                OR event_data LIKE '%services_provided%'
                OR event_data LIKE '%Select Services Offered%'
            )
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        processing_issues = cursor.fetchall()
        
        if processing_issues:
            print(f"\n📋 WEBHOOK PROCESSING LOGS WITH SERVICE FIELDS:")
            
            for event_data, timestamp in processing_issues:
                try:
                    log_data = json.loads(event_data)
                    
                    print(f"\n📅 {timestamp}")
                    print(f"   📝 Form: {log_data.get('form', 'Unknown')}")
                    
                    # Check for service-related field keys
                    if 'elementor_payload_keys' in log_data:
                        service_keys = [key for key in log_data['elementor_payload_keys'] 
                                       if any(keyword in key.lower() for keyword in ['service', 'category', 'offer', 'provide', 'select'])]
                        
                        if service_keys:
                            print(f"   🛠️  Service-related field keys found:")
                            for key in service_keys:
                                print(f"      • {key}")
                    
                    # Check for validation warnings related to services
                    if 'validation_warnings' in log_data:
                        service_warnings = [warning for warning in log_data['validation_warnings'] 
                                           if any(keyword in warning.lower() for keyword in ['service', 'category', 'offer', 'provide'])]
                        
                        if service_warnings:
                            print(f"   ⚠️  Service-related warnings:")
                            for warning in service_warnings:
                                print(f"      • {warning}")
                
                except Exception as e:
                    print(f"❌ Error parsing processing log: {e}")
        
        conn.close()
        
        print(f"\n\n💡 ANALYSIS SUMMARY:")
        print(f"   • Leads analyzed: {len(lead_data)}")
        print(f"   • Vendors analyzed: {len(vendors) if vendors else 0}")
        print(f"   • Processing logs checked: {len(processing_issues) if processing_issues else 0}")
        
        print(f"\n🎯 KEY FINDINGS:")
        print(f"   • Service categories are stored as JSON arrays in vendors table")
        print(f"   • Form field names vary between different form versions")
        print(f"   • Some fields like 'service_categories_selected' are not mapped to GHL fields")
        print(f"   • Field mapping warnings indicate potential data loss")
        
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
    
    analyze_webhook_payload_values(limit=limit)
    
    print(f"\n💡 Usage: python webhook_payload_detailed_analysis.py [limit]")
    print(f"   Example: python webhook_payload_detailed_analysis.py 15")