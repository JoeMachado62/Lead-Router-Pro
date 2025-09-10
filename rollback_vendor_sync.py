#!/usr/bin/env python3
"""
Rollback script to restore vendor data before sync
This creates a backup first, then allows selective restoration
"""

import sqlite3
import json
from datetime import datetime
import os

DB_PATH = "smart_lead_router.db"
BACKUP_PATH = f"vendor_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

def create_backup():
    """Create a full database backup"""
    print(f"📦 Creating backup at {BACKUP_PATH}")
    
    # Create backup using SQLite backup API
    source = sqlite3.connect(DB_PATH)
    backup = sqlite3.connect(BACKUP_PATH)
    
    with backup:
        source.backup(backup)
    
    source.close()
    backup.close()
    
    print(f"✅ Backup created successfully")
    return BACKUP_PATH

def show_recent_vendor_changes():
    """Show vendors that were recently updated"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get vendors updated in the last 24 hours
    cursor.execute("""
        SELECT id, name, company_name, status, ghl_user_id, 
               coverage_type, service_categories, updated_at
        FROM vendors
        WHERE datetime(updated_at) > datetime('now', '-24 hours')
        ORDER BY updated_at DESC
    """)
    
    recent_vendors = cursor.fetchall()
    
    if recent_vendors:
        print(f"\n📊 Found {len(recent_vendors)} vendors updated in the last 24 hours:")
        print("-" * 80)
        
        for vendor in recent_vendors:
            print(f"\nVendor: {vendor[1]} ({vendor[2]})")
            print(f"  ID: {vendor[0]}")
            print(f"  Status: {vendor[3]}")
            print(f"  GHL User ID: {vendor[4] or 'None'}")
            print(f"  Coverage Type: {vendor[5]}")
            print(f"  Service Categories: {vendor[6][:50]}..." if vendor[6] and len(vendor[6]) > 50 else f"  Service Categories: {vendor[6]}")
            print(f"  Updated: {vendor[7]}")
    else:
        print("\n✅ No vendors were updated in the last 24 hours")
    
    conn.close()
    return len(recent_vendors) > 0

def rollback_coverage_fields():
    """Reset coverage fields for vendors without GHL User IDs"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n🔄 Rolling back coverage fields for inactive vendors...")
    
    # Reset coverage fields for vendors without GHL User IDs
    cursor.execute("""
        UPDATE vendors
        SET coverage_type = 'county',
            coverage_states = '[]',
            coverage_counties = '[]',
            updated_at = CURRENT_TIMESTAMP
        WHERE ghl_user_id IS NULL OR ghl_user_id = ''
    """)
    
    affected = cursor.rowcount
    conn.commit()
    
    print(f"✅ Reset coverage fields for {affected} inactive vendors")
    
    # Show current active vendor count
    cursor.execute("SELECT COUNT(*) FROM vendors WHERE ghl_user_id IS NOT NULL AND ghl_user_id != ''")
    active_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM vendors")
    total_count = cursor.fetchone()[0]
    
    print(f"\n📊 Vendor Statistics:")
    print(f"  Total vendors: {total_count}")
    print(f"  Active vendors (with GHL User ID): {active_count}")
    print(f"  Inactive vendors: {total_count - active_count}")
    
    conn.close()

def main():
    """Main rollback function"""
    print("🚨 VENDOR SYNC ROLLBACK UTILITY")
    print("=" * 80)
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        return
    
    # Create backup first
    backup_file = create_backup()
    
    # Show recent changes
    has_changes = show_recent_vendor_changes()
    
    if has_changes:
        print("\n" + "=" * 80)
        print("⚠️  WARNING: This will modify vendor data")
        print("A backup has been created at:", backup_file)
        
        response = input("\n🔄 Do you want to rollback coverage fields for inactive vendors? (y/n): ")
        
        if response.lower() == 'y':
            rollback_coverage_fields()
            print("\n✅ Rollback completed successfully")
            print(f"💾 Backup preserved at: {backup_file}")
        else:
            print("\n❌ Rollback cancelled")
            print(f"💾 Backup still available at: {backup_file}")
    else:
        print("\n✅ No rollback needed - no recent vendor updates found")
        print(f"💾 Backup still created at: {backup_file}")

if __name__ == "__main__":
    main()