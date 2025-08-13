#!/usr/bin/env python3
"""
Active Vendors Printout Script
Generates a formatted report of all active vendors showing:
- Vendor Name
- GHL User ID  
- Primary Service Category
- Specific Services Offered
"""

import sys
import os
import json
from datetime import datetime
from typing import List, Dict, Any

# Add the Lead-Router-Pro directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.simple_connection import SimpleDatabase
from api.services.service_categories import service_manager

def parse_services_data(services_json: str) -> List[str]:
    """Parse services from JSON string, handling various formats"""
    if not services_json:
        return []
    
    try:
        # Try to parse as JSON array
        services = json.loads(services_json)
        if isinstance(services, list):
            return services
        elif isinstance(services, str):
            # If it's a string, try to split by comma
            return [s.strip() for s in services.split(',') if s.strip()]
        else:
            return [str(services)]
    except (json.JSONDecodeError, TypeError):
        # If JSON parsing fails, treat as comma-separated string
        return [s.strip() for s in services_json.split(',') if s.strip()]

def determine_primary_service_category(services: List[str]) -> str:
    """Determine primary service category from services list using service_manager"""
    if not services:
        return "Boater Resources"  # Default from service_manager
    
    # Use service_manager to find the category for the first service
    first_service = services[0].strip()
    
    # Try to find which category this service belongs to
    for category_name, services_list in service_manager.SERVICE_CATEGORIES.items():
        # Check if the service matches exactly
        if first_service in services_list:
            return category_name
        
        # Check if any service in the category contains the service name (case-insensitive)
        for service in services_list:
            if first_service.lower() in service.lower() or service.lower() in first_service.lower():
                return category_name
    
    # If no exact match found, try keyword matching
    first_service_lower = first_service.lower()
    
    # Simple keyword mapping for common terms
    if any(keyword in first_service_lower for keyword in ['maintenance', 'cleaning', 'detailing', 'wash']):
        return "Boat Maintenance"
    elif any(keyword in first_service_lower for keyword in ['engine', 'generator', 'motor']):
        return "Engines and Generators"
    elif any(keyword in first_service_lower for keyword in ['electrical', 'plumbing', 'ac', 'hvac']):
        return "Marine Systems"
    elif any(keyword in first_service_lower for keyword in ['repair', 'fiberglass', 'welding']):
        return "Boat and Yacht Repair"
    elif any(keyword in first_service_lower for keyword in ['towing', 'emergency']):
        return "Boat Towing"
    elif any(keyword in first_service_lower for keyword in ['charter', 'rental']):
        return "Boat Charters and Rentals"
    elif any(keyword in first_service_lower for keyword in ['dock', 'slip', 'marina']):
        return "Dock and Slip Rental"
    elif any(keyword in first_service_lower for keyword in ['fuel', 'gas', 'diesel']):
        return "Fuel Delivery"
    elif any(keyword in first_service_lower for keyword in ['buy', 'sell', 'broker', 'dealer']):
        return "Buying or Selling a Boat"
    elif any(keyword in first_service_lower for keyword in ['management']):
        return "Yacht Management"
    elif any(keyword in first_service_lower for keyword in ['education', 'training']):
        return "Maritime Education and Training"
    elif any(keyword in first_service_lower for keyword in ['property', 'waterfront']):
        return "Waterfront Property"
    elif any(keyword in first_service_lower for keyword in ['seawall', 'lift']):
        return "Docks, Seawalls and Lifts"
    else:
        # If no match found, return the first service as-is or default category
        return first_service if first_service else "Boater Resources"

def format_service_areas(service_areas, service_states, service_counties) -> str:
    """Format service coverage areas into readable string"""
    areas = []
    
    # Parse service areas (zip codes)
    if service_areas:
        if isinstance(service_areas, list):
            # Already a list
            if service_areas:
                areas.append(f"Zip Codes: {', '.join(map(str, service_areas))}")
        elif isinstance(service_areas, str):
            try:
                zip_codes = json.loads(service_areas)
                if isinstance(zip_codes, list) and zip_codes:
                    areas.append(f"Zip Codes: {', '.join(map(str, zip_codes))}")
            except (json.JSONDecodeError, TypeError):
                if service_areas.strip():
                    areas.append(f"Zip Codes: {service_areas}")
    
    # Parse service counties
    if service_counties:
        if isinstance(service_counties, list):
            # Already a list
            if service_counties:
                areas.append(f"Counties: {', '.join(service_counties)}")
        elif isinstance(service_counties, str):
            try:
                counties = json.loads(service_counties)
                if isinstance(counties, list) and counties:
                    areas.append(f"Counties: {', '.join(counties)}")
            except (json.JSONDecodeError, TypeError):
                if service_counties.strip():
                    areas.append(f"Counties: {service_counties}")
    
    # Parse service states
    if service_states:
        if isinstance(service_states, list):
            # Already a list
            if service_states:
                areas.append(f"States: {', '.join(service_states)}")
        elif isinstance(service_states, str):
            try:
                states = json.loads(service_states)
                if isinstance(states, list) and states:
                    areas.append(f"States: {', '.join(states)}")
            except (json.JSONDecodeError, TypeError):
                if service_states.strip():
                    areas.append(f"States: {service_states}")
    
    return " | ".join(areas) if areas else "Not specified"

def print_active_vendors():
    """Main function to print active vendors report"""
    try:
        # Initialize database connection
        db = SimpleDatabase()
        
        print("=" * 100)
        print("ACTIVE VENDORS REPORT")
        print("=" * 100)
        print(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Get all active vendors
        active_vendors = db.get_vendors(status='active')
        
        if not active_vendors:
            print("No active vendors found in the database.")
            print()
            
            # Check if there are any vendors at all
            all_vendors = db.get_vendors()
            if all_vendors:
                print(f"Total vendors in database: {len(all_vendors)}")
                status_counts = {}
                for vendor in all_vendors:
                    status = vendor.get('status', 'unknown')
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                print("Vendor status breakdown:")
                for status, count in status_counts.items():
                    print(f"  {status}: {count}")
            else:
                print("No vendors found in the database at all.")
            
            return
        
        print(f"Total Active Vendors: {len(active_vendors)}")
        print()
        
        # Print header
        print("-" * 100)
        print(f"{'#':<3} {'Vendor Name':<25} {'GHL User ID':<20} {'Primary Category':<25} {'Status':<10}")
        print("-" * 100)
        
        # Print each vendor
        for i, vendor in enumerate(active_vendors, 1):
            vendor_name = vendor.get('name', 'N/A')
            ghl_user_id = vendor.get('ghl_user_id', 'Not Set')
            services_provided = vendor.get('services_provided', [])
            status = vendor.get('status', 'unknown')
            
            # Parse services
            if isinstance(services_provided, str):
                services_list = parse_services_data(services_provided)
            else:
                services_list = services_provided if services_provided else []
            
            # Determine primary category
            primary_category = determine_primary_service_category(services_list)
            
            # Truncate long names for table formatting
            display_name = vendor_name[:24] + "..." if len(vendor_name) > 24 else vendor_name
            display_ghl_id = ghl_user_id[:19] + "..." if len(ghl_user_id) > 19 else ghl_user_id
            display_category = primary_category[:24] + "..." if len(primary_category) > 24 else primary_category
            
            print(f"{i:<3} {display_name:<25} {display_ghl_id:<20} {display_category:<25} {status:<10}")
        
        print("-" * 100)
        print()
        
        # Detailed vendor information
        print("DETAILED VENDOR INFORMATION")
        print("=" * 100)
        
        for i, vendor in enumerate(active_vendors, 1):
            print(f"\n{i}. {vendor.get('name', 'N/A')}")
            print(f"   Company: {vendor.get('company_name', 'N/A')}")
            print(f"   Email: {vendor.get('email', 'N/A')}")
            print(f"   Phone: {vendor.get('phone', 'N/A')}")
            print(f"   GHL Contact ID: {vendor.get('ghl_contact_id', 'Not Set')}")
            print(f"   GHL User ID: {vendor.get('ghl_user_id', 'Not Set')}")
            print(f"   Status: {vendor.get('status', 'unknown')}")
            print(f"   Taking New Work: {'Yes' if vendor.get('taking_new_work', False) else 'No'}")
            print(f"   Performance Score: {vendor.get('performance_score', 'N/A')}")
            
            # Parse and display services
            services_provided = vendor.get('services_provided', [])
            if isinstance(services_provided, str):
                services_list = parse_services_data(services_provided)
            else:
                services_list = services_provided if services_provided else []
            
            primary_category = determine_primary_service_category(services_list)
            print(f"   Primary Service Category: {primary_category}")
            
            if services_list:
                print(f"   Specific Services Offered:")
                for service in services_list:
                    print(f"     • {service}")
            else:
                print(f"   Specific Services Offered: None specified")
            
            # Service coverage areas
            service_areas = format_service_areas(
                vendor.get('service_areas', ''),
                vendor.get('service_states', ''),
                vendor.get('service_counties', '')
            )
            print(f"   Service Coverage: {service_areas}")
            
            # Additional info
            print(f"   Created: {vendor.get('created_at', 'N/A')}")
            print(f"   Last Updated: {vendor.get('updated_at', 'N/A')}")
            
            if vendor.get('last_lead_assigned'):
                print(f"   Last Lead Assigned: {vendor.get('last_lead_assigned')}")
            
            print("-" * 50)
        
        # Summary statistics
        print("\nSUMMARY STATISTICS")
        print("=" * 50)
        
        # Count vendors by service category
        category_counts = {}
        ghl_user_count = 0
        taking_work_count = 0
        
        for vendor in active_vendors:
            services_provided = vendor.get('services_provided', [])
            if isinstance(services_provided, str):
                services_list = parse_services_data(services_provided)
            else:
                services_list = services_provided if services_provided else []
            
            primary_category = determine_primary_service_category(services_list)
            category_counts[primary_category] = category_counts.get(primary_category, 0) + 1
            
            if vendor.get('ghl_user_id'):
                ghl_user_count += 1
            
            if vendor.get('taking_new_work', False):
                taking_work_count += 1
        
        print(f"Total Active Vendors: {len(active_vendors)}")
        print(f"Vendors with GHL User ID: {ghl_user_count}")
        print(f"Vendors Taking New Work: {taking_work_count}")
        print()
        
        print("Vendors by Primary Service Category:")
        for category, count in sorted(category_counts.items()):
            print(f"  {category}: {count}")
        
        print("\n" + "=" * 100)
        print("END OF REPORT")
        print("=" * 100)
        
    except Exception as e:
        print(f"Error generating vendor report: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print_active_vendors()
