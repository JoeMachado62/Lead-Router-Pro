# api/services/lead_routing_service.py

import logging
import random
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from api.services.location_service import location_service
from database.simple_connection import db as simple_db_instance

logger = logging.getLogger(__name__)

class LeadRoutingService:
    """
    Enhanced lead routing service that supports:
    - Geographic coverage types (global, national, state, county, zip)
    - Dual routing methods (round-robin vs performance-based)
    - Configurable routing distribution percentages
    """
    
    def __init__(self):
        self.location_service = location_service
    
    def find_matching_vendors(self, account_id: str, service_category: str, 
                            zip_code: str, priority: str = "normal") -> List[Dict[str, Any]]:
        """
        Find all vendors that can serve the specified location and service category
        
        Args:
            account_id: Account ID to search within
            service_category: Service category requested
            zip_code: ZIP code where service is needed
            priority: Priority level of the request
            
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
            all_vendors = simple_db_instance.get_vendors(account_id=account_id)
            eligible_vendors = []
            
            for vendor in all_vendors:
                # Check if vendor is active and taking new work
                if vendor.get("status") != "active" or not vendor.get("taking_new_work", False):
                    logger.debug(f"Skipping vendor {vendor.get('name')} - not active or not taking work")
                    continue
                
                # Check if vendor provides this service category
                if not self._vendor_matches_service(vendor, service_category):
                    logger.debug(f"Skipping vendor {vendor.get('name')} - service mismatch")
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
            
            logger.info(f"🎯 Found {len(eligible_vendors)} eligible vendors for {service_category} in {zip_code}")
            return eligible_vendors
            
        except Exception as e:
            logger.error(f"❌ Error finding matching vendors: {e}")
            return []
    
    def _vendor_matches_service(self, vendor: Dict[str, Any], service_category: str) -> bool:
        """
        Check if vendor provides the requested service category
        
        Args:
            vendor: Vendor data
            service_category: Requested service category
            
        Returns:
            True if vendor provides this service
        """
        services_provided = vendor.get("services_provided", [])
        if isinstance(services_provided, str):
            services_provided = [s.strip() for s in services_provided.split(',')]
        
        # Simple service matching (can be enhanced with AI later)
        service_category_lower = service_category.lower()
        for service in services_provided:
            service_lower = service.lower()
            if (service_category_lower in service_lower or 
                service_lower in service_category_lower or
                self._services_are_related(service_category_lower, service_lower)):
                return True
        
        return False
    
    def _services_are_related(self, requested: str, provided: str) -> bool:
        """
        Check if two services are related (basic keyword matching)
        This can be enhanced with more sophisticated matching logic
        """
        # Basic keyword matching for marine services
        marine_service_groups = {
            'maintenance': ['maintenance', 'cleaning', 'detailing', 'wash', 'wax', 'service'],
            'repair': ['repair', 'fix', 'restoration', 'fiberglass', 'welding'],
            'engine': ['engine', 'motor', 'outboard', 'inboard', 'generator'],
            'electrical': ['electrical', 'electronics', 'wiring', 'instrument'],
            'marine_systems': ['plumbing', 'hvac', 'ac', 'systems', 'refrigeration'],
            'transport': ['delivery', 'transport', 'hauling', 'towing', 'tow'],
            'charter': ['charter', 'rental', 'fishing', 'boat_rental']
        }
        
        for group_services in marine_service_groups.values():
            if (any(keyword in requested for keyword in group_services) and 
                any(keyword in provided for keyword in group_services)):
                return True
        
        return False
    
    def _vendor_covers_location(self, vendor: Dict[str, Any], zip_code: str, 
                              target_state: Optional[str], target_county: Optional[str]) -> bool:
        """
        Check if vendor covers the specified location based on their coverage type
        
        Args:
            vendor: Vendor data
            zip_code: ZIP code to check
            target_state: State of the ZIP code
            target_county: County of the ZIP code
            
        Returns:
            True if vendor covers this location
        """
        coverage_type = vendor.get('service_coverage_type', 'zip')
        
        if coverage_type == 'global':
            return True
        
        if coverage_type == 'national':
            # Check if ZIP code is in US (has valid state)
            return target_state is not None
        
        if coverage_type == 'state':
            if not target_state:
                return False
            service_states = vendor.get('service_states', [])
            return target_state in service_states
        
        if coverage_type == 'county':
            if not target_county or not target_state:
                return False
            service_counties = vendor.get('service_counties', [])
            
            # Check for county matches (format: "County Name, ST" or just "County Name")
            for coverage_area in service_counties:
                if ',' in coverage_area:
                    county_part, state_part = coverage_area.split(',', 1)
                    county_part = county_part.strip()
                    state_part = state_part.strip()
                    
                    if (target_county.lower() == county_part.lower() and
                        target_state.lower() == state_part.lower()):
                        return True
                else:
                    # Fallback: just match county name
                    if target_county.lower() == coverage_area.strip().lower():
                        return True
            return False
        
        if coverage_type == 'zip':
            # Legacy ZIP code matching
            service_areas = vendor.get('service_areas', [])
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
        """
        coverage_type = vendor.get('service_coverage_type', 'zip')
        
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
                v.get('last_lead_assigned', '1900-01-01')  # Older assignment first for ties
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
            key=lambda v: v.get('last_lead_assigned', '1900-01-01')
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
                coverage_type = vendor.get('service_coverage_type', 'zip')
                coverage_stats[coverage_type] = coverage_stats.get(coverage_type, 0) + 1
            
            # Get recent lead assignments (would need to track this in activity log)
            # For now, return basic stats
            
            return {
                'routing_configuration': config,
                'total_vendors': len(vendors),
                'active_vendors': len([v for v in vendors if v.get('status') == 'active']),
                'vendors_taking_work': len([v for v in vendors if v.get('taking_new_work', False)]),
                'coverage_distribution': coverage_stats,
                'location_service_status': 'active' if self.location_service.zcdb else 'inactive'
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting routing stats for account {account_id}: {e}")
            return {}


# Global instance for use throughout the application
lead_routing_service = LeadRoutingService()
