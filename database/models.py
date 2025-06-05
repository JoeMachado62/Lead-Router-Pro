from sqlalchemy import create_engine, Column, String, DateTime, JSON, Integer, Float, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

Base = declarative_base()

class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ghl_location_id = Column(String(255), unique=True, nullable=False)
    company_name = Column(String(255), nullable=False)
    industry = Column(String(100), default="general")
    settings = Column(JSON, default={})
    subscription_tier = Column(String(50), default="starter")
    ghl_api_token = Column(String(500))  # Encrypted
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    vendors = relationship("Vendor", back_populates="account")
    leads = relationship("Lead", back_populates="account")

class Vendor(Base):
    __tablename__ = "vendors"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    ghl_contact_id = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    company_name = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    services_provided = Column(JSON, default=[])
    service_areas = Column(JSON, default=[])
    performance_score = Column(Float, default=0.0)
    total_leads_received = Column(Integer, default=0)
    total_leads_closed = Column(Integer, default=0)
    avg_response_time_hours = Column(Float, default=24.0)
    customer_rating = Column(Float, default=5.0)
    status = Column(String(50), default="active")
    taking_new_work = Column(Boolean, default=True)
    last_lead_assigned = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    account = relationship("Account", back_populates="vendors")
    leads = relationship("Lead", back_populates="vendor")
    performance_metrics = relationship("PerformanceMetric", back_populates="vendor")

class Lead(Base):
    __tablename__ = "leads"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"))
    ghl_contact_id = Column(String(255), nullable=False)
    service_category = Column(String(100))
    service_details = Column(JSON, default={})
    location_data = Column(JSON, default={})
    estimated_value = Column(Float, default=0.0)
    priority_score = Column(Float, default=0.0)
    status = Column(String(50), default="new")
    assignment_history = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    assigned_at = Column(DateTime)
    first_response_at = Column(DateTime)
    closed_at = Column(DateTime)
    outcome = Column(String(50))  # won, lost, qualified_out
    
    # Relationships
    account = relationship("Account", back_populates="leads")
    vendor = relationship("Vendor", back_populates="leads")
    feedback = relationship("Feedback", back_populates="lead")

class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"))
    metric_type = Column(String(50), nullable=False)  # response_time, conversion, rating
    metric_value = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    vendor = relationship("Vendor", back_populates="performance_metrics")

class Feedback(Base):
    __tablename__ = "feedback"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=False)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False)
    rating = Column(Integer)  # 1-5 scale
    comments = Column(Text)
    feedback_type = Column(String(50), default="post_service")
    submitted_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    lead = relationship("Lead", back_populates="feedback")
