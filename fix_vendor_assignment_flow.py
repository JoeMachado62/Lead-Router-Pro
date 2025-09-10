#!/usr/bin/env python3
"""
Fix script to correct the vendor assignment flow in webhook_routes.py
This script identifies the key issues and provides the fixes needed.

ISSUES IDENTIFIED:
1. Vendor pre-selection happens BEFORE opportunity creation (backwards)
2. Lead is created WITHOUT opportunity_id initially
3. Vendor assignment logic is scattered and not triggered properly
4. No support for preferred vendor from form submission

CORRECT FLOW:
1. Create GHL contact
2. Create opportunity FIRST
3. Create lead WITH opportunity_id
4. Trigger vendor selection based on lead data
5. Update lead with vendor_id
6. Update GHL opportunity with vendor's GHL User ID
"""

import os
import sys

def main():
    print("=" * 80)
    print("VENDOR ASSIGNMENT FLOW FIX ANALYSIS")
    print("=" * 80)
    
    print("\n📋 CURRENT ISSUES FOUND:")
    print("-" * 40)
    
    issues = [
        {
            "issue": "Pre-selection happens too early",
            "location": "webhook_routes.py:1890-1933",
            "description": "Vendor is pre-selected BEFORE opportunity exists",
            "impact": "Can't assign vendor to non-existent opportunity"
        },
        {
            "issue": "Lead created without opportunity_id",
            "location": "webhook_routes.py:2129",
            "description": "Lead INSERT has NULL for ghl_opportunity_id",
            "impact": "Vendor selection can't link to opportunity"
        },
        {
            "issue": "Opportunity created AFTER lead",
            "location": "webhook_routes.py:2165-2199",
            "description": "Opportunity is created after lead insertion",
            "impact": "Lead exists without opportunity_id initially"
        },
        {
            "issue": "Vendor assignment scattered",
            "location": "webhook_routes.py:2232-2280",
            "description": "Assignment logic split between pre-selection and fallback",
            "impact": "Inconsistent assignment behavior"
        }
    ]
    
    for i, issue in enumerate(issues, 1):
        print(f"\n{i}. {issue['issue']}")
        print(f"   Location: {issue['location']}")
        print(f"   Description: {issue['description']}")
        print(f"   Impact: {issue['impact']}")
    
    print("\n\n✅ RECOMMENDED FIXES:")
    print("-" * 40)
    
    fixes = [
        {
            "fix": "Remove pre-selection logic",
            "action": "Delete lines 1890-1933 (vendor pre-selection before background task)"
        },
        {
            "fix": "Create opportunity BEFORE lead",
            "action": "Move opportunity creation (lines 2165-2223) BEFORE lead creation (lines 2096-2162)"
        },
        {
            "fix": "Pass opportunity_id to lead INSERT",
            "action": "Change line 2129 from 'None' to 'opportunity_id'"
        },
        {
            "fix": "Create vendor assignment function",
            "action": "Add new async function to handle vendor selection AFTER lead creation"
        },
        {
            "fix": "Trigger vendor assignment after lead creation",
            "action": "Call vendor assignment function after lead INSERT with opportunity_id"
        }
    ]
    
    for i, fix in enumerate(fixes, 1):
        print(f"\n{i}. {fix['fix']}")
        print(f"   Action: {fix['action']}")
    
    print("\n\n📝 KEY CODE CHANGES NEEDED:")
    print("-" * 40)
    
    print("""
1. In trigger_clean_lead_routing_workflow function:
   
   OLD ORDER:
   - Create lead (without opportunity_id)
   - Create opportunity
   - Try to assign pre-selected vendor
   
   NEW ORDER:
   - Create opportunity FIRST
   - Create lead WITH opportunity_id
   - Trigger vendor selection based on lead data
   - Update opportunity with selected vendor

2. Remove pre-selection logic from main webhook handler

3. Add new function for vendor assignment:
   async def assign_vendor_to_lead(lead_id, opportunity_id, service, location):
       # Find matching vendors
       # Select vendor via algorithm
       # Update lead with vendor_id
       # Update GHL opportunity with vendor's GHL User ID

4. Update lead status to track assignment:
   - "pending_assignment" - awaiting vendor selection
   - "assigned" - vendor selected and notified
   - "unassigned" - no vendors available
""")
    
    print("\n\n🔧 IMPLEMENTATION STEPS:")
    print("-" * 40)
    print("""
1. Backup current webhook_routes.py
2. Apply fixes using webhook_routes_fixed.py as reference
3. Test with a sample lead submission
4. Verify opportunity gets assignedTo field set
5. Monitor logs for successful assignments
""")
    
    print("\n\n⚠️  IMPORTANT NOTES:")
    print("-" * 40)
    print("""
- This fix ensures opportunities are ALWAYS created before vendor selection
- Vendor selection will only trigger for leads with opportunity_ids
- Existing leads without opportunity_ids will need manual correction
- The fix maintains backward compatibility with existing database schema
""")
    
    print("\n" + "=" * 80)
    print("Run this command to backup and apply the fix:")
    print("cp api/routes/webhook_routes.py api/routes/webhook_routes.py.backup_$(date +%Y%m%d)")
    print("Then manually apply the fixes or use the webhook_routes_fixed.py as reference")
    print("=" * 80)

if __name__ == "__main__":
    main()