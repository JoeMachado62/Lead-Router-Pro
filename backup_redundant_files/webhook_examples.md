# Webhook Examples for External Integration

## Server URLs

### Local Development
- **Base URL**: `http://127.0.0.1:8000`
- **Webhook Base**: `http://127.0.0.1:8000/api/v1/webhooks/elementor`

### Production/External Server
- **Base URL**: `http://71.208.153.160:8000`
- **Webhook Base**: `http://71.208.153.160:8000/api/v1/webhooks/elementor`

## Webhook Endpoints

### Client Lead Forms

#### 1. Ceramic Coating Request
```
POST http://71.208.153.160:8000/api/v1/webhooks/elementor/ceramic_coating_request
```

**Example Payload:**
```json
{
  "firstName": "Jennifer",
  "lastName": "Thompson",
  "email": "jennifer.thompson@email.com",
  "phone": "555-123-4567",
  "vessel_make": "Azimut",
  "vessel_model": "55 Flybridge",
  "vessel_year": "2021",
  "vessel_length_ft": "55",
  "vessel_location__slip": "Miami Beach Marina - Slip A-15",
  "specific_service_needed": "Premium ceramic coating for new yacht - full hull and superstructure",
  "zip_code_of_service": "33139",
  "desired_timeline": "Within 3 weeks",
  "budget_range": "$5000-$8000",
  "special_requests__notes": "New yacht, looking for the best ceramic protection available. Please provide portfolio of similar work.",
  "preferred_contact_method": "Email"
}
```

#### 2. Boat Maintenance Request
```
POST http://71.208.153.160:8000/api/v1/webhooks/elementor/boat_maintenance_request
```

**Example Payload:**
```json
{
  "firstName": "Michael",
  "lastName": "Rodriguez",
  "email": "mike.rodriguez@gmail.com",
  "phone": "555-987-6543",
  "vessel_make": "Sea Ray",
  "vessel_model": "Sundancer 320",
  "vessel_year": "2018",
  "vessel_length_ft": "32",
  "vessel_location__slip": "Dinner Key Marina - Dock 3, Slip 42",
  "specific_service_needed": "Full boat detailing - hull cleaning, deck wash, interior cleaning",
  "zip_code_of_service": "33133",
  "desired_timeline": "This weekend if possible",
  "budget_range": "$800-$1200",
  "special_requests__notes": "Boat hasn't been detailed in 6 months. Some algae on hull. Interior needs deep cleaning.",
  "preferred_contact_method": "Phone Call"
}
```

#### 3. Emergency Tow Request
```
POST http://71.208.153.160:8000/api/v1/webhooks/elementor/emergency_tow_request
```

**Example Payload:**
```json
{
  "firstName": "Sarah",
  "lastName": "Johnson",
  "email": "sarah.johnson@email.com",
  "phone": "555-911-1234",
  "vessel_make": "Boston Whaler",
  "vessel_model": "Outrage 280",
  "vessel_year": "2019",
  "vessel_length_ft": "28",
  "vessel_location__slip": "Stiltsville - Coordinates: 25.3781° N, 80.3226° W",
  "specific_service_needed": "Emergency tow - engine failure",
  "zip_code_of_service": "33149",
  "desired_timeline": "ASAP - stranded",
  "special_requests__notes": "Engine died suddenly, no power. Two adults and one child on board. Need immediate assistance.",
  "preferred_contact_method": "Phone Call"
}
```

### Vendor Application Forms

#### 1. General Vendor Application
```
POST http://71.208.153.160:8000/api/v1/webhooks/elementor/vendor_application_general
```

**Example Payload:**
```json
{
  "firstName": "Carlos",
  "lastName": "Martinez",
  "email": "carlos@marinemechanics.com",
  "phone": "555-456-7890",
  "vendor_company_name": "Martinez Marine Mechanics",
  "dba": "Marine Mechanics Pro",
  "years_in_business": "12",
  "services_provided": "Engine repair, generator service, electrical systems, fuel system maintenance",
  "primary_service_category": "Engines and Generators",
  "service_zip_codes": "33101, 33139, 33154, 33109, 33140",
  "website_url": "https://marinemechanics.com",
  "licences__certifications": "Marine Engine Technician Certification, Yamaha Certified, Mercury Certified",
  "insurance_coverage": "General Liability $2M, Professional Liability $1M",
  "about_your_company": "Full-service marine engine repair shop with 12 years experience. Specializing in outboard and inboard engines.",
  "reviews__google_profile_url": "https://g.page/marinemechanics",
  "taking_new_work": "Yes",
  "vendor_preferred_contact_method": "Phone Call"
}
```

#### 2. Boat Detailing Specialist
```
POST http://71.208.153.160:8000/api/v1/webhooks/elementor/vendor_application_detailing_specialist
```

**Example Payload:**
```json
{
  "firstName": "Maria",
  "lastName": "Santos",
  "email": "maria.santos@pristineyachts.com",
  "phone": "555-456-7890",
  "vendor_company_name": "Pristine Yacht Services LLC",
  "dba": "Pristine Yachts",
  "years_in_business": "8",
  "services_provided": "Premium yacht detailing, ceramic coating, interior cleaning, waxing, polishing",
  "primary_service_category": "Boat Maintenance",
  "service_zip_codes": "33139, 33154, 33109, 33140, 33141",
  "website_url": "https://pristineyachts.com",
  "licences__certifications": "Certified Marine Detailer, Ceramic Pro Certified Installer, Insured & Bonded",
  "insurance_coverage": "General Liability $1M, Professional Liability $500K, Bonded $250K",
  "about_your_company": "Premium yacht detailing service with 8 years of experience serving luxury yacht owners in Miami-Dade.",
  "reviews__google_profile_url": "https://g.page/pristineyachts",
  "taking_new_work": "Yes",
  "vendor_preferred_contact_method": "Email"
}
```

## WordPress/Elementor Integration

### Form Action URL
Set your Elementor form action to:
```
http://71.208.153.160:8000/api/v1/webhooks/elementor/{form_identifier}
```

### Form Field Mapping
Make sure your form field names match exactly:

**Client Lead Fields:**
- `firstName`, `lastName`, `email`, `phone`
- `vessel_make`, `vessel_model`, `vessel_year`, `vessel_length_ft`
- `vessel_location__slip`, `specific_service_needed`
- `zip_code_of_service`, `desired_timeline`, `budget_range`
- `special_requests__notes`, `preferred_contact_method`

**Vendor Application Fields:**
- `firstName`, `lastName`, `email`, `phone`
- `vendor_company_name`, `dba`, `years_in_business`
- `services_provided`, `primary_service_category`, `service_zip_codes`
- `website_url`, `licences__certifications`, `insurance_coverage`
- `about_your_company`, `reviews__google_profile_url`
- `taking_new_work`, `vendor_preferred_contact_method`

## Expected Response

### Success Response (200)
```json
{
  "status": "success",
  "message": "Webhook processed successfully. GHL contact {contact_id} {action}.",
  "contact_id": "vSpZ6uNu27Nsc6NJAxkz",
  "action": "created",
  "form_type": "client_lead",
  "processing_time_seconds": 0.892,
  "validation_warnings": []
}
```

### Error Response (400/502)
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Testing the External Webhook

### Using cURL
```bash
curl -X POST "http://71.208.153.160:8000/api/v1/webhooks/elementor/ceramic_coating_request" \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "Test",
    "lastName": "Client",
    "email": "test@example.com",
    "phone": "555-123-4567",
    "vessel_make": "Test Boat",
    "vessel_model": "Test Model",
    "vessel_year": "2023",
    "vessel_length_ft": "30",
    "specific_service_needed": "Test ceramic coating",
    "zip_code_of_service": "33139"
  }'
```

### Using Postman
1. **Method**: POST
2. **URL**: `http://71.208.153.160:8000/api/v1/webhooks/elementor/ceramic_coating_request`
3. **Headers**: `Content-Type: application/json`
4. **Body**: Raw JSON with the payload above

## Health Check
Test if the external server is running:
```
GET http://71.208.153.160:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service_name": "Smart Lead Router Pro - Main Application",
  "database_status": "healthy"
}
```

## Security Considerations

1. **HTTPS**: Consider using HTTPS in production
2. **Rate Limiting**: The system has built-in rate limiting
3. **Validation**: All fields are validated before processing
4. **Error Handling**: Comprehensive error handling and logging

## Troubleshooting

### Common Issues:
1. **Connection Refused**: Server not running or firewall blocking
2. **404 Not Found**: Wrong form identifier in URL
3. **400 Bad Request**: Missing required fields or invalid JSON
4. **502 Bad Gateway**: GHL API connection issues

### Debug Steps:
1. Check server health endpoint
2. Verify form identifier matches supported forms
3. Validate JSON payload format
4. Check server logs for detailed error messages
