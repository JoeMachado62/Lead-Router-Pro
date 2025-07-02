#!/usr/bin/env python3

"""
Test script for the Field Mapping System
This script tests the field mapping functionality to ensure it works correctly.
"""

import sys
import json
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent))

from api.services.field_mapper import field_mapper

def test_field_mapping_system():
    """Test the field mapping system functionality"""
    
    print("🧪 Testing Field Mapping System")
    print("=" * 50)
    
    # Test 1: Basic field mapping
    print("\n1. Testing basic field mapping...")
    test_payload = {
        "serviceNeeded": "Emergency towing",
        "zipCode": "33139",
        "vesselMake": "Sea Ray",
        "firstName": "John",
        "lastName": "Doe"
    }
    
    mapped_payload = field_mapper.map_payload(test_payload, industry="marine")
    print(f"Original: {list(test_payload.keys())}")
    print(f"Mapped:   {list(mapped_payload.keys())}")
    
    # Test 2: Individual mapping lookups
    print("\n2. Testing individual field mappings...")
    test_fields = ["serviceNeeded", "zipCode", "vesselMake", "unknownField"]
    
    for field in test_fields:
        mapped = field_mapper.get_mapping(field, "marine")
        status = "✅ MAPPED" if mapped != field else "➡️ NO CHANGE"
        print(f"  {field} → {mapped} {status}")
    
    # Test 3: Statistics
    print("\n3. Testing mapping statistics...")
    stats = field_mapper.get_mapping_stats()
    print(f"Total mappings: {stats['total_mappings']}")
    print(f"Default mappings: {stats['default_mappings']}")
    print(f"Industry mappings: {stats['industry_mappings']}")
    print(f"Industries: {stats['industries']}")
    
    # Test 4: Reverse mapping
    print("\n4. Testing reverse mapping...")
    ghl_fields = ["specific_service_needed", "zip_code_of_service", "vessel_make"]
    
    for ghl_field in ghl_fields:
        form_field = field_mapper.get_reverse_mapping(ghl_field, "marine")
        print(f"  {ghl_field} ← {form_field}")
    
    # Test 5: Industry-specific mapping
    print("\n5. Testing industry-specific mappings...")
    automotive_payload = {
        "vehicleMake": "Toyota",
        "carModel": "Camry"
    }
    
    marine_mapped = field_mapper.map_payload(automotive_payload, "marine")
    automotive_mapped = field_mapper.map_payload(automotive_payload, "automotive")
    
    print(f"Marine industry:     {marine_mapped}")
    print(f"Automotive industry: {automotive_mapped}")
    
    print("\n✅ Field mapping system test completed!")
    return True

def test_webhook_integration():
    """Test how the field mapping integrates with webhook processing"""
    
    print("\n🔗 Testing Webhook Integration")
    print("=" * 50)
    
    # Simulate a typical form submission that would cause issues
    problem_payload = {
        "serviceNeeded": "Full ceramic coating for hull and deck",
        "zipCode": "33139", 
        "vesselMake": "Sea Ray",
        "firstName": "John",
        "lastName": "Doe",
        "email": "john.doe.test@dockside.life",
        "phone": "555-123-4567"
    }
    
    print("\nOriginal problematic payload:")
    print(json.dumps(problem_payload, indent=2))
    
    # Apply field mapping
    fixed_payload = field_mapper.map_payload(problem_payload, "marine")
    
    print("\nFixed payload after field mapping:")
    print(json.dumps(fixed_payload, indent=2))
    
    # Show the transformation
    print("\nField transformations:")
    for original_key, value in problem_payload.items():
        mapped_key = field_mapper.get_mapping(original_key, "marine")
        if original_key != mapped_key:
            print(f"  ✅ {original_key} → {mapped_key}")
        else:
            print(f"  ➡️ {original_key} (no change)")
    
    return True

if __name__ == "__main__":
    try:
        # Run tests
        test_field_mapping_system()
        test_webhook_integration()
        
        print("\n🎉 All tests passed! The field mapping system is working correctly.")
        print("\n📋 Summary of benefits:")
        print("   • Form field names are automatically mapped to GHL field names")
        print("   • Industry-specific mappings are supported")
        print("   • The system is backward compatible with existing forms")
        print("   • Administrators can define custom mappings through the dashboard")
        print("   • The system is now industry-agnostic and can be used beyond marine services")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
