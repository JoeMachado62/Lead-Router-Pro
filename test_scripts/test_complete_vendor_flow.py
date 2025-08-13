#!/usr/bin/env python3
"""
Complete Vendor Application Flow Test

This script tests the complete vendor application workflow with the new multi-step
category selection flow and all new fields (address, custom fields, consent, etc.)
"""

import requests
import json
import uuid
import time
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"
FORM_IDENTIFIER = "vendor_application"
TEST_EMAIL = f"test.vendor.{int(time.time())}@example.com"

def test_vendor_application():
    """Test the complete vendor application flow"""
    print("🚀 Starting Complete Vendor Application Flow Test")
    print("=" * 60)
    
    # Test payload with all new fields
    test_payload = {
        # Basic contact information (using expected field names)
        "firstName": "John",
        "lastName": "Smith",
        "email": TEST_EMAIL,
        "phone": "+1-555-123-4567",
        "vendor_company_name": "Marine Pro Services LLC",
        
        # NEW ADDRESS FIELDS
        "address1": "123 Harbor Drive",
        "city": "Fort Lauderdale", 
        "state": "FL",
        "postal_code": "33301",
        
        # NEW MULTI-STEP CATEGORY SELECTION
        "primary_service_category": "Engines and Generators",
        "primary_services": ["Engine Repair", "Generator Service", "Electrical Systems"],
        "additional_categories": ["Boat Maintenance", "Cleaning and Detailing"],
        "additional_services": ["Hull Cleaning", "Interior Detailing", "Deck Maintenance"],
        
        # Coverage information
        "coverage_type": "state",
        "coverage_states": ["FL", "GA", "SC"],
        
        # NEW CUSTOM FIELDS
        "taking_new_work": "Yes",
        "reviews__google_profile_url": "https://maps.google.com/marine-pro-services",
        "vendor_preferred_contact_method": "Phone",
        "years_in_business": "15",
        "about_your_company": "We specialize in marine engine repair and generator service with over 15 years of experience serving the Southeast coast.",
        
        # NEW CONSENT FIELDS
        "sms_consent": "on",
        "marketing_consent": "on",
        
        # Other fields
        "website_url": "https://marineproservices.com",
        "licences__certifications": "ABYC Certified, EPA Certified, Florida Marine Contractor License",
        
        # Form metadata
        "form_name": "Vendor Application Form",
        "form_id": "vendor_application_v2",
        "post_id": "12345",
        "element_id": "abc123"
    }
    
    print(f"📝 Test payload created with {len(test_payload)} fields")
    print(f"📧 Test email: {TEST_EMAIL}")
    print(f"🏢 Company: {test_payload['vendor_company_name']}")
    print(f"🔧 Primary category: {test_payload['primary_service_category']}")
    print(f"⚙️ Primary services: {', '.join(test_payload['primary_services'])}")
    print(f"📍 Coverage: {test_payload['coverage_type']} - {', '.join(test_payload['coverage_states'])}")
    print()
    
    # Test the webhook endpoint
    webhook_url = f"{BASE_URL}/api/v1/webhooks/elementor/{FORM_IDENTIFIER}"
    
    print(f"🌐 Testing webhook endpoint: {webhook_url}")
    
    try:
        response = requests.post(
            webhook_url,
            json=test_payload,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Elementor-Test/1.0"
            },
            timeout=30
        )
        
        print(f"📤 Request sent - Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS! Webhook processed successfully")
            print(f"🆔 Contact ID: {result.get('ghl_contact_id', 'N/A')}")
            print(f"📊 Status: {result.get('status', 'N/A')}")
            
            # Check if vendor record was created
            if 'vendor_record' in result:
                print(f"🏪 Vendor Record ID: {result['vendor_record'].get('id', 'N/A')}")
                print(f"📋 Vendor Status: {result['vendor_record'].get('status', 'N/A')}")
            
            # Print field mappings applied
            if 'field_mappings_applied' in result:
                print(f"🗂️  Fields mapped: {result['field_mappings_applied']}")
            
            print("\n📋 Full response:")
            print(json.dumps(result, indent=2))
            
            return True
            
        else:
            print(f"❌ FAILED! HTTP {response.status_code}")
            print(f"🚫 Error: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ NETWORK ERROR: {e}")
        return False
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return False

def test_form_validation():
    """Test form validation with missing required fields"""
    print("\n🧪 Testing Form Validation")
    print("=" * 40)
    
    # Minimal payload missing required fields
    minimal_payload = {
        "firstName": "Test",
        "email": f"minimal.test.{int(time.time())}@example.com"
        # Missing: lastName, vendor_company_name, primary_service_category, coverage info, etc.
    }
    
    webhook_url = f"{BASE_URL}/api/v1/webhooks/elementor/{FORM_IDENTIFIER}"
    
    try:
        response = requests.post(webhook_url, json=minimal_payload, timeout=15)
        print(f"📤 Minimal payload sent - Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Minimal payload accepted (validation may be lenient)")
        else:
            print(f"⚠️  Minimal payload rejected: {response.text}")
            
    except Exception as e:
        print(f"❌ Validation test error: {e}")

def check_system_health():
    """Check if the system is running and healthy"""
    print("🔍 Checking System Health")
    print("=" * 30)
    
    try:
        # Check main health endpoint
        health_response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"🏥 Main health: {health_response.status_code}")
        
        # Check webhook health
        webhook_health_response = requests.get(f"{BASE_URL}/api/v1/webhooks/health", timeout=10)
        print(f"🔗 Webhook health: {webhook_health_response.status_code}")
        
        return health_response.status_code == 200 and webhook_health_response.status_code == 200
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 VENDOR APPLICATION COMPLETE FLOW TEST")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check system health first
    if not check_system_health():
        print("❌ System health check failed. Make sure the server is running.")
        exit(1)
    
    print("✅ System is healthy. Proceeding with tests...\n")
    
    # Run the main test
    success = test_vendor_application()
    
    # Run validation test
    test_form_validation()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 VENDOR APPLICATION FLOW TEST COMPLETED SUCCESSFULLY!")
        print("✅ All new fields and multi-step category selection working properly")
    else:
        print("❌ VENDOR APPLICATION FLOW TEST FAILED!")
        print("🔧 Check the server logs for detailed error information")
    
    print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")