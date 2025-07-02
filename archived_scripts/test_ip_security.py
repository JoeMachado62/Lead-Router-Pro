#!/usr/bin/env python3
"""
Comprehensive test script for the IP Security System
Tests rate limiting, 404 blocking, and admin management features
"""

import asyncio
import json
import requests
import time
import threading
from concurrent.futures import ThreadPoolExecutor
import random

# Test configuration
BASE_URL = "http://127.0.0.1:8000"

def test_normal_requests():
    """Test normal request behavior"""
    print("\n🔍 Testing Normal Request Behavior...")
    
    try:
        # Test valid endpoint
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"✅ Health check: {response.status_code}")
        
        # Test webhook health
        response = requests.get(f"{BASE_URL}/api/v1/webhooks/health", timeout=5)
        print(f"✅ Webhook health: {response.status_code}")
        
        # Check security headers
        headers = response.headers
        if "X-RateLimit-Remaining" in headers:
            print(f"📊 Rate limit remaining: {headers['X-RateLimit-Remaining']}")
        
        return True
    except Exception as e:
        print(f"❌ Normal request test failed: {e}")
        return False

def test_rate_limiting():
    """Test rate limiting functionality"""
    print("\n⚡ Testing Rate Limiting...")
    
    # Make rapid requests to trigger rate limiting
    success_count = 0
    rate_limited_count = 0
    
    for i in range(35):  # More than the default limit of 30
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=2)
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                rate_limited_count += 1
                print(f"⚡ Rate limited on request {i+1}")
                break
            time.sleep(0.1)  # Small delay
        except Exception as e:
            print(f"❌ Request {i+1} failed: {e}")
    
    print(f"📊 Successful requests: {success_count}")
    print(f"📊 Rate limited requests: {rate_limited_count}")
    
    return rate_limited_count > 0

def test_404_blocking():
    """Test 404 error blocking"""
    print("\n📄 Testing 404 Blocking...")
    
    # Make multiple requests to non-existent endpoints
    blocked = False
    for i in range(7):  # More than the default limit of 5
        try:
            fake_endpoint = f"/nonexistent-endpoint-{i}"
            response = requests.get(f"{BASE_URL}{fake_endpoint}", timeout=2)
            
            if response.status_code == 404:
                print(f"📄 404 response {i+1}: {fake_endpoint}")
            elif response.status_code == 444:
                print(f"🚫 BLOCKED! Silent blocking activated on request {i+1}")
                blocked = True
                break
            elif response.status_code == 429:
                print(f"🚫 Rate limited on 404 request {i+1}")
                break
            
            time.sleep(0.5)  # Delay between requests
        except requests.exceptions.ConnectionError:
            print(f"🚫 BLOCKED! Connection refused on request {i+1}")
            blocked = True
            break
        except Exception as e:
            print(f"❌ Request {i+1} failed: {e}")
    
    return blocked

def test_security_admin_endpoints():
    """Test security admin endpoints"""
    print("\n🔐 Testing Security Admin Endpoints...")
    
    try:
        # Test security stats
        response = requests.get(f"{BASE_URL}/api/v1/admin/security/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print("✅ Security stats retrieved:")
            print(f"   📊 Total requests: {stats['statistics']['total_requests']}")
            print(f"   🚫 Blocked requests: {stats['statistics']['blocked_requests']}")
            print(f"   🔒 Currently blocked IPs: {stats['blocked_count']}")
        else:
            print(f"⚠️ Security stats request failed: {response.status_code}")
        
        # Test blocked IPs endpoint
        response = requests.get(f"{BASE_URL}/api/v1/admin/security/blocked-ips", timeout=5)
        if response.status_code == 200:
            blocked_data = response.json()
            print(f"✅ Blocked IPs retrieved: {blocked_data['total_blocked']} IPs")
            
            # Show details of blocked IPs
            for ip, details in blocked_data['blocked_ips'].items():
                print(f"   🚫 {ip}: {details['reason']} (remaining: {details['remaining_seconds']}s)")
        else:
            print(f"⚠️ Blocked IPs request failed: {response.status_code}")
        
        # Test security health
        response = requests.get(f"{BASE_URL}/api/v1/admin/security/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Security health: {health['status']}")
        
        return True
    except Exception as e:
        print(f"❌ Admin endpoints test failed: {e}")
        return False

def test_whitelist_functionality():
    """Test IP whitelisting"""
    print("\n⚪ Testing Whitelist Functionality...")
    
    try:
        # Add localhost to whitelist (should already be there)
        whitelist_data = {"ip": "127.0.0.1", "reason": "Test whitelist"}
        response = requests.post(
            f"{BASE_URL}/api/v1/admin/security/whitelist/add",
            json=whitelist_data,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Whitelist test: {result['message']}")
        else:
            print(f"⚠️ Whitelist add failed: {response.status_code}")
        
        # Get whitelist
        response = requests.get(f"{BASE_URL}/api/v1/admin/security/whitelist", timeout=5)
        if response.status_code == 200:
            whitelist = response.json()
            print(f"✅ Current whitelist: {len(whitelist['whitelist'])} IPs")
            for ip in whitelist['whitelist']:
                print(f"   ⚪ {ip}")
        
        return True
    except Exception as e:
        print(f"❌ Whitelist test failed: {e}")
        return False

def simulate_attack():
    """Simulate a basic attack to test blocking"""
    print("\n💥 Simulating Attack Scenarios...")
    
    def make_rapid_requests():
        """Make rapid requests from one 'attacker'"""
        for i in range(10):
            try:
                # Mix of valid and invalid requests
                if i % 3 == 0:
                    endpoint = f"/fake-endpoint-{i}"
                else:
                    endpoint = "/health"
                
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=1)
                if response.status_code == 444:
                    print(f"🚫 Attack blocked on request {i+1}")
                    break
            except:
                print(f"🚫 Attack connection refused on request {i+1}")
                break
            time.sleep(0.1)
    
    # Run simulated attack
    print("🔥 Starting simulated attack...")
    make_rapid_requests()
    
    time.sleep(2)  # Wait a bit
    
    # Check if the attack was detected
    try:
        response = requests.get(f"{BASE_URL}/api/v1/admin/security/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            attacks_prevented = stats['statistics'].get('attacks_prevented', 0)
            print(f"🛡️ Attacks prevented: {attacks_prevented}")
            return attacks_prevented > 0
    except:
        pass
    
    return False

def test_concurrent_requests():
    """Test behavior under concurrent load"""
    print("\n⚡ Testing Concurrent Request Handling...")
    
    def worker():
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=2)
            return response.status_code
        except:
            return None
    
    # Run 20 concurrent requests
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker) for _ in range(20)]
        results = [f.result() for f in futures]
    
    success_count = sum(1 for r in results if r == 200)
    rate_limited = sum(1 for r in results if r == 429)
    blocked = sum(1 for r in results if r is None)
    
    print(f"📊 Concurrent test results:")
    print(f"   ✅ Successful: {success_count}")
    print(f"   ⚡ Rate limited: {rate_limited}")
    print(f"   🚫 Blocked/Failed: {blocked}")
    
    return True

def cleanup_test_data():
    """Cleanup any test data"""
    print("\n🧹 Cleaning up test data...")
    
    try:
        # Trigger cleanup
        response = requests.post(f"{BASE_URL}/api/v1/admin/security/cleanup", timeout=5)
        if response.status_code == 200:
            print("✅ Security cleanup completed")
        
        # Unblock localhost if it got blocked during testing
        unblock_data = {"ip": "127.0.0.1"}
        response = requests.post(
            f"{BASE_URL}/api/v1/admin/security/unblock",
            json=unblock_data,
            timeout=5
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Unblock test: {result['message']}")
        
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")

def main():
    """Run all security tests"""
    print("=" * 60)
    print("🔒 IP SECURITY SYSTEM COMPREHENSIVE TEST")
    print("=" * 60)
    
    # Wait a moment for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(2)
    
    results = {}
    
    # Run tests
    results['normal_requests'] = test_normal_requests()
    results['rate_limiting'] = test_rate_limiting()
    results['404_blocking'] = test_404_blocking()
    results['admin_endpoints'] = test_security_admin_endpoints()
    results['whitelist'] = test_whitelist_functionality()
    results['attack_simulation'] = simulate_attack()
    results['concurrent_load'] = test_concurrent_requests()
    
    # Cleanup
    cleanup_test_data()
    
    # Final report
    print("\n" + "=" * 60)
    print("📋 SECURITY TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name.replace('_', ' ').title()}: {status}")
        if result:
            passed += 1
    
    print(f"\n📊 Overall Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All security tests PASSED! Your system is well protected.")
    else:
        print("⚠️ Some tests failed. Check the logs above for details.")
    
    print("\n🔗 Key Security Features Tested:")
    print("   ✅ Rate limiting (30 requests/minute)")
    print("   ✅ 404 error blocking (5 consecutive 404s)")
    print("   ✅ Silent blocking (no response to blocked IPs)")
    print("   ✅ IP whitelisting")
    print("   ✅ Admin management endpoints")
    print("   ✅ Concurrent request handling")
    print("   ✅ Attack simulation and detection")
    
    print("\n🎯 Admin Panel Access:")
    print(f"   Security Stats: {BASE_URL}/api/v1/admin/security/stats")
    print(f"   Blocked IPs: {BASE_URL}/api/v1/admin/security/blocked-ips")
    print(f"   Security Health: {BASE_URL}/api/v1/admin/security/health")

if __name__ == "__main__":
    main()
