# If you're in a Python shell, run this:
import sys
import os
import json
import asyncio

# Import your modules
from database.simple_connection import SimpleDatabase
from api.services.ai_classifier import AIServiceClassifier

# Define and run the migration function
def migrate_existing_leads():
    print("🔄 Starting enhanced lead migration...")
    
    db = SimpleDatabase()
    classifier = AIServiceClassifier()
    
    # Get leads that haven't been migrated yet
    conn = db._get_conn()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, service_details, customer_name, customer_email, customer_phone, service_category
        FROM leads 
        WHERE service_zip_code IS NULL OR service_zip_code = ''
    ''')
    
    leads_to_migrate = cursor.fetchall()
    print(f"📊 Found {len(leads_to_migrate)} leads to migrate")
    
    if len(leads_to_migrate) == 0:
        print("✅ No leads need migration - all leads are already in enhanced format")
        conn.close()
        return
    
    migrated_count = 0
    
    for lead_data in leads_to_migrate:
        try:
            lead_id = lead_data[0]
            raw_service_details = lead_data[1]
            customer_name = lead_data[2]
            customer_email = lead_data[3]
            customer_phone = lead_data[4]
            old_service_category = lead_data[5]
            
            print(f"\n🔄 Migrating lead: {lead_id}")
            print(f"   Customer: {customer_name}")
            print(f"   Old Category: {old_service_category}")
            
            # Parse old service details
            if raw_service_details:
                try:
                    old_form_data = json.loads(raw_service_details)
                except:
                    old_form_data = {}
            else:
                old_form_data = {}
            
            # Add customer info for classification
            if customer_name:
                name_parts = customer_name.split(' ', 1)
                old_form_data['firstName'] = name_parts[0] if name_parts else ''
                old_form_data['lastName'] = name_parts[1] if len(name_parts) > 1 else ''
            
            old_form_data['email'] = customer_email or ''
            old_form_data['phone'] = customer_phone or ''
            
            # Re-classify using enhanced classifier
            classification_result = asyncio.run(classifier.classify_service_detailed(old_form_data))
            
            print(f"   New Category: {classification_result['primary_category']}")
            print(f"   Confidence: {classification_result['confidence']*100:.0f}%")
            print(f"   Services: {classification_result['specific_services']}")
            print(f"   Location: {classification_result['coverage_area']['zip_code']}")
            
            # Update lead with enhanced data
            cursor.execute('''
                UPDATE leads SET
                    service_zip_code = ?,
                    service_city = ?,
                    service_state = ?,
                    service_county = ?,
                    specific_services = ?,
                    service_complexity = ?,
                    estimated_duration = ?,
                    requires_emergency_response = ?,
                    classification_confidence = ?,
                    classification_reasoning = ?,
                    service_category = ?
                WHERE id = ?
            ''', (
                classification_result["coverage_area"]["zip_code"],
                classification_result["coverage_area"]["city"],
                classification_result["coverage_area"]["state"],
                classification_result["coverage_area"]["county"],
                json.dumps(classification_result["specific_services"]),
                classification_result["service_complexity"],
                classification_result["estimated_duration"],
                classification_result["requires_emergency_response"],
                classification_result["confidence"],
                classification_result["reasoning"],
                classification_result["primary_category"],
                lead_id
            ))
            
            migrated_count += 1
            print(f"   ✅ Migrated successfully")
            
        except Exception as e:
            print(f"   ❌ Error migrating lead {lead_id}: {e}")
            continue
    
    conn.commit()
    conn.close()
    
    print(f"\n🎉 Migration complete!")
    print(f"✅ Successfully migrated {migrated_count} leads")

# Now run the migration
migrate_existing_leads()