# api/routes/field_mapping_routes.py

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from api.services.field_mapper import field_mapper

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/field-mappings", tags=["Field Mapping Management"])

# Pydantic models for request validation
class FieldMappingModel(BaseModel):
    source_field: str
    target_field: str
    industry: Optional[str] = None

class BulkMappingsModel(BaseModel):
    mappings: Dict[str, Any]

class TestPayloadModel(BaseModel):
    payload: Dict[str, Any]
    industry: str = "marine"

@router.get("/")
async def get_all_field_mappings():
    """Get all current field mappings"""
    try:
        mappings = field_mapper.get_all_mappings()
        stats = field_mapper.get_mapping_stats()
        
        return {
            "status": "success",
            "mappings": mappings,
            "statistics": stats,
            "message": f"Retrieved {stats['total_mappings']} field mappings"
        }
    except Exception as e:
        logger.error(f"Error retrieving field mappings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve field mappings: {str(e)}")

@router.get("/stats")
async def get_mapping_statistics():
    """Get field mapping statistics"""
    try:
        stats = field_mapper.get_mapping_stats()
        return {
            "status": "success",
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Error retrieving mapping statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve statistics: {str(e)}")

@router.get("/industry/{industry}")
async def get_industry_mappings(industry: str):
    """Get field mappings for a specific industry"""
    try:
        all_mappings = field_mapper.get_all_mappings()
        industry_mappings = all_mappings.get("industry_specific", {}).get(industry, {})
        default_mappings = all_mappings.get("default_mappings", {})
        
        return {
            "status": "success",
            "industry": industry,
            "industry_mappings": industry_mappings,
            "default_mappings": default_mappings,
            "total_mappings": len(industry_mappings) + len(default_mappings)
        }
    except Exception as e:
        logger.error(f"Error retrieving mappings for industry {industry}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve industry mappings: {str(e)}")

@router.post("/")
async def add_field_mapping(mapping: FieldMappingModel):
    """Add a new field mapping"""
    try:
        field_mapper.add_mapping(
            source_field=mapping.source_field,
            target_field=mapping.target_field,
            industry=mapping.industry
        )
        
        logger.info(f"Added field mapping: {mapping.source_field} -> {mapping.target_field} (industry: {mapping.industry})")
        
        return {
            "status": "success",
            "message": f"Added mapping: {mapping.source_field} -> {mapping.target_field}",
            "mapping": {
                "source_field": mapping.source_field,
                "target_field": mapping.target_field,
                "industry": mapping.industry
            }
        }
    except Exception as e:
        logger.error(f"Error adding field mapping: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add field mapping: {str(e)}")

@router.put("/bulk")
async def update_bulk_mappings(bulk_mappings: BulkMappingsModel):
    """Update all field mappings with new data"""
    try:
        field_mapper.update_mappings(bulk_mappings.mappings)
        stats = field_mapper.get_mapping_stats()
        
        logger.info(f"Updated bulk field mappings: {stats['total_mappings']} total mappings")
        
        return {
            "status": "success",
            "message": f"Updated {stats['total_mappings']} field mappings",
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Error updating bulk mappings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update bulk mappings: {str(e)}")

@router.delete("/{source_field}")
async def remove_field_mapping(source_field: str, industry: Optional[str] = None):
    """Remove a field mapping"""
    try:
        field_mapper.remove_mapping(source_field=source_field, industry=industry)
        
        logger.info(f"Removed field mapping: {source_field} (industry: {industry})")
        
        return {
            "status": "success",
            "message": f"Removed mapping for field: {source_field}",
            "removed_field": source_field,
            "industry": industry
        }
    except Exception as e:
        logger.error(f"Error removing field mapping: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to remove field mapping: {str(e)}")

@router.post("/test")
async def test_field_mapping(test_data: TestPayloadModel):
    """Test field mapping on a sample payload"""
    try:
        original_payload = test_data.payload
        mapped_payload = field_mapper.map_payload(original_payload, test_data.industry)
        
        # Create mapping details for response
        mapping_details = []
        for original_field, value in original_payload.items():
            mapped_field = field_mapper.get_mapping(original_field, test_data.industry)
            mapping_details.append({
                "original_field": original_field,
                "mapped_field": mapped_field,
                "value": value,
                "was_mapped": original_field != mapped_field
            })
        
        return {
            "status": "success",
            "industry": test_data.industry,
            "original_payload": original_payload,
            "mapped_payload": mapped_payload,
            "mapping_details": mapping_details,
            "total_fields": len(original_payload),
            "mapped_fields": len([d for d in mapping_details if d["was_mapped"]])
        }
    except Exception as e:
        logger.error(f"Error testing field mapping: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to test field mapping: {str(e)}")

@router.get("/reverse/{ghl_field}")
async def get_reverse_mapping(ghl_field: str, industry: str = "marine"):
    """Get the form field name that maps to a GHL field"""
    try:
        form_field = field_mapper.get_reverse_mapping(ghl_field, industry)
        
        return {
            "status": "success",
            "ghl_field": ghl_field,
            "form_field": form_field,
            "industry": industry,
            "has_reverse_mapping": form_field != ghl_field
        }
    except Exception as e:
        logger.error(f"Error getting reverse mapping: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get reverse mapping: {str(e)}")

@router.post("/import")
async def import_mappings_from_csv(request: Request):
    """Import field mappings from CSV data (for migration from existing systems)"""
    try:
        # This endpoint could be extended to parse CSV files with field mappings
        # For now, we'll return a placeholder response
        return {
            "status": "success",
            "message": "CSV import functionality placeholder - can be extended for specific use cases"
        }
    except Exception as e:
        logger.error(f"Error importing mappings from CSV: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to import mappings: {str(e)}")

@router.get("/export")
async def export_mappings():
    """Export current field mappings for backup or sharing"""
    try:
        mappings = field_mapper.get_all_mappings()
        stats = field_mapper.get_mapping_stats()
        
        export_data = {
            "export_info": {
                "exported_at": "2025-06-13T01:00:00Z",
                "total_mappings": stats["total_mappings"],
                "version": mappings.get("metadata", {}).get("version", "1.0")
            },
            "field_mappings": mappings
        }
        
        return {
            "status": "success",
            "export_data": export_data,
            "message": f"Exported {stats['total_mappings']} field mappings"
        }
    except Exception as e:
        logger.error(f"Error exporting mappings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export mappings: {str(e)}")

@router.post("/validate")
async def validate_mappings():
    """Validate current field mappings for consistency and conflicts"""
    try:
        mappings = field_mapper.get_all_mappings()
        validation_results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": []
        }
        
        # Check for circular mappings
        default_mappings = mappings.get("default_mappings", {})
        for source, target in default_mappings.items():
            if target in default_mappings and default_mappings[target] == source:
                validation_results["errors"].append(f"Circular mapping detected: {source} <-> {target}")
                validation_results["is_valid"] = False
        
        # Check for conflicts between industries
        industry_mappings = mappings.get("industry_specific", {})
        for industry1, mappings1 in industry_mappings.items():
            for industry2, mappings2 in industry_mappings.items():
                if industry1 != industry2:
                    for field, target1 in mappings1.items():
                        if field in mappings2 and mappings2[field] != target1:
                            validation_results["warnings"].append(
                                f"Conflicting mapping for '{field}': {industry1}={target1}, {industry2}={mappings2[field]}"
                            )
        
        return {
            "status": "success",
            "validation": validation_results
        }
    except Exception as e:
        logger.error(f"Error validating mappings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to validate mappings: {str(e)}")
