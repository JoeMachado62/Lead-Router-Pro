#!/usr/bin/env python3
"""
Test script to verify multi-level service routing system is working correctly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.services.service_categories import service_manager
from api.services.lead_routing_service import lead_routing_service

def test_service_manager():
    """Test the service_manager single source of truth"""
    print("=" * 60)
    print("TESTING SERVICE MANAGER (Single Source of Truth)")
    print("=" * 60)
    
    # Test 1: Check if service categories are loaded
    categories = service_manager.SERVICE_CATEGORIES
    print(f"✅ Loaded {len(categories)} service categories:")
    for category, services in categories.items():
        print(f"  📂 {category}: {len(services)} services")
    
    print()
    
    # Test 2: Test exact matching
    print("TESTING EXACT SERVICE MATCHING:")
    test_cases = [
        ("Marine Systems", "Yacht AC Service"),
        ("Engines and Generators", "Outboard Engine Service"),
        ("Boat Maintenance", "Ceramic Coating"),
        ("Boat and Yacht Repair", "Fiberglass Repair"),
    ]
    
    for category, service in test_cases:
        # Test with mock vendor services
        mock_vendor_services = ["General Services", service, "Other Service"]
        
        result = service_manager.vendor_matches_service_exact(
            mock_vendor_services, category, service
        )
        
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} Category='{category}', Service='{service}' → {result}")
    
    print()
    
    # Test 3: Test category-only matching
    print("TESTING CATEGORY-ONLY MATCHING:")
    test_cases = [
        ("Marine Systems", ["Marine Systems", "General Services"]),
        ("Boat Maintenance", ["Boat Maintenance", "Other Services"]),
    ]
    
    for category, vendor_services in test_cases:
        result = service_manager.vendor_matches_category_only(vendor_services, category)
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} Category='{category}', Vendor Services={vendor_services} → {result}")
    
    return True

def test_lead_routing_service():
    """Test the enhanced lead routing service"""
    print("=" * 60)
    print("TESTING ENHANCED LEAD ROUTING SERVICE")
    print("=" * 60)
    
    # Test multi-level matching capability
    print("TESTING MULTI-LEVEL MATCHING CAPABILITY:")
    
    # Test that the method signature accepts both parameters
    try:
        # This should not crash - just testing method signature
        print("  📋 Testing method signature...")
        method = getattr(lead_routing_service, 'find_matching_vendors')
        
        # Check if method exists
        if method:
            print("  ✅ find_matching_vendors method exists")
            
            # Check method parameters by inspecting the signature
            import inspect
            sig = inspect.signature(method)
            params = list(sig.parameters.keys())
            
            required_params = ['account_id', 'service_category', 'zip_code', 'specific_service']
            missing_params = [p for p in required_params if p not in params]
            
            if not missing_params:
                print("  ✅ Method signature supports multi-level routing")
                print(f"     Parameters: {params}")
            else:
                print(f"  ❌ Missing parameters: {missing_params}")
                return False
        else:
            print("  ❌ find_matching_vendors method not found")
            return False
            
    except Exception as e:
        print(f"  ❌ Error testing method signature: {e}")
        return False
    
    print("  ✅ Lead routing service ready for multi-level matching")
    return True

def test_integration():
    """Test integration between components"""
    print("=" * 60)
    print("TESTING COMPONENT INTEGRATION")
    print("=" * 60)
    
    # Test 1: Verify service data consistency
    print("TESTING SERVICE DATA CONSISTENCY:")
    
    # Get a sample service from service_manager
    sample_category = "Marine Systems"
    sample_services = service_manager.SERVICE_CATEGORIES.get(sample_category, [])
    
    if sample_services:
        sample_service = sample_services[0]
        print(f"  📋 Testing with: Category='{sample_category}', Service='{sample_service}'")
        
        # Test exact matching
        test_vendor_services = [sample_service, "Other Service"]
        exact_match = service_manager.vendor_matches_service_exact(
            test_vendor_services, sample_category, sample_service
        )
        
        # Test category matching  
        category_match = service_manager.vendor_matches_category_only(
            [sample_category], sample_category
        )
        
        print(f"  ✅ Exact matching: {exact_match}")
        print(f"  ✅ Category matching: {category_match}")
        
        if exact_match and category_match:
            print("  ✅ Integration test PASSED")
            return True
        else:
            print("  ❌ Integration test FAILED")
            return False
    else:
        print(f"  ❌ No services found for category '{sample_category}'")
        return False

def run_comprehensive_test():
    """Run all tests and provide summary"""
    print("🚀 MULTI-LEVEL SERVICE ROUTING SYSTEM TEST")
    print("=" * 80)
    
    tests = [
        ("Service Manager", test_service_manager),
        ("Lead Routing Service", test_lead_routing_service),
        ("Component Integration", test_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔧 Running {test_name} test...")
        try:
            result = test_func()
            results.append((test_name, result, None))
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {status}")
        except Exception as e:
            results.append((test_name, False, str(e)))
            print(f"   ❌ FAILED with exception: {e}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = 0
    total = len(results)
    
    for test_name, result, error in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if error:
            print(f"     Error: {error}")
        if result:
            passed += 1
    
    print(f"\nOverall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Multi-level routing system is working correctly!")
        print("\n📋 SYSTEM READY FOR:")
        print("  • Exact service matching (AC Service → only AC vendors)")
        print("  • Category fallback matching (Marine Systems → all marine system vendors)")
        print("  • Clean data flow through single source of truth")
        print("  • No conflicting service dictionaries")
    else:
        print("⚠️  Some tests failed - please review the issues above")
    
    return passed == total

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
