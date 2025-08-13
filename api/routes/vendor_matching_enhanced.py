"""
Enhanced vendor matching API endpoint with full service category support
Uses existing lead routing service for consistency
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import logging
import json

from database.simple_connection import db
from config import AppConfig
from api.services.lead_routing_service import LeadRoutingService
from comprehensive_service_mappings import (
    DOCKSIDE_PROS_SERVICE_CATEGORIES,
    SPECIFIC_SERVICES_BY_CATEGORY
)

router = APIRouter()
logger = logging.getLogger(__name__)
lead_routing_service = LeadRoutingService()

class EnhancedVendorMatchingRequest(BaseModel):
    zip_code: str
    service_category: str
    specific_service: Optional[str] = None
    additional_service: Optional[str] = None  # For third-level dropdown

@router.get("/service-categories")
async def get_all_service_categories():
    """Get all available service categories"""
    try:
        # Get unique categories from the mapping
        categories = list(set(DOCKSIDE_PROS_SERVICE_CATEGORIES.values()))
        categories.sort()
        
        return {
            "status": "success",
            "categories": categories,
            "count": len(categories)
        }
    except Exception as e:
        logger.error(f"Error getting service categories: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get service categories")

@router.get("/service-categories/{category}/services")
async def get_services_for_category(category: str):
    """Get specific services for a category"""
    try:
        services_data = SPECIFIC_SERVICES_BY_CATEGORY.get(category, [])
        
        # Handle both simple lists and nested dictionaries
        if isinstance(services_data, dict):
            # Category has subcategories
            return {
                "status": "success",
                "category": category,
                "has_subcategories": True,
                "services": services_data.get("Main", []),
                "subcategories": {k: v for k, v in services_data.items() if k != "Main"}
            }
        elif isinstance(services_data, list):
            # Simple list of services
            return {
                "status": "success",
                "category": category,
                "has_subcategories": False,
                "services": services_data
            }
        else:
            return {
                "status": "success",
                "category": category,
                "has_subcategories": False,
                "services": []
            }
            
    except Exception as e:
        logger.error(f"Error getting services for category {category}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get services")

@router.post("/test-vendor-matching")
async def test_vendor_matching_enhanced(request: EnhancedVendorMatchingRequest):
    """Enhanced vendor matching using existing lead routing service"""
    try:
        zip_code = request.zip_code
        service_category = request.service_category
        specific_service = request.specific_service
        additional_service = request.additional_service
        
        # Get the default account
        account = db.get_account_by_ghl_location_id(AppConfig.GHL_LOCATION_ID)
        if not account:
            return {
                "status": "error",
                "message": "No account found - no vendors available",
                "vendors": []
            }
        
        account_id = account["id"]
        
        # Use the existing lead routing service to find matching vendors
        # This uses the same logic as the actual lead routing system
        matching_vendors_raw = lead_routing_service.find_matching_vendors(
            account_id=account_id,
            service_category=service_category,
            zip_code=zip_code,
            specific_service=specific_service  # Pass specific service for exact matching
        )
        
        # Format vendors for display
        matching_vendors = []
        for vendor in matching_vendors_raw:
            vendor_info = {
                "id": vendor.get("id"),
                "company_name": vendor.get("company_name", vendor.get("name", "Unknown")),
                "email": vendor.get("email", ""),
                "phone": vendor.get("phone", ""),
                "service_categories": vendor.get("service_categories", []),
                "specific_services": vendor.get("services_offered", []),
                "coverage_type": vendor.get("coverage_type", "unknown"),
                "hourly_rate": vendor.get("hourly_rate"),
                "priority_score": vendor.get("priority_score", 0),
                "lead_count": vendor.get("lead_count", 0),
                "coverage_areas": vendor.get("coverage_match_reason", "Coverage details unavailable")
            }
            matching_vendors.append(vendor_info)
        
        # Sort vendors by priority score (if available)
        matching_vendors.sort(key=lambda x: x.get("priority_score", 0), reverse=True)
        
        # Build response message
        if matching_vendors:
            message = f"Found {len(matching_vendors)} vendor(s) for {service_category}"
            if specific_service:
                message += f" - {specific_service}"
            if additional_service:
                message += f" - {additional_service}"
            message += f" in ZIP code {zip_code}"
        else:
            message = f"No vendors found for {service_category}"
            if specific_service:
                message += f" - {specific_service}"
            if additional_service:
                message += f" - {additional_service}"
            message += f" in ZIP code {zip_code}"
        
        return {
            "status": "success",
            "message": message,
            "search_criteria": {
                "zip_code": zip_code,
                "service_category": service_category,
                "specific_service": specific_service,
                "additional_service": additional_service
            },
            "vendor_count": len(matching_vendors),
            "vendors": matching_vendors
        }
        
    except Exception as e:
        logger.error(f"Error in enhanced vendor matching: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to test vendor matching: {str(e)}")