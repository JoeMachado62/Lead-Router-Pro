#!/usr/bin/env python3
"""
Script to trace the exact lead assignment process and find where contacts might be created
"""

import re

def analyze_webhook_code():
    """
    Analyze the webhook code to trace the lead assignment process
    """
    print("🔍 TRACING LEAD ASSIGNMENT PROCESS")
    print("=" * 60)
    
    # Read the webhook routes file
    try:
        with open("api/routes/webhook_routes.py", "r") as f:
            webhook_code = f.read()
        
        print("✅ Successfully read webhook_routes.py")
        
        # Find the lead assignment section
        print("\n🎯 SEARCHING FOR LEAD ASSIGNMENT LOGIC:")
        print("-" * 50)
        
        # Look for vendor matching logic
        vendor_matching_pattern = r'find_matching_vendors.*?else:'
        vendor_matches = re.findall(vendor_matching_pattern, webhook_code, re.DOTALL)
        
        if vendor_matches:
            print("✅ Found vendor matching logic")
            for i, match in enumerate(vendor_matches):
                print(f"\nVendor Matching Block {i+1}:")
                print(match[:200] + "..." if len(match) > 200 else match)
        
        # Look for notification functions
        print("\n🔍 SEARCHING FOR NOTIFICATION FUNCTIONS:")
        print("-" * 50)
        
        notification_patterns = [
            r'notify_vendor_of_new_lead.*?except.*?logger\.error',
            r'notify_admin.*?except.*?logger\.error',
            r'send_sms.*?contact_id',
            r'send_email.*?contact_id'
        ]
        
        for pattern in notification_patterns:
            matches = re.findall(pattern, webhook_code, re.DOTALL)
            if matches:
                print(f"✅ Found notification pattern: {pattern[:30]}...")
                for match in matches:
                    print(f"  {match[:150]}...")
        
        # Look for any hardcoded contact IDs or phone numbers
        print("\n🚨 SEARCHING FOR HARDCODED CONTACT INFO:")
        print("-" * 50)
        
        # Look for Jeremy's info
        jeremy_patterns = [
            r'952.*393.*3536',
            r'jeremy',
            r'docksidepros',
            r'b69NCeI1P32jooC7ySfw'
        ]
        
        for pattern in jeremy_patterns:
            matches = re.findall(pattern, webhook_code, re.IGNORECASE)
            if matches:
                print(f"🚨 FOUND JEREMY'S INFO: {pattern} -> {matches}")
        
        # Look for any contact creation calls
        print("\n🔍 SEARCHING FOR CONTACT CREATION CALLS:")
        print("-" * 50)
        
        creation_patterns = [
            r'create_contact.*?\(',
            r'ghl_api_client\..*contact',
            r'\.send_sms\(',
            r'\.send_email\('
        ]
        
        for pattern in creation_patterns:
            matches = re.findall(pattern, webhook_code, re.IGNORECASE)
            if matches:
                print(f"✅ Found creation pattern: {pattern}")
                for match in matches:
                    print(f"  {match}")
        
        # Look for the specific "no vendors found" handling
        print("\n🎯 ANALYZING 'NO VENDORS FOUND' HANDLING:")
        print("-" * 50)
        
        # Find the exact code that runs when no vendors are found
        no_vendors_pattern = r'else:.*?logger\.warning.*?No matching vendors.*?(?=\n\s*#|\n\s*$|\n\s*def|\n\s*class|\n\s*except|\n\s*finally)'
        no_vendors_matches = re.findall(no_vendors_pattern, webhook_code, re.DOTALL)
        
        if no_vendors_matches:
            print("✅ Found 'no vendors found' handling:")
            for match in no_vendors_matches:
                print(f"CODE BLOCK:\n{match}")
                
                # Check if this block contains any notification calls
                if 'notify_admin' in match:
                    print("🚨 FOUND: notify_admin call in no vendors block!")
                if 'send_sms' in match:
                    print("🚨 FOUND: send_sms call in no vendors block!")
                if 'create_contact' in match:
                    print("🚨 FOUND: create_contact call in no vendors block!")
        else:
            print("❌ No 'no vendors found' handling found")
        
        # Look for any background task calls
        print("\n🔍 SEARCHING FOR BACKGROUND TASK CALLS:")
        print("-" * 50)
        
        bg_task_pattern = r'background_tasks\.add_task.*?\)'
        bg_matches = re.findall(bg_task_pattern, webhook_code, re.DOTALL)
        
        if bg_matches:
            print("✅ Found background task calls:")
            for match in bg_matches:
                print(f"  {match}")
        
    except Exception as e:
        print(f"❌ Error reading webhook file: {e}")

def check_for_external_triggers():
    """
    Check if there are any external triggers that might create contacts
    """
    print("\n🔍 CHECKING FOR EXTERNAL TRIGGERS:")
    print("-" * 50)
    
    # Check if there are any GHL workflow files or configs
    import os
    
    files_to_check = [
        "config.py",
        ".env",
        "main_working_final.py"
    ]
    
    for filename in files_to_check:
        if os.path.exists(filename):
            try:
                with open(filename, "r") as f:
                    content = f.read()
                
                # Look for any webhook URLs or notification configs
                if '952' in content or 'jeremy' in content.lower() or 'docksidepros' in content.lower():
                    print(f"🚨 FOUND JEREMY'S INFO in {filename}!")
                    
                    # Show the relevant lines
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if '952' in line or 'jeremy' in line.lower() or 'docksidepros' in line.lower():
                            print(f"  Line {i+1}: {line.strip()}")
                
            except Exception as e:
                print(f"❌ Error reading {filename}: {e}")

def main():
    print("🕵️ INVESTIGATING LEAD ASSIGNMENT PROCESS")
    print("Looking for what creates contacts with Jeremy's info during 'no vendors found'...")
    print()
    
    analyze_webhook_code()
    check_for_external_triggers()
    
    print("\n" + "=" * 60)
    print("🎯 INVESTIGATION SUMMARY")
    print("=" * 60)
    print("Key findings:")
    print("1. Check if any hardcoded admin contact IDs were found")
    print("2. Look for notification calls in 'no vendors found' blocks")
    print("3. Verify if external configs contain Jeremy's contact info")
    print("4. The mysterious contacts might be created by:")
    print("   - Hidden notification logic")
    print("   - External GHL workflows triggered by webhooks")
    print("   - Background tasks with hardcoded admin info")

if __name__ == "__main__":
    main()
