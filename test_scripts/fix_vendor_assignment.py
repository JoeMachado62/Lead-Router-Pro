import logging
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def _vendor_matches_service_fixed(vendor: Dict[str, Any], service_category: str) -> bool:
    """
    Check if vendor provides the requested service category, with improved data validation.
    """
    services_provided = vendor.get("services_provided", [])
    
    # Improved validation: Ensure services_provided is a list
    if isinstance(services_provided, str):
        # If it's a string, split it into a list
        services_provided = [s.strip() for s in services_provided.split(',')]
    
    if not isinstance(services_provided, list):
        # If it's still not a list, treat it as no services provided
        logging.warning(f"Vendor {vendor.get('name')} has malformed services_provided: {services_provided}")
        return False

    service_category_lower = service_category.lower()
    for service in services_provided:
        service_lower = service.lower()
        if (service_category_lower in service_lower or 
            service_lower in service_category_lower):
            return True
    
    return False

def _vendor_covers_location_fixed(vendor: Dict[str, Any], zip_code: str, 
                                  target_state: Optional[str], target_county: Optional[str]) -> bool:
    """
    Check if vendor covers the specified location, with improved data validation.
    """
    coverage_type = vendor.get('service_coverage_type', 'zip')
    
    if coverage_type == 'global':
        return True
    
    if coverage_type == 'national':
        return target_state is not None
    
    if coverage_type == 'state':
        if not target_state:
            return False
        service_states = vendor.get('service_states', [])
        if not isinstance(service_states, list):
            logging.warning(f"Vendor {vendor.get('name')} has malformed service_states: {service_states}")
            return False
        return target_state in service_states
    
    if coverage_type == 'county':
        if not target_county or not target_state:
            return False
        service_counties = vendor.get('service_counties', [])
        if not isinstance(service_counties, list):
            logging.warning(f"Vendor {vendor.get('name')} has malformed service_counties: {service_counties}")
            return False
        
        for coverage_area in service_counties:
            if ',' in coverage_area:
                county_part, state_part = coverage_area.split(',', 1)
                if (target_county.lower() == county_part.strip().lower() and
                    target_state.lower() == state_part.strip().lower()):
                    return True
            elif target_county.lower() == coverage_area.strip().lower():
                return True
        return False
    
    if coverage_type == 'zip':
        service_areas = vendor.get('service_areas', [])
        if not isinstance(service_areas, list):
            logging.warning(f"Vendor {vendor.get('name')} has malformed service_areas: {service_areas}")
            return False
        return zip_code in service_areas
    
    return False

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
            "id": "vendor5",
            "name": "Active Vendor, Malformed JSON",
            "status": "active",
            "taking_new_work": True,
            "services_provided": "Boat Detailing, Cleaning", # Should be a list
            "service_coverage_type": "state",
            "service_states": ["FL"]
        }
    ]
    
    # Test the fixed functions
    for vendor in simulated_vendors:
        logging.info(f"\n--- Checking Vendor: {vendor['name']} with fixed functions ---")
        
        service_match = _vendor_matches_service_fixed(vendor, simulated_lead["service_category"])
        logging.info(f"Service match result: {service_match}")
        
        location_match = _vendor_covers_location_fixed(vendor, simulated_lead["zip_code"], "FL", "Broward")
        logging.info(f"Location match result: {location_match}")
