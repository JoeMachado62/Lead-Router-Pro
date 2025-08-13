#!/usr/bin/env python3
"""
Test authentication issue - root cause analysis
"""

import os
from sqlalchemy.orm import Session
from database.simple_connection import get_db_session
from database.models import User, Tenant
from api.services.auth_service import auth_service

def analyze_auth_issue():
    """Analyze authentication issue"""
    db = get_db_session()
    
    try:
        print("=== Authentication Issue Root Cause Analysis ===\n")
        
        # 1. Check all tenants
        print("1. Checking all tenants in database:")
        tenants = db.query(Tenant).all()
        for tenant in tenants:
            print(f"   - Tenant: {tenant.name}")
            print(f"     ID: {tenant.id}")
            print(f"     Domain: {tenant.domain}")
            print(f"     Subdomain: {tenant.subdomain}")
            print(f"     Active: {tenant.is_active}")
            print()
        
        # 2. Check users for docksidepros.com tenant
        print("2. Checking users for docksidepros.com:")
        tenant = db.query(Tenant).filter(Tenant.domain == "docksidepros.com").first()
        if tenant:
            users = db.query(User).filter(User.tenant_id == tenant.id).all()
            for user in users:
                print(f"   - User: {user.email}")
                print(f"     ID: {user.id}")
                print(f"     Role: {user.role}")
                print(f"     Active: {user.is_active}")
                print(f"     Verified: {user.is_verified}")
                print(f"     Password Hash: {user.password_hash[:20]}...")
                print()
        
        # 3. Test password verification
        print("3. Testing password verification:")
        email = "info@docksidepros.com"
        password = "Docksidepros@2025!"
        
        if tenant:
            user = auth_service.get_user_by_email(email, tenant.id, db)
            if user:
                print(f"   Found user: {user.email}")
                
                # Test password hash
                is_valid = auth_service.verify_password(password, user.password_hash)
                print(f"   Password verification result: {is_valid}")
                
                # Test full authentication
                auth_user, message = auth_service.authenticate_user(email, password, tenant.id, db)
                print(f"   Full authentication result: {message}")
                if auth_user:
                    print(f"   Authentication successful for: {auth_user.email}")
                
        # 4. Check for domain mismatch issues
        print("\n4. Domain matching analysis:")
        print("   When you login, the system extracts domain from:")
        print("   - The 'domain' parameter in login request (if provided)")
        print("   - The 'Host' header from the request (e.g., 'dockside.life')")
        print()
        print("   Current tenant domains in database:")
        for tenant in tenants:
            print(f"   - {tenant.domain}")
            
        # 5. Check if there's a dockside.life tenant
        print("\n5. Checking for dockside.life tenant:")
        dockside_tenant = db.query(Tenant).filter(Tenant.domain == "dockside.life").first()
        if dockside_tenant:
            print(f"   Found dockside.life tenant: {dockside_tenant.name}")
        else:
            print("   ❌ No tenant found for domain 'dockside.life'")
            print("   This is likely the issue - login is looking for dockside.life tenant")
            
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    analyze_auth_issue()