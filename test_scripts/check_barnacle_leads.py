#!/usr/bin/env python3
"""
Check recent barnacle cleaning leads and their vendor assignments
to diagnose round-robin distribution issues
"""

import sqlite3
from datetime import datetime, timedelta
import json

def check_recent_barnacle_leads():
    """Check recent barnacle cleaning leads and assignments"""
    conn = sqlite3.connect('smart_lead_router.db')
    cursor = conn.cursor()
    
    print("=" * 80)
    print("BARNACLE CLEANING LEAD ANALYSIS")
    print("=" * 80)
    
    # 1. Get recent leads for barnacle cleaning
    print("\n1. RECENT BARNACLE CLEANING LEADS:")
    print("-" * 40)
    
    query = """
    SELECT 
        id,
        customer_name,
        primary_service_category,
        specific_service_requested,
        assigned_vendor_id,
        created_at,
        lead_quality_score,
        routing_priority,
        status
    FROM leads
    WHERE (
        LOWER(primary_service_category) LIKE '%barnacle%' 
        OR LOWER(specific_service_requested) LIKE '%barnacle%'
        OR LOWER(primary_service_category) LIKE '%boat maintenance%'
    )
    AND created_at > datetime('now', '-7 days')
    ORDER BY created_at DESC
    LIMIT 10
    """
    
    cursor.execute(query)
    leads = cursor.fetchall()
    
    if leads:
        for lead in leads:
            print(f"\nLead ID: {lead[0]}")
            print(f"  Contact: {lead[1]}")
            print(f"  Service: {lead[2]}")
            print(f"  Specific: {lead[3]}")
            print(f"  Vendor Assigned: {lead[4]}")
            print(f"  Created: {lead[5]}")
            print(f"  Score/Priority: {lead[6]}/{lead[7]}")
            print(f"  Status: {lead[8]}")
    else:
        print("No barnacle cleaning leads found in last 7 days")
    
    # 2. Check vendors offering barnacle cleaning
    print("\n2. VENDORS OFFERING BARNACLE CLEANING:")
    print("-" * 40)
    
    query = """
    SELECT 
        id,
        company_name,
        services_offered,
        total_leads_assigned,
        last_lead_assigned,
        is_active
    FROM vendors
    WHERE (
        LOWER(services_offered) LIKE '%barnacle%'
        OR LOWER(services_offered) LIKE '%boat maintenance%'
    )
    AND is_active = 1
    ORDER BY total_leads_assigned ASC
    """
    
    cursor.execute(query)
    vendors = cursor.fetchall()
    
    if vendors:
        print(f"Found {len(vendors)} active vendors offering barnacle cleaning:\n")
        for vendor in vendors:
            services = vendor[2][:100] + '...' if len(vendor[2]) > 100 else vendor[2]
            print(f"Vendor ID: {vendor[0]} - {vendor[1]}")
            print(f"  Services: {services}")
            print(f"  Total Leads: {vendor[3]}")
            print(f"  Last Lead: {vendor[4]}")
            print(f"  Active: {vendor[5]}")
            print()
    else:
        print("No vendors found offering barnacle cleaning")
    
    # 3. Check lead assignment pattern
    print("\n3. LEAD ASSIGNMENT PATTERN (Last 20 Boat Maintenance Leads):")
    print("-" * 40)
    
    query = """
    SELECT 
        assigned_vendor_id,
        COUNT(*) as lead_count,
        MAX(created_at) as last_assignment
    FROM leads
    WHERE primary_service_category = 'Boat Maintenance'
    AND assigned_vendor_id IS NOT NULL
    AND created_at > datetime('now', '-30 days')
    GROUP BY assigned_vendor_id
    ORDER BY lead_count DESC
    """
    
    cursor.execute(query)
    assignments = cursor.fetchall()
    
    if assignments:
        print(f"{'Vendor':<30} {'Count':<10} {'Last Assignment'}")
        print("-" * 70)
        for assignment in assignments:
            print(f"{assignment[0]:<30} {assignment[1]:<10} {assignment[2]}")
    else:
        print("No lead assignments found")
    
    # 4. Check round-robin tracking
    print("\n4. VENDOR ROUND-ROBIN STATUS:")
    print("-" * 40)
    
    query = """
    SELECT 
        company_name,
        total_leads_assigned,
        last_lead_assigned,
        CASE 
            WHEN last_lead_assigned IS NULL THEN 999999
            ELSE julianday('now') - julianday(last_lead_assigned)
        END as days_since_last_lead
    FROM vendors
    WHERE (
        LOWER(services_offered) LIKE '%barnacle%'
        OR LOWER(services_offered) LIKE '%boat maintenance%'
    )
    AND is_active = 1
    ORDER BY total_leads_assigned ASC, days_since_last_lead DESC
    """
    
    cursor.execute(query)
    rr_status = cursor.fetchall()
    
    if rr_status:
        print(f"{'Company':<30} {'Total Leads':<12} {'Last Lead':<20} {'Days Ago'}")
        print("-" * 80)
        for vendor in rr_status:
            days = "Never" if vendor[3] == 999999 else f"{vendor[3]:.1f}"
            last_lead = vendor[2] if vendor[2] else "Never"
            print(f"{vendor[0]:<30} {vendor[1]:<12} {last_lead:<20} {days}")
    
    # 5. Check for any routing rules
    print("\n5. ROUTING RULES FOR BOAT MAINTENANCE:")
    print("-" * 40)
    
    query = """
    SELECT 
        id,
        rule_name,
        service_category,
        conditions,
        priority_boost,
        is_active
    FROM routing_rules
    WHERE service_category = 'Boat Maintenance'
    OR service_category IS NULL
    """
    
    cursor.execute(query)
    rules = cursor.fetchall()
    
    if rules:
        for rule in rules:
            print(f"Rule: {rule[1]}")
            print(f"  Category: {rule[2]}")
            print(f"  Conditions: {rule[3]}")
            print(f"  Priority Boost: {rule[4]}")
            print(f"  Active: {rule[5]}")
    else:
        print("No routing rules found for Boat Maintenance")
    
    conn.close()

def check_vendor_matching_logic():
    """Check how vendors are being matched for barnacle cleaning"""
    conn = sqlite3.connect('smart_lead_router.db')
    cursor = conn.cursor()
    
    print("\n" + "=" * 80)
    print("VENDOR MATCHING ANALYSIS")
    print("=" * 80)
    
    # Get all vendors and parse their services
    query = """
    SELECT 
        id,
        company_name,
        services_offered
    FROM vendors
    WHERE is_active = 1
    """
    
    cursor.execute(query)
    vendors = cursor.fetchall()
    
    barnacle_vendors = []
    boat_maintenance_vendors = []
    
    for vendor in vendors:
        services = vendor[2].lower() if vendor[2] else ""
        if 'barnacle' in services:
            barnacle_vendors.append((vendor[0], vendor[1]))
        if 'boat maintenance' in services or 'boat and yacht maintenance' in services:
            boat_maintenance_vendors.append((vendor[0], vendor[1]))
    
    print(f"\nVendors with 'barnacle' in services: {len(barnacle_vendors)}")
    for v in barnacle_vendors:
        print(f"  - {v[1]} (ID: {v[0]})")
    
    print(f"\nVendors with 'boat maintenance' in services: {len(boat_maintenance_vendors)}")
    for v in boat_maintenance_vendors:
        print(f"  - {v[1]} (ID: {v[0]})")
    
    conn.close()

def check_last_two_leads():
    """Specifically check the last two barnacle cleaning leads"""
    conn = sqlite3.connect('smart_lead_router.db')
    cursor = conn.cursor()
    
    print("\n" + "=" * 80)
    print("LAST TWO BARNACLE CLEANING LEADS - DETAILED ANALYSIS")
    print("=" * 80)
    
    query = """
    SELECT 
        id,
        customer_name,
        customer_email,
        customer_phone,
        primary_service_category,
        specific_service_requested,
        assigned_vendor_id,
        created_at,
        updated_at,
        lead_quality_score,
        routing_priority,
        status,
        raw_data
    FROM leads
    WHERE (
        LOWER(primary_service_category) LIKE '%barnacle%' 
        OR LOWER(specific_service_requested) LIKE '%barnacle%'
        OR (LOWER(primary_service_category) = 'boat maintenance' AND LOWER(specific_service_requested) LIKE '%barnacle%')
    )
    ORDER BY created_at DESC
    LIMIT 2
    """
    
    cursor.execute(query)
    leads = cursor.fetchall()
    
    if len(leads) >= 2:
        print(f"\nFound {len(leads)} recent barnacle cleaning leads:")
        
        for i, lead in enumerate(leads, 1):
            print(f"\n{'='*40}")
            print(f"LEAD #{i} (Most Recent First)")
            print(f"{'='*40}")
            print(f"ID: {lead[0]}")
            print(f"Contact: {lead[1]}")
            print(f"Email: {lead[2]}")
            print(f"Phone: {lead[3]}")
            print(f"Service Requested: {lead[4]}")
            print(f"Specific Service: {lead[5]}")
            print(f"VENDOR ASSIGNED: {lead[6]}")
            print(f"Created: {lead[7]}")
            print(f"Updated: {lead[8]}")
            print(f"Score/Priority: {lead[9]}/{lead[10]}")
            print(f"Status: {lead[11]}")
            
            # Parse webhook data if available
            if lead[12]:
                try:
                    webhook_data = json.loads(lead[12])
                    if 'form_fields' in webhook_data:
                        print("\nForm Fields:")
                        for key, value in webhook_data['form_fields'].items():
                            if 'service' in key.lower() or 'barnacle' in str(value).lower():
                                print(f"  {key}: {value}")
                except:
                    pass
        
        # Check if same vendor was assigned
        if len(leads) == 2 and leads[0][6] == leads[1][6]:
            print(f"\n{'!'*60}")
            print(f"WARNING: BOTH LEADS ASSIGNED TO SAME VENDOR: {leads[0][6]}")
            print(f"{'!'*60}")
            
            # Get vendor details
            query = """
            SELECT 
                company_name,
                total_leads_assigned,
                last_lead_assigned
            FROM vendors
            WHERE company_name = ?
            """
            cursor.execute(query, (leads[0][6],))
            vendor = cursor.fetchone()
            if vendor:
                print(f"Vendor Details:")
                print(f"  Company: {vendor[0]}")
                print(f"  Total Leads Assigned: {vendor[1]}")
                print(f"  Last Lead Assigned: {vendor[2]}")
    else:
        print(f"Only found {len(leads)} barnacle cleaning lead(s)")
    
    conn.close()

if __name__ == "__main__":
    check_recent_barnacle_leads()
    check_vendor_matching_logic()
    check_last_two_leads()
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)