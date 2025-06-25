# api/services/location_service.py

import logging
from typing import Dict, Optional, Tuple
import re

logger = logging.getLogger(__name__)

class LocationService:
    """
    Service for converting ZIP codes to geographic information (state, county, city)
    Uses pyzipcode library for offline ZIP code database lookups
    """
    
    def __init__(self):
        """Initialize the ZIP code search engine"""
        try:
            from pyzipcode import ZipCodeDatabase
            self.zcdb = ZipCodeDatabase()
            logger.info("✅ LocationService initialized with pyzipcode database")
        except Exception as e:
            logger.error(f"❌ Failed to initialize LocationService: {e}")
            self.zcdb = None
    
    def normalize_zip_code(self, zip_code: str) -> str:
        """
        Normalize ZIP code format to 5-digit format
        
        Args:
            zip_code: Raw ZIP code input (may include +4 extension)
            
        Returns:
            Normalized 5-digit ZIP code
        """
        if not zip_code:
            return ""
        
        # Remove any non-digit characters and get first 5 digits
        digits_only = re.sub(r'\D', '', str(zip_code))
        return digits_only[:5] if len(digits_only) >= 5 else digits_only
    
    def zip_to_location(self, zip_code: str) -> Dict[str, Optional[str]]:
        """
        Convert ZIP code to location information
        
        Args:
            zip_code: ZIP code to lookup
            
        Returns:
            Dictionary containing state, county, city, and other location data
        """
        if not self.zcdb:
            logger.error("❌ LocationService not properly initialized")
            return {
                'state': None,
                'county': None,
                'city': None,
                'error': 'LocationService not initialized'
            }
        
        try:
            # Normalize the ZIP code
            normalized_zip = self.normalize_zip_code(zip_code)
            
            if not normalized_zip or len(normalized_zip) < 5:
                logger.warning(f"⚠️ Invalid ZIP code format: {zip_code}")
                return {
                    'state': None,
                    'county': None,
                    'city': None,
                    'error': f'Invalid ZIP code format: {zip_code}'
                }
            
            # Perform the lookup using pyzipcode
            results = self.zcdb[normalized_zip]
            
            if not results:
                logger.warning(f"⚠️ ZIP code not found: {normalized_zip}")
                return {
                    'state': None,
                    'county': None,
                    'city': None,
                    'error': f'ZIP code not found: {normalized_zip}'
                }
            
            # pyzipcode returns a list, get the first result
            result = results[0] if isinstance(results, list) else results
            
            # Extract location information
            location_data = {
                'state': result.state,
                'state_abbr': result.state,
                'county': result.county,
                'city': result.city,
                'zipcode': result.zip,
                'lat': result.latitude,
                'lng': result.longitude,
                'timezone': getattr(result, 'timezone', None),
                'area_code': getattr(result, 'area_code', None),
                'error': None
            }
            
            logger.debug(f"📍 ZIP {normalized_zip} → {location_data['state']}, {location_data['county']} County")
            return location_data
            
        except Exception as e:
            logger.error(f"❌ Error looking up ZIP code {zip_code}: {e}")
            return {
                'state': None,
                'county': None,
                'city': None,
                'error': f'Lookup error: {str(e)}'
            }
    
    def validate_zip_code(self, zip_code: str) -> bool:
        """
        Validate if a ZIP code exists in the database
        
        Args:
            zip_code: ZIP code to validate
            
        Returns:
            True if ZIP code is valid and exists
        """
        location_data = self.zip_to_location(zip_code)
        return location_data.get('error') is None
    
    def get_state_counties(self, state_abbr: str) -> list:
        """
        Get all counties for a given state
        
        Args:
            state_abbr: Two-letter state abbreviation (e.g., 'FL', 'CA')
            
        Returns:
            List of county names in the state
        """
        if not self.zcdb:
            logger.error("❌ LocationService not properly initialized")
            return []
        
        try:
            # pyzipcode doesn't have a direct by_state method, so we'll use a simplified approach
            # This is a basic implementation - could be enhanced with a more comprehensive lookup
            counties = set()
            
            # Sample some ZIP codes to find counties (this is a simplified approach)
            # In a production system, you might want to maintain a separate state-county mapping
            logger.debug(f"📍 Getting counties for {state_abbr} (simplified lookup)")
            
            # For now, return common counties for major states as examples
            state_counties = {
                'FL': ['Broward', 'Miami-Dade', 'Palm Beach', 'Orange', 'Hillsborough', 'Pinellas'],
                'CA': ['Los Angeles', 'Orange', 'San Diego', 'Riverside', 'San Bernardino', 'Ventura'],
                'NY': ['New York', 'Kings', 'Queens', 'Bronx', 'Richmond', 'Nassau'],
                'TX': ['Harris', 'Dallas', 'Tarrant', 'Bexar', 'Travis', 'Collin']
            }
            
            county_list = state_counties.get(state_abbr, [])
            logger.debug(f"📍 Found {len(county_list)} counties in {state_abbr}")
            return county_list
            
        except Exception as e:
            logger.error(f"❌ Error getting counties for state {state_abbr}: {e}")
            return []
    
    def get_zip_codes_in_county(self, state_abbr: str, county_name: str) -> list:
        """
        Get all ZIP codes within a specific county
        
        Args:
            state_abbr: Two-letter state abbreviation
            county_name: County name
            
        Returns:
            List of ZIP codes in the county
        """
        if not self.zcdb:
            logger.error("❌ LocationService not properly initialized")
            return []
        
        try:
            # pyzipcode doesn't have direct county search, so this is a simplified implementation
            # In a production system, you might want to maintain a separate county-ZIP mapping
            logger.debug(f"📍 Getting ZIP codes for {county_name} County, {state_abbr} (simplified lookup)")
            
            # Return empty list for now - this method would need enhancement for full functionality
            # The main zip_to_location method is the primary function needed for lead routing
            return []
            
        except Exception as e:
            logger.error(f"❌ Error getting ZIP codes for {county_name} County, {state_abbr}: {e}")
            return []
    
    def is_zip_in_coverage_area(self, zip_code: str, coverage_type: str, 
                               coverage_areas: list) -> bool:
        """
        Check if a ZIP code falls within specified coverage areas
        
        Args:
            zip_code: ZIP code to check
            coverage_type: Type of coverage ('global', 'national', 'state', 'county', 'zip')
            coverage_areas: List of coverage areas (states, counties, or ZIP codes)
            
        Returns:
            True if ZIP code is covered
        """
        if coverage_type == 'global':
            return True
        
        if coverage_type == 'national':
            # Check if ZIP code is in US (has valid state)
            location_data = self.zip_to_location(zip_code)
            return location_data.get('state') is not None
        
        location_data = self.zip_to_location(zip_code)
        if location_data.get('error'):
            return False
        
        if coverage_type == 'state':
            return location_data.get('state') in coverage_areas
        
        if coverage_type == 'county':
            # Check if the county is in the coverage list
            zip_county = location_data.get('county')
            zip_state = location_data.get('state')
            
            # Coverage areas for counties should be in format "County Name, ST"
            for coverage_area in coverage_areas:
                if ',' in coverage_area:
                    county_part, state_part = coverage_area.split(',', 1)
                    county_part = county_part.strip()
                    state_part = state_part.strip()
                    
                    if (zip_county and zip_county.lower() == county_part.lower() and
                        zip_state and zip_state.lower() == state_part.lower()):
                        return True
                else:
                    # Fallback: just match county name
                    if zip_county and zip_county.lower() == coverage_area.lower():
                        return True
            return False
        
        if coverage_type == 'zip':
            # Direct ZIP code matching
            normalized_zip = self.normalize_zip_code(zip_code)
            normalized_coverage = [self.normalize_zip_code(z) for z in coverage_areas]
            return normalized_zip in normalized_coverage
        
        return False
    
    def get_coverage_summary(self, coverage_type: str, coverage_areas: list) -> str:
        """
        Generate a human-readable summary of coverage areas
        
        Args:
            coverage_type: Type of coverage
            coverage_areas: List of coverage areas
            
        Returns:
            Human-readable coverage summary
        """
        if coverage_type == 'global':
            return "Global coverage (worldwide)"
        
        if coverage_type == 'national':
            return "National coverage (United States)"
        
        if coverage_type == 'state':
            if len(coverage_areas) == 1:
                return f"State coverage: {coverage_areas[0]}"
            elif len(coverage_areas) <= 3:
                return f"State coverage: {', '.join(coverage_areas)}"
            else:
                return f"State coverage: {len(coverage_areas)} states"
        
        if coverage_type == 'county':
            if len(coverage_areas) == 1:
                return f"County coverage: {coverage_areas[0]}"
            elif len(coverage_areas) <= 3:
                return f"County coverage: {', '.join(coverage_areas)}"
            else:
                return f"County coverage: {len(coverage_areas)} counties"
        
        if coverage_type == 'zip':
            if len(coverage_areas) <= 5:
                return f"ZIP code coverage: {', '.join(coverage_areas)}"
            else:
                return f"ZIP code coverage: {len(coverage_areas)} ZIP codes"
        
        return f"Coverage: {coverage_type}"


# Global instance for use throughout the application
location_service = LocationService()
