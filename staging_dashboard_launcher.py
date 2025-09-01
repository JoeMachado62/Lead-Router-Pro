#!/usr/bin/env python3
"""
Simple launcher for the Staging Dashboard
Run this to test the Dynamic Forms Management System
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn
import os

app = FastAPI(title="Dynamic Forms Staging Dashboard")

@app.get("/")
async def serve_dashboard():
    """Serve the staging dashboard HTML"""
    
    # Read the dashboard HTML file
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
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(
            content="""
            <h1>Dashboard Not Found</h1>
            <p>Could not find dashboard at: {}</p>
            <p>Current directory: {}</p>
            """.format(dashboard_path, os.getcwd())
        )
    except Exception as e:
        return HTMLResponse(
            content=f"""
            <h1>Error Loading Dashboard</h1>
            <p>Error: {str(e)}</p>
            """
        )

# Also include the staging API routes
try:
    from staging.dynamic_forms.api.staging_routes import router as staging_router
    app.include_router(staging_router)
    print("✅ Staging API routes loaded successfully")
except Exception as e:
    print(f"⚠️ Could not load staging API routes: {e}")
    print("   The dashboard will load but API calls won't work")

if __name__ == "__main__":
    print("="*60)
    print("DYNAMIC FORMS STAGING DASHBOARD")
    print("="*60)
    print("\nStarting dashboard server...")
    print("\n✅ Dashboard available at: http://localhost:8003/")
    print("📡 API documentation at: http://localhost:8003/docs")
    print("\nPress Ctrl+C to stop\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8003)