# GHL Vendor User Creation Setup Guide

## Overview

This guide explains how to set up the GoHighLevel workflow webhook to automatically trigger vendor user creation when a vendor application is approved.

## System Components

### 1. **Database Structure**
- `vendors` table has `ghl_user_id` field to store the created user ID
- `update_vendor_status()` method updates vendor status and links user ID

### 2. **GHL API Service** 
- `create_user()` - Creates new users in GHL location using **Agency API key**
- `get_user_by_email()` - Checks if user already exists
- `update_user()` - Updates user permissions/details
- `delete_user()` - Removes users if needed

### 3. **Webhook Endpoint**
- **URL**: `/api/v1/webhooks/ghl/vendor-user-creation`
- **Method**: POST
- **Purpose**: Receives GHL workflow webhook and creates vendor user accounts

### 4. **⚠️ CRITICAL REQUIREMENT: Agency API Key**
- **User creation in GHL requires an Agency API key, NOT a location PIT token**
- The system uses PIT token for contact operations and Agency API key for user operations
- You must configure `GHL_AGENCY_API_KEY` in your environment variables

## GHL Workflow Setup Instructions

### Step 1: Access Your GHL Workflow

1. **Log in to GoHighLevel**
2. **Navigate to**: Automation → Workflows
3. **Find workflow**: "Vendor Submission : 1749074973147"
4. **Click to edit** the workflow

### Step 2: Add Webhook Action

1. **Find the approval step** in your workflow (where vendor gets approved)
2. **Add new action** after approval
3. **Select**: "Webhook" action
4. **Configure webhook**:

#### Webhook Configuration:

**Webhook URL (Local Development):**
```
http://127.0.0.1:8000/api/v1/webhooks/ghl/vendor-user-creation
```

**Webhook URL (Production):**
```
http://71.208.153.160:8000/api/v1/webhooks/ghl/vendor-user-creation
```

**Method:** `POST`

**Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Payload:**
```json
{
  "contact_id": "{{contact.id}}",
  "contactId": "{{contact.id}}",
  "workflow_id": "1749074973147",
  "event_type": "vendor_approved",
  "timestamp": "{{timestamp}}",
  "location_id": "{{location.id}}"
}
```

### Step 3: Workflow Trigger Conditions

**When to trigger the webhook:**
- ✅ Vendor application is **approved**
- ✅ Contact has **vendor application tags**
- ✅ Contact has required **custom fields** populated
- ❌ Do NOT trigger for rejected applications

**Recommended workflow flow:**
1. Vendor submits application (via Elementor form)
2. Contact created in GHL with vendor data
3. **Manual review/approval step** (admin reviews application)
4. **If approved** → Trigger user creation webhook
5. **If rejected** → Send rejection email (no user creation)

### Step 4: Test the Webhook

#### Test Payload Example:
```json
{
  "contact_id": "vSpZ6uNu27Nsc6NJAxkz",
  "contactId": "vSpZ6uNu27Nsc6NJAxkz",
  "workflow_id": "1749074973147",
  "event_type": "vendor_approved",
  "timestamp": "2025-06-04T21:30:00Z",
  "location_id": "ilmrtA1Vk6rvcy4BswKg"
}
```

#### Expected Response (Success):
```json
{
  "status": "success",
  "message": "Successfully created user account for vendor maria.santos@pristineyachts.com",
  "user_id": "user_abc123xyz",
  "contact_id": "vSpZ6uNu27Nsc6NJAxkz",
  "vendor_email": "maria.santos@pristineyachts.com",
  "vendor_company": "Pristine Yacht Services LLC",
  "action": "user_created",
  "processing_time_seconds": 1.234
}
```

## What the Webhook Does

### 1. **Receives GHL Workflow Data**
- Extracts `contact_id` from webhook payload
- Validates required fields

### 2. **Retrieves Vendor Information**
- Fetches full contact details from GHL API
- Extracts vendor email, name, phone, company name
- Gets custom field data (company name, services, etc.)

### 3. **Checks for Existing User**
- Searches GHL location for existing user with same email
- If user exists, links to vendor record and returns success
- If no user exists, proceeds to create new user

### 4. **Creates GHL User Account**
- Creates user with vendor-specific permissions
- Limited access (can only see assigned leads)
- Permissions include: contacts, opportunities, appointments, conversations
- Excludes: campaigns, workflows, settings, admin functions

### 5. **Updates Database**
- Links created user ID to vendor record
- Updates vendor status to "active"
- Logs activity for tracking

### 6. **Sends Welcome Email**
- Automatically sends welcome email to vendor
- Includes login instructions and portal access info
- Explains available features and next steps

## Vendor User Permissions

The created users have **limited vendor permissions**:

### ✅ **Allowed Access:**
- View assigned leads/opportunities
- Manage appointments
- Send/receive messages with clients
- View dashboard stats (their data only)
- Update lead status and notes
- Make phone calls
- View lead values and reporting

### ❌ **Restricted Access:**
- Cannot create/edit campaigns
- Cannot access workflows or triggers
- Cannot see other vendors' data (`assignedDataOnly: true`)
- Cannot access location settings
- Cannot manage other users
- Cannot access billing/payments
- Cannot export data

## Troubleshooting

### Common Issues:

#### 1. **Webhook Not Triggering**
- ✅ Check workflow is active
- ✅ Verify webhook URL is correct
- ✅ Ensure approval step triggers webhook
- ✅ Check GHL workflow logs

#### 2. **Contact ID Not Found**
- ✅ Verify contact exists in GHL
- ✅ Check contact ID format in payload
- ✅ Ensure contact has required fields

#### 3. **User Creation Fails**
- ✅ Check GHL API permissions
- ✅ Verify location ID is correct
- ✅ Check if email already exists
- ✅ Review user creation payload

#### 4. **Database Not Updated**
- ✅ Check if vendor record exists
- ✅ Verify email matching logic
- ✅ Check database connection

### Debug Steps:

1. **Check webhook endpoint health:**
   ```bash
   curl http://127.0.0.1:8000/api/v1/webhooks/health
   ```

2. **Test webhook manually:**
   ```bash
   curl -X POST http://127.0.0.1:8000/api/v1/webhooks/ghl/vendor-user-creation \
     -H "Content-Type: application/json" \
     -d '{"contact_id": "your_contact_id"}'
   ```

3. **Check server logs** for detailed error messages

4. **Verify GHL API access** using test scripts

## Security Considerations

### 1. **Webhook Security**
- Consider adding webhook signature verification
- Use HTTPS in production
- Implement rate limiting

### 2. **User Permissions**
- Users have minimal required permissions
- `assignedDataOnly: true` ensures data isolation
- Regular permission audits recommended

### 3. **Data Protection**
- Vendor emails are normalized (lowercase)
- Sensitive data logged securely
- User creation activities tracked

## Monitoring & Maintenance

### 1. **Activity Logging**
- All user creation attempts logged to database
- Success/failure tracking with timestamps
- Error details captured for debugging

### 2. **Performance Monitoring**
- Processing time tracked for each request
- Database query performance monitoring
- GHL API response time tracking

### 3. **Regular Maintenance**
- Review user permissions periodically
- Clean up inactive vendor accounts
- Monitor webhook success rates

## Integration Flow Summary

```
Vendor Application → GHL Contact → Workflow Approval → Webhook Trigger → User Creation → Welcome Email
```

1. **Vendor submits application** (Elementor form)
2. **Contact created in GHL** with vendor data
3. **Admin reviews and approves** application
4. **GHL workflow triggers webhook** to your system
5. **System creates GHL user** with vendor permissions
6. **Database updated** with user ID link
7. **Welcome email sent** to vendor
8. **Vendor can log in** to portal

This automated process ensures approved vendors get immediate access to their portal while maintaining security and proper permissions.
