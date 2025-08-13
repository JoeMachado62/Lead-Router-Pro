#!/usr/bin/env python3
"""
Get Raw Webhook Payloads from WordPress Elementor Forms
"""

import sqlite3
import json
import sys
from datetime import datetime

def get_raw_webhook_payloads(limit=3):
    """Get the actual raw webhook payloads from the database"""
    
    # Connect to database
    conn = sqlite3.connect('smart_lead_router.db')
    cursor = conn.cursor()
    
    # Get leads with service_details (raw payload data)
    query = """
        SELECT 
            id,
            customer_name,
            customer_email,
            created_at,
            service_details,
            primary_service_category
        FROM leads 
        WHERE service_details IS NOT NULL 
        ORDER BY created_at DESC 
        LIMIT ?
    """
    
    cursor.execute(query, (limit,))
    results = cursor.fetchall()
    
    print("🔍 RAW WEBHOOK PAYLOADS FROM WORDPRESS ELEMENTOR")
    print("=" * 80)
    print(f"📋 Showing the last {limit} webhook payloads received")
    print("=" * 80)
    
    for i, (lead_id, customer_name, customer_email, created_at, service_details, service_category) in enumerate(results, 1):
        print(f"\n📅 WEBHOOK #{i} - {created_at}")
        print(f"👤 Customer: {customer_name} ({customer_email})")
        print(f"🛠️  Service Category: {service_category}")
        print(f"📋 Lead ID: {lead_id}")
        print("\n" + "=" * 80)
        print("🔍 RAW WEBHOOK PAYLOAD (exactly as received from WordPress Elementor):")
        print("=" * 80)
        
        try:
            # Parse and pretty-print the JSON payload
            payload = json.loads(service_details)
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        except json.JSONDecodeError:
            print("❌ Invalid JSON in service_details")
            print(service_details)
        
        print("\n" + "=" * 80)
    
    conn.close()

if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    get_raw_webhook_payloads(limit)