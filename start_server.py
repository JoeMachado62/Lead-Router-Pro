#!/usr/bin/env python3
"""
Start script for Dockside Pro server
Handles different Python environments and starts the application
"""

import os
import sys
import subprocess
from pathlib import Path

def find_python():
    """Find the correct Python interpreter"""
    # Check if we're in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        return sys.executable
    
    # Check for python3 in venv
    venv_python = "./venv/bin/python"
    if os.path.exists(venv_python):
        return venv_python
    
    # Check for python in venv (Windows)
    venv_python_win = "./venv/Scripts/python.exe"
    if os.path.exists(venv_python_win):
        return venv_python_win
    
    # Fall back to system python3
    return "python3"

def main():
    """Start the Dockside Pro server"""
    print("🚤 Starting Dockside Pro Server...")
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Find Python interpreter
    python_cmd = find_python()
    print(f"🐍 Using Python: {python_cmd}")
    
    # Check if virtual environment is activated
    if not (hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)):
        print("⚠️  Virtual environment not activated.")
        print("💡 Run: source venv/bin/activate")
        print("💡 Or use: python3 quick_setup.py")
    
    # Start the server
    try:
        print("🚀 Starting FastAPI server on http://localhost:8000")
        print("📱 Access points:")
        print("   - Login: http://localhost:8000/login")
        print("   - Admin: http://localhost:8000/admin")
        print("   - API Docs: http://localhost:8000/docs")
        print("   - Health: http://localhost:8000/health")
        print("\n🔐 Default credentials:")
        print("   admin@dockside.life / DocksideAdmin2025!")
        print("\n⏹️  Press Ctrl+C to stop the server")
        print("-" * 50)
        
        # Run the main application
        subprocess.run([python_cmd, "-m", "uvicorn", "main_working_final:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "trace"], check=True)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Server failed to start: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Run setup first: python3 quick_setup.py")
        print("2. Check if all dependencies are installed")
        print("3. Activate virtual environment: source venv/bin/activate")
        return 1
    except FileNotFoundError:
        print(f"\n❌ Python interpreter not found: {python_cmd}")
        print("\n🔧 Try:")
        print("1. Install Python 3: apt update && apt install python3")
        print("2. Run setup: python3 quick_setup.py")
        return 1

if __name__ == "__main__":
    sys.exit(main())
