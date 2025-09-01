#!/usr/bin/env python3
"""
Test script to verify field mapping synchronization is working correctly.
Tests the complete pipeline: normalize_field_names() -> field_mapper.map_payload() -> GHL customFields
"""

import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.services.field_mapper import field_mapper
from api.routes.webhook_routes import normalize_field_names

def test_field_mapping_pipeline():
    """Test the complete field mapping pipeline with real-world form data"""
    
    # Simulate a form submission with fields that were previously failing
    test_payload = {
        # Fields that were failing before the sync
        "What Zip Code Are You Requesting a Charter or Rental In?": "33139",
        "What Specific Service(s) Do You Request?": "Yacht Charter",
        "Your Vessel Manufacturer? ": "Sea Ray",
        "Your Vessel Model": "Sundancer 320",
        "Year of Vessel?": "2022",
        "Is The Vessel On a Dock, At a Marina, or On a Trailer?": "Marina - Miami Beach",
        "When Do You Prefer Service?": "Next Weekend",
        "Any Special Requests or Other Information?": "Looking for a sunset cruise",
        "How Should We Contact You Back?": "Phone",
        
        # Standard fields
        "First Name": "Test",
        "Last Name": "User",
        "Your Contact Email?": "test@example.com",
        "Your Contact Phone #?": "305-555-1234",
        
        # Additional fields to test comprehensive mapping
        "What is Your Company Name?": "Test Marine Services",
        "Services Provided": "Charter and Rental",
        "Years in Business": "5",
        
        # Test lowercase variations
        "what type of vessel are you looking to buy or sell?": "Motor Yacht",
        "how many people in your party?": "8",
        "do you have a budget in mind?": "$5000-$10000"
    }
    
    print("=" * 70)
    print("FIELD MAPPING PIPELINE TEST")
    print("=" * 70)
    
    # Step 1: Normalize field names (webhook_routes.py)
    print("\n1. NORMALIZING FIELD NAMES (webhook_routes.py):")
    print("-" * 50)
    normalized_payload = normalize_field_names(test_payload)
    
    changes_made = []
    for original, normalized_value in normalized_payload.items():
        original_value = test_payload.get(original)
        if original not in test_payload or original_value != normalized_value:
            # Field was transformed
            original_key = None
            for k, v in test_payload.items():
                if v == normalized_value and k != original:
                    original_key = k
                    break
            if original_key:
                changes_made.append(f"  '{original_key}' -> '{original}'")
    
    if changes_made:
        print("Field transformations:")
        for change in changes_made[:10]:  # Show first 10 changes
            print(change)
        if len(changes_made) > 10:
            print(f"  ... and {len(changes_made) - 10} more transformations")
    else:
        print("  No field name transformations applied")
    
    print(f"\nNormalized payload has {len(normalized_payload)} fields")
    
    # Step 2: Map payload using field_mapper
    print("\n2. APPLYING FIELD MAPPER (field_mapper.py):")
    print("-" * 50)
    mapped_payload = field_mapper.map_payload(normalized_payload)
    
    # Check if critical fields were mapped correctly
    critical_fields = [
        "zip_code_of_service",
        "specific_service_needed", 
        "vessel_make",
        "vessel_model",
        "vessel_year",
        "vessel_location__slip",
        "desired_timeline",
        "special_requests__notes",
        "preferred_contact_method",
        "vendor_company_name",
        "services_provided"
    ]
    
    print("Critical field presence check:")
    for field in critical_fields:
        if field in mapped_payload:
            value = mapped_payload[field]
            print(f"  ✅ {field}: {value}")
        else:
            print(f"  ❌ {field}: MISSING")
    
    # Step 3: Verify GHL field details are available
    print("\n3. GHL FIELD REFERENCE CHECK:")
    print("-" * 50)
    
    ghl_fields_with_ids = []
    ghl_fields_without_ids = []
    
    for field_key in mapped_payload.keys():
        if field_key in ["firstName", "lastName", "email", "phone"]:
            # Standard fields don't need custom field IDs
            continue
            
        field_details = field_mapper.get_ghl_field_details(field_key)
        if field_details and field_details.get("id"):
            ghl_fields_with_ids.append(field_key)
        else:
            ghl_fields_without_ids.append(field_key)
    
    print(f"Fields with GHL IDs: {len(ghl_fields_with_ids)}")
    if ghl_fields_with_ids:
        print(f"  Examples: {', '.join(ghl_fields_with_ids[:5])}")
    
    if ghl_fields_without_ids:
        print(f"\n⚠️  Fields without GHL IDs: {len(ghl_fields_without_ids)}")
        print(f"  Missing: {', '.join(ghl_fields_without_ids[:5])}")
        print("  These fields may need to be created in GHL or added to field_reference.json")
    
    # Step 4: Simulate building customFields array for GHL
    print("\n4. GHL CUSTOM FIELDS ARRAY:")
    print("-" * 50)
    
    custom_fields = []
    for field_key, value in mapped_payload.items():
        if field_key in ["firstName", "lastName", "email", "phone"]:
            continue
            
        field_details = field_mapper.get_ghl_field_details(field_key)
        if field_details and field_details.get("id"):
            custom_fields.append({
                "id": field_details["id"],
                "key": field_key,
                "field_value": value
            })
    
    print(f"Built {len(custom_fields)} custom fields for GHL API")
    if custom_fields:
        print("\nSample custom fields (first 3):")
        for cf in custom_fields[:3]:
            print(f"  - {cf['key']}: '{cf['field_value']}' (ID: {cf['id'][:8]}...)")
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY:")
    print("=" * 70)
    print(f"✅ Original fields: {len(test_payload)}")
    print(f"✅ After normalization: {len(normalized_payload)} fields")
    print(f"✅ After field mapping: {len(mapped_payload)} fields")
    print(f"✅ Custom fields for GHL: {len(custom_fields)} fields")
    
    if ghl_fields_without_ids:
        print(f"\n⚠️  WARNING: {len(ghl_fields_without_ids)} fields missing GHL IDs")
        print("   These fields won't be sent to GHL until field_reference.json is updated")
    else:
        print("\n✅ All fields have GHL IDs - ready for API submission!")
    
    return {
        "success": len(ghl_fields_without_ids) == 0,
        "original_count": len(test_payload),
        "normalized_count": len(normalized_payload),
        "mapped_count": len(mapped_payload),
        "custom_fields_count": len(custom_fields),
        "missing_ids": ghl_fields_without_ids
    }

if __name__ == "__main__":
    result = test_field_mapping_pipeline()
    
    # Exit with appropriate code
    sys.exit(0 if result["success"] else 1)