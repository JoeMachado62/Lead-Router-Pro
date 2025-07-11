# Smart Lead Router Database Structure and Field Mappings

**Legend:**
- `*` = System-generated field
- No marking = Field mapped from forms or GoHighLevel custom fields
- `⚠️` = Known issues requiring fixes

**Last Updated:** 2025-07-11 (Based on production analysis and debugging session)

---

## Table: accounts
**Purpose:** Company/client accounts in the system

| id* | ghl_location_id | company_name | industry | subscription_tier* | settings* | ghl_private_token | created_at* | updated_at* |
|-----|-----------------|--------------|----------|-------------------|-----------|------------------|-------------|-------------|
| *System UUID* | GHL Location ID | Company Name | Industry Type | *Default: 'starter'* | *JSON config* | GHL API Token | *Auto timestamp* | *Auto timestamp* |

---

## Table: activity_log
**Purpose:** System activity and audit trail

| id* | event_type* | event_data* | lead_id* | vendor_id* | account_id* | success* | error_message* | timestamp* |
|-----|-------------|-------------|----------|------------|-------------|----------|----------------|------------|
| *System UUID* | *Event type* | *JSON data* | *Lead UUID* | *Vendor UUID* | *Account UUID* | *Boolean result* | *Error details* | *Auto timestamp* |

**Recent Updates:**
- Added `lead_id`, `vendor_id`, `account_id` fields to fix logging errors
- Standardized `event_data` field (was `event_data_json`)

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

## Table: leads ⚠️
**Purpose:** Customer leads and service requests  
**Schema:** 27 columns total (verified in production debugging 2025-07-11)

### Core Lead Information
| Field | Type | Purpose | Status |
|-------|------|---------|--------|
| id* | TEXT PRIMARY KEY | Lead identifier | ✅ |
| account_id* | TEXT | Account reference | ✅ |
| ghl_contact_id | TEXT | GHL Contact ID | ✅ |
| ghl_opportunity_id* | TEXT | GHL Opportunity ID | ✅ |

### Customer Contact Data
| Field | Type | Source/Mapping | Status |
|-------|------|----------------|--------|
| customer_name | TEXT | firstName + lastName | ✅ |
| customer_email | TEXT | email field | ✅ |
| customer_phone | TEXT | phone field | ✅ |

### Service Classification ⚠️
| Field | Type | Source/Mapping | Status |
|-------|------|----------------|--------|
| primary_service_category* | TEXT NOT NULL | Form identifier mapping | ⚠️ **CLASSIFICATION ISSUE** |
| specific_service_category | TEXT | specific_service_needed | ✅ |

### Geographic Data
| Field | Type | Source/Mapping | Status |
|-------|------|----------------|--------|
| customer_zip_code | TEXT | zip_code_of_service | ✅ |
| service_county* | TEXT | ZIP→County conversion | ✅ |
| service_state* | TEXT | ZIP→State conversion | ✅ |
| service_zip_code | TEXT | zip_code_of_service (duplicate) | ✅ |
| service_city* | TEXT | ZIP→City conversion | ✅ |

### Lead Assignment ⚠️
| Field | Type | Purpose | Status |
|-------|------|---------|--------|
| vendor_id* | TEXT | Assigned vendor FK | ⚠️ **ROUTING BLOCKED** |
| assigned_at* | TIMESTAMP | Assignment time | ⚠️ **ROUTING BLOCKED** |
| status* | TEXT DEFAULT 'unassigned' | Lead status | ⚠️ **ROUTING BLOCKED** |

### Lead Management
| Field | Type | Purpose | Status |
|-------|------|---------|--------|
| priority* | TEXT DEFAULT 'normal' | Priority level | ✅ |
| source* | TEXT | Lead source identifier | ✅ |
| service_details* | TEXT | Complete form data JSON | ✅ |
| created_at* | TIMESTAMP | Creation time | ✅ |
| updated_at* | TIMESTAMP | Update time | ✅ |

### Classification Metadata
| Field | Type | Purpose | Status |
|-------|------|---------|--------|
| service_complexity* | TEXT DEFAULT 'simple' | Complexity level | ✅ |
| estimated_duration* | TEXT DEFAULT 'medium' | Duration estimate | ✅ |
| requires_emergency_response* | BOOLEAN DEFAULT '0' | Emergency flag | ✅ |
| classification_confidence* | REAL DEFAULT '0.0' | AI confidence score | ✅ |
| classification_reasoning* | TEXT | AI reasoning | ✅ |

**Critical Issues Identified (2025-07-11 debugging session):**
- ⚠️ **Service Classification Error**: `engines_generators` form maps to "Boater Resources" instead of "Engines and Generators"
- ⚠️ **Lead Creation Failure**: "cannot access local variable 'lead_id'" error in background task
- ⚠️ **Database Insert Error**: Previously had "28 values for 27 columns" (fixed during session)
- ⚠️ **Vendor Routing Blocked**: Cannot assign vendors due to classification and database storage failures

**Field Mappings:**
- customer_name → Form fields: firstName, lastName
- customer_email → Form field: email  
- customer_phone → Form field: phone
- specific_service_category → GHL Custom Field: "Specific Service Needed" (ID: FT85QGi0tBq1AfVGNJ9v)
- customer_zip_code → GHL Custom Field: "Zip Code of Service" (ID: y3Xo7qsFEQumoFugTeCq)
- service_zip_code → GHL Custom Field: "Zip Code of Service" (ID: y3Xo7qsFEQumoFugTeCq) [duplicate]

---

## Table: vendors
**Purpose:** Service provider information and routing data

### Core Vendor Information
| Field | Type | Source/Mapping | Status |
|-------|------|----------------|--------|
| id* | TEXT PRIMARY KEY | System UUID | ✅ |
| account_id* | TEXT | Foreign key to accounts | ✅ |
| ghl_contact_id | TEXT | GHL Contact ID | ✅ |
| ghl_user_id | TEXT | GHL User ID for assignment | ✅ |

### Contact Information  
| Field | Type | Source/Mapping | Status |
|-------|------|----------------|--------|
| name | TEXT | firstName + lastName | ✅ |
| email | TEXT | email field | ✅ |
| phone | TEXT | phone field | ✅ |
| company_name | TEXT | vendor_company_name | ✅ |

### Service Capabilities (Critical for Lead Matching)
| Field | Type | Purpose | Status |
|-------|------|---------|--------|
| service_categories* | TEXT | JSON: ["Marine Systems", "Engines and Generators"] | ✅ |
| services_offered* | TEXT | JSON: ["AC Service", "Engine Repair"] | ✅ |

### Geographic Coverage (Critical for Lead Matching)
| Field | Type | Purpose | Status |
|-------|------|---------|--------|
| coverage_type* | TEXT DEFAULT 'zip' | zip, county, state, national | ✅ |
| coverage_states* | TEXT | JSON: ["FL", "GA"] | ✅ |
| coverage_counties* | TEXT | JSON: ["Miami-Dade", "Broward"] | ✅ |

### Performance & Availability
| Field | Type | Source/Mapping | Status |
|-------|------|----------------|--------|
| last_lead_assigned* | TIMESTAMP | Performance tracking | ✅ |
| lead_close_percentage | REAL | GHL Custom Field (ID: OwHQipU7xdrHCpVswtnW) | ✅ |
| status* | TEXT DEFAULT 'pending' | pending, active, inactive | ✅ |
| taking_new_work | BOOLEAN | GHL Custom Field (ID: bTFOs5zXYt85AvDJJUAb) | ✅ |

### System Fields
| Field | Type | Purpose | Status |
|-------|------|---------|--------|
| created_at* | TIMESTAMP | Auto timestamp | ✅ |
| updated_at* | TIMESTAMP | Auto timestamp | ✅ |

**Lead-to-Vendor Matching Logic (Critical for Routing):**
```sql
-- Service Category Match
leads.primary_service_category IN vendors.service_categories (JSON array)

-- Geographic Match (ZIP-level preferred)
leads.customer_zip_code IN vendors.coverage_zip_codes (JSON array)
OR 
leads.service_county IN vendors.coverage_counties (JSON array)

-- Availability Filter
vendors.status = 'active' 
AND vendors.taking_new_work = TRUE
```

**Field Mappings:**
- name → Form fields: firstName, lastName
- email → Form field: email
- phone → Form field: phone
- company_name → Form field: vendor_company_name OR GHL Custom Field: "Vendor Company Name" (ID: JexVrg2VNhnwIX7YlyJV)
- ghl_user_id → GHL Custom Field: "GHL User ID" (ID: HXVNT4y8OynNokWAfO2D)
- lead_close_percentage → GHL Custom Field: "Lead Close %" (ID: OwHQipU7xdrHCpVswtnW)
- taking_new_work → GHL Custom Field: "Taking New Work?" (ID: bTFOs5zXYt85AvDJJUAb)

---

## Service Classification Issues ⚠️

**Problem Identified:** Form identifier `engines_generators` incorrectly maps to "Boater Resources"  
**Expected:** Should map to "Engines and Generators"  
**Location:** `api/routes/webhook_routes.py` - `DOCKSIDE_PROS_SERVICES` dictionary  
**Impact:** Causes vendor matching to fail (no vendors for "Boater Resources" in Miami-Dade)

**Missing Service Mappings:**
```python
DOCKSIDE_PROS_SERVICES = {
    # MISSING ENTRIES IDENTIFIED:
    "engines_generators": "Engines and Generators",  # ← CRITICAL FIX NEEDED
    "outboard_engine_service": "Engines and Generators",
    "generator_service": "Engines and Generators",
    "marine_systems": "Marine Systems",
    "boat_maintenance": "Boat Maintenance",
    # ... existing mappings
}
```

**Evidence from Production Logs:**
```
🎯 Default service mapping: engines_generators → Boater Resources  # ← WRONG
# Should be:
🎯 Direct service mapping: engines_generators → Engines and Generators  # ← CORRECT
```

---

## Database Operation Issues ⚠️

**Background Task Variable Scope Error:**
- **Function:** `trigger_clean_lead_routing_workflow()`
- **Error:** `cannot access local variable 'lead_id' where it is not associated with a value`
- **Fix Required:** Initialize `lead_id = None` at function start

**Previous Schema Issues (Resolved):**
- "28 values for 27 columns" error fixed during debugging session
- Column count now matches INSERT statement placeholders

**Current Status:**
- ✅ GHL contact creation: 100% success rate
- ✅ GHL opportunity creation: Works when background task succeeds  
- ❌ Lead database storage: Fails due to variable scope error
- ❌ Vendor routing: Blocked by classification and storage failures