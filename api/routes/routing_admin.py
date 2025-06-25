# api/routes/routing_admin.py

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
from database.simple_connection import db
from api.services.lead_routing_service import lead_routing_service
from config import AppConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/routing", tags=["Lead Routing Administration"])

@router.get("/configuration")
async def get_routing_configuration():
    """Get current lead routing configuration"""
    try:
        # Get the default account for this GHL location
        account = db.get_account_by_ghl_location_id(AppConfig.GHL_LOCATION_ID)
        if not account:
            # Create default account if none exists
            account_id = db.create_account(
                company_name="Digital Marine LLC",
                industry="marine",
                ghl_location_id=AppConfig.GHL_LOCATION_ID,
                ghl_private_token=AppConfig.GHL_PRIVATE_TOKEN
            )
        else:
            account_id = account["id"]
        
        # Get routing statistics
        routing_stats = lead_routing_service.get_routing_stats(account_id)
        
        return {
            "status": "success",
            "data": routing_stats,
            "account_id": account_id,
            "message": "Routing configuration retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting routing configuration: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve routing configuration")

@router.post("/configuration")
async def update_routing_configuration(performance_percentage: int):
    """Update lead routing configuration"""
    try:
        # Validate percentage
        if not 0 <= performance_percentage <= 100:
            raise HTTPException(status_code=400, detail="Performance percentage must be between 0 and 100")
        
        # Get the default account for this GHL location
        account = db.get_account_by_ghl_location_id(AppConfig.GHL_LOCATION_ID)
        if not account:
            # Create default account if none exists
            account_id = db.create_account(
                company_name="Digital Marine LLC",
                industry="marine",
                ghl_location_id=AppConfig.GHL_LOCATION_ID,
                ghl_private_token=AppConfig.GHL_PRIVATE_TOKEN
            )
        else:
            account_id = account["id"]
        
        # Update routing configuration
        success = lead_routing_service.update_routing_configuration(account_id, performance_percentage)
        
        if success:
            # Get updated stats
            routing_stats = lead_routing_service.get_routing_stats(account_id)
            
            return {
                "status": "success",
                "data": routing_stats,
                "message": f"Routing configuration updated: {performance_percentage}% performance-based, {100 - performance_percentage}% round-robin"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update routing configuration")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating routing configuration: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update routing configuration")

@router.get("/vendors")
async def get_routing_vendors():
    """Get vendors with routing information"""
    try:
        # Get the default account for this GHL location
        account = db.get_account_by_ghl_location_id(AppConfig.GHL_LOCATION_ID)
        if not account:
            return {
                "status": "success",
                "data": [],
                "message": "No account found - no vendors available"
            }
        
        account_id = account["id"]
        vendors = db.get_vendors(account_id)
        
        # Add routing-specific information
        for vendor in vendors:
            vendor['coverage_summary'] = _get_coverage_summary(vendor)
            vendor['routing_eligible'] = (
                vendor.get('status') == 'active' and 
                vendor.get('taking_new_work', False)
            )
        
        return {
            "status": "success",
            "data": vendors,
            "count": len(vendors),
            "message": "Vendors retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting routing vendors: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve vendors")

@router.post("/vendors/{vendor_id}/coverage")
async def update_vendor_coverage(vendor_id: str, coverage_data: Dict[str, Any]):
    """Update vendor coverage configuration"""
    try:
        # Validate coverage data
        coverage_type = coverage_data.get('service_coverage_type', 'zip')
        if coverage_type not in ['global', 'national', 'state', 'county', 'zip']:
            raise HTTPException(status_code=400, detail="Invalid coverage type")
        
        # Update vendor in database
        conn = db._get_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE vendors 
            SET service_coverage_type = ?, 
                service_states = ?, 
                service_counties = ?, 
                service_areas = ?,
                updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (
            coverage_type,
            str(coverage_data.get('service_states', [])),
            str(coverage_data.get('service_counties', [])),
            str(coverage_data.get('service_areas', [])),
            vendor_id
        ))
        
        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="Vendor not found")
        
        conn.commit()
        conn.close()
        
        return {
            "status": "success",
            "message": f"Vendor coverage updated to {coverage_type}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating vendor coverage: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update vendor coverage")

@router.post("/test-matching")
async def test_vendor_matching(zip_code: str, service_category: str):
    """Test vendor matching for a specific location and service"""
    try:
        # Get the default account for this GHL location
        account = db.get_account_by_ghl_location_id(AppConfig.GHL_LOCATION_ID)
        if not account:
            return {
                "status": "success",
                "data": {
                    "matching_vendors": [],
                    "selected_vendor": None,
                    "message": "No account found - no vendors available"
                }
            }
        
        account_id = account["id"]
        
        # Find matching vendors
        matching_vendors = lead_routing_service.find_matching_vendors(
            account_id=account_id,
            service_category=service_category,
            zip_code=zip_code
        )
        
        # Select vendor using routing logic
        selected_vendor = None
        if matching_vendors:
            selected_vendor = lead_routing_service.select_vendor_from_pool(
                matching_vendors, account_id
            )
        
        return {
            "status": "success",
            "data": {
                "zip_code": zip_code,
                "service_category": service_category,
                "matching_vendors": matching_vendors,
                "selected_vendor": selected_vendor,
                "match_count": len(matching_vendors)
            },
            "message": f"Found {len(matching_vendors)} matching vendors for {service_category} in {zip_code}"
        }
        
    except Exception as e:
        logger.error(f"Error testing vendor matching: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to test vendor matching")

def _get_coverage_summary(vendor: Dict[str, Any]) -> str:
    """Generate human-readable coverage summary for vendor"""
    coverage_type = vendor.get('service_coverage_type', 'zip')
    
    if coverage_type == 'global':
        return "Global coverage (worldwide)"
    elif coverage_type == 'national':
        return "National coverage (United States)"
    elif coverage_type == 'state':
        states = vendor.get('service_states', [])
        if len(states) == 1:
            return f"State coverage: {states[0]}"
        elif len(states) <= 3:
            return f"State coverage: {', '.join(states)}"
        else:
            return f"State coverage: {len(states)} states"
    elif coverage_type == 'county':
        counties = vendor.get('service_counties', [])
        if len(counties) == 1:
            return f"County coverage: {counties[0]}"
        elif len(counties) <= 3:
            return f"County coverage: {', '.join(counties)}"
        else:
            return f"County coverage: {len(counties)} counties"
    elif coverage_type == 'zip':
        zip_codes = vendor.get('service_areas', [])
        if len(zip_codes) <= 5:
            return f"ZIP code coverage: {', '.join(zip_codes)}"
        else:
            return f"ZIP code coverage: {len(zip_codes)} ZIP codes"
    else:
        return f"Coverage: {coverage_type}"
