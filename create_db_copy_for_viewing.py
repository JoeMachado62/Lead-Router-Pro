#!/usr/bin/env python3
"""
Create a read-only copy of the database for viewing in VS Code
while the main application is running.
"""

import shutil
import sqlite3
import os
from datetime import datetime

def create_viewable_copy():
    """
    Creates a copy of the database that can be opened in VS Code
    even while the main application is using the original.
    """
    source_db = "/root/Lead-Router-Pro/smart_lead_router.db"
    copy_db = "/root/Lead-Router-Pro/smart_lead_router_VIEW.db"
    
    print("Creating viewable database copy...")
    
    try:
        # Method 1: Try direct file copy first
        if os.path.exists(copy_db):
            os.remove(copy_db)
            print(f"Removed old copy: {copy_db}")
        
        # Use SQLite backup API for safe copying
        source = sqlite3.connect(source_db)
        dest = sqlite3.connect(copy_db)
        
        with dest:
            source.backup(dest)
        
        source.close()
        dest.close()
        
        print(f"✅ Created viewable copy: {copy_db}")
        print(f"   Size: {os.path.getsize(copy_db):,} bytes")
        print("\n📌 You can now open 'smart_lead_router_VIEW.db' in VS Code!")
        print("   This is a snapshot copy that won't be locked by the running app.")
        
        # Quick verification
        conn = sqlite3.connect(copy_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM leads")
        lead_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM vendors")
        vendor_count = cursor.fetchone()[0]
        conn.close()
        
        print(f"\n📊 Database Statistics:")
        print(f"   Leads: {lead_count}")
        print(f"   Vendors: {vendor_count}")
        
        return copy_db
        
    except Exception as e:
        print(f"❌ Error creating copy: {e}")
        
        # Fallback: Try simpler copy
        print("\nTrying fallback method...")
        try:
            shutil.copy2(source_db, copy_db)
            print(f"✅ Created copy using fallback method: {copy_db}")
            return copy_db
        except Exception as e2:
            print(f"❌ Fallback also failed: {e2}")
            return None

def set_wal_mode():
    """
    Set the database to WAL mode which allows concurrent readers.
    This might help VS Code open the original database.
    """
    print("\n🔧 Attempting to set WAL mode for better concurrency...")
    
    try:
        conn = sqlite3.connect("/root/Lead-Router-Pro/smart_lead_router.db")
        cursor = conn.cursor()
        
        # Check current mode
        cursor.execute("PRAGMA journal_mode")
        current_mode = cursor.fetchone()[0]
        print(f"   Current journal mode: {current_mode}")
        
        if current_mode != 'wal':
            # Try to set WAL mode
            cursor.execute("PRAGMA journal_mode=WAL")
            new_mode = cursor.fetchone()[0]
            print(f"   Changed journal mode to: {new_mode}")
            
            if new_mode == 'wal':
                print("   ✅ WAL mode enabled - this should improve concurrent access")
        else:
            print("   ✅ Already in WAL mode")
        
        conn.close()
        
    except Exception as e:
        print(f"   ⚠️ Could not change journal mode: {e}")
        print("   The application may have an exclusive lock")

def main():
    print("=" * 60)
    print("DATABASE VIEWING FIX FOR VS CODE")
    print("=" * 60)
    
    print("\n🔍 Diagnosing the issue...")
    print("The database file is likely locked because:")
    print("1. Your FastAPI app is running and holding connections")
    print("2. SQLite's default 'delete' journal mode can cause locking")
    print("3. VS Code extensions may not handle concurrent access well")
    
    print("\n📋 Solutions:")
    
    # Solution 1: Create a copy
    copy_path = create_viewable_copy()
    
    # Solution 2: Try to enable WAL mode
    set_wal_mode()
    
    print("\n" + "=" * 60)
    print("RECOMMENDED ACTIONS:")
    print("=" * 60)
    
    if copy_path:
        print(f"\n1. Open '{os.path.basename(copy_path)}' in VS Code instead")
        print("   This is a read-only snapshot that won't have locking issues")
    
    print("\n2. If you need to view live data:")
    print("   - Stop the FastAPI app temporarily")
    print("   - Open the original database")
    print("   - Restart the app when done")
    
    print("\n3. For ongoing development, consider:")
    print("   - Using the VIEW copy for browsing")
    print("   - Re-run this script to refresh the snapshot")
    print("   - Or use the included query scripts instead of VS Code")
    
    print("\n4. Alternative: Use command-line SQLite:")
    print("   sqlite3 smart_lead_router.db '.tables'")
    print("   sqlite3 smart_lead_router.db 'SELECT * FROM leads LIMIT 5;'")

if __name__ == "__main__":
    main()