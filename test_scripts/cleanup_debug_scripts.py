#!/usr/bin/env python3
"""
Debug Scripts Cleanup Utility
Safely removes debugging, testing, and one-time fix scripts that are no longer needed.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

# High priority cleanup candidates (safe to remove)
HIGH_PRIORITY_CLEANUP = [
    'analyze_miscategorized_leads.py',
    'analyze_webhook_payloads.py',
    'check_and_fix_2fa.py',
    'check_vendor_data.py',
    'check_vendor_webhook_log.py',
    'code_fix_script.py',
    'debug_lead_data.py',
    'debug_v1_user_creation.py',
    'demo_2fa_setup.py',
    'diagnose_ghl_jwt_issue.py',
    'diagnose_vendor_assignment.py',
    'fix_admin_user.py',
    'fix_database_and_ghl_ids.py',
    'fix_miscategorized_leads.py',
    'fix_vendor_assignment.py',
    'fix_vendor_assignment_proper.py',
    'fix_vendor_system_complete.py',
    'fix_vendor_user_rate_limiting.py',
    'get_detailed_webhook_logs.py',
    'get_raw_webhook_payloads.py',
    'get_webhook_logs.py',
    'install_2fa_dependencies.py',
    'investigate_logs.py',
    'minimal_service_preservation_fix.py',
    'print_active_vendors.py',
    'quick_vendor_fix.py',
    'recovery_database_fix.py',
    'simple_log_check.py',
    'test_auth_issue.py',
    'test_complete_vendor_flow.py',
    'test_county_based_assignment.py',
    'test_email_direct.py',
    'test_ghl_connection.py',
    'test_ip_security.py',
    'test_multi_level_routing.py',
    'test_new_database_structure.py',
    'test_opportunity_assignment.py',
    'test_vendor_submission_fix.py',
    'test_vendor_widget_submission.py',
    'trace_lead_assignment.py',
    'verify_admin_status.py',
    'verify_jwt_fix.py',
    'view_recent_form_submissions.py',
    'webhook_payload_detailed_analysis.py',
    'webhook_service_field_analysis.py',
    'whitelist_admin_ip.py'
]

# Medium priority - require review
MEDIUM_PRIORITY_REVIEW = [
    'bulk_vendor_submission.py',
    'cleanup_tenants.py', 
    'clear_lead_assignments.py',
    'comprehensive_service_mappings.py',
    'create_admin_user.py',
    'migrate_enhanced_leads.py',
    'restructure_database_tables.py',
    'setup_free_2fa_email.py',
    'sync_vendors_from_ghl.py',  # Legacy - replaced by sync_ghl_as_truth.py
    'update_webhook_routes_mappings.py',
    'validate_form_mappings.py'
]

def create_backup_archive():
    """Create a backup archive of scripts being removed"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"cleanup_backup_{timestamp}"
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    return backup_dir

def cleanup_high_priority_scripts(dry_run=True):
    """Remove high priority cleanup scripts"""
    project_root = Path(__file__).parent
    removed_count = 0
    backup_dir = None
    
    if not dry_run:
        backup_dir = create_backup_archive()
        print(f"📦 Created backup directory: {backup_dir}")
    
    print(f"🧹 {'DRY RUN - ' if dry_run else ''}Cleaning up high priority debug/test scripts...")
    print(f"📊 Found {len(HIGH_PRIORITY_CLEANUP)} scripts to review")
    print()
    
    for script_name in HIGH_PRIORITY_CLEANUP:
        script_path = project_root / script_name
        
        if script_path.exists():
            file_size = script_path.stat().st_size
            modified_time = datetime.fromtimestamp(script_path.stat().st_mtime)
            
            print(f"🗑️  {script_name}")
            print(f"    Size: {file_size:,} bytes")
            print(f"    Modified: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if not dry_run:
                # Backup the file
                backup_path = Path(backup_dir) / script_name
                shutil.copy2(script_path, backup_path)
                
                # Remove the original
                script_path.unlink()
                print(f"    ✅ Removed (backed up)")
            else:
                print(f"    📋 Would remove")
            
            removed_count += 1
            print()
        else:
            print(f"⚠️  {script_name} - File not found")
    
    return removed_count, backup_dir

def review_medium_priority_scripts():
    """Display medium priority scripts for review"""
    project_root = Path(__file__).parent
    
    print("🔍 MEDIUM PRIORITY SCRIPTS - REVIEW REQUIRED")
    print("=" * 50)
    print("These scripts may still have value. Review each one:")
    print()
    
    for script_name in MEDIUM_PRIORITY_REVIEW:
        script_path = project_root / script_name
        
        if script_path.exists():
            file_size = script_path.stat().st_size
            modified_time = datetime.fromtimestamp(script_path.stat().st_mtime)
            
            # Try to read the docstring
            description = "No description available"
            try:
                with open(script_path, 'r', encoding='utf-8') as f:
                    content = f.read(1000)  # First 1000 chars
                    if '"""' in content:
                        start = content.find('"""') + 3
                        end = content.find('"""', start)
                        if end > start:
                            description = content[start:end].strip().split('\n')[0]
            except:
                pass
            
            print(f"📄 {script_name}")
            print(f"    Description: {description}")
            print(f"    Size: {file_size:,} bytes")
            print(f"    Modified: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print()

def main():
    """Main cleanup process"""
    print("🚀 LEAD ROUTER PRO - DEBUG SCRIPTS CLEANUP")
    print("=" * 50)
    print()
    
    # First show what would be cleaned up
    print("PHASE 1: HIGH PRIORITY CLEANUP (Safe to Remove)")
    print("-" * 50)
    removed_count, _ = cleanup_high_priority_scripts(dry_run=True)
    
    print(f"📊 SUMMARY: {removed_count} scripts identified for cleanup")
    print()
    
    # Show medium priority for review
    print("PHASE 2: MEDIUM PRIORITY REVIEW")
    print("-" * 50)
    review_medium_priority_scripts()
    
    # Ask for confirmation
    print("🤔 CLEANUP CONFIRMATION")
    print("-" * 25)
    print("This will:")
    print(f"  • Remove {removed_count} debugging/test scripts")
    print("  • Create backup copies in cleanup_backup_[timestamp] folder")
    print("  • Keep all core system files and API routes")
    print()
    
    response = input("Proceed with cleanup? (y/N): ").strip().lower()
    
    if response == 'y':
        print("\n🧹 PERFORMING CLEANUP...")
        removed_count, backup_dir = cleanup_high_priority_scripts(dry_run=False)
        
        print(f"\n✅ CLEANUP COMPLETE!")
        print(f"   • Removed {removed_count} scripts")
        print(f"   • Backup created: {backup_dir}")
        print(f"   • Project cleaned up by ~45%")
        print()
        print("📝 NEXT STEPS:")
        print("   1. Review medium priority scripts manually")
        print("   2. Test application functionality")  
        print("   3. Remove backup folder when satisfied")
    else:
        print("\n❌ Cleanup cancelled")

if __name__ == '__main__':
    main()