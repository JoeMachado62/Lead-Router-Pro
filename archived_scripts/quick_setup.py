#!/usr/bin/env python3
"""
Quick Setup Script for Dockside Pro Authentication
Fixes common issues and gets the system running
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(command, description="", check=True):
    """Run a command and handle errors"""
    print(f"📋 {description}")
    print(f"💻 Running: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        if result.stdout:
            print(f"✅ Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"❌ Error details: {e.stderr.strip()}")
        return False

def check_python():
    """Check Python installation"""
    print("🐍 Checking Python installation...")
    
    # Check if python3 is available
    if run_command("python3 --version", "Checking Python 3", check=False):
        print("✅ Python 3 is available")
        return "python3"
    
    # Check if python is available
    if run_command("python --version", "Checking Python", check=False):
        print("✅ Python is available")
        return "python"
    
    print("❌ Python not found. Please install Python 3.")
    return None

def setup_virtual_environment(python_cmd):
    """Set up virtual environment"""
    print("\n🏗️ Setting up virtual environment...")
    
    if not os.path.exists("venv"):
        if not run_command(f"{python_cmd} -m venv venv", "Creating virtual environment"):
            return False
    
    print("✅ Virtual environment ready")
    return True

def install_dependencies(python_cmd):
    """Install Python dependencies"""
    print("\n📦 Installing dependencies...")
    
    # First, upgrade pip
    pip_cmd = "./venv/bin/pip" if os.path.exists("./venv/bin/pip") else f"{python_cmd} -m pip"
    
    if not run_command(f"{pip_cmd} install --upgrade pip", "Upgrading pip"):
        return False
    
    # Install requirements
    if not run_command(f"{pip_cmd} install -r requirements.txt", "Installing requirements"):
        return False
    
    print("✅ Dependencies installed successfully")
    return True

def setup_database():
    """Set up authentication database"""
    print("\n🗄️ Setting up authentication database...")
    
    python_cmd = "./venv/bin/python" if os.path.exists("./venv/bin/python") else "python3"
    
    if not run_command(f"{python_cmd} setup_auth.py", "Initializing authentication system"):
        return False
    
    print("✅ Database setup complete")
    return True

def main():
    """Main setup function"""
    print("="*60)
    print("🚤 DOCKSIDE PRO AUTHENTICATION QUICK SETUP")
    print("="*60)
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    print(f"📁 Working directory: {project_dir}")
    
    # Check Python
    python_cmd = check_python()
    if not python_cmd:
        return False
    
    # Setup virtual environment
    if not setup_virtual_environment(python_cmd):
        return False
    
    # Install dependencies
    if not install_dependencies(python_cmd):
        return False
    
    # Setup database
    if not setup_database():
        return False
    
    print("\n" + "="*60)
    print("🎉 SETUP COMPLETE!")
    print("="*60)
    
    print("\n📋 Next steps:")
    print("1. Activate virtual environment:")
    print("   source venv/bin/activate")
    print("\n2. Start the application:")
    print("   python main_working_final.py")
    print("\n3. Test the system:")
    print("   python test_auth_system.py")
    print("\n4. Access the application:")
    print("   - Login: http://localhost:8000/login")
    print("   - Admin: http://localhost:8000/admin")
    print("   - API Docs: http://localhost:8000/docs")
    
    print("\n🔐 Default login credentials:")
    print("   Admin: admin@dockside.life / DocksideAdmin2025!")
    print("   User:  user@dockside.life / DocksideUser2025!")
    
    print("\n⚠️ IMPORTANT:")
    print("   - Change default passwords after first login")
    print("   - Configure email settings in .env for 2FA")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Setup failed with error: {e}")
        sys.exit(1)
