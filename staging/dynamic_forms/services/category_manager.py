"""
Dynamic Service Category Manager
Handles CRUD operations for Level 1/2/3 service hierarchies
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from datetime import datetime

from staging.dynamic_forms.models.form_models import (
    DynamicServiceCategory,
    DynamicServiceSubcategory,
    DynamicLevel3Service,
    VendorFormTemplate,
    Base
)

logger = logging.getLogger(__name__)


class ServiceCategoryManager:
    """Manages dynamic service categories and their hierarchies"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    # ============================================
    # LEVEL 1 - PRIMARY CATEGORY MANAGEMENT
    # ============================================
    
    def create_category(self, 
                       category_name: str,
                       display_name: str,
                       description: str = None,
                       form_fields: Dict = None,
                       created_by: str = "system") -> DynamicServiceCategory:
        """
        Create a new Level 1 service category
        
        Example: "Waterfront Vacation Rentals"
        """
        try:
            # Check if category already exists
            existing = self.db.query(DynamicServiceCategory).filter_by(
                category_name=category_name
            ).first()
            
            if existing:
                logger.warning(f"Category '{category_name}' already exists")
                return existing
            
            # Create new category
            category = DynamicServiceCategory(
                category_name=category_name,
                display_name=display_name,
                description=description,
                form_fields=form_fields or {},
                created_by=created_by
            )
            
            self.db.add(category)
            self.db.commit()
            
            logger.info(f"Created Level 1 category: {category_name}")
            return category
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating category: {e}")
            raise
    
    # ============================================
    # LEVEL 2 - SUBCATEGORY MANAGEMENT
    # ============================================
    
    def add_subcategory(self,
                       category_name: str,
                       subcategory_name: str,
                       display_name: str,
                       has_level3_services: bool = False,
                       level3_prompt: str = None) -> DynamicServiceSubcategory:
        """
        Add a Level 2 subcategory to a Level 1 category
        
        Example: "Daily", "Weekly", "Monthly" under "Waterfront Vacation Rentals"
        """
        try:
            # Find parent category
            category = self.db.query(DynamicServiceCategory).filter_by(
                category_name=category_name
            ).first()
            
            if not category:
                raise ValueError(f"Category '{category_name}' not found")
            
            # Check if subcategory exists
            existing = self.db.query(DynamicServiceSubcategory).filter_by(
                category_id=category.id,
                subcategory_name=subcategory_name
            ).first()
            
            if existing:
                logger.warning(f"Subcategory '{subcategory_name}' already exists")
                return existing
            
            # Create subcategory
            subcategory = DynamicServiceSubcategory(
                category_id=category.id,
                subcategory_name=subcategory_name,
                display_name=display_name,
                has_level3_services=has_level3_services,
                level3_prompt=level3_prompt
            )
            
            self.db.add(subcategory)
            self.db.commit()
            
            logger.info(f"Added Level 2 subcategory: {subcategory_name} to {category_name}")
            return subcategory
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding subcategory: {e}")
            raise
    
    # ============================================
    # LEVEL 3 - SPECIFIC SERVICES MANAGEMENT
    # ============================================
    
    def add_level3_services(self,
                           category_name: str,
                           subcategory_name: str,
                           services: List[Dict[str, Any]]) -> List[DynamicLevel3Service]:
        """
        Add Level 3 services to a subcategory
        
        Example services for "Weekly" rental:
        [
            {"name": "With a Pool", "is_premium": True},
            {"name": "With a Jacuzzi", "is_premium": True},
            {"name": "With a Dock", "is_default": True},
            {"name": "With a Boat"},
            {"name": "With Provisions"}
        ]
        """
        try:
            # Find parent subcategory
            category = self.db.query(DynamicServiceCategory).filter_by(
                category_name=category_name
            ).first()
            
            if not category:
                raise ValueError(f"Category '{category_name}' not found")
            
            subcategory = self.db.query(DynamicServiceSubcategory).filter_by(
                category_id=category.id,
                subcategory_name=subcategory_name
            ).first()
            
            if not subcategory:
                raise ValueError(f"Subcategory '{subcategory_name}' not found")
            
            # Enable Level 3 services for this subcategory
            subcategory.has_level3_services = True
            
            created_services = []
            
            for idx, service_data in enumerate(services):
                # Check if service exists
                existing = self.db.query(DynamicLevel3Service).filter_by(
                    subcategory_id=subcategory.id,
                    service_name=service_data["name"]
                ).first()
                
                if existing:
                    logger.warning(f"Level 3 service '{service_data['name']}' already exists")
                    created_services.append(existing)
                    continue
                
                # Create Level 3 service
                service = DynamicLevel3Service(
                    subcategory_id=subcategory.id,
                    service_name=service_data["name"],
                    display_name=service_data.get("display_name", service_data["name"]),
                    description=service_data.get("description"),
                    is_premium=service_data.get("is_premium", False),
                    is_default=service_data.get("is_default", False),
                    base_price=service_data.get("base_price"),
                    sort_order=idx
                )
                
                self.db.add(service)
                created_services.append(service)
            
            self.db.commit()
            
            logger.info(f"Added {len(created_services)} Level 3 services to {subcategory_name}")
            return created_services
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding Level 3 services: {e}")
            raise
    
    # ============================================
    # COMPLETE HIERARCHY CREATION
    # ============================================
    
    def create_complete_hierarchy(self, hierarchy_config: Dict) -> Dict[str, Any]:
        """
        Create a complete Level 1/2/3 hierarchy from configuration
        
        Example config:
        {
            "category": {
                "name": "Waterfront Vacation Rentals",
                "display_name": "Waterfront Vacation Rentals",
                "description": "Luxury waterfront properties for rent"
            },
            "subcategories": [
                {
                    "name": "Daily",
                    "display_name": "Daily Rentals",
                    "level3_services": [
                        {"name": "With a Pool", "is_premium": true},
                        {"name": "With a Dock", "is_default": true}
                    ]
                },
                {
                    "name": "Weekly",
                    "display_name": "Weekly Rentals",
                    "level3_services": [...]
                }
            ]
        }
        """
        try:
            results = {
                "category": None,
                "subcategories": [],
                "level3_services": [],
                "errors": []
            }
            
            # Create Level 1 category
            cat_config = hierarchy_config["category"]
            category = self.create_category(
                category_name=cat_config["name"],
                display_name=cat_config["display_name"],
                description=cat_config.get("description"),
                form_fields=cat_config.get("form_fields")
            )
            results["category"] = category
            
            # Create Level 2 subcategories and Level 3 services
            for sub_config in hierarchy_config.get("subcategories", []):
                # Create subcategory
                has_level3 = bool(sub_config.get("level3_services"))
                
                subcategory = self.add_subcategory(
                    category_name=cat_config["name"],
                    subcategory_name=sub_config["name"],
                    display_name=sub_config["display_name"],
                    has_level3_services=has_level3,
                    level3_prompt=sub_config.get("level3_prompt")
                )
                results["subcategories"].append(subcategory)
                
                # Add Level 3 services if provided
                if sub_config.get("level3_services"):
                    services = self.add_level3_services(
                        category_name=cat_config["name"],
                        subcategory_name=sub_config["name"],
                        services=sub_config["level3_services"]
                    )
                    results["level3_services"].extend(services)
            
            logger.info(f"Successfully created complete hierarchy for {cat_config['name']}")
            return results
            
        except Exception as e:
            logger.error(f"Error creating hierarchy: {e}")
            results["errors"].append(str(e))
            return results
    
    # ============================================
    # RETRIEVAL METHODS
    # ============================================
    
    def get_all_categories(self, active_only: bool = True) -> List[Dict]:
        """Get all Level 1 categories with their complete hierarchies"""
        query = self.db.query(DynamicServiceCategory)
        
        if active_only:
            query = query.filter_by(is_active=True)
        
        categories = query.order_by(DynamicServiceCategory.sort_order).all()
        
        return [cat.to_dict() for cat in categories]
    
    def get_category_hierarchy(self, category_name: str) -> Dict:
        """Get complete hierarchy for a specific category"""
        category = self.db.query(DynamicServiceCategory).filter_by(
            category_name=category_name
        ).first()
        
        if not category:
            return None
        
        hierarchy = {
            "category": category.to_dict(),
            "subcategories": {}
        }
        
        for subcategory in category.subcategories:
            if subcategory.is_active:
                sub_dict = subcategory.to_dict()
                
                # Include Level 3 services if they exist
                if subcategory.has_level3_services:
                    sub_dict["level3_services"] = [
                        svc.to_dict() for svc in subcategory.level3_services 
                        if svc.is_active
                    ]
                
                hierarchy["subcategories"][subcategory.subcategory_name] = sub_dict
        
        return hierarchy
    
    def get_vendor_form_data(self, category_name: Optional[str] = None) -> Dict:
        """
        Get data needed to generate vendor application forms
        Returns all categories or specific category with complete hierarchy
        """
        if category_name:
            return self.get_category_hierarchy(category_name)
        
        # Return all categories for vendor form
        categories = self.get_all_categories()
        
        vendor_form_data = {
            "categories": {},
            "total_categories": len(categories)
        }
        
        for cat in categories:
            vendor_form_data["categories"][cat["category_name"]] = cat
        
        return vendor_form_data
    
    # ============================================
    # UPDATE METHODS
    # ============================================
    
    def update_category(self, category_name: str, updates: Dict) -> bool:
        """Update a Level 1 category"""
        try:
            category = self.db.query(DynamicServiceCategory).filter_by(
                category_name=category_name
            ).first()
            
            if not category:
                logger.error(f"Category '{category_name}' not found")
                return False
            
            for key, value in updates.items():
                if hasattr(category, key):
                    setattr(category, key, value)
            
            category.updated_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Updated category: {category_name}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating category: {e}")
            return False
    
    def toggle_service_active(self, 
                             category_name: str,
                             subcategory_name: str,
                             service_name: Optional[str] = None) -> bool:
        """Toggle active status for a service at any level"""
        try:
            if service_name:
                # Toggle Level 3 service
                service = self.db.query(DynamicLevel3Service).join(
                    DynamicServiceSubcategory
                ).join(
                    DynamicServiceCategory
                ).filter(
                    DynamicServiceCategory.category_name == category_name,
                    DynamicServiceSubcategory.subcategory_name == subcategory_name,
                    DynamicLevel3Service.service_name == service_name
                ).first()
                
                if service:
                    service.is_active = not service.is_active
                    self.db.commit()
                    return True
            
            elif subcategory_name:
                # Toggle Level 2 subcategory
                subcategory = self.db.query(DynamicServiceSubcategory).join(
                    DynamicServiceCategory
                ).filter(
                    DynamicServiceCategory.category_name == category_name,
                    DynamicServiceSubcategory.subcategory_name == subcategory_name
                ).first()
                
                if subcategory:
                    subcategory.is_active = not subcategory.is_active
                    self.db.commit()
                    return True
            
            else:
                # Toggle Level 1 category
                category = self.db.query(DynamicServiceCategory).filter_by(
                    category_name=category_name
                ).first()
                
                if category:
                    category.is_active = not category.is_active
                    self.db.commit()
                    return True
            
            return False
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error toggling service active status: {e}")
            return False
    
    # ============================================
    # EXPORT/IMPORT METHODS
    # ============================================
    
    def export_to_json(self, category_name: Optional[str] = None) -> str:
        """Export categories to JSON format for backup or migration"""
        if category_name:
            data = self.get_category_hierarchy(category_name)
        else:
            data = {
                "categories": self.get_all_categories(),
                "export_timestamp": datetime.utcnow().isoformat(),
                "version": "1.0"
            }
        
        return json.dumps(data, indent=2)
    
    def import_from_json(self, json_data: str) -> Dict[str, Any]:
        """Import categories from JSON data"""
        try:
            data = json.loads(json_data)
            results = {"imported": [], "errors": []}
            
            # Handle single category or multiple
            if "category" in data:
                # Single category hierarchy
                result = self.create_complete_hierarchy(data)
                if result["errors"]:
                    results["errors"].extend(result["errors"])
                else:
                    results["imported"].append(data["category"]["name"])
            
            elif "categories" in data:
                # Multiple categories
                for cat_data in data["categories"]:
                    try:
                        result = self.create_complete_hierarchy(cat_data)
                        if result["errors"]:
                            results["errors"].extend(result["errors"])
                        else:
                            results["imported"].append(cat_data["category"]["name"])
                    except Exception as e:
                        results["errors"].append(f"Error importing {cat_data.get('category', {}).get('name', 'unknown')}: {e}")
            
            return results
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON data: {e}")
            return {"imported": [], "errors": [f"Invalid JSON: {e}"]}