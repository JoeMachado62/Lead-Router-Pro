# WordPress Developer Instructions - Lead Router Pro

## 🚀 SYSTEM STATUS: PRODUCTION READY

The Lead Router Pro system has been **completely rebuilt** with FastAPI and includes a comprehensive admin dashboard. This guide provides current webhook endpoints and integration instructions.

### ✅ **What's New**
- **FastAPI Backend**: High-performance async web framework
- **Admin Dashboard**: Full system management at `/admin`
- **Enhanced API**: RESTful endpoints with automatic documentation
- **Multi-tenant Support**: Scalable architecture for multiple clients
- **Advanced Field Management**: Dynamic field creation and mapping

### ✅ **Current Server Configuration**
- **Production Server**: `https://dockside.life` (when deployed)
- **Development Server**: `http://localhost:8000`
- **Admin Dashboard**: `http://localhost:8000/admin`
- **API Documentation**: `http://localhost:8000/docs`
- **Webhook Base URL**: `http://localhost:8000/api/v1/webhooks/elementor/`

---

# WordPress Developer Integration Guide

## 🔗 Server Endpoints

### Health Check Endpoints
```bash
# System health
GET /health

# Webhook system health  
GET /api/v1/webhooks/health

# Service categories
GET /api/v1/webhooks/service-categories

# Field mappings
GET /api/v1/webhooks/field-mappings
```

### Form Submission Endpoints
```bash
# Primary webhook endpoint
POST /api/v1/webhooks/elementor/{form_identifier}

# Examples:
POST /api/v1/webhooks/elementor/boat_maintenance_ceramic_coating
POST /api/v1/webhooks/elementor/marine_systems_electrical_service
POST /api/v1/webhooks/elementor/emergency_tow_request
POST /api/v1/webhooks/elementor/vendor_application_general
```

## 🛥️ CLIENT LEAD FORMS

### Form 1: Ceramic Coating Request
**Webhook URL**: `http://localhost:8000/api/v1/webhooks/elementor/boat_maintenance_ceramic_coating`

| Elementor Field Label | Custom ID (EXACT) | Required | Sample Value |
|----------------------|-------------------|----------|--------------|
| First Name | `firstName` | ✅ Yes | "John" |
| Last Name | `lastName` | ✅ Yes | "Smith" |
| Email Address | `email` | ✅ Yes | "john.smith@email.com" |
| Phone Number | `phone` | ✅ Yes | "555-123-4567" |
| Vessel Make | `vessel_make` | No | "Sea Ray" |
| Vessel Model | `vessel_model` | No | "Sundancer" |
| Vessel Year | `vessel_year` | No | "2020" |
| Vessel Length (ft) | `vessel_length_ft` | No | "35" |
| Service Needed | `specific_service_needed` | No | "Ceramic coating for 35ft boat" |
| Location/Marina | `vessel_location__slip` | No | "Miami Beach Marina - Slip 42" |
| Zip Code of Service | `zip_code_of_service` | No | "33139" |
| Preferred Timeline | `desired_timeline` | No | "Within 2 weeks" |
| Budget Range | `budget_range` | No | "$3000-$5000" |
| Special Requests | `special_requests__notes` | No | "Please call before arriving" |
| Preferred Contact Method | `preferred_contact_method` | No | "Email" |

### Form 2: Electrical Service Request
**Webhook URL**: `http://localhost:8000/api/v1/webhooks/elementor/marine_systems_electrical_service`

| Elementor Field Label | Custom ID (EXACT) | Required | Sample Value |
|----------------------|-------------------|----------|--------------|
| First Name | `firstName` | ✅ Yes | "Sarah" |
| Last Name | `lastName` | ✅ Yes | "Johnson" |
| Email Address | `email` | ✅ Yes | "sarah.j@gmail.com" |
| Phone Number | `phone` | ✅ Yes | "555-987-6543" |
| Vessel Make | `vessel_make` | No | "Boston Whaler" |
| Vessel Length | `vessel_length_ft` | No | "28" |
| Service Needed | `specific_service_needed` | No | "Battery system upgrade" |
| Location/Marina | `vessel_location__slip` | No | "Key Biscayne Marina" |
| Zip Code of Service | `zip_code_of_service` | No | "33149" |
| Timeline | `desired_timeline` | No | "ASAP" |
| Budget Range | `budget_range` | No | "$1000-$2000" |
| Special Requests | `special_requests__notes` | No | "Need certified marine electrician" |

### Form 3: Emergency Tow Request
**Webhook URL**: `http://localhost:8000/api/v1/webhooks/elementor/emergency_tow_request`

| Elementor Field Label | Custom ID (EXACT) | Required | Sample Value |
|----------------------|-------------------|----------|--------------|
| First Name | `firstName` | ✅ Yes | "Mike" |
| Last Name | `lastName` | ✅ Yes | "Davis" |
| Email Address | `email` | ✅ Yes | "mike@boater.com" |
| Phone Number | `phone` | ✅ Yes | "555-456-7890" |
| Current Location | `vessel_location__slip` | No | "Anchored near Stiltsville" |
| Emergency Details | `specific_service_needed` | No | "Engine failure, need immediate tow" |
| Vessel Make | `vessel_make` | No | "Grady White" |
| Vessel Length | `vessel_length_ft` | No | "32" |
| Zip Code | `zip_code_of_service` | No | "33149" |
| Contact Method | `preferred_contact_method` | No | "Phone Call" |

---

## 🏢 VENDOR APPLICATION FORMS

### Form 1: General Vendor Application
**Webhook URL**: `http://localhost:8000/api/v1/webhooks/elementor/vendor_application_general`

| Elementor Field Label | Custom ID (EXACT) | Required | Sample Value |
|----------------------|-------------------|----------|--------------|
| **Contact Information** |
| First Name | `firstName` | ✅ Yes | "Robert" |
| Last Name | `lastName` | ✅ Yes | "Martinez" |
| Email Address | `email` | ✅ Yes | "rob@marinepro.com" |
| Phone Number | `phone` | ✅ Yes | "555-234-5678" |
| **Business Information** |
| Company Name | `vendor_company_name` | ✅ Yes | "Marine Pro Services LLC" |
| Years in Business | `years_in_business` | No | "8" |
| Website | `website_url` | No | "https://marinepro.com" |
| **Service Details** |
| Services Provided | `services_provided` | No | "Boat maintenance, detailing, repairs" |
| Service Categories | `primary_service_category` | No | "Boat Maintenance" |
| Service Areas | `service_zip_codes` | No | "33101, 33139, 33154" |
| **Credentials** |
| Licenses | `licences__certifications` | No | "FL Marine Contractor #123456" |
| Insurance | `insurance_coverage` | No | "General Liability $1M" |
| About Company | `about_your_company` | No | "Family-owned marine services" |
| **Availability** |
| Taking New Work | `taking_new_work` | No | "Yes" |
| Contact Method | `vendor_preferred_contact_method` | No | "Phone" |

---

## 🧪 TESTING INSTRUCTIONS

### Step 1: Verify Server Status
```bash
# Check if server is running
curl http://localhost:8000/health

# Test webhook system
curl http://localhost:8000/api/v1/webhooks/health

# Check form support
curl http://localhost:8000/api/v1/webhooks/service-categories
```

### Step 2: Test Form Submission

#### Client Lead Test:
```bash
curl -X POST http://localhost:8000/api/v1/webhooks/elementor/boat_maintenance_ceramic_coating \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "John",
    "lastName": "Smith", 
    "email": "john.smith@test.com",
    "phone": "555-123-4567",
    "vessel_make": "Sea Ray",
    "specific_service_needed": "Ceramic coating",
    "zip_code_of_service": "33139",
    "budget_range": "$3000-$5000"
  }'
```

#### Vendor Application Test:
```bash
curl -X POST http://localhost:8000/api/v1/webhooks/elementor/vendor_application_general \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "Robert",
    "lastName": "Martinez",
    "email": "rob@marinepro.com",
    "phone": "555-234-5678",
    "vendor_company_name": "Marine Pro Services LLC",
    "services_provided": "Boat maintenance, detailing",
    "service_zip_codes": "33101, 33139, 33154"
  }'
```

### Expected Response:
```json
{
  "status": "success",
  "message": "Webhook processed successfully",
  "contact_id": "contact_xyz123",
  "action": "created",
  "form_type": "client_lead",
  "service_category": "boat_maintenance",
  "processing_time_seconds": 1.234
}
```

---

## 🚨 CRITICAL REQUIREMENTS

### 1. **Exact Field Matching**
- Custom IDs must match **EXACTLY** (case-sensitive)
- Examples: ✅ `firstName` ❌ `first_name` ❌ `FirstName`

### 2. **Required Fields**
- **Client leads**: `firstName`, `lastName`, `email`
- **Vendor applications**: `firstName`, `lastName`, `email`, `vendor_company_name`

### 3. **Webhook URL Format**
- Must use exact endpoint: `http://localhost:8000/api/v1/webhooks/elementor/{form_identifier}`
- Form identifiers are predefined (see examples above)

### 4. **Content Type**
- Always send `Content-Type: application/json`
- Data must be valid JSON format

---

## ✅ SUCCESS CRITERIA

- ✅ Server responds with HTTP 200 status
- ✅ Returns JSON with `status: "success"`
- ✅ Includes `contact_id` in response
- ✅ No validation errors
- ✅ Admin dashboard shows processed lead

---

## 🔧 ADMIN DASHBOARD

Access the admin dashboard at `http://localhost:8000/admin` for:

- **System Configuration**: GHL API setup and testing
- **Field Management**: Generate field references, create custom fields
- **Form Testing**: Test submissions directly in browser
- **System Monitoring**: View health status and recent activity
- **Vendor Management**: Manage vendor applications and data

---

## 📊 MONITORING

### Admin Dashboard Features:
- Real-time system health monitoring
- Live form submission testing
- Custom field management
- Vendor application tracking
- Service category analytics

### API Documentation:
- Interactive docs: `http://localhost:8000/docs`
- Redoc format: `http://localhost:8000/redoc`

---

## 🆘 TROUBLESHOOTING

### Common Issues:

1. **Connection Failed**: Check server is running on port 8000
2. **Field Validation Error**: Verify exact field name matching
3. **GHL API Error**: Check credentials in admin dashboard
4. **Form Not Found**: Verify webhook URL and form identifier

### Debug Commands:
```bash
# Check server logs
docker-compose logs -f api

# Test specific endpoint
curl -v http://localhost:8000/api/v1/webhooks/health

# Admin dashboard health check
curl http://localhost:8000/admin
```

---

**The system is production-ready and fully functional. Use the admin dashboard for configuration and monitoring.**
