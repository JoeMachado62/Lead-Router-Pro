#!/usr/bin/env python3
"""
Vendor Assignment Diagnostic Tool
Systematically checks why leads are not being assigned to vendors
"""

import sys
import os
import json
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.simple_connection import db as simple_db_instance
from api.services.lead_routing_service import lead_routing_service
from api.services.location_service import location_service
from config import AppConfig

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'-'*40}")
    print(f" {title}")
    print(f"{'-'*40}")

def check_database_status():
    """Check basic database connectivity and stats"""
    print_header("DATABASE STATUS CHECK")
    
    try:
        stats = simple_db_instance.get_stats()
        print(f"✅ Database connection: OK")
        print(f"📊 Accounts: {stats.get('accounts', 0)}")
        print(f"📊 Vendors: {stats.get('vendors', 0)}")
        print(f"📊 Leads: {stats.get('leads', 0)}")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def check_account_configuration():
    """Check account configuration and settings"""
    print_header("ACCOUNT CONFIGURATION CHECK")
    
    try:
        # Get account by GHL Location ID
        account = simple_db_instance.get_account_by_ghl_location_id(AppConfig.GHL_LOCATION_ID)
        
        if not account:
            print(f"❌ No account found for GHL Location ID: {AppConfig.GHL_LOCATION_ID}")
            
            # Try to create account
            print("🔄 Attempting to create account...")
            account_id = simple_db_instance.create_account(
                company_name="Digital Marine LLC",
                industry="marine",
                ghl_location_id=AppConfig.GHL_LOCATION_ID,
                ghl_private_token=AppConfig.GHL_PRIVATE_TOKEN
            )
            print(f"✅ Created account: {account_id}")
            account = simple_db_instance.get_account_by_id(account_id)
        else:
            print(f"✅ Account found: {account['id']}")
            print(f"   Company: {account['company_name']}")
            print(f"   Industry: {account['industry']}")
            print(f"   GHL Location ID: {account['ghl_location_id']}")
        
        # Check routing configuration
        routing_config = lead_routing_service._get_routing_configuration(account['id'])
        print(f"🎯 Routing Configuration:")
        print(f"   Performance-based: {routing_config.get('performance_percentage', 0)}%")
        print(f"   Round-robin: {routing_config.get('round_robin_percentage', 100)}%")
        
        return account
        
    except Exception as e:
        print(f"❌ Account configuration check failed: {e}")
        return None

def check_vendor_status(account_id):
    """Check vendor status and configuration"""
    print_header("VENDOR STATUS CHECK")
    
    try:
        vendors = simple_db_instance.get_vendors(account_id=account_id)
        
        if not vendors:
            print("❌ No vendors found in database")
            return []
        
        print(f"📊 Total vendors: {len(vendors)}")
        
        active_vendors = []
        taking_work_vendors = []
        
        for vendor in vendors:
            status = vendor.get('status', 'unknown')
            taking_work = vendor.get('taking_new_work', False)
            
            print(f"\n👤 Vendor: {vendor.get('name', 'Unknown')}")
            print(f"   ID: {vendor.get('id')}")
            print(f"   Company: {vendor.get('company_name', 'N/A')}")
            print(f"   Email: {vendor.get('email', 'N/A')}")
            print(f"   Status: {status}")
            print(f"   Taking new work: {taking_work}")
            print(f"   Coverage type: {vendor.get('service_coverage_type', 'zip')}")
            
            # Check services
            services = vendor.get('services_provided', [])
            if isinstance(services, str):
                try:
                    services = json.loads(services)
                except:
                    services = [s.strip() for s in services.split(',')]
            print(f"   Services: {services}")
            
            # Check service areas
            areas = vendor.get('service_areas', [])
            if isinstance(areas, str):
                try:
                    areas = json.loads(areas)
                except:
                    areas = [a.strip() for a in areas.split(',')]
            print(f"   Service areas: {areas}")
            
            # Check states/counties for enhanced coverage
            states = vendor.get('service_states', [])
            counties = vendor.get('service_counties', [])
            if isinstance(states, str):
                try:
                    states = json.loads(states)
                except:
                    states = []
            if isinstance(counties, str):
                try:
                    counties = json.loads(counties)
                except:
                    counties = []
            
            if states:
                print(f"   Service states: {states}")
            if counties:
                print(f"   Service counties: {counties}")
            
            print(f"   Last assigned: {vendor.get('last_lead_assigned', 'Never')}")
            print(f"   Close percentage: {vendor.get('lead_close_percentage', 0)}%")
            
            if status == 'active':
                active_vendors.append(vendor)
                if taking_work:
                    taking_work_vendors.append(vendor)
        
        print(f"\n📈 Summary:")
        print(f"   Active vendors: {len(active_vendors)}")
        print(f"   Taking new work: {len(taking_work_vendors)}")
        
        if len(taking_work_vendors) == 0:
            print("⚠️  WARNING: No vendors are currently taking new work!")
        
        return taking_work_vendors
        
    except Exception as e:
        print(f"❌ Vendor status check failed: {e}")
        return []

def check_recent_leads(account_id, limit=10):
    """Check recent leads and their assignment status"""
    print_header("RECENT LEADS CHECK")
    
    try:
        leads = simple_db_instance.get_leads(account_id=account_id)
        
        if not leads:
            print("❌ No leads found in database")
            return []
        
        # Sort by created_at (most recent first)
        leads.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        recent_leads = leads[:limit]
        
        print(f"📊 Total leads: {len(leads)}")
        print(f"📊 Showing {len(recent_leads)} most recent leads:")
        
        unassigned_leads = []
        
        for i, lead in enumerate(recent_leads, 1):
            print(f"\n🎯 Lead #{i}: {lead.get('id')}")
            print(f"   Customer: {lead.get('customer_name', 'Unknown')}")
            print(f"   Email: {lead.get('customer_email', 'N/A')}")
            print(f"   Phone: {lead.get('customer_phone', 'N/A')}")
            print(f"   Service: {lead.get('service_category', 'Unknown')}")
            print(f"   Status: {lead.get('status', 'unknown')}")
            print(f"   Vendor ID: {lead.get('vendor_id', 'UNASSIGNED')}")
            print(f"   Created: {lead.get('created_at', 'Unknown')}")
            
            # Check service details for location info
            service_details = lead.get('service_details', {})
            if isinstance(service_details, str):
                try:
                    service_details = json.loads(service_details)
                except:
                    service_details = {}
            
            location_info = service_details.get('location', {})
            zip_code = location_info.get('zip_code', 'Unknown')
            print(f"   Location: {zip_code}")
            
            if not lead.get('vendor_id'):
                unassigned_leads.append(lead)
        
        print(f"\n📈 Summary:")
        print(f"   Total leads: {len(leads)}")
        print(f"   Unassigned leads: {len(unassigned_leads)}")
        print(f"   Assignment rate: {((len(leads) - len(unassigned_leads)) / len(leads) * 100):.1f}%" if leads else "0%")
        
        return unassigned_leads
        
    except Exception as e:
        print(f"❌ Recent leads check failed: {e}")
        return []

def test_vendor_matching(account_id, unassigned_leads, available_vendors):
    """Test vendor matching logic with real unassigned leads"""
    print_header("VENDOR MATCHING TEST")
    
    if not unassigned_leads:
        print("✅ No unassigned leads to test")
        return
    
    if not available_vendors:
        print("❌ No available vendors to test matching against")
        return
    
    print(f"🧪 Testing vendor matching for {len(unassigned_leads)} unassigned leads")
    print(f"🧪 Against {len(available_vendors)} available vendors")
    
    for i, lead in enumerate(unassigned_leads[:5], 1):  # Test first 5 leads
        print(f"\n🎯 Testing Lead #{i}: {lead.get('id')}")
        
        service_category = lead.get('service_category', 'Unknown')
        service_details = lead.get('service_details', {})
        if isinstance(service_details, str):
            try:
                service_details = json.loads(service_details)
            except:
                service_details = {}
        
        location_info = service_details.get('location', {})
        zip_code = location_info.get('zip_code', '')
        
        print(f"   Service: {service_category}")
        print(f"   ZIP Code: {zip_code}")
        
        # Test the actual matching logic
        try:
            matching_vendors = lead_routing_service.find_matching_vendors(
                account_id=account_id,
                service_category=service_category,
                zip_code=zip_code,
                priority="normal"
            )
            
            print(f"   🔍 Matching vendors found: {len(matching_vendors)}")
            
            if matching_vendors:
                for j, vendor in enumerate(matching_vendors, 1):
                    print(f"     {j}. {vendor.get('name')} - {vendor.get('coverage_match_reason', 'Unknown reason')}")
                
                # Test vendor selection
                selected_vendor = lead_routing_service.select_vendor_from_pool(matching_vendors, account_id)
                if selected_vendor:
                    print(f"   ✅ Selected vendor: {selected_vendor.get('name')}")
                else:
                    print(f"   ❌ Vendor selection failed")
            else:
                print(f"   ❌ No matching vendors found")
                
                # Debug why no vendors match
                print(f"   🔍 Debugging vendor matching:")
                for vendor in available_vendors:
                    print(f"     Testing vendor: {vendor.get('name')}")
                    
                    # Test service matching
                    service_match = lead_routing_service._vendor_matches_service(vendor, service_category)
                    print(f"       Service match: {service_match}")
                    
                    # Test location matching
                    if zip_code:
                        location_data = location_service.zip_to_location(zip_code)
                        target_state = location_data.get('state') if not location_data.get('error') else None
                        target_county = location_data.get('county') if not location_data.get('error') else None
                        
                        location_match = lead_routing_service._vendor_covers_location(
                            vendor, zip_code, target_state, target_county
                        )
                        print(f"       Location match: {location_match}")
                        
                        if location_data.get('error'):
                            print(f"       ZIP resolution error: {location_data['error']}")
                    else:
                        print(f"       No ZIP code to test location matching")
                
        except Exception as e:
            print(f"   ❌ Matching test failed: {e}")

def test_location_service():
    """Test the location service functionality"""
    print_header("LOCATION SERVICE TEST")
    
    test_zip_codes = ["33101", "90210", "10001", "60601", "30301"]
    
    print(f"🧪 Testing location service with sample ZIP codes")
    
    for zip_code in test_zip_codes:
        try:
            location_data = location_service.zip_to_location(zip_code)
            
            if location_data.get('error'):
                print(f"❌ {zip_code}: {location_data['error']}")
            else:
                print(f"✅ {zip_code}: {location_data.get('city', 'Unknown')}, {location_data.get('state', 'Unknown')} - {location_data.get('county', 'Unknown')} County")
        except Exception as e:
            print(f"❌ {zip_code}: Exception - {e}")

def check_activity_logs():
    """Check recent activity logs for assignment errors"""
    print_header("ACTIVITY LOGS CHECK")
    
    try:
        conn = simple_db_instance._get_conn()
        cursor = conn.cursor()
        
        # Get recent activity logs related to lead routing
        cursor.execute("""
            SELECT event_type, event_data_json, success, error_message, timestamp
            FROM activity_log 
            WHERE event_type LIKE '%lead%' OR event_type LIKE '%routing%' OR event_type LIKE '%vendor%'
            ORDER BY timestamp DESC 
            LIMIT 20
        """)
        
        logs = cursor.fetchall()
        conn.close()
        
        if not logs:
            print("📝 No relevant activity logs found")
            return
        
        print(f"📝 Recent activity logs ({len(logs)} entries):")
        
        for log in logs:
            event_type, event_data_json, success, error_message, timestamp = log
            
            status = "✅" if success else "❌"
            print(f"\n{status} {timestamp} - {event_type}")
            
            if event_data_json:
                try:
                    event_data = json.loads(event_data_json)
                    if 'form_identifier' in event_data:
                        print(f"   Form: {event_data['form_identifier']}")
                    if 'service_category' in event_data:
                        print(f"   Service: {event_data['service_category']}")
                    if 'ghl_contact_id' in event_data:
                        print(f"   Contact: {event_data['ghl_contact_id']}")
                except:
                    pass
            
            if error_message:
                print(f"   Error: {error_message}")
                
    except Exception as e:
        print(f"❌ Activity logs check failed: {e}")

def main():
    """Main diagnostic function"""
    print_header("VENDOR ASSIGNMENT DIAGNOSTIC TOOL")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"GHL Location ID: {AppConfig.GHL_LOCATION_ID}")
    
    # Step 1: Check database connectivity
    if not check_database_status():
        print("❌ Cannot proceed without database connectivity")
        return
    
    # Step 2: Check account configuration
    account = check_account_configuration()
    if not account:
        print("❌ Cannot proceed without valid account configuration")
        return
    
    account_id = account['id']
    
    # Step 3: Check vendor status
    available_vendors = check_vendor_status(account_id)
    
    # Step 4: Check recent leads
    unassigned_leads = check_recent_leads(account_id)
    
    # Step 5: Test vendor matching logic
    test_vendor_matching(account_id, unassigned_leads, available_vendors)
    
    # Step 6: Test location service
    test_location_service()
    
    # Step 7: Check activity logs
    check_activity_logs()
    
    # Summary and recommendations
    print_header("DIAGNOSTIC SUMMARY")
    
    if not available_vendors:
        print("🚨 CRITICAL ISSUE: No vendors are available to receive leads")
        print("   Recommendations:")
        print("   1. Check vendor status - ensure vendors are marked as 'active'")
        print("   2. Check 'taking_new_work' flag - ensure vendors are accepting leads")
        print("   3. Add new vendors if none exist")
    elif unassigned_leads:
        print("⚠️  ASSIGNMENT ISSUE: Leads are not being assigned to available vendors")
        print("   Recommendations:")
        print("   1. Check service category matching between leads and vendors")
        print("   2. Check geographic coverage configuration")
        print("   3. Review location service functionality")
        print("   4. Check activity logs for specific error messages")
    else:
        print("✅ No obvious issues found - all recent leads appear to be assigned")
    
    print(f"\n📊 Final Stats:")
    print(f"   Available vendors: {len(available_vendors)}")
    print(f"   Unassigned leads: {len(unassigned_leads)}")

if __name__ == "__main__":
    main()
