#!/usr/bin/env python3
"""
Verify admin user status
"""

import os
from sqlalchemy.orm import Session
from database.simple_connection import get_db_session
from database.models import User, Tenant
from api.services.auth_service import auth_service

def main():
    """Check current admin user status"""
    db = get_db_session()
    
    try:
        print("=== Current Admin User Status ===\n")
        
        # Get dockside.life tenant
        dockside_tenant = db.query(Tenant).filter(Tenant.domain == "dockside.life").first()
        
        if not dockside_tenant:
            print("❌ No tenant found for dockside.life!")
            return
            
        print(f"✅ Found tenant: {dockside_tenant.name} ({dockside_tenant.domain})")
        print(f"   Tenant ID: {dockside_tenant.id}")
        
        # Check for admin user
        admin_email = "info@docksidepros.com"
        admin_user = db.query(User).filter(
            User.email == admin_email,
            User.tenant_id == dockside_tenant.id
        ).first()
        
        if admin_user:
            print(f"\n✅ Admin user found: {admin_user.email}")
            print(f"   User ID: {admin_user.id}")
            print(f"   Role: {admin_user.role}")
            print(f"   Active: {admin_user.is_active}")
            print(f"   Verified: {admin_user.is_verified}")
            
            # Test authentication
            print("\n🔐 Testing authentication:")
            password = "Docksidepros@2025!"
            auth_result, message = auth_service.authenticate_user(
                admin_email,
                password,
                dockside_tenant.id,
                db
            )
            
            if auth_result:
                print("   ✅ Authentication successful!")
            else:
                print(f"   ❌ Authentication failed: {message}")
                
        else:
            print(f"\n❌ No admin user found for {admin_email} under dockside.life tenant")
            
        # Show all users for dockside.life
        print(f"\n📋 All users for {dockside_tenant.domain}:")
        all_users = db.query(User).filter(User.tenant_id == dockside_tenant.id).all()
        for user in all_users:
            print(f"   - {user.email} ({user.role}) - Active: {user.is_active}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()