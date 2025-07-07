# api/services/ai_classifier.py
# Enhanced Marine Service Classification with detailed service breakdown
# This REPLACES the existing ai_classifier.py with enhanced functionality

import json
import logging
from typing import Dict, List, Optional, Set
import re

logger = logging.getLogger(__name__)

class AIServiceClassifier:
    """
    Enhanced marine service classifier that returns detailed service breakdown
    for proper lead routing instead of single category oversimplification.
    
    Maintains backward compatibility with existing code while adding enhanced features.
    """
    
    def __init__(self, industry: str = "marine"):
        self.industry = "marine"  # Fixed to marine only
        self.marine_categories = self._load_marine_categories()
        self.service_mappings = self._load_service_mappings()
        self.specific_services_map = self._load_specific_services_map()
        
        logger.info(f"✅ Enhanced AIServiceClassifier initialized with {len(self.service_mappings)} mappings")
    
    def _load_marine_categories(self) -> List[str]:
        """Load the 16 marine service categories"""
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
    
    def _load_service_mappings(self) -> Dict[str, str]:
        """Load service mappings from actual CSV data"""
        return {
            # ===========================================
            # FORM SOURCE MAPPINGS (90% Confidence)
            # ===========================================
            
            # Boat Maintenance Category
            'boat maintenance category': 'Boat Maintenance',
            'boat-maintenance-category': 'Boat Maintenance',
            'boat_maintenance_category': 'Boat Maintenance',
            'boat maintenance': 'Boat Maintenance',
            'boat-maintenance': 'Boat Maintenance',
            'boat_maintenance': 'Boat Maintenance',
            
            # Engines and Generators Category
            'engines and generators category': 'Engines and Generators',
            'engines-and-generators-category': 'Engines and Generators',
            'engines_and_generators_category': 'Engines and Generators',
            'engines and generators': 'Engines and Generators',
            'engines-and-generators': 'Engines and Generators',
            'engines_and_generators': 'Engines and Generators',
            
            # Marine Systems Category
            'marine systems category': 'Marine Systems',
            'marine-systems-category': 'Marine Systems',
            'marine_systems_category': 'Marine Systems',
            'marine systems': 'Marine Systems',
            'marine-systems': 'Marine Systems',
            'marine_systems': 'Marine Systems',
            
            # Boat and Yacht Repair Category
            'boat and yacht repair category': 'Boat and Yacht Repair',
            'boat-and-yacht-repair-category': 'Boat and Yacht Repair',
            'boat_and_yacht_repair_category': 'Boat and Yacht Repair',
            'boat and yacht repair': 'Boat and Yacht Repair',
            'boat-and-yacht-repair': 'Boat and Yacht Repair',
            'boat_and_yacht_repair': 'Boat and Yacht Repair',
            
            # Boat Hauling and Yacht Delivery Category
            'boat hauling and yacht delivery category': 'Boat Hauling and Yacht Delivery',
            'boat-hauling-and-yacht-delivery-category': 'Boat Hauling and Yacht Delivery',
            'boat_hauling_and_yacht_delivery_category': 'Boat Hauling and Yacht Delivery',
            'boat hauling and yacht delivery': 'Boat Hauling and Yacht Delivery',
            'boat-hauling-and-yacht-delivery': 'Boat Hauling and Yacht Delivery',
            'boat_hauling_and_yacht_delivery': 'Boat Hauling and Yacht Delivery',
            
            # Boat Towing Category
            'boat towing category': 'Boat Towing',
            'boat-towing-category': 'Boat Towing',
            'boat_towing_category': 'Boat Towing',
            'boat towing': 'Boat Towing',
            'boat-towing': 'Boat Towing',
            'boat_towing': 'Boat Towing',
            
            # Boat Charters and Rentals Category
            'boat charters and rentals category': 'Boat Charters and Rentals',
            'boat-charters-and-rentals-category': 'Boat Charters and Rentals',
            'boat_charters_and_rentals_category': 'Boat Charters and Rentals',
            'boat charters and rentals': 'Boat Charters and Rentals',
            'boat-charters-and-rentals': 'Boat Charters and Rentals',
            'boat_charters_and_rentals': 'Boat Charters and Rentals',
            
            # Dock and Slip Rental Category
            'dock and slip rental category': 'Dock and Slip Rental',
            'dock-and-slip-rental-category': 'Dock and Slip Rental',
            'dock_and_slip_rental_category': 'Dock and Slip Rental',
            'dock and slip rental': 'Dock and Slip Rental',
            'dock-and-slip-rental': 'Dock and Slip Rental',
            'dock_and_slip_rental': 'Dock and Slip Rental',
            
            # Fuel Delivery Category
            'fuel delivery category': 'Fuel Delivery',
            'fuel-delivery-category': 'Fuel Delivery',
            'fuel_delivery_category': 'Fuel Delivery',
            'fuel delivery': 'Fuel Delivery',
            'fuel-delivery': 'Fuel Delivery',
            'fuel_delivery': 'Fuel Delivery',
            
            # Buying or Selling a Boat Category
            'buying or selling a boat category': 'Buying or Selling a Boat',
            'buying-or-selling-a-boat-category': 'Buying or Selling a Boat',
            'buying_or_selling_a_boat_category': 'Buying or Selling a Boat',
            'buying or selling a boat': 'Buying or Selling a Boat',
            'buying-or-selling-a-boat': 'Buying or Selling a Boat',
            'buying_or_selling_a_boat': 'Buying or Selling a Boat',
            
            # Boater Resources Category
            'boater resources category': 'Boater Resources',
            'boater-resources-category': 'Boater Resources',
            'boater_resources_category': 'Boater Resources',
            'boater resources': 'Boater Resources',
            'boater-resources': 'Boater Resources',
            'boater_resources': 'Boater Resources',
            
            # Maritime Education and Training Category
            'maritime education and training category': 'Maritime Education and Training',
            'maritime-education-and-training-category': 'Maritime Education and Training',
            'maritime_education_and_training_category': 'Maritime Education and Training',
            'maritime education and training': 'Maritime Education and Training',
            'maritime-education-and-training': 'Maritime Education and Training',
            'maritime_education_and_training': 'Maritime Education and Training',
            
            # Yacht Management Category
            'yacht management category': 'Yacht Management',
            'yacht-management-category': 'Yacht Management',
            'yacht_management_category': 'Yacht Management',
            'yacht management': 'Yacht Management',
            'yacht-management': 'Yacht Management',
            'yacht_management': 'Yacht Management',
            
            # Docks, Seawalls and Lifts Category
            'docks, seawalls and lifts category': 'Docks, Seawalls and Lifts',
            'docks-seawalls-and-lifts-category': 'Docks, Seawalls and Lifts',
            'docks_seawalls_and_lifts_category': 'Docks, Seawalls and Lifts',
            'docks, seawalls and lifts': 'Docks, Seawalls and Lifts',
            'docks-seawalls-and-lifts': 'Docks, Seawalls and Lifts',
            'docks_seawalls_and_lifts': 'Docks, Seawalls and Lifts',
            
            # Waterfront Property Category
            'waterfront property category': 'Waterfront Property',
            'waterfront-property-category': 'Waterfront Property',
            'waterfront_property_category': 'Waterfront Property',
            'waterfront property': 'Waterfront Property',
            'waterfront-property': 'Waterfront Property',
            'waterfront_property': 'Waterfront Property',
            
            # Wholesale or Dealer Product Pricing Category
            'wholesale or dealer product pricing category': 'Boater Resources',
            'wholesale-or-dealer-product-pricing-category': 'Boater Resources',
            'wholesale_or_dealer_product_pricing_category': 'Boater Resources',
            'wholesale or dealer product pricing': 'Boater Resources',
            'wholesale-or-dealer-product-pricing': 'Boater Resources',
            'wholesale_or_dealer_product_pricing': 'Boater Resources',
            
            # ===========================================
            # SERVICE REQUEST MAPPINGS (85% Confidence)
            # ===========================================
            
            # Boat Maintenance Services
            'ceramic coating': 'Boat Maintenance',
            'boat detailing': 'Boat Maintenance',
            'bottom cleaning': 'Boat Maintenance',
            'boat and yacht maintenance': 'Boat Maintenance',
            'boat oil change': 'Boat Maintenance',
            'bilge cleaning': 'Boat Maintenance',
            'jet ski maintenance': 'Boat Maintenance',
            'barnacle cleaning': 'Boat Maintenance',
            'yacht fire detection systems': 'Boat Maintenance',
            'boat wrapping and marine protection film': 'Boat Maintenance',
            
            # Engines and Generators Services
            'engines and generators sales/service': 'Engines and Generators',
            'generator sales or service': 'Engines and Generators',
            'engine service or sales': 'Engines and Generators',
            
            # Marine Systems Services
            'marine systems install and sales': 'Marine Systems',
            'yacht stabilizers and seakeepers': 'Marine Systems',
            'instrument panel and dashboard': 'Marine Systems',
            'yacht ac sales': 'Marine Systems',
            'yacht ac service': 'Marine Systems',
            'boat electrical service': 'Marine Systems',
            'boat sound systems': 'Marine Systems',
            'yacht plumbing': 'Marine Systems',
            'boat lighting': 'Marine Systems',
            'yacht refrigeration and watermakers': 'Marine Systems',
            
            # Boat and Yacht Repair Services
            'boat and yacht repair': 'Boat and Yacht Repair',
            'fiberglass repair': 'Boat and Yacht Repair',
            'welding & metal fabrication': 'Boat and Yacht Repair',
            'carpentry & woodwork': 'Boat and Yacht Repair',
            'riggers & masts': 'Boat and Yacht Repair',
            'jet ski repair': 'Boat and Yacht Repair',
            'boat canvas and upholstery': 'Boat and Yacht Repair',
            'boat decking and yacht flooring': 'Boat and Yacht Repair',
            
            # Boat Hauling and Yacht Delivery Services
            'yacht delivery': 'Boat Hauling and Yacht Delivery',
            'boat hauling and transport': 'Boat Hauling and Yacht Delivery',
            
            # Boat Towing Services
            'get emergency tow': 'Boat Towing',
            'get towing membership': 'Boat Towing',
            
            # Boat Charters and Rentals Services
            'boat charters and rentals': 'Boat Charters and Rentals',
            'boat clubs': 'Boat Charters and Rentals',
            'fishing charters': 'Boat Charters and Rentals',
            'yacht and catamaran charters': 'Boat Charters and Rentals',
            'sailboat charters': 'Boat Charters and Rentals',
            'efoil, kiteboarding & wing surfing': 'Boat Charters and Rentals',
            'dive equipment and services': 'Boat Charters and Rentals',
            
            # Dock and Slip Rental Services
            'dock and slip rental': 'Dock and Slip Rental',
            'rent my dock': 'Dock and Slip Rental',
            
            # Fuel Delivery Services
            'fuel delivery': 'Fuel Delivery',
            
            # Buying or Selling a Boat Services
            'buying or selling a boat or yacht': 'Buying or Selling a Boat',
            'boat insurance': 'Buying or Selling a Boat',
            'yacht insurance': 'Buying or Selling a Boat',
            'yacht builder': 'Buying or Selling a Boat',
            'yacht broker': 'Buying or Selling a Boat',
            'boat broker': 'Buying or Selling a Boat',
            'boat builder': 'Buying or Selling a Boat',
            'boat financing': 'Buying or Selling a Boat',
            'boat surveyors': 'Buying or Selling a Boat',
            'yacht dealers': 'Buying or Selling a Boat',
            'boat dealers': 'Buying or Selling a Boat',
            
            # Boater Resources Services
            'boater resources': 'Boater Resources',
            'yacht wifi': 'Boater Resources',
            'provisioning': 'Boater Resources',
            'boat and yacht parts': 'Boater Resources',
            'yacht photography': 'Boater Resources',
            'yacht videography': 'Boater Resources',
            'maritime advertising, pr and web design': 'Boater Resources',
            'yacht crew placement': 'Boater Resources',
            'yacht account management and bookkeeping': 'Boater Resources',
            'boat salvage': 'Boater Resources',
            'wholesale or dealer product pricing': 'Boater Resources',
            
            # Maritime Education and Training Services
            'maritime education and training': 'Maritime Education and Training',
            
            # Yacht Management Services
            'yacht management': 'Yacht Management',
            
            # Docks, Seawalls and Lifts Services
            'dock and seawall builders or repair': 'Docks, Seawalls and Lifts',
            'boat lift installers': 'Docks, Seawalls and Lifts',
            'floating dock sales': 'Docks, Seawalls and Lifts',
            'davit and hydraulic platform': 'Docks, Seawalls and Lifts',
            'hull, dock, seawall or piling cleaning': 'Docks, Seawalls and Lifts',
            
            # Waterfront Property Services
            'waterfront homes for sale': 'Waterfront Property',
            'sell your waterfront home': 'Waterfront Property',
            'waterfront new developments': 'Waterfront Property',
            
            # ===========================================
            # KEYWORD MAPPINGS (70% Confidence)
            # ===========================================
            
            # Boat Maintenance Keywords
            'ceramic': 'Boat Maintenance',
            'coating': 'Boat Maintenance',
            'detailing': 'Boat Maintenance',
            'detail': 'Boat Maintenance',
            'cleaning': 'Boat Maintenance',
            'clean': 'Boat Maintenance',
            'maintenance': 'Boat Maintenance',
            'maintain': 'Boat Maintenance',
            'wash': 'Boat Maintenance',
            'wax': 'Boat Maintenance',
            'polish': 'Boat Maintenance',
            'bottom': 'Boat Maintenance',
            'hull': 'Boat Maintenance',
            'bilge': 'Boat Maintenance',
            'barnacle': 'Boat Maintenance',
            'wrapping': 'Boat Maintenance',
            'protection film': 'Boat Maintenance',
            'fire detection': 'Boat Maintenance',
            'oil change': 'Boat Maintenance',
            
            # Engine and Generator Keywords
            'engine': 'Engines and Generators',
            'motor': 'Engines and Generators',
            'generator': 'Engines and Generators',
            'outboard': 'Engines and Generators',
            'inboard': 'Engines and Generators',
            'diesel': 'Engines and Generators',
            'gasoline': 'Engines and Generators',
            
            # Marine Systems Keywords
            'electrical': 'Marine Systems',
            'electric': 'Marine Systems',
            'plumbing': 'Marine Systems',
            'hvac': 'Marine Systems',
            'air conditioning': 'Marine Systems',
            'ac service': 'Marine Systems',
            'ac sales': 'Marine Systems',
            'sound system': 'Marine Systems',
            'audio': 'Marine Systems',
            'lighting': 'Marine Systems',
            'lights': 'Marine Systems',
            'refrigeration': 'Marine Systems',
            'watermaker': 'Marine Systems',
            'stabilizer': 'Marine Systems',
            'seakeeper': 'Marine Systems',
            'dashboard': 'Marine Systems',
            'instrument': 'Marine Systems',
            'panel': 'Marine Systems',
            
            # Repair Keywords
            'repair': 'Boat and Yacht Repair',
            'fix': 'Boat and Yacht Repair',
            'fiberglass': 'Boat and Yacht Repair',
            'gelcoat': 'Boat and Yacht Repair',
            'welding': 'Boat and Yacht Repair',
            'metal fabrication': 'Boat and Yacht Repair',
            'carpentry': 'Boat and Yacht Repair',
            'woodwork': 'Boat and Yacht Repair',
            'rigger': 'Boat and Yacht Repair',
            'mast': 'Boat and Yacht Repair',
            'canvas': 'Boat and Yacht Repair',
            'upholstery': 'Boat and Yacht Repair',
            'decking': 'Boat and Yacht Repair',
            'flooring': 'Boat and Yacht Repair',
            
            # Transport Keywords
            'delivery': 'Boat Hauling and Yacht Delivery',
            'transport': 'Boat Hauling and Yacht Delivery',
            'hauling': 'Boat Hauling and Yacht Delivery',
            'haul': 'Boat Hauling and Yacht Delivery',
            'shipping': 'Boat Hauling and Yacht Delivery',
            'move': 'Boat Hauling and Yacht Delivery',
            'relocate': 'Boat Hauling and Yacht Delivery',
            
            # Towing Keywords
            'tow': 'Boat Towing',
            'towing': 'Boat Towing',
            'emergency': 'Boat Towing',
            'breakdown': 'Boat Towing',
            'assistance': 'Boat Towing',
            'rescue': 'Boat Towing',
            'membership': 'Boat Towing',
            
            # Charter Keywords
            'charter': 'Boat Charters and Rentals',
            'rental': 'Boat Charters and Rentals',
            'rent': 'Boat Charters and Rentals',
            'club': 'Boat Charters and Rentals',
            'fishing': 'Boat Charters and Rentals',
            'catamaran': 'Boat Charters and Rentals',
            'sailboat': 'Boat Charters and Rentals',
            'efoil': 'Boat Charters and Rentals',
            'kiteboarding': 'Boat Charters and Rentals',
            'wing surfing': 'Boat Charters and Rentals',
            'diving': 'Boat Charters and Rentals',
            'dive': 'Boat Charters and Rentals',
            
            # Dock Keywords
            'dock': 'Docks, Seawalls and Lifts',
            'seawall': 'Docks, Seawalls and Lifts',
            'lift': 'Docks, Seawalls and Lifts',
            'floating dock': 'Docks, Seawalls and Lifts',
            'davit': 'Docks, Seawalls and Lifts',
            'hydraulic': 'Docks, Seawalls and Lifts',
            'platform': 'Docks, Seawalls and Lifts',
            'piling': 'Docks, Seawalls and Lifts',
            'slip': 'Dock and Slip Rental',
            'marina': 'Dock and Slip Rental',
            'berth': 'Dock and Slip Rental',
            'mooring': 'Dock and Slip Rental',
            
            # Buying/Selling Keywords
            'buy': 'Buying or Selling a Boat',
            'sell': 'Buying or Selling a Boat',
            'sale': 'Buying or Selling a Boat',
            'purchase': 'Buying or Selling a Boat',
            'broker': 'Buying or Selling a Boat',
            'dealer': 'Buying or Selling a Boat',
            'builder': 'Buying or Selling a Boat',
            'insurance': 'Buying or Selling a Boat',
            'financing': 'Buying or Selling a Boat',
            'surveyor': 'Buying or Selling a Boat',
            'survey': 'Buying or Selling a Boat',
            
            # Waterfront Property Keywords
            'waterfront': 'Waterfront Property',
            'home': 'Waterfront Property',
            'property': 'Waterfront Property',
            'real estate': 'Waterfront Property',
            'development': 'Waterfront Property',
            
            # Management Keywords
            'management': 'Yacht Management',
            'crew': 'Boater Resources',
            'captain': 'Maritime Education and Training',
            'training': 'Maritime Education and Training',
            'education': 'Maritime Education and Training',
            'lessons': 'Maritime Education and Training',
            
            # Resources Keywords
            'wifi': 'Boater Resources',
            'internet': 'Boater Resources',
            'provisioning': 'Boater Resources',
            'supplies': 'Boater Resources',
            'parts': 'Boater Resources',
            'photography': 'Boater Resources',
            'videography': 'Boater Resources',
            'advertising': 'Boater Resources',
            'marketing': 'Boater Resources',
            'web design': 'Boater Resources',
            'bookkeeping': 'Boater Resources',
            'accounting': 'Boater Resources',
            'salvage': 'Boater Resources',
            'wholesale': 'Boater Resources',
            
            # Fuel Keywords
            'fuel': 'Fuel Delivery',
            'gas': 'Fuel Delivery',
            'gasoline': 'Fuel Delivery',
            'diesel fuel': 'Fuel Delivery',
            'refuel': 'Fuel Delivery',
            'bunker': 'Fuel Delivery'
        }
    
    def _load_specific_services_map(self) -> Dict[str, List[str]]:
        """Map primary categories to their specific services for detailed breakdown"""
        return {
            "Boat Maintenance": [
                "Ceramic Coating",
                "Boat Detailing", 
                "Bottom Cleaning",
                "Boat and Yacht Maintenance",
                "Boat Oil Change",
                "Bilge Cleaning",
                "Jet Ski Maintenance",
                "Barnacle Cleaning",
                "Yacht Fire Detection Systems",
                "Boat Wrapping and Marine Protection Film"
            ],
            
            "Engines and Generators": [
                "Engines and Generators Sales/Service",
                "Generator Sales or Service",
                "Engine Service or Sales"
            ],
            
            "Marine Systems": [
                "Marine Systems Install and Sales",
                "Yacht Stabilizers and Seakeepers",
                "Instrument Panel and Dashboard",
                "Yacht AC Sales",
                "Yacht AC Service",
                "Boat Electrical Service",
                "Boat Sound Systems",
                "Yacht Plumbing",
                "Boat Lighting",
                "Yacht Refrigeration and Watermakers"
            ],
            
            "Boat and Yacht Repair": [
                "Boat and Yacht Repair",
                "Fiberglass Repair",
                "Welding & Metal Fabrication",
                "Carpentry & Woodwork",
                "Riggers & Masts",
                "Jet Ski Repair",
                "Boat Canvas and Upholstery",
                "Boat Decking and Yacht Flooring"
            ],
            
            "Boat Hauling and Yacht Delivery": [
                "Yacht Delivery",
                "Boat Hauling and Transport"
            ],
            
            "Boat Towing": [
                "Get Emergency Tow",
                "Get Towing Membership"
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
            
            "Dock and Slip Rental": [
                "Dock and Slip Rental",
                "Rent My Dock"
            ],
            
            "Fuel Delivery": [
                "Fuel Delivery"
            ],
            
            "Buying or Selling a Boat": [
                "Buying or Selling a Boat or Yacht",
                "Boat Insurance",
                "Yacht Insurance",
                "Yacht Builder",
                "Yacht Broker",
                "Boat Broker",
                "Boat Builder",
                "Boat Financing",
                "Boat Surveyors",
                "Yacht Dealers",
                "Boat Dealers"
            ],
            
            "Boater Resources": [
                "Boater Resources",
                "Yacht WiFi",
                "Provisioning",
                "Boat and Yacht Parts",
                "Yacht Photography",
                "Yacht Videography",
                "Maritime Advertising, PR and Web Design",
                "Yacht Crew Placement",
                "Yacht Account Management and Bookkeeping",
                "Boat Salvage",
                "Wholesale or Dealer Product Pricing"
            ],
            
            "Maritime Education and Training": [
                "Maritime Education and Training"
            ],
            
            "Yacht Management": [
                "Yacht Management"
            ],
            
            "Docks, Seawalls and Lifts": [
                "Dock and Seawall Builders or Repair",
                "Boat Lift Installers",
                "Floating Dock Sales",
                "Davit and Hydraulic Platform",
                "Hull, Dock, Seawall or Piling Cleaning"
            ],
            
            "Waterfront Property": [
                "Waterfront Homes For Sale",
                "Sell Your Waterfront Home",
                "Waterfront New Developments"
            ]
        }

    # ===========================================
    # LEGACY COMPATIBILITY METHODS
    # ===========================================
    
    async def classify_service(self, form_data: Dict) -> Dict:
        """
        LEGACY METHOD: Maintained for backward compatibility.
        Returns simple classification format expected by existing code.
        """
        # Get detailed classification first
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
    # ENHANCED CLASSIFICATION METHODS
    # ===========================================

    async def classify_service_detailed(self, form_data: Dict) -> Dict:
        """
        Enhanced service classification that returns detailed service breakdown.
        This is the main method for the enhanced system.
        """
        # Clean and normalize input - FIXED: Use correct field names from webhook normalization
        form_source = form_data.get('form_identifier', '').lower().strip()
        service_requested = form_data.get('specific_service_needed', '').lower().strip()
        special_requests = form_data.get('special_requests__notes', '').lower().strip()
        
        # Extract coverage area
        coverage_area = self.extract_coverage_area(form_data)
        
        # Determine priority level
        priority_level = self._determine_priority(form_data)
        
        # Find primary category
        primary_category = self._find_primary_category(form_source, service_requested, special_requests)
        
        # Find specific services requested
        specific_services = self._find_specific_services(service_requested, special_requests, primary_category)
        
        # Build detailed classification result
        result = {
            "primary_category": primary_category["category"],
            "confidence": primary_category["confidence"],
            "reasoning": primary_category["reasoning"],
            "specific_services": specific_services,
            "coverage_area": coverage_area,
            "priority_level": priority_level,
            "service_complexity": self._assess_complexity(specific_services),
            "estimated_duration": self._estimate_duration(specific_services),
            "requires_emergency_response": self._check_emergency(form_data),
            "keywords_found": primary_category.get("keywords_found", []),
            "alternative_categories": primary_category.get("alternative_categories", [])
        }
        
        logger.info(f"🔍 DETAILED SERVICE CLASSIFICATION:")
        logger.info(f"   Primary Category: {result['primary_category']} ({result['confidence']*100:.0f}%)")
        logger.info(f"   Specific Services: {result['specific_services']}")
        logger.info(f"   Coverage Area: {result['coverage_area']['zip_code']} ({result['coverage_area']['city']}, {result['coverage_area']['state']})")
        logger.info(f"   Priority Level: {result['priority_level']}")
        logger.info(f"   Service Complexity: {result['service_complexity']}")
        
        return result

    def extract_coverage_area(self, form_data: Dict) -> Dict[str, str]:
        """Extract coverage area information from form data"""
        coverage_info = {
            "zip_code": "",
            "city": "",
            "state": "",
            "county": "",
            "coverage_type": "zip"
        }
        
        # Extract ZIP code from various field names
        zip_fields = [
            'zip_code_of_service',  # Mapped field from webhook
            'zip_code',             # Secondary mapped field
            'zipCode', 'serviceZipCode', 'postal_code', 'postalCode', 'zip', 'service_zip'
        ]
        
        for field in zip_fields:
            if field in form_data and form_data[field]:
                coverage_info["zip_code"] = str(form_data[field]).strip()
                break
        
        # Extract city and state
        if 'city' in form_data:
            coverage_info["city"] = str(form_data['city']).strip()
        if 'state' in form_data:
            coverage_info["state"] = str(form_data['state']).strip()
        
        # Try to extract location from address fields
        address_fields = ['address', 'address1', 'service_address', 'location']
        for field in address_fields:
            if field in form_data and form_data[field]:
                address = str(form_data[field]).strip()
                # Simple pattern matching for ZIP codes in address
                zip_match = re.search(r'\b\d{5}(?:-\d{4})?\b', address)
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

    def _find_specific_services(self, service_requested: str, special_requests: str, primary_category: Dict) -> List[str]:
        """Find specific services requested within the primary category"""
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

    def _determine_priority(self, form_data: Dict) -> str:
        """Determine priority level based on form data"""
        emergency_keywords = ['emergency', 'urgent', 'asap', 'immediate', 'now', 'breakdown', 'sinking', 'stranded']
        
        # Check various text fields for emergency keywords
        text_fields = ['special_requests', 'message', 'description', 'service_requested']
        for field in text_fields:
            if field in form_data and form_data[field]:
                text = str(form_data[field]).lower()
                if any(keyword in text for keyword in emergency_keywords):
                    return "high"
        
        # Check for towing services (usually urgent)
        if 'towing' in str(form_data.get('service_requested', '')).lower():
            return "high"
        
        return "normal"

    def _assess_complexity(self, specific_services: List[str]) -> str:
        """Assess service complexity based on number and type of services"""
        if len(specific_services) == 1:
            return "simple"
        elif len(specific_services) <= 3:
            return "moderate"
        else:
            return "complex"

    def _estimate_duration(self, specific_services: List[str]) -> str:
        """Estimate service duration based on services requested"""
        quick_services = ['fuel delivery', 'towing', 'emergency']
        long_services = ['fiberglass repair', 'engine service', 'welding', 'carpentry']
        
        service_text = ' '.join(specific_services).lower()
        
        if any(service in service_text for service in quick_services):
            return "short"
        elif any(service in service_text for service in long_services):
            return "long"
        else:
            return "medium"

    def _check_emergency(self, form_data: Dict) -> bool:
        """Check if this is an emergency service request"""
        return self._determine_priority(form_data) == "high"

    # ===========================================
    # UTILITY METHODS
    # ===========================================

    def get_all_categories(self) -> List[str]:
        """Get all available marine service categories"""
        return self.marine_categories.copy()

    def get_mapping_stats(self) -> Dict:
        """Get statistics about the service mappings"""
        stats = {
            "total_mappings": len(self.service_mappings),
            "total_categories": len(self.marine_categories),
            "industry": "marine",
            "category_distribution": {}
        }
        
        # Count mappings per category
        for category in self.marine_categories:
            count = sum(1 for cat in self.service_mappings.values() if cat == category)
            stats["category_distribution"][category] = count
        
        return stats

    def validate_classification(self, result: Dict) -> bool:
        """Validate a classification result"""
        required_fields = ['primary_category', 'confidence', 'reasoning', 'specific_services']
        
        # Check all required fields are present
        for field in required_fields:
            if field not in result:
                logger.error(f"❌ Missing required field in classification result: {field}")
                return False
        
        # Check category is valid
        if result['primary_category'] not in self.marine_categories:
            logger.error(f"❌ Invalid category in classification result: {result['primary_category']}")
            return False
        
        # Check confidence is in valid range
        if not (0 <= result['confidence'] <= 1):
            logger.error(f"❌ Invalid confidence in classification result: {result['confidence']}")
            return False
        
        return True
