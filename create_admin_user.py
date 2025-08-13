#!/usr/bin/env python3
"""
Create Admin User Script
Creates an admin user for Dockside Pros
"""

import os
import sys
from sqlalchemy.orm import Session
from database.simple_connection import get_db_session, auth_engine
from database.models import User, Tenant, Base
from api.services.auth_service import auth_service

def create_tenant_if_not_exists(db: Session):
    """Create Dockside Pros tenant if it doesn't exist"""
    # Try to find by domain first
    tenant = db.query(Tenant).filter(Tenant.domain == "docksidepros.com").first()
    
    if not tenant:
        # Check if subdomain is already taken
        existing_subdomain = db.query(Tenant).filter(Tenant.subdomain == "dockside").first()
        if existing_subdomain:
            # Use a unique subdomain
            subdomain = "docksidepros"
        else:
            subdomain = "dockside"
            
        tenant = Tenant(
            name="Dockside Pros",
            domain="docksidepros.com",
            subdomain=subdomain,
            is_active=True,
            subscription_tier=os.getenv("DEFAULT_SUBSCRIPTION_TIER", "pro"),
            max_users=100,
            settings={
                "timezone": "America/New_York",
                "notification_email": "info@docksidepros.com",
                "enable_smart_routing": True
            }
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        print(f"Created new tenant: {tenant.name} (subdomain: {subdomain})")
    else:
        print(f"Found existing tenant: {tenant.name}")
    
    return tenant

def main():
    """Main function to create admin user"""
    # User details
    email = "info@docksidepros.com"
    password = "Docksidepros@2025!"
    first_name = "Admin"
    last_name = "User"
    role = "admin"
    
    # Create database tables if they don't exist
    print("Ensuring database tables exist...")
    Base.metadata.create_all(bind=auth_engine)
    
    # Get database session
    db = get_db_session()
    
    try:
        # Create or get tenant
        tenant = create_tenant_if_not_exists(db)
        
        # Check if user already exists
        existing_user = auth_service.get_user_by_email(email, tenant.id, db)
        if existing_user:
            print(f"User {email} already exists. Updating password and role...")
            existing_user.password_hash = auth_service.hash_password(password)
            existing_user.role = role
            existing_user.is_active = True
            existing_user.is_verified = True  # Auto-verify admin user
            existing_user.first_name = first_name
            existing_user.last_name = last_name
            db.commit()
            print(f"Updated user: {email} with admin role")
        else:
            # Create new user
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
            
            print(f"Created new admin user: {email}")
            print(f"Tenant: {tenant.name} ({tenant.domain})")
            print(f"Role: {user.role}")
            print(f"2FA Enabled: {user.two_factor_enabled}")
            
    except Exception as e:
        print(f"Error creating user: {str(e)}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()
    
    print("\nAdmin user created successfully!")
    print("You can now login with:")
    print(f"Email: {email}")
    print(f"Password: {password}")
    print("\nNote: 2FA is enabled by default. You'll receive a code via email on first login.")

if __name__ == "__main__":
    main()