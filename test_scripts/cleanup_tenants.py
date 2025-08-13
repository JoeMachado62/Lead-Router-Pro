#!/usr/bin/env python3
"""
Clean up unnecessary tenant and verify admin user setup
"""

import os
import sys
from sqlalchemy.orm import Session
from database.simple_connection import get_db_session
from database.models import User, Tenant
from api.services.auth_service import auth_service

def main():
    """Clean up tenants and verify admin user"""
    db = get_db_session()
    
    try:
        print("=== Tenant Cleanup and Admin User Verification ===\n")
        
        # 1. Show current state
        print("1. Current tenants:")
        tenants = db.query(Tenant).all()
        for tenant in tenants:
            user_count = db.query(User).filter(User.tenant_id == tenant.id).count()
            print(f"   - {tenant.name} ({tenant.domain}) - {user_count} users")
        
        # 2. Check for docksidepros.com tenant
        docksidepros_tenant = db.query(Tenant).filter(Tenant.domain == "docksidepros.com").first()
        if docksidepros_tenant:
            print(f"\n2. Found unnecessary tenant: {docksidepros_tenant.name}")
            
            # Check for users under this tenant
            users = db.query(User).filter(User.tenant_id == docksidepros_tenant.id).all()
            if users:
                print(f"   Users under this tenant: {len(users)}")
                for user in users:
                    print(f"   - {user.email}")
                    
                # Delete users first
                db.query(User).filter(User.tenant_id == docksidepros_tenant.id).delete()
                print("   ✅ Deleted users from unnecessary tenant")
            
            # Delete the tenant
            db.delete(docksidepros_tenant)
            db.commit()
            print("   ✅ Removed unnecessary docksidepros.com tenant")
        
        # 3. Verify admin user under dockside.life
        print("\n3. Verifying admin user under dockside.life:")
        dockside_tenant = db.query(Tenant).filter(Tenant.domain == "dockside.life").first()
        
        if not dockside_tenant:
            print("   ❌ Error: No dockside.life tenant found!")
            sys.exit(1)
            
        admin_user = auth_service.get_user_by_email("info@docksidepros.com", dockside_tenant.id, db)
        if admin_user:
            print(f"   ✅ Admin user exists: {admin_user.email}")
            print(f"      Role: {admin_user.role}")
            print(f"      Active: {admin_user.is_active}")
            print(f"      Verified: {admin_user.is_verified}")
        else:
            print("   ❌ Admin user not found under dockside.life tenant")
            
        # 4. Final state
        print("\n4. Final state:")
        remaining_tenants = db.query(Tenant).all()
        for tenant in remaining_tenants:
            user_count = db.query(User).filter(User.tenant_id == tenant.id).count()
            print(f"   - {tenant.name} ({tenant.domain}) - {user_count} users")
            
            # List users for this tenant
            users = db.query(User).filter(User.tenant_id == tenant.id).all()
            for user in users:
                print(f"     • {user.email} ({user.role})")
        
        print("\n✅ Cleanup complete!")
        print("\nYou can login at https://dockside.life/ with:")
        print("Email: info@docksidepros.com")
        print("Password: Docksidepros@2025!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        db.rollback()
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()