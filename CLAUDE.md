# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Starting the Application
```bash
# Install dependencies
pip install -r requirements.txt

# Start the FastAPI application
python main_working_final.py

# For development with Docker
docker-compose up -d
```

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest test_ghl_connection.py

# Test API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/webhooks/health
```

### Environment Setup
Create a `.env` file with the following structure:
```env
# GoHighLevel API
GHL_LOCATION_ID=your_location_id
GHL_PRIVATE_TOKEN=your_private_token
GHL_AGENCY_API_KEY=your_agency_key

# Database
DATABASE_URL=sqlite:///smart_lead_router.db

# Security
SECRET_KEY=your_secret_key
JWT_SECRET_KEY=your_jwt_secret

# Email (for 2FA)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email
SMTP_PASSWORD=your_app_password
```

## High-Level Architecture

### System Overview
Lead Router Pro is an AI-powered lead routing system for marine services that processes form submissions via webhooks and integrates with GoHighLevel CRM. The system follows a multi-layered architecture:

```
WordPress/Elementor → Webhook → FastAPI Server → Service Classification → GHL Integration → Vendor Routing
```

### Core Components

1. **FastAPI Application** (`main_working_final.py`)
   - Entry point that sets up routes, middleware, and CORS
   - Serves admin dashboard and API documentation
   - Handles security through IP whitelisting and JWT authentication

2. **API Routes** (`api/routes/`)
   - `webhook_routes.py`: Processes form submissions from Elementor
   - `admin_routes.py`: Admin dashboard API endpoints
   - `routing_admin.py`: Smart routing configuration and management
   - `auth_routes.py`: Authentication and 2FA endpoints
   - `security_admin.py`: IP whitelist and security management

3. **Services** (`api/services/`)
   - `ghl_api.py` / `ghl_api_enhanced_v2.py`: GoHighLevel API integration
   - `ai_classifier.py`: Service classification with 60+ marine categories
   - `simple_lead_router.py`: Lead routing logic and vendor assignment
   - `field_mapper.py`: Maps form fields to GHL custom fields
   - `email_service.py` / `free_email_2fa.py`: Email notifications and 2FA

4. **Database** (`database/`)
   - `models.py`: SQLAlchemy models for multi-tenant architecture
   - `simple_connection.py`: Database connection management
   - Tables: tenants, users, accounts, vendors, leads, webhooks, routing_rules

5. **Security** (`api/security/`)
   - `middleware.py`: IP security and cleanup middleware
   - `auth_middleware.py`: JWT authentication middleware
   - `ip_security.py`: IP whitelist management

### Key Workflows

1. **Form Processing Flow**:
   - Elementor form submission → webhook endpoint
   - Field validation and mapping
   - Service classification (60+ categories)
   - Contact creation/update in GHL
   - Lead scoring and priority assignment
   - Vendor routing (when enabled)

2. **Admin Dashboard Features**:
   - System health monitoring
   - Field management (generate references, create from CSV)
   - Form testing interface
   - Vendor management
   - Security configuration

3. **Authentication Flow**:
   - Email/password login
   - 2FA via email (Gmail SMTP)
   - JWT token generation
   - IP whitelist validation

### Important Files and Their Purposes

- `lead_router_pro_dashboard.html`: Comprehensive admin dashboard UI
- `config.py`: Centralized configuration management
- `field_reference.json`: GHL custom field mappings (auto-generated)
- `security_data.json`: IP whitelist and security settings
- `requirements.txt`: Python dependencies (FastAPI, SQLAlchemy, etc.)

### Database Schema
The system uses a multi-tenant architecture with the following key models:
- **Tenant**: Organization/company accounts
- **User**: Authentication with roles (admin, user, viewer)
- **Account**: GHL location configurations
- **Vendor**: Service providers with coverage areas
- **Lead**: Processed form submissions
- **WebhookLog**: Request/response logging
- **RoutingRule**: Smart routing configurations

### API Endpoints Structure
- `/api/v1/webhooks/elementor/{form_identifier}`: Form processing
- `/api/v1/admin/*`: Admin dashboard APIs
- `/api/v1/auth/*`: Authentication endpoints
- `/api/v1/routing/*`: Smart routing configuration
- `/api/v1/security/*`: Security management

### Testing Approach
- Use `TESTING_GUIDE.md` for comprehensive 8-phase testing
- Test form submissions with different service types
- Verify GHL integration with test connections
- Check field mapping and custom field creation
- Validate vendor routing logic

### Common Development Tasks

When adding new features:
1. Check existing patterns in similar files
2. Follow the established routing structure in `api/routes/`
3. Use the existing GHL API client in `api/services/ghl_api.py`
4. Add appropriate logging for debugging
5. Update the admin dashboard if UI changes needed

When debugging:
1. Check logs in the console output
2. Use the admin dashboard for system status
3. Test API endpoints directly with curl or Swagger UI
4. Verify environment variables are loaded correctly
5. Check database connections and migrations