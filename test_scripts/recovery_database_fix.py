#!/usr/bin/env python3
"""
Recovery Database Fix - Run this if you applied code fixes before database schema fix
This will add the missing columns to make your updated code work properly
"""

import sqlite3
import os

def check_and_fix_activity_log():
    """Check current schema and add missing columns"""
    
    print("🔍 CHECKING ACTIVITY LOG TABLE SCHEMA")
    print("-" * 50)
    
    # Check if database exists
    if not os.path.exists('smart_lead_router.db'):
        print("❌ Database file not found: smart_lead_router.db")
        return False
    
    try:
        conn = sqlite3.connect('smart_lead_router.db')
        cursor = conn.cursor()
        
        # Get current table schema
        cursor.execute("PRAGMA table_info(activity_log)")
        columns_info = cursor.fetchall()
        columns = [row[1] for row in columns_info]
        
        print(f"📋 Current columns: {columns}")
        
        # Check which columns are missing
        required_columns = ['account_id', 'event_data', 'lead_id', 'vendor_id']
        missing_columns = [col for col in required_columns if col not in columns]
        
        if not missing_columns:
            print("✅ All required columns already exist!")
            conn.close()
            return True
        
        print(f"⚠️ Missing columns: {missing_columns}")
        print("🔧 Adding missing columns...")
        
        # Add each missing column
        for column in missing_columns:
            try:
                if column == 'account_id':
                    cursor.execute("ALTER TABLE activity_log ADD COLUMN account_id TEXT")
                    print(f"  ✅ Added {column}")
                elif column == 'event_data':
                    cursor.execute("ALTER TABLE activity_log ADD COLUMN event_data TEXT DEFAULT '{}'")
                    print(f"  ✅ Added {column}")
                elif column == 'lead_id':
                    cursor.execute("ALTER TABLE activity_log ADD COLUMN lead_id TEXT")
                    print(f"  ✅ Added {column}")
                elif column == 'vendor_id':
                    cursor.execute("ALTER TABLE activity_log ADD COLUMN vendor_id TEXT")
                    print(f"  ✅ Added {column}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"  ℹ️ {column} already exists")
                else:
                    print(f"  ❌ Error adding {column}: {e}")
        
        # Commit changes
        conn.commit()
        
        # Verify the fix
        cursor.execute("PRAGMA table_info(activity_log)")
        new_columns = [row[1] for row in cursor.fetchall()]
        
        print(f"\n📋 Updated columns: {new_columns}")
        
        # Check if all required columns now exist
        still_missing = [col for col in required_columns if col not in new_columns]
        
        if still_missing:
            print(f"❌ Still missing: {still_missing}")
            return False
        else:
            print("✅ All required columns now exist!")
            return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        if conn:
            conn.close()

def test_logging():
    """Test if activity logging now works"""
    print("\n🧪 TESTING ACTIVITY LOGGING")
    print("-" * 30)
    
    try:
        # Import your database connection
        import sys
        import os
        
        # Add project root to path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from database.simple_connection import db as simple_db_instance
        
        # Try to log a test activity
        activity_id = simple_db_instance.log_activity(
            event_type="test_recovery",
            event_data={"test": "recovery fix applied"},
            account_id="test_account",
            success=True
        )
        
        if activity_id:
            print("✅ Activity logging test successful!")
            print(f"   Created activity ID: {activity_id}")
            return True
        else:
            print("❌ Activity logging test failed")
            return False
            
    except Exception as e:
        print(f"❌ Activity logging test error: {e}")
        return False

if __name__ == "__main__":
    print("🚑 LEAD ROUTER PRO - RECOVERY DATABASE FIX")
    print("=" * 60)
    print("This will add missing columns to make your updated code work")
    print("")
    
    # Step 1: Fix the schema
    schema_fixed = check_and_fix_activity_log()
    
    if schema_fixed:
        # Step 2: Test the fix
        test_logging()
        
        print("\n🎉 RECOVERY COMPLETE!")
        print("✅ Your code fixes should now work properly")
        print("✅ Activity logging errors should be resolved")
    else:
        print("\n❌ RECOVERY FAILED")
        print("You may need to check the database manually")
    
    print("\n" + "=" * 60)