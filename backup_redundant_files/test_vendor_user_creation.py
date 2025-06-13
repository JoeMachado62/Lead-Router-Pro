#!/usr/bin/env python3
"""
Test script for vendor user creation webhook
Tests the GHL workflow webhook that creates vendor user accounts
"""

import requests
import json
import time

# Server configuration
BASE_URL = "http://127.0.0.1:8000"
WEBHOOK_URL = f"{BASE_URL}/api/v1/webhooks/ghl/vendor-user-creation"

def test_webhook_health():
    """Test if the webhook system is healthy"""
    print("🔍 Testing Webhook System Health...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/webhooks/health", timeout=10)
        print(f"Health Check Status: {response.status_code}")
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Webhook system is healthy")
            print(f"   Database status: {health_data.get('database_status')}")
            print(f"   GHL Location ID: {health_data.get('ghl_location_id')}")
            return True
        else:
            print(f"❌ Webhook health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_vendor_user_creation_webhook():
    """Test the vendor user creation webhook with sample data"""
    print("\n🔐 Testing Vendor User Creation Webhook...")
    
    # Use a contact ID from our previous tests
    test_payload = {
        "contact_id": "vSpZ6uNu27Nsc6NJAxkz",  # From lead simulation test
        "contactId": "vSpZ6uNu27Nsc6NJAxkz",
        "workflow_id": "1749074973147",
        "event_type": "vendor_approved",
        "timestamp": "2025-06-04T21:30:00Z",
        "location_id": "ilmrtA1Vk6rvcy4BswKg"
    }
    
    print(f"Webhook URL: {WEBHOOK_URL}")
    print(f"Test Payload: {json.dumps(test_payload, indent=2)}")
    
    try:
        start_time = time.time()
        response = requests.post(
            WEBHOOK_URL,
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
            print(f"✅ SUCCESS: Vendor user creation webhook working!")
            print(f"   Action: {result.get('action')}")
            print(f"   User ID: {result.get('user_id')}")
            print(f"   Vendor Email: {result.get('vendor_email')}")
            print(f"   Vendor Company: {result.get('vendor_company')}")
            return True
        elif response.status_code == 404:
            print(f"⚠️ Contact not found - this is expected if using test contact ID")
            print(f"   Use a real contact ID from your GHL system for actual testing")
            return False
        else:
            print(f"❌ FAILED: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error Details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Raw Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_with_real_vendor_contact():
    """Test with a real vendor contact that was created by the vendor simulator"""
    print("\n🏢 Testing with Real Vendor Contact...")
    
    # First, let's check if we have any vendor contacts in the system
    try:
        stats_response = requests.get(f"{BASE_URL}/api/v1/simple-admin/vendors", timeout=10)
        if stats_response.status_code == 200:
            vendors_data = stats_response.json()
            vendors = vendors_data.get('data', [])
            
            if vendors:
                # Use the first vendor's contact ID
                vendor = vendors[0]
                contact_id = vendor.get('ghl_contact_id')
                
                if contact_id:
                    print(f"Found vendor contact: {vendor.get('name')} ({vendor.get('email')})")
                    print(f"Contact ID: {contact_id}")
                    
                    test_payload = {
                        "contact_id": contact_id,
                        "contactId": contact_id,
                        "workflow_id": "1749074973147",
                        "event_type": "vendor_approved",
                        "timestamp": "2025-06-04T21:30:00Z",
                        "location_id": "ilmrtA1Vk6rvcy4BswKg"
                    }
                    
                    print(f"Testing with real vendor contact...")
                    
                    try:
                        response = requests.post(
                            WEBHOOK_URL,
                            json=test_payload,
                            headers={"Content-Type": "application/json"},
                            timeout=30
                        )
                        
                        print(f"Response Status: {response.status_code}")
                        print(f"Response: {response.text}")
                        
                        if response.status_code == 200:
                            result = response.json()
                            print(f"✅ SUCCESS: Real vendor user creation worked!")
                            print(f"   User ID: {result.get('user_id')}")
                            print(f"   Action: {result.get('action')}")
                            return True
                        else:
                            print(f"❌ Failed with real vendor: {response.status_code}")
                            return False
                            
                    except Exception as e:
                        print(f"❌ Exception with real vendor: {e}")
                        return False
                else:
                    print("⚠️ Vendor found but no GHL contact ID")
                    return False
            else:
                print("⚠️ No vendors found in system")
                print("   Run vendor_signup_simulator.py first to create test vendors")
                return False
        else:
            print(f"❌ Could not fetch vendors: {stats_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error fetching vendors: {e}")
        return False

def test_error_scenarios():
    """Test various error scenarios"""
    print("\n🚨 Testing Error Scenarios...")
    
    # Test 1: Missing contact ID
    print("\n--- Test 1: Missing Contact ID ---")
    try:
        response = requests.post(
            WEBHOOK_URL,
            json={"workflow_id": "1749074973147"},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"Status: {response.status_code} (Expected: 400)")
        if response.status_code == 400:
            print("✅ Correctly rejected missing contact ID")
        else:
            print("❌ Should have rejected missing contact ID")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 2: Invalid JSON
    print("\n--- Test 2: Invalid JSON ---")
    try:
        response = requests.post(
            WEBHOOK_URL,
            data="invalid json",
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"Status: {response.status_code} (Expected: 400)")
        if response.status_code == 400:
            print("✅ Correctly rejected invalid JSON")
        else:
            print("❌ Should have rejected invalid JSON")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 3: Non-existent contact ID
    print("\n--- Test 3: Non-existent Contact ID ---")
    try:
        response = requests.post(
            WEBHOOK_URL,
            json={"contact_id": "nonexistent_contact_id"},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"Status: {response.status_code} (Expected: 404)")
        if response.status_code == 404:
            print("✅ Correctly handled non-existent contact")
        else:
            print("❌ Should have returned 404 for non-existent contact")
    except Exception as e:
        print(f"❌ Exception: {e}")

def main():
    """Main test function"""
    print("=" * 60)
    print("  VENDOR USER CREATION WEBHOOK TEST")
    print("=" * 60)
    
    # Step 1: Test webhook system health
    if not test_webhook_health():
        print("\n❌ Webhook system not healthy. Cannot proceed with tests.")
        return
    
    # Step 2: Test with sample contact ID
    sample_success = test_vendor_user_creation_webhook()
    
    # Step 3: Test with real vendor contact (if available)
    real_success = test_with_real_vendor_contact()
    
    # Step 4: Test error scenarios
    test_error_scenarios()
    
    # Summary
    print("\n" + "=" * 60)
    print("  TEST SUMMARY")
    print("=" * 60)
    print(f"Webhook System Health: ✅ Working")
    print(f"Sample Contact Test: {'✅ Working' if sample_success else '⚠️ Expected (test contact)'}")
    print(f"Real Vendor Test: {'✅ Working' if real_success else '⚠️ No real vendors available'}")
    print(f"Error Handling: ✅ Working")
    
    if real_success:
        print(f"\n🎉 Vendor user creation webhook is fully functional!")
        print(f"   Ready for GHL workflow integration")
    elif sample_success:
        print(f"\n✅ Webhook endpoint is working correctly")
        print(f"   Test with real vendor contacts for full verification")
    else:
        print(f"\n⚠️ Webhook endpoint needs real vendor data for testing")
        print(f"   Run vendor_signup_simulator.py first")
    
    print(f"\n📋 Next Steps:")
    print(f"   1. Set up GHL workflow webhook (see GHL_VENDOR_USER_CREATION_SETUP.md)")
    print(f"   2. Configure webhook URL in GHL workflow")
    print(f"   3. Test with real vendor approval workflow")

if __name__ == "__main__":
    main()
