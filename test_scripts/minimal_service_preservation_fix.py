#!/usr/bin/env python3
"""
Minimal Service Preservation Fix
Fixes the critical service corruption issue in ai_classifier.py
Preserves original service details while keeping AI classifications as additional context.
"""

import os
from pathlib import Path

def apply_service_preservation_fix():
    """
    Apply the minimal fix to preserve original service details in AI classifier.
    This fixes the core issue where "Inboard Engine Service" gets corrupted.
    """
    
    ai_classifier_path = Path("api/services/ai_classifier.py")
    
    if not ai_classifier_path.exists():
        print(f"❌ Could not find {ai_classifier_path}")
        return False
    
    # Read current file
    with open(ai_classifier_path, 'r') as f:
        content = f.read()
    
    # Create backup
    backup_path = ai_classifier_path.with_suffix('.py.backup_preservation')
    with open(backup_path, 'w') as f:
        f.write(content)
    print(f"📦 Backup created: {backup_path}")
    
    # Find and replace the _find_specific_services method
    old_method_start = "def _find_specific_services(self, service_requested: str, special_requests: str, primary_category: Dict) -> List[str]:"
    
    if old_method_start not in content:
        print("❌ Could not find _find_specific_services method")
        return False
    
    # Create the fixed method
    new_method = '''    def _find_specific_services(self, service_requested: str, special_requests: str, primary_category: Dict) -> List[str]:
        """
        FIXED VERSION: Preserve original service details instead of replacing them.
        Maintains backward compatibility while fixing data corruption.
        """
        specific_services = []
        category_name = primary_category["category"]
        
        # STEP 1: Always preserve the original service if it's meaningful
        if service_requested and len(service_requested.strip()) > 3:
            original_service = service_requested.strip()
            specific_services.append(original_service)
            print(f"🔒 PRESERVED ORIGINAL: '{original_service}'")
        
        # STEP 2: Add AI categorized services (only if different from original)
        available_services = self.specific_services_map.get(category_name, [])
        search_text = f"{service_requested} {special_requests}".lower()
        
        for service in available_services:
            service_lower = service.lower()
            original_lower = service_requested.lower() if service_requested else ""
            
            # Only add AI service if it's different from the original
            if (service_lower != original_lower and
                service not in specific_services and
                (service_lower in search_text or 
                 any(word in search_text for word in service_lower.split() if len(word) > 3))):
                specific_services.append(service)
                print(f"➕ ADDED AI SERVICE: '{service}'")
        
        # STEP 3: Fallback if we have nothing
        if not specific_services:
            specific_services = [category_name]
            print(f"🔄 FALLBACK TO CATEGORY: '{category_name}'")
        
        print(f"✅ FINAL SERVICES: {specific_services}")
        return specific_services'''
    
    # Find the complete old method to replace
    lines = content.split('\n')
    start_idx = -1
    end_idx = -1
    
    for i, line in enumerate(lines):
        if old_method_start in line:
            start_idx = i
            break
    
    if start_idx == -1:
        print("❌ Could not find method start")
        return False
    
    # Find the end of the method
    method_indent = len(lines[start_idx]) - len(lines[start_idx].lstrip())
    
    for i in range(start_idx + 1, len(lines)):
        line = lines[i]
        if line.strip() == "":
            continue
        
        current_indent = len(line) - len(line.lstrip())
        
        # If we hit a line with same or less indentation, method is done
        if current_indent <= method_indent and line.strip():
            end_idx = i
            break
    
    if end_idx == -1:
        end_idx = len(lines)
    
    # Replace the old method with the new one
    new_lines = lines[:start_idx] + new_method.split('\n') + lines[end_idx:]
    new_content = '\n'.join(new_lines)
    
    # Write the fixed file
    with open(ai_classifier_path, 'w') as f:
        f.write(new_content)
    
    print("✅ Applied service preservation fix to ai_classifier.py")
    print("🎯 Original service details will now be preserved!")
    return True

def test_fix():
    """
    Test that the fix works correctly
    """
    print("\n🧪 Testing the fix...")
    
    try:
        from api.services.ai_classifier import AIServiceClassifier
        
        classifier = AIServiceClassifier("marine")
        
        # Test with the actual problematic data from your debug log
        test_data = {
            "specific_service_needed": "Inboard Engine Service",
            "special_requests__notes": "testing webhooks",
            "form_identifier": "engines_generators"
        }
        
        print(f"📋 Input: '{test_data['specific_service_needed']}'")
        
        if hasattr(classifier, 'classify_service_detailed'):
            result = classifier.classify_service_detailed(test_data)
            specific_services = result.get('specific_services', [])
            
            print(f"📤 Output: {specific_services}")
            
            # Check if original is preserved
            if "Inboard Engine Service" in specific_services:
                print("✅ SUCCESS: Original service preserved!")
                return True
            else:
                print("❌ FAILED: Original service not preserved")
                return False
        else:
            print("⚠️ classify_service_detailed method not found")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """
    Apply the service preservation fix and test it
    """
    print("🔧 MINIMAL SERVICE PRESERVATION FIX")
    print("=" * 50)
    
    print("🎯 Problem: 'Inboard Engine Service' gets corrupted to generic services")
    print("🛠️ Solution: Preserve original service + add AI insights as additional context")
    
    print("\n🔄 Applying fix...")
    success = apply_service_preservation_fix()
    
    if success:
        print("\n🧪 Testing fix...")
        test_success = test_fix()
        
        if test_success:
            print("\n🎉 SUCCESS!")
            print("✅ Service preservation fix applied and tested")
            print("🔄 Restart your webhook server to apply changes")
            print("\n📋 Expected result:")
            print("  Input: 'Inboard Engine Service'")
            print("  Output: ['Inboard Engine Service', 'Engine Service or Sales']")
            print("  ✅ Original preserved + AI insights added")
        else:
            print("\n⚠️ Fix applied but test failed")
            print("Please restart your webhook server and test manually")
    else:
        print("\n❌ Fix failed to apply")
        print("Please check the error messages above")

if __name__ == "__main__":
    main()