#!/usr/bin/env python3
"""
Script to apply the reassignment endpoint fixes.
This updates the existing endpoints to use the new core logic.
"""

import os
import sys
from datetime import datetime

def backup_file(filepath):
    """Create a backup of the file before modification"""
    if os.path.exists(filepath):
        backup_path = f"{filepath}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        with open(filepath, 'r') as f:
            content = f.read()
        with open(backup_path, 'w') as f:
            f.write(content)
        print(f"✅ Backed up {filepath} to {backup_path}")
        return backup_path
    return None

def apply_webhook_fix():
    """Update the webhook_routes.py to use the fixed reassignment handler"""
    print("\n📝 Updating webhook reassignment endpoint...")
    
    webhook_file = "api/routes/webhook_routes.py"
    backup_file(webhook_file)
    
    # Read the current file
    with open(webhook_file, 'r') as f:
        content = f.read()
    
    # Check if already fixed
    if 'lead_reassignment_core' in content:
        print("⚠️  Webhook already appears to be using core logic")
        return
    
    # Add import for the fixed handler
    import_line = "from api.routes.webhook_reassignment_fixed import handle_lead_reassignment_webhook_fixed\n"
    
    # Find the imports section and add our import
    if 'from api.services.webhook_integration_patch import' in content:
        content = content.replace(
            'from api.services.webhook_integration_patch import process_webhook_with_service_mapping',
            f'from api.services.webhook_integration_patch import process_webhook_with_service_mapping\n{import_line}'
        )
    
    # Replace the old endpoint with a call to the fixed one
    old_handler_start = '@router.post("/ghl/reassign-lead")\nasync def handle_lead_reassignment_webhook(request: Request):'
    new_handler = '''@router.post("/ghl/reassign-lead")
async def handle_lead_reassignment_webhook(request: Request):
    """
    FIXED: Delegates to the corrected reassignment handler that follows proper flow.
    """
    from api.routes.webhook_reassignment_fixed import handle_lead_reassignment_webhook_fixed
    return await handle_lead_reassignment_webhook_fixed(request)'''
    
    if old_handler_start in content:
        # Find the end of the function (next function or end of file)
        import re
        pattern = r'@router\.post\("/ghl/reassign-lead"\).*?(?=@router\.|$)'
        content = re.sub(pattern, new_handler + '\n\n', content, flags=re.DOTALL)
        
        print("✅ Updated webhook reassignment endpoint to use fixed handler")
    else:
        print("⚠️  Could not find webhook reassignment endpoint pattern to replace")
    
    # Write the updated content
    with open(webhook_file, 'w') as f:
        f.write(content)

def update_main_file():
    """Update main_working_final.py to include the fixed endpoints"""
    print("\n📝 Updating main application file...")
    
    main_file = "main_working_final.py"
    backup_file(main_file)
    
    with open(main_file, 'r') as f:
        content = f.read()
    
    # Check if already includes fixed endpoint
    if 'lead_reassignment_fixed' in content:
        print("⚠️  Main file already includes fixed endpoints")
        return
    
    # Add import for fixed endpoint
    if 'from api.routes.lead_reassignment import router as lead_reassignment_router' in content:
        content = content.replace(
            'from api.routes.lead_reassignment import router as lead_reassignment_router',
            '''from api.routes.lead_reassignment import router as lead_reassignment_router
from api.routes.lead_reassignment_fixed import router as lead_reassignment_fixed_router'''
        )
        
        # Add router registration
        if 'app.include_router(lead_reassignment_router)' in content:
            content = content.replace(
                'app.include_router(lead_reassignment_router)',
                '''app.include_router(lead_reassignment_router)
app.include_router(lead_reassignment_fixed_router)  # Fixed endpoints with proper flow'''
            )
        
        print("✅ Added fixed reassignment endpoints to main application")
    
    with open(main_file, 'w') as f:
        f.write(content)

def create_test_script():
    """Create a test script to verify the fixes"""
    print("\n📝 Creating test script...")
    
    test_script = """#!/usr/bin/env python3
'''
Test script to verify reassignment endpoints are working correctly
'''

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_api_reassignment():
    '''Test the fixed API reassignment endpoint'''
    print("\\n🧪 Testing API reassignment endpoint...")
    
    # Test data - you'll need to update with a real contact_id
    test_data = {
        "contact_id": "YOUR_TEST_CONTACT_ID",
        "reason": "test_reassignment",
        "exclude_previous": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/reassignment/lead/fixed",
            json=test_data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print(f"✅ Reassignment successful: {result.get('message')}")
                print(f"   Lead ID: {result.get('lead_id')}")
                print(f"   Opportunity ID: {result.get('opportunity_id')}")
                print(f"   New Vendor: {result.get('vendor_name')}")
            else:
                print(f"⚠️ Reassignment failed: {result.get('message')}")
        else:
            print(f"❌ API error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

def test_webhook_reassignment():
    '''Test the webhook reassignment endpoint'''
    print("\\n🧪 Testing webhook reassignment endpoint...")
    
    # Test webhook payload
    test_payload = {
        "contact_id": "YOUR_TEST_CONTACT_ID",
        "opportunity_id": None,  # Will create if needed
        "reason": "webhook_test"
    }
    
    headers = {
        "X-Webhook-API-Key": "YOUR_WEBHOOK_API_KEY",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/webhooks/ghl/reassign-lead",
            json=test_payload,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Webhook processed: {result.get('status')}")
            print(f"   Message: {result.get('message')}")
        else:
            print(f"❌ Webhook error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

def test_history():
    '''Test reassignment history endpoint'''
    print("\\n🧪 Testing reassignment history...")
    
    contact_id = "YOUR_TEST_CONTACT_ID"
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/reassignment/history/{contact_id}"
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ History retrieved successfully")
            print(f"   Lead ID: {result.get('lead_id')}")
            print(f"   Original Source: {result.get('original_source')}")
            print(f"   Reassignment Count: {result.get('reassignment_count')}")
        else:
            print(f"❌ History error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("REASSIGNMENT ENDPOINT TESTS")
    print("=" * 60)
    print("\\n⚠️  Update the test contact IDs before running!")
    print("⚠️  Make sure the application is running on localhost:8000")
    
    # Uncomment to run tests
    # test_api_reassignment()
    # test_webhook_reassignment() 
    # test_history()
    
    print("\\n" + "=" * 60)
"""
    
    with open('test_reassignment_endpoints.py', 'w') as f:
        f.write(test_script)
    
    print("✅ Created test_reassignment_endpoints.py")

def main():
    print("=" * 80)
    print("APPLYING REASSIGNMENT ENDPOINT FIXES")
    print("=" * 80)
    
    print("\n📌 This script will:")
    print("1. Update webhook reassignment to use core logic")
    print("2. Add fixed API endpoints that preserve source")
    print("3. Ensure proper flow: opportunity → lead → vendor")
    print("4. Update GHL opportunities with vendor assignments")
    
    response = input("\nProceed with updates? (y/n): ")
    if response.lower() != 'y':
        print("❌ Aborted")
        return
    
    try:
        # Apply fixes
        apply_webhook_fix()
        update_main_file()
        create_test_script()
        
        print("\n" + "=" * 80)
        print("✅ FIXES APPLIED SUCCESSFULLY")
        print("=" * 80)
        
        print("\n📌 Next steps:")
        print("1. Restart the application: python main_working_final.py")
        print("2. Test the endpoints using test_reassignment_endpoints.py")
        print("3. Monitor logs for any issues")
        
        print("\n📌 New endpoints available:")
        print("- /api/v1/reassignment/lead/fixed - Fixed API endpoint")
        print("- /api/v1/reassignment/bulk/fixed - Fixed bulk endpoint")
        print("- /api/v1/webhooks/ghl/reassign-lead - Fixed webhook endpoint")
        
        print("\n⚠️  IMPORTANT: The source column will now be preserved during bulk operations!")
        
    except Exception as e:
        print(f"\n❌ Error applying fixes: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()