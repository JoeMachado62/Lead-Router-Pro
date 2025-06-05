from fastapi import APIRouter, HTTPException # type: ignore
from typing import List, Dict, Any, Optional
import logging
from database.simple_connection import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/simple-admin", tags=["Simple Admin"])

@router.get("/stats")
async def get_system_stats():
    """Get basic system statistics"""
    try:
        stats = db.get_stats()
        return {
            "status": "success",
            "data": stats,
            "message": "System statistics retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system statistics")

@router.get("/accounts")
async def get_accounts():
    """Get all accounts"""
    try:
        accounts = db.get_accounts()
        return {
            "status": "success",
            "data": accounts,
            "count": len(accounts),
            "message": "Accounts retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting accounts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve accounts")

@router.post("/accounts")
async def create_account(company_name: str, industry: str = "marine"):
    """Create a new account"""
    try:
        if not company_name or len(company_name.strip()) < 2:
            raise HTTPException(status_code=400, detail="Company name must be at least 2 characters")
        
        account_id = db.create_account(company_name.strip(), industry)
        
        return {
            "status": "success",
            "data": {"account_id": account_id},
            "message": f"Account '{company_name}' created successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating account: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create account")

@router.get("/vendors")
async def get_vendors(account_id: Optional[str] = None):
    """Get vendors, optionally filtered by account"""
    try:
        vendors = db.get_vendors(account_id)
        return {
            "status": "success",
            "data": vendors,
            "count": len(vendors),
            "message": "Vendors retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting vendors: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve vendors")

@router.post("/vendors")
async def create_vendor(account_id: str, name: str, company_name: str = "", 
                       email: str = "", phone: str = ""):
    """Create a new vendor"""
    try:
        if not account_id or not name:
            raise HTTPException(status_code=400, detail="Account ID and vendor name are required")
        
        if len(name.strip()) < 2:
            raise HTTPException(status_code=400, detail="Vendor name must be at least 2 characters")
        
        vendor_id = db.create_vendor(
            account_id.strip(), 
            name.strip(), 
            company_name.strip(), 
            email.strip(), 
            phone.strip()
        )
        
        return {
            "status": "success",
            "data": {"vendor_id": vendor_id},
            "message": f"Vendor '{name}' created successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating vendor: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create vendor")

@router.get("/leads")
async def get_leads(account_id: Optional[str] = None):
    """Get leads, optionally filtered by account"""
    try:
        leads = db.get_leads(account_id)
        return {
            "status": "success",
            "data": leads,
            "count": len(leads),
            "message": "Leads retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting leads: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve leads")

@router.post("/leads")
async def create_lead(service_category: str, customer_name: str = "", 
                     customer_email: str = "", account_id: Optional[str] = None, 
                     vendor_id: Optional[str] = None):
    """Create a new lead"""
    try:
        if not service_category:
            raise HTTPException(status_code=400, detail="Service category is required")
        
        if len(service_category.strip()) < 2:
            raise HTTPException(status_code=400, detail="Service category must be at least 2 characters")
        
        lead_id = db.create_lead(
            service_category.strip(), 
            customer_name.strip(), 
            customer_email.strip(),
            account_id=account_id,
            vendor_id=vendor_id
        )
        
        return {
            "status": "success",
            "data": {"lead_id": lead_id},
            "message": f"Lead for '{service_category}' created successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating lead: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create lead")
