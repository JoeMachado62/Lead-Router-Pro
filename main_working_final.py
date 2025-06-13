# main.py - Enhanced with Admin Dashboard

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
from pathlib import Path # os was not used, Path is already imported

# Define the base directory for the application (directory of this main.py file)
BASE_DIR = Path(__file__).resolve().parent

# Import your existing routes
from api.routes.webhook_routes import router as webhook_router
from api.routes.admin_routes import router as admin_router
from api.routes.simple_admin import router as simple_admin_router
from api.routes.field_mapping_routes import router as field_mapping_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="DocksidePros Smart Lead Router Pro",
    description="Advanced lead routing system with admin dashboard",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for admin dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(webhook_router)
app.include_router(admin_router)
app.include_router(simple_admin_router)
app.include_router(field_mapping_router)

# Create static and templates directories if they don't exist relative to BASE_DIR
static_dir = BASE_DIR / "static"
static_dir.mkdir(exist_ok=True)
templates_dir = BASE_DIR / "templates"
templates_dir.mkdir(exist_ok=True)

# Serve static files (for admin dashboard assets) from BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

def read_html_file(file_path: Path) -> str: # Changed type hint to Path
    """Read HTML file with error handling"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"HTML file not found: {file_path}")
        return f"<html><body><h1>Error: Template {file_path} not found</h1></body></html>"
    except Exception as e:
        logger.error(f"Error reading HTML file {file_path}: {e}")
        return f"<html><body><h1>Error loading template: {e}</h1></body></html>"

# Main admin dashboard route
@app.get("/admin", response_class=HTMLResponse)
@app.get("/admin/", response_class=HTMLResponse)
async def admin_dashboard():
    """Serve the main admin dashboard"""
    return HTMLResponse(content=read_html_file(BASE_DIR / "lead_router_pro_dashboard.html"))

# Service Categories page
@app.get("/service-categories", response_class=HTMLResponse)
@app.get("/categories", response_class=HTMLResponse)
async def service_categories_page():
    """Serve the service categories page"""
    return HTMLResponse(content=read_html_file(BASE_DIR / "templates" / "service_categories.html"))

# System Health page
@app.get("/system-health", response_class=HTMLResponse)
@app.get("/health-check", response_class=HTMLResponse)
async def system_health_page():
    """Serve the system health page"""
    return HTMLResponse(content=read_html_file(BASE_DIR / "templates" / "system_health.html"))

# Enhanced Form Tester page
@app.get("/form-tester", response_class=HTMLResponse)
@app.get("/test-forms", response_class=HTMLResponse)
async def enhanced_form_tester_page():
    """Serve the enhanced form tester page"""
    return HTMLResponse(content=read_html_file(BASE_DIR / "templates" / "enhanced_form_tester.html"))

# Root endpoint with enhanced navigation
@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with navigation to all dashboard features"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>DocksidePros Smart Lead Router Pro</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.19/tailwind.min.css" rel="stylesheet">
        <style>
            .gradient-bg { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
            .card-hover { transition: all 0.3s ease; }
            .card-hover:hover { transform: translateY(-4px); box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1); }
        </style>
    </head>
    <body class="bg-gray-50 min-h-screen">
        <!-- Header -->
        <header class="gradient-bg text-white shadow-lg">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                <div class="text-center">
                    <div class="flex justify-center items-center space-x-3 mb-4">
                        <div class="bg-white/20 p-3 rounded-lg">
                            <svg class="w-12 h-12" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z"></path>
                            </svg>
                        </div>
                        <div>
                            <h1 class="text-4xl font-bold">🚤 DocksidePros Smart Lead Router Pro</h1>
                            <p class="text-xl text-blue-100 mt-2">Advanced lead routing system for marine services</p>
                        </div>
                    </div>
                </div>
            </div>
        </header>

        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <!-- Main Navigation Cards -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <div class="bg-white rounded-xl shadow-md p-6 card-hover text-center">
                    <div class="bg-blue-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg class="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 00-2-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v4"></path>
                        </svg>
                    </div>
                    <h3 class="text-lg font-semibold text-gray-900 mb-2">🔧 Admin Dashboard</h3>
                    <p class="text-gray-600 text-sm mb-4">Configure system, manage fields, test forms</p>
                    <a href="/admin" class="inline-block bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                        Open Admin Dashboard
                    </a>
                </div>

                <div class="bg-white rounded-xl shadow-md p-6 card-hover text-center">
                    <div class="bg-green-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg class="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                    </div>
                    <h3 class="text-lg font-semibold text-gray-900 mb-2">🔍 System Health</h3>
                    <p class="text-gray-600 text-sm mb-4">Check webhook system status and diagnostics</p>
                    <a href="/system-health" class="inline-block bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors">
                        Health Check
                    </a>
                </div>

                <div class="bg-white rounded-xl shadow-md p-6 card-hover text-center">
                    <div class="bg-purple-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg class="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"></path>
                        </svg>
                    </div>
                    <h3 class="text-lg font-semibold text-gray-900 mb-2">🏷️ Service Categories</h3>
                    <p class="text-gray-600 text-sm mb-4">View all supported service categories</p>
                    <a href="/service-categories" class="inline-block bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors">
                        View Categories
                    </a>
                </div>

                <div class="bg-white rounded-xl shadow-md p-6 card-hover text-center">
                    <div class="bg-yellow-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg class="w-8 h-8 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
                        </svg>
                    </div>
                    <h3 class="text-lg font-semibold text-gray-900 mb-2">📚 API Documentation</h3>
                    <p class="text-gray-600 text-sm mb-4">Interactive API documentation</p>
                    <a href="/docs" class="inline-block bg-yellow-600 text-white px-4 py-2 rounded-lg hover:bg-yellow-700 transition-colors">
                        View API Docs
                    </a>
                </div>
            </div>

            <!-- System Status -->
            <div class="bg-white rounded-xl shadow-md p-6 mb-8">
                <h2 class="text-xl font-semibold text-gray-900 mb-4">System Status</h2>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <span class="text-gray-600">Overall Status:</span>
                        <span id="overallStatus" class="text-gray-500">Checking...</span>
                    </div>
                    <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <span class="text-gray-600">Service Categories:</span>
                        <span id="categoriesStatus" class="text-gray-500">Loading...</span>
                    </div>
                    <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <span class="text-gray-600">Custom Fields:</span>
                        <span id="fieldsStatus" class="text-gray-500">Loading...</span>
                    </div>
                </div>
            </div>

            <!-- Quick Stats -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div class="bg-white rounded-xl shadow-md p-6 text-center">
                    <div class="text-3xl font-bold text-blue-600" id="totalForms">--</div>
                    <div class="text-gray-600 text-sm">Total Forms</div>
                </div>
                <div class="bg-white rounded-xl shadow-md p-6 text-center">
                    <div class="text-3xl font-bold text-green-600" id="totalCategories">--</div>
                    <div class="text-gray-600 text-sm">Service Categories</div>
                </div>
                <div class="bg-white rounded-xl shadow-md p-6 text-center">
                    <div class="text-3xl font-bold text-purple-600" id="totalFields">--</div>
                    <div class="text-gray-600 text-sm">Custom Fields</div>
                </div>
                <div class="bg-white rounded-xl shadow-md p-6 text-center">
                    <div class="text-3xl font-bold text-yellow-600" id="totalVendors">--</div>
                    <div class="text-gray-600 text-sm">Active Vendors</div>
                </div>
            </div>
        </div>

        <script>
            // Load system status and stats
            document.addEventListener('DOMContentLoaded', function() {
                loadSystemStatus();
                loadStats();
            });

            async function loadSystemStatus() {
                try {
                    const response = await fetch('/api/v1/webhooks/health');
                    const data = await response.json();
                    
                    const statusEl = document.getElementById('overallStatus');
                    if (data.status === 'healthy') {
                        statusEl.innerHTML = '<span class="text-green-600 font-medium">✅ All Systems Operational</span>';
                    } else {
                        statusEl.innerHTML = '<span class="text-red-600 font-medium">❌ System Issues Detected</span>';
                    }
                    
                    document.getElementById('categoriesStatus').innerHTML = 
                        `<span class="text-blue-600 font-medium">${data.service_categories || 0} Available</span>`;
                    document.getElementById('fieldsStatus').innerHTML = 
                        `<span class="text-purple-600 font-medium">${data.custom_field_mappings || 0} Mapped</span>`;
                    
                } catch (error) {
                    document.getElementById('overallStatus').innerHTML = 
                        '<span class="text-red-600 font-medium">❌ Connection Failed</span>';
                }
            }

            async function loadStats() {
                try {
                    const [webhookResponse, categoriesResponse] = await Promise.all([
                        fetch('/api/v1/webhooks/health'),
                        fetch('/api/v1/webhooks/service-categories')
                    ]);
                    
                    const webhookData = await webhookResponse.json();
                    const categoriesData = await categoriesResponse.json();
                    
                    document.getElementById('totalForms').textContent = categoriesData.total_categories || 17;
                    document.getElementById('totalCategories').textContent = categoriesData.total_categories || 17;
                    document.getElementById('totalFields').textContent = webhookData.custom_field_mappings || 0;
                    document.getElementById('totalVendors').textContent = '--'; // Would need vendor endpoint
                    
                } catch (error) {
                    console.error('Error loading stats:', error);
                }
            }
        </script>
    </body>
    </html>
    """)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Global health check"""
    return {
        "status": "healthy",
        "service": "DocksidePros Lead Router Pro",
        "version": "2.0.0",
        "features": [
            "Enhanced webhook processing",
            "Dynamic form handling", 
            "Admin dashboard",
            "Field management",
            "Service classification",
            "Vendor routing"
        ]
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return HTMLResponse(
        content="""
        <html>
            <head>
                <title>404 - Not Found</title>
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; margin-top: 100px; background: #f8f9fa; }
                    .container { max-width: 600px; margin: 0 auto; padding: 40px 20px; background: white; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
                    h1 { color: #dc3545; margin-bottom: 20px; }
                    p { color: #6c757d; margin-bottom: 30px; }
                    a { color: #007bff; text-decoration: none; margin: 0 10px; }
                    a:hover { text-decoration: underline; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>404 - Page Not Found</h1>
                    <p>The requested resource was not found on this server.</p>
                    <div>
                        <a href="/">← Back to Home</a> | 
                        <a href="/admin">Admin Dashboard</a> |
                        <a href="/docs">API Docs</a> |
                        <a href="/system-health">System Health</a>
                    </div>
                </div>
            </body>
        </html>
        """,
        status_code=404
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    logger.info("🚀 DocksidePros Lead Router Pro starting up...")
    logger.info("✅ Enhanced webhook system loaded")
    logger.info("✅ Admin dashboard available at /admin")
    logger.info("✅ System health page available at /system-health")
    logger.info("✅ Service categories page available at /service-categories")
    logger.info("✅ API documentation available at /docs")
    logger.info("🎯 Ready to process form submissions!")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
