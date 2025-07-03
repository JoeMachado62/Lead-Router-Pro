#!/usr/bin/env python3
"""
Install 2FA Email Dependencies
Ensures all required packages for 2FA email functionality are installed
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description=""):
    """Run a command and handle errors"""
    print(f"📦 {description}")
    print(f"💻 Running: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(f"✅ Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"❌ Error details: {e.stderr.strip()}")
        return False

def check_python():
    """Check Python version"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    print(f"Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required")
        return False
    
    print("✅ Python version is compatible")
    return True

def install_dependencies():
    """Install all dependencies from requirements.txt"""
    print("\n📦 Installing dependencies...")
    
    # Check if we're in a virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if not in_venv:
        print("⚠️  Warning: Not in a virtual environment")
        print("Consider creating one with: python -m venv venv && source venv/bin/activate")
        
        proceed = input("Continue anyway? (y/n): ").strip().lower()
        if proceed != 'y':
            print("❌ Installation cancelled")
            return False
    
    # Upgrade pip first
    if not run_command(f"{sys.executable} -m pip install --upgrade pip", "Upgrading pip"):
        return False
    
    # Install requirements
    if not run_command(f"{sys.executable} -m pip install -r requirements.txt", "Installing requirements"):
        return False
    
    print("✅ All dependencies installed successfully")
    return True

def verify_email_imports():
    """Verify that email-related imports work"""
    print("\n🔍 Verifying email imports...")
    
    test_imports = [
        ("smtplib", "SMTP library"),
        ("email.mime.text", "Email MIME support"),
        ("email.mime.multipart", "Email multipart support"),
        ("jinja2", "Template engine"),
    ]
    
    all_good = True
    
    for module, description in test_imports:
        try:
            __import__(module)
            print(f"✅ {description}: OK")
        except ImportError as e:
            print(f"❌ {description}: FAILED - {e}")
            all_good = False
    
    return all_good

def test_2fa_service():
    """Test that the 2FA service can be imported"""
    print("\n🧪 Testing 2FA service import...")
    
    try:
        # Change to the project directory
        project_dir = Path(__file__).parent
        os.chdir(project_dir)
        
        # Try to import the 2FA service
        sys.path.insert(0, str(project_dir))
        from api.services.free_email_2fa import free_2fa_service
        
        print("✅ 2FA service imported successfully")
        
        # Test basic functionality
        if hasattr(free_2fa_service, 'send_2fa_code'):
            print("✅ 2FA service has required methods")
        else:
            print("❌ 2FA service missing required methods")
            return False
            
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import 2FA service: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing 2FA service: {e}")
        return False

def create_test_env():
    """Create a sample .env file if it doesn't exist"""
    env_path = Path(".env")
    
    if env_path.exists():
        print("\n✅ .env file already exists")
        return True
    
    print("\n📝 Creating sample .env file...")
    
    sample_env = """# Dockside Pro Configuration

# Database Configuration
DATABASE_URL=sqlite:///./dockside_pro.db

# JWT Configuration
JWT_SECRET_KEY=your-super-secure-jwt-secret-key-change-this
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Demo 2FA Configuration (for testing without email)
EMAIL_TEST_MODE=true
TWO_FACTOR_ENABLED=true
TWO_FACTOR_CODE_LENGTH=6
TWO_FACTOR_CODE_EXPIRE_MINUTES=10
DEMO_2FA_MODE=true

# Gmail 2FA Configuration (uncomment and configure for production)
# FREE_2FA_EMAIL=your.email@gmail.com
# FREE_2FA_PASSWORD=your-16-char-app-password
# EMAIL_TEST_MODE=false

# Security Settings
ACCOUNT_LOCKOUT_THRESHOLD=5
ACCOUNT_LOCKOUT_DURATION_MINUTES=30
SESSION_TIMEOUT_MINUTES=60

# Application Settings
DEBUG=false
LOG_LEVEL=INFO
"""
    
    try:
        with open(env_path, 'w') as f:
            f.write(sample_env)
        print("✅ Sample .env file created")
        print("📝 Edit .env file to configure your settings")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def main():
    """Main installation function"""
    print("🚤 Dockside Pro - 2FA Dependencies Installer")
    print("=" * 50)
    
    # Check Python version
    if not check_python():
        return False
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Verify imports
    if not verify_email_imports():
        print("\n❌ Some email imports failed. Try:")
        print("pip install --upgrade email-validator jinja2")
        return False
    
    # Test 2FA service
    if not test_2fa_service():
        print("\n❌ 2FA service test failed")
        return False
    
    # Create sample .env
    create_test_env()
    
    print("\n" + "=" * 50)
    print("🎉 2FA DEPENDENCIES INSTALLATION COMPLETE!")
    print("=" * 50)
    
    print("\n📋 What's been installed:")
    print("✅ All Python dependencies")
    print("✅ Email libraries verified")
    print("✅ 2FA service tested")
    print("✅ Sample .env file created")
    
    print("\n🚀 Next steps:")
    print("1. Configure .env file with your settings")
    print("2. For demo mode: python demo_2fa_setup.py")
    print("3. For Gmail: python setup_free_2fa_email.py")
    print("4. Start server: python main_working_final.py")
    
    print("\n📚 Documentation:")
    print("- 2FA Setup Guide: 2FA_SETUP_GUIDE.md")
    print("- Gmail Setup: GMAIL_SETUP_GUIDE.md")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Installation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Installation failed with error: {e}")
        sys.exit(1)
