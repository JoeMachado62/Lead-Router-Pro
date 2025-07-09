## Database Structure (smart_lead_router.db)

The database contains the following tables:

### 1. __tenants__ - Multi-tenant support

- id (UUID)
- name, domain, subdomain
- settings (JSON), is_active, subscription_tier, max_users
- created_at, updated_at

### 2. __users__ - User authentication

- id (UUID), tenant_id
- email, password_hash, first_name, last_name, role
- is_active, is_verified, two_factor_enabled
- last_login, login_attempts, locked_until
- created_at, updated_at

### 3. __accounts__ - Company accounts

- id (UUID), tenant_id
- ghl_location_id, company_name, industry
- settings (JSON), subscription_tier
- ghl_api_token
- created_at, updated_at

### 4. __vendors__ - Service providers

- id (UUID), account_id
- ghl_contact_id, name, company_name, email, phone
- services_provided (JSON), service_areas (JSON)
- performance_score, total_leads_received/closed
- avg_response_time_hours, customer_rating, status
- taking_new_work, last_lead_assigned
- created_at

### 5. __leads__ - Customer leads

- id (UUID), account_id, vendor_id
- ghl_contact_id, service_category
- service_details (JSON), location_data (JSON)
- estimated_value, priority_score, status
- assignment_history (JSON)
- created_at, assigned_at, first_response_at, closed_at
- outcome

### 6. __performance_metrics__ - Vendor metrics

- id (UUID), vendor_id, lead_id
- metric_type, metric_value
- timestamp

### 7. __feedback__ - Customer feedback

- id (UUID), lead_id, vendor_id
- rating, comments, feedback_type
- submitted_at

### 8. __auth_tokens__ - JWT tokens

- id (UUID), user_id
- token_type, token_hash, expires_at, is_revoked
- created_at

### 9. __two_factor_codes__ - 2FA codes

- id (UUID), user_id
- code, purpose, expires_at, is_used, attempts
- created_at

### 10. __audit_logs__ - Security audit trail

- id (UUID), tenant_id, user_id
- action, resource, ip_address, user_agent
- details (JSON), timestamp

## Field Mapping System

The system uses a three-tier field mapping approach:

### 1. __Form Field Normalization__ (WordPress/Elementor → Standard Names)

Examples:

- "Your Contact Email?" → "email"
- "What Zip Code Are You Requesting Service In?" → "zip_code_of_service"
- "What Specific Service(s) Do You Request?" → "specific_service_needed"
- "Your Vessel Manufacturer?" → "vessel_make"

### 2. __Standard to GHL Field Mapping__ (field_mappings.json)

```javascript
ServiceNeeded → specific_service_needed
zipCode → zip_code_of_service
vesselMake → vessel_make
vesselModel → vessel_model
specialRequests → special_requests__notes
```

### 3. __GHL Custom Field IDs__ (field_reference.json)

Each GHL custom field has:

- Field Key (e.g., "contact.vessel_make")
- Unique ID (e.g., "B0wHr7XBtjkawyP5O6qH")
- Data Type (TEXT, NUMERICAL, DATE, etc.)

Key custom fields include:

- Vessel Information: make, model, year, length
- Service Details: category, specific needs, timeline
- Location: ZIP code, vessel location/slip
- Vendor Info: company name, services provided, service areas

## Data Flow Process

1. __Webhook Receipt__ → Form data arrives at `/api/v1/webhooks/elementor/{form_identifier}`
2. __Field Normalization__ → WordPress field names converted to standard names
3. __Service Classification__ → Direct mapping to service categories (no AI)
4. __Field Mapping__ → Standard names mapped to GHL field names
5. __GHL Payload Creation__ → Custom fields array built with proper IDs
6. __Contact Creation/Update__ → Data sent to GoHighLevel
7. __Lead Creation__ → Lead record created in local database
8. __Vendor Routing__ → Matching vendors found based on service & location
9. __Assignment__ → Lead assigned to vendor, opportunity created in GHL



# Smart Lead Router Database Structure and Field Mappings

**Legend:**
- `*` = System-generated field
- No marking = Field mapped from forms or GoHighLevel custom fields

---

## Table: accounts
**Purpose:** Company/client accounts in the system

| id* | ghl_location_id | company_name | industry | subscription_tier* | settings* | ghl_private_token | created_at* | updated_at* |
|-----|-----------------|--------------|----------|-------------------|-----------|------------------|-------------|-------------|
| *System UUID* | GHL Location ID | Company Name | Industry Type | *Default: 'starter'* | *JSON config* | GHL API Token | *Auto timestamp* | *Auto timestamp* |

---

## Table: activity_log
**Purpose:** System activity and audit trail

| id* | event_type* | event_data_json* | related_contact_id | related_vendor_id | success* | error_message* | timestamp* | event_data* |
|-----|-------------|------------------|-------------------|-------------------|----------|----------------|------------|-------------|
| *System UUID* | *Event type* | *JSON data* | GHL Contact ID | Vendor ID | *Boolean result* | *Error details* | *Auto timestamp* | *Additional data* |

---

## Table: account_settings
**Purpose:** Account configuration settings

| id* | account_id* | setting_key* | setting_value* | created_at* | updated_at* |
|-----|-------------|--------------|----------------|-------------|-------------|
| *Auto increment* | *Foreign key* | *Setting name* | *Setting value* | *Auto timestamp* | *Auto timestamp* |

---

## Table: tenants
**Purpose:** Multi-tenant support

| id* | name | domain | subdomain | settings* | is_active* | subscription_tier* | max_users* | created_at* | updated_at* |
|-----|------|--------|-----------|-----------|------------|-------------------|------------|-------------|-------------|
| *System UUID* | Tenant Name | Domain Name | Subdomain | *JSON config* | *Boolean status* | *Tier level* | *User limit* | *Auto timestamp* | *Auto timestamp* |

---

## Table: users
**Purpose:** User authentication and management

| id* | tenant_id* | email | password_hash* | first_name | last_name | role* | is_active* | is_verified* | two_factor_enabled* | last_login* | login_attempts* | locked_until* | created_at* | updated_at* |
|-----|------------|-------|----------------|------------|-----------|-------|------------|--------------|-------------------|-------------|----------------|---------------|-------------|-------------|
| *System UUID* | *Foreign key* | Email Address | *Hashed password* | First Name | Last Name | *User role* | *Boolean status* | *Boolean status* | *Boolean setting* | *Login timestamp* | *Attempt counter* | *Lock timestamp* | *Auto timestamp* | *Auto timestamp* |

---

## Table: auth_tokens
**Purpose:** JWT authentication tokens

| id* | user_id* | token_type* | token_hash* | expires_at* | is_revoked* | created_at* |
|-----|----------|-------------|-------------|-------------|-------------|-------------|
| *System UUID* | *Foreign key* | *Token type* | *Hashed token* | *Expiry time* | *Boolean status* | *Auto timestamp* |

---

## Table: two_factor_codes
**Purpose:** Two-factor authentication codes

| id* | user_id* | code* | purpose* | expires_at* | is_used* | attempts* | created_at* |
|-----|----------|-------|----------|-------------|----------|-----------|-------------|
| *System UUID* | *Foreign key* | *2FA code* | *Code purpose* | *Expiry time* | *Boolean status* | *Attempt counter* | *Auto timestamp* |

---

## Table: audit_logs
**Purpose:** Security audit logging

| id* | tenant_id* | user_id* | action* | resource* | ip_address* | user_agent* | details* | timestamp* |
|-----|------------|----------|---------|-----------|-------------|-------------|----------|------------|
| *System UUID* | *Foreign key* | *Foreign key* | *Action type* | *Resource type* | *IP address* | *Browser info* | *JSON details* | *Auto timestamp* |

---

## Table: performance_metrics
**Purpose:** Vendor performance tracking

| id* | vendor_id* | lead_id* | metric_type* | metric_value* | timestamp* |
|-----|------------|----------|--------------|---------------|------------|
| *System UUID* | *Foreign key* | *Foreign key* | *Metric type* | *Calculated value* | *Auto timestamp* |

---

## Table: feedback
**Purpose:** Customer feedback on services

| id* | lead_id* | vendor_id* | rating | comments | feedback_type* | submitted_at* |
|-----|----------|------------|--------|----------|----------------|---------------|
| *System UUID* | *Foreign key* | *Foreign key* | How Would You Rate Us? | Your Feedback | *Feedback category* | *Auto timestamp* |

**Field Mappings:**
- rating → GHL Custom Field: "How Would You Rate Us?" (ID: W7cAoRsRq5k9o7ws17Vw)
- comments → GHL Custom Field: "Your Feedback" (ID: sedQ09cOeF9GkzxpcyJU)

---

## Table: leads
**Purpose:** Customer leads and service requests

| id* | account_id* | ghl_contact_id | ghl_opportunity_id* | customer_name | customer_email | customer_phone | primary_service_category* | specific_service_requested | customer_zip_code | service_county* | service_state* | vendor_id* | assigned_at* | status* | priority* | source* | service_details* | created_at* | updated_at* | service_zip_code | service_city* | specific_services* | service_complexity* | estimated_duration* | requires_emergency_response* | classification_confidence* | classification_reasoning* |
|-----|-------------|----------------|-------------------|---------------|----------------|----------------|---------------------------|---------------------------|-------------------|----------------|----------------|------------|-------------|---------|-----------|---------|------------------|-------------|-------------|------------------|---------------|-------------------|--------------------|--------------------|-----------------------------|---------------------------|---------------------------|
| *System UUID* | *Foreign key* | GHL Contact ID | *System generated* | firstName + lastName | email | phone | *Service classification* | specific_service_needed | zip_code_of_service | *ZIP→County conversion* | *ZIP→State conversion* | *Assigned vendor* | *Assignment time* | *Lead status* | *Priority level* | *Lead source* | *JSON form data* | *Auto timestamp* | *Auto timestamp* | zip_code_of_service | *Derived from ZIP* | *JSON services* | *Complexity level* | *Duration estimate* | *Emergency flag* | *AI confidence* | *AI reasoning* |

**Field Mappings:**
- customer_name → Form fields: firstName, lastName
- customer_email → Form field: email
- customer_phone → Form field: phone
- specific_service_requested → GHL Custom Field: "Specific Service Needed" (ID: FT85QGi0tBq1AfVGNJ9v)
- customer_zip_code → GHL Custom Field: "Zip Code of Service" (ID: y3Xo7qsFEQumoFugTeCq)
- service_zip_code → GHL Custom Field: "Zip Code of Service" (ID: y3Xo7qsFEQumoFugTeCq)

---

## Table: vendors
**Purpose:** Service provider information and routing data

| id* | account_id* | ghl_contact_id | ghl_user_id | name | email | phone | company_name | service_categories* | services_offered* | coverage_type* | coverage_states* | coverage_counties* | last_lead_assigned* | lead_close_percentage | status* | taking_new_work | created_at* | updated_at* |
|-----|-------------|----------------|-------------|------|-------|-------|--------------|-------------------|------------------|----------------|------------------|-------------------|-------------------|---------------------|---------|----------------|-------------|-------------|
| *System UUID* | *Foreign key* | GHL Contact ID | GHL User ID | firstName + lastName | email | phone | vendor_company_name | *JSON categories* | *JSON services* | *Coverage type* | *JSON states* | *JSON counties* | *Last assignment* | Lead Close % | *Vendor status* | taking_new_work | *Auto timestamp* | *Auto timestamp* |

**Field Mappings:**
- name → Form fields: firstName, lastName
- email → Form field: email
- phone → Form field: phone
- company_name → Form field: vendor_company_name OR GHL Custom Field: "Vendor Company Name" (ID: JexVrg2VNhnwIX7YlyJV)
- ghl_user_id → GHL Custom Field: "GHL User ID" (ID: HXVNT4y8OynNokWAfO2D)
- lead_close_percentage → GHL Custom Field: "Lead Close %" (ID: OwHQipU7xdrHCpVswtnW)
- taking_new_work → GHL Custom Field: "Taking New Work?" (ID: bTFOs5zXYt85AvDJJUAb)

---

## Key Form Field Mappings (WordPress/Elementor → Database)

### Customer Lead Forms:
- "Your Contact Email?" → email
- "What Zip Code Are You Requesting Service In?" → zip_code_of_service
- "What Specific Service(s) Do You Request?" → specific_service_needed
- "Your Vessel Manufacturer?" → vessel_make
- "Your Vessel Model or Length of Vessel in Feet?" → vessel_model
- "Year of Vessel?" → vessel_year
- "Is The Vessel On a Dock, At a Marina, or On a Trailer?" → vessel_location__slip
- "When Do You Prefer Service?" → desired_timeline
- "Any Special Requests or Other Information?" → special_requests__notes

### Vendor Application Forms:
- "What is Your Company Name?" → vendor_company_name
- "What Main Service Does Your Company Offer?" → services_provided
- "Service Areas" → service_zip_codes
- "Years in Business" → years_in_business

### GHL Custom Field Mappings:
- vessel_make → "Vessel Make" (ID: B0wHr7XBtjkawyP5O6qH)
- vessel_model → "Vessel Model" (ID: FfBSzKytAmjHpgeadINR)
- vessel_year → "Vessel Year" (ID: 8HWqslCRX6hXl6lWYrWZ)
- vessel_length_ft → "Vessel Length (ft)" (ID: er480ND4nXmk5gFO1kWG)
- vessel_location__slip → "Vessel Location / Slip" (ID: 43F7QfjDIM0Zf9AcluWa)
- desired_timeline → "Desired Timeline" (ID: x3eHJ91v180aLs3HidEB)
- special_requests__notes → "Special Requests / Notes" (ID: 16b5tLOqrBbL61IDPbBz)
- budget_range → "Budget Range" (ID: lzPNBivJaiVIh9FEpLbE)
- preferred_contact_method → "Preferred Contact Method" (ID: 3DfFfFktWJtsynpOy6z9)

---

## Data Flow Summary:

1. **Webhook Receipt:** Form data arrives at `/api/v1/webhooks/elementor/{form_identifier}`
2. **Field Normalization:** WordPress field names → Standard field names
3. **Service Classification:** Direct mapping to service categories (no AI)
4. **Field Mapping:** Standard names → GHL field names
5. **GHL Payload Creation:** Custom fields array built with proper IDs
6. **Database Storage:** Mapped fields stored in appropriate table columns
7. **Vendor Routing:** System uses service_category, zip_code for vendor matching

**System Fields (marked with *):** Generated by application logic, timestamps, calculations, foreign keys, status tracking
**Mapped Fields (no marking):** Come from form submissions or GHL custom field synchronization

---

*Generated: 2025-07-09*
*Database: smart_lead_router.db*
*System: Lead Router Pro*
