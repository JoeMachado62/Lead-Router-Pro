from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SimpleLeadRouter:
    """Simplified lead router that works with the existing system"""
    
    def __init__(self, account_id: Optional[str] = None):
        self.account_id = account_id
        self.service_mappings = self._load_service_mappings()
    
    def _load_service_mappings(self) -> Dict[str, str]:
        """Load service type mappings for classification"""
        return {
            # Marine services
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
            
            # Keywords
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
    
    def classify_service(self, form_data: Dict) -> Dict:
        """Classify the service type from form data"""
        # Check form name/source first
        form_source = form_data.get('form_source', '').lower()
        if form_source in self.service_mappings:
            return {
                "category": self.service_mappings[form_source],
                "confidence": 0.9,
                "reasoning": f"Matched form source: {form_source}",
                "keywords_found": [form_source]
            }
        
        # Check specific service field
        service_field = form_data.get('service_requested', '').lower()
        if service_field in self.service_mappings:
            return {
                "category": self.service_mappings[service_field],
                "confidence": 0.85,
                "reasoning": f"Matched service field: {service_field}",
                "keywords_found": [service_field]
            }
        
        # Check for keywords in service description
        service_text = f"{service_field} {form_data.get('special_requests', '')}".lower()
        
        for keyword, service_type in self.service_mappings.items():
            if keyword in service_text:
                return {
                    "category": service_type,
                    "confidence": 0.7,
                    "reasoning": f"Found keyword '{keyword}' in service description",
                    "keywords_found": [keyword]
                }
        
        # Default fallback
        return {
            "category": "Boater Resources",
            "confidence": 0.3,
            "reasoning": "No clear classification, using default category",
            "keywords_found": []
        }
    
    def calculate_lead_score(self, form_data: Dict, service_info: Dict) -> Dict:
        """Calculate lead value and priority"""
        # Base values for different service types
        service_values = {
            "Boat Maintenance": 500,
            "Engines and Generators": 2000,
            "Marine Systems": 1500,
            "Boat and Yacht Repair": 3000,
            "Boat Hauling and Yacht Delivery": 1000,
            "Boat Towing": 300,
            "Boat Charters and Rentals": 800,
            "Dock and Slip Rental": 200,
            "Fuel Delivery": 100,
            "Buying or Selling a Boat": 5000,
            "Boater Resources": 250,
            "Maritime Education and Training": 400,
            "Yacht Management": 2000,
            "Docks, Seawalls and Lifts": 5000,
            "Waterfront Property": 10000
        }
        
        base_value = service_values.get(service_info['category'], 500)
        
        # Completeness score
        required_fields = ['name', 'email', 'phone', 'service_requested']
        optional_fields = ['zip_code', 'special_requests', 'vessel_make', 'vessel_model']
        
        required_score = sum(1 for field in required_fields if form_data.get(field))
        optional_score = sum(1 for field in optional_fields if form_data.get(field))
        
        completeness_score = (required_score / len(required_fields)) * 0.7 + (optional_score / len(optional_fields)) * 0.3
        
        # Urgency score
        urgency_keywords = ['emergency', 'urgent', 'asap', 'immediately', 'broken', 'not working', 'help']
        text = f"{form_data.get('service_requested', '')} {form_data.get('special_requests', '')}".lower()
        urgency_count = sum(1 for keyword in urgency_keywords if keyword in text)
        urgency_score = min(urgency_count * 0.3, 1.0)
        
        # Calculate final values
        estimated_value = base_value * (1 + completeness_score * 0.5)
        priority_score = (urgency_score * 0.4) + (completeness_score * 0.3) + (estimated_value / 10000 * 0.3)
        
        return {
            "estimated_value": round(estimated_value, 2),
            "priority": round(priority_score, 2),
            "factors": {
                "completeness": completeness_score,
                "urgency": urgency_score
            }
        }
    
    async def process_lead(self, form_data: Dict) -> Dict:
        """Process a lead with simplified logic"""
        try:
            logger.info(f"Processing lead: {form_data}")
            
            # Step 1: Classify service
            service_info = self.classify_service(form_data)
            
            # Step 2: Calculate lead score
            lead_score = self.calculate_lead_score(form_data, service_info)
            
            # Step 3: Create result
            result = {
                "success": True,
                "lead_id": f"lead_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "service_category": service_info['category'],
                "confidence_score": service_info['confidence'],
                "estimated_value": lead_score['estimated_value'],
                "priority_score": lead_score['priority'],
                "reasoning": service_info['reasoning'],
                "keywords_found": service_info['keywords_found']
            }
            
            logger.info(f"Lead processed successfully: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing lead: {str(e)}")
            return {"success": False, "error": str(e)}
