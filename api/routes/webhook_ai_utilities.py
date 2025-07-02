# api/routes/webhook_ai_utilities.py
# AI utilities, examples, and testing functions for webhook processing
# THIS IS NOT A REPLACEMENT FOR YOUR EXISTING webhook_routes.py
# These are utilities and examples you can import and use

import asyncio
import logging
from typing import Dict, Any, Optional
from fastapi import BackgroundTasks, HTTPException, Request
from datetime import datetime

# Import V2 AI services
from api.services.ghl_api_enhanced_v2 import get_enhanced_ghl_client_v2
from api.services.ai_enhanced_field_mapper_v2 import ai_enhanced_field_mapper_v2
from api.services.ai_error_recovery_v2 import ai_error_recovery_v2
from api.services.field_reference_service import field_reference_service
from config import AppConfig

logger = logging.getLogger(__name__)

class WebhookAIUtilities:
    """
    Utility class for AI-enhanced webhook processing
    Use these methods in your existing webhook_routes.py
    """
    
    @staticmethod
    async def enhance_contact_creation(contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Utility to enhance contact creation with AI recovery
        
        Usage in your webhook_routes.py:
        ```python
        from api.routes.webhook_ai_utilities import WebhookAIUtilities
        
        # Replace your existing contact creation
        result = await WebhookAIUtilities.enhance_contact_creation(contact_data)
        ```
        """
        enhanced_client = get_enhanced_ghl_client_v2()
        
        try:
            result = await enhanced_client.create_contact_with_ai_recovery(contact_data)
            
            return {
                "success": not result.get("error", False),
                "contact_id": result.get("contact", {}).get("id") or result.get("id"),
                "ai_recovery_used": result.get("ai_recovery_attempted", False),
                "ai_recovery_success": result.get("ai_recovery_success", False),
                "result": result
            }
            
        except Exception as e:
            logger.error(f"❌ Enhanced contact creation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "result": None
            }
    
    @staticmethod
    async def analyze_and_map_form_fields(form_data: Dict[str, Any], 
                                         form_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Utility to analyze unknown form fields and get mapping suggestions
        
        Usage in your webhook_routes.py:
        ```python
        # Before processing form data
        field_analysis = await WebhookAIUtilities.analyze_and_map_form_fields(
            form_data=form_data,
            form_context={"form_type": "client_lead", "form_identifier": form_identifier}
        )
        
        # Use the recommendations
        ai_recommendations = field_analysis["mapping_recommendations"]
        ```
        """
        try:
            analysis = await ai_enhanced_field_mapper_v2.analyze_form_fields_batch_v2(
                form_data=form_data,
                context=form_context
            )
            
            return {
                "success": True,
                "total_fields": analysis["total_fields"],
                "unknown_fields": len(analysis["unknown_fields"]),
                "mapping_recommendations": analysis["mapping_recommendations"],
                "suggested_mappings": analysis["suggested_new_mappings"],
                "cache_efficiency": analysis["v2_metrics"]["cache_efficiency"],
                "analysis": analysis
            }
            
        except Exception as e:
            logger.error(f"❌ Field analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "mapping_recommendations": {},
                "analysis": None
            }
    
    @staticmethod
    async def auto_learn_field_mappings(form_data: Dict[str, Any], 
                                       form_context: Dict[str, Any] = None,
                                       enable_auto_save: bool = True) -> Dict[str, Any]:
        """
        Utility to enable auto-learning of field mappings
        
        Usage in your webhook_routes.py:
        ```python
        # Enable auto-learning from form submissions
        learning_result = await WebhookAIUtilities.auto_learn_field_mappings(
            form_data=form_data,
            form_context={"form_identifier": form_identifier},
            enable_auto_save=True
        )
        
        logger.info(f"Auto-learned {learning_result['auto_saved_count']} new mappings")
        ```
        """
        try:
            learning_result = await ai_enhanced_field_mapper_v2.auto_learn_from_form_submission_v2(
                form_data=form_data,
                context=form_context,
                auto_save=enable_auto_save
            )
            
            return {
                "success": True,
                "auto_saved_count": len(learning_result["auto_saved_mappings"]),
                "auto_saved_mappings": learning_result["auto_saved_mappings"],
                "learning_summary": learning_result["learning_summary"],
                "full_result": learning_result
            }
            
        except Exception as e:
            logger.error(f"❌ Auto-learning failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "auto_saved_count": 0,
                "auto_saved_mappings": {}
            }
    
    @staticmethod
    def build_enhanced_ghl_payload(form_data: Dict[str, Any], 
                                  ai_recommendations: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Utility to build GHL payload with AI field mapping recommendations
        
        Usage in your webhook_routes.py:
        ```python
        # Get AI recommendations first
        field_analysis = await WebhookAIUtilities.analyze_and_map_form_fields(form_data)
        
        # Build enhanced payload
        ghl_payload = WebhookAIUtilities.build_enhanced_ghl_payload(
            form_data=form_data,
            ai_recommendations=field_analysis["mapping_recommendations"]
        )
        ```
        """
        # Start with standard fields
        payload = {
            "firstName": form_data.get("firstName") or form_data.get("first_name") or "",
            "lastName": form_data.get("lastName") or form_data.get("last_name") or "",
            "email": form_data.get("email") or "",
            "phone": form_data.get("phone") or "",
            "locationId": AppConfig.GHL_LOCATION_ID
        }
        
        # Apply AI recommendations for unknown fields
        ai_recommendations = ai_recommendations or {}
        
        # Build custom fields array
        custom_fields = []
        processed_fields = {"firstName", "lastName", "email", "phone", "locationId"}
        
        for field_name, field_value in form_data.items():
            if field_name in processed_fields:
                continue
            
            # Check if AI recommended a mapping
            if field_name in ai_recommendations:
                ghl_field_key = ai_recommendations[field_name]
                field_details = field_reference_service.get_field_definition(ghl_field_key)
                
                if field_details and field_details.get("id"):
                    custom_fields.append({
                        "id": field_details["id"],
                        "fieldKey": field_details["fieldKey"],
                        "value": str(field_value)
                    })
                    logger.info(f"🤖 Applied AI mapping: {field_name} → {ghl_field_key}")
            else:
                # Use existing field mapper as fallback
                ghl_field_key = ai_enhanced_field_mapper_v2.map_to_ghl_field(field_name)
                field_details = ai_enhanced_field_mapper_v2.get_ghl_field_details(ghl_field_key)
                
                if field_details and field_details.get("id"):
                    custom_fields.append({
                        "id": field_details["id"],
                        "fieldKey": field_details["fieldKey"],
                        "value": str(field_value)
                    })
        
        payload["customFields"] = custom_fields
        
        logger.info(f"🔧 Built enhanced GHL payload with {len(custom_fields)} custom fields")
        return payload

class WebhookAIMonitoring:
    """
    Monitoring and health check utilities for AI features
    """
    
    @staticmethod
    def get_ai_health_status() -> Dict[str, Any]:
        """
        Get comprehensive AI health status
        
        Usage:
        ```python
        @router.get("/ai-health")
        async def ai_health_check():
            return WebhookAIMonitoring.get_ai_health_status()
        ```
        """
        # Get V2 service stats
        error_recovery_stats = ai_error_recovery_v2.get_enhanced_stats()
        field_mapper_stats = ai_enhanced_field_mapper_v2.get_v2_enhanced_stats()
        field_service_stats = field_reference_service.get_field_statistics()
        
        # Calculate overall health
        components_healthy = [
            error_recovery_stats["ai_enabled"],
            field_mapper_stats["ai_field_analysis_enabled"],
            field_service_stats["total_fields"] > 0
        ]
        
        overall_status = "healthy" if all(components_healthy) else "degraded"
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": overall_status,
            "version": "v2",
            "components": {
                "ai_error_recovery": {
                    "status": "healthy" if error_recovery_stats["ai_enabled"] else "disabled",
                    "cache_hit_rate": error_recovery_stats["cache_stats"]["hit_rate_percent"],
                    "total_analyses": error_recovery_stats["metrics"]["total_analyses"],
                    "successful_recoveries": error_recovery_stats["metrics"]["successful_recoveries"]
                },
                "ai_field_mapper": {
                    "status": "healthy" if field_mapper_stats["ai_field_analysis_enabled"] else "disabled",
                    "total_mappings": field_mapper_stats["total_mappings"],
                    "auto_saved_mappings": field_mapper_stats["v2_metrics"]["auto_saved_mappings"],
                    "cache_hit_rate": field_mapper_stats["v2_metrics"]["cache_hit_rate"]
                },
                "field_reference_service": {
                    "status": "healthy" if field_service_stats["total_fields"] > 0 else "degraded",
                    "total_fields": field_service_stats["total_fields"],
                    "data_types": field_service_stats["data_types"]
                }
            },
            "performance_summary": {
                "token_efficiency": error_recovery_stats["efficiency"]["avg_tokens_per_call"] < 1000,
                "cache_performance": error_recovery_stats["cache_stats"]["hit_rate_percent"] > 20,
                "recovery_success_rate": error_recovery_stats["efficiency"]["successful_recovery_rate"]
            }
        }
    
    @staticmethod
    def get_ai_metrics_summary() -> Dict[str, Any]:
        """
        Get AI metrics summary for dashboard monitoring
        """
        error_recovery_stats = ai_error_recovery_v2.get_enhanced_stats()
        field_mapper_stats = ai_enhanced_field_mapper_v2.get_v2_enhanced_stats()
        
        return {
            "error_recovery": {
                "total_analyses": error_recovery_stats["metrics"]["total_analyses"],
                "cache_hits": error_recovery_stats["cache_stats"]["hits"],
                "successful_recoveries": error_recovery_stats["metrics"]["successful_recoveries"],
                "token_usage": error_recovery_stats["metrics"]["token_usage"]
            },
            "field_mapping": {
                "total_analyses": field_mapper_stats["v2_metrics"]["total_analyses"],
                "auto_saved_mappings": field_mapper_stats["v2_metrics"]["auto_saved_mappings"],
                "cache_hits": field_mapper_stats["v2_metrics"]["cache_hits"]
            },
            "efficiency": {
                "avg_tokens_per_analysis": error_recovery_stats["efficiency"]["avg_tokens_per_call"],
                "overall_cache_hit_rate": (
                    error_recovery_stats["cache_stats"]["hits"] + field_mapper_stats["v2_metrics"]["cache_hits"]
                ) / max(
                    error_recovery_stats["metrics"]["total_analyses"] + field_mapper_stats["v2_metrics"]["total_analyses"], 1
                ) * 100
            }
        }

class WebhookAITesting:
    """
    Testing utilities for AI features
    """
    
    @staticmethod
    async def test_ai_error_recovery() -> Dict[str, Any]:
        """Test AI error recovery with mock data"""
        
        # Mock error scenario
        mock_payload = {
            "firstName": "Test",
            "lastName": "User",
            "email": "invalid-email-format",  # Should trigger validation error
            "phone": "123",  # Invalid phone format
            "locationId": AppConfig.GHL_LOCATION_ID
        }
        
        enhanced_client = get_enhanced_ghl_client_v2()
        
        try:
            result = await enhanced_client.create_contact_with_ai_recovery(mock_payload)
            
            return {
                "test": "ai_error_recovery",
                "success": not result.get("error", False),
                "ai_recovery_attempted": result.get("ai_recovery_attempted", False),
                "ai_recovery_success": result.get("ai_recovery_success", False),
                "final_state": result.get("final_state"),
                "analysis_count": len(result.get("ai_v2_analysis", [])),
                "result_summary": {
                    "contact_created": bool(result.get("contact", {}).get("id")),
                    "error_present": result.get("error", False)
                }
            }
            
        except Exception as e:
            return {
                "test": "ai_error_recovery",
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    async def test_ai_field_analysis() -> Dict[str, Any]:
        """Test AI field analysis with mock data"""
        
        mock_form_data = {
            "boat_type": "Sailboat",
            "unknown_marine_field": "Catamaran",
            "vessel_make": "Catalina",
            "mystery_field": "Some unknown value",
            "email": "test@example.com"  # Known field
        }
        
        try:
            analysis = await ai_enhanced_field_mapper_v2.analyze_form_fields_batch_v2(
                form_data=mock_form_data,
                context={"form_type": "client_lead", "test": True}
            )
            
            return {
                "test": "ai_field_analysis",
                "success": True,
                "total_fields": analysis["total_fields"],
                "unknown_fields_found": len(analysis["unknown_fields"]),
                "ai_recommendations": analysis["mapping_recommendations"],
                "cache_efficiency": analysis["v2_metrics"]["cache_efficiency"],
                "high_confidence_mappings": analysis["v2_metrics"]["high_confidence_mappings"],
                "unknown_fields": analysis["unknown_fields"]
            }
            
        except Exception as e:
            return {
                "test": "ai_field_analysis",
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    async def test_auto_learning() -> Dict[str, Any]:
        """Test auto-learning functionality"""
        
        mock_form_data = {
            "client_boat_name": "Sea Breeze",
            "preferred_service_date": "2025-07-15",
            "marina_location": "Miami Marina"
        }
        
        try:
            learning_result = await ai_enhanced_field_mapper_v2.auto_learn_from_form_submission_v2(
                form_data=mock_form_data,
                context={"form_type": "client_lead", "test": True},
                auto_save=False  # Don't actually save during testing
            )
            
            return {
                "test": "auto_learning",
                "success": True,
                "total_analyzed": learning_result["learning_summary"]["total_analyzed"],
                "high_confidence_mappings": learning_result["learning_summary"]["high_confidence"],
                "would_auto_save": len(learning_result["auto_saved_mappings"]),
                "cache_efficiency": learning_result["learning_summary"]["cache_efficiency"]
            }
            
        except Exception as e:
            return {
                "test": "auto_learning",
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    async def run_comprehensive_ai_tests() -> Dict[str, Any]:
        """Run all AI tests and return comprehensive results"""
        
        tests = []
        
        # Test 1: AI Error Recovery
        try:
            recovery_test = await WebhookAITesting.test_ai_error_recovery()
            tests.append(recovery_test)
        except Exception as e:
            tests.append({"test": "ai_error_recovery", "success": False, "error": str(e)})
        
        # Test 2: AI Field Analysis
        try:
            field_test = await WebhookAITesting.test_ai_field_analysis()
            tests.append(field_test)
        except Exception as e:
            tests.append({"test": "ai_field_analysis", "success": False, "error": str(e)})
        
        # Test 3: Auto-Learning
        try:
            learning_test = await WebhookAITesting.test_auto_learning()
            tests.append(learning_test)
        except Exception as e:
            tests.append({"test": "auto_learning", "success": False, "error": str(e)})
        
        # Calculate overall results
        successful_tests = [t for t in tests if t.get("success", False)]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "ai_comprehensive_test": True,
            "version": "v2",
            "tests": tests,
            "summary": {
                "total_tests": len(tests),
                "successful_tests": len(successful_tests),
                "success_rate": len(successful_tests) / len(tests) * 100 if tests else 0
            },
            "overall_status": "healthy" if len(successful_tests) == len(tests) else "degraded"
        }

# Example webhook enhancement function
async def example_enhanced_webhook_processing(
    form_identifier: str,
    form_data: Dict[str, Any],
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Example of how to enhance your existing webhook processing
    
    YOU DON'T NEED TO REPLACE YOUR WEBHOOK_ROUTES.PY
    Instead, import the utilities and use them in your existing functions
    """
    
    logger.info(f"🚀 Example enhanced processing for form '{form_identifier}'")
    
    processing_results = {
        "form_identifier": form_identifier,
        "success": False,
        "ai_enhanced": True,
        "start_time": datetime.now().isoformat()
    }
    
    try:
        # Step 1: Analyze form fields with AI
        field_analysis = await WebhookAIUtilities.analyze_and_map_form_fields(
            form_data=form_data,
            form_context={"form_identifier": form_identifier, "form_type": "client_lead"}
        )
        
        processing_results["field_analysis"] = {
            "unknown_fields": field_analysis["unknown_fields"],
            "ai_recommendations": len(field_analysis["mapping_recommendations"]),
            "cache_efficiency": field_analysis["cache_efficiency"]
        }
        
        # Step 2: Enable auto-learning
        learning_result = await WebhookAIUtilities.auto_learn_field_mappings(
            form_data=form_data,
            form_context={"form_identifier": form_identifier},
            enable_auto_save=True
        )
        
        processing_results["auto_learning"] = {
            "new_mappings_learned": learning_result["auto_saved_count"],
            "mappings": learning_result["auto_saved_mappings"]
        }
        
        # Step 3: Build enhanced GHL payload
        ghl_payload = WebhookAIUtilities.build_enhanced_ghl_payload(
            form_data=form_data,
            ai_recommendations=field_analysis["mapping_recommendations"]
        )
        
        # Step 4: Create contact with AI recovery
        contact_result = await WebhookAIUtilities.enhance_contact_creation(ghl_payload)
        
        processing_results["contact_creation"] = {
            "success": contact_result["success"],
            "contact_id": contact_result.get("contact_id"),
            "ai_recovery_used": contact_result["ai_recovery_used"],
            "ai_recovery_success": contact_result["ai_recovery_success"]
        }
        
        processing_results["success"] = contact_result["success"]
        processing_results["end_time"] = datetime.now().isoformat()
        
        return processing_results
        
    except Exception as e:
        logger.exception(f"💥 Example enhanced processing failed: {e}")
        processing_results["error"] = str(e)
        processing_results["end_time"] = datetime.now().isoformat()
        return processing_results

# Export key utilities for easy importing
__all__ = [
    "WebhookAIUtilities",
    "WebhookAIMonitoring", 
    "WebhookAITesting",
    "example_enhanced_webhook_processing"
]