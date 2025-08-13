import logging
import json
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Mock necessary modules and classes
class MockLocationService:
    def zip_to_location(self, zip_code: str) -> Dict[str, Optional[str]]:
        if zip_code == "33316":
            return {'state': 'FL', 'county': 'Broward', 'error': None}
        elif zip_code == "90210":
            return {'state': 'CA', 'county': 'Los Angeles', 'error': None}
        else:
            return {'error': f'ZIP code not found: {zip_code}'}

    def normalize_zip_code(self, zip_code: str) -> str:
        return zip_code

class MockSimpleDatabase:
    def __init__(self, vendors: List[Dict[str, Any]]):
        self.vendors = vendors

    def get_vendors(self, account_id: str) -> List[Dict[str, Any]]:
        return self.vendors

# Replace the actual services with our mocks
from api.services.lead_routing_service import LeadRoutingService
lead_routing_service_instance = LeadRoutingService()
lead_routing_service_instance.location_service = MockLocationService()
lead_routing_service_instance.simple_db_instance = MockSimpleDatabase([])

def diagnose_vendor_assignment(lead_payload: Dict[str, Any], vendors_data: List[Dict[str, Any]]):
    """
    Diagnoses why vendors are not being matched for a given lead.
    """
    logging.info("Starting vendor assignment diagnosis...")
    
    # Set up the mock database with the provided vendor data
    lead_routing_service_instance.simple_db_instance.vendors = vendors_data
    
    service_category = lead_payload.get("service_category")
    zip_code = lead_payload.get("zip_code")
    
    logging.info(f"Attempting to match lead: Service='{service_category}', Zip='{zip_code}'")
    
    # Get all vendors from the mock database
    all_vendors = lead_routing_service_instance.simple_db_instance.get_vendors("test_account")
    logging.info(f"Found {len(all_vendors)} total vendors to check.")
    
    # Manually iterate through vendors and check each condition
    for vendor in all_vendors:
        vendor_name = vendor.get("name", "Unknown Vendor")
        logging.info(f"\n--- Checking Vendor: {vendor_name} ---")
        
        # 1. Check status and availability
        is_active = vendor.get("status") == "active" and vendor.get("taking_new_work", False)
        if not is_active:
            logging.warning(f"REJECTED: Vendor is not active or not taking new work. Status: {vendor.get('status')}, Taking Work: {vendor.get('taking_new_work')}")
            continue
        logging.info("  [PASS] Vendor is active and taking new work.")
        
        # 2. Check service matching
        service_match = lead_routing_service_instance._vendor_matches_service(vendor, service_category)
        if not service_match:
            logging.warning(f"REJECTED: Service mismatch.")
            logging.warning(f"  - Lead requires: '{service_category}'")
            logging.warning(f"  - Vendor provides: {vendor.get('services_provided')}")
            continue
        logging.info("  [PASS] Service category matches.")
        
        # 3. Check location coverage
        location_data = lead_routing_service_instance.location_service.zip_to_location(zip_code)
        target_state = location_data.get('state')
        target_county = location_data.get('county')
        
        location_match = lead_routing_service_instance._vendor_covers_location(vendor, zip_code, target_state, target_county)
        if not location_match:
            logging.warning(f"REJECTED: Location mismatch.")
            logging.warning(f"  - Lead location: Zip={zip_code}, State={target_state}, County={target_county}")
            logging.warning(f"  - Vendor coverage type: {vendor.get('service_coverage_type')}")
            logging.warning(f"  - Vendor states: {vendor.get('service_states')}")
            logging.warning(f"  - Vendor counties: {vendor.get('service_counties')}")
            logging.warning(f"  - Vendor zip codes: {vendor.get('service_areas')}")
            continue
        logging.info("  [PASS] Location coverage matches.")
        
        logging.info(f"  *** VENDOR {vendor_name} IS A MATCH! ***")

if __name__ == "__main__":
    # --- Simulation Data ---
    
    # Simulate a lead payload
    simulated_lead = {
        "service_category": "Boat Detailing",
        "zip_code": "33316"
    }
    
    # Simulate vendor data from the database
    simulated_vendors = [
        {
            "id": "vendor1",
            "name": "Active Vendor, Wrong Service",
            "status": "active",
            "taking_new_work": True,
            "services_provided": ["Engine Repair", "Fiberglass"],
            "service_coverage_type": "state",
            "service_states": ["FL"]
        },
        {
            "id": "vendor2",
            "name": "Active Vendor, Right Service, Wrong Location",
            "status": "active",
            "taking_new_work": True,
            "services_provided": ["Boat Detailing", "Waxing"],
            "service_coverage_type": "state",
            "service_states": ["CA", "NV"]
        },
        {
            "id": "vendor3",
            "name": "Inactive Vendor",
            "status": "inactive",
            "taking_new_work": True,
            "services_provided": ["Boat Detailing"],
            "service_coverage_type": "state",
            "service_states": ["FL"]
        },
        {
            "id": "vendor4",
            "name": "Active Vendor, Right Service, Right Location (County)",
            "status": "active",
            "taking_new_work": True,
            "services_provided": ["detailing"],
            "service_coverage_type": "county",
            "service_counties": ["Broward, FL", "Miami-Dade, FL"]
        },
        {
            "id": "vendor5",
            "name": "Active Vendor, Malformed JSON",
            "status": "active",
            "taking_new_work": True,
            "services_provided": "Boat Detailing, Cleaning", # Should be a list
            "service_coverage_type": "state",
            "service_states": ["FL"]
        }
    ]
    
    diagnose_vendor_assignment(simulated_lead, simulated_vendors)
