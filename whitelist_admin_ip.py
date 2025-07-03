#!/usr/bin/env python3
"""
Script to whitelist admin IP addresses to prevent rate limiting issues
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.security.ip_security import security_manager

def whitelist_ip(ip_address):
    """Add IP to whitelist"""
    print(f"Adding {ip_address} to whitelist...")
    security_manager.add_to_whitelist(ip_address)
    print(f"✅ Successfully whitelisted {ip_address}")

def main():
    # Your IP address from the logs
    admin_ip = "71.208.153.160"
    
    print("🔐 Admin IP Whitelisting Tool")
    print("=" * 40)
    
    # Add admin IP to whitelist
    whitelist_ip(admin_ip)
    
    # Also unblock if currently blocked
    if security_manager.unblock_ip(admin_ip):
        print(f"✅ Unblocked {admin_ip}")
    
    # Show current whitelist
    stats = security_manager.get_security_stats()
    print(f"\n📊 Security Stats:")
    print(f"   Whitelist size: {stats['whitelist_size']}")
    print(f"   Rate limit: {stats['max_requests_per_window']}/minute")
    print(f"   Currently blocked IPs: {stats['currently_blocked_ips']}")
    
    print("\n✅ Admin IP whitelisting complete!")

if __name__ == "__main__":
    main()
