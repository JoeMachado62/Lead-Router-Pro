# api/services/lead_routing_service.py

import logging
import random
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
            all_vendors = self._get_vendors_from_new_schema(account_id)
            eligible_vendors = []
            
            for vendor in all_vendors:
                # Check if vendor is active and taking new work
                if vendor.get("status") != "active" or not vendor.get("taking_new_work", False):
                    logger.debug(f"Skipping vendor {vendor.get('name')} - not active or not taking work")
                    continue
                
                # Multi-level service matching: try exact matching first, then fallback
                if specific_service:
                    # Try exact service matching first
                    if self._vendor_matches_service_exact(vendor, service_category, specific_service):
                        logger.debug(f"✅ Vendor {vendor.get('name')} - EXACT service match: {specific_service}")
                    elif self._vendor_matches_service_legacy(vendor, service_category):
                        logger.debug(f"⚠️ Vendor {vendor.get('name')} - FALLBACK category match only: {service_category}")
                    else:
                        logger.debug(f"Skipping vendor {vendor.get('name')} - no service match")
                        continue
                else:
                    # No specific service provided, use legacy category matching
                    if not self._vendor_matches_service_legacy(vendor, service_category):
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
    
    def _get_vendors_from_new_schema(self, account_id: str) -> List[Dict[str, Any]]:
        """
        Get vendors from the new database schema with proper field mappings.
        UPDATED: Works with new column names (services_offered, coverage_counties, etc.)
        """
        try:
            import sqlite3
            import json
            
            conn = sqlite3.connect('smart_lead_router.db')
            cursor = conn.cursor()
            
            # Query vendors with new schema column names
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
                    'services_offered': json.loads(row[9]) if row[9] else [],  # NEW COLUMN NAME
                    'coverage_type': row[10] or 'county',
                    'coverage_states': json.loads(row[11]) if row[11] else [],
                    'coverage_counties': json.loads(row[12]) if row[12] else [],  # NEW COLUMN NAME
                    'last_lead_assigned': row[13],
                    'lead_close_percentage': row[14] or 0.0,
                    'status': row[15] or 'active',
                    'taking_new_work': bool(row[16]) if row[16] is not None else True,
                    
                    # Map to old field names for backward compatibility
                    'services_provided': json.loads(row[9]) if row[9] else [],  # Map services_offered → services_provided
                    'service_coverage_type': row[10] or 'county',  # Map coverage_type → service_coverage_type
                    'service_counties': json.loads(row[12]) if row[12] else [],  # Map coverage_counties → service_counties
                    'service_states': json.loads(row[11]) if row[11] else []  # Map coverage_states → service_states
                }
                vendors.append(vendor)
            
            conn.close()
            logger.debug(f"📊 Retrieved {len(vendors)} vendors from new schema for account {account_id}")
            return vendors
            
        except Exception as e:
            logger.error(f"❌ Error getting vendors from new schema: {e}")
            return []
    
    def _vendor_matches_service_exact(self, vendor: Dict[str, Any], 
                                    primary_category: str, specific_service: str) -> bool:
        """
        NEW: Check if vendor matches both primary category AND specific service exactly.
        This is the core method for multi-level routing precision.
        """
        # Get vendor services as list
        services_provided = self._get_vendor_services_list(vendor)
        
        # Use service_manager for exact matching
        return service_manager.vendor_matches_service_exact(
            services_provided, primary_category, specific_service
        )
    
    def _vendor_matches_service_legacy(self, vendor: Dict[str, Any], service_category: str) -> bool:
        """
        LEGACY: Check if vendor provides the requested service category (fallback method).
        Renamed from _vendor_matches_service for clarity. Used when no specific service 
        is provided or when exact matching finds no results.
        """
        services_provided = self._get_vendor_services_list(vendor)
        
        # Try service_manager category matching first
        if service_manager.vendor_matches_category_only(services_provided, service_category):
            return True
        
        # Fallback to legacy keyword matching for backward compatibility
        service_category_lower = service_category.lower()
        for service in services_provided:
            service_lower = service.lower()
            if (service_category_lower in service_lower or 
                service_lower in service_category_lower or
                self._services_are_related(service_category_lower, service_lower)):
                return True
        
        return False
    
    def _get_vendor_services_list(self, vendor: Dict[str, Any]) -> List[str]:
        """
        Helper method to get vendor services as a clean list.
        Handles various data formats and validates the structure.
        """
        services_provided = vendor.get("services_provided", [])
        
        # Handle different data formats
        if isinstance(services_provided, str):
            # If it's a string, split it into a list
            services_provided = [s.strip() for s in services_provided.split(',')]
        elif not isinstance(services_provided, list):
            # If it's still not a list, treat it as no services provided
            logger.warning(f"Vendor {vendor.get('name')} has malformed services_provided: {services_provided}")
            return []
        
        # Clean and filter the list
        cleaned_services = []
        for service in services_provided:
            if service and isinstance(service, str):
                cleaned_service = service.strip()
                if cleaned_service:  # Only add non-empty services
                    cleaned_services.append(cleaned_service)
        
        return cleaned_services
    
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
                logger.warning(f"Vendor {vendor.get('name')} has malformed service_states: {service_states}")
                return False
            return target_state in service_states
        
        if coverage_type == 'county':
            if not target_county or not target_state:
                return False
            service_counties = vendor.get('service_counties', [])
            if not isinstance(service_counties, list):
                logger.warning(f"Vendor {vendor.get('name')} has malformed service_counties: {service_counties}")
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
                'location_service_status': 'active' if self.location_service.geo_us else 'inactive'
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting routing stats for account {account_id}: {e}")
            return {}


# Global instance for use throughout the application
lead_routing_service = LeadRoutingService()
