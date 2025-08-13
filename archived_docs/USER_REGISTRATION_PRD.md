# User Registration & Approval System - Product Requirements Document

## Executive Summary
This document outlines the implementation of an automated user registration and approval system integrated with GoHighLevel (GHL) CRM. The system processes registration forms, creates contacts, and upon admin approval, automatically generates GHL user accounts with appropriate credentials and permissions.

## System Architecture

### Overview
```
Registration Form → Webhook Endpoint → Contact Creation → Admin Approval → GHL User Creation → Credential Assignment
```

### Core Components
1. **Registration Form Processing** - Receives and validates user registration data
2. **Contact Management** - Creates/updates contacts in GHL CRM
3. **Admin Approval Workflow** - Tag-based or webhook-triggered approval mechanism
4. **User Account Generation** - Creates GHL user accounts with restricted permissions
5. **Credential Management** - Generates and assigns login credentials

## Implementation Guide

### 1. Database Schema

```sql
-- Users table for storing registration data
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    company_name VARCHAR(255),
    ghl_contact_id VARCHAR(100),
    ghl_user_id VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending', -- pending, approved, active, suspended
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    activated_at TIMESTAMP
);

-- Activity log for tracking events
CREATE TABLE activity_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type VARCHAR(100),
    event_data JSON,
    user_id INTEGER,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 2. Registration Form Webhook Endpoint

```python
from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any
import json
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/api/v1/webhooks/registration/{form_identifier}")
async def handle_registration_form(request: Request, form_identifier: str):
    """
    Process user registration form submissions
    """
    try:
        # Parse form data
        form_data = await request.json()
        logger.info(f"Registration form received: {json.dumps(form_data, indent=2)}")
        
        # Extract user information
        user_data = {
            "email": form_data.get("email"),
            "first_name": form_data.get("first_name"),
            "last_name": form_data.get("last_name"),
            "phone": form_data.get("phone"),
            "company_name": form_data.get("company_name"),
            "additional_info": form_data.get("additional_info", {})
        }
        
        # Validate required fields
        if not user_data["email"]:
            raise HTTPException(status_code=400, detail="Email is required")
        
        # Check for existing user
        existing_user = db.get_user_by_email(user_data["email"])
        if existing_user:
            logger.info(f"User already exists: {user_data['email']}")
            return {
                "status": "existing_user",
                "message": "User already registered",
                "user_id": existing_user["id"]
            }
        
        # Create contact in GHL
        ghl_contact = await create_ghl_contact(user_data)
        user_data["ghl_contact_id"] = ghl_contact["id"]
        
        # Store user in database
        user_id = db.create_user(user_data)
        
        # Log activity
        db.log_activity(
            event_type="user_registration",
            event_data=user_data,
            user_id=user_id,
            success=True
        )
        
        # Send admin notification
        await notify_admin_new_registration(user_data)
        
        return {
            "status": "success",
            "message": "Registration successful - pending approval",
            "user_id": user_id,
            "ghl_contact_id": ghl_contact["id"]
        }
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

### 3. GHL Contact Creation

```python
async def create_ghl_contact(user_data: Dict[str, Any]) -> Dict:
    """
    Create or update contact in GoHighLevel
    """
    ghl_api = GoHighLevelAPI(
        private_token=config.GHL_PRIVATE_TOKEN,
        location_id=config.GHL_LOCATION_ID
    )
    
    # Check for existing contact
    existing_contact = ghl_api.search_contact_by_email(user_data["email"])
    
    if existing_contact:
        # Update existing contact
        contact_payload = {
            "firstName": user_data["first_name"],
            "lastName": user_data["last_name"],
            "phone": user_data["phone"],
            "companyName": user_data["company_name"],
            "tags": ["registration_pending"],
            "customFields": [
                {"key": "registration_status", "value": "pending_approval"},
                {"key": "registration_date", "value": str(datetime.now())}
            ]
        }
        updated_contact = ghl_api.update_contact(existing_contact["id"], contact_payload)
        return updated_contact
    else:
        # Create new contact
        contact_payload = {
            "firstName": user_data["first_name"],
            "lastName": user_data["last_name"],
            "email": user_data["email"],
            "phone": user_data["phone"],
            "companyName": user_data["company_name"],
            "source": "Registration Form",
            "tags": ["registration_pending"],
            "customFields": [
                {"key": "registration_status", "value": "pending_approval"},
                {"key": "registration_date", "value": str(datetime.now())}
            ]
        }
        new_contact = ghl_api.create_contact(contact_payload)
        return new_contact
```

### 4. Admin Approval Webhook

```python
@router.post("/api/v1/webhooks/approve-user")
async def handle_user_approval_webhook(request: Request):
    """
    GHL workflow webhook triggered when admin adds 'approved' tag
    """
    try:
        # Validate webhook security
        api_key = request.headers.get("X-Webhook-API-Key")
        if api_key != config.WEBHOOK_API_KEY:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        # Parse GHL webhook payload
        payload = await request.json()
        contact_id = payload.get("contact_id")
        email = payload.get("email")
        
        logger.info(f"User approval webhook received for: {email}")
        
        # Get user from database
        user = db.get_user_by_email(email)
        if not user:
            logger.error(f"No user found for email: {email}")
            raise HTTPException(status_code=404, detail="User not found")
        
        if user["status"] == "active":
            logger.info(f"User already active: {email}")
            return {"status": "already_active", "user_id": user["id"]}
        
        # Create GHL user account
        ghl_user = await create_ghl_user_account(user)
        
        # Update user status
        db.update_user_status(
            user_id=user["id"],
            status="active",
            ghl_user_id=ghl_user["id"],
            approved_at=datetime.now()
        )
        
        # Update contact with user ID
        await update_contact_with_user_id(contact_id, ghl_user["id"])
        
        # Send welcome email with credentials
        await send_welcome_email(user, ghl_user)
        
        # Log activity
        db.log_activity(
            event_type="user_approved",
            event_data={
                "user_id": user["id"],
                "ghl_user_id": ghl_user["id"],
                "approved_by": "admin"
            },
            user_id=user["id"],
            success=True
        )
        
        return {
            "status": "success",
            "message": f"User approved and account created",
            "user_id": user["id"],
            "ghl_user_id": ghl_user["id"]
        }
        
    except Exception as e:
        logger.error(f"Approval webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

### 5. GHL User Account Creation

```python
import secrets
import string

async def create_ghl_user_account(user: Dict) -> Dict:
    """
    Create GHL user account with appropriate permissions
    """
    ghl_api = GoHighLevelAPI(
        private_token=config.GHL_PRIVATE_TOKEN,
        location_id=config.GHL_LOCATION_ID,
        agency_api_key=config.GHL_AGENCY_API_KEY,
        company_id=config.GHL_COMPANY_ID
    )
    
    # Check if user already exists
    existing_user = ghl_api.get_user_by_email(user["email"])
    if existing_user:
        logger.info(f"GHL user already exists: {user['email']}")
        return existing_user
    
    # Generate secure password
    password = generate_secure_password()
    
    # Prepare user data with restricted permissions
    user_data = {
        "firstName": user["first_name"],
        "lastName": user["last_name"],
        "email": user["email"],
        "phone": user["phone"],
        "password": password,
        "type": "account",
        "role": "user",
        "locationIds": [config.GHL_LOCATION_ID],
        "permissions": {
            # Core permissions for users
            "contactsEnabled": True,           # View assigned contacts
            "conversationsEnabled": True,      # Communicate with contacts
            "opportunitiesEnabled": True,      # Manage opportunities
            "appointmentsEnabled": True,       # Schedule appointments
            "dashboardStatsEnabled": True,     # View dashboard
            "assignedDataOnly": True,          # CRITICAL: Only see assigned data
            
            # Disabled permissions for security
            "campaignsEnabled": False,
            "workflowsEnabled": False,
            "triggersEnabled": False,
            "funnelsEnabled": False,
            "websitesEnabled": False,
            "settingsEnabled": False,
            "marketingEnabled": False,
            "paymentsEnabled": False,
            "bulkRequestsEnabled": False,
            "exportPaymentsEnabled": False
        }
    }
    
    # Create user (tries V2 API first, falls back to V1)
    created_user = ghl_api.create_user(user_data)
    
    if not created_user or created_user.get("error"):
        raise Exception(f"Failed to create GHL user: {created_user}")
    
    # Store password temporarily for welcome email
    created_user["temp_password"] = password
    
    logger.info(f"GHL user created successfully: {created_user['id']}")
    return created_user

def generate_secure_password(length=12):
    """Generate a secure random password"""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(characters) for _ in range(length))
    return password
```

### 6. Contact Update with User ID

```python
async def update_contact_with_user_id(contact_id: str, ghl_user_id: str):
    """
    Update GHL contact with the created user ID
    """
    ghl_api = GoHighLevelAPI(
        private_token=config.GHL_PRIVATE_TOKEN,
        location_id=config.GHL_LOCATION_ID
    )
    
    update_payload = {
        "customFields": [
            {"key": "ghl_user_id", "value": ghl_user_id},
            {"key": "registration_status", "value": "active"},
            {"key": "activation_date", "value": str(datetime.now())}
        ],
        "tags": ["user_active", "registration_complete"]
    }
    
    # Remove pending tag
    ghl_api.remove_contact_tag(contact_id, "registration_pending")
    
    # Update contact
    updated = ghl_api.update_contact(contact_id, update_payload)
    logger.info(f"Contact {contact_id} updated with user ID {ghl_user_id}")
    return updated
```

### 7. Welcome Email with Credentials

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

async def send_welcome_email(user: Dict, ghl_user: Dict):
    """
    Send welcome email with login credentials
    """
    smtp_config = {
        "host": config.SMTP_HOST,
        "port": config.SMTP_PORT,
        "username": config.SMTP_USERNAME,
        "password": config.SMTP_PASSWORD
    }
    
    # Email content
    subject = "Welcome! Your Account Has Been Approved"
    
    html_content = f"""
    <html>
        <body>
            <h2>Welcome {user['first_name']}!</h2>
            
            <p>Your registration has been approved and your account is now active.</p>
            
            <h3>Your Login Credentials:</h3>
            <ul>
                <li><strong>Login URL:</strong> {config.GHL_LOGIN_URL}</li>
                <li><strong>Email:</strong> {user['email']}</li>
                <li><strong>Temporary Password:</strong> {ghl_user['temp_password']}</li>
            </ul>
            
            <p><strong>Important:</strong> Please change your password upon first login.</p>
            
            <h3>What You Can Do:</h3>
            <ul>
                <li>View and manage your assigned contacts</li>
                <li>Track opportunities and leads</li>
                <li>Schedule appointments</li>
                <li>Communicate with customers</li>
                <li>View your performance dashboard</li>
            </ul>
            
            <p>If you have any questions, please contact support.</p>
            
            <p>Best regards,<br>
            The Admin Team</p>
        </body>
    </html>
    """
    
    # Create message
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = smtp_config["username"]
    message["To"] = user["email"]
    
    # Add HTML content
    html_part = MIMEText(html_content, "html")
    message.attach(html_part)
    
    # Send email
    try:
        with smtplib.SMTP(smtp_config["host"], smtp_config["port"]) as server:
            server.starttls()
            server.login(smtp_config["username"], smtp_config["password"])
            server.send_message(message)
        
        logger.info(f"Welcome email sent to {user['email']}")
        return True
    except Exception as e:
        logger.error(f"Failed to send welcome email: {str(e)}")
        return False
```

## Configuration Requirements

### Environment Variables
```env
# GoHighLevel Configuration
GHL_LOCATION_ID=your_location_id
GHL_PRIVATE_TOKEN=your_private_token
GHL_AGENCY_API_KEY=your_agency_api_key
GHL_COMPANY_ID=your_company_id
GHL_LOGIN_URL=https://app.gohighlevel.com

# Webhook Security
WEBHOOK_API_KEY=your_webhook_api_key

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Database
DATABASE_URL=sqlite:///user_registration.db
```

### GHL Custom Fields Setup
Create these custom fields in GoHighLevel:
- `registration_status` (Text) - Tracks registration state
- `ghl_user_id` (Text) - Stores the created GHL user ID
- `registration_date` (Date) - When user registered
- `activation_date` (Date) - When account was activated

### GHL Workflow Configuration
Create a workflow in GoHighLevel that:
1. Triggers when tag "approve_user" is added to a contact
2. Sends webhook to your approval endpoint
3. Includes contact_id, email, and other relevant fields

## Security Considerations

### 1. Webhook Authentication
- Always validate API keys in webhook headers
- Implement IP whitelisting for GHL servers
- Use HTTPS for all endpoints

### 2. User Permissions
- Apply principle of least privilege
- Set `assignedDataOnly: true` to restrict data access
- Disable unnecessary features like workflows, campaigns, settings

### 3. Password Management
- Generate strong random passwords
- Force password change on first login
- Never store passwords in plain text
- Use secure email for credential delivery

### 4. Data Validation
- Validate all input data
- Check for existing users before creating duplicates
- Implement rate limiting on registration endpoint

## Testing Strategy

### 1. Unit Tests
```python
def test_user_registration():
    """Test user registration flow"""
    user_data = {
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "phone": "+1234567890",
        "company_name": "Test Company"
    }
    
    # Test registration
    response = client.post("/api/v1/webhooks/registration/test", json=user_data)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Verify user in database
    user = db.get_user_by_email("test@example.com")
    assert user is not None
    assert user["status"] == "pending"

def test_user_approval():
    """Test user approval and GHL account creation"""
    # Create pending user
    user_id = db.create_user({
        "email": "approve@example.com",
        "first_name": "Jane",
        "last_name": "Doe",
        "status": "pending"
    })
    
    # Test approval webhook
    approval_payload = {
        "contact_id": "test_contact_123",
        "email": "approve@example.com"
    }
    
    response = client.post(
        "/api/v1/webhooks/approve-user",
        json=approval_payload,
        headers={"X-Webhook-API-Key": config.WEBHOOK_API_KEY}
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Verify user is active
    user = db.get_user_by_id(user_id)
    assert user["status"] == "active"
    assert user["ghl_user_id"] is not None
```

### 2. Integration Tests
- Test full registration to approval flow
- Verify GHL contact creation
- Confirm user account generation
- Validate email delivery

### 3. Load Testing
- Test concurrent registrations
- Verify rate limiting works
- Check database performance
- Monitor API response times

## Monitoring & Logging

### Key Metrics to Track
- Registration success rate
- Approval processing time
- GHL API response times
- Failed user creations
- Email delivery success

### Logging Requirements
```python
# Log all critical events
logger.info(f"User registered: {email}")
logger.info(f"User approved: {email}")
logger.info(f"GHL user created: {user_id}")
logger.error(f"Registration failed: {email} - {error}")
logger.error(f"GHL API error: {response}")
```

## Deployment Checklist

- [ ] Database migrations applied
- [ ] Environment variables configured
- [ ] GHL custom fields created
- [ ] GHL workflow configured
- [ ] Webhook endpoints secured
- [ ] Email service configured
- [ ] SSL certificates installed
- [ ] Monitoring alerts set up
- [ ] Backup strategy implemented
- [ ] Documentation updated

## Support & Maintenance

### Common Issues & Solutions

1. **User already exists error**
   - Check for duplicate emails
   - Verify contact merge logic
   - Review deduplication rules

2. **GHL API failures**
   - Verify API credentials
   - Check rate limits
   - Review permission scopes

3. **Email delivery issues**
   - Validate SMTP settings
   - Check spam filters
   - Review email templates

### Troubleshooting Commands
```bash
# Check user status
python check_user_status.py --email user@example.com

# Manually approve user
python approve_user.py --email user@example.com

# Resend welcome email
python resend_credentials.py --email user@example.com

# Sync GHL contacts
python sync_ghl_users.py --location-id YOUR_LOCATION_ID
```

## Conclusion

This system provides a complete automated solution for user registration and approval with GoHighLevel integration. The implementation ensures security through restricted permissions, proper authentication, and comprehensive logging while maintaining a smooth user experience from registration to account activation.