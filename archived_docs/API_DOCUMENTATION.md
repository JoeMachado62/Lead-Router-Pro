# DocksidePros Lead Router Pro - API Documentation

## Overview

The DocksidePros Lead Router Pro provides a comprehensive REST API for managing lead routing, authentication, field mapping, and vendor management. This documentation covers the main endpoints and integration examples.

## Base URL

- **Production**: `https://dockside.life`
- **Development**: `http://localhost:8000`

## Authentication

The API uses JWT (JSON Web Tokens) for authentication with 2FA support.

### Authentication Flow

1. **Register** → Email verification required
2. **Login Step 1** → Email/password authentication
3. **Login Step 2** → 2FA code verification (if enabled)
4. **Access** → Use JWT token in Authorization header

### Headers

```
Authorization: Bearer <your_jwt_token>
Content-Type: application/json
```

## Core API Endpoints

### 🔐 Authentication Endpoints

#### Register User
```http
POST /api/v1/auth/register
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "first_name": "John",
  "last_name": "Doe",
  "domain": "dockside.life"
}
```

**Response:**
```json
{
  "message": "Registration successful. Please check your email to verify your account.",
  "user_id": "uuid-here"
}
```

#### Verify Email
```http
POST /api/v1/auth/verify-email
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "verification_code": "123456",
  "domain": "dockside.life"
}
```

#### Login (Step 1)
```http
POST /api/v1/auth/login
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "domain": "dockside.life"
}
```

**Response (2FA Required):**
```json
{
  "message": "2FA code sent to your email",
  "requires_2fa": true,
  "user_id": "uuid-here",
  "session_token": "temporary-session-token"
}
```

#### Verify 2FA (Step 2)
```http
POST /api/v1/auth/verify-2fa
```

**Request Body:**
```json
{
  "user_id": "uuid-here",
  "code": "123456",
  "session_token": "temporary-session-token"
}
```

**Response:**
```json
{
  "access_token": "jwt-access-token",
  "refresh_token": "jwt-refresh-token",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "uuid-here",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "user",
    "tenant_id": "tenant-uuid"
  }
}
```

#### Password Reset
```http
POST /api/v1/auth/forgot-password
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "domain": "dockside.life"
}
```

#### Reset Password with Code
```http
POST /api/v1/auth/reset-password
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "reset_code": "RESET123",
  "new_password": "NewSecurePassword123!",
  "domain": "dockside.life"
}
```

### 🎯 Lead Routing Endpoints

#### Submit Lead via Webhook
```http
POST /api/v1/webhooks/elementor/{form_identifier}
```

**Example Form Identifiers:**
- `boat_maintenance_ceramic_coating`
- `marine_systems_electrical_service`
- `emergency_tow_request`
- `vendor_application_general`

**Request Body:**
```json
{
  "firstName": "John",
  "lastName": "Doe",
  "email": "john.doe@example.com",
  "phone": "555-123-4567",
  "serviceNeeded": "Ceramic coating for 40ft yacht",
  "zipCode": "33139",
  "vesselMake": "Sea Ray",
  "vesselModel": "Sundancer 350",
  "vesselLength": "40",
  "urgency": "normal"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Lead processed and routed successfully",
  "lead_id": "lead-uuid",
  "assigned_vendor": {
    "id": "vendor-uuid",
    "name": "Marine Pro Services",
    "email": "contact@marinepro.com",
    "phone": "555-987-6543"
  },
  "routing_method": "performance_based",
  "processing_time_ms": 245
}
```

#### Get Routing Configuration
```http
GET /api/v1/routing/configuration
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "routing_configuration": {
      "performance_percentage": 30
    },
    "total_vendors": 15,
    "vendors_taking_work": 12,
    "location_service_status": "active"
  }
}
```

#### Update Routing Configuration
```http
POST /api/v1/routing/configuration
```

**Request Body:**
```json
{
  "performance_percentage": 50
}
```

#### Test Vendor Matching
```http
POST /api/v1/routing/test-matching
```

**Request Body:**
```json
{
  "zip_code": "33139",
  "service_category": "Boat Maintenance"
}
```

### 📋 Field Management Endpoints

#### Get Field Mappings
```http
GET /api/v1/webhooks/field-mappings
```

**Response:**
```json
{
  "status": "success",
  "custom_field_mappings": {
    "firstName": {
      "name": "First Name",
      "dataType": "TEXT",
      "id": "ghl-field-id"
    },
    "vesselMake": {
      "name": "Vessel Make",
      "dataType": "TEXT",
      "id": "ghl-field-id"
    }
  }
}
```

#### Generate Field Reference
```http
POST /api/v1/admin/generate-field-reference
```

**Response:**
```json
{
  "success": true,
  "fieldCount": 45,
  "message": "Field reference generated successfully"
}
```

#### Create Fields from CSV
```http
POST /api/v1/admin/create-fields-from-csv
```

**Request:** Multipart form data with CSV file

**Response:**
```json
{
  "success": true,
  "created": 5,
  "skipped": 2,
  "errors": 0,
  "message": "Fields created successfully"
}
```

### 👥 Vendor Management Endpoints

#### Get Vendors
```http
GET /api/v1/simple-admin/vendors
```

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "vendor-uuid",
      "name": "Marine Pro Services",
      "email": "contact@marinepro.com",
      "company_name": "Marine Pro LLC",
      "status": "active",
      "performance_score": 0.95,
      "taking_new_work": true,
      "service_areas": ["33139", "33140", "33141"],
      "specialties": ["Boat Maintenance", "Marine Systems"]
    }
  ]
}
```

### 📊 System Health & Monitoring

#### Health Check
```http
GET /api/v1/webhooks/health
```

**Response:**
```json
{
  "status": "healthy",
  "webhook_system": "enhanced_dynamic_processing",
  "database_status": "healthy",
  "field_reference_status": "loaded",
  "service_categories": 17,
  "custom_field_mappings": 45,
  "last_lead_processed": "2025-01-15T10:30:00Z"
}
```

#### Get Service Categories
```http
GET /api/v1/webhooks/service-categories
```

**Response:**
```json
{
  "status": "success",
  "total_categories": 17,
  "service_categories": {
    "boat_maintenance": {
      "name": "Boat Maintenance",
      "keywords": ["maintenance", "cleaning", "detailing"],
      "subcategories": ["ceramic_coating", "hull_cleaning"]
    }
  }
}
```

## Integration Examples

### JavaScript/Node.js Example

```javascript
const axios = require('axios');

class DocksideProAPI {
  constructor(baseURL = 'https://dockside.life') {
    this.baseURL = baseURL;
    this.accessToken = null;
  }

  async login(email, password, domain = 'dockside.life') {
    try {
      // Step 1: Email/Password
      const step1Response = await axios.post(`${this.baseURL}/api/v1/auth/login`, {
        email,
        password,
        domain
      });

      if (step1Response.data.requires_2fa) {
        console.log('2FA required. Check your email for the code.');
        return { requires2FA: true, sessionData: step1Response.data };
      } else {
        this.accessToken = step1Response.data.access_token;
        return { success: true, user: step1Response.data.user };
      }
    } catch (error) {
      throw new Error(`Login failed: ${error.response?.data?.detail || error.message}`);
    }
  }

  async verify2FA(userId, code, sessionToken) {
    try {
      const response = await axios.post(`${this.baseURL}/api/v1/auth/verify-2fa`, {
        user_id: userId,
        code,
        session_token: sessionToken
      });

      this.accessToken = response.data.access_token;
      return { success: true, user: response.data.user };
    } catch (error) {
      throw new Error(`2FA verification failed: ${error.response?.data?.detail || error.message}`);
    }
  }

  async submitLead(formId, leadData) {
    try {
      const response = await axios.post(
        `${this.baseURL}/api/v1/webhooks/elementor/${formId}`,
        leadData,
        {
          headers: {
            'Authorization': `Bearer ${this.accessToken}`,
            'Content-Type': 'application/json'
          }
        }
      );

      return response.data;
    } catch (error) {
      throw new Error(`Lead submission failed: ${error.response?.data?.detail || error.message}`);
    }
  }
}

// Usage Example
async function example() {
  const api = new DocksideProAPI();
  
  // Login
  const loginResult = await api.login('user@example.com', 'password123');
  
  if (loginResult.requires2FA) {
    const code = prompt('Enter 2FA code from email:');
    await api.verify2FA(
      loginResult.sessionData.user_id,
      code,
      loginResult.sessionData.session_token
    );
  }

  // Submit a lead
  const leadResult = await api.submitLead('emergency_tow_request', {
    firstName: 'John',
    lastName: 'Doe',
    email: 'john@example.com',
    phone: '555-123-4567',
    serviceNeeded: 'Emergency towing needed',
    zipCode: '33139',
    urgency: 'high'
  });

  console.log('Lead submitted:', leadResult);
}
```

### Python Example

```python
import requests
import json

class DocksideProAPI:
    def __init__(self, base_url='https://dockside.life'):
        self.base_url = base_url
        self.access_token = None
        self.session = requests.Session()

    def login(self, email, password, domain='dockside.life'):
        """Login with email and password"""
        response = self.session.post(f'{self.base_url}/api/v1/auth/login', json={
            'email': email,
            'password': password,
            'domain': domain
        })
        
        if response.status_code == 200:
            data = response.json()
            if data.get('requires_2fa'):
                return {'requires_2fa': True, 'session_data': data}
            else:
                self.access_token = data['access_token']
                return {'success': True, 'user': data['user']}
        else:
            raise Exception(f"Login failed: {response.text}")

    def verify_2fa(self, user_id, code, session_token):
        """Verify 2FA code"""
        response = self.session.post(f'{self.base_url}/api/v1/auth/verify-2fa', json={
            'user_id': user_id,
            'code': code,
            'session_token': session_token
        })
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data['access_token']
            return {'success': True, 'user': data['user']}
        else:
            raise Exception(f"2FA verification failed: {response.text}")

    def submit_lead(self, form_id, lead_data):
        """Submit a lead"""
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        response = self.session.post(
            f'{self.base_url}/api/v1/webhooks/elementor/{form_id}',
            json=lead_data,
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Lead submission failed: {response.text}")

# Usage
api = DocksideProAPI()

# Login
login_result = api.login('user@example.com', 'password123')

if login_result.get('requires_2fa'):
    code = input('Enter 2FA code from email: ')
    api.verify_2fa(
        login_result['session_data']['user_id'],
        code,
        login_result['session_data']['session_token']
    )

# Submit lead
result = api.submit_lead('boat_maintenance_ceramic_coating', {
    'firstName': 'John',
    'lastName': 'Doe',
    'email': 'john@example.com',
    'phone': '555-123-4567',
    'serviceNeeded': 'Full ceramic coating',
    'zipCode': '33139',
    'vesselMake': 'Sea Ray',
    'vesselLength': '35'
})

print('Lead submitted:', result)
```

## Error Handling

### Common HTTP Status Codes

- **200**: Success
- **400**: Bad Request (invalid data)
- **401**: Unauthorized (invalid/expired token)
- **403**: Forbidden (insufficient permissions)
- **404**: Not Found
- **409**: Conflict (duplicate data)
- **422**: Validation Error
- **500**: Internal Server Error

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong",
  "status_code": 400,
  "timestamp": "2025-01-15T10:30:00Z"
}
```

## Rate Limiting

- **Authentication endpoints**: 10 requests per minute per IP
- **Lead submission**: 100 requests per hour per authenticated user
- **Admin endpoints**: 1000 requests per hour per authenticated admin

## Webhook Security

All webhook endpoints support:

- **IP Whitelisting**: Configure allowed IP addresses
- **HMAC Signature Verification**: Verify request authenticity
- **Rate Limiting**: Prevent abuse
- **Request Logging**: Full audit trail

## Support

For API support and integration assistance:

- **Documentation**: This file and inline API docs at `/docs`
- **Health Check**: Monitor system status at `/health`
- **Test Environment**: Use `http://localhost:8000` for development

## Changelog

### Version 2.0.0 (Current)
- Added 2FA authentication
- Enhanced lead routing with performance-based algorithms
- Improved field mapping system
- Added comprehensive audit logging
- Multi-tenant support

### Version 1.0.0
- Basic lead routing
- Simple authentication
- Field mapping
- Vendor management
