"""
Webhook Integration Patch for Service Dictionary Mapper
========================================================
This module integrates the new service_dictionary_mapper with the existing webhook_routes.py
to properly handle service categorization and field mapping.

Author: Lead Router Pro Team
Created: January 2025
"""

import logging
import json
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

# Import the new service dictionary mapper
from api.services.service_dictionary_mapper import service_dictionary_mapper

# Import existing modules
from api.services.field_mapper import field_mapper
from config import AppConfig

logger = logging.getLogger(__name__)


class EnhancedWebhookProcessor:
    """
    Enhanced webhook processor that integrates the service dictionary mapper
    with the existing webhook processing pipeline.
    """
    
    def __init__(self):
        self.service_mapper = service_dictionary_mapper
        self.field_mapper = field_mapper
        logger.info("✅ Enhanced Webhook Processor initialized with Service Dictionary Mapper")
    
    def process_form_with_service_mapping(self, 
                                         form_data: Dict[str, Any], 
                                         form_identifier: str) -> Dict[str, Any]:
        """
        Process incoming form data with intelligent service mapping.
        
        This method:
        1. Uses service_dictionary_mapper to identify service categories
        2. Consolidates redundant custom fields
        3. Maintains compatibility with existing field_mapper
        4. Returns enhanced payload ready for GHL
        
        Args:
            form_data: Raw form data from webhook
            form_identifier: Form identifier/source
            
        Returns:
            Enhanced payload with proper service categorization
        """
        
        logger.info(f"🔄 Processing form '{form_identifier}' with Service Dictionary Mapper")
        
        # Step 1: Apply service dictionary mapping
        service_mapping_result = self.service_mapper.map_payload_to_service(form_data)
        
        # Extract results
        standardized_fields = service_mapping_result["standardized_fields"]
        service_classification = service_mapping_result["service_classification"]
        confidence_scores = service_mapping_result["confidence_scores"]
        
        logger.info(f"📊 Service Classification: L1={service_classification['level1_category']}, "
                   f"L2={service_classification['level2_service']}, "
                   f"L3={service_classification['level3_specific']}")
        
        # Step 2: Prepare consolidated payload
        consolidated_payload = self._prepare_consolidated_payload(
            standardized_fields,
            service_classification,
            form_data,
            form_identifier
        )
        
        # Step 3: Apply existing field mapper for GHL field IDs
        # This maintains compatibility with your existing system
        mapped_payload = self.field_mapper.map_payload(consolidated_payload)
        
        # Step 4: Enhance with service metadata
        enhanced_payload = self._enhance_with_metadata(
            mapped_payload,
            service_classification,
            confidence_scores,
            form_identifier
        )
        
        logger.info(f"✅ Enhanced payload ready with {len(enhanced_payload)} fields")
        
        return enhanced_payload
    
    def _prepare_consolidated_payload(self,
                                     standardized_fields: Dict[str, Any],
                                     service_classification: Dict[str, Any],
                                     original_data: Dict[str, Any],
                                     form_identifier: str) -> Dict[str, Any]:
        """
        Prepare a consolidated payload that merges standardized fields
        with original data while avoiding duplication.
        """
        
        consolidated = {}
        
        # Add standardized fields first
        consolidated.update(standardized_fields)
        
        # Add service classification fields
        consolidated["primary_service_category"] = service_classification.get("level1_category", "")
        consolidated["service_type"] = service_classification.get("level2_service", "")
        
        # CRITICAL: Map Level 3 to specific_service_requested if not already present
        if service_classification.get("level3_specific"):
            if "specific_service_requested" in consolidated:
                # Append Level 3 to existing value
                existing = consolidated["specific_service_requested"]
                consolidated["specific_service_requested"] = f"{existing} - {service_classification['level3_specific']}"
            else:
                consolidated["specific_service_requested"] = service_classification["level3_specific"]
        
        # Add original fields that weren't standardized (preserving all data)
        for key, value in original_data.items():
            if key not in consolidated and value:
                # Check if this is a redundant custom field we should skip
                if not self._is_redundant_custom_field(key):
                    consolidated[key] = value
        
        # Ensure critical fields are present
        consolidated = self._ensure_critical_fields(consolidated, original_data)
        
        return consolidated
    
    def _is_redundant_custom_field(self, field_name: str) -> bool:
        """
        Check if a field is one of the redundant custom fields
        that should be consolidated.
        """
        
        redundant_patterns = [
            "what_management_services",
            "what_specific_attorney",
            "what_specific_charter",
            "what_specific_sailboat",
            "what_specific_parts",
            "what_type_of_fuel",
            "what_type_of_party",
            "what_type_of_private",
            "what_type_of_salvage",
            "what_type_of_trip",
            "what_education_or_training",
            "what_type_of_boat_club",
            "what_type_of_crew",
            "what_product_category",
            "what_product_specifically"
        ]
        
        field_lower = field_name.lower().replace(" ", "_")
        
        for pattern in redundant_patterns:
            if pattern in field_lower:
                logger.debug(f"🚫 Skipping redundant field: {field_name}")
                return True
        
        return False
    
    def _ensure_critical_fields(self, payload: Dict[str, Any], original_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure critical fields are present in the payload.
        """
        
        # List of critical fields and their fallback sources
        critical_fields = {
            "firstName": ["first_name", "fname", "First Name", "name"],
            "lastName": ["last_name", "lname", "Last Name", "surname"],
            "email": ["Email", "email_address", "Email Address", "contact_email"],
            "phone": ["Phone", "phone_number", "Phone Number", "contact_phone"],
            "zip_code_of_service": ["zip", "zipcode", "Zip Code", "Service Zip Code", "Location"]
        }
        
        for target_field, source_options in critical_fields.items():
            if target_field not in payload or not payload[target_field]:
                # Try to find value from source options
                for source in source_options:
                    if source in original_data and original_data[source]:
                        payload[target_field] = original_data[source]
                        logger.debug(f"📍 Found {target_field} from {source}")
                        break
        
        return payload
    
    def _enhance_with_metadata(self,
                              payload: Dict[str, Any],
                              service_classification: Dict[str, Any],
                              confidence_scores: Dict[str, Any],
                              form_identifier: str) -> Dict[str, Any]:
        """
        Enhance the payload with service metadata for better tracking and routing.
        """
        
        # Add service metadata as a JSON field
        service_metadata = {
            "classification": service_classification,
            "confidence_scores": confidence_scores,
            "form_source": form_identifier,
            "processing_timestamp": datetime.now().isoformat(),
            "processor_version": "2.0_service_dictionary_mapper"
        }
        
        # Store metadata in a custom field
        payload["service_classification_metadata"] = json.dumps(service_metadata)
        
        # Add routing hints
        if service_classification.get("level1_category"):
            payload["routing_category"] = service_classification["level1_category"]
        
        if service_classification.get("level2_service"):
            payload["routing_service"] = service_classification["level2_service"]
        
        # Set priority based on service type
        payload["routing_priority"] = self._determine_priority(service_classification)
        
        return payload
    
    def _determine_priority(self, service_classification: Dict[str, Any]) -> str:
        """
        Determine routing priority based on service classification.
        """
        
        level1 = service_classification.get("level1_category", "").lower()
        level2 = service_classification.get("level2_service", "").lower()
        
        # High priority services
        high_priority = [
            "emergency", "urgent", "leak", "damage", "sinking", "fire", "accident"
        ]
        
        # Check for high priority keywords
        for keyword in high_priority:
            if keyword in level1 or keyword in level2:
                return "high"
        
        # Medium priority for time-sensitive services
        if any(term in level1 for term in ["charter", "rental", "delivery"]):
            return "medium"
        
        # Default priority
        return "normal"
    
    def get_service_category_for_form(self, form_identifier: str) -> str:
        """
        Get the service category for a form identifier.
        Maintains backward compatibility with existing code.
        """
        
        # Map form identifiers to service categories
        form_to_category = {
            # Repairs
            "fiberglass_repair": "Boat and Yacht Repair",
            "engine_repair": "Engines and Generators",
            "canvas_upholstery": "Boat and Yacht Repair",
            
            # Charters
            "yacht_charter": "Boat Charters and Rentals",
            "sailboat_charter": "Boat Charters and Rentals",
            "fishing_charter": "Boat Charters and Rentals",
            "party_boat": "Boat Charters and Rentals",
            
            # Services
            "boat_detailing": "Boat Maintenance",
            "bottom_painting": "Boat Maintenance",
            "yacht_management": "Yacht Management",
            
            # Resources
            "attorney": "Boater Resources",
            "insurance": "Buying or Selling a Boat",
            "financing": "Buying or Selling a Boat",
            "survey": "Buying or Selling a Boat",
            
            # Default
            "general": "Boater Resources"
        }
        
        # Check exact match
        if form_identifier in form_to_category:
            return form_to_category[form_identifier]
        
        # Check partial match
        form_lower = form_identifier.lower()
        for key, category in form_to_category.items():
            if key in form_lower or form_lower in key:
                return category
        
        # Default
        return "Boater Resources"


# Create singleton instance
enhanced_processor = EnhancedWebhookProcessor()


# =============================================================================
# INTEGRATION FUNCTIONS FOR webhook_routes.py
# =============================================================================

def integrate_service_mapping(normalize_field_names_func):
    """
    Decorator to integrate service mapping with the existing normalize_field_names function.
    
    Usage in webhook_routes.py:
    ```python
    from api.services.webhook_integration_patch import integrate_service_mapping
    
    @integrate_service_mapping
    def normalize_field_names(payload):
        # existing code...
    ```
    """
    
    def wrapper(payload: Dict[str, Any]) -> Dict[str, Any]:
        # First, run the original normalization
        normalized = normalize_field_names_func(payload)
        
        # Then apply service dictionary mapping
        try:
            # Get form identifier from payload
            form_identifier = payload.get("form_name", payload.get("form_id", "unknown"))
            
            # Process with enhanced mapper
            enhanced_result = enhanced_processor.process_form_with_service_mapping(
                normalized,
                form_identifier
            )
            
            logger.info(f"✅ Enhanced field mapping applied: {len(enhanced_result)} fields")
            return enhanced_result
            
        except Exception as e:
            logger.error(f"❌ Service mapping failed, falling back to original: {e}")
            return normalized
    
    return wrapper


def patch_webhook_routes():
    """
    Patch the webhook_routes module to use the enhanced service mapping.
    Call this function during application startup.
    
    Usage in main_working_final.py:
    ```python
    from api.services.webhook_integration_patch import patch_webhook_routes
    
    # During app initialization
    patch_webhook_routes()
    ```
    """
    
    try:
        import api.routes.webhook_routes as webhook_routes
        
        # Store original functions
        original_normalize = webhook_routes.normalize_field_names
        original_get_service = getattr(webhook_routes, 'get_direct_service_category', None)
        
        # Create enhanced versions
        def enhanced_normalize_field_names(payload: Dict[str, Any]) -> Dict[str, Any]:
            """Enhanced field normalization with service mapping"""
            
            # Run original normalization
            normalized = original_normalize(payload)
            
            # Apply service dictionary mapping
            form_identifier = payload.get("form_name", payload.get("form_id", "unknown"))
            
            try:
                result = enhanced_processor.process_form_with_service_mapping(
                    normalized,
                    form_identifier
                )
                logger.info("✅ Service dictionary mapping applied successfully")
                return result
            except Exception as e:
                logger.error(f"❌ Service mapping error: {e}")
                return normalized
        
        def enhanced_get_service_category(form_identifier: str) -> str:
            """Enhanced service category detection"""
            return enhanced_processor.get_service_category_for_form(form_identifier)
        
        # Replace functions
        webhook_routes.normalize_field_names = enhanced_normalize_field_names
        if original_get_service:
            webhook_routes.get_direct_service_category = enhanced_get_service_category
        
        logger.info("✅ Webhook routes successfully patched with service dictionary mapper")
        
    except Exception as e:
        logger.error(f"❌ Failed to patch webhook routes: {e}")


def process_webhook_with_service_mapping(webhook_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Standalone function to process webhook data with service mapping.
    Can be called directly from webhook_routes.py
    
    Args:
        webhook_data: Raw webhook payload
        
    Returns:
        Tuple of (processed_data, service_metadata)
    
    Usage in webhook_routes.py:
    ```python
    from api.services.webhook_integration_patch import process_webhook_with_service_mapping
    
    # In your webhook handler
    processed_data, service_metadata = process_webhook_with_service_mapping(form_data)
    ```
    """
    
    form_identifier = webhook_data.get("form_name", webhook_data.get("form_id", "unknown"))
    
    # Process with service mapping
    enhanced_result = enhanced_processor.process_form_with_service_mapping(
        webhook_data,
        form_identifier
    )
    
    # Extract service metadata
    service_metadata = {
        "primary_category": enhanced_result.get("primary_service_category"),
        "service_type": enhanced_result.get("service_type"),
        "specific_service": enhanced_result.get("specific_service_requested"),
        "routing_category": enhanced_result.get("routing_category"),
        "routing_priority": enhanced_result.get("routing_priority"),
        "metadata": json.loads(enhanced_result.get("service_classification_metadata", "{}"))
    }
    
    return enhanced_result, service_metadata


# =============================================================================
# MIGRATION HELPER FUNCTIONS
# =============================================================================

def identify_fields_to_consolidate(field_reference: Dict[str, Any]) -> Dict[str, str]:
    """
    Identify which custom fields in field_reference.json should be consolidated.
    
    Returns:
        Dict mapping field IDs to their consolidated standard field
    """
    
    fields_to_consolidate = {}
    
    redundant_patterns = [
        ("what management services", "specific_service_requested"),
        ("what specific attorney", "specific_service_requested"),
        ("what specific charter", "specific_service_requested"),
        ("what specific sailboat", "specific_service_requested"),
        ("what specific service", "specific_service_requested"),
        ("what specific parts", "specific_service_requested"),
        ("what type of fuel", "specific_service_requested"),
        ("what type of party boat", "specific_service_requested"),
        ("what type of private yacht", "specific_service_requested"),
        ("what type of salvage", "specific_service_requested"),
        ("what type of trip", "specific_service_requested"),
        ("what education or training", "specific_service_requested"),
        ("what type of boat club", "specific_service_requested"),
        ("what type of crew", "specific_service_requested"),
        ("what product category", "product_category"),
        ("what product specifically", "product_specific")
    ]
    
    for field_name, field_data in field_reference.items():
        field_lower = field_name.lower()
        field_id = field_data.get("id")
        
        for pattern, consolidated_field in redundant_patterns:
            if pattern in field_lower and field_id:
                fields_to_consolidate[field_id] = consolidated_field
                logger.info(f"📋 Field '{field_name}' (ID: {field_id}) → {consolidated_field}")
                break
    
    return fields_to_consolidate


def generate_cleanup_report(field_reference: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a report of fields that can be cleaned up.
    
    Returns:
        Detailed cleanup report
    """
    
    consolidation_map = identify_fields_to_consolidate(field_reference)
    
    report = {
        "total_custom_fields": len(field_reference),
        "fields_to_consolidate": len(consolidation_map),
        "consolidation_targets": {},
        "estimated_cleanup": {
            "fields_to_remove": [],
            "fields_to_keep": [],
            "new_standard_fields": set()
        }
    }
    
    # Group by consolidation target
    for field_id, target in consolidation_map.items():
        if target not in report["consolidation_targets"]:
            report["consolidation_targets"][target] = []
        report["consolidation_targets"][target].append(field_id)
        report["estimated_cleanup"]["new_standard_fields"].add(target)
    
    # Identify fields to remove
    for field_name, field_data in field_reference.items():
        field_id = field_data.get("id")
        if field_id in consolidation_map:
            report["estimated_cleanup"]["fields_to_remove"].append({
                "name": field_name,
                "id": field_id,
                "consolidate_to": consolidation_map[field_id]
            })
        else:
            report["estimated_cleanup"]["fields_to_keep"].append({
                "name": field_name,
                "id": field_id
            })
    
    report["estimated_cleanup"]["new_standard_fields"] = list(
        report["estimated_cleanup"]["new_standard_fields"]
    )
    
    return report


# Example usage documentation
"""
INTEGRATION GUIDE
=================

1. In your webhook_routes.py, add at the top:
   ```python
   from api.services.webhook_integration_patch import (
       process_webhook_with_service_mapping,
       enhanced_processor
   )
   ```

2. In your webhook handler, replace the normalization with:
   ```python
   # Instead of:
   normalized_data = normalize_field_names(form_data)
   
   # Use:
   processed_data, service_metadata = process_webhook_with_service_mapping(form_data)
   ```

3. The service_metadata will contain:
   - primary_category: Level 1 service category
   - service_type: Level 2 service type
   - specific_service: Level 3 specific service
   - routing_priority: Priority for routing
   - metadata: Complete classification details

4. In main_working_final.py, add during startup:
   ```python
   from api.services.webhook_integration_patch import patch_webhook_routes
   patch_webhook_routes()
   ```

This integration maintains full backward compatibility while adding
intelligent service classification and field consolidation.
"""