"""
Service Dictionary Mapper for Lead Router Pro
==============================================
This module provides intelligent mapping from various form questions to standardized service categories
based on the official services_data_dictionary.md hierarchy.

Author: Lead Router Pro Team
Created: January 2025
"""

import re
import json
import logging
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
from dataclasses import dataclass
from difflib import get_close_matches

logger = logging.getLogger(__name__)


@dataclass
class ServiceMapping:
    """Represents a complete service mapping"""
    level1_category: str  # Main category (e.g., "Boat and Yacht Repair")
    level2_service: str   # Service type (e.g., "Fiberglass Repair")
    level3_specific: str  # Specific service (e.g., "Hull Crack or Structural Repair")
    confidence: float     # Confidence score (0-1)
    matched_keywords: List[str]
    source_question: str
    extracted_value: str


class ServiceDictionaryMapper:
    """
    Maps incoming form questions and answers to standardized service categories
    using both question patterns and the official service hierarchy.
    """
    
    def __init__(self):
        self.service_hierarchy = self._load_service_hierarchy()
        self.question_patterns = self._build_question_patterns()
        self.keyword_mappings = self._build_keyword_mappings()
        self.field_consolidation_map = self._build_field_consolidation_map()
        
        logger.info(f"✅ ServiceDictionaryMapper initialized with {len(self.service_hierarchy)} L1 categories")
    
    def _load_service_hierarchy(self) -> Dict:
        """Load and parse the services_data_dictionary.md structure"""
        
        # This would normally load from the actual file, but for now we'll hardcode the structure
        # In production, this would parse the markdown file
        
        hierarchy = {
            "Boat and Yacht Repair": {
                "services": {
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
                        "Custom Railings",
                        "Ladders or Boarding Equipment",
                        "T-Tops, Hardtops or Bimini Frames",
                        "Fuel or Water Tank Fabrication",
                        "Exhaust, Engine Bed or Structural Reinforcement",
                        "Other"
                    ],
                    "Carpentry & Woodwork": [
                        "Interior Woodwork and Cabinetry",
                        "Teak Deck Repair or Replacement",
                        "Varnishing & Wood Finishing",
                        "Structural Wood Repairs",
                        "Custom Furniture or Fixtures",
                        "Other"
                    ],
                    "Jet Ski Repair": [
                        "Engine Diagnostics & Repair",
                        "Jet Pump Rebuild or Replacement",
                        "Fuel Systems Cleaning or Repair",
                        "Battery or Electrical Repairs",
                        "Cooling System Flush or Repair",
                        "General Maintenance",
                        "Other"
                    ],
                    "Boat Canvas and Upholstery": [
                        "Upholstery",
                        "Canvas or Sunshade",
                        "Trim and Finish",
                        "Boat Cover or T-Top",
                        "Acrylic or Strataglass Enclosures",
                        "Other"
                    ]
                }
            },
            "Boat Charters and Rentals": {
                "services": {
                    "Yacht and Catamaran Charters": [
                        "Day Yacht Charter",
                        "Day Catamaran Charter",
                        "Group Yacht or Catamaran Charter",
                        "Weekly or Monthly Catamaran or Yacht Charter",
                        "Other"
                    ],
                    "Sailboat Charters": [
                        "Bareboat Charter (No Captain or Crew)",
                        "Skippered Charter",
                        "Crewed Charter",
                        "Cabin Charter",
                        "Sailing Charter (Learn to Sail)",
                        "Weekly or Monthly Charter"
                    ],
                    "Fishing Charters": [
                        "Inshore Fishing Charter",
                        "Offshore (Deep Sea) Fishing Charter",
                        "Reef & Wreck Fishing Charter",
                        "Drift Boat Charter",
                        "Freshwater Fishing Charter",
                        "Private Party Boat Charter",
                        "Fishing Resort Vacation"
                    ],
                    "Party Boat Charter": [
                        "Pontoon Party Boat",
                        "Catamaran Party Boat",
                        "Yacht Party Boat",
                        "50+ Person Party Boat"
                    ],
                    "Jet Ski Rental": [
                        "Hourly Jet Ski Rental",
                        "Multiple Day Jet Ski Rental",
                        "Jet Ski Tour"
                    ]
                }
            },
            "Boat Maintenance": {
                "services": {
                    "Boat Detailing": [],
                    "Ceramic Coating": [],
                    "Bottom Painting": [],
                    "Oil Change": [],
                    "Bilge Cleaning": [],
                    "Barnacle Cleaning": []
                }
            },
            "Yacht Management": {
                "services": {
                    "Yacht Management": [
                        "Full Service Vessel Management",
                        "Technical Management (Maintenance, Repairs, Upgrades, etc)",
                        "Crew Management",
                        "Accounting & Financial Management",
                        "Insurance & Risk Management",
                        "Regulatory Compliance",
                        "Maintenance & Refit Management",
                        "Logistical Support (Transportation, Provisioning, Fuel or Dockage)",
                        "Wash Downs and Systems Checks"
                    ]
                }
            },
            "Boater Resources": {
                "services": {
                    "Maritime Attorney": [
                        "Maritime Personal Injury Case",
                        "Marine Insurance Dispute",
                        "Maritime Commercial and Contract Case",
                        "Environmental & Regulatory Compliance",
                        "Vessel Documentation and Transactions",
                        "Maritime Criminal Defense",
                        "Other"
                    ],
                    "Boat and Yacht Parts": [
                        "Engine & Propulsion Parts",
                        "Electrical & Battery Systems Parts",
                        "Steering & Control Systems Parts",
                        "Navigation & Electronics Parts",
                        "Plumbing & Water Systems Parts",
                        "Hull, Deck & Hardware Parts"
                    ],
                    "Provisioning": [
                        "Food & Beverage Provisioning",
                        "Galley & Kitchen Supplies",
                        "Crew Provisioning",
                        "Cabin & Guest Comfort Supplies",
                        "Medical & First Aid Provisioning"
                    ]
                }
            }
        }
        
        return hierarchy
    
    def _build_question_patterns(self) -> Dict[str, Dict]:
        """
        Build patterns to recognize service context from questions themselves.
        Maps question patterns to service categories.
        """
        
        patterns = {
            # Management Services
            r"what management services": {
                "level1": "Yacht Management",
                "level2": "Yacht Management",
                "context": "management"
            },
            
            # Attorney Services
            r"what specific attorney service": {
                "level1": "Boater Resources",
                "level2": "Maritime Attorney",
                "context": "legal"
            },
            
            # Charter Services
            r"what specific (sailboat )?charter": {
                "level1": "Boat Charters and Rentals",
                "level2": "Sailboat Charters",
                "context": "charter"
            },
            r"what type of private yacht charter": {
                "level1": "Boat Charters and Rentals",
                "level2": "Yacht and Catamaran Charters",
                "context": "charter"
            },
            r"what type of party boat": {
                "level1": "Boat Charters and Rentals",
                "level2": "Party Boat Charter",
                "context": "charter"
            },
            
            # Parts and Products
            r"what specific parts": {
                "level1": "Boater Resources",
                "level2": "Boat and Yacht Parts",
                "context": "parts"
            },
            r"what product (category|specifically)": {
                "level1": "Wholesale or Dealer Product Pricing",
                "level2": "Wholesale or Dealer Product Pricing",
                "context": "products"
            },
            
            # Fuel Services
            r"what type of fuel": {
                "level1": "Fuel Delivery",
                "level2": "Fuel Delivery",
                "context": "fuel"
            },
            
            # Salvage Services
            r"what type of salvage": {
                "level1": "Boater Resources",
                "level2": "Boat Salvage",
                "context": "salvage"
            },
            
            # Provisioning
            r"what type of trip .* provisioning": {
                "level1": "Boater Resources",
                "level2": "Provisioning",
                "context": "provisioning"
            },
            
            # Education/Training
            r"what education or training": {
                "level1": "Maritime Education and Training",
                "level2": "Maritime Education and Training",
                "context": "education"
            },
            
            # Vessel Purchase/Insurance
            r"what type of vessel .* (buy|sell)": {
                "level1": "Buying or Selling a Boat",
                "level2": "Boat Broker",
                "context": "brokerage"
            },
            r"what type of vessel .* insure": {
                "level1": "Buying or Selling a Boat",
                "level2": "Boat Insurance",
                "context": "insurance"
            },
            r"what type of vessel .* survey": {
                "level1": "Buying or Selling a Boat",
                "level2": "Boat Surveyors",
                "context": "survey"
            },
            
            # Boat Clubs
            r"what type of boat club": {
                "level1": "Boat Charters and Rentals",
                "level2": "Boat Clubs",
                "context": "club"
            },
            
            # Crew Services
            r"what type of crew": {
                "level1": "Boater Resources",
                "level2": "Yacht Crew Placement",
                "context": "crew"
            },
            
            # Dockage
            r"type of dockage": {
                "level1": "Dock and Slip Rental",
                "level2": "Dock and Slip Rental",
                "context": "dockage"
            },
            
            # Financing
            r"type of financing": {
                "level1": "Buying or Selling a Boat",
                "level2": "Boat Financing",
                "context": "financing"
            }
        }
        
        return patterns
    
    def _build_keyword_mappings(self) -> Dict[str, List[str]]:
        """
        Build keyword mappings for Level 3 service identification.
        Maps keywords to specific services.
        """
        
        mappings = {
            # Yacht Management specific services
            "full service": ["Full Service Vessel Management"],
            "technical management": ["Technical Management (Maintenance, Repairs, Upgrades, etc)"],
            "crew management": ["Crew Management"],
            "accounting": ["Accounting & Financial Management"],
            "financial management": ["Accounting & Financial Management"],
            "insurance management": ["Insurance & Risk Management"],
            "risk management": ["Insurance & Risk Management"],
            "compliance": ["Regulatory Compliance"],
            "refit": ["Maintenance & Refit Management"],
            "logistics": ["Logistical Support (Transportation, Provisioning, Fuel or Dockage)"],
            "wash down": ["Wash Downs and Systems Checks"],
            
            # Attorney services
            "personal injury": ["Maritime Personal Injury Case"],
            "insurance dispute": ["Marine Insurance Dispute"],
            "contract": ["Maritime Commercial and Contract Case"],
            "environmental": ["Environmental & Regulatory Compliance"],
            "vessel documentation": ["Vessel Documentation and Transactions"],
            "criminal": ["Maritime Criminal Defense"],
            
            # Charter types
            "bareboat": ["Bareboat Charter (No Captain or Crew)"],
            "skippered": ["Skippered Charter"],
            "crewed": ["Crewed Charter"],
            "cabin": ["Cabin Charter"],
            "learn to sail": ["Sailing Charter (Learn to Sail)"],
            "day charter": ["Day Yacht Charter", "Day Catamaran Charter"],
            "weekly": ["Weekly or Monthly Charter"],
            "monthly": ["Weekly or Monthly Charter"],
            
            # Party boat types
            "pontoon": ["Pontoon Party Boat"],
            "catamaran": ["Catamaran Party Boat"],
            "yacht party": ["Yacht Party Boat"],
            "50+ person": ["50+ Person Party Boat"],
            
            # Parts categories
            "engine parts": ["Engine & Propulsion Parts"],
            "electrical parts": ["Electrical & Battery Systems Parts"],
            "steering": ["Steering & Control Systems Parts"],
            "navigation": ["Navigation & Electronics Parts"],
            "plumbing": ["Plumbing & Water Systems Parts"],
            "hull": ["Hull, Deck & Hardware Parts"],
            
            # Fuel types
            "dyed diesel": ["Dyed Diesel Fuel (For Boats)"],
            "regular diesel": ["Regular Diesel Fuel (Landside Business)"],
            "rec 90": ["Rec 90 (Ethanol Free Gas)"],
            "ethanol free": ["Rec 90 (Ethanol Free Gas)"]
        }
        
        return mappings
    
    def _build_field_consolidation_map(self) -> Dict[str, str]:
        """
        Maps various service-specific question fields to consolidated standard fields.
        This consolidates all the redundant custom fields into proper categories.
        """
        
        consolidation = {
            # All service-specific questions map to specific_service_requested
            "what_management_services_do_you_request": "specific_service_requested",
            "what_specific_attorney_service_do_you_request": "specific_service_requested",
            "what_specific_charter_do_you_request": "specific_service_requested",
            "what_specific_sailboat_charter_do_you_request": "specific_service_requested",
            "what_specific_service_do_you_request": "specific_service_requested",
            "what_specific_parts_do_you_request": "specific_service_requested",
            "what_type_of_fuel_do_you_need": "specific_service_requested",
            "what_type_of_party_boat_are_you_interested_in": "specific_service_requested",
            "what_type_of_private_yacht_charter_are_you_interested_in": "specific_service_requested",
            "what_type_of_salvage_do_you_request": "specific_service_requested",
            "what_type_of_trip_do_you_request_provisioning_for": "specific_service_requested",
            "what_education_or_training_do_you_request": "specific_service_requested",
            "what_type_of_boat_club_are_you_interested_in": "specific_service_requested",
            "what_type_of_crew": "specific_service_requested",
            
            # Product questions map to product_interest
            "what_product_category_are_you_interested_in": "product_category",
            "what_product_specifically_are_you_interested_in": "product_specific",
            
            # Vessel questions map to vessel fields
            "what_type_of_vessel_are_you_looking_to_buy_or_sell": "vessel_transaction_type",
            "what_type_of_vessel_are_you_looking_to_insure": "vessel_insurance_type",
            "what_type_of_vessel_are_you_looking_to_survey": "vessel_survey_type",
            
            # Dockage questions
            "type_of_dockage_available": "dockage_type",
            "type_of_dockage_requested": "dockage_type",
            "what_specific_dates_do_you_require_dockage": "dockage_dates",
            "what_dates_specifically_is_the_dock_or_slip_available": "dockage_availability",
            
            # Other specific fields
            "type_of_financing_requested": "financing_type",
            "what_is_your_ideal_budget": "budget_range",
            "what_is_your_boating_experience": "experience_level",
            "tell_us_more_about_your_company": "company_description"
        }
        
        return consolidation
    
    def map_payload_to_service(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main method to process a form payload and map to standardized services.
        
        Args:
            payload: Raw form data from webhook
            
        Returns:
            Dict containing:
                - standardized_fields: Consolidated field mappings
                - service_classification: Level 1, 2, 3 service categories
                - confidence_scores: Mapping confidence
                - original_mapping: Debug info showing what was mapped
        """
        
        result = {
            "standardized_fields": {},
            "service_classification": {
                "level1_category": None,
                "level2_service": None,
                "level3_specific": None
            },
            "confidence_scores": {},
            "original_mapping": {},
            "processing_notes": []
        }
        
        # Track service context from questions
        service_contexts = []
        
        # Process each field in the payload
        for field_name, field_value in payload.items():
            if not field_value:
                continue
                
            field_lower = field_name.lower().strip()
            
            # Check if this is a service-specific question
            service_mapping = self._identify_service_from_question(field_lower, str(field_value))
            if service_mapping:
                service_contexts.append(service_mapping)
                
                # Map to standardized field
                standardized_field = self._get_standardized_field(field_lower)
                if standardized_field:
                    result["standardized_fields"][standardized_field] = field_value
                    result["original_mapping"][field_name] = {
                        "mapped_to": standardized_field,
                        "service_context": service_mapping
                    }
                    
                    logger.info(f"📍 Mapped '{field_name}' → '{standardized_field}' with context: {service_mapping['level1']}")
        
        # Determine primary service classification
        if service_contexts:
            primary_context = self._select_primary_service(service_contexts)
            result["service_classification"]["level1_category"] = primary_context["level1"]
            result["service_classification"]["level2_service"] = primary_context["level2"]
            
            # Try to identify Level 3 specific service from the answer
            level3 = self._identify_level3_service(
                primary_context,
                result["standardized_fields"].get("specific_service_requested", "")
            )
            result["service_classification"]["level3_specific"] = level3
            
            result["confidence_scores"] = {
                "overall": primary_context.get("confidence", 0.85),
                "level1": 0.95,
                "level2": 0.90,
                "level3": 0.75 if level3 else 0.0
            }
            
            result["processing_notes"].append(
                f"Identified service from {len(service_contexts)} question patterns"
            )
        
        # Add any unmapped fields to standardized_fields with original names
        for field_name, field_value in payload.items():
            if field_value and field_name not in result["original_mapping"]:
                # Keep original field if not mapped
                result["standardized_fields"][field_name] = field_value
        
        logger.info(f"✅ Processed payload with {len(result['standardized_fields'])} fields")
        logger.info(f"📊 Service Classification: L1={result['service_classification']['level1_category']}, "
                   f"L2={result['service_classification']['level2_service']}, "
                   f"L3={result['service_classification']['level3_specific']}")
        
        return result
    
    def _identify_service_from_question(self, question: str, answer: str) -> Optional[Dict]:
        """Identify service context from the question itself"""
        
        for pattern_str, context in self.question_patterns.items():
            if re.search(pattern_str, question, re.IGNORECASE):
                return {
                    "level1": context["level1"],
                    "level2": context["level2"],
                    "context_type": context["context"],
                    "confidence": 0.9,
                    "pattern_matched": pattern_str,
                    "answer": answer
                }
        
        return None
    
    def _get_standardized_field(self, field_name: str) -> Optional[str]:
        """Get the standardized field name for a given input field"""
        
        # Remove question marks and extra spaces
        clean_name = re.sub(r'[?]+', '', field_name).strip()
        clean_name = re.sub(r'\s+', '_', clean_name)
        clean_name = clean_name.replace(' ', '_').lower()
        
        # Check consolidation map
        if clean_name in self.field_consolidation_map:
            return self.field_consolidation_map[clean_name]
        
        # Check for partial matches
        for mapped_field, standard_field in self.field_consolidation_map.items():
            if mapped_field in clean_name or clean_name in mapped_field:
                return standard_field
        
        return None
    
    def _select_primary_service(self, contexts: List[Dict]) -> Dict:
        """Select the primary service context from multiple matches"""
        
        if not contexts:
            return {}
        
        # Sort by confidence and return highest
        sorted_contexts = sorted(contexts, key=lambda x: x.get("confidence", 0), reverse=True)
        return sorted_contexts[0]
    
    def _identify_level3_service(self, context: Dict, answer: str) -> Optional[str]:
        """Identify the specific Level 3 service from the answer text"""
        
        if not answer or not context:
            return None
        
        answer_lower = answer.lower()
        level1 = context.get("level1")
        level2 = context.get("level2")
        
        # Get available Level 3 services for this L1/L2 combination
        if level1 in self.service_hierarchy:
            services = self.service_hierarchy[level1].get("services", {})
            if level2 in services:
                level3_options = services[level2]
                
                # Try exact match first
                for option in level3_options:
                    if option.lower() in answer_lower:
                        return option
                
                # Try keyword matching
                for keyword, mapped_services in self.keyword_mappings.items():
                    if keyword in answer_lower:
                        for service in mapped_services:
                            if service in level3_options:
                                return service
                
                # Try fuzzy matching
                matches = get_close_matches(answer, level3_options, n=1, cutoff=0.6)
                if matches:
                    return matches[0]
        
        return None
    
    def get_service_hierarchy_for_category(self, level1_category: str) -> Dict:
        """Get the complete service hierarchy for a Level 1 category"""
        
        if level1_category in self.service_hierarchy:
            return self.service_hierarchy[level1_category]
        return {}
    
    def validate_service_mapping(self, level1: str, level2: str, level3: str) -> bool:
        """Validate that a service mapping is valid according to the hierarchy"""
        
        if level1 not in self.service_hierarchy:
            return False
            
        services = self.service_hierarchy[level1].get("services", {})
        if level2 not in services:
            return False
            
        if level3 and level3 not in services[level2]:
            return False
            
        return True


# Singleton instance
service_dictionary_mapper = ServiceDictionaryMapper()


# Convenience function for direct usage
def map_form_to_service(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to map form payload to service categories.
    
    Args:
        payload: Raw form data
        
    Returns:
        Mapped service data with standardized fields and classifications
    """
    return service_dictionary_mapper.map_payload_to_service(payload)