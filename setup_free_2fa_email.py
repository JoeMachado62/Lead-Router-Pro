#!/usr/bin/env python3
"""
Setup script for Free 2FA Email Service
Configures Gmail or other free email providers for 2FA
"""

import os
import asyncio
import getpass
from pathlib import Path
from api.services.free_email_2fa import free_2fa_service, setup_gmail_2fa

def create_env_file():
    """Create or update .env file with 2FA email settings"""
    env_path = Path(".env")
    
    print("🔧 Setting up Free 2FA Email Service")
    print("=" * 50)
    
    # Get email configuration
    print("\n📧 Email Configuration:")
    print("We'll use Gmail's free SMTP service for 2FA emails.")
    print("You'll need a Gmail account and an App Password.")
    
    email = input("\nEnter your Gmail address: ").strip()
    if not email.endswith("@gmail.com"):
        print("⚠️  Warning: This setup is optimized for Gmail. Other providers may need different settings.")
    
    print("\n🔐 App Password Setup:")
    print("1. Go to your Google Account settings")
    print("2. Security > 2-Step Verification > App passwords")
    print("3. Generate a password for 'Mail'")
    print("4. Copy the 16-character password")
    
    app_password = getpass.getpass("Enter your Gmail App Password (hidden): ").strip()
    
    # Read existing .env or create new
    env_content = ""
    if env_path.exists():
        with open(env_path, 'r') as f:
            env_content = f.read()
    
    # Update or add 2FA email settings
    new_settings = f"""
# Free 2FA Email Service Configuration
FREE_2FA_EMAIL={email}
FREE_2FA_PASSWORD={app_password}
EMAIL_TEST_MODE=false

# 2FA Settings
TWO_FACTOR_ENABLED=true
TWO_FACTOR_CODE_LENGTH=6
TWO_FACTOR_CODE_EXPIRE_MINUTES=10
"""
    
    # Remove existing 2FA settings if present
    lines = env_content.split('\n')
    filtered_lines = []
    skip_section = False
    
    for line in lines:
        if line.strip().startswith("# Free 2FA Email Service"):
            skip_section = True
            continue
        elif line.strip().startswith("#") and skip_section:
            if "2FA" not in line:
                skip_section = False
                filtered_lines.append(line)
        elif not skip_section:
            if not any(line.startswith(key) for key in ["FREE_2FA_EMAIL=", "FREE_2FA_PASSWORD=", "EMAIL_TEST_MODE=", "TWO_FACTOR_ENABLED=", "TWO_FACTOR_CODE_LENGTH=", "TWO_FACTOR_CODE_EXPIRE_MINUTES="]):
                filtered_lines.append(line)
    
    # Write updated .env file
    with open(env_path, 'w') as f:
        f.write('\n'.join(filtered_lines))
        f.write(new_settings)
    
    print(f"\n✅ Configuration saved to {env_path}")
    return email, app_password

async def test_email_setup(email: str, app_password: str):
    """Test the email configuration"""
    print("\n🧪 Testing Email Configuration...")
    
    # Configure the service
    setup_gmail_2fa(email, app_password)
    
    # Test connection
    if free_2fa_service.test_connection():
        print("✅ Email connection successful!")
        
        # Ask if user wants to send test email
        test_email = input(f"\nSend test 2FA email to {email}? (y/n): ").strip().lower()
        if test_email == 'y':
            success = await free_2fa_service.send_test_email(email)
            if success:
                print("✅ Test email sent! Check your inbox.")
            else:
                print("❌ Failed to send test email.")
        
        return True
    else:
        print("❌ Email connection failed. Please check your credentials.")
        return False

def update_auth_service():
    """Update the auth service to use the new 2FA email module"""
    print("\n🔄 Updating authentication service...")
    
    auth_service_path = Path("api/services/auth_service.py")
    if not auth_service_path.exists():
        print("❌ auth_service.py not found")
        return False
    
    # Read current auth service
    with open(auth_service_path, 'r') as f:
        content = f.read()
    
    # Check if already updated
    if "from .free_email_2fa import free_2fa_service" in content:
        print("✅ Auth service already updated")
        return True
    
    # Add import for free 2FA service
    import_line = "from .free_email_2fa import free_2fa_service"
    
    # Find where to add the import
    lines = content.split('\n')
    import_index = -1
    
    for i, line in enumerate(lines):
        if line.startswith("from .email_service import"):
            import_index = i + 1
            break
        elif line.startswith("import") and import_index == -1:
            import_index = i + 1
    
    if import_index > -1:
        lines.insert(import_index, import_line)
        
        # Update the content
        updated_content = '\n'.join(lines)
        
        # Replace email service calls with free 2FA service for 2FA codes
        updated_content = updated_content.replace(
            "await email_service.send_2fa_code(",
            "await free_2fa_service.send_2fa_code("
        )
        
        # Write updated file
        with open(auth_service_path, 'w') as f:
            f.write(updated_content)
        
        print("✅ Auth service updated to use free 2FA email")
        return True
    else:
        print("❌ Could not find where to add import in auth_service.py")
        return False

def create_test_script():
    """Create a test script for the 2FA email system"""
    test_script = """#!/usr/bin/env python3
\"\"\"
Test script for Free 2FA Email Service
\"\"\"

import asyncio
import sys
from api.services.free_email_2fa import free_2fa_service

async def main():
    print("🧪 Testing Free 2FA Email Service")
    print("=" * 40)
    
    # Test connection
    print("\\n1. Testing email connection...")
    if free_2fa_service.test_connection():
        print("✅ Connection successful!")
    else:
        print("❌ Connection failed!")
        return
    
    # Get test email
    test_email = input("\\nEnter email to send test 2FA code: ").strip()
    if not test_email:
        print("No email provided, skipping test send")
        return
    
    # Send test 2FA code
    print(f"\\n2. Sending test 2FA code to {test_email}...")
    success = await free_2fa_service.send_2fa_code(test_email, "123456", "Test User")
    
    if success:
        print("✅ Test 2FA email sent successfully!")
        print("Check your inbox for the verification code.")
    else:
        print("❌ Failed to send test email")

if __name__ == "__main__":
    asyncio.run(main())
"""
    
    with open("test_free_2fa_email.py", 'w') as f:
        f.write(test_script)
    
    print("✅ Test script created: test_free_2fa_email.py")

async def main():
    """Main setup function"""
    print("🚤 Dockside Pro - Free 2FA Email Setup")
    print("=" * 50)
    
    try:
        # Create/update .env file
        email, app_password = create_env_file()
        
        # Test email setup
        if await test_email_setup(email, app_password):
            # Update auth service
            update_auth_service()
            
            # Create test script
            create_test_script()
            
            print("\n" + "=" * 50)
            print("🎉 FREE 2FA EMAIL SETUP COMPLETE!")
            print("=" * 50)
            
            print("\n📋 What's been configured:")
            print(f"✅ Gmail account: {email}")
            print("✅ App password configured")
            print("✅ Environment variables set")
            print("✅ Auth service updated")
            print("✅ Test script created")
            
            print("\n🚀 Next steps:")
            print("1. Restart your application to load new settings")
            print("2. Test 2FA login at: http://localhost:8000/login")
            print("3. Run test script: python test_free_2fa_email.py")
            
            print("\n🔐 2FA is now enabled with email delivery!")
            
        else:
            print("\n❌ Setup failed. Please check your Gmail credentials.")
            print("\nTroubleshooting:")
            print("1. Make sure 2FA is enabled on your Google account")
            print("2. Use an App Password, not your regular password")
            print("3. Check that 'Less secure app access' is not needed")
            
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
