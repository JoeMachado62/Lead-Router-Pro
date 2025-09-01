"""
Staging API Routes for Dynamic Form and Service Management
Safe testing environment - does not affect production
"""

from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

# Import staging models and services
from staging.dynamic_forms.services.category_manager import ServiceCategoryManager
from staging.dynamic_forms.services.form_manager import FormManager
from staging.dynamic_forms.models.form_models import Base

# For now, we'll use a simple SQLite database for staging
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)

# Create staging database
STAGING_DB_URL = "sqlite:///staging_dynamic_forms.db"
staging_engine = create_engine(STAGING_DB_URL, echo=True)
Base.metadata.create_all(bind=staging_engine)
StagingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=staging_engine)

# Create router
router = APIRouter(prefix="/api/staging/dynamic-forms", tags=["Staging - Dynamic Forms"])


def get_staging_db():
    """Get staging database session"""
    db = StagingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================
# SERVICE CATEGORY ENDPOINTS
# ============================================

@router.post("/categories/create")
async def create_category(
    category_data: Dict[str, Any],
    db: Session = Depends(get_staging_db)
):
    """
    Create a new Level 1 service category
    
    Example payload:
    {
        "category": {
            "name": "Waterfront Vacation Rentals",
            "display_name": "Waterfront Vacation Rentals",
            "description": "Luxury waterfront properties"
        },
        "subcategories": [
            {
                "name": "Daily",
                "display_name": "Daily Rentals",
                "level3_services": [
                    {"name": "With a Pool", "is_premium": true},
                    {"name": "With a Dock", "is_default": true}
                ]
            }
        ]
    }
    """
    try:
        manager = ServiceCategoryManager(db)
        result = manager.create_complete_hierarchy(category_data)
        
        if result.get("errors"):
            raise HTTPException(status_code=400, detail=result["errors"])
        
        return {
            "success": True,
            "message": f"Created category: {category_data['category']['name']}",
            "data": {
                "category": result["category"].to_dict() if result["category"] else None,
                "subcategories": len(result["subcategories"]),
                "level3_services": len(result["level3_services"])
            }
        }
    except Exception as e:
        logger.error(f"Error creating category: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def get_categories(
    active_only: bool = True,
    db: Session = Depends(get_staging_db)
):
    """Get all service categories with hierarchies"""
    try:
        manager = ServiceCategoryManager(db)
        categories = manager.get_all_categories(active_only=active_only)
        
        return {
            "success": True,
            "categories": categories,
            "total": len(categories)
        }
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories/{category_name}")
async def get_category_hierarchy(
    category_name: str,
    db: Session = Depends(get_staging_db)
):
    """Get complete hierarchy for a specific category"""
    try:
        manager = ServiceCategoryManager(db)
        hierarchy = manager.get_category_hierarchy(category_name)
        
        if not hierarchy:
            raise HTTPException(status_code=404, detail=f"Category '{category_name}' not found")
        
        return {
            "success": True,
            "hierarchy": hierarchy
        }
    except Exception as e:
        logger.error(f"Error getting category hierarchy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/categories/{category_name}/subcategories")
async def add_subcategory(
    category_name: str,
    subcategory_data: Dict[str, Any],
    db: Session = Depends(get_staging_db)
):
    """Add a Level 2 subcategory to an existing category"""
    try:
        manager = ServiceCategoryManager(db)
        
        subcategory = manager.add_subcategory(
            category_name=category_name,
            subcategory_name=subcategory_data["name"],
            display_name=subcategory_data["display_name"],
            has_level3_services=subcategory_data.get("has_level3_services", False),
            level3_prompt=subcategory_data.get("level3_prompt")
        )
        
        # Add Level 3 services if provided
        if subcategory_data.get("level3_services"):
            manager.add_level3_services(
                category_name=category_name,
                subcategory_name=subcategory_data["name"],
                services=subcategory_data["level3_services"]
            )
        
        return {
            "success": True,
            "message": f"Added subcategory: {subcategory_data['name']}",
            "subcategory": subcategory.to_dict()
        }
    except Exception as e:
        logger.error(f"Error adding subcategory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/categories/{category_name}/{subcategory_name}/level3-services")
async def add_level3_services(
    category_name: str,
    subcategory_name: str,
    services: List[Dict[str, Any]],
    db: Session = Depends(get_staging_db)
):
    """Add Level 3 services to a subcategory"""
    try:
        manager = ServiceCategoryManager(db)
        
        created_services = manager.add_level3_services(
            category_name=category_name,
            subcategory_name=subcategory_name,
            services=services
        )
        
        return {
            "success": True,
            "message": f"Added {len(created_services)} Level 3 services",
            "services": [svc.to_dict() for svc in created_services]
        }
    except Exception as e:
        logger.error(f"Error adding Level 3 services: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vendor-form-data")
async def get_vendor_form_data(
    category_name: Optional[str] = None,
    db: Session = Depends(get_staging_db)
):
    """Get data needed to generate vendor application forms"""
    try:
        manager = ServiceCategoryManager(db)
        form_data = manager.get_vendor_form_data(category_name)
        
        return {
            "success": True,
            "form_data": form_data
        }
    except Exception as e:
        logger.error(f"Error getting vendor form data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# FORM CONFIGURATION ENDPOINTS
# ============================================

@router.post("/forms/register")
async def register_form(
    form_config: Dict[str, Any],
    db: Session = Depends(get_staging_db)
):
    """
    Register a new form configuration
    
    Example payload:
    {
        "form_identifier": "luxury-rental-inquiry",
        "form_name": "Luxury Rental Inquiry",
        "form_type": "client_lead",
        "category_name": "Waterfront Vacation Rentals",
        "required_fields": ["firstName", "lastName", "email"],
        "priority": "normal",
        "auto_route_to_vendor": true
    }
    """
    try:
        manager = FormManager(db)
        form = manager.register_form(form_config)
        
        return {
            "success": True,
            "message": f"Registered form: {form_config['form_identifier']}",
            "form": form.to_dict()
        }
    except Exception as e:
        logger.error(f"Error registering form: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/forms")
async def get_forms(
    active_only: bool = True,
    form_type: Optional[str] = None,
    db: Session = Depends(get_staging_db)
):
    """Get all registered forms"""
    try:
        manager = FormManager(db)
        forms = manager.get_all_forms(active_only=active_only, form_type=form_type)
        
        return {
            "success": True,
            "forms": forms,
            "total": len(forms)
        }
    except Exception as e:
        logger.error(f"Error getting forms: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/forms/{form_identifier}/configuration")
async def get_form_configuration(
    form_identifier: str,
    db: Session = Depends(get_staging_db)
):
    """Get configuration for a specific form (used by webhook handler)"""
    try:
        manager = FormManager(db)
        config = manager.get_form_configuration(form_identifier)
        
        if not config:
            # Form not registered - return None to trigger auto-discovery
            return {
                "success": False,
                "registered": False,
                "form_identifier": form_identifier
            }
        
        return {
            "success": True,
            "registered": True,
            "configuration": config
        }
    except Exception as e:
        logger.error(f"Error getting form configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/forms/{form_identifier}/test")
async def test_form(
    form_identifier: str,
    test_payload: Dict[str, Any],
    db: Session = Depends(get_staging_db)
):
    """Test a form configuration with sample data"""
    try:
        manager = FormManager(db)
        results = manager.test_form(form_identifier, test_payload)
        
        return {
            "success": results["success"],
            "test_results": results
        }
    except Exception as e:
        logger.error(f"Error testing form: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/forms/{form_identifier}")
async def update_form(
    form_identifier: str,
    updates: Dict[str, Any],
    db: Session = Depends(get_staging_db)
):
    """Update an existing form configuration"""
    try:
        manager = FormManager(db)
        form = manager.update_form(form_identifier, updates)
        
        return {
            "success": True,
            "message": f"Updated form: {form_identifier}",
            "form": form.to_dict()
        }
    except Exception as e:
        logger.error(f"Error updating form: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/forms/{form_identifier}")
async def delete_form(
    form_identifier: str,
    db: Session = Depends(get_staging_db)
):
    """Deactivate a form configuration"""
    try:
        manager = FormManager(db)
        success = manager.delete_form(form_identifier)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Form '{form_identifier}' not found")
        
        return {
            "success": True,
            "message": f"Deactivated form: {form_identifier}"
        }
    except Exception as e:
        logger.error(f"Error deleting form: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# AUTO-DISCOVERY ENDPOINTS
# ============================================

@router.get("/forms/unregistered")
async def get_unregistered_forms(
    status: str = "pending",
    db: Session = Depends(get_staging_db)
):
    """Get unregistered form submissions for review"""
    try:
        manager = FormManager(db)
        forms = manager.get_unregistered_forms(status=status)
        
        return {
            "success": True,
            "unregistered_forms": forms,
            "total": len(forms)
        }
    except Exception as e:
        logger.error(f"Error getting unregistered forms: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/forms/unregistered/{form_id}/auto-register")
async def auto_register_form(
    form_id: str,
    config_overrides: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_staging_db)
):
    """Auto-register an unregistered form"""
    try:
        manager = FormManager(db)
        form = manager.auto_register_form(form_id, config_overrides or {})
        
        return {
            "success": True,
            "message": f"Auto-registered form: {form.form_identifier}",
            "form": form.to_dict()
        }
    except Exception as e:
        logger.error(f"Error auto-registering form: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# WEBHOOK SIMULATION ENDPOINT
# ============================================

@router.post("/webhook/simulate/{form_identifier}")
async def simulate_webhook(
    form_identifier: str,
    payload: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_staging_db)
):
    """
    Simulate a webhook submission to test form processing
    This mimics what would happen when a real form is submitted
    """
    try:
        manager = FormManager(db)
        
        # Try to get form configuration
        config = manager.get_form_configuration(form_identifier)
        
        if not config:
            # Handle unregistered form
            logger.info(f"Unregistered form detected: {form_identifier}")
            unregistered = manager.handle_unregistered_form(form_identifier, payload)
            
            return {
                "success": False,
                "message": "Form not registered",
                "action": "auto_discovery",
                "unregistered_id": unregistered.id,
                "suggested_type": unregistered.suggested_form_type,
                "suggested_category": unregistered.suggested_category,
                "detected_fields": unregistered.detected_fields
            }
        
        # Process as registered form
        validation_errors = []
        
        # Validate required fields
        for field in config["required_fields"]:
            if field not in payload or not payload[field]:
                validation_errors.append(f"Missing required field: {field}")
        
        if validation_errors:
            return {
                "success": False,
                "message": "Validation failed",
                "errors": validation_errors
            }
        
        # Simulate successful processing
        return {
            "success": True,
            "message": "Form processed successfully",
            "form_type": config["form_type"],
            "category": config["service_category"],
            "priority": config["priority"],
            "auto_route": config["auto_route_to_vendor"],
            "mapped_fields": len(config.get("field_mappings", {})),
            "tags": config.get("default_tags", [])
        }
        
    except Exception as e:
        logger.error(f"Error simulating webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# IMPORT/EXPORT ENDPOINTS
# ============================================

@router.post("/categories/import")
async def import_categories(
    import_data: Dict[str, Any],
    db: Session = Depends(get_staging_db)
):
    """Import service categories from JSON"""
    try:
        manager = ServiceCategoryManager(db)
        
        import json
        json_str = json.dumps(import_data)
        results = manager.import_from_json(json_str)
        
        return {
            "success": len(results["errors"]) == 0,
            "imported": results["imported"],
            "errors": results["errors"]
        }
    except Exception as e:
        logger.error(f"Error importing categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories/export")
async def export_categories(
    category_name: Optional[str] = None,
    db: Session = Depends(get_staging_db)
):
    """Export service categories to JSON"""
    try:
        manager = ServiceCategoryManager(db)
        
        export_json = manager.export_to_json(category_name)
        import json
        export_data = json.loads(export_json)
        
        return {
            "success": True,
            "export_data": export_data
        }
    except Exception as e:
        logger.error(f"Error exporting categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))