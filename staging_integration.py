"""
Integration file to add staging dashboard to the main application
This allows accessing the staging dashboard through your existing domain
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
import os

# Create a router for staging features
staging_router = APIRouter(prefix="/staging", tags=["Staging"])

@staging_router.get("/dashboard")
async def serve_staging_dashboard():
    """Serve the staging dashboard through the main application"""
    
    dashboard_path = os.path.join(
        os.path.dirname(__file__), 
        "staging", 
        "dynamic_forms", 
        "ui", 
        "dashboard.html"
    )
    
    try:
        with open(dashboard_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Update API endpoints to use relative paths
        html_content = html_content.replace(
            "const API_BASE = '/api/staging/dynamic-forms';",
            "const API_BASE = '/staging/api/dynamic-forms';"
        )
        
        return HTMLResponse(content=html_content)
    except Exception as e:
        return HTMLResponse(
            content=f"""
            <h1>Staging Dashboard Error</h1>
            <p>Could not load dashboard: {str(e)}</p>
            <p>Path tried: {dashboard_path}</p>
            """
        )

# Try to import staging API routes
try:
    from staging.dynamic_forms.api.staging_routes import router as staging_api_router
    # Mount the API routes under /staging/api
    staging_router.include_router(
        staging_api_router, 
        prefix="/api",
        tags=["Staging API"]
    )
except Exception as e:
    print(f"Warning: Could not load staging API routes: {e}")

# Instructions for integration
"""
To add the staging dashboard to your main application (main_working_final.py):

1. Add this import at the top:
   from staging_integration import staging_router

2. Add this line after creating the FastAPI app:
   app.include_router(staging_router)

3. Access the staging dashboard at:
   https://dockside.life/staging/dashboard

This way you can access it through your existing domain!
"""