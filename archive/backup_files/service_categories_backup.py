"""
Service Categories - Single Source of Truth
Multi-level service routing system for precise vendor matching.

This module contains the definitive service hierarchy and is the ONLY
source for service category and specific service definitions.
"""

import json
import logging
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# SERVICE HIERARCHY - SINGLE SOURCE OF TRUTH
# This data structure is the definitive reference for all service categories
# and specific services. DO NOT duplicate this data elsewhere in the codebase.
SERVICE_CATEGORIES = {
    "Boat and Yacht Repair": [
        "Fiberglass Repair",
        "Welding & Metal Fabrication",
        "Carpentry & Woodwork",
        "Riggers & Masts",
        "Jet Ski Repair",
        "Boat Canvas and Upholstery",
        "Boat Decking and Yacht Flooring"
    ],
    "Boat Charters and Rentals": [
        "Boat Charters and Rentals",
        "Boat Clubs",
        "Fishing Charters",
        "Yacht and Catamaran Charters",
        "Sailboat Charters",
        "eFoil, Kiteboarding & Wing Surfing",
        "Dive Equipment and Services"
    ],
    "Boat Hauling and Yacht Delivery": [
        "Yacht Delivery",
        "Boat Hauling and Transport"
    ],
    "Boat Maintenance": [
        "Barnacle Cleaning",
        "Boat and Yacht Maintenance",
        "Boat Bilge Cleaning",
        "Boat Bottom Cleaning",
        "Boat Detailing",
        "Boat Oil Change",
        "Boat Wrapping and Marine Protection Film",
        "Ceramic Coating",
        "Jet Ski Maintenance",
        "Yacht Armor",
        "Yacht Fire Detection Systems"
    ],
    "Boat Towing": [
        "Get Emergency Tow",
        "Get Towing Membership"
    ],
    "Boater Resources": [
        "Yacht Wi-Fi",
        "Provisioning",
        "Boat and Yacht Parts",
        "Boat Salvage",
        "Yacht Photography",
        "Yacht Videography",
        "Yacht Crew Placement",
        "Yacht Account Management and Bookkeeping"
    ],
    "Buying or Selling a Boat": [
        "Boat Dealers",
        "Yacht Dealers",
        "Boat Surveyors",
        "Boat Financing",
        "Boat Builders",
        "Boat Brokers",
        "Yacht Brokers",
        "Yacht Builders",
        "Boat Insurance",
        "Yacht Insurance"
    ],
    "Docks, Seawalls and Lifts": [
        "Dock and Seawall Builders or Repair",
        "Boat Lift Installers",
        "Floating Dock Sales",
        "Davit and Hydraulic Platform"
    ],
    "Dock and Slip Rental": [
        "Dock and Slip Rental",
        "Rent My Dock"
    ],
    "Engines and Generators": [
        "Outboard Engine Service",
        "Outboard Engine Sales",
        "Inboard Engine Service",
        "Inboard Engine Sales",
        "Diesel Engine Service",
        "Diesel Engine Sales",
        "Generator Service and Repair",
        "Generator Sales"
    ],
    "Fuel Delivery": [
        "Fuel Delivery"
    ],
    "Marine Systems": [
        "Yacht AC Sales",
        "Yacht AC Service",
        "Boat Electrical Service",
        "Yacht Plumbing",
        "Boat Sound Systems",
        "Boat Lighting",
        "Yacht Stabilizers & Seakeepers",
        "Yacht Refrigeration & Watermakers"
    ],
    "Maritime Education and Training": [
        "Maritime Certification",
        "Maritime Academy",
        "Sailing Schools",
        "Yacht Training"
    ],
    "Waterfront Property": [
        "Waterfront Homes For Sale",
        "Sell Your Waterfront Home",
        "New Waterfront Developments"
    ],
    "Wholesale or Dealer Product Pricing": [
        "Wholesale or Dealer Product Pricing"
    ],
    "Yacht Management": [
        "Yacht Management"
    ]
}

class ServiceCategoryManager:
    """
    Manager class for service category operations.
    Provides all functionality needed for multi-level service routing.
    """
    
    def __init__(self):
        self.categories = SERVICE_CATEGORIES
        self.SERVICE_CATEGORIES = SERVICE_CATEGORIES  # FIXED: Expose for backward compatibility
        self._build_service_lookup_maps()
        logger.info(f"✅ ServiceCategoryManager initialized with {len(self.categories)} categories")
    
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
                    self.keyword_to_category[keyword].append(category)
        
        logger.debug(f"Built lookup maps: {len(self.service_to_category)} services, {len(self.keyword_to_category)} keywords")
    
    def _extract_keywords(self, service_name: str) -> List[str]:
        """Extract meaningful keywords from service names"""
        # Remove common words and extract meaningful terms
        common_words = {'and', 'or', 'the', 'of', 'for', 'in', 'on', 'at', 'to', 'a', 'an', '&'}
        words = service_name.lower().replace('&', ' ').split()
        keywords = [word.strip() for word in words if word.strip() not in common_words and len(word.strip()) > 2]
        return keywords
    
    # ====================
    # PRIMARY LOOKUP METHODS
    # ====================
    
    def get_all_categories(self) -> List[str]:
        """Get all service categories"""
        return list(self.categories.keys())
    
    def get_services_for_category(self, category: str) -> List[str]:
        """Get all specific services for a category"""
        return self.categories.get(category, [])
    
    def get_category_for_service(self, service: str) -> Optional[str]:
        """Get the category for a specific service (exact match)"""
        return self.service_to_category.get(service)
    
    def is_valid_category(self, category: str) -> bool:
        """Check if a category is valid"""
        return category in self.categories
    
    def is_valid_service(self, service: str) -> bool:
        """Check if a service is valid"""
        return service in self.service_to_category
    
    def is_service_in_category(self, service: str, category: str) -> bool:
        """Check if a service belongs to a specific category"""
        return service in self.categories.get(category, [])
    
    # ====================
    # MULTI-LEVEL MATCHING METHODS
    # ====================
    
    def find_matching_services(self, search_text: str, category: str = None) -> List[str]:
        """
        Find specific services that match the search text.
        If category is provided, only search within that category.
        """
        if not search_text:
            return []
        
        search_lower = search_text.lower().strip()
        matches = []
        
        # Search scope
        search_categories = [category] if category else self.categories.keys()
        
        for cat in search_categories:
            if cat not in self.categories:
                continue
                
            for service in self.categories[cat]:
                service_lower = service.lower()
                
                # Exact match
                if search_lower == service_lower:
                    matches.append(service)
                # Partial match - check if search text is contained in service
                elif search_lower in service_lower or service_lower in search_lower:
                    matches.append(service)
                # Keyword match - check if any keywords overlap
                elif self._has_keyword_overlap(search_text, service):
                    matches.append(service)
        
        return list(set(matches))  # Remove duplicates
    
    def find_best_category_match(self, search_text: str) -> Optional[str]:
        """
        Find the best category match for search text.
        Uses fuzzy matching with confidence scoring.
        """
        if not search_text:
            return None
        
        search_lower = search_text.lower().strip()
        
        # Direct category name match
        for category in self.categories.keys():
            if search_lower == category.lower():
                return category
            if search_lower in category.lower() or category.lower() in search_lower:
                return category
        
        # Service-based category match
        matching_services = self.find_matching_services(search_text)
        if matching_services:
            # Return category of first matching service
            return self.get_category_for_service(matching_services[0])
        
        # Keyword-based fallback
        search_keywords = self._extract_keywords(search_text)
        category_scores = {}
        
        for keyword in search_keywords:
            if keyword in self.keyword_to_category:
                for category in self.keyword_to_category[keyword]:
                    category_scores[category] = category_scores.get(category, 0) + 1
        
        if category_scores:
            # Return category with highest score
            return max(category_scores, key=category_scores.get)
        
        return None
    
    def _has_keyword_overlap(self, text1: str, text2: str) -> bool:
        """Check if two texts have overlapping keywords"""
        keywords1 = set(self._extract_keywords(text1))
        keywords2 = set(self._extract_keywords(text2))
        return len(keywords1.intersection(keywords2)) > 0
    
    # ====================
    # VENDOR MATCHING METHODS
    # ====================
    
    def vendor_matches_service_exact(self, vendor_services: List[str], 
                                   primary_category: str, specific_service: str) -> bool:
        """
        Check if vendor matches both primary category AND specific service exactly.
        This is the core method for multi-level routing.
        """
        # Filter 1: Primary category exact match
        vendor_has_category = any(
            self.get_category_for_service(vs) == primary_category 
            for vs in vendor_services
        )
        
        if not vendor_has_category:
            return False
        
        # Filter 2: Specific service exact match
        if specific_service in vendor_services:
            return True
        
        return False
    
    def vendor_matches_category_only(self, vendor_services: List[str], 
                                   primary_category: str) -> bool:
        """
        Check if vendor matches primary category (fallback method).
        Used when no specific service is provided or no exact matches found.
        """
        return any(
            self.get_category_for_service(vs) == primary_category 
            for vs in vendor_services
        )
    
    # ====================
    # UTILITY METHODS
    # ====================
    
    def get_stats(self) -> Dict:
        """Get statistics about the service hierarchy"""
        total_services = sum(len(services) for services in self.categories.values())
        
        category_stats = {}
        for category, services in self.categories.items():
            category_stats[category] = len(services)
        
        return {
            "total_categories": len(self.categories),
            "total_services": total_services,
            "average_services_per_category": round(total_services / len(self.categories), 1),
            "category_breakdown": category_stats,
            "largest_category": max(category_stats, key=category_stats.get),
            "smallest_category": min(category_stats, key=category_stats.get)
        }
    
    def validate_vendor_services(self, vendor_services: List[str]) -> Dict:
        """
        Validate vendor services against the service hierarchy.
        Returns validation results and suggestions.
        """
        valid_services = []
        invalid_services = []
        suggestions = {}
        
        for service in vendor_services:
            if self.is_valid_service(service):
                valid_services.append(service)
            else:
                invalid_services.append(service)
                # Find closest matches
                matches = self.find_matching_services(service)
                if matches:
                    suggestions[service] = matches[:3]  # Top 3 suggestions
        
        return {
            "valid_services": valid_services,
            "invalid_services": invalid_services,
            "suggestions": suggestions,
            "validation_rate": len(valid_services) / len(vendor_services) if vendor_services else 0
        }
    
    def export_for_forms(self) -> Dict:
        """
        Export service hierarchy in format suitable for form dropdowns.
        Returns category -> services mapping for frontend use.
        """
        return {
            "categories": self.get_all_categories(),
            "service_hierarchy": self.categories.copy(),
            "total_categories": len(self.categories),
            "total_services": sum(len(services) for services in self.categories.values())
        }
    
    def classify_form_identifier(self, form_identifier: str) -> str:
        """
        Classify form identifier to determine service category.
        NEW: Used by webhook_routes.py for form processing.
        """
        if not form_identifier:
            return "Boater Resources"
        
        # Use existing best category match logic
        best_match = self.find_best_category_match(form_identifier)
        
        if best_match:
            return best_match
        
        # Fallback to default category
        return "Boater Resources"

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
    """Check if vendor matches both category and specific service exactly"""
    return service_manager.vendor_matches_service_exact(vendor_services, primary_category, specific_service)
