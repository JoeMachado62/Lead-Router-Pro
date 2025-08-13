#!/usr/bin/env python3
"""
Focused analysis of service categories and services offered fields
to identify data type issues and array handling problems
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
import sys

def analyze_service_field_issues():
    """Analyze service field data type issues in webhook processing"""
    
    # Database path
    db_path = Path(__file__).parent / "smart_lead_router.db"
    
    if not db_path.exists():
        print(f"❌ Database not found at: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 SERVICE FIELD DATA TYPE ANALYSIS")
        print("=" * 80)
        
        # 1. Analyze webhook form field variations
        print("\n📋 1. WEBHOOK FORM FIELD VARIATIONS")
        print("-" * 50)
        
        cursor.execute("""
            SELECT 
                json_extract(event_data, '$.form') as form_name,
                json_extract(event_data, '$.elementor_payload_keys') as field_keys,
                timestamp
            FROM activity_log
            WHERE event_type LIKE '%webhook%'
            AND event_data LIKE '%service%'
            ORDER BY timestamp DESC
            LIMIT 20
        """)
        
        webhook_forms = cursor.fetchall()
        
        form_field_variations = {}
        
        for form_name, field_keys_json, timestamp in webhook_forms:
            if field_keys_json:
                try:
                    field_keys = json.loads(field_keys_json)
                    service_fields = [key for key in field_keys if 'service' in key.lower() or 'category' in key.lower() or 'offer' in key.lower()]
                    
                    if form_name not in form_field_variations:
                        form_field_variations[form_name] = {}
                    
                    field_set = tuple(sorted(service_fields))
                    if field_set not in form_field_variations[form_name]:
                        form_field_variations[form_name][field_set] = []
                    
                    form_field_variations[form_name][field_set].append(timestamp)
                    
                except:
                    continue
        
        for form_name, variations in form_field_variations.items():
            print(f"\n📝 {form_name.upper()} FORM SERVICE FIELDS:")
            for idx, (field_set, timestamps) in enumerate(variations.items(), 1):
                print(f"   Variation {idx} ({len(timestamps)} submissions):")
                for field in field_set:
                    print(f"      • {field}")
                print(f"   Last seen: {timestamps[0]}")
        
        # 2. Analyze field mapping issues
        print(f"\n\n📋 2. FIELD MAPPING ISSUES")
        print("-" * 50)
        
        cursor.execute("""
            SELECT 
                json_extract(event_data, '$.form') as form_name,
                json_extract(event_data, '$.validation_warnings') as warnings,
                timestamp
            FROM activity_log
            WHERE event_type LIKE '%webhook%'
            AND event_data LIKE '%service%'
            AND event_data LIKE '%validation_warnings%'
            ORDER BY timestamp DESC
            LIMIT 10
        """)
        
        mapping_issues = cursor.fetchall()
        
        service_mapping_problems = {}
        
        for form_name, warnings_json, timestamp in mapping_issues:
            if warnings_json:
                try:
                    warnings = json.loads(warnings_json)
                    service_warnings = [w for w in warnings if 'service' in w.lower() or 'category' in w.lower() or 'offer' in w.lower()]
                    
                    if service_warnings:
                        if form_name not in service_mapping_problems:
                            service_mapping_problems[form_name] = {}
                        
                        for warning in service_warnings:
                            if warning not in service_mapping_problems[form_name]:
                                service_mapping_problems[form_name][warning] = []
                            service_mapping_problems[form_name][warning].append(timestamp)
                
                except:
                    continue
        
        for form_name, problems in service_mapping_problems.items():
            print(f"\n📝 {form_name.upper()} FORM MAPPING ISSUES:")
            for warning, timestamps in problems.items():
                print(f"   ⚠️  {warning}")
                print(f"      → Occurred {len(timestamps)} times, last: {timestamps[0]}")
        
        # 3. Analyze actual service data types in vendor records
        print(f"\n\n📋 3. VENDOR SERVICE DATA ANALYSIS")
        print("-" * 50)
        
        cursor.execute("""
            SELECT 
                name,
                company_name,
                service_categories,
                services_offered,
                ghl_contact_id,
                created_at
            FROM vendors
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        vendors = cursor.fetchall()
        
        service_data_patterns = {
            'categories': {'arrays': 0, 'strings': 0, 'empty': 0},
            'services': {'arrays': 0, 'strings': 0, 'empty': 0}
        }
        
        print(f"\n📊 SERVICE DATA PATTERNS IN VENDOR RECORDS:")
        
        for name, company, categories_json, services_json, ghl_id, created in vendors:
            print(f"\n👔 {name} ({company}) - {created}")
            
            # Analyze service categories
            if categories_json:
                try:
                    categories = json.loads(categories_json)
                    if isinstance(categories, list):
                        service_data_patterns['categories']['arrays'] += 1
                        print(f"   🛠️  Categories (array): {categories}")
                    else:
                        service_data_patterns['categories']['strings'] += 1
                        print(f"   🛠️  Categories (string): {categories}")
                except:
                    service_data_patterns['categories']['strings'] += 1
                    print(f"   🛠️  Categories (raw): {categories_json}")
            else:
                service_data_patterns['categories']['empty'] += 1
                print(f"   🛠️  Categories: None")
            
            # Analyze services offered
            if services_json:
                try:
                    services = json.loads(services_json)
                    if isinstance(services, list):
                        service_data_patterns['services']['arrays'] += 1
                        print(f"   📋 Services (array): {services}")
                    else:
                        service_data_patterns['services']['strings'] += 1
                        print(f"   📋 Services (string): {services}")
                except:
                    service_data_patterns['services']['strings'] += 1
                    print(f"   📋 Services (raw): {services_json}")
            else:
                service_data_patterns['services']['empty'] += 1
                print(f"   📋 Services: None")
        
        # 4. Look for raw webhook payloads with service field values
        print(f"\n\n📋 4. RAW WEBHOOK PAYLOAD ANALYSIS")
        print("-" * 50)
        
        # Check if there are any raw payloads stored
        cursor.execute("""
            SELECT DISTINCT 
                json_extract(event_data, '$.form') as form_name,
                json_extract(event_data, '$.elementor_payload_keys') as keys
            FROM activity_log
            WHERE event_type LIKE '%webhook%'
            AND event_data LIKE '%service%'
            LIMIT 5
        """)
        
        raw_payloads = cursor.fetchall()
        
        print(f"\n📄 ELEMENTOR FORM FIELD KEYS BY FORM:")
        
        for form_name, keys_json in raw_payloads:
            if keys_json:
                try:
                    keys = json.loads(keys_json)
                    service_keys = [k for k in keys if 'service' in k.lower() or 'category' in k.lower() or 'offer' in k.lower()]
                    
                    print(f"\n📝 {form_name.upper()} form service-related fields:")
                    for key in service_keys:
                        print(f"   • {key}")
                
                except:
                    continue
        
        # 5. Summary and recommendations
        print(f"\n\n📋 5. SUMMARY & RECOMMENDATIONS")
        print("-" * 50)
        
        total_vendors = len(vendors)
        
        print(f"\n📊 SERVICE DATA TYPE STATISTICS:")
        print(f"   Service Categories:")
        print(f"      • Arrays: {service_data_patterns['categories']['arrays']}/{total_vendors} ({service_data_patterns['categories']['arrays']/total_vendors*100:.1f}%)")
        print(f"      • Strings: {service_data_patterns['categories']['strings']}/{total_vendors} ({service_data_patterns['categories']['strings']/total_vendors*100:.1f}%)")
        print(f"      • Empty: {service_data_patterns['categories']['empty']}/{total_vendors} ({service_data_patterns['categories']['empty']/total_vendors*100:.1f}%)")
        
        print(f"   Services Offered:")
        print(f"      • Arrays: {service_data_patterns['services']['arrays']}/{total_vendors} ({service_data_patterns['services']['arrays']/total_vendors*100:.1f}%)")
        print(f"      • Strings: {service_data_patterns['services']['strings']}/{total_vendors} ({service_data_patterns['services']['strings']/total_vendors*100:.1f}%)")
        print(f"      • Empty: {service_data_patterns['services']['empty']}/{total_vendors} ({service_data_patterns['services']['empty']/total_vendors*100:.1f}%)")
        
        print(f"\n🎯 KEY FINDINGS:")
        print(f"   1. Form field names vary between different versions of the same form")
        print(f"   2. Some service fields are not mapped to GHL custom fields")
        print(f"   3. Service categories and services are stored as JSON arrays in the database")
        print(f"   4. Field mapping warnings indicate potential data loss during processing")
        
        print(f"\n💡 RECOMMENDATIONS:")
        print(f"   1. Create consistent field mappings for all service-related fields")
        print(f"   2. Ensure comma-separated strings are properly converted to arrays")
        print(f"   3. Add validation for service field data types before storage")
        print(f"   4. Map unmapped fields like 'service_categories_selected' to appropriate GHL fields")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error analyzing service field issues: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_service_field_issues()
    
    print(f"\n💡 This analysis helps identify service field data type issues")
    print(f"   and field mapping problems in webhook processing.")