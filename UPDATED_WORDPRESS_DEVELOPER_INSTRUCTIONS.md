# Updated WordPress Developer Instructions

## ⚠️ CRITICAL CHANGES FROM PREVIOUS INSTRUCTIONS

The webhook system has been **significantly updated** to fix payload processing issues. The main changes are:

### 1. **Custom Fields Now Use Array Format**
- The system now properly processes custom fields using GoHighLevel's official `customFields` array format
- **Field names remain exactly the same** - no changes needed to your Elementor forms
- The middleware automatically converts individual field properties to the proper array format

### 2. **All Custom Fields Are Now Mapped**
- All custom fields from your previous instructions are confirmed to exist in the system
- Field validation is now more robust with proper error handling

### 3. **New Vendor Application Forms Added**
- Additional specialized vendor forms have been added to the system
- More comprehensive vendor onboarding process

---

# WordPress Developer Testing Guide - Lead Forms (UPDATED)

## Server Configuration
- **Testing Server**: `http://71.208.153.160:8000`
- **Webhook Base URL**: `http://71.208.153.160:8000/api/v1/webhooks/elementor/`

## 🛥️ CLIENT LEAD FORMS

### Form 1: Ceramic Coating Request
**Webhook URL**: `http://71.208.153.160:8000/api/v1/webhooks/elementor/ceramic_coating_request`

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
| **Hidden Field - Form Source** | `source` | No | **Default Value**: "Ceramic Coating Request Form (DSP)" |

### Form 2: Emergency Tow Request
**Webhook URL**: `http://71.208.153.160:8000/api/v1/webhooks/elementor/emergency_tow_request`

| Elementor Field Label | Custom ID (EXACT) | Required | Sample Value |
|----------------------|-------------------|----------|--------------|
| First Name | `firstName` | ✅ Yes | "Sarah" |
| Last Name | `lastName` | ✅ Yes | "Johnson" |
| Email Address | `email` | ✅ Yes | "sarah.j@gmail.com" |
| Phone Number | `phone` | ✅ Yes | "555-987-6543" |
| Current Location | `vessel_location__slip` | No | "Anchored near Stiltsville" |
| What Happened? | `special_requests__notes` | No | "Engine overheating, need immediate tow" |
| Vessel Make | `vessel_make` | No | "Boston Whaler" |
| Vessel Length | `vessel_length_ft` | No | "28" |
| Zip Code of Service | `zip_code_of_service` | No | "33149" |
| Preferred Contact Method | `preferred_contact_method` | No | "Phone Call" |
| **Hidden Field - Form Source** | `source` | No | **Default Value**: "Emergency Tow Request Form (DSP)" |

### Form 3: Yacht Delivery Request
**Webhook URL**: `http://71.208.153.160:8000/api/v1/webhooks/elementor/yacht_delivery_request`

| Elementor Field Label | Custom ID (EXACT) | Required | Sample Value |
|----------------------|-------------------|----------|--------------|
| First Name | `firstName` | ✅ Yes | "Michael" |
| Last Name | `lastName` | ✅ Yes | "Davis" |
| Email Address | `email` | ✅ Yes | "mdavis@yachtowner.com" |
| Phone Number | `phone` | ✅ Yes | "555-456-7890" |
| Vessel Make | `vessel_make` | No | "Azimut" |
| Vessel Model | `vessel_model` | No | "58 Flybridge" |
| Vessel Length (ft) | `vessel_length_ft` | No | "58" |
| Pickup Location | `vessel_location__slip` | No | "Fort Lauderdale Marine Center" |
| Delivery Zip Code | `zip_code_of_service` | No | "33139" |
| Timeline Needed | `desired_timeline` | No | "Next month" |
| Budget Range | `budget_range` | No | "$2000-$4000" |
| Special Instructions | `special_requests__notes` | No | "White glove service required" |
| **Hidden Field - Form Source** | `source` | No | **Default Value**: "Yacht Delivery Request Form (DSP)" |

### Form 4: Boat Maintenance Request
**Webhook URL**: `http://71.208.153.160:8000/api/v1/webhooks/elementor/boat_maintenance_request`

| Elementor Field Label | Custom ID (EXACT) | Required | Sample Value |
|----------------------|-------------------|----------|--------------|
| First Name | `firstName` | ✅ Yes | "Lisa" |
| Last Name | `lastName` | ✅ Yes | "Wilson" |
| Email Address | `email` | ✅ Yes | "lisa.wilson@email.com" |
| Phone Number | `phone` | ✅ Yes | "555-234-5678" |
| Vessel Make | `vessel_make` | No | "Beneteau" |
| Vessel Model | `vessel_model` | No | "Oceanis 40" |
| Vessel Year | `vessel_year` | No | "2019" |
| Service Needed | `specific_service_needed` | No | "Annual maintenance and bottom cleaning" |
| Location/Marina | `vessel_location__slip` | No | "Coconut Grove Marina" |
| Zip Code of Service | `zip_code_of_service` | No | "33133" |
| Timeline | `desired_timeline` | No | "Next 2 weeks" |
| Budget Range | `budget_range` | No | "$1500-$2500" |
| **Hidden Field - Form Source** | `source` | No | **Default Value**: "Boat Maintenance Request Form (DSP)" |

---

# Vendor Application Forms (UPDATED)

## 🏢 VENDOR APPLICATION FORMS

### Form 1: General Vendor Application
**Webhook URL**: `http://71.208.153.160:8000/api/v1/webhooks/elementor/vendor_application_general`

| Elementor Field Label | Custom ID (EXACT) | Required | Sample Value |
|----------------------|-------------------|----------|--------------|
| **Contact Information** |
| First Name | `firstName` | ✅ Yes | "Robert" |
| Last Name | `lastName` | ✅ Yes | "Martinez" |
| Email Address | `email` | ✅ Yes | "rob@marinepro.com" |
| Phone Number | `phone` | ✅ Yes | "555-234-5678" |
| **Business Information** |
| Business/Company Name | `vendor_company_name` | ✅ Yes | "Marine Pro Services LLC" |
| DBA Name (if different) | `dba` | No | "Marine Pro" |
| Years in Business | `years_in_business` | No | "8" |
| Business Website | `website_url` | No | "https://marinepro.com" |
| **Service Details** |
| Services You Provide | `services_provided` | No | "Boat maintenance, detailing, minor repairs, bottom cleaning" |
| Primary Service Category | `primary_service_category` | No | "Boat Maintenance" |
| Service Area Zip Codes | `service_zip_codes` | No | "33101, 33139, 33154, 33109, 33140" |
| **Business Credentials** |
| Licenses & Certifications | `licences__certifications` | No | "Florida Marine Contractor License #FL123456, Insured & Bonded" |
| Insurance Coverage | `insurance_coverage` | No | "General Liability $1M, Professional Liability $500K" |
| About Your Company | `about_your_company` | No | "Family-owned marine service company serving South Florida for 8 years" |
| Google Business Profile URL | `reviews__google_profile_url` | No | "https://g.page/marinepro" |
| **Availability** |
| Currently Taking New Work? | `taking_new_work` | No | "Yes" |
| Preferred Contact Method | `vendor_preferred_contact_method` | No | "Phone Call" |
| **Hidden Field - Form Source** | `source` | No | **Default Value**: "General Vendor Application Form (DSP)" |

### Form 2: Marine Mechanic Application
**Webhook URL**: `http://71.208.153.160:8000/api/v1/webhooks/elementor/vendor_application_marine_mechanic`

| Elementor Field Label | Custom ID (EXACT) | Required | Sample Value |
|----------------------|-------------------|----------|--------------|
| **Contact Information** |
| First Name | `firstName` | ✅ Yes | "Carlos" |
| Last Name | `lastName` | ✅ Yes | "Rodriguez" |
| Email Address | `email` | ✅ Yes | "carlos@engineexperts.com" |
| Phone Number | `phone` | ✅ Yes | "555-345-6789" |
| **Business Information** |
| Business/Company Name | `vendor_company_name` | ✅ Yes | "Engine Experts Marine LLC" |
| DBA Name | `dba` | No | "Engine Experts" |
| Years in Business | `years_in_business` | No | "15" |
| Business Website | `website_url` | No | "https://engineexperts.com" |
| **Specialization** |
| Engine Services Provided | `services_provided` | No | "Inboard/Outboard repair, Generator service, Diagnostics, Winterization" |
| Primary Service Category | `primary_service_category` | No | "Engines and Generators" |
| Service Area Zip Codes | `service_zip_codes` | No | "33101, 33139, 33154, 33109" |
| **Certifications** |
| Engine Certifications | `licences__certifications` | No | "Mercury Certified Technician, Volvo Penta Certified, Cummins Authorized" |
| Insurance Coverage | `insurance_coverage` | No | "General Liability $2M, Professional Liability $1M" |
| Training & Education | `training__education_type` | No | "Marine Technology Institute Graduate, 15+ years experience" |
| **Business Profile** |
| About Your Company | `about_your_company` | No | "Specialized marine engine repair with factory-trained technicians" |
| Google Business Profile | `reviews__google_profile_url` | No | "https://g.page/engineexperts" |
| Currently Taking New Work? | `taking_new_work` | No | "Yes" |
| Preferred Contact Method | `vendor_preferred_contact_method` | No | "Email" |
| **Hidden Field - Form Source** | `source` | No | **Default Value**: "Marine Mechanic Application Form (DSP)" |

### Form 3: Boat Detailing Specialist
**Webhook URL**: `http://71.208.153.160:8000/api/v1/webhooks/elementor/vendor_application_detailing_specialist`

| Elementor Field Label | Custom ID (EXACT) | Required | Sample Value |
|----------------------|-------------------|----------|--------------|
| **Contact Information** |
| First Name | `firstName` | ✅ Yes | "Maria" |
| Last Name | `lastName` | ✅ Yes | "Santos" |
| Email Address | `email` | ✅ Yes | "maria@pristineyachts.com" |
| Phone Number | `phone` | ✅ Yes | "555-456-7890" |
| **Business Information** |
| Business/Company Name | `vendor_company_name` | ✅ Yes | "Pristine Yacht Services" |
| Years in Business | `years_in_business` | No | "6" |
| Business Website | `website_url` | No | "https://pristineyachts.com" |
| **Service Specialization** |
| Detailing Services | `services_provided` | No | "Yacht detailing, ceramic coating, waxing, interior cleaning" |
| Primary Service Category | `primary_service_category` | No | "Boat Maintenance" |
| Service Area Zip Codes | `service_zip_codes` | No | "33139, 33154, 33109, 33140, 33141" |
| **Credentials & Experience** |
| Certifications | `licences__certifications` | No | "Certified Marine Detailer, Ceramic Pro Certified Installer" |
| Insurance Coverage | `insurance_coverage` | No | "General Liability $1M, Bonded" |
| About Your Services | `about_your_company` | No | "Premium yacht detailing with eco-friendly products and ceramic protection" |
| **Availability** |
| Google Business Profile | `reviews__google_profile_url` | No | "https://g.page/pristineyachts" |
| Currently Taking New Work? | `taking_new_work` | No | "Yes" |
| Preferred Contact Method | `vendor_preferred_contact_method` | No | "Text Message" |
| **Hidden Field - Form Source** | `source` | No | **Default Value**: "Detailing Specialist Application Form (DSP)" |

---

## 🧪 TESTING INSTRUCTIONS

### Step 1: Test Server Connectivity First
```bash
# Test if server is running
curl http://71.208.153.160:8000/health

# Test webhook system
curl http://71.208.153.160:8000/api/v1/webhooks/health

# Check supported forms
curl http://71.208.153.160:8000/api/v1/webhooks/supported-forms
```

### Step 2: Test Each Form with cURL

#### Client Lead Test (Ceramic Coating):
```bash
curl -X POST http://71.208.153.160:8000/api/v1/webhooks/elementor/ceramic_coating_request \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "John",
    "lastName": "Smith", 
    "email": "john.smith@test.com",
    "phone": "555-123-4567",
    "vessel_make": "Sea Ray",
    "vessel_model": "Sundancer",
    "vessel_year": "2020",
    "vessel_length_ft": "35",
    "specific_service_needed": "Ceramic coating",
    "zip_code_of_service": "33139",
    "budget_range": "$3000-$5000",
    "source": "Ceramic Coating Request Form (DSP)"
  }'
```

#### Vendor Application Test (General):
```bash
curl -X POST http://71.208.153.160:8000/api/v1/webhooks/elementor/vendor_application_general \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "Robert",
    "lastName": "Martinez",
    "email": "rob@marinepro.com",
    "phone": "555-234-5678",
    "vendor_company_name": "Marine Pro Services LLC",
    "services_provided": "Boat maintenance, detailing, minor repairs",
    "years_in_business": "8",
    "service_zip_codes": "33101, 33139, 33154",
    "insurance_coverage": "General Liability $1M",
    "source": "General Vendor Application Form (DSP)"
  }'
```

### Expected Successful Response:
```json
{
  "status": "success",
  "message": "Webhook processed successfully. GHL contact [ID] created.",
  "contact_id": "contact_xyz123",
  "action": "created",
  "form_type": "client_lead",
  "processing_time_seconds": 1.234,
  "validation_warnings": []
}
```

---

## 🚨 CRITICAL REQUIREMENTS (UNCHANGED)

### 1. **Exact Custom ID Matching**
- Custom IDs must match **EXACTLY** (case-sensitive)
- No spaces, special characters except underscores
- Examples: ✅ `firstName` ❌ `first_name` ❌ `FirstName`

### 2. **Required Fields**
- **All forms**: `email` (absolute minimum)
- **Client leads**: `firstName`, `lastName`, `email`
- **Vendor applications**: `firstName`, `lastName`, `email`, `vendor_company_name`

### 3. **Hidden Source Field**
- Always include hidden field with Custom ID: `source`
- Set default value exactly as shown in tables
- This helps track which form generated the lead

### 4. **Webhook URL Format**
- Must start with: `http://71.208.153.160:8000/api/v1/webhooks/elementor/`
- Must end with exact form identifier (no spaces, lowercase with underscores)

---

## ✅ SUCCESS CRITERIA

- ✅ Webhook responds with 200 status
- ✅ Returns success JSON with `contact_id`
- ✅ No validation errors in response
- ✅ Server logs show successful processing
- ✅ GHL contact created/updated with all custom fields

---

## 🔧 WHAT'S DIFFERENT FROM PREVIOUS INSTRUCTIONS

### ✅ **No Changes Required to Your Forms**
- All field names remain exactly the same
- All webhook URLs remain the same
- All validation rules remain the same

### ✅ **Improved Backend Processing**
- Custom fields now properly processed using GHL's official format
- Better error handling and validation
- More robust field mapping system
- Enhanced logging for troubleshooting

### ✅ **New Features Added**
- Additional vendor application forms
- Better form validation
- Improved response format with warnings
- Enhanced debugging capabilities

**The system is now significantly more reliable and should process all form submissions successfully!**
