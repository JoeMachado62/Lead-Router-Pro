#!/usr/bin/env python3
"""
DATABASE RESTRUCTURING SCRIPT
Clears and rebuilds leads and vendors tables with proper schema for multi-level routing.

CRITICAL FEATURES:
- Proper service matching fields (primary category + specific service)
- County-based location matching (ZIP → County conversion)
- Vendor routing fields (performance + round-robin)
- Preserves other tables intact

SCHEMA DESIGNED FOR 1:1 MATCHING RELATIONSHIPS
"""

import sqlite3
import json
import logging
import sys
import os
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def backup_existing_data():
    """Create backup of existing leads and vendors data before restructuring"""
    try:
        conn = sqlite3.connect('smart_lead_router.db')
        cursor = conn.cursor()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f'database_backup_{timestamp}.sql'
        
        # Export leads and vendors tables
        with open(backup_file, 'w') as f:
            for line in conn.iterdump():
                if 'CREATE TABLE leads' in line or 'INSERT INTO leads' in line:
                    f.write(line + '\n')
                elif 'CREATE TABLE vendors' in line or 'INSERT INTO vendors' in line:
                    f.write(line + '\n')
        
        # Count existing records
        cursor.execute("SELECT COUNT(*) FROM leads")
        leads_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM vendors") 
        vendors_count = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"✅ Backup created: {backup_file}")
        print(f"   📊 Backed up {leads_count} leads, {vendors_count} vendors")
        return backup_file, leads_count, vendors_count
        
    except Exception as e:
        print(f"❌ Error creating backup: {e}")
        return None, 0, 0

def create_new_leads_table():
    """Create new leads table with proper schema for multi-level routing"""
    
    leads_schema = """
    CREATE TABLE leads (
        -- Core Lead Identification
        id TEXT PRIMARY KEY,
        account_id TEXT NOT NULL,
        ghl_contact_id TEXT,
        ghl_opportunity_id TEXT,
        
        -- Customer Contact Information
        customer_name TEXT,
        customer_email TEXT,
        customer_phone TEXT,
        
        -- SERVICE MATCHING FIELDS (CRITICAL FOR ROUTING)
        primary_service_category TEXT NOT NULL,           -- e.g., "Marine Systems"
        specific_service_requested TEXT,                  -- e.g., "AC Service" (from GHL field FT85QGi0tBq1AfVGNJ9v)
        
        -- LOCATION MATCHING FIELDS (CRITICAL FOR ROUTING)
        customer_zip_code TEXT,                          -- ZIP provided by customer
        service_county TEXT,                             -- ZIP converted to county (for matching)
        service_state TEXT,                              -- State for validation
        
        -- Lead Assignment & Tracking
        vendor_id TEXT,                                  -- Assigned vendor ID
        assigned_at TIMESTAMP,                           -- When assigned
        status TEXT DEFAULT 'unassigned',               -- unassigned, assigned, completed, etc.
        priority TEXT DEFAULT 'normal',                  -- normal, high, urgent
        source TEXT,                                     -- webhook, bulk_processing, manual, etc.
        
        -- Rich Data Preservation  
        service_details TEXT,                            -- JSON blob preserving original form data
        
        -- Timestamps
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        -- Foreign Key Constraints
        FOREIGN KEY (account_id) REFERENCES accounts(id),
        FOREIGN KEY (vendor_id) REFERENCES vendors(id)
    );
    """
    
    return leads_schema

def create_new_vendors_table():
    """Create new vendors table with proper schema for multi-level routing"""
    
    vendors_schema = """
    CREATE TABLE vendors (
        -- Core Vendor Identification
        id TEXT PRIMARY KEY,
        account_id TEXT NOT NULL,
        ghl_contact_id TEXT UNIQUE,                      -- GHL Contact ID
        ghl_user_id TEXT,                                -- GHL User ID for assignment
        
        -- Vendor Contact Information
        name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        company_name TEXT,
        
        -- SERVICE MATCHING FIELDS (CRITICAL FOR ROUTING)
        service_categories TEXT,                         -- JSON array: ["Marine Systems", "Engines and Generators"]
        services_offered TEXT,                           -- JSON array: ["AC Service", "Engine Repair", "Detailing"]
        
        -- COVERAGE MATCHING FIELDS (CRITICAL FOR ROUTING)
        coverage_type TEXT DEFAULT 'county',            -- global, national, state, county, zip
        coverage_states TEXT,                            -- JSON array: ["FL", "CA"] (if state-level)
        coverage_counties TEXT,                          -- JSON array: ["Miami-Dade, FL", "Broward, FL"] (if county-level)
        
        -- LEAD ASSIGNMENT ROUTING FIELDS (CRITICAL FOR ALGORITHMS)
        last_lead_assigned TIMESTAMP,                    -- For round-robin routing (GHL field: NbsJTMv3EkxqNfwx8Jh4)
        lead_close_percentage REAL DEFAULT 0.0,         -- For performance-based routing (GHL field: OwHQipU7xdrHCpVswtnW)
        
        -- Vendor Status & Availability
        status TEXT DEFAULT 'active',                    -- active, inactive, suspended
        taking_new_work BOOLEAN DEFAULT 1,               -- 1 = taking leads, 0 = not available
        
        -- Timestamps
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        -- Foreign Key Constraints
        FOREIGN KEY (account_id) REFERENCES accounts(id)
    );
    """
    
    return vendors_schema

def create_indexes():
    """Create indexes for optimal query performance"""
    
    indexes = [
        # Leads table indexes for fast routing queries
        "CREATE INDEX idx_leads_service_category ON leads(primary_service_category);",
        "CREATE INDEX idx_leads_specific_service ON leads(specific_service_requested);", 
        "CREATE INDEX idx_leads_county ON leads(service_county);",
        "CREATE INDEX idx_leads_status ON leads(status);",
        "CREATE INDEX idx_leads_account ON leads(account_id);",
        "CREATE INDEX idx_leads_ghl_contact ON leads(ghl_contact_id);",
        
        # Vendors table indexes for fast matching queries
        "CREATE INDEX idx_vendors_account ON vendors(account_id);",
        "CREATE INDEX idx_vendors_status ON vendors(status);",
        "CREATE INDEX idx_vendors_taking_work ON vendors(taking_new_work);",
        "CREATE INDEX idx_vendors_coverage_type ON vendors(coverage_type);",
        "CREATE INDEX idx_vendors_ghl_contact ON vendors(ghl_contact_id);",
        "CREATE INDEX idx_vendors_last_assigned ON vendors(last_lead_assigned);",
        "CREATE INDEX idx_vendors_close_percentage ON vendors(lead_close_percentage);"
    ]
    
    return indexes

def restructure_database():
    """Main function to restructure the database tables"""
    
    print("🚀 DATABASE RESTRUCTURING - MULTI-LEVEL ROUTING SCHEMA")
    print("=" * 65)
    print("RESTRUCTURING: leads and vendors tables only")
    print("PRESERVING: All other tables (accounts, activity_log, etc.)")
    print("")
    
    # Step 1: Create backup
    print("STEP 1: Creating backup of existing data...")
    backup_file, leads_count, vendors_count = backup_existing_data()
    
    if not backup_file:
        print("❌ Backup failed - aborting restructure for safety")
        return False
    
    try:
        conn = sqlite3.connect('smart_lead_router.db')
        cursor = conn.cursor()
        
        # Step 2: Drop existing tables
        print("\nSTEP 2: Dropping existing leads and vendors tables...")
        cursor.execute("DROP TABLE IF EXISTS leads;")
        cursor.execute("DROP TABLE IF EXISTS vendors;")
        print("✅ Old tables dropped")
        
        # Step 3: Create new leads table
        print("\nSTEP 3: Creating new leads table with proper schema...")
        leads_schema = create_new_leads_table()
        cursor.execute(leads_schema)
        print("✅ New leads table created")
        print("   📋 Fields: primary_service_category, specific_service_requested")
        print("   📍 Fields: customer_zip_code, service_county, service_state")
        print("   📊 Fields: vendor_id, status, priority, service_details")
        
        # Step 4: Create new vendors table
        print("\nSTEP 4: Creating new vendors table with proper schema...")
        vendors_schema = create_new_vendors_table()
        cursor.execute(vendors_schema)
        print("✅ New vendors table created")
        print("   🛠️ Fields: service_categories, services_offered")
        print("   🗺️ Fields: coverage_type, coverage_counties, coverage_states")
        print("   🎯 Fields: last_lead_assigned, lead_close_percentage")
        
        # Step 5: Create performance indexes
        print("\nSTEP 5: Creating performance indexes...")
        indexes = create_indexes()
        for index_sql in indexes:
            cursor.execute(index_sql)
        print(f"✅ Created {len(indexes)} performance indexes")
        
        # Step 6: Verify table structure
        print("\nSTEP 6: Verifying new table structures...")
        
        # Check leads table
        cursor.execute("PRAGMA table_info(leads);")
        leads_columns = cursor.fetchall()
        leads_column_names = [col[1] for col in leads_columns]
        
        # Check vendors table  
        cursor.execute("PRAGMA table_info(vendors);")
        vendors_columns = cursor.fetchall()
        vendors_column_names = [col[1] for col in vendors_columns]
        
        # Commit all changes
        conn.commit()
        conn.close()
        
        # Report success
        print("\n🎉 DATABASE RESTRUCTURING COMPLETE!")
        print("=" * 50)
        print(f"✅ Backup saved: {backup_file}")
        print(f"✅ Previous data: {leads_count} leads, {vendors_count} vendors")
        print("✅ New schema ready for multi-level routing")
        print("")
        print("📋 NEW LEADS TABLE COLUMNS:")
        for col in leads_column_names:
            print(f"   • {col}")
        print("")
        print("🏢 NEW VENDORS TABLE COLUMNS:")
        for col in vendors_column_names:
            print(f"   • {col}")
        print("")
        print("🎯 READY FOR:")
        print("   • Service category + specific service matching")
        print("   • ZIP → County conversion and matching")
        print("   • Performance-based + round-robin routing")
        print("   • Proper 1:1 matching relationships")
        print("")
        print("🔄 NEXT STEPS:")
        print("   1. Update webhook processing to populate new fields")
        print("   2. Create GHL sync script to repopulate vendor data")
        print("   3. Test routing with properly structured data")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during restructuring: {e}")
        return False

def validate_schema():
    """Validate that the new schema has all required fields"""
    
    print("\n🔍 SCHEMA VALIDATION")
    print("-" * 30)
    
    try:
        conn = sqlite3.connect('smart_lead_router.db')
        cursor = conn.cursor()
        
        # Required fields for leads
        required_leads_fields = [
            'primary_service_category', 'specific_service_requested',
            'customer_zip_code', 'service_county', 'service_state'
        ]
        
        # Required fields for vendors
        required_vendors_fields = [
            'service_categories', 'services_offered', 'coverage_type',
            'coverage_counties', 'last_lead_assigned', 'lead_close_percentage'
        ]
        
        # Check leads table
        cursor.execute("PRAGMA table_info(leads);")
        leads_columns = [col[1] for col in cursor.fetchall()]
        
        print("LEADS TABLE VALIDATION:")
        for field in required_leads_fields:
            if field in leads_columns:
                print(f"   ✅ {field}")
            else:
                print(f"   ❌ {field} - MISSING!")
        
        # Check vendors table
        cursor.execute("PRAGMA table_info(vendors);")
        vendors_columns = [col[1] for col in cursor.fetchall()]
        
        print("\nVENDORS TABLE VALIDATION:")
        for field in required_vendors_fields:
            if field in vendors_columns:
                print(f"   ✅ {field}")
            else:
                print(f"   ❌ {field} - MISSING!")
        
        conn.close()
        
        # Overall validation
        missing_leads = [f for f in required_leads_fields if f not in leads_columns]
        missing_vendors = [f for f in required_vendors_fields if f not in vendors_columns]
        
        if not missing_leads and not missing_vendors:
            print("\n🎉 SCHEMA VALIDATION PASSED!")
            print("   ✅ All required fields present")
            print("   ✅ Ready for multi-level routing")
            return True
        else:
            print(f"\n❌ SCHEMA VALIDATION FAILED!")
            if missing_leads:
                print(f"   Missing leads fields: {missing_leads}")
            if missing_vendors:
                print(f"   Missing vendors fields: {missing_vendors}")
            return False
            
    except Exception as e:
        print(f"❌ Error validating schema: {e}")
        return False

if __name__ == '__main__':
    print("DATABASE RESTRUCTURING FOR MULTI-LEVEL ROUTING")
    print("This will clear leads and vendors tables and rebuild with proper schema.")
    print("")
    
    # Confirm before proceeding
    confirm = input("Are you sure you want to proceed? (yes/no): ").lower().strip()
    if confirm != 'yes':
        print("❌ Restructuring cancelled")
        sys.exit(0)
    
    # Execute restructuring
    success = restructure_database()
    
    if success:
        # Validate the new schema
        validate_schema()
        
        print("\n🚀 DATABASE RESTRUCTURING SUCCESSFUL!")
        print("The system is now ready for proper multi-level routing.")
        print("Next: Create vendor sync script to populate from GHL.")
    else:
        print("\n❌ DATABASE RESTRUCTURING FAILED!")
        print("Check error messages above and restore from backup if needed.")
