#!/usr/bin/env python3
"""
Bulk Vendor Submission Script
Processes vendor data from JSON format and submits to Lead Router API
"""

import json
import requests
import time
import csv
from typing import List, Dict, Any
from datetime import datetime

class BulkVendorSubmitter:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.webhook_endpoint = f"{base_url}/api/v1/webhooks/elementor/vendor_application_general"
        self.results = []
        
    def validate_vendor_data(self, vendor: Dict[str, Any]) -> Dict[str, Any]:
        """Validate vendor data before submission"""
        validation = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Required fields
        required_fields = ["firstName", "lastName", "email", "vendor_company_name"]
        for field in required_fields:
            if not vendor.get(field) or str(vendor.get(field)).strip() == "":
                validation["errors"].append(f"Required field '{field}' is missing or empty")
                validation["is_valid"] = False
        
        # Email format validation
        email = vendor.get("email", "")
        if email and "@" not in email:
            validation["errors"].append("Invalid email format")
            validation["is_valid"] = False
        
        # Phone format validation
        phone = vendor.get("phone", "")
        if phone and len(phone.replace("-", "").replace("(", "").replace(")", "").replace(" ", "")) < 10:
            validation["warnings"].append("Phone number may be invalid")
        
        # Service areas validation
        service_zip_codes = vendor.get("service_zip_codes", "")
        if service_zip_codes:
            zip_codes = [z.strip() for z in service_zip_codes.split(",")]
            for zip_code in zip_codes:
                if not zip_code.isdigit() or len(zip_code) != 5:
                    validation["warnings"].append(f"ZIP code '{zip_code}' may be invalid")
        
        return validation
    
    def normalize_vendor_data(self, vendor: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize vendor data to expected format"""
        normalized = vendor.copy()
        
        # Ensure companyName matches vendor_company_name
        if vendor.get("vendor_company_name") and not vendor.get("companyName"):
            normalized["companyName"] = vendor["vendor_company_name"]
        
        # Normalize phone number
        if vendor.get("phone"):
            phone = vendor["phone"]
            # Remove common formatting
            phone = phone.replace("-", "").replace("(", "").replace(")", "").replace(" ", "")
            # Add +1 if it's a 10-digit US number
            if len(phone) == 10 and phone.isdigit():
                normalized["phone"] = f"+1-{phone[:3]}-{phone[3:6]}-{phone[6:]}"
        
        # Ensure source and tags are set
        normalized["source"] = "Bulk Vendor Import (DSP)"
        normalized["tags"] = ["New Vendor Application", "Bulk Import"]
        
        # Add services to tags if provided
        if vendor.get("services_provided"):
            services = [s.strip() for s in vendor["services_provided"].split(",")]
            normalized["tags"].extend(services[:3])  # Add up to 3 service tags
        
        return normalized
    
    def submit_vendor(self, vendor: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a single vendor to the API"""
        try:
            # Validate data
            validation = self.validate_vendor_data(vendor)
            if not validation["is_valid"]:
                return {
                    "success": False,
                    "vendor_email": vendor.get("email", "Unknown"),
                    "vendor_company": vendor.get("vendor_company_name", "Unknown"),
                    "error": f"Validation failed: {', '.join(validation['errors'])}",
                    "validation": validation
                }
            
            # Normalize data
            normalized_vendor = self.normalize_vendor_data(vendor)
            
            # Submit to API
            response = requests.post(
                self.webhook_endpoint,
                json=normalized_vendor,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result_data = response.json()
                return {
                    "success": True,
                    "vendor_email": vendor.get("email"),
                    "vendor_company": vendor.get("vendor_company_name"),
                    "contact_id": result_data.get("contact_id"),
                    "action": result_data.get("action"),
                    "processing_time": result_data.get("processing_time_seconds"),
                    "warnings": validation.get("warnings", []),
                    "response": result_data
                }
            else:
                return {
                    "success": False,
                    "vendor_email": vendor.get("email"),
                    "vendor_company": vendor.get("vendor_company_name"),
                    "error": f"API error: {response.status_code} - {response.text}",
                    "status_code": response.status_code
                }
                
        except Exception as e:
            return {
                "success": False,
                "vendor_email": vendor.get("email", "Unknown"),
                "vendor_company": vendor.get("vendor_company_name", "Unknown"),
                "error": f"Exception: {str(e)}",
                "exception_type": e.__class__.__name__
            }
    
    def submit_vendors_from_json(self, json_file_path: str, delay_seconds: float = 1.0) -> Dict[str, Any]:
        """Submit vendors from a JSON file"""
        print(f"🚀 Starting bulk vendor submission from {json_file_path}")
        print(f"⏱️  Delay between submissions: {delay_seconds} seconds")
        print(f"🎯 Target endpoint: {self.webhook_endpoint}")
        
        try:
            # Load vendor data
            with open(json_file_path, 'r') as f:
                vendors_data = json.load(f)
            
            # Handle both array of vendors and single vendor object
            if isinstance(vendors_data, dict):
                vendors = [vendors_data]
            elif isinstance(vendors_data, list):
                vendors = vendors_data
            else:
                raise ValueError("JSON file must contain a vendor object or array of vendor objects")
            
            print(f"📋 Loaded {len(vendors)} vendor(s) from JSON file")
            
            # Process each vendor
            successful_submissions = 0
            failed_submissions = 0
            
            for i, vendor in enumerate(vendors, 1):
                print(f"\n📤 Processing vendor {i}/{len(vendors)}: {vendor.get('vendor_company_name', 'Unknown Company')}")
                
                result = self.submit_vendor(vendor)
                self.results.append(result)
                
                if result["success"]:
                    successful_submissions += 1
                    print(f"  ✅ SUCCESS: {result['vendor_company']} ({result['vendor_email']})")
                    print(f"     Contact ID: {result.get('contact_id', 'N/A')}")
                    print(f"     Action: {result.get('action', 'N/A')}")
                    if result.get("warnings"):
                        print(f"     Warnings: {', '.join(result['warnings'])}")
                else:
                    failed_submissions += 1
                    print(f"  ❌ FAILED: {result['vendor_company']} ({result['vendor_email']})")
                    print(f"     Error: {result['error']}")
                
                # Delay between submissions to avoid overwhelming the API
                if i < len(vendors):
                    time.sleep(delay_seconds)
            
            # Summary
            summary = {
                "total_vendors": len(vendors),
                "successful_submissions": successful_submissions,
                "failed_submissions": failed_submissions,
                "success_rate": round((successful_submissions / len(vendors)) * 100, 2) if vendors else 0,
                "results": self.results
            }
            
            print(f"\n📊 BULK SUBMISSION SUMMARY")
            print(f"   Total Vendors: {summary['total_vendors']}")
            print(f"   Successful: {summary['successful_submissions']}")
            print(f"   Failed: {summary['failed_submissions']}")
            print(f"   Success Rate: {summary['success_rate']}%")
            
            return summary
            
        except Exception as e:
            print(f"❌ Error processing JSON file: {str(e)}")
            return {
                "total_vendors": 0,
                "successful_submissions": 0,
                "failed_submissions": 0,
                "success_rate": 0,
                "error": str(e),
                "results": []
            }
    
    def submit_vendors_from_csv(self, csv_file_path: str, delay_seconds: float = 1.0) -> Dict[str, Any]:
        """Submit vendors from a CSV file"""
        print(f"🚀 Starting bulk vendor submission from CSV: {csv_file_path}")
        
        try:
            vendors = []
            
            # Read CSV file
            with open(csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    # Convert CSV row to vendor object, skipping empty values
                    vendor = {k: v for k, v in row.items() if v and v.strip()}
                    if vendor:  # Only add non-empty rows
                        vendors.append(vendor)
            
            print(f"📋 Loaded {len(vendors)} vendor(s) from CSV file")
            
            # Convert to JSON temporarily and use existing JSON processing
            temp_json_path = f"temp_vendors_{int(time.time())}.json"
            with open(temp_json_path, 'w') as f:
                json.dump(vendors, f, indent=2)
            
            # Process using JSON method
            result = self.submit_vendors_from_json(temp_json_path, delay_seconds)
            
            # Clean up temp file
            import os
            os.remove(temp_json_path)
            
            return result
            
        except Exception as e:
            print(f"❌ Error processing CSV file: {str(e)}")
            return {
                "total_vendors": 0,
                "successful_submissions": 0,
                "failed_submissions": 0,
                "success_rate": 0,
                "error": str(e),
                "results": []
            }
    
    def generate_sample_json(self, output_file: str = "sample_vendors.json"):
        """Generate a sample JSON file with vendor data"""
        sample_vendors = [
            {
                "firstName": "Michael",
                "lastName": "Rodriguez",
                "email": "mike@marineprosolutions.com",
                "phone": "+1-305-555-0123",
                "vendor_company_name": "Marine Pro Solutions LLC",
                "companyName": "Marine Pro Solutions LLC",
                "address1": "1234 Marina Boulevard",
                "city": "Miami",
                "state": "FL",
                "postal_code": "33139",
                "website": "https://marineprosolutions.com",
                "services_provided": "Boat Maintenance, Marine Systems, Engine Service",
                "service_zip_codes": "33139,33140,33141,33154,33155,33156",
                "years_in_business": "8",
                "preferred_contact_method": "Phone",
                "vessel_types_serviced": "Sailboats, Motor Yachts, Sport Fishing Boats",
                "certifications_licenses": "ABYC Certified, Florida Marine Contractor License #MC12345",
                "insurance_coverage": "General Liability: $2M, Professional Liability: $1M",
                "availability_schedule": "Monday-Friday 8AM-6PM, Saturday 9AM-3PM",
                "emergency_services": "Yes",
                "service_radius_miles": "25",
                "crew_size": "4",
                "special_equipment": "Mobile crane, underwater welding equipment",
                "pricing_structure": "Hourly rates, Project-based quotes available",
                "payment_terms": "Net 30, Credit cards accepted",
                "references": "Harbor Marina (305-555-0100), Sunset Yacht Club (305-555-0200)",
                "special_requests__notes": "Specializing in luxury yacht maintenance and emergency repairs. Available 24/7 for emergency calls."
            },
            {
                "firstName": "Sarah",
                "lastName": "Johnson",
                "email": "sarah@coastalengineering.com",
                "phone": "954-555-0456",
                "vendor_company_name": "Coastal Engineering Services",
                "companyName": "Coastal Engineering Services",
                "address1": "567 Harbor Drive",
                "city": "Fort Lauderdale",
                "state": "FL",
                "postal_code": "33301",
                "website": "https://coastalengineering.com",
                "services_provided": "Marine Systems, Engines and Generators",
                "service_zip_codes": "33301,33302,33303,33304,33305",
                "years_in_business": "12",
                "preferred_contact_method": "Email",
                "vessel_types_serviced": "Motor Yachts, Commercial Vessels",
                "certifications_licenses": "Marine Engineer License, USCG Certified",
                "insurance_coverage": "Professional Liability: $5M, General Liability: $3M",
                "availability_schedule": "Monday-Saturday 7AM-7PM",
                "emergency_services": "Yes",
                "service_radius_miles": "50",
                "crew_size": "6",
                "special_equipment": "Diagnostic computers, Hydraulic test equipment",
                "pricing_structure": "Project-based quotes, Emergency rates available",
                "payment_terms": "Net 15, All major credit cards",
                "references": "Bahia Mar Marina (954-555-0300), Las Olas Marina (954-555-0400)",
                "special_requests__notes": "Specialized in complex marine electrical systems and generator installations."
            }
        ]
        
        with open(output_file, 'w') as f:
            json.dump(sample_vendors, f, indent=2)
        
        print(f"📄 Sample vendor JSON file created: {output_file}")
        print(f"   Contains {len(sample_vendors)} sample vendor records")
        print(f"   Edit this file with your actual vendor data, then run:")
        print(f"   python bulk_vendor_submission.py --json {output_file}")
    
    def save_results_report(self, results: Dict[str, Any], output_file: str = None):
        """Save detailed results report"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"vendor_submission_report_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"📄 Detailed results report saved: {output_file}")


def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Bulk Vendor Submission Tool")
    parser.add_argument("--json", help="JSON file containing vendor data")
    parser.add_argument("--csv", help="CSV file containing vendor data")
    parser.add_argument("--sample", action="store_true", help="Generate sample JSON file")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between submissions (seconds)")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL for Lead Router API")
    
    args = parser.parse_args()
    
    submitter = BulkVendorSubmitter(base_url=args.url)
    
    if args.sample:
        submitter.generate_sample_json()
        return
    
    if args.json:
        results = submitter.submit_vendors_from_json(args.json, args.delay)
        submitter.save_results_report(results)
    elif args.csv:
        results = submitter.submit_vendors_from_csv(args.csv, args.delay)
        submitter.save_results_report(results)
    else:
        print("❌ Please specify --json, --csv, or --sample")
        print("Examples:")
        print("  python bulk_vendor_submission.py --sample")
        print("  python bulk_vendor_submission.py --json vendors.json")
        print("  python bulk_vendor_submission.py --csv vendors.csv --delay 2.0")


if __name__ == "__main__":
    main()
