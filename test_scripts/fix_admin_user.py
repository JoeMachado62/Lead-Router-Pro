#!/usr/bin/env python3
"""
Fix Admin User - Create admin user for dockside.life tenant
"""

import os
import sys
from sqlalchemy.orm import Session
from database.simple_connection import get_db_session
from database.models import User, Tenant
from api.services.auth_service import auth_service

def main():
    """Create admin user for the correct tenant"""
    # User details
    email = "info@docksidepros.com"
    password = "Docksidepros@2025!"
    first_name = "Admin"
    last_name = "User"
    role = "admin"
    
    db = get_db_session()
    
    try:
        # Get the dockside.life tenant
        tenant = db.query(Tenant).filter(Tenant.domain == "dockside.life").first()
        
        if not tenant:
            print("❌ Error: No tenant found for domain 'dockside.life'")
            sys.exit(1)
            
        print(f"Found tenant: {tenant.name} ({tenant.domain})")
        
        # Check if user already exists for this tenant
        existing_user = auth_service.get_user_by_email(email, tenant.id, db)
        if existing_user:
            print(f"User {email} already exists for {tenant.domain}. Updating...")
            existing_user.password_hash = auth_service.hash_password(password)
            existing_user.role = role
            existing_user.is_active = True
            existing_user.is_verified = True
            existing_user.first_name = first_name
            existing_user.last_name = last_name
            db.commit()
            print(f"✅ Updated user: {email} for tenant {tenant.domain}")
        else:
            # Create new user for dockside.life tenant
            user = auth_service.create_user(
                email=email,
                password=password,
                tenant_id=tenant.id,
                first_name=first_name,
                last_name=last_name,
                role=role,
                db=db
            )
            
            # Auto-verify admin user
            user.is_verified = True
            db.commit()
            
            print(f"✅ Created new admin user: {email}")
            print(f"   Tenant: {tenant.name} ({tenant.domain})")
            print(f"   Role: {user.role}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()
    
    print("\n✅ Admin user is now available for dockside.life!")
    print("You can login at https://dockside.life/ with:")
    print(f"Email: {email}")
    print(f"Password: {password}")

if __name__ == "__main__":
    main()