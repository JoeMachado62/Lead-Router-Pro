#!/usr/bin/env python3
"""
Test script to verify external webhook functionality
Tests the external IP webhook endpoint with sample data
"""

import requests
import json
import time

# External server configuration
EXTERNAL_BASE_URL = "http://71.208.153.160:8000"
EXTERNAL_WEBHOOK_BASE = f"{EXTERNAL_BASE_URL}/api/v1/webhooks/elementor"

def test_external_server_health():
    """Test if the external server is accessible"""
    print("🔍 Testing External Server Health...")
    print(f"External URL: {EXTERNAL_BASE_URL}")
    
    try:
        response = requests.get(f"{EXTERNAL_BASE_URL}/health", timeout=10)
        print(f"Health Check Status: {response.status_code}")
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ External server is healthy")
            print(f"   Service: {health_data.get('service_name')}")
            print(f"   Database: {health_data.get('database_status')}")
            return True
        else:
            print(f"❌ External server health check failed: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectTimeout:
        print("❌ Connection timeout - server may not be running")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection refused - server not accessible")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_external_webhook_client_lead():
    """Test external webhook with a client lead"""
    print("\n🛥️ Testing External Webhook - Client Lead...")
    
    webhook_url = f"{EXTERNAL_WEBHOOK_BASE}/ceramic_coating_request"
    
    test_payload = {
        "firstName": "External",
        "lastName": "Test",
        "email": "external.test@example.com",
        "phone": "555-999-8888",
        "vessel_make": "Test Yacht",
        "vessel_model": "External Test Model",
        "vessel_year": "2023",
        "vessel_length_ft": "45",
        "vessel_location__slip": "Test Marina - External Slip",
        "specific_service_needed": "External webhook test - ceramic coating",
        "zip_code_of_service": "33139",
        "desired_timeline": "Test timeline",
        "budget_range": "$1000-$2000",
        "special_requests__notes": "This is a test from external webhook verification",
        "preferred_contact_method": "Email"
    }
    
    print(f"Webhook URL: {webhook_url}")
    print(f"Payload: {json.dumps(test_payload, indent=2)}")
    
    try:
        start_time = time.time()
        response = requests.post(
            webhook_url,
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        processing_time = round(time.time() - start_time, 3)
        
        print(f"Response Status: {response.status_code}")
        print(f"Processing Time: {processing_time}s")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS: External webhook working!")
            print(f"   Contact ID: {result.get('contact_id')}")
            print(f"   Action: {result.get('action')}")
            print(f"   Form Type: {result.get('form_type')}")
            return True
        else:
            print(f"❌ FAILED: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_external_webhook_vendor_application():
    """Test external webhook with a vendor application"""
    print("\n🏢 Testing External Webhook - Vendor Application...")
    
    webhook_url = f"{EXTERNAL_WEBHOOK_BASE}/vendor_application_detailing_specialist"
    
    test_payload = {
        "firstName": "External",
        "lastName": "Vendor",
        "email": "external.vendor@example.com",
        "phone": "555-888-7777",
        "vendor_company_name": "External Test Detailing LLC",
        "dba": "External Test",
        "years_in_business": "5",
        "services_provided": "External webhook test - boat detailing and maintenance",
        "primary_service_category": "Boat Maintenance",
        "service_zip_codes": "33139, 33154",
        "website_url": "https://externaltest.com",
        "licences__certifications": "External Test Certification",
        "insurance_coverage": "Test Insurance Coverage",
        "about_your_company": "This is a test vendor application from external webhook verification",
        "reviews__google_profile_url": "https://g.page/externaltest",
        "taking_new_work": "Yes",
        "vendor_preferred_contact_method": "Email"
    }
    
    print(f"Webhook URL: {webhook_url}")
    print(f"Payload: {json.dumps(test_payload, indent=2)}")
    
    try:
        start_time = time.time()
        response = requests.post(
            webhook_url,
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        processing_time = round(time.time() - start_time, 3)
        
        print(f"Response Status: {response.status_code}")
        print(f"Processing Time: {processing_time}s")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS: External webhook working!")
            print(f"   Contact ID: {result.get('contact_id')}")
            print(f"   Action: {result.get('action')}")
            print(f"   Form Type: {result.get('form_type')}")
            return True
        else:
            print(f"❌ FAILED: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("  EXTERNAL WEBHOOK TEST")
    print("=" * 60)
    print(f"Testing external server: {EXTERNAL_BASE_URL}")
    
    # Step 1: Test server health
    if not test_external_server_health():
        print("\n❌ External server not accessible. Cannot proceed with webhook tests.")
        print("\n💡 Possible issues:")
        print("   1. FastAPI server not running on external IP")
        print("   2. Firewall blocking port 8000")
        print("   3. Network connectivity issues")
        print("   4. Server configuration problems")
        return
    
    # Step 2: Test client lead webhook
    client_success = test_external_webhook_client_lead()
    
    # Step 3: Test vendor application webhook
    vendor_success = test_external_webhook_vendor_application()
    
    # Summary
    print("\n" + "=" * 60)
    print("  TEST SUMMARY")
    print("=" * 60)
    print(f"External Server Health: ✅ Working")
    print(f"Client Lead Webhook: {'✅ Working' if client_success else '❌ Failed'}")
    print(f"Vendor Application Webhook: {'✅ Working' if vendor_success else '❌ Failed'}")
    
    if client_success and vendor_success:
        print(f"\n🎉 All external webhook tests passed!")
        print(f"   Your external server is ready to receive webhooks from WordPress/Elementor")
        print(f"   Base URL: {EXTERNAL_BASE_URL}")
        print(f"   Webhook Base: {EXTERNAL_WEBHOOK_BASE}")
    else:
        print(f"\n⚠️ Some webhook tests failed.")
        print(f"   Check server logs and configuration.")

if __name__ == "__main__":
    main()
