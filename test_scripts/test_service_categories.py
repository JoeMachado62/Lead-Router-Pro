#!/usr/bin/env python3
"""
Test script for the enhanced service_categories.py
Tests fuzzy matching, aliases, and Level 3 services
"""

from api.services.service_categories import (
    service_manager,
    vendor_matches_service_fuzzy,
    normalize_service_name,
    get_level3_services
)

def test_fuzzy_matching():
    """Test fuzzy matching capabilities"""
    print("\n=== Testing Fuzzy Matching ===")
    
    # Test cases with variations
    test_cases = [
        ("generator service", "Engines and Generators"),  # Should match "Generator Service"
        ("Generator Service and Repair", "Engines and Generators"),  # Exact alias
        ("fishing charters", "Boat Charters and Rentals"),  # Plural variation
        ("boat oil change", "Boat Maintenance"),  # With "boat" prefix
        ("oil change", "Boat Maintenance"),  # Without prefix
        ("fiberglass", "Boat and Yacht Repair"),  # Single word
        ("ac repair", "Marine Systems"),  # Alias
        ("welding", "Boat and Yacht Repair"),  # Partial match
    ]
    
    for service, expected_category in test_cases:
        category = service_manager.get_category_for_service(service)
        status = "✅" if category == expected_category else "❌"
        print(f"{status} '{service}' -> {category} (expected: {expected_category})")

def test_vendor_matching():
    """Test vendor matching with fuzzy logic"""
    print("\n=== Testing Vendor Matching ===")
    
    # Vendor's services (what they selected in their profile)
    vendor_services = [
        "Generator Service",  # Not "Generator Service and Repair"
        "Outboard Engine Service",
        "Fiberglass Repair",
        "Fishing Charters"  # Plural
    ]
    
    # Test matching against various service requests
    test_requests = [
        ("generator service", True),  # Should match despite case
        ("Generator Service and Repair", True),  # Should match the alias
        ("generator repair", True),  # Should match via alias
        ("Generator Sales", False),  # Different service
        ("fishing charter", True),  # Singular vs plural
        ("Inboard Engine Service", False),  # Different engine type
        ("fiberglass", True),  # Partial match
        ("Canvas or Upholstery", False),  # Not offered
    ]
    
    print(f"Vendor offers: {vendor_services}")
    print("\nMatching results:")
    
    for requested_service, should_match in test_requests:
        matches = vendor_matches_service_fuzzy(vendor_services, requested_service)
        status = "✅" if matches == should_match else "❌"
        print(f"{status} '{requested_service}' -> {matches} (expected: {should_match})")

def test_level3_services():
    """Test Level 3 service retrieval"""
    print("\n=== Testing Level 3 Services ===")
    
    test_cases = [
        ("Boat and Yacht Repair", "Fiberglass Repair"),
        ("Boat and Yacht Repair", "Welding & Metal Fabrication"),
        ("Engines and Generators", "Generator Service"),
        ("Marine Systems", "AC Sales or Service"),
        ("Boat Charters and Rentals", "Fishing Charter"),
    ]
    
    for category, subcategory in test_cases:
        level3 = get_level3_services(category, subcategory)
        if level3:
            print(f"\n{category} -> {subcategory}:")
            for service in level3[:3]:  # Show first 3
                print(f"  - {service}")
            if len(level3) > 3:
                print(f"  ... and {len(level3) - 3} more")
        else:
            print(f"\n{category} -> {subcategory}: No Level 3 services")

def test_service_normalization():
    """Test service name normalization"""
    print("\n=== Testing Service Normalization ===")
    
    test_cases = [
        "generator repair",  # Should normalize to "Generator Service"
        "fishing charters",  # Should normalize to "Fishing Charter"
        "boat oil change",  # Should normalize to "Oil Change"
        "ac repair",  # Should normalize to "AC Sales or Service"
        "Fiberglass Repair",  # Already normalized
    ]
    
    for service in test_cases:
        normalized = normalize_service_name(service)
        print(f"'{service}' -> '{normalized}'")

def test_form_identifier_classification():
    """Test form identifier classification"""
    print("\n=== Testing Form Identifier Classification ===")
    
    test_identifiers = [
        "generator_service",
        "fishing_charters",
        "boat_maintenance",
        "fiberglass_repair",
        "emergency_tow",
        "yacht_management",
    ]
    
    for identifier in test_identifiers:
        category, specific_service = service_manager.classify_form_identifier(identifier)
        print(f"'{identifier}':")
        print(f"  Category: {category}")
        print(f"  Service: {specific_service}")

def test_statistics():
    """Display statistics about the service hierarchy"""
    print("\n=== Service Hierarchy Statistics ===")
    
    stats = service_manager.get_stats()
    print(f"Total Categories: {stats['total_categories']}")
    print(f"Total Services (including aliases): {stats['total_services']}")
    print(f"Total Aliases: {stats['total_aliases']}")
    print(f"Total Level 3 Services: {stats['total_level3_services']}")
    print(f"Average Services per Category: {stats['average_services_per_category']}")
    print(f"Largest Category: {stats['largest_category']} ({stats['category_breakdown'][stats['largest_category']]} services)")
    print(f"Smallest Category: {stats['smallest_category']} ({stats['category_breakdown'][stats['smallest_category']]} services)")

def main():
    print("=" * 60)
    print("Testing Enhanced Service Categories Module")
    print("=" * 60)
    
    test_fuzzy_matching()
    test_vendor_matching()
    test_level3_services()
    test_service_normalization()
    test_form_identifier_classification()
    test_statistics()
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()