#!/usr/bin/env python3
"""
Check specific vendor data in the database
"""

import sqlite3
import json
from pathlib import Path

def check_vendor_by_ghl_id(ghl_contact_id):
    """Check vendor data by GHL contact ID"""
    
    db_path = Path(__file__).parent / "smart_lead_router.db"
    
    if not db_path.exists():
        print(f"❌ Database not found at: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"🔍 Checking vendor with GHL Contact ID: {ghl_contact_id}")
        print("=" * 100)
        
        # Get vendor details
        cursor.execute("""
            SELECT 
                id,
                name,
                company_name,
                email,
                phone,
                services_offered,
                service_categories,
                coverage_type,
                coverage_states,
                coverage_counties,
                created_at,
                updated_at,
                ghl_contact_id
            FROM vendors
            WHERE ghl_contact_id = ?
        """, (ghl_contact_id,))
        
        vendor = cursor.fetchone()
        
        if vendor:
            (vendor_id, name, company, email, phone, services, service_categories, coverage_type,
             coverage_states, coverage_counties, created, updated, ghl_id) = vendor
            
            print("\n👔 VENDOR DETAILS:")
            print(f"   ID: {vendor_id}")
            print(f"   Name: {name}")
            print(f"   Company: {company}")
            print(f"   Email: {email}")
            print(f"   Phone: {phone}")
            print(f"   GHL Contact ID: {ghl_id}")
            print(f"   Created: {created}")
            print(f"   Updated: {updated}")
            
            print("\n🛠️ SERVICE CATEGORIES:")
            if service_categories:
                try:
                    categories_list = json.loads(service_categories) if isinstance(service_categories, str) else service_categories
                    if isinstance(categories_list, list):
                        for category in categories_list:
                            print(f"   • {category}")
                    else:
                        print(f"   {service_categories}")
                except:
                    print(f"   {service_categories}")
                    
            print("\n🛠️ SERVICES OFFERED:")
            if services:
                try:
                    services_list = json.loads(services) if isinstance(services, str) else services
                    if isinstance(services_list, list):
                        for service in services_list:
                            print(f"   • {service}")
                    else:
                        print(f"   {services}")
                except:
                    print(f"   {services}")
            
            print("\n📍 COVERAGE:")
            print(f"   Coverage Type: {coverage_type}")
            print(f"   Coverage States: {coverage_states}")
            print(f"   Coverage Counties: {coverage_counties}")
            
            # Check activity logs for this vendor creation
            print("\n📋 ACTIVITY LOG:")
            cursor.execute("""
                SELECT 
                    timestamp,
                    event_type,
                    event_data
                FROM activity_log
                WHERE lead_id = ? 
                OR event_data LIKE ?
                ORDER BY timestamp DESC
                LIMIT 5
            """, (ghl_contact_id, f'%{ghl_contact_id}%'))
            
            activities = cursor.fetchall()
            for timestamp, event_type, event_data in activities:
                print(f"\n   [{timestamp}] {event_type}")
                try:
                    data = json.loads(event_data)
                    if 'form_data' in data:
                        print("   Form Data Received:")
                        form_data = data['form_data']
                        print(f"     - coverage_type: {form_data.get('coverage_type')}")
                        print(f"     - service_coverage_area: {form_data.get('service_coverage_area')}")
                        print(f"     - coverage_states: {form_data.get('coverage_states')}")
                        print(f"     - service_categories: {form_data.get('service_categories')}")
                        print(f"     - services_provided: {form_data.get('services_provided')}")
                except:
                    pass
        else:
            print(f"\n⚠️ No vendor found with GHL Contact ID: {ghl_contact_id}")
            
            # Check if contact exists in activity logs
            cursor.execute("""
                SELECT COUNT(*) 
                FROM activity_log 
                WHERE event_data LIKE ?
            """, (f'%{ghl_contact_id}%',))
            
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"ℹ️ Found {count} activity log entries mentioning this GHL ID")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Check the specific vendor
    check_vendor_by_ghl_id("LtzgRiCMo4DDV3sZfEa4")