#!/usr/bin/env python3
"""
Debug script to see what field keys are being loaded
"""

import json

# Load field reference
with open("field_reference.json", "r") as f:
    FIELD_REFERENCE_DATA = json.load(f)

ALL_GHL_FIELDS_MAP_FROM_JSON = FIELD_REFERENCE_DATA.get("all_ghl_fields", {})

print("=== FIELD REFERENCE ANALYSIS ===")
print(f"Total fields in reference: {len(ALL_GHL_FIELDS_MAP_FROM_JSON)}")

# Show how the current logic processes fields
VALID_GHL_PAYLOAD_KEYS = set()
field_mapping = {}

for name, details in ALL_GHL_FIELDS_MAP_FROM_JSON.items():
    if details.get("fieldKey"):
        full_key = details.get("fieldKey")
        api_key = full_key.split("contact.")[-1]
        VALID_GHL_PAYLOAD_KEYS.add(api_key)
        field_mapping[api_key] = full_key
        
        # Show vendor fields specifically
        if any(vendor_term in name.lower() for vendor_term in ["vendor", "company", "service", "business"]):
            print(f"Vendor Field: '{name}' -> '{api_key}' (full: {full_key})")

print(f"\nTotal valid keys extracted: {len(VALID_GHL_PAYLOAD_KEYS)}")

# Check specific vendor fields
vendor_fields = ["vendor_company_name", "years_in_business", "services_provided", "primary_service_category", "service_zip_codes"]
print(f"\n=== VENDOR FIELD CHECK ===")
for field in vendor_fields:
    if field in VALID_GHL_PAYLOAD_KEYS:
        print(f"✅ {field} -> {field_mapping.get(field)}")
    else:
        print(f"❌ {field} NOT FOUND")

print(f"\n=== SAMPLE VALID KEYS ===")
for i, key in enumerate(sorted(VALID_GHL_PAYLOAD_KEYS)):
    if i < 10:  # Show first 10
        print(f"  {key}")
    elif i == 10:
        print(f"  ... and {len(VALID_GHL_PAYLOAD_KEYS) - 10} more")
        break
