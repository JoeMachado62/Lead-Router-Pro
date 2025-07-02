#!/usr/bin/env python3
"""
Comprehensive 2FA and Email System Test
Tests the complete authentication flow including email sending
"""

import asyncio
import os
import sys
import json
import requests
from datetime import datetime
from typing import Dict, Any

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.services.email_service import email_service
from api.services.auth_service import auth_service
from database.simple_connection import get_db_session
from database.models import User, Tenant, TwoFactorCode


class TwoFactorEmailTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_email = "test.2fa@dockside.life"
        self.test_password = "TestPassword123!"
        self.test_domain = "dockside.life"
        self.session = requests.Session()
        
    def print_header(self, title: str):
        """Print a formatted header"""
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
        
    def print_step(self, step: str, status: str = "INFO"):
        """Print a test step"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{status}] {step}")
        
    def print_result(self, success: bool, message: str):
        """Print test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}: {message}")
        
    async def test_email_service_configuration(self):
        """Test email service configuration"""
        self.print_header("EMAIL SERVICE CONFIGURATION TEST")
        
        # Check environment variables
        smtp_host = os.getenv("SMTP_HOST")
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_password = os.getenv("SMTP_PASSWORD")
        
        self.print_step("Checking SMTP configuration...")
        
        if not smtp_username or not smtp_password:
            self.print_result(False, "SMTP credentials not configured in environment")
            print("\n  Required environment variables:")
            print("  - SMTP_HOST (default: smtp.gmail.com)")
            print("  - SMTP_PORT (default: 587)")
            print("  - SMTP_USERNAME (your email)")
            print("  - SMTP_PASSWORD (your app password)")
            print("  - SMTP_FROM_EMAIL (sender email)")
            print("  - SMTP_FROM_NAME (sender name)")
            return False
        else:
            self.print_result(True, f"SMTP configured: {smtp_username} via {smtp_host}")
            
        # Test email service initialization
        self.print_step("Testing email service initialization...")
        try:
            service = email_service
            self.print_result(True, f"Email service initialized successfully")
            print(f"    From: {service.from_name} <{service.from_email}>")
            print(f"    SMTP: {service.smtp_host}:{service.smtp_port}")
            return True
        except Exception as e:
            self.print_result(False, f"Email service initialization failed: {str(e)}")
            return False
    
    async def test_send_2fa_email(self):
        """Test sending 2FA email"""
        self.print_header("2FA EMAIL SENDING TEST")
        
        self.print_step("Sending test 2FA email...")
        
        try:
            success = await email_service.send_2fa_code(
                to_email=self.test_email,
                code="123456",
                user_name="Test User"
            )
            
            if success:
                self.print_result(True, f"2FA email sent successfully to {self.test_email}")
                print("    Check your email for the 2FA code")
                return True
            else:
                self.print_result(False, "Failed to send 2FA email")
                return False
                
        except Exception as e:
            self.print_result(False, f"Error sending 2FA email: {str(e)}")
            return False
    
    async def test_send_password_reset_email(self):
        """Test sending password reset email"""
        self.print_header("PASSWORD RESET EMAIL TEST")
        
        self.print_step("Sending test password reset email...")
        
        try:
            success = await email_service.send_password_reset(
                to_email=self.test_email,
                reset_code="RESET123",
                user_name="Test User"
            )
            
            if success:
                self.print_result(True, f"Password reset email sent successfully to {self.test_email}")
                print("    Check your email for the reset code")
                return True
            else:
                self.print_result(False, "Failed to send password reset email")
                return False
                
        except Exception as e:
            self.print_result(False, f"Error sending password reset email: {str(e)}")
            return False
    
    async def test_send_welcome_email(self):
        """Test sending welcome email"""
        self.print_header("WELCOME EMAIL TEST")
        
        self.print_step("Sending test welcome email...")
        
        try:
            success = await email_service.send_welcome_email(
                to_email=self.test_email,
                user_name="Test User",
                verification_code="VERIFY123"
            )
            
            if success:
                self.print_result(True, f"Welcome email sent successfully to {self.test_email}")
                print("    Check your email for the verification code")
                return True
            else:
                self.print_result(False, "Failed to send welcome email")
                return False
                
        except Exception as e:
            self.print_result(False, f"Error sending welcome email: {str(e)}")
            return False
    
    def test_database_setup(self):
        """Test database setup for authentication"""
        self.print_header("DATABASE SETUP TEST")
        
        self.print_step("Testing database connection...")
        
        try:
            db = get_db_session()
            
            # Test tenant exists
            tenant = db.query(Tenant).filter(Tenant.domain == self.test_domain).first()
            if not tenant:
                self.print_result(False, f"No tenant found for domain: {self.test_domain}")
                print("    Run setup_auth.py to create the tenant")
                return False
            else:
                self.print_result(True, f"Tenant found: {tenant.name} (ID: {tenant.id})")
            
            # Test user table structure
            self.print_step("Checking user table structure...")
            user_count = db.query(User).count()
            self.print_result(True, f"User table accessible, {user_count} users found")
            
            # Test 2FA codes table
            self.print_step("Checking 2FA codes table...")
            code_count = db.query(TwoFactorCode).count()
            self.print_result(True, f"TwoFactorCode table accessible, {code_count} codes found")
            
            db.close()
            return True
            
        except Exception as e:
            self.print_result(False, f"Database error: {str(e)}")
            return False
    
    def test_api_registration(self):
        """Test user registration via API"""
        self.print_header("API REGISTRATION TEST")
        
        self.print_step("Testing user registration...")
        
        try:
            # First, try to delete existing test user
            db = get_db_session()
            tenant = db.query(Tenant).filter(Tenant.domain == self.test_domain).first()
            if tenant:
                existing_user = db.query(User).filter(
                    User.email == self.test_email,
                    User.tenant_id == tenant.id
                ).first()
                if existing_user:
                    db.delete(existing_user)
                    db.commit()
                    self.print_step("Deleted existing test user")
            db.close()
            
            # Register new user
            response = self.session.post(f"{self.base_url}/api/v1/auth/register", json={
                "email": self.test_email,
                "password": self.test_password,
                "first_name": "Test",
                "last_name": "User",
                "domain": self.test_domain
            })
            
            if response.status_code == 200:
                data = response.json()
                self.print_result(True, f"User registered successfully: {data['message']}")
                print(f"    User ID: {data.get('user_id', 'N/A')}")
                return True
            else:
                self.print_result(False, f"Registration failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.print_result(False, f"Registration error: {str(e)}")
            return False
    
    def test_api_login_with_2fa(self):
        """Test login with 2FA via API"""
        self.print_header("API LOGIN WITH 2FA TEST")
        
        # First verify the user's email
        self.print_step("Verifying user email first...")
        
        try:
            # Get the verification code from database
            db = get_db_session()
            tenant = db.query(Tenant).filter(Tenant.domain == self.test_domain).first()
            user = db.query(User).filter(
                User.email == self.test_email,
                User.tenant_id == tenant.id
            ).first()
            
            if not user:
                self.print_result(False, "Test user not found")
                return False
            
            # Get verification code
            verification_code = db.query(TwoFactorCode).filter(
                TwoFactorCode.user_id == user.id,
                TwoFactorCode.purpose == "email_verification",
                TwoFactorCode.is_used == False
            ).first()
            
            if verification_code:
                # Verify email
                verify_response = self.session.post(f"{self.base_url}/api/v1/auth/verify-email", json={
                    "email": self.test_email,
                    "verification_code": verification_code.code,
                    "domain": self.test_domain
                })
                
                if verify_response.status_code == 200:
                    self.print_result(True, "Email verified successfully")
                else:
                    self.print_result(False, f"Email verification failed: {verify_response.text}")
                    return False
            
            db.close()
            
            # Now test login
            self.print_step("Testing login step 1 (email/password)...")
            
            login_response = self.session.post(f"{self.base_url}/api/v1/auth/login", json={
                "email": self.test_email,
                "password": self.test_password,
                "domain": self.test_domain
            })
            
            if login_response.status_code == 200:
                login_data = login_response.json()
                
                if login_data.get("requires_2fa"):
                    self.print_result(True, "Login step 1 successful, 2FA required")
                    print(f"    Message: {login_data['message']}")
                    print(f"    Session token received: {login_data['session_token'][:20]}...")
                    
                    # Get 2FA code from database
                    self.print_step("Retrieving 2FA code from database...")
                    
                    db = get_db_session()
                    two_fa_code = db.query(TwoFactorCode).filter(
                        TwoFactorCode.user_id == login_data['user_id'],
                        TwoFactorCode.purpose == "login",
                        TwoFactorCode.is_used == False
                    ).order_by(TwoFactorCode.created_at.desc()).first()
                    
                    if two_fa_code:
                        self.print_result(True, f"2FA code found: {two_fa_code.code}")
                        
                        # Test 2FA verification
                        self.print_step("Testing 2FA verification...")
                        
                        verify_2fa_response = self.session.post(f"{self.base_url}/api/v1/auth/verify-2fa", json={
                            "user_id": login_data['user_id'],
                            "code": two_fa_code.code,
                            "session_token": login_data['session_token']
                        })
                        
                        if verify_2fa_response.status_code == 200:
                            auth_data = verify_2fa_response.json()
                            self.print_result(True, "2FA verification successful")
                            print(f"    Access token received: {auth_data['access_token'][:20]}...")
                            print(f"    User: {auth_data['user']['first_name']} {auth_data['user']['last_name']}")
                            return True
                        else:
                            self.print_result(False, f"2FA verification failed: {verify_2fa_response.text}")
                            return False
                    else:
                        self.print_result(False, "No 2FA code found in database")
                        return False
                    
                    db.close()
                else:
                    self.print_result(True, "Login successful without 2FA")
                    return True
            else:
                self.print_result(False, f"Login failed: {login_response.status_code} - {login_response.text}")
                return False
                
        except Exception as e:
            self.print_result(False, f"Login test error: {str(e)}")
            return False
    
    def test_api_password_reset(self):
        """Test password reset via API"""
        self.print_header("API PASSWORD RESET TEST")
        
        self.print_step("Testing password reset request...")
        
        try:
            # Request password reset
            reset_response = self.session.post(f"{self.base_url}/api/v1/auth/forgot-password", json={
                "email": self.test_email,
                "domain": self.test_domain
            })
            
            if reset_response.status_code == 200:
                reset_data = reset_response.json()
                self.print_result(True, f"Password reset requested: {reset_data['message']}")
                
                # Get reset code from database
                self.print_step("Retrieving reset code from database...")
                
                db = get_db_session()
                tenant = db.query(Tenant).filter(Tenant.domain == self.test_domain).first()
                user = db.query(User).filter(
                    User.email == self.test_email,
                    User.tenant_id == tenant.id
                ).first()
                
                reset_code = db.query(TwoFactorCode).filter(
                    TwoFactorCode.user_id == user.id,
                    TwoFactorCode.purpose == "password_reset",
                    TwoFactorCode.is_used == False
                ).order_by(TwoFactorCode.created_at.desc()).first()
                
                if reset_code:
                    self.print_result(True, f"Reset code found: {reset_code.code}")
                    
                    # Test password reset
                    self.print_step("Testing password reset with code...")
                    
                    new_password = "NewTestPassword123!"
                    
                    reset_confirm_response = self.session.post(f"{self.base_url}/api/v1/auth/reset-password", json={
                        "email": self.test_email,
                        "reset_code": reset_code.code,
                        "new_password": new_password,
                        "domain": self.test_domain
                    })
                    
                    if reset_confirm_response.status_code == 200:
                        confirm_data = reset_confirm_response.json()
                        self.print_result(True, f"Password reset successful: {confirm_data['message']}")
                        
                        # Test login with new password
                        self.print_step("Testing login with new password...")
                        
                        login_response = self.session.post(f"{self.base_url}/api/v1/auth/login", json={
                            "email": self.test_email,
                            "password": new_password,
                            "domain": self.test_domain
                        })
                        
                        if login_response.status_code == 200:
                            self.print_result(True, "Login with new password successful")
                            return True
                        else:
                            self.print_result(False, f"Login with new password failed: {login_response.text}")
                            return False
                    else:
                        self.print_result(False, f"Password reset failed: {reset_confirm_response.text}")
                        return False
                else:
                    self.print_result(False, "No reset code found in database")
                    return False
                
                db.close()
            else:
                self.print_result(False, f"Password reset request failed: {reset_response.text}")
                return False
                
        except Exception as e:
            self.print_result(False, f"Password reset test error: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all tests"""
        print(f"\n🚀 Starting 2FA and Email System Tests")
        print(f"Test Email: {self.test_email}")
        print(f"Base URL: {self.base_url}")
        
        results = []
        
        # Test email service configuration
        results.append(await self.test_email_service_configuration())
        
        # Test database setup
        results.append(self.test_database_setup())
        
        # Test email sending
        results.append(await self.test_send_2fa_email())
        results.append(await self.test_send_password_reset_email())
        results.append(await self.test_send_welcome_email())
        
        # Test API endpoints
        results.append(self.test_api_registration())
        results.append(self.test_api_login_with_2fa())
        results.append(self.test_api_password_reset())
        
        # Summary
        self.print_header("TEST SUMMARY")
        
        passed = sum(results)
        total = len(results)
        
        print(f"Tests Passed: {passed}/{total}")
        
        if passed == total:
            print("🎉 All tests passed! 2FA and email system is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the output above for details.")
            
        return passed == total


async def main():
    """Main test function"""
    tester = TwoFactorEmailTester()
    
    # Check if server is running
    try:
        response = requests.get(f"{tester.base_url}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server is not responding correctly")
            print("   Please start the server with: python start_server.py")
            return
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to server")
        print("   Please start the server with: python start_server.py")
        return
    
    # Run tests
    success = await tester.run_all_tests()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
