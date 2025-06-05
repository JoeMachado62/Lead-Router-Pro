import json
from typing import Dict, Tuple
import os
import logging

logger = logging.getLogger(__name__)

class AIServiceClassifier:
    def __init__(self, industry: str = "general"):
        self.industry = industry
        self.industry_categories = self._load_industry_categories()
    
    def _load_industry_categories(self) -> list:
        """Load service categories specific to industry"""
        categories = {
            "marine": [
                "Boat Maintenance", "Engines and Generators", "Marine Systems",
                "Boat and Yacht Repair", "Boat Hauling and Yacht Delivery",
                "Boat Towing", "Boat Charters and Rentals", "Dock and Slip Rental",
                "Fuel Delivery", "Buying or Selling a Boat", "Boater Resources",
                "Maritime Education and Training", "Yacht Management",
                "Docks, Seawalls and Lifts", "Waterfront Property"
            ],
            "home_services": [
                "HVAC", "Plumbing", "Electrical", "Roofing", "Flooring",
                "Painting", "Landscaping", "Cleaning", "Security Systems",
                "Pool Services", "Pest Control", "Appliance Repair"
            ],
            "automotive": [
                "Auto Repair", "Oil Change", "Tire Services", "Body Work",
                "Detailing", "Towing", "Transmission", "Brake Service",
                "Engine Repair", "Diagnostic", "Auto Sales"
            ],
            "general": [
                "Maintenance", "Repair", "Installation", "Consultation",
                "Emergency Service", "Inspection", "Sales", "Rental"
            ]
        }
        return categories.get(self.industry, categories["general"])
    
    async def classify_service(self, form_data: Dict) -> Dict:
        """Classify service using rule-based approach (fallback for now)"""
        
        # For now, use the existing rule-based classification from the original lead_router
        # This can be enhanced with AI later when API keys are configured
        
        form_text = self._prepare_form_text(form_data)
        result = self._rule_based_classification(form_data)
        
        logger.info(f"Classified service: {result}")
        return result
    
    def _prepare_form_text(self, form_data: Dict) -> str:
        """Prepare form data for analysis"""
        relevant_fields = [
            'service_requested', 'service_type', 'special_requests',
            'message', 'description', 'form_source'
        ]
        
        text_parts = []
        for field in relevant_fields:
            if field in form_data and form_data[field]:
                text_parts.append(f"{field}: {form_data[field]}")
        
        return "\n".join(text_parts)
    
    def _rule_based_classification(self, form_data: Dict) -> Dict:
        """Rule-based classification using existing logic"""
        
        # Service mappings from original lead_router.py
        service_mappings = {
            # Form-based mappings
            'boat-detailing': 'Boat Maintenance',
            'engine-repair': 'Engines and Generators', 
            'yacht-welding': 'Boat and Yacht Repair',
            'bottom-cleaning': 'Boat Maintenance',
            'ac-repair': 'Marine Systems',
            'electrical-repair': 'Marine Systems',
            'plumbing-repair': 'Marine Systems',
            'canvas-repair': 'Boat and Yacht Repair',
            'fiberglass-repair': 'Boat and Yacht Repair',
            'boat-transport': 'Boat Hauling and Yacht Delivery',
            'yacht-delivery': 'Boat Hauling and Yacht Delivery',
            'boat-towing': 'Boat Towing',
            'emergency-tow': 'Boat Towing',
            'boat-charter': 'Boat Charters and Rentals',
            'yacht-charter': 'Boat Charters and Rentals',
            'boat-rental': 'Boat Charters and Rentals',
            'dock-rental': 'Dock and Slip Rental',
            'slip-rental': 'Dock and Slip Rental',
            'marina-services': 'Dock and Slip Rental',
            'fuel-delivery': 'Fuel Delivery',
            'boat-sales': 'Buying or Selling a Boat',
            'yacht-sales': 'Buying or Selling a Boat',
            'boat-brokerage': 'Buying or Selling a Boat',
            'marine-insurance': 'Boater Resources',
            'boat-financing': 'Boater Resources',
            'marine-surveyor': 'Boater Resources',
            'captain-services': 'Maritime Education and Training',
            'boat-training': 'Maritime Education and Training',
            'sailing-lessons': 'Maritime Education and Training',
            'yacht-management': 'Yacht Management',
            'dock-installation': 'Docks, Seawalls and Lifts',
            'seawall-repair': 'Docks, Seawalls and Lifts',
            'boat-lift': 'Docks, Seawalls and Lifts',
            'waterfront-property': 'Waterfront Property',
            
            # Keyword-based mappings
            'detailing': 'Boat Maintenance',
            'cleaning': 'Boat Maintenance',
            'wash': 'Boat Maintenance',
            'wax': 'Boat Maintenance',
            'engine': 'Engines and Generators',
            'motor': 'Engines and Generators',
            'generator': 'Engines and Generators',
            'outboard': 'Engines and Generators',
            'inboard': 'Engines and Generators',
            'electrical': 'Marine Systems',
            'plumbing': 'Marine Systems',
            'hvac': 'Marine Systems',
            'air conditioning': 'Marine Systems',
            'welding': 'Boat and Yacht Repair',
            'fiberglass': 'Boat and Yacht Repair',
            'gelcoat': 'Boat and Yacht Repair',
            'hull': 'Boat and Yacht Repair',
            'canvas': 'Boat and Yacht Repair',
            'upholstery': 'Boat and Yacht Repair',
            'transport': 'Boat Hauling and Yacht Delivery',
            'delivery': 'Boat Hauling and Yacht Delivery',
            'haul': 'Boat Hauling and Yacht Delivery',
            'towing': 'Boat Towing',
            'tow': 'Boat Towing',
            'emergency': 'Boat Towing',
            'charter': 'Boat Charters and Rentals',
            'rental': 'Boat Charters and Rentals',
            'rent': 'Boat Charters and Rentals',
            'dock': 'Dock and Slip Rental',
            'slip': 'Dock and Slip Rental',
            'marina': 'Dock and Slip Rental',
            'fuel': 'Fuel Delivery',
            'gas': 'Fuel Delivery',
            'diesel': 'Fuel Delivery',
            'sales': 'Buying or Selling a Boat',
            'broker': 'Buying or Selling a Boat',
            'buy': 'Buying or Selling a Boat',
            'sell': 'Buying or Selling a Boat',
            'insurance': 'Boater Resources',
            'survey': 'Boater Resources',
            'financing': 'Boater Resources',
            'training': 'Maritime Education and Training',
            'lessons': 'Maritime Education and Training',
            'captain': 'Maritime Education and Training',
            'education': 'Maritime Education and Training',
            'management': 'Yacht Management',
            'seawall': 'Docks, Seawalls and Lifts',
            'lift': 'Docks, Seawalls and Lifts',
            'waterfront': 'Waterfront Property',
            'property': 'Waterfront Property'
        }
        
        # Check form name/source first
        form_source = form_data.get('form_source', '').lower()
        if form_source in service_mappings:
            return {
                "category": service_mappings[form_source],
                "confidence": 0.9,
                "reasoning": f"Matched form source: {form_source}",
                "keywords_found": [form_source],
                "alternative_categories": []
            }
        
        # Check specific service field
        service_field = form_data.get('service_requested', '').lower()
        if service_field in service_mappings:
            return {
                "category": service_mappings[service_field],
                "confidence": 0.85,
                "reasoning": f"Matched service field: {service_field}",
                "keywords_found": [service_field],
                "alternative_categories": []
            }
        
        # Check for keywords in service description
        service_text = f"{service_field} {form_data.get('special_requests', '')}".lower()
        
        for keyword, service_type in service_mappings.items():
            if keyword in service_text:
                return {
                    "category": service_type,
                    "confidence": 0.7,
                    "reasoning": f"Found keyword '{keyword}' in service description",
                    "keywords_found": [keyword],
                    "alternative_categories": []
                }
        
        # Default fallback
        default_category = self.industry_categories[0] if self.industry_categories else "General Service"
        return {
            "category": default_category,
            "confidence": 0.3,
            "reasoning": "No clear classification, using default category",
            "keywords_found": [],
            "alternative_categories": []
        }
