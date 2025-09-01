"""
Dynamic Form and Service Category Management Models
Staging Environment - Safe for testing without affecting production
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

# ============================================
# SERVICE CATEGORY MANAGEMENT MODELS
# ============================================

class DynamicServiceCategory(Base):
    """Level 1 Primary Categories - Industry/vertical specific"""
    __tablename__ = "dynamic_service_categories"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    category_name = Column(String(255), unique=True, nullable=False)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)
    icon_url = Column(String(500))
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    requires_location = Column(Boolean, default=True)
    requires_timeline = Column(Boolean, default=False)
    
    # Metadata for form generation
    form_fields = Column(JSON)  # Additional fields specific to this category
    validation_rules = Column(JSON)
    
    # Relationships
    subcategories = relationship("DynamicServiceSubcategory", back_populates="category", cascade="all, delete-orphan")
    forms = relationship("FormConfiguration", back_populates="category")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))
    
    def to_dict(self):
        return {
            "id": self.id,
            "category_name": self.category_name,
            "display_name": self.display_name,
            "description": self.description,
            "subcategories": [sub.to_dict() for sub in self.subcategories if sub.is_active]
        }


class DynamicServiceSubcategory(Base):
    """Level 2 Subcategories - Service types within a category"""
    __tablename__ = "dynamic_service_subcategories"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    category_id = Column(String(36), ForeignKey("dynamic_service_categories.id"), nullable=False)
    subcategory_name = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Control whether this subcategory has Level 3 services
    has_level3_services = Column(Boolean, default=False)
    level3_prompt = Column(String(500))  # "Select specific amenities:" for rentals
    
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Vendor-specific settings
    requires_certification = Column(Boolean, default=False)
    certification_types = Column(JSON)  # List of required certifications
    
    # Relationships
    category = relationship("DynamicServiceCategory", back_populates="subcategories")
    level3_services = relationship("DynamicLevel3Service", back_populates="subcategory", cascade="all, delete-orphan")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "subcategory_name": self.subcategory_name,
            "display_name": self.display_name,
            "has_level3_services": self.has_level3_services,
            "level3_services": [svc.to_dict() for svc in self.level3_services if svc.is_active]
        }


class DynamicLevel3Service(Base):
    """Level 3 Specific Services - Granular service options"""
    __tablename__ = "dynamic_level3_services"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    subcategory_id = Column(String(36), ForeignKey("dynamic_service_subcategories.id"), nullable=False)
    service_name = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Service-specific attributes
    is_premium = Column(Boolean, default=False)
    base_price = Column(Float)
    estimated_duration = Column(Integer)  # in minutes
    
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)  # Pre-selected in vendor forms
    
    # Relationships
    subcategory = relationship("DynamicServiceSubcategory", back_populates="level3_services")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "service_name": self.service_name,
            "display_name": self.display_name,
            "is_premium": self.is_premium,
            "is_default": self.is_default
        }


# ============================================
# FORM CONFIGURATION MODELS
# ============================================

class FormConfiguration(Base):
    """Dynamic form configurations for different form types"""
    __tablename__ = "form_configurations"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    form_identifier = Column(String(255), unique=True, nullable=False)
    form_name = Column(String(255), nullable=False)
    form_type = Column(String(50), nullable=False)  # client_lead, vendor_application, emergency_service
    
    # Service category mapping
    category_id = Column(String(36), ForeignKey("dynamic_service_categories.id"))
    default_subcategory = Column(String(255))  # Optional default Level 2
    
    # Form configuration
    required_fields = Column(JSON, default=list)  # ["firstName", "lastName", "email", etc.]
    optional_fields = Column(JSON, default=list)
    field_mappings = Column(JSON, default=dict)  # Map form fields to GHL fields
    validation_rules = Column(JSON, default=dict)
    
    # Behavior settings
    priority = Column(String(20), default="normal")  # normal, high, emergency
    auto_route_to_vendor = Column(Boolean, default=False)
    requires_approval = Column(Boolean, default=False)
    send_confirmation_email = Column(Boolean, default=True)
    
    # Webhook configuration
    webhook_endpoint = Column(String(500))
    webhook_headers = Column(JSON, default=dict)
    webhook_timeout = Column(Integer, default=30)
    
    # Tags and metadata
    default_tags = Column(JSON, default=list)
    meta_data = Column(JSON, default=dict)  # Renamed from metadata to avoid SQLAlchemy conflict
    
    # Status
    is_active = Column(Boolean, default=True)
    is_tested = Column(Boolean, default=False)
    last_submission = Column(DateTime)
    submission_count = Column(Integer, default=0)
    
    # Relationships
    category = relationship("DynamicServiceCategory", back_populates="forms")
    field_configs = relationship("FormFieldConfiguration", back_populates="form", cascade="all, delete-orphan")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))
    
    def to_dict(self):
        return {
            "id": self.id,
            "form_identifier": self.form_identifier,
            "form_name": self.form_name,
            "form_type": self.form_type,
            "category": self.category.display_name if self.category else None,
            "is_active": self.is_active,
            "submission_count": self.submission_count
        }


class FormFieldConfiguration(Base):
    """Detailed field configuration for each form"""
    __tablename__ = "form_field_configurations"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    form_id = Column(String(36), ForeignKey("form_configurations.id"), nullable=False)
    
    field_name = Column(String(100), nullable=False)  # Form field name
    field_label = Column(String(255))
    field_type = Column(String(50))  # text, email, phone, select, checkbox, etc.
    
    # Mapping
    ghl_field_name = Column(String(100))  # Maps to GHL custom field
    ghl_field_id = Column(String(100))
    
    # Validation
    is_required = Column(Boolean, default=False)
    validation_pattern = Column(String(500))  # Regex pattern
    min_length = Column(Integer)
    max_length = Column(Integer)
    allowed_values = Column(JSON)  # For select/radio fields
    
    # Transformation
    transform_function = Column(String(100))  # uppercase, lowercase, phone_format, etc.
    default_value = Column(String(500))
    
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    form = relationship("FormConfiguration", back_populates="field_configs")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================
# VENDOR FORM TEMPLATE MODEL
# ============================================

class VendorFormTemplate(Base):
    """Templates for dynamically generated vendor forms"""
    __tablename__ = "vendor_form_templates"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    template_name = Column(String(255), unique=True, nullable=False)
    category_id = Column(String(36), ForeignKey("dynamic_service_categories.id"))
    
    # Template configuration
    include_level3_selection = Column(Boolean, default=True)
    max_categories = Column(Integer, default=3)  # Max primary + additional categories
    max_services_per_category = Column(Integer, default=10)
    
    # Coverage options
    allow_global_coverage = Column(Boolean, default=False)
    allow_national_coverage = Column(Boolean, default=False)
    allow_state_coverage = Column(Boolean, default=True)
    allow_county_coverage = Column(Boolean, default=True)
    allow_zip_coverage = Column(Boolean, default=True)
    
    # Additional fields
    custom_fields = Column(JSON, default=list)  # Additional vendor-specific fields
    required_documents = Column(JSON, default=list)  # Insurance, license, etc.
    
    # Styling
    theme_colors = Column(JSON, default=dict)
    logo_url = Column(String(500))
    header_text = Column(Text)
    footer_text = Column(Text)
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================
# AUTO-DISCOVERY MODEL
# ============================================

class UnregisteredFormSubmission(Base):
    """Track unregistered form submissions for auto-discovery"""
    __tablename__ = "unregistered_form_submissions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    form_identifier = Column(String(255), nullable=False)
    
    # Submission data
    raw_payload = Column(JSON, nullable=False)
    detected_fields = Column(JSON)  # Auto-detected field names and types
    suggested_form_type = Column(String(50))  # AI-suggested form type
    suggested_category = Column(String(255))  # AI-suggested service category
    
    # Tracking
    submission_count = Column(Integer, default=1)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    
    # Status
    status = Column(String(50), default="pending")  # pending, reviewed, registered, ignored
    reviewed_by = Column(String(100))
    reviewed_at = Column(DateTime)
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================
# ANALYTICS MODEL
# ============================================

class FormAnalytics(Base):
    """Track form performance and usage"""
    __tablename__ = "form_analytics"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    form_id = Column(String(36), ForeignKey("form_configurations.id"))
    
    date = Column(DateTime, nullable=False)
    submissions = Column(Integer, default=0)
    successful_submissions = Column(Integer, default=0)
    failed_submissions = Column(Integer, default=0)
    
    avg_processing_time = Column(Float)  # in seconds
    conversion_rate = Column(Float)  # For vendor applications
    
    # Error tracking
    validation_errors = Column(Integer, default=0)
    ghl_errors = Column(Integer, default=0)
    routing_errors = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)