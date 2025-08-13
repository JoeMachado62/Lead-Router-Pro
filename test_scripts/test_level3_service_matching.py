#!/usr/bin/env python3
"""
Test script to verify Level 3 service matching is working correctly
"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.services.lead_routing_service import LeadRoutingService
from api.services.service_categories import LEVEL_3_SERVICES

def test_vendor_matching():
    """Test the vendor matching logic with Level 3 services"""
    
    routing_service = LeadRoutingService()
    
    # Test Case 1: Vendor with Level 3 services for Fishing Charters
    print("\n" + "="*60)
    print("TEST CASE 1: Vendor with specific Level 3 fishing services")
    print("="*60)
    
    vendor_with_level3 = {
        'name': 'Joe\'s Fishing Charters',
        'services_offered': [
            'Inshore Fishing Charter',
            'Offshore (Deep Sea) Fishing Charter',
            'Reef & Wreck Fishing Charter'
            # Note: NOT including 'Freshwater Fishing Charter'
        ]
    }
    
    # Should match specific services they offer
    test_services = [
        ('Inshore Fishing Charter', True),
        ('Offshore (Deep Sea) Fishing Charter', True),
        ('Reef & Wreck Fishing Charter', True),
        ('Freshwater Fishing Charter', False),  # Should NOT match - vendor doesn't offer this
        ('Fishing Charters', False),  # Should NOT match Level 2 category when vendor has Level 3
        ('Fishing Charter', False)  # Should NOT match variant
    ]
    
    for service, expected in test_services:
        result = routing_service._vendor_matches_service(vendor_with_level3, service)
        status = "✅" if result == expected else "❌"
        print(f"{status} Service: '{service}' - Expected: {expected}, Got: {result}")
    
    # Test Case 2: Vendor with Level 2 services only (backward compatibility)
    print("\n" + "="*60)
    print("TEST CASE 2: Vendor with Level 2 services only")
    print("="*60)
    
    vendor_with_level2 = {
        'name': 'Marine Services Inc',
        'services_offered': [
            'Fishing Charters',  # Level 2 subcategory
            'Boat Maintenance'   # Level 1 category
        ]
    }
    
    # Should match the category and any service under it
    test_services = [
        ('Fishing Charters', True),  # Exact match
        ('Boat Maintenance', True),  # Exact match
        ('Inshore Fishing Charter', False),  # Level 3 service - no match since vendor uses Level 2
        ('Boat Detailing', True),  # Service under Boat Maintenance
        ('Bottom Cleaning', True),  # Service under Boat Maintenance
    ]
    
    for service, expected in test_services:
        result = routing_service._vendor_matches_service(vendor_with_level2, service)
        status = "✅" if result == expected else "❌"
        print(f"{status} Service: '{service}' - Expected: {expected}, Got: {result}")
    
    # Test Case 3: Mixed vendor with Fiberglass Repair Level 3 services
    print("\n" + "="*60)
    print("TEST CASE 3: Vendor with Level 3 Fiberglass Repair services")
    print("="*60)
    
    vendor_fiberglass = {
        'name': 'Expert Fiberglass',
        'services_offered': [
            'Hull Crack or Structural Repair',
            'Gelcoat Repair and Color Matching',
            'Transom Repair & Reinforcement'
            # NOT including 'Deck Delamination & Soft Spot Repair'
        ]
    }
    
    test_services = [
        ('Hull Crack or Structural Repair', True),
        ('Gelcoat Repair and Color Matching', True),
        ('Deck Delamination & Soft Spot Repair', False),  # Not offered
        ('Fiberglass Repair', False),  # Level 2 - should NOT match when vendor has Level 3
        ('Boat and Yacht Repair', False)  # Level 1 - should NOT match
    ]
    
    for service, expected in test_services:
        result = routing_service._vendor_matches_service(vendor_fiberglass, service)
        status = "✅" if result == expected else "❌"
        print(f"{status} Service: '{service}' - Expected: {expected}, Got: {result}")
    
    print("\n" + "="*60)
    print("SUMMARY: Level 3 service matching test complete")
    print("="*60)
    print("\nKey findings:")
    print("1. Vendors with Level 3 services only match exact Level 3 services")
    print("2. Vendors with Level 2 services match categories and their children")
    print("3. This prevents vendors from getting leads for services they don't offer")

if __name__ == "__main__":
    test_vendor_matching()