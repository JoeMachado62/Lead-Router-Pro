#!/usr/bin/env python3
"""
Test script for the new service dictionary mapping integration
"""

import json
import logging
from api.services.webhook_integration_patch import process_webhook_with_service_mapping

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_service_mapping():
    """Test various webhook payloads with the new service mapping"""
    
    # Test Case 1: Yacht Management Service Request
    test_payload_1 = {
        "firstName": "John",
        "lastName": "Doe",
        "email": "john@example.com",
        "phone": "555-1234",
        "What management services do you request?": "Full Service Vessel Management",
        "zip_code_of_service": "33139"
    }
    
    print("\n" + "="*60)
    print("TEST 1: Yacht Management Service Request")
    print("="*60)
    print("Input payload:")
    print(json.dumps(test_payload_1, indent=2))
    
    processed_data, service_metadata = process_webhook_with_service_mapping(test_payload_1)
    
    print("\nService Classification:")
    print(f"  Level 1: {service_metadata.get('primary_category')}")
    print(f"  Level 2: {service_metadata.get('service_type')}")
    print(f"  Level 3: {service_metadata.get('specific_service')}")
    print(f"  Priority: {service_metadata.get('routing_priority')}")
    
    print("\nConsolidated Fields:")
    print(f"  specific_service_requested: {processed_data.get('specific_service_requested')}")
    
    # Test Case 2: Attorney Service Request
    test_payload_2 = {
        "firstName": "Jane",
        "lastName": "Smith",
        "email": "jane@example.com",
        "What specific attorney service do you request?": "Maritime Personal Injury Case",
        "Location": "Miami, FL"
    }
    
    print("\n" + "="*60)
    print("TEST 2: Maritime Attorney Service Request")
    print("="*60)
    print("Input payload:")
    print(json.dumps(test_payload_2, indent=2))
    
    processed_data, service_metadata = process_webhook_with_service_mapping(test_payload_2)
    
    print("\nService Classification:")
    print(f"  Level 1: {service_metadata.get('primary_category')}")
    print(f"  Level 2: {service_metadata.get('service_type')}")
    print(f"  Level 3: {service_metadata.get('specific_service')}")
    print(f"  Priority: {service_metadata.get('routing_priority')}")
    
    print("\nConsolidated Fields:")
    print(f"  specific_service_requested: {processed_data.get('specific_service_requested')}")
    
    # Test Case 3: Charter Service Request
    test_payload_3 = {
        "firstName": "Bob",
        "lastName": "Johnson",
        "Your Contact Email?": "bob@example.com",
        "Phone Number": "555-5678",
        "What type of private yacht charter are you interested in?": "Day Yacht Charter",
        "Service Zip Code": "33316"
    }
    
    print("\n" + "="*60)
    print("TEST 3: Yacht Charter Service Request")
    print("="*60)
    print("Input payload:")
    print(json.dumps(test_payload_3, indent=2))
    
    processed_data, service_metadata = process_webhook_with_service_mapping(test_payload_3)
    
    print("\nService Classification:")
    print(f"  Level 1: {service_metadata.get('primary_category')}")
    print(f"  Level 2: {service_metadata.get('service_type')}")
    print(f"  Level 3: {service_metadata.get('specific_service')}")
    print(f"  Priority: {service_metadata.get('routing_priority')}")
    
    print("\nConsolidated Fields:")
    print(f"  specific_service_requested: {processed_data.get('specific_service_requested')}")
    print(f"  email: {processed_data.get('email')}")
    print(f"  phone: {processed_data.get('phone')}")
    
    # Test Case 4: Multiple redundant fields
    test_payload_4 = {
        "first_name": "Alice",
        "last_name": "Williams",
        "Email": "alice@example.com",
        "What specific parts do you request?": "Engine & Propulsion Parts",
        "What type of fuel do you need?": "Rec 90 (Ethanol Free Gas)",
        "zip": "33101"
    }
    
    print("\n" + "="*60)
    print("TEST 4: Multiple Service Requests (Parts & Fuel)")
    print("="*60)
    print("Input payload:")
    print(json.dumps(test_payload_4, indent=2))
    
    processed_data, service_metadata = process_webhook_with_service_mapping(test_payload_4)
    
    print("\nService Classification:")
    print(f"  Level 1: {service_metadata.get('primary_category')}")
    print(f"  Level 2: {service_metadata.get('service_type')}")
    print(f"  Level 3: {service_metadata.get('specific_service')}")
    print(f"  Priority: {service_metadata.get('routing_priority')}")
    
    print("\nConsolidated Fields:")
    print(f"  specific_service_requested: {processed_data.get('specific_service_requested')}")
    print(f"  All standardized fields: {list(processed_data.keys())}")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    test_service_mapping()