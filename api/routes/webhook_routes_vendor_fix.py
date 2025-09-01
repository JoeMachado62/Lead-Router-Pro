def create_vendor_from_payload(contact_id: str, elementor_payload: dict, 
                              ghl_response: dict, account_id: str) -> str:
    """
    Create vendor record using data directly from the normalized payload
    instead of relying solely on GHL field extraction
    """
    try:
        # Extract vendor data from the ORIGINAL normalized payload
        vendor_first_name = elementor_payload.get('firstName', '')
        vendor_last_name = elementor_payload.get('lastName', '')
        vendor_email = elementor_payload.get('email', '')
        vendor_phone = elementor_payload.get('phone', '')
        
        # Get vendor company name from multiple possible sources
        vendor_company_name = (
            elementor_payload.get('vendor_company_name') or
            elementor_payload.get('companyName') or
            elementor_payload.get('company_name') or
            ghl_response.get('companyName', '')
        )
        
        # Get services from payload
        services_provided = elementor_payload.get('services_provided', '')
        if services_provided:
            # Parse services into categories
            services_list = [s.strip() for s in services_provided.split(',')]
            primary_service = services_list[0] if services_list else "General Services"
            secondary_services = services_list[1:] if len(services_list) > 1 else []
        else:
            primary_service = "General Services"
            secondary_services = []
        
        # Get coverage areas from payload
        service_zip_codes = (
            elementor_payload.get('service_zip_codes') or
            elementor_payload.get('service_areas') or
            elementor_payload.get('Service Areas', '')
        )
        
        # Convert ZIP codes to counties
        if service_zip_codes:
            from api.services.location_service import location_service
            counties = []
            states = set()
            
            zip_list = [z.strip() for z in str(service_zip_codes).split(',')]
            for zip_code in zip_list:
                location = location_service.zip_to_location(zip_code)
                if location.get('county') and location.get('state'):
                    counties.append(f"{location['county']}, {location['state']}")
                    states.add(location['state'])
        else:
            # Don't default to Miami - leave empty
            counties = []
            states = []
        
        # Create vendor record with properly mapped data
        vendor_data = {
            'account_id': account_id,
            'name': f"{vendor_first_name} {vendor_last_name}".strip(),
            'email': vendor_email,
            'phone': vendor_phone,
            'company_name': vendor_company_name,  # This was missing!
            'ghl_contact_id': contact_id,
            'ghl_user_id': ghl_response.get('id', ''),
            'service_categories': json.dumps([primary_service] + secondary_services),
            'services_offered': json.dumps(services_list if services_provided else []),
            'coverage_type': 'county' if counties else 'zip',
            'coverage_states': json.dumps(list(states)),
            'coverage_counties': json.dumps(counties),
            'status': 'active',
            'taking_new_work': 'Yes'  # Default for new vendors
        }
        
        # Use the proper database method
        vendor_id = simple_db_instance.create_vendor(
            account_id=vendor_data['account_id'],
            name=vendor_data['name'],
            email=vendor_data['email'],
            company_name=vendor_data['company_name'],
            phone=vendor_data['phone'],
            ghl_contact_id=vendor_data['ghl_contact_id'],
            status=vendor_data['status'],
            services_provided=vendor_data['services_offered'],
            service_areas=json.dumps(zip_list) if service_zip_codes else '[]'
        )
        
        logger.info(f"✅ Created vendor record with company: {vendor_company_name}")
        return vendor_id
        
    except Exception as e:
        logger.error(f"❌ Failed to create vendor record: {e}")
        raise