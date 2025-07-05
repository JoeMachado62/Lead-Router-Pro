#!/usr/bin/env python3
"""Rollback vendor migration using backup file"""

import sys
import os
import json
import glob
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.simple_connection import db

def rollback_migration():
    """Rollback vendor migration using the most recent backup file"""
    print("🔄 Vendor Migration Rollback Tool")
    print("=" * 40)
    
    # Find most recent backup
    backup_files = glob.glob('vendor_backup_*.json')
    if not backup_files:
        print("❌ No backup files found")
        return
    
    # Sort by filename (timestamp) to get most recent
    latest_backup = max(backup_files)
    print(f"📦 Found backup file: {latest_backup}")
    
    # Confirm rollback
    response = input("This will restore vendor data from backup. Continue? (yes/no): ").lower().strip()
    if response not in ['yes', 'y']:
        print("❌ Rollback cancelled by user")
        return
    
    try:
        # Load backup data
        with open(latest_backup, 'r') as f:
            backup_vendors = json.load(f)
        
        print(f"📋 Loaded backup with {len(backup_vendors)} vendors")
        
        # Restore each vendor
        conn = db._get_conn()
        cursor = conn.cursor()
        
        restored_count = 0
        for vendor in backup_vendors:
            cursor.execute('''
                UPDATE vendors 
                SET service_coverage_type = ?,
                    service_areas = ?,
                    service_counties = ?
                WHERE id = ?
            ''', (vendor['service_coverage_type'], vendor['service_areas'], 
                  vendor['service_counties'], vendor['id']))
            
            if cursor.rowcount > 0:
                restored_count += 1
        
        conn.commit()
        conn.close()
        
        print(f"✅ Successfully restored {restored_count} vendors from backup")
        
        # Create rollback log
        rollback_log = f'rollback_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        with open(rollback_log, 'w') as f:
            f.write(f"Rollback performed at: {datetime.now()}\n")
            f.write(f"Backup file used: {latest_backup}\n")
            f.write(f"Vendors restored: {restored_count}\n")
        
        print(f"📝 Rollback log created: {rollback_log}")
        
    except Exception as e:
        print(f"❌ Error during rollback: {e}")

if __name__ == "__main__":
    rollback_migration()
