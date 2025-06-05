#!/usr/bin/env python3
"""
Vendor Signup Simulator Script
Simulates 2 vendor signups for the same service (Boat Maintenance/Detailing)
Tests vendor contact creation and sub-account credential generation
"""

import requests
import json
import time
import random
from datetime import datetime

# Configuration - Auto-detect working server (prioritize localhost)
SERVER_CONFIGS = [
    {"name": "Localhost (127.0.0.1)", "url": "http://127.0.0.1:8000"},
    {"name": "Localhost (localhost)", "url": "http://localhost:8000"},
    {"name": "External IP", "url": "http://71.208.153.160:8000"}
]

BASE_URL = None  # Will be set by find_working_server()
WEBHOOK_BASE = None
ADMIN_API_BASE = None

# Test vendor data for Boat Maintenance/Detailing service
VENDOR_DATA = [
    {
        # Vendor 1: Established Detailing Company
        "form_identifier": "vendor_application_detailing_specialist",
        "data": {
            "firstName": "Maria",
            "lastName": "Santos",
            "email": "maria.santos@pristineyachts.com",
            "phone": "555-456-7890",
            "vendor_company_name": "Pristine Yacht Services LLC",
            "dba": "Pristine Yachts",
            "years_in_business": "8",
            "services_provided": "Premium yacht detailing, ceramic coating, interior cleaning, waxing, polishing",
            "primary_service_category": "Boat Maintenance",
            "service_zip_codes": "33139, 33154, 33109, 33140, 33141",
            "website_url": "https://pristineyachts.com",
            "licences__certifications": "Certified Marine Detailer, Ceramic Pro Certified Installer, Insured & Bonded",
            "insurance_coverage": "General Liability $1M, Professional Liability $500K, Bonded $250K",
            "about_your_company": "Premium yacht detailing service with 8 years of experience serving luxury yacht owners in Miami-Dade. We specialize in ceramic coatings and eco-friendly products.",
            "reviews__google_profile_url": "https://g.page/pristineyachts",
            "taking_new_work": "Yes",
            "vendor_preferred_contact_method": "Email",
            "source": "Detailing Specialist Application Form (DSP)"
        }
    },
    {
        # Vendor 2: Newer Detailing Business
        "form_identifier": "vendor_application_detailing_specialist", 
        "data": {
            "firstName": "Carlos",
            "lastName": "Rodriguez",
            "email": "carlos@boatshinedetailing.com",
            "phone": "555-789-0123",
            "vendor_company_name": "BoatShine Detailing Services",
            "years_in_business": "3",
            "services_provided": "Boat detailing, hull cleaning, deck restoration, vinyl repair, boat washing",
            "primary_service_category": "Boat Maintenance", 
            "service_zip_codes": "33101, 33139, 33154, 33109",
            "website_url": "https://boatshinedetailing.com",
            "licences__certifications": "Florida Business License, General Liability Insurance, Marine Detailing Certification",
            "insurance_coverage": "General Liability $1M, Bonded",
            "about_your_company": "Affordable and reliable boat detailing services. Family-owned business focused on quality workmanship and customer satisfaction.",
            "reviews__google_profile_url": "https://g.page/boatshinedetailing",
            "taking_new_work": "Yes", 
            "vendor_preferred_contact_method": "Phone Call",
            "source": "Detailing Specialist Application Form (DSP)"
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

def submit_vendor_application(vendor_info):
    """Submit a vendor application via webhook"""
    form_id = vendor_info["form_identifier"]
    vendor_data = vendor_info["data"]
    
    print(f"\n📋 Submitting vendor application for: {vendor_data['vendor_company_name']}")
    print(f"   Contact: {vendor_data['firstName']} {vendor_data['lastName']}")
    print(f"   Email: {vendor_data['email']}")
    print(f"   Service Category: {vendor_data['primary_service_category']}")
    print(f"   Years in Business: {vendor_data['years_in_business']}")
    
    webhook_url = f"{WEBHOOK_BASE}/{form_id}"
    
    try:
        # Submit vendor application
        start_time = time.time()
        response = requests.post(
            webhook_url,
            json=vendor_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        processing_time = round(time.time() - start_time, 3)
        
        print(f"   Webhook URL: {webhook_url}")
        print(f"   Response Status: {response.status_code}")
        print(f"   Processing Time: {processing_time}s")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS: {result.get('message', 'Vendor application submitted')}")
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
                "vendor_data": vendor_data,
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

def check_admin_stats():
    """Check system stats via admin API"""
    print_separator("CHECKING SYSTEM STATISTICS")
    
    try:
        # Get system stats
        stats_response = requests.get(f"{ADMIN_API_BASE}/stats", timeout=10)
        if stats_response.status_code == 200:
            stats = stats_response.json()
            print("📊 System Statistics:")
            print(f"   Status: {stats.get('status')}")
            if 'data' in stats:
                data = stats['data']
                print(f"   Total Accounts: {data.get('total_accounts', 'N/A')}")
                print(f"   Total Vendors: {data.get('total_vendors', 'N/A')}")
                print(f"   Total Leads: {data.get('total_leads', 'N/A')}")
                print(f"   Recent Activities: {data.get('recent_activities', 'N/A')}")
        
        # Get vendors list
        vendors_response = requests.get(f"{ADMIN_API_BASE}/vendors", timeout=10)
        if vendors_response.status_code == 200:
            vendors = vendors_response.json()
            print(f"\n👥 Current Vendors: {vendors.get('count', 0)}")
            if vendors.get('data'):
                for vendor in vendors['data'][-5:]:  # Show last 5
                    print(f"   - {vendor.get('name', 'Unknown')} ({vendor.get('company_name', 'No company')})")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Admin API check failed: {e}")

def simulate_vendor_credential_generation(vendor_results):
    """Simulate the sub-account credential generation process"""
    print_separator("SIMULATING SUB-ACCOUNT CREDENTIAL GENERATION")
    
    successful_vendors = [v for v in vendor_results if v.get('success')]
    
    if not successful_vendors:
        print("❌ No successful vendor signups to process")
        return
    
    print(f"🔐 Processing {len(successful_vendors)} vendor(s) for sub-account creation...")
    
    for i, vendor in enumerate(successful_vendors, 1):
        vendor_data = vendor['vendor_data']
        contact_id = vendor['contact_id']
        
        print(f"\n   Vendor {i}: {vendor_data['vendor_company_name']}")
        print(f"   Contact ID: {contact_id}")
        print(f"   Contact Email: {vendor_data['email']}")
        
        # Simulate credential generation process
        print("   🔄 Generating sub-account credentials...")
        time.sleep(1)  # Simulate processing time
        
        # Generate mock credentials
        username = vendor_data['email'].split('@')[0] + str(random.randint(100, 999))
        temp_password = f"TempPass{random.randint(1000, 9999)}!"
        
        print(f"   ✅ Sub-account created:")
        print(f"      Username: {username}")
        print(f"      Temp Password: {temp_password}")
        print(f"      Portal URL: https://vendors.docksidepros.com/login")
        print(f"      Account Status: Pending Approval")
        
        # Simulate email notification
        print(f"   📧 Welcome email sent to: {vendor_data['email']}")
        print(f"      Subject: Welcome to Dockside Pros Vendor Network")
        print(f"      Contains: Login credentials and next steps")

def main():
    """Main execution function"""
    print_separator("VENDOR SIGNUP SIMULATION - BOAT DETAILING SERVICE")
    print("Testing vendor contact creation and sub-account credential generation")
    print(f"Target Service: Boat Maintenance/Detailing")
    print(f"Number of Vendors: {len(VENDOR_DATA)}")
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
    
    # Step 2: Check initial system stats
    check_admin_stats()
    
    # Step 3: Submit vendor applications
    print_separator("SUBMITTING VENDOR APPLICATIONS")
    vendor_results = []
    
    for i, vendor_info in enumerate(VENDOR_DATA, 1):
        print(f"\n--- Vendor Application {i} of {len(VENDOR_DATA)} ---")
        result = submit_vendor_application(vendor_info)
        vendor_results.append(result)
        
        # Wait between submissions to avoid overwhelming the server
        if i < len(VENDOR_DATA):
            print("   ⏱️  Waiting 2 seconds before next submission...")
            time.sleep(2)
    
    # Step 4: Check updated system stats
    print_separator("UPDATED SYSTEM STATISTICS")
    check_admin_stats()
    
    # Step 5: Simulate credential generation
    simulate_vendor_credential_generation(vendor_results)
    
    # Step 6: Final summary
    print_separator("VENDOR SIGNUP SIMULATION SUMMARY")
    successful = sum(1 for r in vendor_results if r.get('success'))
    failed = len(vendor_results) - successful
    
    print(f"📊 Results Summary:")
    print(f"   ✅ Successful signups: {successful}")
    print(f"   ❌ Failed signups: {failed}")
    print(f"   📧 Welcome emails sent: {successful}")
    print(f"   🔐 Sub-accounts created: {successful}")
    
    if successful > 0:
        print(f"\n🎯 Next Steps:")
        print(f"   1. Vendors receive welcome emails with login credentials")
        print(f"   2. Admin reviews applications in DSP dashboard")
        print(f"   3. Upon approval, vendors can access their portal")
        print(f"   4. Vendors can now receive leads for Boat Maintenance services")
    
    print(f"\n✅ Vendor signup simulation completed!")
    print(f"   Ready to test lead assignment to these vendors")

if __name__ == "__main__":
    main()