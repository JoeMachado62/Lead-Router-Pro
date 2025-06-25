"""
Free Email 2FA Service Module
Uses Gmail's free SMTP service for 2FA email delivery
Separate module for easy configuration and testing
"""

import os
import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class FreeEmail2FAService:
    """
    Free email service specifically for 2FA using Gmail
    This module handles all 2FA email sending independently
    """
    
    def __init__(self):
        # Default to a test Gmail account - you can override these
        self.smtp_host = "smtp.gmail.com"
        self.smtp_port = 587
        
        # These will be set from environment or config
        self.email_address = os.getenv("FREE_2FA_EMAIL", "dockside.test.2fa@gmail.com")
        self.email_password = os.getenv("FREE_2FA_PASSWORD", "")  # App password
        self.from_name = "Dockside Pro Security"
        
        # Test mode flag
        self.test_mode = os.getenv("EMAIL_TEST_MODE", "true").lower() == "true"
        
    def configure_email(self, email: str, password: str):
        """Configure email credentials programmatically"""
        self.email_address = email
        self.email_password = password
        logger.info(f"Email configured for: {email}")
    
    async def send_2fa_code(self, to_email: str, code: str, user_name: str = None) -> bool:
        """
        Send 2FA code via email
        Returns True if successful, False otherwise
        """
        if self.test_mode and not self.email_password:
            # In test mode without credentials, simulate success
            logger.info(f"TEST MODE: Would send 2FA code {code} to {to_email}")
            print(f"🔐 TEST 2FA CODE for {to_email}: {code}")
            return True
            
        try:
            subject = f"Your Dockside Pro Security Code: {code}"
            
            # Create HTML email
            html_body = self._create_2fa_html(code, user_name)
            text_body = self._create_2fa_text(code, user_name)
            
            success = await self._send_email(to_email, subject, html_body, text_body)
            
            if success:
                logger.info(f"2FA code sent successfully to {to_email}")
            else:
                logger.error(f"Failed to send 2FA code to {to_email}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error sending 2FA code to {to_email}: {str(e)}")
            return False
    
    async def _send_email(self, to_email: str, subject: str, html_body: str, text_body: str) -> bool:
        """Internal method to send email via SMTP"""
        try:
            if not self.email_address or not self.email_password:
                logger.error("Email credentials not configured")
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.email_address}>"
            msg['To'] = to_email
            msg['Date'] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")
            
            # Add text and HTML parts
            text_part = MIMEText(text_body, 'plain')
            html_part = MIMEText(html_body, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send via Gmail SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_address, self.email_password)
                server.send_message(msg)
            
            return True
            
        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP Authentication failed - check email credentials")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email: {str(e)}")
            return False
    
    def _create_2fa_html(self, code: str, user_name: str = None) -> str:
        """Create HTML email template for 2FA code"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>2FA Security Code</title>
            <style>
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                    margin: 0; 
                    padding: 20px; 
                    background-color: #f8fafc; 
                    color: #334155;
                }}
                .container {{ 
                    max-width: 500px; 
                    margin: 0 auto; 
                    background-color: white; 
                    border-radius: 12px; 
                    padding: 40px 30px; 
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                }}
                .header {{ 
                    text-align: center; 
                    margin-bottom: 30px; 
                }}
                .logo {{ 
                    color: #3b82f6; 
                    font-size: 28px; 
                    font-weight: 700; 
                    margin-bottom: 10px;
                }}
                .title {{ 
                    color: #1e293b; 
                    font-size: 24px; 
                    font-weight: 600; 
                    margin: 0;
                }}
                .code-section {{ 
                    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); 
                    color: white; 
                    padding: 30px 20px; 
                    border-radius: 10px; 
                    text-align: center; 
                    margin: 30px 0; 
                }}
                .code-label {{ 
                    font-size: 16px; 
                    margin-bottom: 15px; 
                    opacity: 0.9;
                }}
                .code {{ 
                    font-size: 36px; 
                    font-weight: 700; 
                    letter-spacing: 8px; 
                    margin: 15px 0; 
                    font-family: 'Courier New', monospace;
                }}
                .expiry {{ 
                    font-size: 14px; 
                    margin-top: 15px; 
                    opacity: 0.8;
                }}
                .warning {{ 
                    background-color: #fef3c7; 
                    border-left: 4px solid #f59e0b; 
                    color: #92400e; 
                    padding: 16px 20px; 
                    border-radius: 6px; 
                    margin: 25px 0; 
                    font-size: 14px;
                }}
                .footer {{ 
                    text-align: center; 
                    margin-top: 40px; 
                    color: #64748b; 
                    font-size: 14px; 
                    line-height: 1.5;
                }}
                .timestamp {{ 
                    font-size: 12px; 
                    color: #94a3b8; 
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🚤 Dockside Pro</div>
                    <h1 class="title">Security Verification</h1>
                </div>
                
                <p>{"Hello " + user_name + "," if user_name else "Hello,"}</p>
                
                <p>You're attempting to sign in to your Dockside Pro account. Please use the verification code below to complete your login:</p>
                
                <div class="code-section">
                    <div class="code-label">Your verification code is:</div>
                    <div class="code">{code}</div>
                    <div class="expiry">⏰ Expires in 10 minutes</div>
                </div>
                
                <div class="warning">
                    <strong>🔒 Security Notice:</strong> If you didn't request this code, please ignore this email and consider changing your password. Never share this code with anyone.
                </div>
                
                <p>This code will expire in 10 minutes for your security. If you need a new code, please request one from the login page.</p>
                
                <div class="footer">
                    <p>This is an automated security message from Dockside Pro</p>
                    <p>© 2025 Dockside Pro. All rights reserved.</p>
                    <div class="timestamp">Sent: {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}</div>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_2fa_text(self, code: str, user_name: str = None) -> str:
        """Create plain text email for 2FA code"""
        return f"""
DOCKSIDE PRO - SECURITY VERIFICATION

{"Hello " + user_name + "," if user_name else "Hello,"}

You're attempting to sign in to your Dockside Pro account.

Your verification code is: {code}

This code expires in 10 minutes.

SECURITY NOTICE: If you didn't request this code, please ignore this email and consider changing your password. Never share this code with anyone.

---
This is an automated security message from Dockside Pro
© 2025 Dockside Pro. All rights reserved.
Sent: {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}
        """
    
    def test_connection(self) -> bool:
        """Test email connection and credentials"""
        try:
            if not self.email_address or not self.email_password:
                logger.error("Email credentials not configured for testing")
                return False
                
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_address, self.email_password)
                logger.info("Email connection test successful")
                return True
                
        except Exception as e:
            logger.error(f"Email connection test failed: {str(e)}")
            return False
    
    async def send_test_email(self, to_email: str) -> bool:
        """Send a test email to verify everything works"""
        test_code = "123456"
        logger.info(f"Sending test 2FA email to {to_email}")
        return await self.send_2fa_code(to_email, test_code, "Test User")


# Global instance for easy import
free_2fa_service = FreeEmail2FAService()


# Configuration helper functions
def setup_gmail_2fa(email: str, app_password: str):
    """
    Setup Gmail for 2FA emails
    
    Args:
        email: Gmail address (e.g., 'your.email@gmail.com')
        app_password: Gmail App Password (not regular password)
    
    Instructions to get Gmail App Password:
    1. Enable 2FA on your Google account
    2. Go to Google Account settings
    3. Security > 2-Step Verification > App passwords
    4. Generate password for "Mail"
    5. Use that 16-character password here
    """
    free_2fa_service.configure_email(email, app_password)
    logger.info(f"Gmail 2FA configured for: {email}")


def setup_env_2fa():
    """Setup 2FA from environment variables"""
    email = os.getenv("FREE_2FA_EMAIL")
    password = os.getenv("FREE_2FA_PASSWORD")
    
    if email and password:
        free_2fa_service.configure_email(email, password)
        logger.info("2FA email configured from environment variables")
        return True
    else:
        logger.warning("2FA email environment variables not found")
        return False


# Auto-setup from environment on import
setup_env_2fa()
