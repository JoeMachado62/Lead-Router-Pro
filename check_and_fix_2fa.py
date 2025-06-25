#!/usr/bin/env python3
"""
Check and Fix 2FA Settings
"""

import sqlite3
import sys
import os

def check_and_fix_2fa():
    """Check and fix 2FA settings for all users"""
    
    db_path = 'smart_lead_router.db'
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all users
        cursor.execute('''
            SELECT u.id, u.email, u.two_factor_enabled, u.is_verified, u.role, t.domain 
            FROM users u 
            JOIN tenants t ON u.tenant_id = t.id
        ''')
        
        users = cursor.fetchall()
        
        print("Current User Settings:")
        print("=" * 60)
        
        for user in users:
            user_id, email, two_factor_enabled, is_verified, role, domain = user
            print(f"Email: {email}")
            print(f"Domain: {domain}")
            print(f"2FA Enabled: {two_factor_enabled}")
            print(f"Is Verified: {is_verified}")
            print(f"Role: {role}")
            print("-" * 40)
        
        # Enable 2FA for all users
        print("\n🔧 Enabling 2FA for all users...")
        cursor.execute('UPDATE users SET two_factor_enabled = 1')
        
        # Verify all users (so they can log in)
        cursor.execute('UPDATE users SET is_verified = 1')
        
        conn.commit()
        
        print("✅ Updated all users:")
        print("   - 2FA enabled: TRUE")
        print("   - Email verified: TRUE")
        
        # Show updated settings
        cursor.execute('''
            SELECT u.email, u.two_factor_enabled, u.is_verified, u.role, t.domain 
            FROM users u 
            JOIN tenants t ON u.tenant_id = t.id
        ''')
        
        updated_users = cursor.fetchall()
        
        print("\nUpdated User Settings:")
        print("=" * 60)
        
        for user in updated_users:
            email, two_factor_enabled, is_verified, role, domain = user
            print(f"Email: {email}")
            print(f"Domain: {domain}")
            print(f"2FA Enabled: {two_factor_enabled}")
            print(f"Is Verified: {is_verified}")
            print(f"Role: {role}")
            print("-" * 40)
        
        conn.close()
        
        print("\n🎯 Now try logging in again - 2FA should be required!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    check_and_fix_2fa()
