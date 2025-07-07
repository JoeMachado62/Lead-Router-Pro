CREATE TABLE leads (
                    id TEXT PRIMARY KEY,
                    account_id TEXT,
                    vendor_id TEXT,
                    ghl_contact_id TEXT, 
                    service_category TEXT,
                    customer_name TEXT,
                    customer_email TEXT,
                    customer_phone TEXT,
                    service_details TEXT DEFAULT '{}',
                    estimated_value REAL DEFAULT 0,
                    priority_score REAL DEFAULT 0,
                    status TEXT DEFAULT 'new', 
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, ghl_opportunity_id TEXT, priority TEXT DEFAULT 'normal', source TEXT DEFAULT 'normal', service_zip_code TEXT, service_city TEXT, service_state TEXT, service_county TEXT, specific_services TEXT DEFAULT '[]', service_complexity TEXT DEFAULT 'simple', estimated_duration TEXT DEFAULT 'medium', requires_emergency_response BOOLEAN DEFAULT 0, classification_confidence REAL DEFAULT 0.0, classification_reasoning TEXT,
                    FOREIGN KEY (account_id) REFERENCES accounts (id),
                    FOREIGN KEY (vendor_id) REFERENCES vendors (id)
                );
CREATE TABLE vendors (
                    id TEXT PRIMARY KEY,
                    account_id TEXT,
                    name TEXT NOT NULL,
                    company_name TEXT,
                    email TEXT, /* Consider UNIQUE constraint if email must be unique per account or globally */
                    phone TEXT,
                    ghl_contact_id TEXT UNIQUE, 
                    ghl_user_id TEXT UNIQUE,    
                    services_provided TEXT DEFAULT '[]',
                    service_areas TEXT DEFAULT '[]',
                    status TEXT DEFAULT 'pending', 
                    taking_new_work BOOLEAN DEFAULT 1,
                    performance_score REAL DEFAULT 0.8,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, service_coverage_type TEXT DEFAULT 'zip', service_states TEXT DEFAULT '[]', service_counties TEXT DEFAULT '[]', last_lead_assigned TIMESTAMP, lead_close_percentage REAL DEFAULT 0.0,
                    FOREIGN KEY (account_id) REFERENCES accounts (id)
                );
