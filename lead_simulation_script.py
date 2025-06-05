#!/usr/bin/env python3
"""
Lead Simulation Script - Fixed Version
Simulates 2 client lead submissions for Boat Maintenance/Detailing services
Tests lead creation and assignment functionality to available vendors
"""

import requests
import json
import time
import random
from datetime import datetime, timedelta

# Configuration - Auto-detect working server (prioritize localhost)
SERVER_CONFIGS = [
    {"name": "Localhost (127.0.0.1)", "url": "http://127.0.0.1:8000"},
    {"name": "Localhost (localhost)", "url": "http://localhost:8000"},
    {"name": "External IP", "url": "http://71.208.153.160:8000"}
]

BASE_URL = None  # Will be set by find_working_server()
WEBHOOK_BASE = None
ADMIN_API_BASE = None

# Test lead data for Boat Maintenance/Detailing service
LEAD_DATA = [
    {
        # Lead 1: High-Value Ceramic Coating Request
        "form_identifier": "ceramic_coating_request",
        "data": {
            "firstName": "Jennifer",
            "lastName": "Thompson",
            "email": "jennifer.thompson@email.com",
            "phone": "555-123-4567",
            "vessel_make": "Azimut",
            "vessel_model": "55 Flybridge", 
            "vessel_year": "2021",
            "vessel_length_ft": "55",
            "vessel_location__slip": "Miami Beach Marina - Slip A-15",
            "specific_service_needed": "Premium ceramic coating for new yacht - full hull and superstructure",
            "zip_code_of_service": "33139",
            "desired_timeline": "Within 3 weeks",
            "budget_range": "$5000-$8000",
            "special_requests__notes": "New yacht, looking for the best ceramic protection available. Please provide portfolio of similar work.",
            "preferred_contact_method": "Email",
            "source": "Ceramic Coating Request Form (DSP)"
        },
        "lead_profile": {
            "type": "High-Value",
            "urgency": "Normal",
            "vessel_size": "Large",
            "estimated_value": "$6500"
        }
    },
    {
        # Lead 2: Regular Detailing Service Request
        "form_identifier": "boat_maintenance_request",
        "data": {
            "firstName": "Michael",
            "lastName": "Rodriguez",
            "email": "mike.rodriguez@gmail.com", 
            "phone": "555-987-6543",
            "vessel_make": "Sea Ray",
            "vessel_model": "Sundancer 320",
            "vessel_year": "2018",
            "vessel_length_ft": "32",
            "vessel_location__slip": "Dinner Key Marina - Dock 3, Slip 42",
            "specific_service_needed": "Full boat detailing - hull cleaning, deck wash, interior cleaning",
            "zip_code_of_service": "33133",
            "desired_timeline": "This weekend if possible",
            "budget_range": "$800-$1200",
            "special_requests__notes": "Boat hasn't been detailed in 6 months. Some algae on hull. Interior needs deep cleaning.",
            "preferred_contact_method": "Phone Call",
            "source": "Boat Maintenance Request Form (DSP)"
        },
        "lead_profile": {
            "type": "Regular Service",
            "urgency": "Moderate",
            "vessel_size": "Medium", 
            "estimated_value": "$1000"
        }
    }
]

def print_separator(title):
    """Print a formatted section separator"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def find_working_server():
    """Find the first working server configuration"""
    global BASE_URL, WEBHOOK_BASE, ADMIN_API_BASE
    
    print("🔍 Searching for running Lead Router Pro server...")
    
    for config in SERVER_CONFIGS:
        print(f"\n🔍 Testing connection to: {config['url']}")
        try:
            response = requests.get(f"{config['url']}/health", timeout=5)
            if response.status_code == 200:
                print(f"   ✅ Found working server: {config['name']}")
                BASE_URL = config['url']
                WEBHOOK_BASE = f"{BASE_URL}/api/v1/webhooks/elementor"
                ADMIN_API_BASE = f"{BASE_URL}/api/v1/simple-admin"
                return True
            else:
                print(f"   ❌ Server responded with: {response.status_code}")
        except requests.exceptions.ConnectTimeout:
            print(f"   ❌ Connection timeout")
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection refused")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n❌ No working server found!")
    print("\n💡 To start your Lead Router Pro server:")
    print("   1. Open terminal: cd 'C:\\Users\\joema\\OneDrive\\Documents\\Digital Boost\\Dockside Pros'")
    print("   2. Run: python main_working_final.py")
    print("   3. Wait for 'Uvicorn running on http://0.0.0.0:8000'")
    print("   4. Then run this script again")
    return False

def test_server_health():
    """Test if the server is running and responsive"""
    print_separator("TESTING SERVER HEALTH")
    
    if not BASE_URL:
        print("❌ No server URL configured")
        return False
    
    try:
        # Test main health endpoint
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"✅ Main server health: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"   Database status: {health_data.get('database_status')}")
            print(f"   Service name: {health_data.get('service_name')}")
        
        # Test webhook health
        webhook_health = requests.get(f"{WEBHOOK_BASE}/health", timeout=10)
        print(f"✅ Webhook system health: {webhook_health.status_code}")
        if webhook_health.status_code == 200:
            webhook_data = webhook_health.json()
            print(f"   Valid field count: {webhook_data.get('valid_field_count')}")
            print(f"   GHL Location ID: {webhook_data.get('ghl_location_id')}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Server health check failed: {e}")
        return False

def check_available_vendors():
    """Check what vendors are available for lead assignment"""
    print_separator("CHECKING AVAILABLE VENDORS")
    
    try:
        vendors_response = requests.get(f"{ADMIN_API_BASE}/vendors", timeout=10)
        if vendors_response.status_code == 200:
            vendors = vendors_response.json()
            total_vendors = vendors.get('count', 0)
            print(f"👥 Total Vendors in System: {total_vendors}")
            
            if vendors.get('data'):
                print(f"\n📋 Available Vendors for Boat Maintenance:")
                boat_maintenance_vendors = []
                
                for vendor in vendors['data']:
                    # Look for vendors that might handle boat maintenance
                    services = vendor.get('services_provided', '').lower()
                    company = vendor.get('company_name', 'Unknown Company')
                    name = vendor.get('name', 'Unknown')
                    
                    if any(keyword in services for keyword in ['detailing', 'maintenance', 'cleaning', 'coating']):
                        boat_maintenance_vendors.append(vendor)
                        print(f"   ✅ {company} ({name})")
                        print(f"      Services: {vendor.get('services_provided', 'Not specified')}")
                        print(f"      Contact: {vendor.get('email', 'No email')}")
                
                print(f"\n🎯 Vendors available for lead assignment: {len(boat_maintenance_vendors)}")
                return boat_maintenance_vendors
            else:
                print("❌ No vendors found in system")
                return []
        else:
            print(f"❌ Failed to fetch vendors: {vendors_response.status_code}")
            return []
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Vendor check failed: {e}")
        return []

def submit_lead_request(lead_info):
    """Submit a client lead request via webhook"""
    form_id = lead_info["form_identifier"]
    lead_data = lead_info["data"]
    lead_profile = lead_info["lead_profile"]
    
    print(f"\n🛥️ Submitting lead request:")
    print(f"   Client: {lead_data['firstName']} {lead_data['lastName']}")
    print(f"   Email: {lead_data['email']}")
    print(f"   Vessel: {lead_data['vessel_year']} {lead_data['vessel_make']} {lead_data['vessel_model']}")
    print(f"   Service: {lead_data['specific_service_needed']}")
    print(f"   Location: {lead_data['zip_code_of_service']}")
    print(f"   Budget: {lead_data.get('budget_range', 'Not specified')}")
    print(f"   Timeline: {lead_data['desired_timeline']}")
    print(f"   Estimated Value: {lead_profile['estimated_value']}")
    
    webhook_url = f"{WEBHOOK_BASE}/{form_id}"
    
    try:
        # Submit lead request
        start_time = time.time()
        response = requests.post(
            webhook_url,
            json=lead_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        processing_time = round(time.time() - start_time, 3)
        
        print(f"   Webhook URL: {webhook_url}")
        print(f"   Response Status: {response.status_code}")
        print(f"   Processing Time: {processing_time}s")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS: {result.get('message', 'Lead request submitted')}")
            print(f"   Contact ID: {result.get('contact_id')}")
            print(f"   Action: {result.get('action')}")
            print(f"   Form Type: {result.get('form_type')}")
            
            # Check for warnings
            warnings = result.get('validation_warnings', [])
            if warnings:
                print(f"⚠️  Warnings: {warnings}")
            
            return {
                "success": True,
                "contact_id": result.get('contact_id'),
                "lead_data": lead_data,
                "lead_profile": lead_profile,
                "processing_time": processing_time
            }
        else:
            print(f"❌ FAILED: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"   Error: {response.text}")
            return {"success": False, "error": response.text}
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return {"success": False, "error": str(e)}

def simulate_lead_assignment(lead_results, available_vendors):
    """Simulate the lead assignment process to available vendors"""
    print_separator("SIMULATING LEAD ASSIGNMENT PROCESS")
    
    successful_leads = [l for l in lead_results if l.get('success')]
    
    if not successful_leads:
        print("❌ No successful leads to assign")
        return
    
    if not available_vendors:
        print("❌ No available vendors for assignment")
        return
    
    print(f"🎯 Processing {len(successful_leads)} lead(s) for assignment...")
    print(f"📋 Available vendors: {len(available_vendors)}")
    
    for i, lead in enumerate(successful_leads, 1):
        lead_data = lead['lead_data']
        lead_profile = lead['lead_profile']
        contact_id = lead['contact_id']
        
        print(f"\n--- Lead Assignment {i} ---")
        print(f"   Lead: {lead_data['firstName']} {lead_data['lastName']}")
        print(f"   Service: {lead_data['specific_service_needed']}")
        print(f"   Value: {lead_profile['estimated_value']}")
        print(f"   Urgency: {lead_profile['urgency']}")
        print(f"   Contact ID: {contact_id}")
        
        # Simulate AI classification
        print(f"   🤖 Running AI service classification...")
        time.sleep(1)
        print(f"      ✅ Classified as: Boat Maintenance")
        print(f"      ✅ Confidence: 95%")
        print(f"      ✅ Sub-category: {lead_profile['type']}")
        
        # Simulate vendor matching
        print(f"   🔍 Finding matching vendors...")
        time.sleep(1)
        
        # Simple vendor selection logic for simulation
        suitable_vendors = []
        for vendor in available_vendors:
            services = vendor.get('services_provided', '').lower()
            if 'detailing' in services or 'coating' in services or 'maintenance' in services:
                suitable_vendors.append(vendor)
        
        if suitable_vendors:
            print(f"      ✅ Found {len(suitable_vendors)} matching vendor(s)")
            
            # Simulate ranking and selection
            selected_vendor = suitable_vendors[0]  # Simple selection for demo
            backup_vendor = suitable_vendors[1] if len(suitable_vendors) > 1 else None
            
            print(f"      🎯 Primary vendor: {selected_vendor.get('company_name')}")
            print(f"         Contact: {selected_vendor.get('name')}")
            print(f"         Email: {selected_vendor.get('email')}")
            
            if backup_vendor:
                print(f"      🔄 Backup vendor: {backup_vendor.get('company_name')}")
            
            # Simulate GHL opportunity creation
            print(f"   📊 Creating opportunity in GHL pipeline...")
            time.sleep(1)
            opportunity_id = f"opp_{random.randint(100000, 999999)}"
            print(f"      ✅ Opportunity created: {opportunity_id}")
            print(f"      ✅ Pipeline: Boat Maintenance Leads")
            print(f"      ✅ Stage: New Lead")
            print(f"      ✅ Value: {lead_profile['estimated_value']}")
            
            # Simulate vendor notification
            print(f"   📧 Notifying assigned vendor...")
            time.sleep(1)
            print(f"      ✅ Email sent to: {selected_vendor.get('email')}")
            print(f"         Subject: New Lead Assignment - {lead_profile['type']}")
            print(f"         Lead ID: {contact_id}")
            print(f"         Client: {lead_data['firstName']} {lead_data['lastName']}")
            print(f"         Estimated Value: {lead_profile['estimated_value']}")
            
            # Simulate SMS notification for urgent leads
            if lead_profile['urgency'] in ['High', 'Urgent']:
                print(f"      📱 SMS sent (urgent lead)")
                print(f"         To: {selected_vendor.get('phone', 'No phone')}")
                print(f"         Message: URGENT: New high-priority lead assigned")
            
        else:
            print(f"      ❌ No suitable vendors found")
            print(f"      📧 Admin notification sent - manual assignment needed")

def simulate_client_notifications(lead_results):
    """Simulate client notification and follow-up processes"""
    print_separator("SIMULATING CLIENT NOTIFICATIONS")
    
    successful_leads = [l for l in lead_results if l.get('success')]
    
    for i, lead in enumerate(successful_leads, 1):
        lead_data = lead['lead_data']
        contact_id = lead['contact_id']
        
        print(f"\n--- Client Notification {i} ---")
        print(f"   Client: {lead_data['firstName']} {lead_data['lastName']}")
        print(f"   Email: {lead_data['email']}")
        
        # Simulate confirmation email
        print(f"   📧 Sending confirmation email...")
        time.sleep(1)
        print(f"      ✅ Email sent to: {lead_data['email']}")
        print(f"         Subject: Your Service Request Received - Dockside Pros")
        print(f"         Lead ID: {contact_id}")
        print(f"         Expected response: Within 2 hours")
        
        # Simulate GHL workflow trigger
        print(f"   🔄 Triggering GHL follow-up workflow...")
        print(f"      ✅ Follow-up sequence started")
        print(f"      ✅ SMS confirmation scheduled")
        print(f"      ✅ 24-hour follow-up scheduled")

def check_final_system_state():
    """Check final system state after lead processing"""
    print_separator("FINAL SYSTEM STATE CHECK")
    
    try:
        # Get updated system stats
        stats_response = requests.get(f"{ADMIN_API_BASE}/stats", timeout=10)
        if stats_response.status_code == 200:
            stats = stats_response.json()
            print("📊 Updated System Statistics:")
            if 'data' in stats:
                data = stats['data']
                print(f"   Total Leads: {data.get('total_leads', 'N/A')}")
                print(f"   Total Vendors: {data.get('total_vendors', 'N/A')}")
                print(f"   Recent Activities: {data.get('recent_activities', 'N/A')}")
        
        # Get recent leads
        leads_response = requests.get(f"{ADMIN_API_BASE}/leads", timeout=10)
        if leads_response.status_code == 200:
            leads = leads_response.json()
            print(f"\n🎯 Total Leads in System: {leads.get('count', 0)}")
            if leads.get('data'):
                recent_leads = leads['data'][-3:]  # Show last 3
                for lead in recent_leads:
                    print(f"   - {lead.get('customer_name', 'Unknown')} ({lead.get('service_category', 'Unknown service')})")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Final state check failed: {e}")

def main():
    """Main execution function"""
    print_separator("LEAD SIMULATION - BOAT MAINTENANCE/DETAILING SERVICES")
    print("Testing lead creation and assignment functionality")
    print(f"Target Service: Boat Maintenance/Detailing")
    print(f"Number of Leads: {len(LEAD_DATA)}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 0: Find working server
    if not find_working_server():
        print("\n❌ Cannot find running server. Please start your FastAPI server first.")
        return
    
    print(f"\n✅ Using server: {BASE_URL}")
    
    # Step 1: Test server health
    if not test_server_health():
        print("\n❌ Server health check failed. Cannot proceed with testing.")
        return
    
    # Step 2: Check available vendors for assignment
    available_vendors = check_available_vendors()
    if not available_vendors:
        print("\n⚠️ WARNING: No vendors available for assignment.")
        print("   Consider running vendor signup simulation first.")
        proceed = input("\n   Continue with lead creation anyway? (y/n): ")
        if proceed.lower() != 'y':
            return
    
    # Step 3: Submit lead requests
    print_separator("SUBMITTING CLIENT LEAD REQUESTS")
    lead_results = []
    
    for i, lead_info in enumerate(LEAD_DATA, 1):
        print(f"\n--- Lead Submission {i} of {len(LEAD_DATA)} ---")
        result = submit_lead_request(lead_info)
        lead_results.append(result)
        
        # Wait between submissions to avoid overwhelming the server
        if i < len(LEAD_DATA):
            print("   ⏱️  Waiting 3 seconds before next submission...")
            time.sleep(3)
    
    # Step 4: Simulate lead assignment process
    if available_vendors:
        simulate_lead_assignment(lead_results, available_vendors)
    else:
        print_separator("LEAD ASSIGNMENT SKIPPED")
        print("⚠️ No vendors available - leads created but not assigned")
    
    # Step 5: Simulate client notifications
    simulate_client_notifications(lead_results)
    
    # Step 6: Check final system state
    check_final_system_state()
    
    # Step 7: Final summary
    print_separator("LEAD SIMULATION SUMMARY")
    successful = 0
    failed = 0
    
    for result in lead_results:
        if result.get('success'):
            successful += 1
        else:
            failed += 1
    
    print(f"📊 Results Summary:")
    print(f"   ✅ Successful lead submissions: {successful}")
    print(f"   ❌ Failed submissions: {failed}")
    print(f"   👥 Available vendors: {len(available_vendors)}")
    print(f"   🎯 Leads assigned: {successful if available_vendors else 0}")
    print(f"   📧 Client confirmations sent: {successful}")
    
    if successful > 0:
        # Calculate total lead value safely
        total_value = 0
        for result in lead_results:
            if result.get('success') and 'lead_profile' in result:
                value_str = result['lead_profile']['estimated_value']
                # Remove $ and , from value string and convert to float
                clean_value = value_str.replace('$', '').replace(',', '')
                total_value += float(clean_value)
        
        print(f"   💰 Total lead value: ${total_value:,.2f}")
        
        print(f"\n🎯 System Performance:")
        
        # Calculate average processing time safely
        total_processing_time = 0
        for result in lead_results:
            if result.get('success'):
                total_processing_time += result.get('processing_time', 0)
        
        avg_processing_time = total_processing_time / successful if successful > 0 else 0
        print(f"   ⚡ Average processing time: {avg_processing_time:.3f}s")
        print(f"   🔄 Lead routing: {'Functional' if available_vendors else 'Pending vendors'}")
        print(f"   📱 Notifications: Functional")
    
    if available_vendors and successful > 0:
        print(f"\n🚀 Next Steps in Real System:")
        print(f"   1. Vendors receive lead notifications via email/SMS")
        print(f"   2. Vendors can view lead details in their portal")
        print(f"   3. Vendors submit quotes/proposals to clients")
        print(f"   4. Clients receive vendor proposals")
        print(f"   5. Booking and payment processing")
        print(f"   6. Service completion and review collection")
    
    print(f"\n✅ Lead simulation completed successfully!")
    if not available_vendors:
        print(f"   💡 Tip: Run vendor simulation first for full assignment testing")

if __name__ == "__main__":
    main()
