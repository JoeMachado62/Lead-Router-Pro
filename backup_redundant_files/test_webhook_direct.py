#!/usr/bin/env python3
"""
Test the webhook directly with the correct payload format
"""

import requests
import json

def test_webhook_directly():
    """Test the webhook endpoint directly"""
    print("🔍 Testing Webhook Directly...")
    
    # This is the exact payload the vendor simulator sends
    webhook_payload = {
        "firstName": "Maria",
        "lastName": "Santos",
        "email": "maria.santos.webhook.test@pristineyachts.com",
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
    
    webhook_url = "http://127.0.0.1:8000/api/v1/webhooks/elementor/vendor_application_detailing_specialist"
    
    print(f"Webhook URL: {webhook_url}")
    print(f"Payload: {json.dumps(webhook_payload, indent=2)}")
    
    try:
        response = requests.post(
            webhook_url,
            json=webhook_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS: {result.get('message', 'Webhook processed')}")
            print(f"Contact ID: {result.get('contact_id')}")
            print(f"Action: {result.get('action')}")
            return True
        else:
            print(f"❌ FAILED: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error Details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Raw Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("  DIRECT WEBHOOK TEST")
    print("=" * 60)
    
    success = test_webhook_directly()
    
    print("\n" + "=" * 60)
    print(f"  TEST {'PASSED' if success else 'FAILED'}")
    print("=" * 60)
