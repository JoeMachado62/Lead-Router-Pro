# Smart Lead Router Pro - Development Implementation Prompt

## Project Mission
Transform the working DockSide Pros Lead Router MVP into a production-ready GHL Marketplace SaaS application with multi-tenant architecture, advanced analytics, and white-label capabilities.

## Development Environment Setup

### Step 1: Initialize Project Structure
```bash
# Create project directory structure
mkdir smart-lead-router-pro
cd smart-lead-router-pro

# Create core directories
mkdir -p {
  api/{routes,middleware,services,models},
  dashboard/{components,pages,hooks,utils},
  database/{migrations,seeds},
  docker,
  tests/{unit,integration},
  scripts,
  docs,
  config
}

# Initialize package files
touch {requirements.txt,.env.example,docker-compose.yml,Dockerfile}
```

### Step 2: Create Development Environment
```bash
# Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install base dependencies
pip install fastapi uvicorn sqlalchemy alembic psycopg2-binary redis celery
pip install pytest pytest-asyncio httpx
pip install openai anthropic  # For AI classification
pip install stripe  # For billing
pip install sentry-sdk  # For monitoring

# Frontend dependencies (if building React dashboard)
cd dashboard
npm init -y
npm install react next.js typescript @types/react
npm install tailwindcss recharts lucide-react
```

### Step 3: Database Setup (Local Development)
```python
# File: database/models.py
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

# File: database/connection.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/smartleadrouter")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

## Core Application Development

### Step 4: Multi-Tenant Lead Router Service
```python
# File: api/services/lead_router.py
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
from sqlalchemy.orm import Session
from ..models import Account, Vendor, Lead, PerformanceMetric
from .ghl_api import GoHighLevelAPI
from .ai_classifier import AIServiceClassifier
from .performance_calculator import PerformanceCalculator

class MultiTenantLeadRouter:
    def __init__(self, account_id: str, db: Session):
        self.account_id = account_id
        self.db = db
        self.account = self._get_account()
        self.ghl_api = GoHighLevelAPI(
            self.account.ghl_api_token,
            self.account.ghl_location_id
        )
        self.ai_classifier = AIServiceClassifier(self.account.industry)
        self.performance_calc = PerformanceCalculator(db)
    
    def _get_account(self) -> Account:
        return self.db.query(Account).filter(Account.id == self.account_id).first()
    
    async def process_lead(self, form_data: Dict) -> Dict:
        """Main lead processing pipeline"""
        try:
            # Step 1: AI-powered service classification
            service_info = await self.ai_classifier.classify_service(form_data)
            
            # Step 2: Lead scoring and valuation
            lead_score = await self._calculate_lead_score(form_data, service_info)
            
            # Step 3: Intelligent vendor matching
            matching_vendors = await self._find_matching_vendors(
                service_info['category'], 
                form_data.get('location', ''),
                lead_score['estimated_value']
            )
            
            # Step 4: Performance-based vendor selection
            selected_vendor = await self._select_optimal_vendor(matching_vendors, lead_score)
            
            # Step 5: Create lead in database and GHL
            lead = await self._create_lead_record(form_data, service_info, lead_score, selected_vendor)
            
            # Step 6: Create GHL contact and opportunity
            ghl_contact = await self._create_ghl_contact(lead, form_data)
            if ghl_contact:
                lead.ghl_contact_id = ghl_contact['id']
                
                if selected_vendor:
                    await self._create_ghl_opportunity(lead, selected_vendor)
                    await self._update_vendor_assignment(selected_vendor, lead)
            
            # Step 7: Trigger notifications
            if selected_vendor:
                await self._notify_vendor(selected_vendor, lead)
            
            self.db.commit()
            
            return {
                "success": True,
                "lead_id": str(lead.id),
                "ghl_contact_id": lead.ghl_contact_id,
                "service_category": service_info['category'],
                "confidence_score": service_info['confidence'],
                "assigned_vendor": selected_vendor.company_name if selected_vendor else None,
                "estimated_value": lead_score['estimated_value'],
                "priority_score": lead_score['priority']
            }
            
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def _calculate_lead_score(self, form_data: Dict, service_info: Dict) -> Dict:
        """Calculate lead value and priority using ML"""
        # Implementation for lead scoring algorithm
        base_value = self._get_base_service_value(service_info['category'])
        
        # Factors that influence lead value
        completeness_score = self._score_form_completeness(form_data)
        urgency_score = self._detect_urgency_indicators(form_data)
        geographic_score = await self._score_geographic_demand(form_data.get('location'))
        seasonal_score = self._score_seasonal_factors(service_info['category'])
        
        estimated_value = base_value * (1 + completeness_score + geographic_score + seasonal_score)
        priority_score = (urgency_score * 0.4) + (completeness_score * 0.3) + (estimated_value / 10000 * 0.3)
        
        return {
            "estimated_value": round(estimated_value, 2),
            "priority": round(priority_score, 2),
            "factors": {
                "completeness": completeness_score,
                "urgency": urgency_score,
                "geographic": geographic_score,
                "seasonal": seasonal_score
            }
        }
    
    async def _find_matching_vendors(self, service_category: str, location: str, lead_value: float) -> List[Vendor]:
        """Find vendors matching service and location with performance consideration"""
        query = self.db.query(Vendor).filter(
            Vendor.account_id == self.account_id,
            Vendor.status == "active",
            Vendor.taking_new_work == True
        )
        
        # Service matching
        vendors = []
        for vendor in query.all():
            if self._service_matches(vendor.services_provided, service_category):
                if self._location_matches(vendor.service_areas, location):
                    vendors.append(vendor)
        
        # Filter by capacity and performance for high-value leads
        if lead_value > 5000:  # High-value leads get premium vendors
            vendors = [v for v in vendors if v.performance_score > 0.7]
        
        return vendors
    
    async def _select_optimal_vendor(self, vendors: List[Vendor], lead_score: Dict) -> Optional[Vendor]:
        """Select best vendor using performance-weighted round-robin"""
        if not vendors:
            return None
        
        # Calculate selection weights based on performance and availability
        vendor_weights = []
        for vendor in vendors:
            # Base weight from performance score
            weight = vendor.performance_score
            
            # Boost vendors who haven't received leads recently
            hours_since_last = self._hours_since_last_assignment(vendor)
            if hours_since_last > 24:
                weight *= 1.2
            elif hours_since_last < 2:
                weight *= 0.8
            
            # Consider workload
            current_load = self._get_vendor_current_load(vendor)
            if current_load > 10:  # Too many active leads
                weight *= 0.5
            
            vendor_weights.append((vendor, weight))
        
        # Weighted random selection favoring top performers
        vendor_weights.sort(key=lambda x: x[1], reverse=True)
        
        # For high-priority leads, always select top performer
        if lead_score['priority'] > 0.8:
            return vendor_weights[0][0]
        
        # Otherwise, weighted selection with some randomization
        total_weight = sum(weight for _, weight in vendor_weights)
        if total_weight > 0:
            import random
            selection_point = random.uniform(0, total_weight)
            current_weight = 0
            for vendor, weight in vendor_weights:
                current_weight += weight
                if current_weight >= selection_point:
                    return vendor
        
        return vendor_weights[0][0] if vendor_weights else None
    
    async def _create_lead_record(self, form_data: Dict, service_info: Dict, lead_score: Dict, vendor: Optional[Vendor]) -> Lead:
        """Create lead record in database"""
        lead = Lead(
            account_id=self.account_id,
            vendor_id=vendor.id if vendor else None,
            service_category=service_info['category'],
            service_details={
                "requested_service": form_data.get('service_requested', ''),
                "special_requests": form_data.get('special_requests', ''),
                "classification_confidence": service_info['confidence'],
                "ai_reasoning": service_info.get('reasoning', '')
            },
            location_data={
                "zip_code": form_data.get('zip_code', ''),
                "city": form_data.get('city', ''),
                "address": form_data.get('address', '')
            },
            estimated_value=lead_score['estimated_value'],
            priority_score=lead_score['priority'],
            assignment_history=[{
                "vendor_id": str(vendor.id) if vendor else None,
                "assigned_at": datetime.utcnow().isoformat(),
                "assignment_reason": "initial_routing"
            }] if vendor else []
        )
        
        if vendor:
            lead.assigned_at = datetime.utcnow()
        
        self.db.add(lead)
        self.db.flush()  # Get the ID
        return lead
    
    # Additional helper methods...
    def _service_matches(self, vendor_services: List[str], requested_service: str) -> bool:
        """Check if vendor services match requested service"""
        for service in vendor_services:
            if requested_service.lower() in service.lower() or service.lower() in requested_service.lower():
                return True
        return False
    
    def _location_matches(self, vendor_areas: List[str], requested_location: str) -> bool:
        """Check if vendor serves the requested location"""
        if not requested_location:
            return True
        for area in vendor_areas:
            if requested_location in area or area in requested_location:
                return True
        return False
```

### Step 5: AI Service Classification
```python
# File: api/services/ai_classifier.py
import openai
import anthropic
import json
from typing import Dict, Tuple
import os

class AIServiceClassifier:
    def __init__(self, industry: str = "general"):
        self.industry = industry
        self.anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.industry_categories = self._load_industry_categories()
    
    def _load_industry_categories(self) -> Dict:
        """Load service categories specific to industry"""
        categories = {
            "marine": [
                "Boat Maintenance", "Engines and Generators", "Marine Systems",
                "Boat and Yacht Repair", "Boat Hauling and Yacht Delivery",
                "Boat Towing", "Boat Charters and Rentals", "Dock and Slip Rental",
                "Fuel Delivery", "Buying or Selling a Boat", "Boater Resources",
                "Maritime Education and Training", "Yacht Management",
                "Docks, Seawalls and Lifts", "Waterfront Property"
            ],
            "home_services": [
                "HVAC", "Plumbing", "Electrical", "Roofing", "Flooring",
                "Painting", "Landscaping", "Cleaning", "Security Systems",
                "Pool Services", "Pest Control", "Appliance Repair"
            ],
            "automotive": [
                "Auto Repair", "Oil Change", "Tire Services", "Body Work",
                "Detailing", "Towing", "Transmission", "Brake Service",
                "Engine Repair", "Diagnostic", "Auto Sales"
            ],
            "general": [
                "Maintenance", "Repair", "Installation", "Consultation",
                "Emergency Service", "Inspection", "Sales", "Rental"
            ]
        }
        return categories.get(self.industry, categories["general"])
    
    async def classify_service(self, form_data: Dict) -> Dict:
        """Use Claude to classify service with high accuracy"""
        
        # Prepare form data for analysis
        form_text = self._prepare_form_text(form_data)
        
        prompt = f"""
        You are an expert service classifier for the {self.industry} industry.
        
        Analyze this service request and classify it into the most appropriate category:
        
        Available Categories: {json.dumps(self.industry_categories, indent=2)}
        
        Service Request Data:
        {form_text}
        
        Respond with ONLY a JSON object in this exact format:
        {{
            "category": "exact_category_name_from_list",
            "confidence": 0.95,
            "reasoning": "brief explanation of classification logic",
            "keywords_found": ["keyword1", "keyword2"],
            "alternative_categories": ["backup_category1", "backup_category2"]
        }}
        
        Rules:
        - Category MUST be exactly from the provided list
        - Confidence must be 0.0 to 1.0
        - If unsure, use lower confidence and provide alternatives
        - Focus on the primary service being requested
        """
        
        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result = json.loads(response.content[0].text)
            
            # Validate response
            if result.get("category") not in self.industry_categories:
                result["category"] = self.industry_categories[0]  # Default to first category
                result["confidence"] = 0.3
                result["reasoning"] = "Classification failed, using default category"
            
            return result
            
        except Exception as e:
            # Fallback to rule-based classification
            return self._fallback_classification(form_data)
    
    def _prepare_form_text(self, form_data: Dict) -> str:
        """Prepare form data for AI analysis"""
        relevant_fields = [
            'service_requested', 'service_type', 'special_requests',
            'message', 'description', 'form_source'
        ]
        
        text_parts = []
        for field in relevant_fields:
            if field in form_data and form_data[field]:
                text_parts.append(f"{field}: {form_data[field]}")
        
        return "\n".join(text_parts)
    
    def _fallback_classification(self, form_data: Dict) -> Dict:
        """Rule-based fallback classification"""
        # Simple keyword matching as fallback
        text = " ".join(str(v) for v in form_data.values()).lower()
        
        classification_rules = {
            "Boat Maintenance": ["detail", "clean", "wash", "wax", "maintenance"],
            "Engines and Generators": ["engine", "motor", "generator", "outboard"],
            "Marine Systems": ["electrical", "plumbing", "hvac", "ac", "system"],
            "Boat and Yacht Repair": ["repair", "fix", "broken", "damage", "welding"],
        }
        
        for category, keywords in classification_rules.items():
            if any(keyword in text for keyword in keywords):
                return {
                    "category": category,
                    "confidence": 0.7,
                    "reasoning": f"Fallback classification based on keywords: {keywords}",
                    "keywords_found": [kw for kw in keywords if kw in text],
                    "alternative_categories": []
                }
        
        return {
            "category": self.industry_categories[0],
            "confidence": 0.3,
            "reasoning": "No clear classification, using default",
            "keywords_found": [],
            "alternative_categories": []
        }
```

### Step 6: FastAPI Application Structure
```python
# File: main.py
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import uvicorn

from api.routes import webhooks, analytics, vendors, accounts
from database.connection import get_db, create_tables
from api.middleware.auth import validate_api_key
from api.middleware.rate_limit import RateLimitMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_tables()
    yield
    # Shutdown
    pass

app = FastAPI(
    title="Smart Lead Router Pro",
    description="AI-powered lead routing for service businesses",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimitMiddleware)

# Routes
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["webhooks"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(vendors.router, prefix="/api/v1/vendors", tags=["vendors"])
app.include_router(accounts.router, prefix="/api/v1/accounts", tags=["accounts"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# File: api/routes/webhooks.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict
import logging

from ..services.lead_router import MultiTenantLeadRouter
from ..services.webhook_processor import WebhookProcessor
from database.connection import get_db
from database.models import Account

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/elementor/{account_id}")
async def handle_elementor_webhook(
    account_id: str,
    webhook_data: Dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Handle Elementor form webhooks for specific account"""
    try:
        # Validate account exists
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Process webhook
        processor = WebhookProcessor(account_id, db)
        form_data = processor.extract_form_data(webhook_data)
        
        # Route lead
        router_service = MultiTenantLeadRouter(account_id, db)
        result = await router_service.process_lead(form_data)
        
        # Add background tasks for notifications, analytics, etc.
        if result.get("success"):
            background_tasks.add_task(
                processor.trigger_notifications,
                result["lead_id"],
                result.get("assigned_vendor")
            )
            background_tasks.add_task(
                processor.update_analytics,
                account_id,
                result
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/ghl-install")
async def handle_ghl_installation(
    installation_data: Dict,
    db: Session = Depends(get_db)
):
    """Handle GoHighLevel app installation"""
    try:
        # Extract GHL location data
        location_id = installation_data.get("locationId")
        access_token = installation_data.get("accessToken")
        
        # Create or update account
        account = Account(
            ghl_location_id=location_id,
            ghl_api_token=access_token,
            company_name=installation_data.get("companyName", "New Account"),
            subscription_tier="starter"
        )
        
        db.add(account)
        db.commit()
        
        return {
            "success": True,
            "account_id": str(account.id),
            "webhook_url": f"/api/v1/webhooks/elementor/{account.id}"
        }
        
    except Exception as e:
        logger.error(f"Installation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Installation failed")
```

### Step 7: Performance Analytics Engine
```python
# File: api/services/performance_calculator.py
from typing import Dict, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from database.models import Vendor, Lead, PerformanceMetric, Feedback

class PerformanceCalculator:
    def __init__(self, db: Session):
        self.db = db
    
    async def calculate_vendor_performance(self, vendor_id: str) -> Dict:
        """Calculate comprehensive vendor performance metrics"""
        vendor = self.db.query(Vendor).filter(Vendor.id == vendor_id).first()
        if not vendor:
            return {}
        
        # Get performance data for last 90 days
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        
        # Response time metrics
        response_metrics = self._calculate_response_metrics(vendor_id, cutoff_date)
        
        # Conversion metrics
        conversion_metrics = self._calculate_conversion_metrics(vendor_id, cutoff_date)
        
        # Customer satisfaction metrics
        satisfaction_metrics = self._calculate_satisfaction_metrics(vendor_id, cutoff_date)
        
        # Overall performance score (weighted average)
        performance_score = self._calculate_composite_score(
            response_metrics, conversion_metrics, satisfaction_metrics
        )
        
        # Update vendor record
        vendor.performance_score = performance_score
        vendor.avg_response_time_hours = response_metrics.get('avg_response_hours', 24.0)
        vendor.customer_rating = satisfaction_metrics.get('avg_rating', 5.0)
        
        self.db.commit()
        
        return {
            "vendor_id": vendor_id,
            "performance_score": performance_score,
            "response_metrics": response_metrics,
            "conversion_metrics": conversion_metrics,
            "satisfaction_metrics": satisfaction_metrics,
            "calculation_date": datetime.utcnow().isoformat()
        }
    
    def _calculate_response_metrics(self, vendor_id: str, cutoff_date: datetime) -> Dict:
        """Calculate response time metrics"""
        leads = self.db.query(Lead).filter(
            Lead.vendor_id == vendor_id,
            Lead.assigned_at >= cutoff_date,
            Lead.first_response_at.isnot(None)
        ).all()
        
        if not leads:
            return {"avg_response_hours": 24.0, "response_rate": 0.0, "total_leads": 0}
        
        # Calculate response times
        response_times = []
        for lead in leads:
            if lead.first_response_at and lead.assigned_at:
                response_time = (lead.first_response_at - lead.assigned_at).total_seconds() / 3600
                response_times.append(response_time)
        
        # Total leads assigned (including non-responsive)
        total_assigned = self.db.query(Lead).filter(
            Lead.vendor_id == vendor_id,
            Lead.assigned_at >= cutoff_date
        ).count()
        
        return {
            "avg_response_hours": sum(response_times) / len(response_times) if response_times else 24.0,
            "median_response_hours": sorted(response_times)[len(response_times)//2] if response_times else 24.0,
            "response_rate": len(response_times) / total_assigned if total_assigned > 0 else 0.0,
            "total_leads": total_assigned,
            "responded_leads": len(response_times)
        }
    
    def _calculate_conversion_metrics(self, vendor_id: str, cutoff_date: datetime) -> Dict:
        """Calculate conversion rate metrics"""
        total_leads = self.db.query(Lead).filter(
            Lead.vendor_id == vendor_id,
            Lead.assigned_at >= cutoff_date
        ).count()
        
        won_leads = self.db.query(Lead).filter(
            Lead.vendor_id == vendor_id,
            Lead.assigned_at >= cutoff_date,
            Lead.outcome == "won"
        ).count()
        
        lost_leads = self.db.query(Lead).filter(
            Lead.vendor_id == vendor_id,
            Lead.assigned_at >= cutoff_date,
            Lead.outcome == "lost"
        ).count()
        
        # Revenue metrics (if available)
        total_revenue = self.db.query(func.sum(Lead.estimated_value)).filter(
            Lead.vendor_id == vendor_id,
            Lead.assigned_at >= cutoff_date,
            Lead.outcome == "won"
        ).scalar() or 0
        
        conversion_rate = won_leads / total_leads if total_leads > 0 else 0.0
        
        return {
            "total_leads": total_leads,
            "won_leads": won_leads,
            "lost_leads": lost_leads,
            "conversion_rate": conversion_rate,
            "total_revenue": float(total_revenue),
            "avg_deal_size": float(total_revenue / won_leads) if won_leads > 0 else 0.0
        }
    
    def _calculate_satisfaction_metrics(self, vendor_id: str, cutoff_date: datetime) -> Dict:
        """Calculate customer satisfaction metrics"""
        feedback_records = self.db.query(Feedback).filter(
            Feedback.vendor_id == vendor_id,
            Feedback.submitted_at >= cutoff_date,
            Feedback.rating.isnot(None)
        ).all()
        
        if not feedback_records:
            return {"avg_rating": 5.0, "total_reviews": 0, "rating_distribution": {}}
        
        ratings = [f.rating for f in feedback_records]
        avg_rating = sum(ratings) / len(ratings)
        
        # Rating distribution
        rating_dist = {i: ratings.count(i) for i in range(1, 6)}
        
        return {
            "avg_rating": avg_rating,
            "total_reviews": len(ratings),
            "rating_distribution": rating_dist,
            "latest_feedback": feedback_records[-1].comments if feedback_records else None
        }
    
    def _calculate_composite_score(self, response_metrics: Dict, conversion_metrics: Dict, satisfaction_metrics: Dict) -> float:
        """Calculate weighted composite performance score (0.0 - 1.0)"""
        # Response score (faster is better, max 24 hours)
        avg_response = response_metrics.get('avg_response_hours', 24.0)
        response_score = max(0, (24 - min(avg_response, 24)) / 24)
        
        # Conversion score
        conversion_score = conversion_metrics.get('conversion_rate', 0.0)
        
        # Satisfaction score (rating out of 5)
        satisfaction_score = (satisfaction_metrics.get('avg_rating', 5.0) - 1) / 4
        
        # Weighted average: Response 30%, Conversion 40%, Satisfaction 30%
        composite_score = (response_score * 0.3) + (conversion_score * 0.4) + (satisfaction_score * 0.3)
        
        return min(1.0, max(0.0, composite_score))

# File: api/services/analytics_engine.py
from typing import Dict, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from database.models import Account, Vendor, Lead, PerformanceMetric

class AnalyticsEngine:
    def __init__(self, db: Session):
        self.db = db
    
    async def get_account_dashboard(self, account_id: str, days: int = 30) -> Dict:
        """Generate comprehensive account dashboard data"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Lead volume metrics
        lead_volume = await self._get_lead_volume_metrics(account_id, cutoff_date)
        
        # Vendor performance summary
        vendor_performance = await self._get_vendor_performance_summary(account_id, cutoff_date)
        
        # Routing efficiency metrics
        routing_efficiency = await self._get_routing_efficiency(account_id, cutoff_date)
        
        # Revenue metrics
        revenue_metrics = await self._get_revenue_metrics(account_id, cutoff_date)
        
        # Service category breakdown
        service_breakdown = await self._get_service_category_breakdown(account_id, cutoff_date)
        
        return {
            "account_id": account_id,
            "reporting_period": f"Last {days} days",
            "lead_volume": lead_volume,
            "vendor_performance": vendor_performance,
            "routing_efficiency": routing_efficiency,
            "revenue_metrics": revenue_metrics,
            "service_breakdown": service_breakdown,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    async def _get_lead_volume_metrics(self, account_id: str, cutoff_date: datetime) -> Dict:
        """Calculate lead volume and trend metrics"""
        # Total leads in period
        total_leads = self.db.query(Lead).filter(
            Lead.account_id == account_id,
            Lead.created_at >= cutoff_date
        ).count()
        
        # Daily lead volume for trend analysis
        daily_leads = self.db.query(
            func.date(Lead.created_at).label('date'),
            func.count(Lead.id).label('count')
        ).filter(
            Lead.account_id == account_id,
            Lead.created_at >= cutoff_date
        ).group_by(func.date(Lead.created_at)).all()
        
        # Lead status breakdown
        status_breakdown = self.db.query(
            Lead.status,
            func.count(Lead.id).label('count')
        ).filter(
            Lead.account_id == account_id,
            Lead.created_at >= cutoff_date
        ).group_by(Lead.status).all()
        
        return {
            "total_leads": total_leads,
            "daily_trend": [{"date": str(d.date), "count": d.count} for d in daily_leads],
            "status_breakdown": {s.status: s.count for s in status_breakdown}
        }
    
    async def _get_vendor_performance_summary(self, account_id: str, cutoff_date: datetime) -> Dict:
        """Get vendor performance summary"""
        vendors = self.db.query(Vendor).filter(
            Vendor.account_id == account_id,
            Vendor.status == "active"
        ).all()
        
        vendor_stats = []
        for vendor in vendors:
            lead_count = self.db.query(Lead).filter(
                Lead.vendor_id == vendor.id,
                Lead.assigned_at >= cutoff_date
            ).count()
            
            vendor_stats.append({
                "vendor_id": str(vendor.id),
                "name": vendor.company_name,
                "performance_score": vendor.performance_score,
                "leads_assigned": lead_count,
                "avg_response_time": vendor.avg_response_time_hours,
                "customer_rating": vendor.customer_rating
            })
        
        # Sort by performance score
        vendor_stats.sort(key=lambda x: x["performance_score"], reverse=True)
        
        return {
            "total_vendors": len(vendors),
            "active_vendors": len([v for v in vendors if v.taking_new_work]),
            "avg_performance_score": sum(v.performance_score for v in vendors) / len(vendors) if vendors else 0,
            "vendor_rankings": vendor_stats[:10]  # Top 10
        }

# File: api/routes/analytics.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from ..services.analytics_engine import AnalyticsEngine
from ..services.performance_calculator import PerformanceCalculator
from database.connection import get_db
from database.models import Account

router = APIRouter()

@router.get("/dashboard/{account_id}")
async def get_dashboard(
    account_id: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get comprehensive dashboard analytics for account"""
    # Validate account
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    analytics_engine = AnalyticsEngine(db)
    dashboard_data = await analytics_engine.get_account_dashboard(account_id, days)
    
    return dashboard_data

@router.get("/vendors/{account_id}/performance")
async def get_vendor_performance(
    account_id: str,
    db: Session = Depends(get_db)
):
    """Get detailed vendor performance metrics"""
    performance_calc = PerformanceCalculator(db)
    
    # Get all vendors for account
    vendors = db.query(Vendor).filter(Vendor.account_id == account_id).all()
    
    vendor_performances = []
    for vendor in vendors:
        performance = await performance_calc.calculate_vendor_performance(str(vendor.id))
        vendor_performances.append(performance)
    
    return {"vendors": vendor_performances}

@router.post("/vendors/{vendor_id}/recalculate")
async def recalculate_vendor_performance(
    vendor_id: str,
    db: Session = Depends(get_db)
):
    """Manually trigger vendor performance recalculation"""
    performance_calc = PerformanceCalculator(db)
    result = await performance_calc.calculate_vendor_performance(vendor_id)
    
    return {"success": True, "performance": result}
```

### Step 8: Docker Configuration for Local Development and Production
```dockerfile
# File: Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# File: docker-compose.yml
version: '3.8'

services:
  # Main API application
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/smartleadrouter
      - REDIS_URL=redis://redis:6379
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    depends_on:
      - db
      - redis
    volumes:
      - .:/app
    command: ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

  # PostgreSQL database
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=smartleadrouter
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql

  # Redis for caching and sessions
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # Celery worker for background tasks
  worker:
    build: .
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/smartleadrouter
      - REDIS_URL=redis://redis:6379
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    depends_on:
      - db
      - redis
    command: ["celery", "-A", "api.tasks", "worker", "--loglevel=info"]

  # React dashboard (optional)
  dashboard:
    build: ./dashboard
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
    volumes:
      - ./dashboard:/app
      - /app/node_modules

volumes:
  postgres_data:
  redis_data:

# File: requirements.txt
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.7
alembic==1.12.1
pydantic==2.5.0
python-multipart==0.0.6
python-dotenv==1.0.0
redis==5.0.1
celery==5.3.4
anthropic==0.7.8
openai==1.3.5
stripe==7.8.0
sentry-sdk==1.38.0
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2
Jinja2==3.1.2
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
```

### Step 9: Testing Framework
```python
# File: tests/test_lead_router.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid

from main import app
from database.models import Base, Account, Vendor, Lead
from database.connection import get_db

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture
def test_account():
    db = TestingSessionLocal()
    account = Account(
        ghl_location_id="test_location_123",
        company_name="Test Marine Services",
        industry="marine",
        ghl_api_token="test_token"
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    db.close()
    return account

@pytest.fixture
def test_vendor(test_account):
    db = TestingSessionLocal()
    vendor = Vendor(
        account_id=test_account.id,
        ghl_contact_id="test_vendor_123",
        name="Test Vendor",
        company_name="Test Marine Repair",
        services_provided=["Boat Maintenance", "Engine Repair"],
        service_areas=["33101", "33102"],
        taking_new_work=True
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    db.close()
    return vendor

class TestLeadRouting:
    def test_webhook_endpoint_creates_lead(self, test_client, test_account, test_vendor, setup_database):
        """Test that webhook endpoint creates lead successfully"""
        webhook_data = {
            "name": "John Smith",
            "email": "john@example.com",
            "phone": "+1234567890",
            "service_requested": "boat detailing",
            "zip_code": "33101",
            "special_requests": "Need full detail"
        }
        
        response = test_client.post(
            f"/api/v1/webhooks/elementor/{test_account.id}",
            json=webhook_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "lead_id" in data
        assert data["service_category"] == "Boat Maintenance"
        assert data["assigned_vendor"] == "Test Marine Repair"
    
    def test_vendor_matching_logic(self, test_client, test_account, test_vendor, setup_database):
        """Test vendor matching logic"""
        # Test with matching service and location
        webhook_data = {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "service_requested": "engine repair",
            "zip_code": "33102"
        }
        
        response = test_client.post(
            f"/api/v1/webhooks/elementor/{test_account.id}",
            json=webhook_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["assigned_vendor"] == "Test Marine Repair"
    
    def test_no_matching_vendor(self, test_client, test_account, setup_database):
        """Test behavior when no vendor matches"""
        webhook_data = {
            "name": "Bob Wilson",
            "email": "bob@example.com",
            "service_requested": "aircraft repair",  # No vendor for this
            "zip_code": "90210"  # Wrong location
        }
        
        response = test_client.post(
            f"/api/v1/webhooks/elementor/{test_account.id}",
            json=webhook_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["assigned_vendor"] is None
    
    def test_analytics_endpoint(self, test_client, test_account, setup_database):
        """Test analytics dashboard endpoint"""
        response = test_client.get(f"/api/v1/analytics/dashboard/{test_account.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "lead_volume" in data
        assert "vendor_performance" in data
        assert "routing_efficiency" in data

# File: tests/test_ai_classifier.py
import pytest
from unittest.mock import AsyncMock, patch
from api.services.ai_classifier import AIServiceClassifier

class TestAIClassifier:
    @pytest.mark.asyncio
    async def test_marine_service_classification(self):
        """Test AI classification for marine services"""
        classifier = AIServiceClassifier("marine")
        
        form_data = {
            "service_requested": "boat detailing and waxing",
            "special_requests": "Full detail with ceramic coating"
        }
        
        with patch.object(classifier.anthropic_client.messages, 'create') as mock_create:
            mock_response = AsyncMock()
            mock_response.content = [AsyncMock()]
            mock_response.content[0].text = '{"category": "Boat Maintenance", "confidence": 0.95, "reasoning": "Clear detailing service request"}'
            mock_create.return_value = mock_response
            
            result = await classifier.classify_service(form_data)
            
            assert result["category"] == "Boat Maintenance"
            assert result["confidence"] == 0.95
    
    @pytest.mark.asyncio
    async def test_fallback_classification(self):
        """Test fallback classification when AI fails"""
        classifier = AIServiceClassifier("marine")
        
        form_data = {"service_requested": "engine repair"}
        
        with patch.object(classifier.anthropic_client.messages, 'create', side_effect=Exception("API Error")):
            result = await classifier.classify_service(form_data)
            
            assert result["category"] == "Engines and Generators"
            assert result["confidence"] == 0.7

# File: run_tests.py
import subprocess
import sys

def run_tests():
    """Run all tests and generate coverage report"""
    commands = [
        ["pytest", "tests/", "-v", "--cov=api", "--cov-report=html", "--cov-report=term"],
        ["pytest", "tests/", "--cov=api", "--cov-fail-under=80"]
    ]
    
    for cmd in commands:
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        if result.returncode != 0:
            sys.exit(result.returncode)

if __name__ == "__main__":
    run_tests()
```

### Step 10: Production Deployment Scripts
```bash
# File: scripts/deploy.sh
#!/bin/bash

set -e

echo "🚀 Smart Lead Router Pro - Production Deployment"
echo "================================================"

# Configuration
PROJECT_NAME="smart-lead-router-pro"
DOMAIN="${DOMAIN:-your-domain.com}"
ENVIRONMENT="${ENVIRONMENT:-production}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Install Docker and Docker Compose
echo "📦 Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl enable docker
systemctl start docker

# Install Docker Compose
echo "📦 Installing Docker Compose..."
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create application directory
APP_DIR="/opt/$PROJECT_NAME"
echo "📁 Creating application directory: $APP_DIR"
mkdir -p $APP_DIR
cd $APP_DIR

# Create production environment file
echo "⚙️ Setting up environment configuration..."
cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql://smartrouter:$(openssl rand -base64 32)@db:5432/smartleadrouter
REDIS_URL=redis://redis:6379

# API Keys (MUST BE SET)
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key
STRIPE_SECRET_KEY=your_stripe_secret_key

# Security
SECRET_KEY=$(openssl rand -base64 32)
ALLOWED_HOSTS=$DOMAIN,localhost

# Monitoring
SENTRY_DSN=your_sentry_dsn

# Environment
ENVIRONMENT=production
DEBUG=false
EOF

# Create production docker-compose.yml
echo "🐳 Creating production Docker configuration..."
cat > docker-compose.prod.yml << EOF
version: '3.8'

services:
  api:
    image: smartleadrouter/api:latest
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=\${DATABASE_URL}
      - REDIS_URL=\${REDIS_URL}
      - ANTHROPIC_API_KEY=\${ANTHROPIC_API_KEY}
      - SECRET_KEY=\${SECRET_KEY}
      - ENVIRONMENT=production
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs

  db:
    image: postgres:15
    restart: unless-stopped
    environment:
      - POSTGRES_DB=smartleadrouter
      - POSTGRES_USER=smartrouter
      - POSTGRES_PASSWORD=\${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    ports:
      - "127.0.0.1:5432:5432"

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  worker:
    image: smartleadrouter/api:latest
    restart: unless-stopped
    environment:
      - DATABASE_URL=\${DATABASE_URL}
      - REDIS_URL=\${REDIS_URL}
      - ANTHROPIC_API_KEY=\${ANTHROPIC_API_KEY}
    depends_on:
      - db
      - redis
    command: ["celery", "-A", "api.tasks", "worker", "--loglevel=info"]

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
      - ./logs:/var/log/nginx
    depends_on:
      - api

volumes:
  postgres_data:
  redis_data:
EOF

# Create Nginx configuration
echo "🌐 Setting up Nginx configuration..."
cat > nginx.conf << EOF
events {
    worker_connections 1024;
}

http {
    upstream api {
        server api:8000;
    }

    server {
        listen 80;
        server_name $DOMAIN;
        return 301 https://\$server_name\$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name $DOMAIN;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        location / {
            proxy_pass http://api;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        location /health {
            proxy_pass http://api/health;
            access_log off;
        }
    }
}
EOF

# Create SSL directory
mkdir -p ssl logs backups

# Install Certbot for SSL
echo "🔒 Installing Certbot for SSL certificates..."
apt install -y certbot python3-certbot-nginx

# Generate SSL certificate
echo "🔒 Generating SSL certificate..."
certbot certonly --standalone -d $DOMAIN --email admin@$DOMAIN --agree-tos --non-interactive

# Copy certificates
cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem ssl/cert.pem
cp /etc/letsencrypt/live/$DOMAIN/privkey.pem ssl/key.pem

# Set up automatic certificate renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -

# Create systemd service for auto-startup
echo "⚙️ Creating systemd service..."
cat > /etc/systemd/system/smart-lead-router.service << EOF
[Unit]
Description=Smart Lead Router Pro
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$APP_DIR
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
systemctl daemon-reload
systemctl enable smart-lead-router

echo "✅ Deployment completed!"
echo ""
echo "📋 Next steps:"
echo "1. Edit $APP_DIR/.env with your actual API keys"
echo "2. Update domain name in nginx.conf if needed"
echo "3. Start the service: systemctl start smart-lead-router"
echo "4. Check status: systemctl status smart-lead-router"
echo ""
echo "🌐 Your API will be available at: https://$DOMAIN"
echo "📊 Health check: https://$DOMAIN/health"

# File: scripts/local-dev.sh
#!/bin/bash

echo "🧪 Smart Lead Router Pro - Local Development Setup"
echo "================================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📋 Creating .env file from template..."
    cp .env.example .env
    echo "✏️ Please edit .env file with your actual configuration"
fi

# Start development environment
echo "🚀 Starting development environment..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Run database migrations
echo "🗄️ Running database migrations..."
docker-compose exec api alembic upgrade head

# Run tests
echo "🧪 Running tests..."
docker-compose exec api python -m pytest tests/ -v

echo "✅ Development environment is ready!"
echo ""
echo "🌐 API Server: http://localhost:8000"
echo "📊 Health Check: http://localhost:8000/health"
echo "📖 API Docs: http://localhost:8000/docs"
echo "🗄️ Database: localhost:5432"
echo "🔴 Redis: localhost:6379"
echo ""
echo "🔧 Useful commands:"
echo "  docker-compose logs api     # View API logs"
echo "  docker-compose exec api bash   # Access API container"
echo "  docker-compose down         # Stop all services"
```

### Step 11: Final Implementation Commands

```bash
# Execute these commands step by step to build the complete system

# 1. Initialize project
mkdir smart-lead-router-pro && cd smart-lead-router-pro

# 2. Create all directories and files as specified above

# 3. Set up local development
chmod +x scripts/local-dev.sh
./scripts/local-dev.sh

# 4. Test the system
python run_tests.py

# 5. Deploy to production
chmod +x scripts/deploy.sh
sudo DOMAIN=your-domain.com ./scripts/deploy.sh

# 6. Configure GHL marketplace app
# Follow GHL marketplace guidelines to package and submit
```

This comprehensive development prompt provides step-by-step instructions to build a production-ready, multi-tenant lead routing SaaS application that can be deployed locally for testing and scaled for the GoHighLevel marketplace.