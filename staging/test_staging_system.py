#!/usr/bin/env python3
"""
Test script for the Dynamic Forms & Service Management staging system
Demonstrates adding new categories, forms, and handling vendor applications
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
import uvicorn

# Import staging routes
from staging.dynamic_forms.api.staging_routes import router as staging_router

# Create FastAPI app for staging
app = FastAPI(
    title="Dynamic Forms Staging System",
    description="Test environment for dynamic form and service management",
    version="1.0.0"
)

# Include staging routes
app.include_router(staging_router)

# Serve the dashboard with proper path resolution
@app.get("/staging-dashboard")
async def serve_dashboard():
    dashboard_path = os.path.join(os.path.dirname(__file__), "dynamic_forms", "ui", "dashboard.html")
    
    # Check if file exists and read it
    if os.path.exists(dashboard_path):
        with open(dashboard_path, 'r') as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    else:
        return HTMLResponse(content=f"<h1>Error: Dashboard not found at {dashboard_path}</h1>")

# Health check
@app.get("/staging/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": "staging",
        "message": "Dynamic Forms staging system is running"
    }

# Example endpoint to demonstrate how it integrates with existing webhook handler
@app.post("/staging/webhook-handler-example/{form_identifier}")
async def example_webhook_handler(form_identifier: str, payload: dict):
    """
    Example of how the production webhook handler would integrate
    with the dynamic form system
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from staging.dynamic_forms.services.form_manager import FormManager
    
    # Get staging database
    engine = create_engine("sqlite:///staging_dynamic_forms.db")
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Use FormManager to get configuration
        manager = FormManager(db)
        config = manager.get_form_configuration(form_identifier)
        
        if not config:
            # Handle unregistered form
            unregistered = manager.handle_unregistered_form(form_identifier, payload)
            return {
                "status": "unregistered",
                "message": "Form not registered - added to auto-discovery",
                "unregistered_id": unregistered.id,
                "suggested_type": unregistered.suggested_form_type
            }
        
        # Process with configuration
        return {
            "status": "success",
            "message": "Form would be processed with configuration",
            "form_type": config["form_type"],
            "category": config["service_category"],
            "priority": config["priority"],
            "auto_route": config["auto_route_to_vendor"]
        }
    finally:
        db.close()

def create_sample_data():
    """Create sample data for testing"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from staging.dynamic_forms.services.category_manager import ServiceCategoryManager
    from staging.dynamic_forms.services.form_manager import FormManager
    
    print("Creating sample data for staging system...")
    
    # Setup database
    engine = create_engine("sqlite:///staging_dynamic_forms.db")
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Create service category manager
        cat_manager = ServiceCategoryManager(db)
        
        # Example 1: Add "Waterfront Vacation Rentals" category
        print("\n1. Creating 'Waterfront Vacation Rentals' category...")
        vacation_config = {
            "category": {
                "name": "Waterfront Vacation Rentals",
                "display_name": "Waterfront Vacation Rentals",
                "description": "Luxury waterfront properties for short-term rental"
            },
            "subcategories": [
                {
                    "name": "Daily",
                    "display_name": "Daily Rentals",
                    "level3_services": [
                        {"name": "With a Pool", "is_premium": True},
                        {"name": "With a Jacuzzi", "is_premium": True},
                        {"name": "With a Dock", "is_default": True},
                        {"name": "With a Boat"},
                        {"name": "With Provisions"}
                    ]
                },
                {
                    "name": "Weekly",
                    "display_name": "Weekly Rentals",
                    "level3_services": [
                        {"name": "With a Pool", "is_premium": True},
                        {"name": "With a Jacuzzi", "is_premium": True},
                        {"name": "With a Dock", "is_default": True},
                        {"name": "Pet Friendly"},
                        {"name": "With Chef Service", "is_premium": True}
                    ]
                },
                {
                    "name": "Monthly",
                    "display_name": "Monthly Rentals",
                    "level3_services": [
                        {"name": "Furnished", "is_default": True},
                        {"name": "Unfurnished"},
                        {"name": "With Utilities Included"},
                        {"name": "With Housekeeping", "is_premium": True}
                    ]
                },
                {
                    "name": "Seasonal",
                    "display_name": "Seasonal Rentals",
                    "level3_services": [
                        {"name": "Winter Season"},
                        {"name": "Summer Season"},
                        {"name": "Full Year", "is_premium": True}
                    ]
                }
            ]
        }
        
        result = cat_manager.create_complete_hierarchy(vacation_config)
        if result.get("errors"):
            print(f"  Errors: {result['errors']}")
        else:
            print(f"  ✅ Created with {len(result['subcategories'])} subcategories and {len(result['level3_services'])} Level 3 services")
        
        # Example 2: Add "Marine Electronics" category
        print("\n2. Creating 'Marine Electronics' category...")
        electronics_config = {
            "category": {
                "name": "Marine Electronics",
                "display_name": "Marine Electronics & Navigation",
                "description": "Electronic systems and navigation equipment for boats"
            },
            "subcategories": [
                {
                    "name": "Navigation Systems",
                    "display_name": "Navigation & GPS",
                    "level3_services": [
                        {"name": "GPS Installation", "is_default": True},
                        {"name": "Chartplotter Setup"},
                        {"name": "Radar Installation", "is_premium": True},
                        {"name": "AIS System Setup"},
                        {"name": "Autopilot Installation", "is_premium": True}
                    ]
                },
                {
                    "name": "Communication Systems",
                    "display_name": "Marine Communication",
                    "level3_services": [
                        {"name": "VHF Radio Installation"},
                        {"name": "SSB Radio Setup", "is_premium": True},
                        {"name": "Satellite Phone Installation", "is_premium": True},
                        {"name": "WiFi/Internet Setup"}
                    ]
                },
                {
                    "name": "Entertainment Systems",
                    "display_name": "Marine Entertainment",
                    "level3_services": [
                        {"name": "Marine Audio Installation"},
                        {"name": "TV/Satellite TV Setup"},
                        {"name": "Underwater Lighting", "is_premium": True}
                    ]
                }
            ]
        }
        
        result = cat_manager.create_complete_hierarchy(electronics_config)
        if not result.get("errors"):
            print(f"  ✅ Created with {len(result['subcategories'])} subcategories")
        
        # Create form manager
        form_manager = FormManager(db)
        
        # Register forms for the new categories
        print("\n3. Registering forms for new categories...")
        
        # Vacation rental inquiry form
        rental_form = {
            "form_identifier": "luxury-rental-inquiry",
            "form_name": "Luxury Waterfront Rental Inquiry",
            "form_type": "client_lead",
            "category_name": "Waterfront Vacation Rentals",
            "required_fields": ["firstName", "lastName", "email", "phone", "check_in_date", "check_out_date"],
            "optional_fields": ["number_of_guests", "special_requests", "pet_info"],
            "priority": "high",
            "auto_route_to_vendor": True
        }
        form_manager.register_form(rental_form)
        print("  ✅ Registered 'luxury-rental-inquiry' form")
        
        # Vendor application for rental properties
        vendor_form = {
            "form_identifier": "rental-property-vendor",
            "form_name": "Rental Property Owner Application",
            "form_type": "vendor_application",
            "category_name": "Waterfront Vacation Rentals",
            "required_fields": ["firstName", "lastName", "email", "phone", "property_address", "property_type"],
            "optional_fields": ["property_photos", "amenities", "availability_calendar"],
            "requires_approval": True
        }
        form_manager.register_form(vendor_form)
        print("  ✅ Registered 'rental-property-vendor' form")
        
        # Electronics service request
        electronics_form = {
            "form_identifier": "marine-electronics-service",
            "form_name": "Marine Electronics Service Request",
            "form_type": "client_lead",
            "category_name": "Marine Electronics",
            "required_fields": ["firstName", "lastName", "email", "phone", "boat_make", "boat_model"],
            "optional_fields": ["service_needed", "preferred_date", "marina_location"],
            "priority": "normal",
            "auto_route_to_vendor": True
        }
        form_manager.register_form(electronics_form)
        print("  ✅ Registered 'marine-electronics-service' form")
        
        print("\n✅ Sample data creation complete!")
        print("\nYou can now:")
        print("1. Access the dashboard at: http://localhost:8003/staging-dashboard")
        print("2. Test the API at: http://localhost:8003/docs")
        print("3. View categories at: http://localhost:8003/api/staging/dynamic-forms/categories")
        
    except Exception as e:
        print(f"Error creating sample data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("="*60)
    print("DYNAMIC FORMS STAGING SYSTEM")
    print("="*60)
    print("\nThis is a STAGING environment for testing the dynamic form system.")
    print("Changes here do NOT affect your production system.\n")
    
    # Create sample data
    create_sample_data()
    
    print("\n" + "="*60)
    print("Starting staging server on http://localhost:8003")
    print("="*60)
    print("\nEndpoints available:")
    print("  Dashboard: http://localhost:8003/staging-dashboard")
    print("  API Docs: http://localhost:8003/docs")
    print("  Health: http://localhost:8003/staging/health")
    print("\nPress Ctrl+C to stop the server\n")
    
    # Run the staging server on port 8003 (avoiding conflicts with 8001 and 3001)
    uvicorn.run(app, host="0.0.0.0", port=8003)