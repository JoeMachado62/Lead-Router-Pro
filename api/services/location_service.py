# File: Lead-Router-Pro/api/services/location_service.py

import logging
from typing import Dict, Optional, List
import re
from utils.dependency_manager import get_module, is_available

logger = logging.getLogger(__name__)

class LocationService:
    """
    Service for converting ZIP codes to geographic information.
    Uses pgeocode library for offline, fast, and reliable lookups.
    """
    
    def __init__(self):  # ← Fixed: was **init** (markdown formatting issue)
        """Initialize the geocoding engine for the US."""
        if not is_available('pgeocode'):
            logger.warning("⚠️ LocationService initialized without pgeocode")
            self.geo_us = None
            self.pgeocode_available = False
            return
        
        try:
            pgeocode = get_module('pgeocode')
            self.geo_us = pgeocode.Nominatim('us')
            self.pgeocode_available = True
            logger.info("✅ LocationService initialized with pgeocode")
        except Exception as e:
            logger.error(f"❌ Failed to initialize LocationService: {e}")
            self.geo_us = None
            self.pgeocode_available = False

    def normalize_zip_code(self, zip_code: str) -> str:
        """
        Normalize ZIP code to a 5-digit string.
        """
        if not zip_code or not isinstance(zip_code, str):
            return ""
        return re.sub(r'\D', '', zip_code).zfill(5)[:5]

    def zip_to_location(self, zip_code: str) -> Dict[str, Optional[str]]:
        """
        Convert a ZIP code to its corresponding geographic information.
        """
        if not is_available('pgeocode'):
            return {
                'error': 'pgeocode library not installed. Install with: pip install pgeocode pandas',
                'zip_code': zip_code,
                'requires_installation': True
            }
        
        if not self.geo_us:
            return {'error': 'LocationService not initialized properly'}

        normalized_zip = self.normalize_zip_code(zip_code)
        if not normalized_zip:
            return {'error': f'Invalid ZIP code format: {zip_code}'}

        try:
            location_data = self.geo_us.query_postal_code(normalized_zip)
            
            # Handle pandas checking gracefully
            pd = get_module('pandas')
            if pd and pd.isna(location_data.county_name):
                return {'error': f'ZIP code not found: {normalized_zip}'}
            elif not pd and not location_data.county_name:
                return {'error': f'ZIP code not found: {normalized_zip}'}

            return {
                'state': location_data.state_code,
                'county': location_data.county_name,
                'city': location_data.place_name,
                'zipcode': location_data.postal_code,
                'lat': location_data.latitude,
                'lng': location_data.longitude,
                'accuracy': location_data.accuracy,
                'error': None
            }
        except Exception as e:
            logger.error(f"❌ Error looking up ZIP code {normalized_zip}: {e}")
            return {'error': f'Lookup error: {str(e)}'}

    def get_state_counties(self, state_abbr: str) -> List[str]:
        """
        Get all unique counties for a given state abbreviation.
        """
        if not is_available('pgeocode'):
            logger.warning("⚠️ get_state_counties requires pgeocode installation")
            return []
        
        if not self.geo_us:
            return []
        
        try:
            # pgeocode's underlying data can be accessed for this
            all_data = self.geo_us._data
            state_data = all_data[all_data['state_code'] == state_abbr.upper()]
            return sorted(state_data['county_name'].unique().tolist())
        except Exception as e:
            logger.error(f"❌ Error getting counties for state {state_abbr}: {e}")
            return []

# Global instance for use throughout the application
location_service = LocationService()