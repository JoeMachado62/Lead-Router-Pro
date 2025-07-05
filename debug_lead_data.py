#!/usr/bin/env python3
"""
Lead Data Structure Inspector
Debug tool to inspect actual GHL lead data structure and find where ZIP codes are stored
"""

import sys
import os
import json
from pprint import pprint

# Add the Lead-Router-Pro directory to the path
sys.path.insert(0, '/root/Lead-Router-Pro')

# Load environment variables
def load_env_file(env_path: str = '.env'):
    if not os.path.exists(env_path):
        return
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                value = value.strip('"\'')
                os.environ[key] = value

load_env_file()

from api.services.ghl_api import GoHighLevelAPI
from config import AppConfig

async def inspect_lead_data():
    """Inspect actual lead data structure from GHL"""
    print("🔍 LEAD DATA STRUCTURE INSPECTOR")
    print("=" * 60)
    
    try:
        # Initialize GHL API (same way as routing_admin.py)
        print("🔌 Initializing GHL API client...")
        ghl_api = GoHighLevelAPI(
            location_api_key=AppConfig.GHL_LOCATION_API,
            private_token=AppConfig.GHL_PRIVATE_TOKEN,
            location_id=AppConfig.GHL_LOCATION_ID,
            agency_api_key=AppConfig.GHL_AGENCY_API_KEY,
            company_id=AppConfig.GHL_COMPANY_ID
        )
        
        # Get unassigned leads from GHL
        print("📡 Fetching unassigned opportunities from GoHighLevel...")
        
        # Get opportunities from the new lead stage (unassigned)
        response = ghl_api.get_opportunities_by_pipeline_stage(
            AppConfig.GHL_LOCATION_ID,
            AppConfig.PIPELINE_ID,
            AppConfig.NEW_LEAD_STAGE_ID
        )
        
        if not response or 'opportunities' not in response:
            print("❌ No opportunities found or invalid response")
            print(f"Response: {response}")
            return
        
        opportunities = response['opportunities']
        print(f"✅ Found {len(opportunities)} unassigned opportunities")
        
        if not opportunities:
            print("📭 No leads to inspect")
            return
        
        # Inspect first few leads in detail
        for i, opportunity in enumerate(opportunities[:3]):  # Only check first 3
            print(f"\n" + "="*80)
            print(f"🔍 LEAD #{i+1} DETAILED INSPECTION")
            print(f"🆔 Opportunity ID: {opportunity.get('id')}")
            print("="*80)
            
            # Get the contact details
            contact_id = opportunity.get('contactId')
            print(f"👤 Contact ID: {contact_id}")
            
            if contact_id:
                print(f"\n📞 Fetching contact details for {contact_id}...")
                contact_response = ghl_api.get_contact(AppConfig.GHL_LOCATION_ID, contact_id)
                
                if contact_response:
                    print(f"\n📋 FULL CONTACT DATA STRUCTURE:")
                    print("-" * 50)
                    print(json.dumps(contact_response, indent=2))
                    
                    print(f"\n🔍 LOOKING FOR ZIP CODE PATTERNS:")
                    print("-" * 50)
                    
                    # Check standard fields
                    standard_fields = ['postalCode', 'postal_code', 'zipCode', 'zip_code', 'zip', 'address', 'address1']
                    for field in standard_fields:
                        value = contact_response.get(field)
                        if value:
                            print(f"   📍 {field}: {value}")
                    
                    # Check custom fields in detail
                    custom_fields = contact_response.get('customFields', {})
                    print(f"\n🏷️ CUSTOM FIELDS ANALYSIS:")
                    print(f"   Type: {type(custom_fields)}")
                    print(f"   Length: {len(custom_fields) if hasattr(custom_fields, '__len__') else 'N/A'}")
                    
                    if isinstance(custom_fields, list):
                        print("   📝 Custom fields (LIST format):")
                        for idx, field in enumerate(custom_fields):
                            print(f"      [{idx}] {field}")
                            
                            # Look for ZIP-like patterns
                            field_name = str(field.get('name', '')).lower()
                            field_value = field.get('value')
                            
                            if any(zip_word in field_name for zip_word in ['zip', 'postal', 'location', 'area', 'service']):
                                print(f"         🎯 POTENTIAL ZIP FIELD: {field}")
                                
                    elif isinstance(custom_fields, dict):
                        print("   📝 Custom fields (DICT format):")
                        for key, value in custom_fields.items():
                            print(f"      {key}: {value}")
                            
                            # Look for ZIP-like patterns
                            if any(zip_word in key.lower() for zip_word in ['zip', 'postal', 'location', 'area', 'service']):
                                print(f"         🎯 POTENTIAL ZIP FIELD: {key} = {value}")
                    
                    # Check tags
                    tags = contact_response.get('tags', [])
                    if tags:
                        print(f"\n🏷️ TAGS:")
                        for tag in tags:
                            print(f"   📌 {tag}")
                            # Look for ZIP patterns in tags
                            import re
                            if re.search(r'\b\d{5}\b', str(tag)):
                                print(f"         🎯 POTENTIAL ZIP IN TAG: {tag}")
                    
                    # Check ALL top-level fields for ZIP patterns
                    print(f"\n🔍 ALL FIELDS SCAN FOR ZIP PATTERNS:")
                    print("-" * 50)
                    for field_name, field_value in contact_response.items():
                        if field_value and isinstance(field_value, (str, int)):
                            # Check if field value looks like a ZIP code
                            zip_str = str(field_value).strip()
                            if len(zip_str) == 5 and zip_str.isdigit():
                                print(f"   🎯 FOUND 5-DIGIT NUMBER: {field_name} = {zip_str}")
                            
                            # Check if field name suggests location data
                            field_name_lower = field_name.lower()
                            if any(zip_word in field_name_lower for zip_word in ['zip', 'postal', 'location', 'area', 'address', 'city', 'state']):
                                print(f"   📍 LOCATION-RELATED FIELD: {field_name} = {field_value}")
                
                else:
                    print("❌ Could not fetch contact details")
            
            print(f"\n" + "-"*60)
            
            # Ask user if they want to continue with next lead
            if i < min(len(opportunities), 3) - 1:
                continue_inspection = input(f"\n❓ Continue with lead #{i+2}? (y/n): ").strip().lower()
                if continue_inspection not in ['y', 'yes']:
                    break
        
        # Summary of findings
        print(f"\n" + "="*80)
        print(f"📊 INSPECTION SUMMARY")
        print("="*80)
        print(f"✅ Successfully inspected {min(len(opportunities), 3)} leads")
        print(f"🔍 Use the detailed output above to understand:")
        print(f"   1. What field names contain ZIP codes")
        print(f"   2. Whether custom fields are in list or dict format")
        print(f"   3. The exact data structure of your GHL leads")
        print(f"   4. Where location data is actually stored")
        
        print(f"\n💡 NEXT STEPS:")
        print(f"   1. Look for 🎯 POTENTIAL ZIP FIELD markers in the output")
        print(f"   2. Note any 📍 LOCATION-RELATED FIELD entries")
        print(f"   3. Check for 5-DIGIT NUMBER patterns")
        print(f"   4. Update _extract_location_data() with correct field names")
        
    except Exception as e:
        print(f"❌ Error during inspection: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function - non-async version"""
    print("🔍 Lead Data Structure Inspector")
    print("This tool will help identify where ZIP codes are stored in your GHL leads")
    print("")
    
    proceed = input("❓ Ready to inspect lead data? (y/n): ").strip().lower()
    if proceed not in ['y', 'yes']:
        print("❌ Inspection cancelled")
        return
    
    # Note: Making this synchronous since the GHL API methods might be sync
    try:
        # Initialize GHL API (same way as routing_admin.py)
        print("🔌 Initializing GHL API client...")
        ghl_api = GoHighLevelAPI(
            location_api_key=AppConfig.GHL_LOCATION_API,
            private_token=AppConfig.GHL_PRIVATE_TOKEN,
            location_id=AppConfig.GHL_LOCATION_ID,
            agency_api_key=AppConfig.GHL_AGENCY_API_KEY,
            company_id=AppConfig.GHL_COMPANY_ID
        )
        
        # Get unassigned leads from GHL
        print("📡 Fetching unassigned contacts from GoHighLevel...")
        
        # Use the same method as routing_admin.py: search_contacts
        contacts = ghl_api.search_contacts(query="lead", limit=100)
        
        if not contacts:
            print("❌ No contacts found")
            return
        
        # Filter for leads (same logic as routing_admin.py)
        unassigned_leads = []
        for contact in contacts:
            assigned_to = contact.get('assignedTo')
            tags = contact.get('tags', [])
            
            # Consider it a lead if it has lead-related tags or is in a lead pipeline
            is_lead = any(tag.lower() in ['lead', 'new lead', 'unassigned'] for tag in tags)
            
            if is_lead and not assigned_to:
                unassigned_leads.append(contact)
        
        print(f"✅ Found {len(contacts)} total contacts")
        print(f"✅ Found {len(unassigned_leads)} unassigned leads")
        
        if not unassigned_leads:
            print("📭 No unassigned leads to inspect")
            print("💡 This might explain why ZIP extraction is failing!")
            return
        
        # Show the first lead's structure quickly
        print(f"\n🔍 QUICK INSPECTION OF FIRST UNASSIGNED LEAD:")
        print("=" * 50)
        first_lead = unassigned_leads[0]
        print(f"Lead structure: {json.dumps(first_lead, indent=2)}")
        
        # Look for ZIP code patterns in the first lead
        print(f"\n🔍 ZIP CODE ANALYSIS:")
        print("-" * 30)
        
        # Check standard fields
        standard_fields = ['postalCode', 'postal_code', 'zipCode', 'zip_code', 'zip', 'address', 'address1']
        found_location_data = False
        
        for field in standard_fields:
            value = first_lead.get(field)
            if value:
                print(f"   📍 {field}: {value}")
                found_location_data = True
        
        # Check custom fields
        custom_fields = first_lead.get('customFields', {})
        print(f"\n🏷️ CUSTOM FIELDS:")
        print(f"   Type: {type(custom_fields)}")
        
        if isinstance(custom_fields, list):
            print("   📝 Custom fields (LIST format):")
            for idx, field in enumerate(custom_fields):
                field_name = str(field.get('name', '')).lower()
                field_value = field.get('value')
                print(f"      [{idx}] {field.get('name')}: {field_value}")
                
                # Look for ZIP-like patterns
                if any(zip_word in field_name for zip_word in ['zip', 'postal', 'location', 'area', 'service']):
                    print(f"         🎯 POTENTIAL ZIP FIELD!")
                    found_location_data = True
                    
        elif isinstance(custom_fields, dict):
            print("   📝 Custom fields (DICT format):")
            for key, value in custom_fields.items():
                print(f"      {key}: {value}")
                
                # Look for ZIP-like patterns
                if any(zip_word in key.lower() for zip_word in ['zip', 'postal', 'location', 'area', 'service']):
                    print(f"         🎯 POTENTIAL ZIP FIELD!")
                    found_location_data = True
        
        # Check tags for ZIP patterns
        tags = first_lead.get('tags', [])
        if tags:
            print(f"\n🏷️ TAGS:")
            for tag in tags:
                print(f"   📌 {tag}")
                import re
                if re.search(r'\b\d{5}\b', str(tag)):
                    print(f"         🎯 POTENTIAL ZIP IN TAG!")
                    found_location_data = True
        
        # Check all fields for 5-digit numbers
        print(f"\n🔍 ALL FIELDS SCAN:")
        for field_name, field_value in first_lead.items():
            if field_value and isinstance(field_value, (str, int)):
                zip_str = str(field_value).strip()
                if len(zip_str) == 5 and zip_str.isdigit():
                    print(f"   🎯 FOUND 5-DIGIT NUMBER: {field_name} = {zip_str}")
                    found_location_data = True
        
        if not found_location_data:
            print(f"\n❌ NO LOCATION DATA FOUND!")
            print(f"💡 This explains why all 8 leads failed ZIP extraction!")
            print(f"🔧 SOLUTIONS:")
            print(f"   1. Check if leads have location data in other stages")
            print(f"   2. Update forms to capture ZIP codes")  
            print(f"   3. Implement metro area fallback strategies")
        else:
            print(f"\n✅ FOUND LOCATION DATA!")
            print(f"💡 Update _extract_location_data() to check these fields")
        
    except Exception as e:
        print(f"❌ Error during inspection: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"❌ Error during inspection: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()