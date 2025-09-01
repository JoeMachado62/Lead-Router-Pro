"""
Dynamic Form Configuration Manager
Handles form registration, auto-discovery, and webhook processing
"""

import json
import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime

from staging.dynamic_forms.models.form_models import (
    FormConfiguration,
    FormFieldConfiguration,
    UnregisteredFormSubmission,
    FormAnalytics,
    DynamicServiceCategory
)

logger = logging.getLogger(__name__)


class FormManager:
    """Manages dynamic form configurations and processing"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    # ============================================
    # FORM REGISTRATION
    # ============================================
    
    def register_form(self, form_config: Dict) -> FormConfiguration:
        """
        Register a new form configuration
        
        Example config:
        {
            "form_identifier": "luxury-rental-inquiry",
            "form_name": "Luxury Rental Inquiry Form",
            "form_type": "client_lead",
            "category_name": "Waterfront Vacation Rentals",
            "required_fields": ["firstName", "lastName", "email", "phone"],
            "priority": "normal",
            "auto_route_to_vendor": True
        }
        """
        try:
            # Check if form already exists
            existing = self.db.query(FormConfiguration).filter_by(
                form_identifier=form_config["form_identifier"]
            ).first()
            
            if existing:
                logger.warning(f"Form '{form_config['form_identifier']}' already exists")
                return self.update_form(form_config["form_identifier"], form_config)
            
            # Get category if specified
            category = None
            if form_config.get("category_name"):
                category = self.db.query(DynamicServiceCategory).filter_by(
                    category_name=form_config["category_name"]
                ).first()
            
            # Create form configuration
            form = FormConfiguration(
                form_identifier=form_config["form_identifier"],
                form_name=form_config["form_name"],
                form_type=form_config.get("form_type", "client_lead"),
                category_id=category.id if category else None,
                default_subcategory=form_config.get("default_subcategory"),
                required_fields=form_config.get("required_fields", []),
                optional_fields=form_config.get("optional_fields", []),
                field_mappings=form_config.get("field_mappings", {}),
                validation_rules=form_config.get("validation_rules", {}),
                priority=form_config.get("priority", "normal"),
                auto_route_to_vendor=form_config.get("auto_route_to_vendor", False),
                requires_approval=form_config.get("requires_approval", False),
                send_confirmation_email=form_config.get("send_confirmation_email", True),
                webhook_endpoint=form_config.get("webhook_endpoint"),
                webhook_headers=form_config.get("webhook_headers", {}),
                default_tags=form_config.get("default_tags", []),
                meta_data=form_config.get("metadata", {}),  # Use meta_data to avoid SQLAlchemy conflict
                created_by=form_config.get("created_by", "system")
            )
            
            self.db.add(form)
            
            # Add field configurations if provided
            if form_config.get("fields"):
                for field_config in form_config["fields"]:
                    self.add_field_configuration(form, field_config)
            
            self.db.commit()
            
            logger.info(f"Registered form: {form_config['form_identifier']}")
            return form
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error registering form: {e}")
            raise
    
    def add_field_configuration(self, form: FormConfiguration, field_config: Dict):
        """Add detailed field configuration to a form"""
        field = FormFieldConfiguration(
            form_id=form.id,
            field_name=field_config["field_name"],
            field_label=field_config.get("field_label"),
            field_type=field_config.get("field_type", "text"),
            ghl_field_name=field_config.get("ghl_field_name"),
            ghl_field_id=field_config.get("ghl_field_id"),
            is_required=field_config.get("is_required", False),
            validation_pattern=field_config.get("validation_pattern"),
            min_length=field_config.get("min_length"),
            max_length=field_config.get("max_length"),
            allowed_values=field_config.get("allowed_values"),
            transform_function=field_config.get("transform_function"),
            default_value=field_config.get("default_value"),
            sort_order=field_config.get("sort_order", 0)
        )
        self.db.add(field)
    
    # ============================================
    # FORM AUTO-DISCOVERY
    # ============================================
    
    def handle_unregistered_form(self, form_identifier: str, payload: Dict) -> UnregisteredFormSubmission:
        """
        Handle submission from an unregistered form
        Auto-detect fields and suggest configuration
        """
        try:
            # Check if we've seen this form before
            existing = self.db.query(UnregisteredFormSubmission).filter_by(
                form_identifier=form_identifier,
                status="pending"
            ).first()
            
            if existing:
                # Update submission count and last seen
                existing.submission_count += 1
                existing.last_seen = datetime.utcnow()
                
                # Update detected fields with any new ones
                current_fields = set(existing.detected_fields or [])
                new_fields = set(payload.keys())
                existing.detected_fields = list(current_fields.union(new_fields))
                
                self.db.commit()
                return existing
            
            # Analyze the payload to detect form type and fields
            detected_fields = self._analyze_payload_fields(payload)
            suggested_form_type = self._suggest_form_type(payload)
            suggested_category = self._suggest_category(payload)
            
            # Create new unregistered form record
            unregistered = UnregisteredFormSubmission(
                form_identifier=form_identifier,
                raw_payload=payload,
                detected_fields=detected_fields,
                suggested_form_type=suggested_form_type,
                suggested_category=suggested_category
            )
            
            self.db.add(unregistered)
            self.db.commit()
            
            logger.info(f"Recorded unregistered form: {form_identifier}")
            return unregistered
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error handling unregistered form: {e}")
            raise
    
    def _analyze_payload_fields(self, payload: Dict) -> List[Dict]:
        """Analyze payload to detect field types and characteristics"""
        detected_fields = []
        
        for field_name, value in payload.items():
            field_info = {
                "name": field_name,
                "sample_value": str(value)[:100] if value else None,
                "type": self._detect_field_type(field_name, value),
                "is_empty": value is None or value == "",
                "length": len(str(value)) if value else 0
            }
            detected_fields.append(field_info)
        
        return detected_fields
    
    def _detect_field_type(self, field_name: str, value: Any) -> str:
        """Detect field type based on name and value"""
        field_lower = field_name.lower()
        
        # Check field name patterns
        if "email" in field_lower:
            return "email"
        elif "phone" in field_lower or "mobile" in field_lower:
            return "phone"
        elif "date" in field_lower or "time" in field_lower:
            return "datetime"
        elif "zip" in field_lower or "postal" in field_lower:
            return "zip"
        elif any(word in field_lower for word in ["address", "street", "city", "state"]):
            return "address"
        elif "url" in field_lower or "website" in field_lower:
            return "url"
        
        # Check value type
        if isinstance(value, bool):
            return "checkbox"
        elif isinstance(value, (int, float)):
            return "number"
        elif isinstance(value, list):
            return "multi_select"
        elif isinstance(value, dict):
            return "json"
        
        # Check value patterns
        if value and isinstance(value, str):
            if "@" in value and "." in value:
                return "email"
            elif value.startswith("http"):
                return "url"
            elif len(value) > 100:
                return "textarea"
        
        return "text"
    
    def _suggest_form_type(self, payload: Dict) -> str:
        """Suggest form type based on payload analysis"""
        # Check for vendor-specific fields
        vendor_indicators = ["vendor_company_name", "services_offered", "coverage_type", 
                           "services_provided", "business_name", "company_name"]
        if any(field in payload for field in vendor_indicators):
            return "vendor_application"
        
        # Check for emergency indicators
        emergency_indicators = ["urgent", "emergency", "immediate", "asap", "critical"]
        for field, value in payload.items():
            if any(indicator in str(value).lower() for indicator in emergency_indicators):
                return "emergency_service"
        
        # Default to client lead
        return "client_lead"
    
    def _suggest_category(self, payload: Dict) -> Optional[str]:
        """Suggest service category based on payload content"""
        # Look for service-related fields
        service_fields = ["service_requested", "service_category", "service_type", 
                         "primary_service_category", "category"]
        
        for field in service_fields:
            if field in payload and payload[field]:
                return str(payload[field])
        
        return None
    
    def auto_register_form(self, unregistered_id: str, config_overrides: Dict = None) -> FormConfiguration:
        """
        Auto-register a form based on unregistered submission data
        """
        try:
            # Get unregistered form
            unregistered = self.db.query(UnregisteredFormSubmission).filter_by(
                id=unregistered_id
            ).first()
            
            if not unregistered:
                raise ValueError(f"Unregistered form {unregistered_id} not found")
            
            # Build form configuration from detected data
            form_config = {
                "form_identifier": unregistered.form_identifier,
                "form_name": f"Auto-registered: {unregistered.form_identifier}",
                "form_type": unregistered.suggested_form_type or "client_lead",
                "category_name": unregistered.suggested_category,
                "required_fields": [],
                "optional_fields": []
            }
            
            # Extract field names from detected fields
            if unregistered.detected_fields:
                for field_info in unregistered.detected_fields:
                    if not field_info.get("is_empty"):
                        form_config["required_fields"].append(field_info["name"])
                    else:
                        form_config["optional_fields"].append(field_info["name"])
            
            # Apply any overrides
            if config_overrides:
                form_config.update(config_overrides)
            
            # Register the form
            form = self.register_form(form_config)
            
            # Update unregistered form status
            unregistered.status = "registered"
            unregistered.reviewed_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Auto-registered form: {unregistered.form_identifier}")
            return form
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error auto-registering form: {e}")
            raise
    
    # ============================================
    # FORM RETRIEVAL AND LOOKUP
    # ============================================
    
    def get_form_configuration(self, form_identifier: str) -> Optional[Dict]:
        """
        Get form configuration for webhook processing
        This is the main method called by the webhook handler
        """
        # Check for registered form
        form = self.db.query(FormConfiguration).filter_by(
            form_identifier=form_identifier,
            is_active=True
        ).first()
        
        if form:
            config = {
                "form_type": form.form_type,
                "service_category": form.category.category_name if form.category else None,
                "default_subcategory": form.default_subcategory,
                "required_fields": form.required_fields,
                "optional_fields": form.optional_fields,
                "field_mappings": form.field_mappings,
                "validation_rules": form.validation_rules,
                "priority": form.priority,
                "auto_route_to_vendor": form.auto_route_to_vendor,
                "requires_approval": form.requires_approval,
                "default_tags": form.default_tags,
                "metadata": form.meta_data  # Use meta_data field
            }
            
            # Update submission tracking
            form.submission_count += 1
            form.last_submission = datetime.utcnow()
            self.db.commit()
            
            return config
        
        return None
    
    def get_all_forms(self, active_only: bool = True, form_type: Optional[str] = None) -> List[Dict]:
        """Get all registered forms"""
        query = self.db.query(FormConfiguration)
        
        if active_only:
            query = query.filter_by(is_active=True)
        
        if form_type:
            query = query.filter_by(form_type=form_type)
        
        forms = query.order_by(FormConfiguration.created_at.desc()).all()
        
        return [form.to_dict() for form in forms]
    
    def get_unregistered_forms(self, status: str = "pending") -> List[Dict]:
        """Get unregistered form submissions for review"""
        forms = self.db.query(UnregisteredFormSubmission).filter_by(
            status=status
        ).order_by(UnregisteredFormSubmission.submission_count.desc()).all()
        
        return [
            {
                "id": form.id,
                "form_identifier": form.form_identifier,
                "submission_count": form.submission_count,
                "first_seen": form.first_seen.isoformat(),
                "last_seen": form.last_seen.isoformat(),
                "detected_fields": form.detected_fields,
                "suggested_form_type": form.suggested_form_type,
                "suggested_category": form.suggested_category
            }
            for form in forms
        ]
    
    # ============================================
    # FORM TESTING
    # ============================================
    
    def test_form(self, form_identifier: str, test_payload: Dict) -> Dict[str, Any]:
        """Test a form configuration with sample data"""
        config = self.get_form_configuration(form_identifier)
        
        if not config:
            return {
                "success": False,
                "error": f"Form '{form_identifier}' not found"
            }
        
        results = {
            "success": True,
            "form_type": config["form_type"],
            "validation_results": {},
            "field_mappings": {},
            "warnings": []
        }
        
        # Validate required fields
        for field in config["required_fields"]:
            if field not in test_payload or not test_payload[field]:
                results["validation_results"][field] = "Missing required field"
                results["success"] = False
            else:
                results["validation_results"][field] = "OK"
        
        # Check field mappings
        for form_field, ghl_field in config.get("field_mappings", {}).items():
            if form_field in test_payload:
                results["field_mappings"][form_field] = f"Maps to: {ghl_field}"
        
        # Check for extra fields not in configuration
        configured_fields = set(config["required_fields"] + config.get("optional_fields", []))
        payload_fields = set(test_payload.keys())
        extra_fields = payload_fields - configured_fields
        
        if extra_fields:
            results["warnings"].append(f"Unmapped fields: {', '.join(extra_fields)}")
        
        return results
    
    # ============================================
    # FORM UPDATES
    # ============================================
    
    def update_form(self, form_identifier: str, updates: Dict) -> FormConfiguration:
        """Update an existing form configuration"""
        try:
            form = self.db.query(FormConfiguration).filter_by(
                form_identifier=form_identifier
            ).first()
            
            if not form:
                raise ValueError(f"Form '{form_identifier}' not found")
            
            # Update allowed fields
            updateable_fields = [
                "form_name", "form_type", "default_subcategory", "required_fields",
                "optional_fields", "field_mappings", "validation_rules", "priority",
                "auto_route_to_vendor", "requires_approval", "send_confirmation_email",
                "default_tags", "metadata", "is_active"
            ]
            
            for field in updateable_fields:
                if field in updates:
                    setattr(form, field, updates[field])
            
            # Update category if provided
            if "category_name" in updates:
                category = self.db.query(DynamicServiceCategory).filter_by(
                    category_name=updates["category_name"]
                ).first()
                form.category_id = category.id if category else None
            
            form.updated_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Updated form: {form_identifier}")
            return form
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating form: {e}")
            raise
    
    def delete_form(self, form_identifier: str) -> bool:
        """Soft delete a form (set inactive)"""
        try:
            form = self.db.query(FormConfiguration).filter_by(
                form_identifier=form_identifier
            ).first()
            
            if not form:
                return False
            
            form.is_active = False
            form.updated_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Deactivated form: {form_identifier}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting form: {e}")
            return False