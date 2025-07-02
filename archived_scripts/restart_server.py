#!/usr/bin/env python3
"""
Restart script for Dockside Pro server
Safely stops existing processes and starts a fresh server instance
"""

import os
import sys
import subprocess
import signal
import time
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

def kill_existing_processes():
    """Kill any existing server processes"""
    print("🔍 Checking for existing server processes...")
    
    try:
        # Find processes running main_working_final.py
        result = subprocess.run(
            ["pgrep", "-f", "main_working_final.py"], 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            print(f"🛑 Found {len(pids)} existing server process(es)")
            
            for pid in pids:
                if pid.strip():
                    try:
                        print(f"   Killing process {pid}")
                        os.kill(int(pid), signal.SIGTERM)
                    except (ProcessLookupError, ValueError):
                        print(f"   Process {pid} already terminated")
            
            # Give processes time to shut down gracefully
            time.sleep(2)
            
            # Force kill any remaining processes
            result = subprocess.run(
                ["pgrep", "-f", "main_working_final.py"], 
                capture_output=True, 
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                remaining_pids = result.stdout.strip().split('\n')
                print(f"🔨 Force killing {len(remaining_pids)} stubborn process(es)")
                
                for pid in remaining_pids:
                    if pid.strip():
                        try:
                            os.kill(int(pid), signal.SIGKILL)
                            print(f"   Force killed process {pid}")
                        except (ProcessLookupError, ValueError):
                            pass
        else:
            print("✅ No existing server processes found")
            
    except FileNotFoundError:
        # pgrep not available, try alternative method
        print("⚠️  pgrep not available, using alternative method...")
        try:
            result = subprocess.run(
                ["ps", "aux"], 
                capture_output=True, 
                text=True
            )
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                killed_any = False
                
                for line in lines:
                    if 'main_working_final.py' in line and 'grep' not in line:
                        parts = line.split()
                        if len(parts) > 1:
                            try:
                                pid = int(parts[1])
                                print(f"🛑 Killing process {pid}")
                                os.kill(pid, signal.SIGTERM)
                                killed_any = True
                            except (ValueError, ProcessLookupError):
                                pass
                
                if killed_any:
                    time.sleep(2)  # Give time for graceful shutdown
                else:
                    print("✅ No existing server processes found")
                    
        except Exception as e:
            print(f"⚠️  Could not check for existing processes: {e}")

def check_port_availability():
    """Check if port 8000 is available"""
    print("🔍 Checking port 8000 availability...")
    
    try:
        result = subprocess.run(
            ["netstat", "-tulpn"], 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            if ":8000 " in result.stdout:
                print("⚠️  Port 8000 is still in use")
                
                # Try to find what's using it
                lines = result.stdout.split('\n')
                for line in lines:
                    if ":8000 " in line:
                        print(f"   {line.strip()}")
                
                print("🔄 Waiting for port to be released...")
                time.sleep(3)
            else:
                print("✅ Port 8000 is available")
        
    except FileNotFoundError:
        print("⚠️  netstat not available, skipping port check")

def main():
    """Restart the Dockside Pro server"""
    print("🔄 Restarting Dockside Pro Server...")
    print("=" * 50)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Step 1: Kill existing processes
    kill_existing_processes()
    
    # Step 2: Check port availability
    check_port_availability()
    
    # Step 3: Find Python interpreter
    python_cmd = find_python()
    print(f"🐍 Using Python: {python_cmd}")
    
    # Step 4: Check virtual environment
    if not (hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)):
        print("⚠️  Virtual environment not activated.")
        print("💡 Run: source venv/bin/activate")
        print("💡 Or use: python3 quick_setup.py")
    
    # Step 5: Start the server
    try:
        print("\n🚀 Starting fresh FastAPI server on http://localhost:8000")
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
        subprocess.run([python_cmd, "main_working_final.py"], check=True)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Server failed to start: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Run setup first: python3 quick_setup.py")
        print("2. Check if all dependencies are installed")
        print("3. Activate virtual environment: source venv/bin/activate")
        print("4. Check logs for specific errors")
        return 1
    except FileNotFoundError:
        print(f"\n❌ Python interpreter not found: {python_cmd}")
        print("\n🔧 Try:")
        print("1. Install Python 3: apt update && apt install python3")
        print("2. Run setup: python3 quick_setup.py")
        return 1

if __name__ == "__main__":
    sys.exit(main())
