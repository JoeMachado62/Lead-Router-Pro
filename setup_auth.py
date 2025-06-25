"""
Setup script for authentication system
Creates default tenant, admin user, and initializes database
"""

import os
import asyncio
from database.models import Base, Tenant, User
from database.simple_connection import auth_engine, get_db_session
from api.services.auth_service import auth_service
from api.services.email_service import email_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def setup_database():
    """Initialize database and create default tenant and admin user"""
    logger.info("Setting up authentication database...")
    
    # Create all tables
    Base.metadata.create_all(bind=auth_engine)
    logger.info("Database tables created")
    
    db = get_db_session()
    
    try:
        # Create default tenant
        existing_tenant = db.query(Tenant).filter(Tenant.domain == "dockside.life").first()
        if not existing_tenant:
            tenant = Tenant(
                name="Dockside Pro",
                domain="dockside.life",
                subdomain="dockside",
                settings={
                    "theme": "blue",
                    "features": {
                        "2fa_required": True,
                        "password_complexity": True,
                        "session_timeout": 60
                    }
                },
                subscription_tier="enterprise",
                max_users=50
            )
            db.add(tenant)
            db.commit()
            db.refresh(tenant)
            logger.info(f"Created default tenant: {tenant.name}")
        else:
            tenant = existing_tenant
            logger.info(f"Using existing tenant: {tenant.name}")
        
        # Create admin user
        admin_email = "joe@ezwai.com"
        existing_admin = auth_service.get_user_by_email(admin_email, str(tenant.id), db)
        
        if not existing_admin:
            # Default admin password (should be changed on first login)
            admin_password = "DocksideAdmin2025!"
            
            admin_user = auth_service.create_user(
                email=admin_email,
                password=admin_password,
                tenant_id=str(tenant.id),
                first_name="System",
                last_name="Administrator",
                role="admin",
                db=db
            )
            
            # Mark admin as verified and disable 2FA for testing
            admin_user.is_verified = True
            admin_user.two_factor_enabled = False
            db.commit()
            
            logger.info(f"Created admin user: {admin_email}")
            logger.info(f"Admin password: {admin_password}")
            logger.info("*** PLEASE CHANGE THE ADMIN PASSWORD AFTER FIRST LOGIN ***")
            
            # Try to send welcome email if SMTP is configured
            if os.getenv("SMTP_USERNAME") and os.getenv("SMTP_PASSWORD"):
                try:
                    await email_service.send_welcome_email(
                        to_email=admin_email,
                        user_name="Administrator",
                        verification_code="VERIFIED"
                    )
                    logger.info("Welcome email sent to admin")
                except Exception as e:
                    logger.warning(f"Could not send welcome email: {e}")
        else:
            logger.info(f"Admin user already exists: {admin_email}")
        
        # Create additional sample users if needed
        sample_users = [
            {
                "email": "user@dockside.life",
                "password": "DocksideUser2025!",
                "first_name": "Sample",
                "last_name": "User",
                "role": "user"
            }
        ]
        
        for user_data in sample_users:
            existing_user = auth_service.get_user_by_email(user_data["email"], str(tenant.id), db)
            if not existing_user:
                user = auth_service.create_user(
                    email=user_data["email"],
                    password=user_data["password"],
                    tenant_id=str(tenant.id),
                    first_name=user_data["first_name"],
                    last_name=user_data["last_name"],
                    role=user_data["role"],
                    db=db
                )
                # Mark as verified and disable 2FA for testing
                user.is_verified = True
                user.two_factor_enabled = False
                db.commit()
                logger.info(f"Created sample user: {user_data['email']}")
        
        logger.info("Authentication setup completed successfully!")
        
        # Print summary
        print("\n" + "="*50)
        print("AUTHENTICATION SETUP COMPLETE")
        print("="*50)
        print(f"Default Tenant: {tenant.name} ({tenant.domain})")
        print(f"Admin Email: joe@ezwai.com")
        print(f"Admin Password: DocksideAdmin2025!")
        print(f"Sample User: user@dockside.life")
        print(f"Sample Password: DocksideUser2025!")
        print(f"\n🔐 2FA Status: DISABLED for testing")
        print("\nAccess your application at:")
        print(f"- Login: https://{tenant.domain}/login")
        print(f"- Admin: https://{tenant.domain}/admin")
        print(f"- API Docs: https://{tenant.domain}/docs")
        print("\n*** REMEMBER TO CHANGE DEFAULT PASSWORDS ***")
        print("*** 2FA is disabled for testing - enable when email is configured ***")
        print("="*50)
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

async def update_email_config():
    """Update email configuration if needed"""
    current_smtp = os.getenv("SMTP_USERNAME")
    if not current_smtp or current_smtp == "your-email@gmail.com":
        print("\n" + "="*50)
        print("EMAIL CONFIGURATION NEEDED")
        print("="*50)
        print("To enable 2FA and email notifications, update your .env file:")
        print("")
        print("SMTP_HOST=smtp.gmail.com")
        print("SMTP_PORT=587")
        print("SMTP_USERNAME=your-actual-email@gmail.com")
        print("SMTP_PASSWORD=your-app-password")
        print("SMTP_FROM_EMAIL=noreply@dockside.life")
        print("")
        print("For Gmail, use an App Password:")
        print("1. Enable 2FA on your Google account")
        print("2. Generate an App Password")
        print("3. Use the App Password as SMTP_PASSWORD")
        print("="*50)

def verify_requirements():
    """Verify all required dependencies are installed"""
    try:
        import sqlalchemy
        import fastapi
        import pydantic
        import passlib
        import jose
        logger.info("All required dependencies found")
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        print("\nInstall missing dependencies:")
        print("pip install -r requirements.txt")
        exit(1)

async def main():
    """Main setup function"""
    logger.info("Starting Dockside Pro Authentication Setup...")
    
    # Verify requirements
    verify_requirements()
    
    # Setup database and users
    await setup_database()
    
    # Check email configuration
    await update_email_config()
    
    print("\nSetup complete! You can now start the application:")
    print("python main_working_final.py")

if __name__ == "__main__":
    asyncio.run(main())
