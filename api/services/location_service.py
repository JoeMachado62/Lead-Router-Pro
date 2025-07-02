# api/services/location_service.py

import logging
from typing import Dict, Optional, List
import re
import pgeocode
import pandas as pd

logger = logging.getLogger(__name__)

class LocationService:
    """
    Service for converting ZIP codes to geographic information.
    Uses pgeocode library for offline, fast, and reliable lookups.
    """
    
    def __init__(self):
        """Initialize the geocoding engine for the US."""
        try:
            # pgeocode automatically downloads data on first use.
            # We initialize it for the United States.
            self.geo_us = pgeocode.Nominatim('us')
            logger.info("✅ LocationService initialized with pgeocode for US lookups.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize LocationService with pgeocode: {e}")
            self.geo_us = None

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
        if not self.geo_us:
            return {'error': 'LocationService not initialized'}

        normalized_zip = self.normalize_zip_code(zip_code)
        if not normalized_zip:
            return {'error': f'Invalid ZIP code format: {zip_code}'}

        try:
            location_data = self.geo_us.query_postal_code(normalized_zip)
            
            if pd.isna(location_data.county_name):
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
