#!/usr/bin/env python3
"""
Fix for the race condition in opportunity assignment
The issue: When multiple leads come in quickly, the background tasks
may use the wrong vendor's GHL user ID due to shared state
"""

import sqlite3
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GHL_LOCATION_ID = os.getenv('GHL_LOCATION_ID')
GHL_PRIVATE_TOKEN = os.getenv('GHL_PRIVATE_TOKEN')

def fix_barnacle_opportunity_assignments():
    """
    Fix the incorrectly assigned opportunities
    """
    conn = sqlite3.connect('smart_lead_router.db')
    cursor = conn.cursor()
    
    print("=" * 80)
    print("FIXING BARNACLE CLEANING OPPORTUNITY ASSIGNMENTS")
    print("=" * 80)
    
    # Get the leads that need fixing
    cursor.execute("""
    SELECT 
        l.id,
        l.customer_name,
        l.ghl_opportunity_id,
        l.vendor_id,
        v.company_name,
        v.ghl_user_id
    FROM leads l
    JOIN vendors v ON l.vendor_id = v.id
    WHERE l.specific_service_requested = 'Barnacle Cleaning'
    ORDER BY l.created_at
    """)
    
    leads = cursor.fetchall()
    
    # Check each lead
    for lead in leads:
        lead_id = lead[0]
        customer_name = lead[1]
        opportunity_id = lead[2]
        vendor_id = lead[3]
        vendor_name = lead[4]
        correct_ghl_user_id = lead[5]
        
        print(f"\nLead: {lead_id}")
        print(f"  Customer: {customer_name}")
        print(f"  Opportunity: {opportunity_id}")
        print(f"  Should be assigned to: {vendor_name}")
        print(f"  Correct GHL User ID: {correct_ghl_user_id}")
        
        # Fix the first lead (Vendor1) which was incorrectly assigned to Vendor2
        if vendor_name == "BRP BM Vendor1 T13" and correct_ghl_user_id == "8TlskoHjoHyAVO05ceZX":
            print(f"  ⚠️ This opportunity needs to be reassigned from Vendor2 to Vendor1")
            
            if input("  Fix this assignment? (y/n): ").lower() == 'y':
                # Update opportunity in GHL
                update_opportunity_assignment(opportunity_id, correct_ghl_user_id)
    
    conn.close()

def update_opportunity_assignment(opportunity_id, ghl_user_id):
    """
    Update opportunity assignment in GHL
    """
    url = f"https://services.leadconnectorhq.com/opportunities/{opportunity_id}"
    
    headers = {
        "Authorization": f"Bearer {GHL_PRIVATE_TOKEN}",
        "Version": "2021-07-28",
        "Content-Type": "application/json"
    }
    
    payload = {
        "assignedTo": ghl_user_id
    }
    
    print(f"  Updating opportunity {opportunity_id} to user {ghl_user_id}...")
    
    try:
        response = requests.put(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            print(f"  ✅ Successfully reassigned opportunity!")
        else:
            print(f"  ❌ Failed to update: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

def propose_code_fix():
    """
    Propose a code fix for the race condition
    """
    print("\n" + "=" * 80)
    print("PROPOSED CODE FIX")
    print("=" * 80)
    
    print("""
The issue is in the background task `trigger_clean_lead_routing_workflow`.
When multiple leads come in quickly, the background tasks may overlap.

SOLUTION: Make the vendor assignment atomic by:

1. Pass the vendor_ghl_user_id directly to the background task
2. Don't re-fetch vendor data in the background task
3. Use the vendor data that was selected during the initial request

In webhook_routes.py, modify the background task call:

```python
# Current (buggy):
background_tasks.add_task(
    trigger_clean_lead_routing_workflow, 
    ghl_contact_id=final_ghl_contact_id,
    form_identifier=form_identifier,
    form_config=form_config,
    form_data=elementor_payload
)

# Fixed:
background_tasks.add_task(
    trigger_clean_lead_routing_workflow, 
    ghl_contact_id=final_ghl_contact_id,
    form_identifier=form_identifier,
    form_config=form_config,
    form_data=elementor_payload,
    selected_vendor_id=selected_vendor['id'] if selected_vendor else None,  # Pass vendor ID
    selected_vendor_ghl_user=selected_vendor['ghl_user_id'] if selected_vendor else None  # Pass GHL user
)
```

And in the background task, use the passed values instead of re-fetching.
""")

if __name__ == "__main__":
    fix_barnacle_opportunity_assignments()
    propose_code_fix()
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)