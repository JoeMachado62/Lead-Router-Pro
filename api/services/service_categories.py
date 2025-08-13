"""
Service Categories - Single Source of Truth (FIXED VERSION)
Multi-level service routing system with complete service hierarchy.

This module contains the definitive service hierarchy with Level 3 services
and is the ONLY source for service category and specific service definitions.

Updated to include:
- Complete service listings from dashboard
- Level 3 service definitions
- Service aliases for better matching
- Fuzzy matching capabilities
"""

import json
import logging
from typing import Dict, List, Optional, Set, Tuple
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

# SERVICE HIERARCHY - COMPLETE SINGLE SOURCE OF TRUTH
# This data structure now includes ALL services from the dashboard
# with proper subcategories and Level 3 services where applicable
SERVICE_CATEGORIES = {
    "Boat Maintenance": [
        "Ceramic Coating",
        "Boat Detailing", 
        "Bottom Cleaning",
        "Oil Change",
        "Boat Oil Change",  # Alias
        "Bilge Cleaning",
        "Boat Bilge Cleaning",  # Alias
        "Jet Ski Maintenance",
        "Barnacle Cleaning",
        "Fire Detection Systems",
        "Yacht Fire Detection Systems",  # Alias
        "Boat Wrapping or Marine Protection Film",
        "Boat Wrapping and Marine Protection Film",  # Alias
        "Boat Wrapping",  # Alias
        "Marine Protection Film",  # Alias
        "Boat and Yacht Maintenance",
        "Yacht Armor",
        "Other"
    ],
    "Boat and Yacht Repair": [
        "Fiberglass Repair",
        "Welding & Metal Fabrication",
        "Welding and Metal Fabrication",  # Alias
        "Carpentry & Woodwork",
        "Carpentry and Woodwork",  # Alias
        "Teak or Woodwork",
        "Riggers & Masts",
        "Riggers and Masts",  # Alias
        "Jet Ski Repair",
        "Canvas or Upholstery",
        "Boat Canvas and Upholstery",  # Alias
        "Boat Decking",
        "Boat Decking and Yacht Flooring",  # Alias
        "Yacht Flooring",  # Alias
        "Other"
    ],
    "Engines and Generators": [
        "Outboard Engine Service",
        "Outboard Engine Sales",
        "Inboard Engine Service", 
        "Inboard Engine Sales",
        "Diesel Engine Service",
        "Diesel Engine Sales",
        "Generator Service",
        "Generator Service and Repair",  # Alias
        "Generator Sales",
        "Engine Service",  # Generic aliases
        "Engine Sales",
        "Engine Service or Sales"
    ],
    "Marine Systems": [
        "Stabilizers or Seakeepers",
        "Yacht Stabilizers and Seakeepers",  # Alias
        "Yacht Stabilizers & Seakeepers",  # Alias
        "Instrument Panel and Dashboard",
        "Instrument Panel",  # Alias
        "Dashboard",  # Alias
        "AC Sales or Service",
        "Yacht AC Sales",
        "Yacht AC Service",
        "Electrical Service",
        "Boat Electrical Service",
        "Sound System",
        "Boat Sound Systems",
        "Plumbing",
        "Yacht Plumbing",
        "Lighting",
        "Boat Lighting",
        "Refrigeration or Watermakers",
        "Yacht Refrigeration and Watermakers",  # Alias
        "Yacht Refrigeration & Watermakers",  # Alias
        "Yacht Refrigeration",  # Alias
        "Watermakers",  # Alias
        "Marine Systems Install and Sales"  # Generic
    ],
    "Boat Charters and Rentals": [
        "Weekly or Monthly Yacht or Catamaran Charter",
        "Daily Yacht or Catamaran Charter",
        "Yacht and Catamaran Charters",  # Alias
        "Yacht Charters",  # Alias
        "Catamaran Charters",  # Alias
        "Sailboat Charter",
        "Sailboat Charters",  # Alias
        "Fishing Charter",
        "Fishing Charters",  # Alias
        "Party Boat Charter",
        "Pontoon Charter",
        "Jet Ski Rental",
        "Paddleboard Rental",
        "Kayak Rental",
        "eFoil, Kiteboarding or Wing Surfing Lessons",
        "eFoil Lessons",  # Alias
        "Kiteboarding Lessons",  # Alias
        "Wing Surfing Lessons",  # Alias
        "eFoil, Kiteboarding & Wing Surfing",  # Alias
        "Boat Club",
        "Boat Clubs",  # Alias
        "Boat Charters and Rentals",  # Generic
        "Dive Equipment and Services",
        "Dive Equipment",  # Alias
        "Dive Services"  # Alias
    ],
    "Docks, Seawalls and Lifts": [
        "Dock and Seawall Builders or Repair",
        "Dock Builders",  # Alias
        "Seawall Builders",  # Alias
        "Dock Repair",  # Alias
        "Seawall Repair",  # Alias
        "Boat Lift Installers",
        "Boat Lift",  # Alias
        "Floating Dock Sales",
        "Floating Docks",  # Alias
        "Davit and Hydraulic Platform",
        "Davit & Hydraulic Platform",  # Alias
        "Hull Dock Seawall or Piling Cleaning",  # Alias
        "Seawall or Piling Cleaning",  # Alias
        "Piling Cleaning"  # Alias
    ],
    "Boat Towing": [
        "Get Emergency Tow",
        "Emergency Tow",  # Alias
        "Emergency Towing",  # Alias
        "Get Towing Membership",
        "Towing Membership"  # Alias
    ],
    "Fuel Delivery": [
        "Dyed Diesel Fuel (For Boats)",
        "Regular Diesel Fuel (Landside Business)",
        "Rec 90 (Ethanol Free Gas)",
        "Fuel Delivery",  # Generic
        "Diesel Delivery",  # Alias
        "Gasoline Delivery"  # Alias
    ],
    "Dock and Slip Rental": [
        "Private Dock",
        "Boat Slip",
        "Marina",
        "Mooring Ball",
        "Dock and Slip Rental",  # Generic
        "Dock Rental",  # Alias
        "Slip Rental",  # Alias
        "Rent My Dock"
    ],
    "Yacht Management": [
        "Full Service Vessel Management",
        "Full Service Yacht Management",  # Alias
        "Technical Management",
        "Crew Management",
        "Accounting & Financial Management",
        "Accounting and Financial Management",  # Alias
        "Insurance & Risk Management",
        "Insurance and Risk Management",  # Alias
        "Regulatory Compliance",
        "Yacht Management"  # Generic
    ],
    "Boater Resources": [
        "Boat or Yacht Parts",
        "Boat and Yacht Parts",  # Alias
        "Boat Parts",  # Alias
        "Yacht Parts",  # Alias
        "Vessel WiFi or Communications",
        "Yacht Wi-Fi",  # Alias
        "Yacht WiFi",  # Alias
        "Vessel WiFi",  # Alias
        "Provisioning",
        "Boat Salvage",
        "Photography or Videography",
        "Yacht Photography",  # Alias
        "Yacht Videography",  # Alias
        "Crew Management",
        "Yacht Crew Placement",  # Alias
        "Account Management and Bookkeeping",
        "Yacht Account Management and Bookkeeping",  # Alias
        "Marketing or Web Design",
        "Maritime Advertising",  # Alias
        "Maritime PR",  # Alias
        "Maritime Web Design"  # Alias
    ],
    "Buying or Selling a Boat": [
        "Boat Insurance",
        "Yacht Insurance", 
        "Yacht Broker",
        "Yacht Brokers",  # Alias
        "Boat Broker",
        "Boat Brokers",  # Alias
        "Boat Financing",
        "Boat Surveyors",
        "Yacht Dealers",
        "Boat Dealers",
        "Boat Builders",
        "Yacht Builders",
        "Buying or Selling a Boat"  # Generic
    ],
    "Maritime Education and Training": [
        "Yacht, Sailboat or Catamaran On Water Training",
        "On Water Training",  # Alias
        "Interested In Buying a Boat/Insurance Signoff",
        "Insurance Signoff",  # Alias
        "Maritime Academy",
        "Sailing Schools",
        "Captains License",
        "Captain's License",  # Alias
        "Maritime Certification",
        "Yacht Training",
        "Maritime Education and Training"  # Generic
    ],
    "Waterfront Property": [
        "Buy a Waterfront Home or Condo",
        "Waterfront Homes for Sale",  # Alias
        "Waterfront Homes For Sale",  # Alias
        "Sell a Waterfront Home or Condo",
        "Sell Your Waterfront Home",  # Alias
        "Buy a Waterfront New Development",
        "Waterfront New Developments",  # Alias
        "New Waterfront Developments",  # Alias
        "Rent a Waterfront Property",
        "Waterfront Rentals"  # Alias
    ],
    "Wholesale or Dealer Product Pricing": [
        "Apparel",
        "Boat Accessories",
        "Boat Maintenance & Cleaning Products",
        "Boat Maintenance and Cleaning Products",  # Alias
        "Boat Safety Products",
        "Diving Equipment",
        "Dock Accessories",
        "Fishing Gear",
        "Personal Watercraft",
        "Marine Electronics",  # Additional from old version
        "Engine Parts",  # Additional
        "Navigation Equipment",  # Additional
        "Wholesale or Dealer Product Pricing",  # Generic
        "Other"
    ],
    "Boat Hauling and Yacht Delivery": [
        "Yacht Delivery",
        "Boat Hauling and Transport",
        "Boat Hauling",  # Alias
        "Boat Transport",  # Alias
        "Local Boat Hauling",  # Alias
        "Long Distance Transport",  # Alias
        "International Yacht Delivery"  # Alias
    ]
}

# LEVEL 3 SERVICES - For categories with additional detail levels
LEVEL_3_SERVICES = {
    "Boat and Yacht Repair": {
        "Fiberglass Repair": [
            "Hull Crack or Structural Repair",
            "Gelcoat Repair and Color Matching",
            "Transom Repair & Reinforcement",
            "Deck Delamination & Soft Spot Repair",
            "Stringer & Bulkhead Repair",
            "Other"
        ],
        "Welding & Metal Fabrication": [
            "Aluminum or Stainless Steel Hull Repairs",
            "Custom Railings, Ladders or Boarding Equipment",
            "T-Tops, Hardtops or Bimini Frames",
            "Fuel or Water Tank Fabrication",
            "Exhaust, Engine Bed or Structural Reinforcement",
            "Other"
        ],
        "Welding and Metal Fabrication": [  # Alias
            "Aluminum or Stainless Steel Hull Repairs",
            "Custom Railings, Ladders or Boarding Equipment",
            "T-Tops, Hardtops or Bimini Frames",
            "Fuel or Water Tank Fabrication",
            "Exhaust, Engine Bed or Structural Reinforcement",
            "Other"
        ],
        "Canvas or Upholstery": [
            "Upholstery",
            "Canvas or Sunshade",
            "Trim and Finish",
            "Boat Cover or T-Top",
            "Acrylic or Strataglass Enclosures",
            "Other"
        ],
        "Boat Canvas and Upholstery": [  # Alias
            "Upholstery",
            "Canvas or Sunshade", 
            "Trim and Finish",
            "Boat Cover or T-Top",
            "Acrylic or Strataglass Enclosures",
            "Other"
        ],
        "Boat Decking": [
            "SeaDek",
            "Real Teak Wood",
            "Cork",
            "Synthetic Teak",
            "Vinyl Flooring",
            "Tile Flooring",
            "Other"
        ]
    },
    "Engines and Generators": {
        "Generator Service": [
            "Generator Installation",
            "Routine Generator Maintenance",
            "Electrical System Integration & Transfer Switches",
            "Diagnostics & Repairs",
            "Sound Shielding & Vibration Control"
        ],
        "Outboard Engine Service": [
            "New Engine Sales",
            "Engine Refit",
            "Routine Engine Maintenance",
            "Cooling System Service",
            "Fuel System Cleaning & Repair",
            "Engine Diagnostics & Troubleshooting"
        ]
    },
    "Marine Systems": {
        "AC Sales or Service": [
            "New AC Install or Replacement",
            "AC Maintenance & Servicing",
            "Refrigerant Charging & Leak Repair",
            "Pump & Water Flow Troubleshooting",
            "Thermostat & Control Panel Upgrades"
        ],
        "Electrical Service": [
            "Battery System Install or Maintenance",
            "Wiring & Rewiring",
            "Shore Power & Inverter Systems",
            "Lighting Systems",
            "Electrical Panel & Breaker",
            "Navigation & Communication",
            "Generator Electrical Integration",
            "Solar Power & Battery Charging"
        ],
        "Boat Electrical Service": [  # Alias
            "Battery System Install or Maintenance",
            "Wiring & Rewiring",
            "Shore Power & Inverter Systems",
            "Lighting Systems",
            "Electrical Panel & Breaker",
            "Navigation & Communication",
            "Generator Electrical Integration",
            "Solar Power & Battery Charging"
        ]
    },
    "Boat Charters and Rentals": {
        "Fishing Charter": [
            "Inshore Fishing Charter",
            "Offshore (Deep Sea) Fishing Charter",
            "Reef & Wreck Fishing Charter",
            "Drift Boat Charter",
            "Freshwater Fishing Charter",
            "Private Party Boat Charter"
        ],
        "Fishing Charters": [  # Alias
            "Inshore Fishing Charter",
            "Offshore (Deep Sea) Fishing Charter",
            "Reef & Wreck Fishing Charter",
            "Drift Boat Charter",
            "Freshwater Fishing Charter",
            "Private Party Boat Charter"
        ]
    },
    "Docks, Seawalls and Lifts": {
        "Dock and Seawall Builders or Repair": [
            "Seawall Construction or Repair",
            "New Dock",
            "Dock Repair",
            "Pilings or Structural Support",
            "Floating Docks",
            "Boat Lift",
            "Seawall or Piling Cleaning"
        ]
    }
}

# SERVICE ALIASES - Maps common variations to canonical service names
# This helps with fuzzy matching and handles different naming conventions
SERVICE_ALIASES = {
    # Boat Maintenance aliases
    "boat oil change": "Oil Change",
    "oil change": "Oil Change",
    "boat bilge cleaning": "Bilge Cleaning",
    "bilge cleaning": "Bilge Cleaning",
    "yacht fire detection": "Fire Detection Systems",
    "fire detection": "Fire Detection Systems",
    "boat wrapping": "Boat Wrapping or Marine Protection Film",
    "marine protection film": "Boat Wrapping or Marine Protection Film",
    
    # Repair aliases
    "fiberglass": "Fiberglass Repair",
    "welding": "Welding & Metal Fabrication",
    "metal fabrication": "Welding & Metal Fabrication",
    "carpentry": "Carpentry & Woodwork",
    "woodwork": "Carpentry & Woodwork",
    "teak": "Teak or Woodwork",
    "canvas": "Canvas or Upholstery",
    "upholstery": "Canvas or Upholstery",
    "decking": "Boat Decking",
    "flooring": "Boat Decking",
    
    # Engine/Generator aliases
    "generator repair": "Generator Service",
    "generator maintenance": "Generator Service",
    "outboard service": "Outboard Engine Service",
    "outboard sales": "Outboard Engine Sales",
    "inboard service": "Inboard Engine Service",
    "inboard sales": "Inboard Engine Sales",
    "diesel service": "Diesel Engine Service",
    "diesel sales": "Diesel Engine Sales",
    
    # Marine Systems aliases
    "ac repair": "AC Sales or Service",
    "ac service": "AC Sales or Service",
    "air conditioning": "AC Sales or Service",
    "electrical": "Electrical Service",
    "sound system": "Sound System",
    "audio": "Sound System",
    "plumbing": "Plumbing",
    "lighting": "Lighting",
    "refrigeration": "Refrigeration or Watermakers",
    "watermaker": "Refrigeration or Watermakers",
    "stabilizers": "Stabilizers or Seakeepers",
    "seakeepers": "Stabilizers or Seekeepers",
    
    # Charter/Rental aliases
    "fishing charter": "Fishing Charter",
    "fishing charters": "Fishing Charter",
    "yacht charter": "Daily Yacht or Catamaran Charter",
    "catamaran charter": "Daily Yacht or Catamaran Charter",
    "sailboat charter": "Sailboat Charter",
    "jet ski": "Jet Ski Rental",
    "paddleboard": "Paddleboard Rental",
    "kayak": "Kayak Rental",
    "boat club": "Boat Club",
    
    # Towing aliases
    "emergency tow": "Get Emergency Tow",
    "towing": "Get Emergency Tow",
    "tow membership": "Get Towing Membership",
    
    # Other aliases
    "dock rental": "Dock and Slip Rental",
    "slip rental": "Dock and Slip Rental",
    "marina": "Marina",
    "fuel": "Fuel Delivery",
    "diesel fuel": "Dyed Diesel Fuel (For Boats)",
    "rec 90": "Rec 90 (Ethanol Free Gas)"
}

class ServiceCategoryManager:
    """
    Enhanced manager class for service category operations.
    Now includes fuzzy matching, aliases, and Level 3 services.
    """
    
    def __init__(self):
        self.categories = SERVICE_CATEGORIES
        self.level3_services = LEVEL_3_SERVICES
        self.aliases = SERVICE_ALIASES
        self.SERVICE_CATEGORIES = SERVICE_CATEGORIES  # Backward compatibility
        self._build_service_lookup_maps()
        logger.info(f"✅ ServiceCategoryManager initialized with {len(self.categories)} categories and {len(self.aliases)} aliases")
    
    def _build_service_lookup_maps(self):
        """Build reverse lookup maps for efficient searching"""
        # Service -> Category mapping
        self.service_to_category = {}
        
        # Lowercase service -> Category mapping for fuzzy matching
        self.service_fuzzy_map = {}
        
        # Keyword -> Category mapping for fallback matching
        self.keyword_to_category = {}
        
        for category, services in self.categories.items():
            # Build exact service mappings
            for service in services:
                self.service_to_category[service] = category
                self.service_fuzzy_map[service.lower()] = category
                
                # Extract keywords from service names for fuzzy matching
                keywords = self._extract_keywords(service)
                for keyword in keywords:
                    if keyword not in self.keyword_to_category:
                        self.keyword_to_category[keyword] = []
                    if category not in self.keyword_to_category[keyword]:
                        self.keyword_to_category[keyword].append(category)
        
        logger.debug(f"Built lookup maps: {len(self.service_to_category)} services, {len(self.keyword_to_category)} keywords")
    
    def _extract_keywords(self, service_name: str) -> List[str]:
        """Extract meaningful keywords from service names"""
        # Remove common words and extract meaningful terms
        common_words = {'and', 'or', 'the', 'of', 'for', 'in', 'on', 'at', 'to', 'a', 'an', '&', 'your', 'my'}
        words = service_name.lower().replace('&', ' ').replace('/', ' ').split()
        keywords = [word.strip('().,') for word in words if word.strip('().,') not in common_words and len(word.strip('().,')) > 2]
        return keywords
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings (0-1 scale)"""
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    def _services_are_related(self, service1: str, service2: str) -> bool:
        """Check if two services are actually related (not just in same category)"""
        # Extract key words from both services
        keywords1 = set(self._extract_keywords(service1))
        keywords2 = set(self._extract_keywords(service2))
        
        # Services are related if they share key terms
        common_keywords = keywords1.intersection(keywords2)
        
        # Need at least one common keyword or high similarity
        return len(common_keywords) > 0 or self._calculate_similarity(service1, service2) > 0.8
    
    # ====================
    # PRIMARY LOOKUP METHODS
    # ====================
    
    def get_all_categories(self) -> List[str]:
        """Get all service categories"""
        return list(self.categories.keys())
    
    def get_services_for_category(self, category: str) -> List[str]:
        """Get all specific services for a category (excluding aliases)"""
        services = []
        for service in self.categories.get(category, []):
            # Filter out obvious aliases (those that are variations)
            if not any(alias in service.lower() for alias in ['alias', '# alias']):
                services.append(service)
        return services
    
    def get_all_services_including_aliases(self, category: str) -> List[str]:
        """Get all services including aliases for maximum matching"""
        return self.categories.get(category, [])
    
    def get_category_for_service(self, service: str) -> Optional[str]:
        """Get the category for a specific service with fuzzy matching"""
        # Try exact match first
        if service in self.service_to_category:
            return self.service_to_category[service]
        
        # Try alias lookup
        service_lower = service.lower()
        if service_lower in self.aliases:
            canonical = self.aliases[service_lower]
            if canonical in self.service_to_category:
                return self.service_to_category[canonical]
        
        # Try fuzzy match
        if service_lower in self.service_fuzzy_map:
            return self.service_fuzzy_map[service_lower]
        
        # Try similarity matching (threshold: 0.85)
        best_match = None
        best_score = 0
        for known_service, category in self.service_to_category.items():
            score = self._calculate_similarity(service, known_service)
            if score > 0.85 and score > best_score:
                best_score = score
                best_match = category
        
        return best_match
    
    def get_level3_services(self, category: str, subcategory: str) -> List[str]:
        """Get Level 3 services for a specific subcategory"""
        if category in self.level3_services:
            # Try exact match
            if subcategory in self.level3_services[category]:
                return self.level3_services[category][subcategory]
            # Try with variations (handle & vs and)
            for key in self.level3_services[category]:
                if self._calculate_similarity(subcategory, key) > 0.9:
                    return self.level3_services[category][key]
        return []
    
    def is_valid_category(self, category: str) -> bool:
        """Check if a category is valid"""
        return category in self.categories
    
    def is_valid_service(self, service: str) -> bool:
        """Check if a service is valid (including aliases)"""
        return self.get_category_for_service(service) is not None
    
    def is_service_in_category(self, service: str, category: str) -> bool:
        """Check if a service belongs to a specific category"""
        found_category = self.get_category_for_service(service)
        return found_category == category
    
    # ====================
    # MULTI-LEVEL MATCHING METHODS
    # ====================
    
    def find_matching_services(self, search_text: str, category: str = None) -> List[str]:
        """
        Find specific services that match the search text with fuzzy matching.
        If category is provided, only search within that category.
        """
        if not search_text:
            return []
        
        search_lower = search_text.lower().strip()
        matches = []
        scores = {}
        
        # Check aliases first
        if search_lower in self.aliases:
            canonical = self.aliases[search_lower]
            if self.is_valid_service(canonical):
                matches.append(canonical)
                scores[canonical] = 1.0
        
        # Search scope
        search_categories = [category] if category and category in self.categories else self.categories.keys()
        
        for cat in search_categories:
            for service in self.get_all_services_including_aliases(cat):
                service_lower = service.lower()
                
                # Skip if already added
                if service in matches:
                    continue
                
                # Calculate similarity score
                score = 0
                
                # Exact match
                if search_lower == service_lower:
                    score = 1.0
                # Contains match
                elif search_lower in service_lower or service_lower in search_lower:
                    score = 0.9
                # Similarity match
                else:
                    score = self._calculate_similarity(search_text, service)
                
                # Add if score is high enough
                if score > 0.7:
                    matches.append(service)
                    scores[service] = score
        
        # Sort by score
        matches.sort(key=lambda x: scores.get(x, 0), reverse=True)
        return matches[:10]  # Return top 10 matches
    
    def find_best_category_match(self, search_text: str) -> Optional[str]:
        """
        Find the best category match for search text using enhanced matching.
        """
        if not search_text:
            return None
        
        search_lower = search_text.lower().strip()
        
        # Direct category name match
        for category in self.categories.keys():
            if search_lower == category.lower():
                return category
            if self._calculate_similarity(search_text, category) > 0.85:
                return category
        
        # Check if it's a known service
        category = self.get_category_for_service(search_text)
        if category:
            return category
        
        # Service-based category match
        matching_services = self.find_matching_services(search_text)
        if matching_services:
            # Return category of best matching service
            return self.get_category_for_service(matching_services[0])
        
        # Keyword-based fallback with scoring
        search_keywords = self._extract_keywords(search_text)
        category_scores = {}
        
        for keyword in search_keywords:
            if keyword in self.keyword_to_category:
                for category in self.keyword_to_category[keyword]:
                    category_scores[category] = category_scores.get(category, 0) + 1
        
        if category_scores:
            # Return category with highest score
            return max(category_scores, key=category_scores.get)
        
        # Last resort - check for any partial matches
        for category, services in self.categories.items():
            for service in services:
                if self._calculate_similarity(search_text, service) > 0.7:
                    return category
        
        return None
    
    # ====================
    # VENDOR MATCHING METHODS (ENHANCED)
    # ====================
    
    def vendor_matches_service_fuzzy(self, vendor_services: List[str], 
                                    service_requested: str, 
                                    threshold: float = 0.85) -> bool:
        """
        Check if vendor matches service with fuzzy matching.
        This addresses the exact match problem in the original code.
        """
        if not vendor_services or not service_requested:
            return False
        
        # Normalize the requested service
        service_lower = service_requested.lower()
        
        # Check aliases
        if service_lower in self.aliases:
            service_requested = self.aliases[service_lower]
        
        # Check each vendor service
        for vendor_service in vendor_services:
            # Exact match
            if vendor_service.lower() == service_lower:
                return True
            
            # Alias match
            vendor_lower = vendor_service.lower()
            if vendor_lower in self.aliases:
                if self.aliases[vendor_lower].lower() == service_lower:
                    return True
            
            # Fuzzy match
            similarity = self._calculate_similarity(vendor_service, service_requested)
            if similarity >= threshold:
                return True
            
            # Check if they're in the same category and similar enough
            vendor_category = self.get_category_for_service(vendor_service)
            requested_category = self.get_category_for_service(service_requested)
            
            if vendor_category and vendor_category == requested_category:
                # Only match if they're actually similar services, not just same category
                if similarity >= 0.75 and self._services_are_related(vendor_service, service_requested):
                    return True
        
        return False
    
    def vendor_matches_service_exact(self, vendor_services: List[str], 
                                   primary_category: str, specific_service: str) -> bool:
        """
        Enhanced vendor matching with fuzzy logic.
        Fixes the original exact match problem.
        """
        # Filter 1: Primary category match (with fuzzy matching)
        vendor_has_category = False
        for vs in vendor_services:
            vs_category = self.get_category_for_service(vs)
            if vs_category == primary_category:
                vendor_has_category = True
                break
        
        if not vendor_has_category:
            return False
        
        # Filter 2: Specific service match (with fuzzy matching)
        return self.vendor_matches_service_fuzzy(vendor_services, specific_service)
    
    def vendor_matches_category_only(self, vendor_services: List[str], 
                                   primary_category: str) -> bool:
        """
        Check if vendor matches primary category (enhanced with fuzzy logic).
        """
        for vs in vendor_services:
            vs_category = self.get_category_for_service(vs)
            if vs_category == primary_category:
                return True
        return False
    
    def vendor_matches_level3_service(self, vendor_level3_services: Dict[str, List[str]], 
                                     category: str, subcategory: str, 
                                     level3_service: str) -> bool:
        """
        Check if vendor offers a specific Level 3 service.
        """
        if not vendor_level3_services:
            return False
        
        # Check if vendor has this subcategory
        if subcategory in vendor_level3_services:
            vendor_l3_list = vendor_level3_services[subcategory]
            
            # Exact match
            if level3_service in vendor_l3_list:
                return True
            
            # Fuzzy match
            for vendor_l3 in vendor_l3_list:
                if self._calculate_similarity(vendor_l3, level3_service) > 0.85:
                    return True
        
        return False
    
    # ====================
    # UTILITY METHODS
    # ====================
    
    def get_stats(self) -> Dict:
        """Get statistics about the service hierarchy"""
        total_services = sum(len(services) for services in self.categories.values())
        total_level3 = sum(
            sum(len(l3_list) for l3_list in cat_l3.values()) 
            for cat_l3 in self.level3_services.values()
        )
        
        category_stats = {}
        for category, services in self.categories.items():
            # Count non-alias services
            non_alias_count = len([s for s in services if '# Alias' not in s])
            category_stats[category] = non_alias_count
        
        return {
            "total_categories": len(self.categories),
            "total_services": total_services,
            "total_aliases": len(self.aliases),
            "total_level3_services": total_level3,
            "average_services_per_category": round(total_services / len(self.categories), 1),
            "category_breakdown": category_stats,
            "largest_category": max(category_stats, key=category_stats.get),
            "smallest_category": min(category_stats, key=category_stats.get)
        }
    
    def validate_vendor_services(self, vendor_services: List[str]) -> Dict:
        """
        Validate vendor services with fuzzy matching and provide corrections.
        """
        valid_services = []
        invalid_services = []
        corrections = {}
        suggestions = {}
        
        for service in vendor_services:
            # Check if valid (including fuzzy match)
            category = self.get_category_for_service(service)
            
            if category:
                valid_services.append(service)
                # Check if there's a canonical version
                service_lower = service.lower()
                if service_lower in self.aliases:
                    canonical = self.aliases[service_lower]
                    if canonical != service:
                        corrections[service] = canonical
            else:
                invalid_services.append(service)
                # Find closest matches
                matches = self.find_matching_services(service)
                if matches:
                    suggestions[service] = matches[:3]  # Top 3 suggestions
        
        return {
            "valid_services": valid_services,
            "invalid_services": invalid_services,
            "corrections": corrections,
            "suggestions": suggestions,
            "validation_rate": len(valid_services) / len(vendor_services) if vendor_services else 0
        }
    
    def normalize_service_name(self, service: str) -> str:
        """
        Normalize a service name to its canonical form.
        """
        service_lower = service.lower()
        
        # Check aliases
        if service_lower in self.aliases:
            return self.aliases[service_lower]
        
        # Check if it's already valid
        if service in self.service_to_category:
            return service
        
        # Try to find best match
        matches = self.find_matching_services(service)
        if matches:
            return matches[0]
        
        return service
    
    def export_for_forms(self) -> Dict:
        """
        Export service hierarchy in format suitable for form dropdowns.
        """
        # Filter out aliases for cleaner form display
        clean_categories = {}
        for category, services in self.categories.items():
            clean_services = [s for s in services if '# Alias' not in s and 'Alias' not in s]
            clean_categories[category] = clean_services
        
        return {
            "categories": self.get_all_categories(),
            "service_hierarchy": clean_categories,
            "level3_services": self.level3_services,
            "total_categories": len(self.categories),
            "total_services": sum(len(services) for services in clean_categories.values()),
            "has_level3": list(self.level3_services.keys())
        }
    
    def classify_form_identifier(self, form_identifier: str) -> Tuple[str, Optional[str]]:
        """
        Classify form identifier to determine service category and specific service.
        Returns tuple of (category, specific_service).
        Enhanced to handle both category and service identification.
        """
        if not form_identifier:
            return ("Boater Resources", None)
        
        # Clean the identifier
        clean_id = form_identifier.replace('_', ' ').replace('-', ' ').strip()
        
        # Check if it's a direct service match
        service_category = self.get_category_for_service(clean_id)
        if service_category:
            return (service_category, self.normalize_service_name(clean_id))
        
        # Try to match as category
        best_category = self.find_best_category_match(clean_id)
        if best_category:
            # Try to extract specific service from identifier
            services = self.find_matching_services(clean_id, best_category)
            specific_service = services[0] if services else None
            return (best_category, specific_service)
        
        # Fallback
        return ("Boater Resources", None)

# Global instance for use throughout the application
service_manager = ServiceCategoryManager()

# Convenience functions for backward compatibility
def get_all_categories() -> List[str]:
    """Get all service categories"""
    return service_manager.get_all_categories()

def get_services_for_category(category: str) -> List[str]:
    """Get all specific services for a category"""
    return service_manager.get_services_for_category(category)

def find_best_category_match(search_text: str) -> Optional[str]:
    """Find the best category match for search text"""
    return service_manager.find_best_category_match(search_text)

def vendor_matches_service_exact(vendor_services: List[str], 
                               primary_category: str, specific_service: str) -> bool:
    """Check if vendor matches both category and specific service (with fuzzy matching)"""
    return service_manager.vendor_matches_service_exact(vendor_services, primary_category, specific_service)

def vendor_matches_service_fuzzy(vendor_services: List[str], 
                                service_requested: str, 
                                threshold: float = 0.85) -> bool:
    """Check if vendor matches service with fuzzy matching"""
    return service_manager.vendor_matches_service_fuzzy(vendor_services, service_requested, threshold)

def normalize_service_name(service: str) -> str:
    """Normalize a service name to its canonical form"""
    return service_manager.normalize_service_name(service)

def get_level3_services(category: str, subcategory: str) -> List[str]:
    """Get Level 3 services for a specific subcategory"""
    return service_manager.get_level3_services(category, subcategory)

# Export key data structures for external use
__all__ = [
    'SERVICE_CATEGORIES',
    'LEVEL_3_SERVICES', 
    'SERVICE_ALIASES',
    'ServiceCategoryManager',
    'service_manager',
    'get_all_categories',
    'get_services_for_category',
    'find_best_category_match',
    'vendor_matches_service_exact',
    'vendor_matches_service_fuzzy',
    'normalize_service_name',
    'get_level3_services'
]