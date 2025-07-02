#!/usr/bin/env python3
"""
Script to add IP address to whitelist using the admin API
"""

import requests
import json
import sys

def add_ip_to_whitelist(ip_address, server_url="http://localhost:8000"):
    """Add IP to whitelist using admin API"""
    
    endpoint = f"{server_url}/api/v1/admin/security/whitelist/add"
    
    payload = {
        "ip": ip_address,
        "reason": "Added via admin script - requested IP whitelist"
    }
    
    try:
        print(f"Adding IP {ip_address} to whitelist...")
        
        response = requests.post(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS: {result.get('message', 'IP added to whitelist')}")
            print(f"   IP: {result.get('ip')}")
            print(f"   Was previously blocked: {result.get('was_blocked', False)}")
            return True
        else:
            print(f"❌ ERROR: HTTP {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   Details: {error_detail}")
            except:
                print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ ERROR: Could not connect to server at {server_url}")
        print("   Make sure the Lead Router Pro server is running")
        return False
    except requests.exceptions.Timeout:
        print("❌ ERROR: Request timed out")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    # IP address to add
    ip_to_add = "34.174.132.172"
    
    print("Lead Router Pro - IP Whitelist Manager")
    print("=" * 40)
    
    success = add_ip_to_whitelist(ip_to_add)
    
    if success:
        print(f"\n🎉 IP {ip_to_add} has been successfully added to the whitelist!")
        print("   The IP should now be able to access Elementor webhook endpoints.")
    else:
        print(f"\n💥 Failed to add IP {ip_to_add} to whitelist.")
        print("   Please check that the server is running and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()
