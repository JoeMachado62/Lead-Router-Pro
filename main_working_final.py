# main_working_final.py (Revised to be more comprehensive)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import uvicorn
import logging
import json # For loading field_reference if needed here, though better in relevant modules

# --- Router Imports ---
from api.routes.webhook_routes import router as dsp_elementor_webhook_router
from api.routes.simple_admin import router as simple_admin_router # Assuming you want admin CRUD API

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Smart Lead Router Pro (Main App)...")
    try:
        # Ensure simple_db_instance is initialized when simple_connection is imported
        from database.simple_connection import db as simple_db_instance
        stats = simple_db_instance.get_stats() 
        logger.info(f"✅ Database connected on startup. Stats: {stats}")
    except ImportError:
        logger.error("❌ Failed to import database instance. simple_connection.py might have an issue or not be found.")
    except Exception as e:
        logger.error(f"❌ Database connection/initialization error on startup: {e}")
    
    logger.info("✅ Smart Lead Router Pro system ready.")
    yield
    logger.info("Shutting down Smart Lead Router Pro...")

app = FastAPI(
    title="Smart Lead Router Pro - Main Application",
    description="AI-powered lead routing for DSP, integrating Elementor webhooks and admin functionalities.",
    version="1.1.0", # Version update
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include Routers from other modules ---
app.include_router(dsp_elementor_webhook_router) 
app.include_router(simple_admin_router) # Handles /api/v1/simple-admin/* routes

# Admin Interface HTML (This is likely the large part from your original file)
# If this ADMIN_HTML was very extensive, it's exactly what would make your original file long.
ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Smart Lead Router Pro - DSP Admin Dashboard</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; background: #f5f7fa; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 12px; text-align: center; margin-bottom: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        .status { background: #d4edda; color: #155724; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #28a745; }
        .section { background: white; padding: 25px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
        .section h3 { margin-top: 0; color: #2c3e50; border-bottom: 2px solid #ecf0f1; padding-bottom: 10px; }
        .btn { background: #3498db; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; margin: 8px; transition: all 0.3s; }
        .btn:hover { background: #2980b9; transform: translateY(-2px); }
        .feature-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }
        .feature-card { background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #3498db; }
        .code { background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 6px; font-family: 'Courier New', monospace; font-size: 14px; overflow-x: auto; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Smart Lead Router Pro (DSP Edition)</h1>
        <p>AI-Powered Lead Routing Platform</p>
        <p><strong>Version """ + app.version + """</strong> | Status: <span style="color: #2ecc71;">OPERATIONAL</span></p>
    </div>
    
    <div class="status">
        ✅ <strong>System Status: FULLY OPERATIONAL</strong><br>
        Server running successfully. Elementor webhooks for DSP are active via <code>/api/v1/webhooks/elementor/{form_identifier}</code>.
    </div>
    
    <div class="section">
        <h3>🏢 System Information</h3>
        <div class="feature-grid">
            <div class="feature-card"><h4>🗄️ Database</h4><p>SQLite (Local)<br><small>Using simple_connection.py</small></p></div>
            <div class="feature-card"><h4>⚡ Server</h4><p>FastAPI + Uvicorn<br><small>High-performance async</small></p></div>
            <div class="feature-card"><h4>📊 Admin API</h4><p>Available at <code>/api/v1/simple-admin/</code></p></div>
            <div class="feature-card"><h4>🤖 AI Ready</h4><p>Rule-based active. LLM capable.</p></div>
        </div>
    </div>

    <div class="section">
        <h3>🔗 Quick Links & Documentation</h3>
        <div style="margin: 20px 0;">
            <a href="/docs" class="btn" target="_blank">📖 Interactive API Docs (Swagger)</a>
            <a href="/redoc" class="btn" target="_blank">📕 Alternative API Docs (ReDoc)</a>
            <a href="/health" class="btn" target="_blank">🔍 System Health Check</a>
            <a href="/api/v1/simple-admin/stats" class="btn" target="_blank">📈 Admin API Stats</a>
        </div>
        
    <div class="section">
    <h3>📋 Supported Form Types</h3>
    <div class="feature-grid">
        <div class="feature-card">
            <h4>🛥️ Client Lead Forms</h4>
            <p>Ceramic Coating, Yacht Delivery, Emergency Tow, Engine Repair</p>
        </div>
        <div class="feature-card">
            <h4>🏢 Vendor Applications</h4>
            <p>General, Marine Mechanic, Boat Detailing</p>
        </div>
        <div class="feature-card">
            <h4>📞 General Inquiries</h4>
            <p>Contact forms and information requests</p>
        </div>
    </div>
    <p><strong>Webhook Pattern:</strong> <code>/api/v1/webhooks/elementor/{form_identifier}</code></p>
</div>
        
    </div>
    
    <!-- You can add more sections here from your original ADMIN_HTML if they were extensive -->
    <!-- For example: AI Service Configuration, Testing & Validation details, etc. -->
    
    <div class="section">
        <p><strong>🎉 Congratulations!</strong> Your Smart Lead Router Pro is operational!</p>
    </div>
</body>
</html>
"""

@app.get("/admin-gui", response_class=HTMLResponse, include_in_schema=False) # Renamed for clarity, or use /api/v1/admin/
async def admin_gui_dashboard():
    """Serves the main HTML admin dashboard GUI."""
    # This replaces the old /api/v1/admin/ if that was also serving HTML.
    # The /api/v1/simple-admin/ routes are for JSON API data for the admin panel.
    return HTMLResponse(content=ADMIN_HTML.replace("</p>\n    </div>", f"</p><p><small>FastAPI App Title: {app.title}</small></p>\n    </div>"))


@app.get("/health")
async def health_check():
    db_status = "unknown"
    db_error_msg = "Not checked"
    try:
        from database.simple_connection import db as simple_db_instance
        simple_db_instance.get_stats() 
        db_status = "healthy"
        db_error_msg = "No error"
    except Exception as e:
        db_status = "unhealthy"
        db_error_msg = str(e)
        logger.error(f"Health check DB error: {e}")

    return {
        "status": "healthy", 
        "version": app.version,
        "service_name": app.title,
        "database_status": db_status,
        "database_check_message": db_error_msg,
        "active_routers": {
            "elementor_webhooks_dsp": "✅ Included",
            "simple_admin_api": "✅ Included",
        }
    }

@app.get("/")
async def root_info():
    return {
        "application": app.title,
        "version": app.version,
        "message": "Welcome! The API is operational.",
        "documentation": app.docs_url,
        "admin_gui": "/admin-gui", # Link to the HTML dashboard
        "health_check": "/health"
    }

# No other webhook endpoints should be defined here if they are in imported routers.

if __name__ == "__main__":
    uvicorn.run("main_working_final:app", host="0.0.0.0", port=8000, reload=True)