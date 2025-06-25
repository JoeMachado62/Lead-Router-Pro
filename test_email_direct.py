#!/usr/bin/env python3
"""
Direct Email Test - Tests email functionality using server environment
"""

import asyncio
import os
import sys
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from api.services.email_service import email_service


async def test_email_direct():
    """Test email sending directly"""
    print("🧪 Direct Email Service Test")
    print("=" * 50)
    
    # Check configuration
    print(f"SMTP Host: {os.getenv('SMTP_HOST')}")
    print(f"SMTP Username: {os.getenv('SMTP_USERNAME')}")
    print(f"SMTP Password: {'*' * len(os.getenv('SMTP_PASSWORD', '')) if os.getenv('SMTP_PASSWORD') else 'Not set'}")
    print(f"From Email: {os.getenv('SMTP_FROM_EMAIL')}")
    print()
    
    test_email = "ezautobuying@gmail.com"  # Using your actual email
    
    # Test 2FA email
    print("📧 Testing 2FA Email...")
    try:
        success = await email_service.send_2fa_code(
            to_email=test_email,
            code="TEST123",
            user_name="Test User"
        )
        print(f"✅ 2FA Email: {'SUCCESS' if success else 'FAILED'}")
    except Exception as e:
        print(f"❌ 2FA Email Error: {str(e)}")
    
    # Test password reset email
    print("📧 Testing Password Reset Email...")
    try:
        success = await email_service.send_password_reset(
            to_email=test_email,
            reset_code="RESET456",
            user_name="Test User"
        )
        print(f"✅ Password Reset Email: {'SUCCESS' if success else 'FAILED'}")
    except Exception as e:
        print(f"❌ Password Reset Email Error: {str(e)}")
    
    # Test welcome email
    print("📧 Testing Welcome Email...")
    try:
        success = await email_service.send_welcome_email(
            to_email=test_email,
            user_name="Test User",
            verification_code="WELCOME789"
        )
        print(f"✅ Welcome Email: {'SUCCESS' if success else 'FAILED'}")
    except Exception as e:
        print(f"❌ Welcome Email Error: {str(e)}")
    
    print()
    print("🎯 Check your email inbox for the test emails!")
    print(f"📬 Email address: {test_email}")


if __name__ == "__main__":
    asyncio.run(test_email_direct())
