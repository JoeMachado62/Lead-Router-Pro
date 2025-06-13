#!/usr/bin/env python3
import json

with open('field_reference.json', 'r') as f:
    data = json.load(f)

client_fields = ['vessel_make', 'vessel_model', 'vessel_year', 'vessel_length_ft', 'vessel_location__slip', 'specific_service_needed', 'zip_code_of_service', 'desired_timeline', 'budget_range', 'special_requests__notes', 'preferred_contact_method']
print('=== CLIENT LEAD FIELD MAPPING ===')
for field_name in client_fields:
    found = False
    for ghl_name, details in data['all_ghl_fields'].items():
        field_key = details['fieldKey'].split('contact.')[-1]
        if field_key == field_name:
            print(f'{field_name}: {details["fieldKey"]} (ID: {details["id"]})')
            found = True
            break
    if not found:
        print(f'{field_name}: NOT FOUND')
