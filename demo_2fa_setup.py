#!/usr/bin/env python3
"""
Demo 2FA Setup - Quick setup for testing without email configuration
Uses console output to display 2FA codes for immediate testing
"""

import os
import asyncio
from pathlib import Path
from api.services.free_email_2fa import free_2fa_service

class Demo2FAService:
    """Demo 2FA service that prints codes to console for testing"""
    
    def __init__(self):
        self.test_mode = True
        
    async def send_2fa_code(self, to_email: str, code: str, user_name: str = None) -> bool:
        """Print 2FA code to console for demo purposes"""
        print("\n" + "="*60)
        print("🔐 DEMO 2FA CODE DELIVERY")
        print("="*60)
        print(f"📧 To: {to_email}")
        print(f"👤 User: {user_name or 'Unknown'}")
        print(f"🔢 Code: {code}")
        print(f"⏰ Expires: 10 minutes")
        print("="*60)
        print("💡 In production, this would be sent via email")
        print("="*60)
        return True

def setup_demo_mode():
    """Setup demo mode for immediate testing"""
    print("🚤 Dockside Pro - Demo 2FA Setup")
    print("="*50)
    print("This sets up 2FA in demo mode for immediate testing.")
    print("2FA codes will be displayed in the console instead of sent via email.")
    
    # Create or update .env file
    env_path = Path(".env")
    
    demo_settings = """
# Demo 2FA Configuration (for testing without email)
EMAIL_TEST_MODE=true
TWO_FACTOR_ENABLED=true
TWO_FACTOR_CODE_LENGTH=6
TWO_FACTOR_CODE_EXPIRE_MINUTES=10

# Demo mode - codes shown in console
DEMO_2FA_MODE=true
"""
    
    # Read existing .env or create new
    env_content = ""
    if env_path.exists():
        with open(env_path, 'r') as f:
            env_content = f.read()
    
    # Remove existing demo settings if present
    lines = env_content.split('\n')
    filtered_lines = []
    skip_demo = False
    
    for line in lines:
        if line.strip().startswith("# Demo 2FA Configuration"):
            skip_demo = True
            continue
        elif line.strip().startswith("#") and skip_demo:
            if "Demo" not in line and "2FA" not in line:
                skip_demo = False
                filtered_lines.append(line)
        elif not skip_demo:
            if not any(line.startswith(key) for key in ["EMAIL_TEST_MODE=", "TWO_FACTOR_ENABLED=", "TWO_FACTOR_CODE_LENGTH=", "TWO_FACTOR_CODE_EXPIRE_MINUTES=", "DEMO_2FA_MODE="]):
                filtered_lines.append(line)
    
    # Write updated .env file
    with open(env_path, 'w') as f:
        f.write('\n'.join(filtered_lines))
        f.write(demo_settings)
    
    print(f"✅ Demo configuration saved to {env_path}")

def update_auth_service_for_demo():
    """Update auth service to use demo 2FA in test mode"""
    print("\n🔄 Updating auth service for demo mode...")
    
    auth_service_path = Path("api/services/auth_service.py")
    if not auth_service_path.exists():
        print("❌ auth_service.py not found")
        return False
    
    # Read current auth service
    with open(auth_service_path, 'r') as f:
        content = f.read()
    
    # Check if demo import already exists
    if "Demo 2FA mode" in content:
        print("✅ Auth service already configured for demo mode")
        return True
    
    # Add demo 2FA code at the top after imports
    demo_code = '''
# Demo 2FA mode for testing without email
import os
if os.getenv("DEMO_2FA_MODE", "false").lower() == "true":
    class Demo2FAService:
        async def send_2fa_code(self, to_email: str, code: str, user_name: str = None) -> bool:
            print("\\n" + "="*60)
            print("🔐 DEMO 2FA CODE DELIVERY")
            print("="*60)
            print(f"📧 To: {to_email}")
            print(f"👤 User: {user_name or 'Unknown'}")
            print(f"🔢 Code: {code}")
            print(f"⏰ Expires: 10 minutes")
            print("="*60)
            print("💡 In production, this would be sent via email")
            print("="*60)
            return True
    
    # Override the email service for demo
    demo_2fa_service = Demo2FAService()
else:
    from .free_email_2fa import free_2fa_service as demo_2fa_service
'''
    
    # Find where to insert demo code (after imports)
    lines = content.split('\n')
    insert_index = -1
    
    for i, line in enumerate(lines):
        if line.startswith('class ') or line.startswith('def ') or line.startswith('async def'):
            insert_index = i
            break
    
    if insert_index > -1:
        lines.insert(insert_index, demo_code)
        
        # Update email service calls to use demo service
        updated_content = '\n'.join(lines)
        updated_content = updated_content.replace(
            "await email_service.send_2fa_code(",
            "await demo_2fa_service.send_2fa_code("
        )
        
        # Write updated file
        with open(auth_service_path, 'w') as f:
            f.write(updated_content)
        
        print("✅ Auth service updated for demo mode")
        return True
    else:
        print("❌ Could not find insertion point in auth_service.py")
        return False

def enable_2fa_for_users():
    """Enable 2FA for existing users"""
    print("\n👥 Enabling 2FA for test users...")
    
    setup_script = '''
import asyncio
from database.simple_connection import get_db_session
from database.models import User

async def enable_2fa():
    db = get_db_session()
    try:
        users = db.query(User).all()
        for user in users:
            user.two_factor_enabled = True
            print(f"✅ Enabled 2FA for: {user.email}")
        db.commit()
        print(f"\\n🔐 2FA enabled for {len(users)} users")
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(enable_2fa())
'''
    
    with open("enable_2fa_users.py", 'w') as f:
        f.write(setup_script)
    
    print("✅ Created enable_2fa_users.py script")

def create_demo_test_script():
    """Create a test script for demo 2FA"""
    test_script = '''#!/usr/bin/env python3
"""
Demo 2FA Test Script
Tests the demo 2FA system with console output
"""

import asyncio
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

async def test_demo_2fa():
    print("🧪 Testing Demo 2FA System")
    print("="*40)
    
    # Test login step 1
    print("\\n1. Testing login step 1...")
    
    login_data = {
        "email": "joe@ezwai.com",
        "password": "DocksideAdmin2025!",
        "domain": "dockside.life"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Login step 1 successful!")
            
            if data.get("requires_2fa"):
                print("🔐 2FA required - check console for code")
                print("\\nLook for the 2FA code displayed above, then use it to complete login")
                
                # Get 2FA code from user
                code = input("\\nEnter the 2FA code shown above: ").strip()
                
                # Test 2FA verification
                verify_data = {
                    "user_id": data.get("user_id"),
                    "code": code,
                    "session_token": data.get("session_token")
                }
                
                verify_response = requests.post(f"{BASE_URL}/api/v1/auth/verify-2fa", json=verify_data)
                
                if verify_response.status_code == 200:
                    verify_result = verify_response.json()
                    print("✅ 2FA verification successful!")
                    print(f"Access token received: {verify_result.get('access_token')[:20]}...")
                else:
                    print(f"❌ 2FA verification failed: {verify_response.text}")
            else:
                print("⚠️ 2FA not required - check configuration")
        else:
            print(f"❌ Login failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    print("Make sure the server is running: python main_working_final.py")
    print("Then press Enter to continue...")
    input()
    
    asyncio.run(test_demo_2fa())
'''
    
    with open("test_demo_2fa.py", 'w') as f:
        f.write(test_script)
    
    print("✅ Created test_demo_2fa.py script")

async def main():
    """Main demo setup function"""
    print("🚤 Dockside Pro - Demo 2FA Setup")
    print("="*50)
    print("This configures 2FA in demo mode for immediate testing.")
    print("2FA codes will be displayed in the console.")
    
    try:
        # Setup demo mode
        setup_demo_mode()
        
        # Update auth service
        update_auth_service_for_demo()
        
        # Create helper scripts
        enable_2fa_for_users()
        create_demo_test_script()
        
        print("\n" + "="*50)
        print("🎉 DEMO 2FA SETUP COMPLETE!")
        print("="*50)
        
        print("\n📋 What's been configured:")
        print("✅ Demo mode enabled")
        print("✅ 2FA codes will show in console")
        print("✅ Auth service updated")
        print("✅ Helper scripts created")
        
        print("\n🚀 Next steps:")
        print("1. Enable 2FA for users: python enable_2fa_users.py")
        print("2. Start the application: python main_working_final.py")
        print("3. Test demo 2FA: python test_demo_2fa.py")
        print("4. Login at: http://localhost:8000/login")
        
        print("\n🔐 Demo 2FA is now ready!")
        print("When you login, the 2FA code will appear in the console.")
        
        # Ask if user wants to enable 2FA for users now
        enable_now = input("\\nEnable 2FA for existing users now? (y/n): ").strip().lower()
        if enable_now == 'y':
            print("\\nRunning enable_2fa_users.py...")
            os.system("python enable_2fa_users.py")
        
    except Exception as e:
        print(f"\\n❌ Demo setup failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
