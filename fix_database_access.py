#!/usr/bin/env python3
"""
Fix database access issues for VS Code
Reverts any changes that might prevent opening in VS Code
"""

import sqlite3
import os
import shutil
from datetime import datetime

def fix_database_access():
    """Reset database to state that VS Code can open"""
    
    db_path = "/root/Lead-Router-Pro/smart_lead_router.db"
    
    print("🔧 Fixing database access for VS Code...")
    print("=" * 60)
    
    try:
        # 1. Create a backup first
        backup_name = f"smart_lead_router_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(db_path, backup_name)
        print(f"✅ Created backup: {backup_name}")
        
        # 2. Connect and reset journal mode to default
        conn = sqlite3.connect(db_path, isolation_level=None)
        cursor = conn.cursor()
        
        # Check current settings
        cursor.execute("PRAGMA journal_mode;")
        current_journal = cursor.fetchone()[0]
        print(f"   Current journal mode: {current_journal}")
        
        # Reset to DELETE mode (SQLite default that VS Code expects)
        cursor.execute("PRAGMA journal_mode=DELETE;")
        new_mode = cursor.fetchone()[0]
        print(f"   Reset journal mode to: {new_mode}")
        
        # Ensure database is not in exclusive lock mode
        cursor.execute("PRAGMA locking_mode=NORMAL;")
        print("   Set locking mode to: NORMAL")
        
        # Run checkpoint if in WAL mode
        if current_journal == 'wal':
            cursor.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            print("   Performed WAL checkpoint")
        
        # Vacuum to clean up
        print("   Running VACUUM to optimize database...")
        cursor.execute("VACUUM;")
        print("   ✅ Database optimized")
        
        conn.close()
        print("\n✅ Database reset to VS Code compatible state")
        
        # 3. Remove any WAL or SHM files
        wal_file = db_path + "-wal"
        shm_file = db_path + "-shm"
        
        if os.path.exists(wal_file):
            os.remove(wal_file)
            print(f"   Removed WAL file: {wal_file}")
        
        if os.path.exists(shm_file):
            os.remove(shm_file)
            print(f"   Removed SHM file: {shm_file}")
        
        # 4. Set proper permissions
        os.chmod(db_path, 0o644)
        print("   Set permissions to 644")
        
        # 5. Test that it's readable
        test_conn = sqlite3.connect(db_path)
        test_conn.execute("SELECT COUNT(*) FROM leads").fetchone()
        test_conn.close()
        print("   ✅ Database is readable")
        
        print("\n" + "=" * 60)
        print("✅ DATABASE FIXED!")
        print("=" * 60)
        print("\n📌 Next steps:")
        print("1. Close any open database tabs in VS Code")
        print("2. Restart VS Code completely")
        print("3. Try opening 'smart_lead_router.db' again")
        print("4. If still not working, try the backup file created")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error fixing database: {e}")
        return False

def check_what_changed():
    """Check what might have changed since yesterday"""
    print("\n🔍 Checking what changed...")
    print("-" * 60)
    
    # Check if FastAPI is running
    import subprocess
    try:
        result = subprocess.run(['pgrep', '-f', 'main_working_final'], capture_output=True, text=True)
        if result.stdout:
            print("⚠️  FastAPI is currently running - this might lock the database")
            print("   Consider stopping it temporarily to open in VS Code")
        else:
            print("✅ FastAPI is not running")
    except:
        pass
    
    # Check for any lock files
    db_dir = "/root/Lead-Router-Pro"
    for file in os.listdir(db_dir):
        if file.startswith("smart_lead_router.db") and file != "smart_lead_router.db":
            print(f"   Found related file: {file}")
    
    print("\nChanges made today that might affect database:")
    print("1. Changed journal mode to WAL (now reverted)")
    print("2. Created database connections in new reassignment code")
    print("3. FastAPI app is holding connections")

if __name__ == "__main__":
    print("DATABASE ACCESS FIX FOR VS CODE")
    print("=" * 60)
    
    fix_database_access()
    check_what_changed()
    
    print("\n💡 TIP: If VS Code still can't open it:")
    print("   1. Stop FastAPI: pkill -f 'python.*main_working_final'")
    print("   2. Try opening the database")
    print("   3. Restart FastAPI when done")