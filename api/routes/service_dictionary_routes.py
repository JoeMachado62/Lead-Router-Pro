"""
API routes for serving the unified DockSide Pros service dictionary
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
import logging
from api.services.dockside_pros_service_dictionary import (
    DOCKSIDE_PROS_SERVICES,
    get_all_categories,
    get_subcategories_for_category,
    get_specific_services,
    validate_service_hierarchy
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/services", tags=["Service Dictionary"])

@router.get("/dictionary")
async def get_service_dictionary() -> Dict:
    """
    Get the complete DockSide Pros service dictionary.
    Returns the full hierarchy with categories, subcategories, and specific services.
    """
    try:
        # Transform the dictionary to a more frontend-friendly format
        transformed_dict = {}
        
        for cat_id, cat_data in DOCKSIDE_PROS_SERVICES.items():
            category_name = cat_data["name"]
            transformed_dict[category_name] = {
                "id": cat_id,
                "name": category_name,
                "subcategories": {}
            }
            
            for subcat_name, subcat_data in cat_data["subcategories"].items():
                transformed_dict[category_name]["subcategories"][subcat_name] = {
                    "name": subcat_name,
                    "request_a_pro": subcat_data.get("request_a_pro", True),
                    "specific_services": subcat_data.get("specific_services", []),
                    "hardcoded_vendor": subcat_data.get("hardcoded_vendor", None)
                }
        
        return {
            "success": True,
            "data": transformed_dict,
            "total_categories": len(transformed_dict)
        }
    except Exception as e:
        logger.error(f"Error getting service dictionary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories")
async def get_categories() -> Dict:
    """
    Get all primary category names.
    """
    try:
        categories = get_all_categories()
        return {
            "success": True,
            "categories": categories,
            "count": len(categories)
        }
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/subcategories/{category_name}")
async def get_subcategories(category_name: str) -> Dict:
    """
    Get all subcategories for a specific category.
    """
    try:
        subcategories = get_subcategories_for_category(category_name)
        if not subcategories:
            raise HTTPException(status_code=404, detail=f"Category '{category_name}' not found")
        
        return {
            "success": True,
            "category": category_name,
            "subcategories": subcategories,
            "count": len(subcategories)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting subcategories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/specific-services/{category_name}/{subcategory_name}")
async def get_specific_services_endpoint(category_name: str, subcategory_name: str) -> Dict:
    """
    Get specific services (Level 3) for a given category and subcategory.
    """
    try:
        services = get_specific_services(category_name, subcategory_name)
        
        return {
            "success": True,
            "category": category_name,
            "subcategory": subcategory_name,
            "specific_services": services,
            "count": len(services),
            "has_services": len(services) > 0
        }
    except Exception as e:
        logger.error(f"Error getting specific services: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate")
async def validate_service(data: Dict) -> Dict:
    """
    Validate a service hierarchy (category, subcategory, and optionally specific service).
    """
    try:
        category = data.get("category")
        subcategory = data.get("subcategory")
        specific_service = data.get("specific_service")
        
        if not category or not subcategory:
            raise HTTPException(status_code=400, detail="Category and subcategory are required")
        
        is_valid, message = validate_service_hierarchy(category, subcategory, specific_service)
        
        return {
            "success": is_valid,
            "message": message,
            "validated": {
                "category": category,
                "subcategory": subcategory,
                "specific_service": specific_service
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating service: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dictionary/formatted")
async def get_formatted_dictionary() -> Dict:
    """
    Get the service dictionary formatted specifically for the vendor application form.
    Includes proper structure for Level 3 services.
    """
    try:
        formatted = {}
        
        for cat_data in DOCKSIDE_PROS_SERVICES.values():
            category_name = cat_data["name"]
            
            # Build subcategories list
            subcategories = []
            level3_services = {}
            
            for subcat_name, subcat_data in cat_data["subcategories"].items():
                subcategories.append(subcat_name)
                
                # Add Level 3 services if they exist
                specific_services = subcat_data.get("specific_services", [])
                if specific_services:
                    level3_services[subcat_name] = specific_services
            
            formatted[category_name] = {
                "subcategories": subcategories,
                "level3Services": level3_services
            }
        
        return {
            "success": True,
            "data": formatted
        }
    except Exception as e:
        logger.error(f"Error getting formatted dictionary: {e}")
        raise HTTPException(status_code=500, detail=str(e))