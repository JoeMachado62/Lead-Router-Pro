# api/services/lead_routing_service.py

import logging
import random
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from api.services.location_service import location_service
from api.services.service_categories import service_manager
from database.simple_connection import db as simple_db_instance

logger = logging.getLogger(__name__)

class LeadRoutingService:
    """
    Enhanced lead routing service that supports:
    - Geographic coverage types (global, national, state, county, zip)
    - Dual routing methods (round-robin vs performance-based)
    - Configurable routing distribution percentages
    - DIRECT STRING MATCHING for service matching (no keyword matching)
    """
    
    def __init__(self):
        self.location_service = location_service
    
    def find_matching_vendors(self, account_id: str, service_category: str, 
                            zip_code: str, priority: str = "normal",
                            specific_service: str = None) -> List[Dict[str, Any]]:
        """
        Find all vendors that can serve the specified location and service category.
        Enhanced with multi-level service matching for precise vendor routing.
        
        Args:
            account_id: Account ID to search within
            service_category: Primary service category (e.g., "Marine Systems")
            zip_code: ZIP code where service is needed
            priority: Priority level of the request
            specific_service: Specific service needed (e.g., "AC Service") - NEW
            
        Returns:
            List of matching vendors with coverage verification
        """
        try:
            # Convert ZIP code to location information
            location_data = self.location_service.zip_to_location(zip_code)
            
            if location_data.get('error'):
                logger.warning(f"⚠️ Could not resolve ZIP code {zip_code}: {location_data['error']}")
                # Continue with limited matching for legacy ZIP code vendors
                target_state = None
                target_county = None
            else:
                target_state = location_data.get('state')
                target_county = location_data.get('county')
                logger.info(f"📍 Lead location: {zip_code} → {target_state}, {target_county} County")
            
            # Get all active vendors for this account
            all_vendors = self._get_vendors_from_database(account_id)
            eligible_vendors = []
            
            for vendor in all_vendors:
                # Check if vendor is active and taking new work
                if vendor.get("status") != "active" or not vendor.get("taking_new_work", False):
                    logger.debug(f"Skipping vendor {vendor.get('name')} - not active or not taking work")
                    continue
                
                # DIRECT SERVICE MATCHING - match specific service if provided, otherwise category
                service_to_match = specific_service if specific_service else service_category
                if not self._vendor_matches_service(vendor, service_to_match):
                    logger.debug(f"Skipping vendor {vendor.get('name')} - no exact service match for '{service_to_match}'")
                    continue
                
                # Check if vendor can serve this location
                if self._vendor_covers_location(vendor, zip_code, target_state, target_county):
                    # Add coverage info for debugging
                    vendor_copy = vendor.copy()
                    vendor_copy['coverage_match_reason'] = self._get_coverage_match_reason(
                        vendor, zip_code, target_state, target_county
                    )
                    eligible_vendors.append(vendor_copy)
                    logger.debug(f"✅ Vendor {vendor.get('name')} matches - {vendor_copy['coverage_match_reason']}")
                else:
                    logger.debug(f"Skipping vendor {vendor.get('name')} - location not covered")
            
            service_desc = f"specific service '{specific_service}'" if specific_service else f"category '{service_category}'"
            logger.info(f"🎯 Found {len(eligible_vendors)} eligible vendors for {service_desc} in {zip_code}")
            return eligible_vendors
            
        except Exception as e:
            logger.error(f"❌ Error finding matching vendors: {e}")
            return []
    
    def _get_vendors_from_database(self, account_id: str) -> List[Dict[str, Any]]:
        """
        Get vendors from database using ACTUAL field names (no incorrect mapping).
        FIXED: Uses the field names that actually exist in the database.
        """
        try:
            import sqlite3
            
            conn = sqlite3.connect('smart_lead_router.db')
            cursor = conn.cursor()
            
            # Query vendors using ACTUAL database field names
            cursor.execute("""
                SELECT id, account_id, ghl_contact_id, ghl_user_id, name, email, phone,
                       company_name, service_categories, services_offered, coverage_type,
                       coverage_states, coverage_counties, last_lead_assigned,
                       lead_close_percentage, status, taking_new_work
                FROM vendors
                WHERE account_id = ?
            """, (account_id,))
            
            vendors = []
            for row in cursor.fetchall():
                vendor = {
                    'id': row[0],
                    'account_id': row[1],
                    'ghl_contact_id': row[2],
                    'ghl_user_id': row[3],
                    'name': row[4],
                    'email': row[5],
                    'phone': row[6],
                    'company_name': row[7],
                    'service_categories': json.loads(row[8]) if row[8] else [],
                    'services_offered': json.loads(row[9]) if row[9] else [],  # ACTUAL field name
                    'coverage_type': row[10] or 'county',  # ACTUAL field name
                    'coverage_states': json.loads(row[11]) if row[11] else [],  # ACTUAL field name
                    'coverage_counties': json.loads(row[12]) if row[12] else [],  # ACTUAL field name
                    'last_lead_assigned': row[13],
                    'lead_close_percentage': row[14] or 0.0,
                    'status': row[15] or 'active',
                    'taking_new_work': bool(row[16]) if row[16] is not None else True
                }
                vendors.append(vendor)
            
            conn.close()
            logger.debug(f"📊 Retrieved {len(vendors)} vendors using actual field names for account {account_id}")
            return vendors
            
        except Exception as e:
            logger.error(f"❌ Error getting vendors from database: {e}")
            return []
    
    def _vendor_matches_service(self, vendor: Dict[str, Any], service_category: str) -> bool:
        """
        Check if vendor provides the requested service using DIRECT STRING MATCHING ONLY.
        
        NO keyword matching, NO AI, NO parsing - just exact string comparison.
        
        Args:
            vendor: Vendor dictionary with services_offered field
            service_category: Exact service name requested (e.g., "Inboard Engine Service")
            
        Returns:
            bool: True if vendor offers the exact service, False otherwise
        """
        try:
            services_offered = vendor.get('services_offered', [])
            
            # Handle string format (convert to list)
            if isinstance(services_offered, str):
                try:
                    services_offered = json.loads(services_offered)
                except (json.JSONDecodeError, TypeError):
                    # If JSON parsing fails, treat as comma-separated string
                    services_offered = [s.strip() for s in services_offered.split(',') if s.strip()]
            
            # Ensure it's a list
            if not isinstance(services_offered, list):
                logger.warning(f"Vendor {vendor.get('name')} has malformed services_offered: {services_offered}")
                return False
            
            # DIRECT STRING MATCHING ONLY - exact match required
            for offered_service in services_offered:
                if str(offered_service).strip() == str(service_category).strip():
                    logger.debug(f"✅ Exact service match: '{service_category}' in vendor services")
                    return True
            
            # No exact match found
            logger.debug(f"❌ No exact match for '{service_category}' in {services_offered}")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error in service matching for vendor {vendor.get('name')}: {e}")
            return False
    
    def _vendor_covers_location(self, vendor: Dict[str, Any], zip_code: str, 
                              target_state: Optional[str], target_county: Optional[str]) -> bool:
        """
        Check if vendor covers the specified location, with improved data validation.
        FIXED: Uses actual database field names (coverage_type, coverage_states, coverage_counties)
        """
        coverage_type = vendor.get('coverage_type', 'zip')  # FIXED: Use actual field name
        
        if coverage_type == 'global':
            return True
        
        if coverage_type == 'national':
            return target_state is not None
        
        if coverage_type == 'state':
            if not target_state:
                return False
            coverage_states = vendor.get('coverage_states', [])  # FIXED: Use actual field name
            if not isinstance(coverage_states, list):
                logger.warning(f"Vendor {vendor.get('name')} has malformed coverage_states: {coverage_states}")
                return False
            return target_state in coverage_states
        
        if coverage_type == 'county':
            if not target_county or not target_state:
                return False
            coverage_counties = vendor.get('coverage_counties', [])  # FIXED: Use actual field name
            if not isinstance(coverage_counties, list):
                logger.warning(f"Vendor {vendor.get('name')} has malformed coverage_counties: {coverage_counties}")
                return False
            
            # Build the full county string to match against vendor's coverage
            full_county_string = f"{target_county}, {target_state}"
            
            for coverage_area in coverage_counties:
                # Direct string comparison for exact match
                if coverage_area.strip() == full_county_string:
                    logger.debug(f"✅ Exact county match: '{full_county_string}' in vendor's coverage")
                    return True
                
                # Also try component matching for flexibility
                if ',' in coverage_area:
                    county_part, state_part = coverage_area.split(',', 1)
                    if (target_county.lower() == county_part.strip().lower() and
                        target_state.lower() == state_part.strip().lower()):
                        logger.debug(f"✅ Component county match: {target_county}, {target_state}")
                        return True
            return False
        
        if coverage_type == 'zip':
            service_areas = vendor.get('service_areas', [])  # NOTE: This field doesn't exist in vendors table
            if not isinstance(service_areas, list):
                logger.warning(f"Vendor {vendor.get('name')} has malformed service_areas: {service_areas}")
                return False
            normalized_zip = self.location_service.normalize_zip_code(zip_code)
            normalized_service_areas = [
                self.location_service.normalize_zip_code(z) for z in service_areas
            ]
            return normalized_zip in normalized_service_areas
        
        return False
    
    def _get_coverage_match_reason(self, vendor: Dict[str, Any], zip_code: str,
                                 target_state: Optional[str], target_county: Optional[str]) -> str:
        """
        Get human-readable reason for why vendor matches the location
        FIXED: Uses actual database field name (coverage_type)
        """
        coverage_type = vendor.get('coverage_type', 'zip')  # FIXED: Use actual field name
        
        if coverage_type == 'global':
            return "Global coverage"
        elif coverage_type == 'national':
            return "National coverage"
        elif coverage_type == 'state':
            return f"State coverage: {target_state}"
        elif coverage_type == 'county':
            return f"County coverage: {target_county}, {target_state}"
        elif coverage_type == 'zip':
            return f"ZIP code coverage: {zip_code}"
        else:
            return f"Coverage type: {coverage_type}"
    
    def select_vendor_from_pool(self, eligible_vendors: List[Dict[str, Any]], 
                              account_id: str) -> Optional[Dict[str, Any]]:
        """
        Select a vendor from the eligible pool using the configured routing method
        
        Args:
            eligible_vendors: List of vendors that can serve the request
            account_id: Account ID for routing configuration
            
        Returns:
            Selected vendor or None if no vendors available
        """
        if not eligible_vendors:
            return None
        
        # Get routing configuration for this account
        routing_config = self._get_routing_configuration(account_id)
        performance_percentage = routing_config.get('performance_percentage', 0)
        
        # Decide which routing method to use based on percentage
        use_performance = random.randint(1, 100) <= performance_percentage
        
        if use_performance:
            logger.info(f"🎯 Using performance-based routing ({performance_percentage}% configured)")
            selected_vendor = self._select_by_performance(eligible_vendors)
        else:
            logger.info(f"🔄 Using round-robin routing ({100 - performance_percentage}% configured)")
            selected_vendor = self._select_by_round_robin(eligible_vendors)
        
        # Update vendor's last_lead_assigned timestamp
        if selected_vendor:
            self._update_vendor_last_assigned(selected_vendor['id'])
        
        return selected_vendor
    
    def _get_routing_configuration(self, account_id: str) -> Dict[str, Any]:
        """
        Get routing configuration for the account
        
        Args:
            account_id: Account ID
            
        Returns:
            Routing configuration dictionary
        """
        try:
            # Get performance percentage from account settings
            performance_percentage = simple_db_instance.get_account_setting(
                account_id, 'lead_routing_performance_percentage'
            )
            
            if performance_percentage is None:
                # Default to 0% performance-based (100% round-robin)
                performance_percentage = 0
                # Save default setting
                simple_db_instance.upsert_account_setting(
                    account_id, 'lead_routing_performance_percentage', 0
                )
            else:
                performance_percentage = int(performance_percentage)
            
            return {
                'performance_percentage': performance_percentage,
                'round_robin_percentage': 100 - performance_percentage
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting routing configuration for account {account_id}: {e}")
            return {'performance_percentage': 0, 'round_robin_percentage': 100}
    
    def _select_by_performance(self, vendors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Select vendor with highest lead_close_percentage
        
        Args:
            vendors: List of eligible vendors
            
        Returns:
            Vendor with best performance
        """
        # Sort by close percentage (desc), then by last_lead_assigned (asc) for ties
        sorted_vendors = sorted(
            vendors,
            key=lambda v: (
                -v.get('lead_close_percentage', 0),  # Higher percentage first
                v.get('last_lead_assigned') or '1900-01-01'  # Older assignment first for ties
            )
        )
        
        selected = sorted_vendors[0]
        logger.info(f"🏆 Performance-based selection: {selected.get('name')} "
                   f"(close rate: {selected.get('lead_close_percentage', 0)}%)")
        return selected
    
    def _select_by_round_robin(self, vendors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Select vendor with oldest last_lead_assigned date
        
        Args:
            vendors: List of eligible vendors
            
        Returns:
            Vendor with oldest assignment
        """
        # Sort by last_lead_assigned (asc) - oldest first
        sorted_vendors = sorted(
            vendors,
            key=lambda v: v.get('last_lead_assigned') or '1900-01-01'
        )
        
        selected = sorted_vendors[0]
        last_assigned = selected.get('last_lead_assigned', 'Never')
        logger.info(f"🔄 Round-robin selection: {selected.get('name')} "
                   f"(last assigned: {last_assigned})")
        return selected
    
    def _update_vendor_last_assigned(self, vendor_id: str) -> None:
        """
        Update vendor's last_lead_assigned timestamp
        
        Args:
            vendor_id: Vendor ID to update
        """
        try:
            conn = simple_db_instance._get_conn()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE vendors 
                SET last_lead_assigned = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (vendor_id,))
            conn.commit()
            conn.close()
            logger.debug(f"✅ Updated last_lead_assigned for vendor {vendor_id}")
        except Exception as e:
            logger.error(f"❌ Error updating last_lead_assigned for vendor {vendor_id}: {e}")
    
    def update_routing_configuration(self, account_id: str, performance_percentage: int) -> bool:
        """
        Update the routing configuration for an account
        
        Args:
            account_id: Account ID
            performance_percentage: Percentage of leads to route by performance (0-100)
            
        Returns:
            True if update was successful
        """
        try:
            # Validate percentage
            if not 0 <= performance_percentage <= 100:
                raise ValueError("Performance percentage must be between 0 and 100")
            
            # Save to account settings
            simple_db_instance.upsert_account_setting(
                account_id, 'lead_routing_performance_percentage', performance_percentage
            )
            
            logger.info(f"✅ Updated routing configuration for account {account_id}: "
                       f"{performance_percentage}% performance, {100 - performance_percentage}% round-robin")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating routing configuration for account {account_id}: {e}")
            return False
    
    def get_routing_stats(self, account_id: str) -> Dict[str, Any]:
        """
        Get routing statistics for an account
        
        Args:
            account_id: Account ID
            
        Returns:
            Dictionary with routing statistics
        """
        try:
            config = self._get_routing_configuration(account_id)
            vendors = simple_db_instance.get_vendors(account_id=account_id)
            
            # Count vendors by coverage type
            coverage_stats = {}
            for vendor in vendors:
                coverage_type = vendor.get('coverage_type', 'zip')  # FIXED: Use actual field name
                coverage_stats[coverage_type] = coverage_stats.get(coverage_type, 0) + 1
            
            # Get recent lead assignments (would need to track this in activity log)
            # For now, return basic stats
            
            return {
                'routing_configuration': config,
                'total_vendors': len(vendors),
                'active_vendors': len([v for v in vendors if v.get('status') == 'active']),
                'vendors_taking_work': len([v for v in vendors if v.get('taking_new_work', False)]),
                'coverage_distribution': coverage_stats,
                'location_service_status': 'active' if self.location_service.geo_us else 'inactive'
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting routing stats for account {account_id}: {e}")
            return {}


# COMPREHENSIVE SERVICE LIST FOR VALIDATION
COMPLETE_SERVICES_LIST = [
    "Barnacle Cleaning", "Boat and Yacht Maintenance", "Boat and Yacht Parts", 
    "Boat Bilge Cleaning", "Boat Bottom Cleaning", "Boat Brokers", "Boat Builders", 
    "Boat Canvas and Upholstery", "Boat Charters and Rentals", "Boat Clubs", 
    "Boat Dealers", "Boat Decking and Yacht Flooring", "Boat Detailing", 
    "Boat Electrical Service", "Boat Financing", "Boat Hauling and Transport", 
    "Boat Insurance", "Boat Lift Installers", "Boat Lighting", "Boat Oil Change", 
    "Boat Salvage", "Boat Sound Systems", "Boat Surveyors", 
    "Boat Wrapping and Marine Protection Film", "Carpentry & Woodwork", 
    "Ceramic Coating", "Davit and Hydraulic Platform", "Diesel Engine Sales", 
    "Diesel Engine Service", "Dive Equipment and Services", 
    "Dock and Seawall Builders or Repair", "Dock and Slip Rental", 
    "eFoil, Kiteboarding & Wing Surfing", "Fiberglass Repair", "Fishing Charters", 
    "Floating Dock Sales", "Fuel Delivery", "Generator Sales", 
    "Generator Service and Repair", "Get Emergency Tow", "Get Towing Membership", 
    "Inboard Engine Sales", "Inboard Engine Service", "Jet Ski Maintenance", 
    "Jet Ski Repair", "Maritime Academy", "Maritime Certification", 
    "New Waterfront Developments", "Outboard Engine Sales", "Outboard Engine Service", 
    "Provisioning", "Rent My Dock", "Riggers & Masts", "Sailboat Charters", 
    "Sailing Schools", "Sell Your Waterfront Home", "Waterfront Homes For Sale", 
    "Welding & Metal Fabrication", "Wholesale or Dealer Product Pricing", 
    "Yacht AC Sales", "Yacht AC Service", "Yacht Account Management and Bookkeeping", 
    "Yacht and Catamaran Charters", "Yacht Armor", "Yacht Brokers", 
    "Yacht Builders", "Yacht Crew Placement", "Yacht Dealers", "Yacht Delivery", 
    "Yacht Fire Detection Systems", "Yacht Insurance", "Yacht Management", 
    "Yacht Photography", "Yacht Plumbing", "Yacht Refrigeration & Watermakers", 
    "Yacht Stabilizers & Seakeepers", "Yacht Training", "Yacht Videography", 
    "Yacht Wi-Fi"
]

def validate_service_name(service_name: str) -> bool:
    """
    Validate that a service name is in the approved comprehensive list
    
    Args:
        service_name: Service name to validate
        
    Returns:
        bool: True if service is in approved list, False otherwise
    """
    return service_name.strip() in COMPLETE_SERVICES_LIST


# Global instance for use throughout the application
lead_routing_service = LeadRoutingService()
