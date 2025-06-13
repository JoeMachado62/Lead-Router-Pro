# api/services/field_mapper.py

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

class FieldMapper:
    """
    Central field mapping service for dynamic field name translation.
    Supports industry-specific mappings and default fallbacks.
    """
    
    def __init__(self, file_path: str = "field_mappings.json"):
        self._file_path = Path(file_path)
        self._mappings = {}
        self.load_mappings()
    
    def load_mappings(self):
        """Load field mappings from JSON file"""
        try:
            if self._file_path.exists():
                with open(self._file_path, 'r') as f:
                    self._mappings = json.load(f)
                logger.info(f"✅ Loaded field mappings from {self._file_path}")
            else:
                # Initialize with default mappings based on current DSP system
                self._mappings = {
                    "default_mappings": {
                        # Common form field variations to GHL standard names
                        "ServiceNeeded": "specific_service_needed",
                        "serviceNeeded": "specific_service_needed",
                        "service_needed": "specific_service_needed",
                        "zipCode": "zip_code_of_service",
                        "zip_code": "zip_code_of_service",
                        "serviceZipCode": "zip_code_of_service",
                        "vesselMake": "vessel_make",
                        "vessel_make": "vessel_make",
                        "boatMake": "vessel_make",
                        "vesselModel": "vessel_model",
                        "vessel_model": "vessel_model",
                        "boatModel": "vessel_model",
                        "vesselYear": "vessel_year",
                        "vessel_year": "vessel_year",
                        "boatYear": "vessel_year",
                        "vesselLength": "vessel_length_ft",
                        "vessel_length": "vessel_length_ft",
                        "boatLength": "vessel_length_ft",
                        "vesselLocation": "vessel_location__slip",
                        "vessel_location": "vessel_location__slip",
                        "boatLocation": "vessel_location__slip",
                        "specialRequests": "special_requests__notes",
                        "special_requests": "special_requests__notes",
                        "notes": "special_requests__notes",
                        "preferredContact": "preferred_contact_method",
                        "preferred_contact": "preferred_contact_method",
                        "contactMethod": "preferred_contact_method",
                        "desiredTimeline": "desired_timeline",
                        "desired_timeline": "desired_timeline",
                        "timeline": "desired_timeline",
                        "budgetRange": "budget_range",
                        "budget_range": "budget_range",
                        "budget": "budget_range"
                    },
                    "industry_specific": {
                        "marine": {
                            # Marine-specific mappings
                            "boatType": "vessel_make",
                            "yachtMake": "vessel_make",
                            "marineMake": "vessel_make",
                            "dockLocation": "vessel_location__slip",
                            "marinaName": "vessel_location__slip",
                            "emergencyTow": "need_emergency_tow",
                            "towService": "need_emergency_tow"
                        },
                        "automotive": {
                            # Example automotive mappings for future use
                            "vehicleMake": "vehicle_make",
                            "carMake": "vehicle_make",
                            "vehicleModel": "vehicle_model",
                            "carModel": "vehicle_model"
                        }
                    },
                    "reverse_mappings": {},  # For GHL to form field mapping
                    "metadata": {
                        "version": "1.0",
                        "created": "2025-06-13",
                        "description": "Dynamic field mapping system for multi-industry lead routing"
                    }
                }
                self.save_mappings()
                logger.info("🔧 Created default field mappings")
        except Exception as e:
            logger.error(f"❌ Error loading field mappings: {e}")
            self._mappings = {"default_mappings": {}, "industry_specific": {}}
    
    def save_mappings(self):
        """Save current mappings to JSON file"""
        try:
            with open(self._file_path, 'w') as f:
                json.dump(self._mappings, f, indent=2)
            logger.info(f"💾 Saved field mappings to {self._file_path}")
        except Exception as e:
            logger.error(f"❌ Error saving field mappings: {e}")
    
    def get_mapping(self, field_name: str, industry: str = "marine") -> str:
        """
        Get the mapped field name for a given input field name.
        
        Args:
            field_name: Original field name from form
            industry: Industry context for specific mappings
            
        Returns:
            Mapped field name or original if no mapping exists
        """
        if not field_name:
            return field_name
        
        # Check industry-specific mappings first
        industry_mappings = self._mappings.get("industry_specific", {}).get(industry, {})
        if field_name in industry_mappings:
            mapped = industry_mappings[field_name]
            logger.debug(f"🔄 Industry mapping: {field_name} -> {mapped} (industry: {industry})")
            return mapped
        
        # Check default mappings
        default_mappings = self._mappings.get("default_mappings", {})
        if field_name in default_mappings:
            mapped = default_mappings[field_name]
            logger.debug(f"🔄 Default mapping: {field_name} -> {mapped}")
            return mapped
        
        # Return original if no mapping found
        logger.debug(f"➡️ No mapping found for '{field_name}', using original")
        return field_name
    
    def add_mapping(self, source_field: str, target_field: str, industry: Optional[str] = None):
        """Add a new field mapping"""
        if industry:
            if "industry_specific" not in self._mappings:
                self._mappings["industry_specific"] = {}
            if industry not in self._mappings["industry_specific"]:
                self._mappings["industry_specific"][industry] = {}
            self._mappings["industry_specific"][industry][source_field] = target_field
            logger.info(f"➕ Added industry mapping: {source_field} -> {target_field} (industry: {industry})")
        else:
            if "default_mappings" not in self._mappings:
                self._mappings["default_mappings"] = {}
            self._mappings["default_mappings"][source_field] = target_field
            logger.info(f"➕ Added default mapping: {source_field} -> {target_field}")
        
        self.save_mappings()
    
    def remove_mapping(self, source_field: str, industry: Optional[str] = None):
        """Remove a field mapping"""
        if industry:
            industry_mappings = self._mappings.get("industry_specific", {}).get(industry, {})
            if source_field in industry_mappings:
                del industry_mappings[source_field]
                logger.info(f"🗑️ Removed industry mapping: {source_field} (industry: {industry})")
        else:
            default_mappings = self._mappings.get("default_mappings", {})
            if source_field in default_mappings:
                del default_mappings[source_field]
                logger.info(f"🗑️ Removed default mapping: {source_field}")
        
        self.save_mappings()
    
    def get_all_mappings(self) -> Dict[str, Any]:
        """Get all current mappings"""
        return self._mappings.copy()
    
    def update_mappings(self, new_mappings: Dict[str, Any]):
        """Update all mappings with new data"""
        self._mappings = new_mappings
        self.save_mappings()
        logger.info("🔄 Updated all field mappings")
    
    def map_payload(self, payload: Dict[str, Any], industry: str = "marine") -> Dict[str, Any]:
        """
        Map an entire payload using field mappings.
        
        Args:
            payload: Original payload with potentially unmapped field names
            industry: Industry context for mappings
            
        Returns:
            New payload with mapped field names
        """
        mapped_payload = {}
        mapping_log = []
        
        for field_name, value in payload.items():
            mapped_name = self.get_mapping(field_name, industry)
            mapped_payload[mapped_name] = value
            
            if mapped_name != field_name:
                mapping_log.append(f"{field_name} -> {mapped_name}")
        
        if mapping_log:
            logger.info(f"🔄 Applied field mappings: {', '.join(mapping_log)}")
        
        return mapped_payload
    
    def get_reverse_mapping(self, ghl_field_name: str, industry: str = "marine") -> str:
        """
        Get the form field name that maps to a given GHL field.
        Useful for generating forms or documentation.
        """
        # Check industry-specific reverse mappings
        industry_mappings = self._mappings.get("industry_specific", {}).get(industry, {})
        for form_field, ghl_field in industry_mappings.items():
            if ghl_field == ghl_field_name:
                return form_field
        
        # Check default reverse mappings
        default_mappings = self._mappings.get("default_mappings", {})
        for form_field, ghl_field in default_mappings.items():
            if ghl_field == ghl_field_name:
                return form_field
        
        return ghl_field_name
    
    def get_mapping_stats(self) -> Dict[str, int]:
        """Get statistics about current mappings"""
        default_count = len(self._mappings.get("default_mappings", {}))
        industry_count = sum(
            len(mappings) for mappings in self._mappings.get("industry_specific", {}).values()
        )
        
        return {
            "total_mappings": default_count + industry_count,
            "default_mappings": default_count,
            "industry_mappings": industry_count,
            "industries": len(self._mappings.get("industry_specific", {}))
        }


# Global singleton instance
field_mapper = FieldMapper()
