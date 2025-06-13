#!/usr/bin/env python3
"""
Simple Port 8000 Monitor
Just monitors incoming connections and requests on port 8000
"""

import subprocess
import time
import re
from datetime import datetime

def monitor_port_8000():
    """Simple monitor for port 8000 activity"""
    print("🔍 Monitoring Port 8000 Activity...")
    print("📡 Watching for webhook requests...")
    print("⏹️  Press Ctrl+C to stop\n")
    
    last_connections = set()
    
    try:
        while True:
            # Get current connections
            try:
                result = subprocess.run(
                    ['netstat', '-an'], 
                    capture_output=True, 
                    text=True, 
                    shell=True
                )
                
                # Filter for port 8000
                lines = result.stdout.split('\n')
                port_8000_lines = [line for line in lines if ':8000' in line and 'TCP' in line]
                
                current_connections = set(port_8000_lines)
                
                # Check for new connections
                new_connections = current_connections - last_connections
                closed_connections = last_connections - current_connections
                
                timestamp = datetime.now().strftime('%H:%M:%S')
                
                # Show new connections (potential webhook requests)
                for conn in new_connections:
                    if 'ESTABLISHED' in conn or 'TIME_WAIT' in conn:
                        # Extract client IP
                        match = re.search(r'(\d+\.\d+\.\d+\.\d+):(\d+)', conn)
                        if match:
                            client_ip = match.group(1)
                            client_port = match.group(2)
                            if 'ESTABLISHED' in conn:
                                print(f"📥 {timestamp} | NEW REQUEST from {client_ip}:{client_port}")
                            elif 'TIME_WAIT' in conn:
                                print(f"📤 {timestamp} | REQUEST COMPLETED from {client_ip}:{client_port}")
                
                # Update tracking
                last_connections = current_connections
                
                # Show current status
                active_connections = len([line for line in port_8000_lines if 'ESTABLISHED' in line])
                if active_connections > 0:
                    print(f"\r🔄 {timestamp} | Active connections: {active_connections}", end='', flush=True)
                else:
                    print(f"\r⭐ {timestamp} | Waiting for requests...", end='', flush=True)
                
                time.sleep(1)
                
            except Exception as e:
                print(f"\n❌ Error monitoring: {e}")
                time.sleep(5)
                
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Monitoring stopped at {datetime.now().strftime('%H:%M:%S')}")

def simple_connection_count():
    """Just show current connection count"""
    try:
        result = subprocess.run(
            ['netstat', '-an'], 
            capture_output=True, 
            text=True, 
            shell=True
        )
        
        lines = result.stdout.split('\n')
        port_8000_lines = [line for line in lines if ':8000' in line and 'TCP' in line]
        
        print(f"📊 Port 8000 Status:")
        for line in port_8000_lines:
            if 'LISTENING' in line:
                print(f"   ✅ Server listening on port 8000")
            elif 'ESTABLISHED' in line:
                print(f"   🔄 Active connection: {line.strip()}")
            elif 'TIME_WAIT' in line:
                print(f"   ⏳ Closing connection: {line.strip()}")
        
        if not port_8000_lines:
            print(f"   ❌ No activity on port 8000")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("=" * 50)
    print("  SIMPLE PORT 8000 MONITOR")
    print("=" * 50)
    
    print("1. Monitor continuously")
    print("2. Show current status only")
    print("3. Show help")
    
    choice = input("\nChoice (1-3) or Enter for continuous: ").strip()
    
    if choice == "2":
        simple_connection_count()
    elif choice == "3":
        print("\n💡 Manual commands you can use:")
        print("   Windows: netstat -an | findstr :8000")
        print("   Check FastAPI: curl http://127.0.0.1:8000/health")
        print("   Monitor log: tail -f fastapi_events.log")
    else:
        monitor_port_8000()

if __name__ == "__main__":
    main()