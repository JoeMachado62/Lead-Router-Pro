"""
Service Hierarchy API Routes
Provides endpoints to serve the complete service hierarchy to frontend applications
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any
import logging

from api.services.service_categories import (
    SERVICE_CATEGORIES,
    LEVEL_3_SERVICES,
    service_manager
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/services", tags=["Services"])


@router.get("/hierarchy")
async def get_service_hierarchy() -> Dict[str, Any]:
    """
    Get the complete service hierarchy including Level 1, 2, and 3 services.
    
    Returns:
        Dict containing the complete service hierarchy structure
    """
    try:
        # Build the response structure matching vendor_application_final.html format
        hierarchy = {}
        
        for category in SERVICE_CATEGORIES.keys():
            hierarchy[category] = {
                "subcategories": SERVICE_CATEGORIES.get(category, []),
                "level3Services": LEVEL_3_SERVICES.get(category, {})
            }
        
        return {
            "success": True,
            "data": hierarchy,
            "stats": {
                "total_categories": len(SERVICE_CATEGORIES),
                "categories_with_level3": len(LEVEL_3_SERVICES)
            }
        }
    except Exception as e:
        logger.error(f"Error fetching service hierarchy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def get_categories() -> Dict[str, Any]:
    """
    Get list of all Level 1 service categories.
    
    Returns:
        List of category names
    """
    try:
        categories = list(SERVICE_CATEGORIES.keys())
        return {
            "success": True,
            "data": categories,
            "total": len(categories)
        }
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/category/{category_name}/services")
async def get_category_services(category_name: str) -> Dict[str, Any]:
    """
    Get Level 2 services for a specific category.
    
    Args:
        category_name: The Level 1 category name
        
    Returns:
        List of Level 2 services for the category
    """
    try:
        # Handle URL encoding (e.g., %20 for spaces)
        import urllib.parse
        category_name = urllib.parse.unquote(category_name)
        
        if category_name not in SERVICE_CATEGORIES:
            raise HTTPException(status_code=404, detail=f"Category '{category_name}' not found")
        
        services = SERVICE_CATEGORIES[category_name]
        level3_services = LEVEL_3_SERVICES.get(category_name, {})
        
        return {
            "success": True,
            "category": category_name,
            "services": services,
            "level3Services": level3_services,
            "stats": {
                "total_services": len(services),
                "services_with_level3": len(level3_services)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching services for category {category_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/level3/{category_name}/{service_name}")
async def get_level3_services(category_name: str, service_name: str) -> Dict[str, Any]:
    """
    Get Level 3 services for a specific Level 2 service.
    
    Args:
        category_name: The Level 1 category name
        service_name: The Level 2 service name
        
    Returns:
        List of Level 3 services
    """
    try:
        # Handle URL encoding
        import urllib.parse
        category_name = urllib.parse.unquote(category_name)
        service_name = urllib.parse.unquote(service_name)
        
        if category_name not in LEVEL_3_SERVICES:
            raise HTTPException(status_code=404, detail=f"Category '{category_name}' not found in Level 3 services")
        
        category_level3 = LEVEL_3_SERVICES[category_name]
        
        if service_name not in category_level3:
            raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found in category '{category_name}'")
        
        level3_list = category_level3[service_name]
        
        return {
            "success": True,
            "category": category_name,
            "service": service_name,
            "level3Services": level3_list,
            "total": len(level3_list)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching Level 3 services: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_services(query: str) -> Dict[str, Any]:
    """
    Search for services across all levels.
    
    Args:
        query: Search term
        
    Returns:
        Search results with matches from all levels
    """
    try:
        query_lower = query.lower()
        results = {
            "level1_matches": [],
            "level2_matches": [],
            "level3_matches": []
        }
        
        # Search Level 1 categories
        for category in SERVICE_CATEGORIES.keys():
            if query_lower in category.lower():
                results["level1_matches"].append(category)
        
        # Search Level 2 services
        for category, services in SERVICE_CATEGORIES.items():
            for service in services:
                if query_lower in service.lower():
                    results["level2_matches"].append({
                        "category": category,
                        "service": service
                    })
        
        # Search Level 3 services
        for category, subcategories in LEVEL_3_SERVICES.items():
            for subcategory, level3_list in subcategories.items():
                for level3 in level3_list:
                    if query_lower in level3.lower():
                        results["level3_matches"].append({
                            "category": category,
                            "subcategory": subcategory,
                            "service": level3
                        })
        
        total_matches = (len(results["level1_matches"]) + 
                        len(results["level2_matches"]) + 
                        len(results["level3_matches"]))
        
        return {
            "success": True,
            "query": query,
            "results": results,
            "total_matches": total_matches
        }
    except Exception as e:
        logger.error(f"Error searching services: {e}")
        raise HTTPException(status_code=500, detail=str(e))