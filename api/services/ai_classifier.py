# Enhanced AI Classifier with Simplified Processing
# File: api/services/ai_classifier.py

import json
import logging
from typing import Dict, List, Optional, Set
import re
from api.services.service_categories import service_manager

logger = logging.getLogger(__name__)

class AIServiceClassifier:
    """
    Enhanced marine service classifier with simplified processing for clean form data.
    
    KEY FIX: Preserves original form data when it's already clean (from Elementor forms)
    and only applies AI "enhancement" for truly malformed data.
    """
    
    def __init__(self, industry: str = "marine"):
        self.industry = "marine"
        self.marine_categories = self._load_marine_categories()
        self.service_mappings = self._load_service_mappings()
        self.specific_services_map = self._load_specific_services_map()
        
        logger.info(f"✅ Simplified AIServiceClassifier initialized with {len(self.service_mappings)} mappings")
    
    # ===========================================
    # SIMPLIFIED PROCESSING METHODS (NEW)
    # ===========================================
    
    def is_clean_form_data(self, form_data: Dict) -> bool:
        """
        Determine if form data is already clean and doesn't need AI enhancement.
        
        Clean data criteria:
        1. Has form_identifier (from URL path)
        2. Has specific_service_needed (user selected from dropdown)
        3. Form identifier maps to known category
        """
        form_identifier = form_data.get('form_identifier', '').lower().strip()
        specific_service = form_data.get('specific_service_needed', '').strip()
        
        # Check if form identifier maps to known category
        has_valid_category = False
        for keyword, category in self.service_mappings.items():
            if form_identifier in keyword or keyword in form_identifier:
                has_valid_category = True
                break
        
        is_clean = bool(form_identifier and specific_service and has_valid_category)
        
        logger.info(f"🔍 Form data cleanliness check:")
        logger.info(f"   Form ID: '{form_identifier}' ({'✅' if form_identifier else '❌'})")
        logger.info(f"   Specific Service: '{specific_service}' ({'✅' if specific_service else '❌'})")
        logger.info(f"   Valid Category: {'✅' if has_valid_category else '❌'}")
        logger.info(f"   Result: {'✅ CLEAN' if is_clean else '❌ NEEDS AI'}")
        
        return is_clean
    
    async def classify_service_simplified(self, form_data: Dict) -> Dict:
        """
        SIMPLIFIED classification that preserves original data for clean forms.
        
        This is the KEY FIX - use this instead of classify_service_detailed for clean data.
        """
        form_identifier = form_data.get('form_identifier', '').lower().strip()
        specific_service = form_data.get('specific_service_needed', '').strip()
        
        # Extract coverage area (this part works fine)
        coverage_area = self.extract_coverage_area(form_data)
        
        # Determine priority (this part works fine) 
        priority_level = self._determine_priority(form_data)
        
        # Get category from form identifier (SIMPLE MAPPING)
        category = self._get_category_from_form_identifier(form_identifier)
        
        # Preserve the EXACT specific service (NO AI ENHANCEMENT)
        specific_services = [specific_service] if specific_service else [category]
        
        result = {
            "primary_category": category,
            "confidence": 0.95,  # High confidence for clean data
            "reasoning": f"Direct form mapping: '{form_identifier}' → '{category}', preserving original service: '{specific_service}'",
            "specific_services": specific_services,  # PRESERVE ORIGINAL
            "coverage_area": coverage_area,
            "priority_level": priority_level,
            "service_complexity": "moderate",
            "estimated_duration": "long",
            "requires_emergency_response": False,
            "keywords_found": [form_identifier],
            "alternative_categories": [],
            "processing_method": "simplified"  # Flag to track which method was used
        }
        
        logger.info(f"✅ SIMPLIFIED CLASSIFICATION:")
        logger.info(f"   Input Service: '{specific_service}'")
        logger.info(f"   Output Services: {specific_services}")
        logger.info(f"   Category: {category}")
        logger.info(f"   ✅ PRESERVED ORIGINAL DATA")
        
        return result
    
    def _get_category_from_form_identifier(self, form_identifier: str) -> str:
        """
        Get category directly from form identifier without AI processing.
        """
        # Direct mappings from form identifiers to categories
        identifier_mappings = {
            'engines_generators': 'Engines and Generators',
            'boat_maintenance': 'Boat Maintenance', 
            'marine_systems': 'Marine Systems',
            'boat_yacht_repair': 'Boat and Yacht Repair',
            'boat_hauling_delivery': 'Boat Hauling and Yacht Delivery',
            'boat_towing': 'Boat Towing',
            'boat_charters_rentals': 'Boat Charters and Rentals',
            'buying_selling_boats': 'Buying or Selling a Boat',
            'dock_slip_rental': 'Dock and Slip Rental',
            'docks_seawalls_lifts': 'Docks, Seawalls and Lifts',
            'fuel_delivery': 'Fuel Delivery',
            'boater_resources': 'Boater Resources',
            'maritime_education': 'Maritime Education and Training',
            'waterfront_property': 'Waterfront Property',
            'yacht_management': 'Yacht Management'
        }
        
        # Direct lookup first
        if form_identifier in identifier_mappings:
            return identifier_mappings[form_identifier]
        
        # Partial matching for variations
        for identifier, category in identifier_mappings.items():
            if identifier in form_identifier or form_identifier in identifier:
                return category
        
        # Fallback
        return 'Boat Maintenance'
    
    # ===========================================
    # ENHANCED ROUTING LOGIC (FIXED)
    # ===========================================
    
    async def classify_service_detailed(self, form_data: Dict) -> Dict:
        """
        UPDATED: Enhanced classification that chooses between simplified and AI processing.
        """
        # Check if data is clean and can use simplified processing
        if self.is_clean_form_data(form_data):
            logger.info("🎯 Using SIMPLIFIED processing for clean form data")
            return await self.classify_service_simplified(form_data)
        else:
            logger.info("🤖 Using AI processing for messy/malformed data")
            return await self.classify_service_ai_enhanced(form_data)
    
    async def classify_service_ai_enhanced(self, form_data: Dict) -> Dict:
        """
        AI-enhanced processing for messy/malformed data (existing logic).
        """
        # This is the existing AI logic for handling malformed data
        form_source = form_data.get('form_identifier', '').lower().strip()
        service_requested = form_data.get('specific_service_needed', '').lower().strip()
        special_requests = form_data.get('special_requests__notes', '').lower().strip()
        
        # Extract coverage area
        coverage_area = self.extract_coverage_area(form_data)
        
        # Determine priority level
        priority_level = self._determine_priority(form_data)
        
        # Find primary category using AI
        primary_category = self._find_primary_category(form_source, service_requested, special_requests)
        
        # Find specific services using AI (this was corrupting clean data)
        specific_services = self._find_specific_services_ai(service_requested, special_requests, primary_category)
        
        # Build detailed classification result
        result = {
            "primary_category": primary_category["category"],
            "confidence": primary_category["confidence"],
            "reasoning": primary_category["reasoning"],
            "specific_services": specific_services,
            "coverage_area": coverage_area,
            "priority_level": priority_level,
            "service_complexity": self._determine_complexity(service_requested),
            "estimated_duration": self._estimate_duration(service_requested),
            "requires_emergency_response": self._check_emergency_response(form_data),
            "keywords_found": primary_category.get("keywords_found", []),
            "alternative_categories": self._find_alternative_categories(service_requested, primary_category["category"]),
            "processing_method": "ai_enhanced"
        }
        
        logger.info(f"🤖 AI ENHANCED CLASSIFICATION:")
        logger.info(f"   Primary Category: {result['primary_category']} ({result['confidence']:.0%})")
        logger.info(f"   Specific Services: {result['specific_services']}")
        logger.info(f"   Coverage Area: {result['coverage_area']['zip_code']}")
        logger.info(f"   Priority Level: {result['priority_level']}")
        logger.info(f"   Service Complexity: {result['service_complexity']}")
        
        return result
    
    def _find_specific_services_ai(self, service_requested: str, special_requests: str, primary_category: Dict) -> List[str]:
        """
        AI-enhanced specific service finding (renamed to avoid corrupting clean data).
        """
        specific_services = []
        category_name = primary_category["category"]
        
        # Get all possible services for this category
        available_services = self.specific_services_map.get(category_name, [])
        
        # Search text for specific service mentions
        search_text = f"{service_requested} {special_requests}".lower()
        
        for service in available_services:
            service_lower = service.lower()
            # Check for exact matches or close matches
            if (service_lower in search_text or 
                any(word in search_text for word in service_lower.split() if len(word) > 3)):
                specific_services.append(service)
        
        # If no specific services found, use the primary category as default
        if not specific_services:
            specific_services = [category_name]
        
        return specific_services
    
    # ===========================================
    # LEGACY COMPATIBILITY
    # ===========================================
    
    async def classify_service(self, form_data: Dict) -> Dict:
        """
        Main entry point - maintains backward compatibility.
        """
        # Get detailed classification (now uses simplified path for clean data)
        detailed_result = await self.classify_service_detailed(form_data)
        
        # Convert to legacy format
        legacy_result = {
            "category": detailed_result["primary_category"],
            "confidence": detailed_result["confidence"],
            "reasoning": detailed_result["reasoning"],
            "keywords_found": detailed_result.get("keywords_found", []),
            "alternative_categories": detailed_result.get("alternative_categories", [])
        }
        
        return legacy_result
    
    # ===========================================
    # EXISTING HELPER METHODS (UNCHANGED)
    # ===========================================
    
    def _load_marine_categories(self) -> List[str]:
        """Load the 15 marine service categories"""
        return [
            "Boat Maintenance",
            "Engines and Generators", 
            "Marine Systems",
            "Boat and Yacht Repair",
            "Boat Hauling and Yacht Delivery",
            "Boat Towing",
            "Boat Charters and Rentals",
            "Dock and Slip Rental",
            "Fuel Delivery",
            "Buying or Selling a Boat",
            "Boater Resources",
            "Maritime Education and Training",
            "Yacht Management",
            "Docks, Seawalls and Lifts",
            "Waterfront Property"
        ]
    
    def extract_coverage_area(self, form_data: Dict) -> Dict:
        """Extract geographic coverage information from form data"""
        coverage_info = {
            "zip_code": "",
            "city": "", 
            "state": "",
            "county": "",
            "coverage_type": "zip"
        }
        
        # Primary ZIP code extraction
        zip_fields = ['zip_code_of_service', 'zip_code', 'postal_code', 'zipCode']
        for field in zip_fields:
            zip_value = form_data.get(field, '').strip()
            if zip_value and len(zip_value) >= 5:
                coverage_info["zip_code"] = zip_value[:5]
                break
        
        # Extract from address fields if available
        address_fields = ['address1', 'full_address', 'street_address']
        for field in address_fields:
            address = form_data.get(field, '').strip()
            if address:
                zip_match = re.search(r'\b(\d{5})(-\d{4})?\b', address)
                if zip_match and not coverage_info["zip_code"]:
                    coverage_info["zip_code"] = zip_match.group()
                    break
        
        logger.info(f"🗺️ Extracted coverage area: {coverage_info}")
        return coverage_info
    
    def _find_primary_category(self, form_source: str, service_requested: str, special_requests: str) -> Dict:
        """Find the primary service category with confidence scoring"""
        
        # Step 1: Check form source (90% confidence)
        if form_source and form_source in self.service_mappings:
            return {
                "category": self.service_mappings[form_source],
                "confidence": 0.9,
                "reasoning": f"Exact form source match: '{form_source}'",
                "keywords_found": [form_source]
            }
        
        # Step 2: Check service requested (85% confidence)
        if service_requested and service_requested in self.service_mappings:
            return {
                "category": self.service_mappings[service_requested],
                "confidence": 0.85,
                "reasoning": f"Exact service match: '{service_requested}'",
                "keywords_found": [service_requested]
            }
        
        # Step 3: Keyword matching (70% confidence)
        service_text = f"{service_requested} {special_requests}".lower()
        for keyword, category in self.service_mappings.items():
            if keyword in service_text:
                return {
                    "category": category,
                    "confidence": 0.7,
                    "reasoning": f"Keyword match: '{keyword}' found in service text",
                    "keywords_found": [keyword]
                }
        
        # Default fallback
        return {
            "category": "Boat Maintenance",
            "confidence": 0.3,
            "reasoning": "No matches found - using default category",
            "keywords_found": []
        }
    
    def _determine_priority(self, form_data: Dict) -> str:
        """Determine priority level based on form data"""
        emergency_keywords = ['emergency', 'urgent', 'asap', 'immediate', 'now', 'breakdown', 'sinking', 'stranded']
        
        # Check various text fields for emergency keywords
        text_fields = ['special_requests__notes', 'desired_timeline', 'service_requested']
        
        for field in text_fields:
            text = form_data.get(field, '').lower()
            if any(keyword in text for keyword in emergency_keywords):
                return 'high'
        
        return 'normal'
    
    def _determine_complexity(self, service_requested: str) -> str:
        """Determine service complexity"""
        complex_keywords = ['major', 'overhaul', 'rebuild', 'replacement', 'installation', 'new']
        simple_keywords = ['cleaning', 'inspection', 'maintenance', 'touch-up', 'minor']
        
        service_lower = service_requested.lower()
        
        if any(keyword in service_lower for keyword in complex_keywords):
            return 'complex'
        elif any(keyword in service_lower for keyword in simple_keywords):
            return 'simple'
        else:
            return 'moderate'
    
    def _estimate_duration(self, service_requested: str) -> str:
        """Estimate service duration"""
        quick_keywords = ['inspection', 'cleaning', 'wash', 'touch-up']
        long_keywords = ['overhaul', 'rebuild', 'major', 'installation', 'replacement']
        
        service_lower = service_requested.lower()
        
        if any(keyword in service_lower for keyword in quick_keywords):
            return 'short'
        elif any(keyword in service_lower for keyword in long_keywords):
            return 'long'
        else:
            return 'medium'
    
    def _check_emergency_response(self, form_data: Dict) -> bool:
        """Check if emergency response is required"""
        emergency_indicators = ['emergency', 'urgent', 'breakdown', 'sinking', 'stranded', 'tow']
        
        text_fields = ['special_requests__notes', 'desired_timeline', 'service_requested']
        
        for field in text_fields:
            text = form_data.get(field, '').lower()
            if any(indicator in text for indicator in emergency_indicators):
                return True
        
        return False
    
    def _find_alternative_categories(self, service_requested: str, primary_category: str) -> List[str]:
        """Find alternative categories that might also apply"""
        alternatives = []
        
        service_lower = service_requested.lower()
        
        # Cross-category services
        if any(keyword in service_lower for keyword in ['electric', 'electrical', 'wiring']):
            if primary_category != 'Marine Systems':
                alternatives.append('Marine Systems')
        
        if any(keyword in service_lower for keyword in ['engine', 'motor', 'generator']):
            if primary_category != 'Engines and Generators':
                alternatives.append('Engines and Generators')
        
        if any(keyword in service_lower for keyword in ['repair', 'fix', 'broken']):
            if primary_category != 'Boat and Yacht Repair':
                alternatives.append('Boat and Yacht Repair')
        
        return alternatives[:2]  # Limit to 2 alternatives
    
    def _load_service_mappings(self) -> Dict[str, str]:
        """Load comprehensive service mappings"""
        # This would be your existing service mappings dictionary
        # Keeping it as is since it works for malformed data
        return {
            # Form source mappings
            'engines_generators': 'Engines and Generators',
            'boat_maintenance': 'Boat Maintenance',
            # ... all your existing mappings
        }
    
    def _load_specific_services_map(self) -> Dict[str, List[str]]:
        """Map primary categories to their specific services"""
        # This would be your existing specific services map
        # Keeping it as is since it's only used for AI processing now
        return {
            "Boat Maintenance": [
                "Ceramic Coating",
                "Boat Detailing", 
                "Bottom Cleaning",
                # ... existing services
            ],
            # ... all your existing mappings
        }
