#!/usr/bin/env python3
"""
GHL AS SINGLE SOURCE OF TRUTH SYNC SCRIPT
=========================================
This script validates Lead Router database records against GoHighLevel CRM.
GHL is the single source of truth - any discrepancies are resolved by updating
or deleting local database records to match GHL.

Sync Logic:
1. For each vendor/lead in database, look it up in GHL
2. If found in GHL and data differs - update database to match GHL
3. If not found in GHL - delete from database
4. After validation, check for new records in GHL not in database and add them
"""

import sqlite3
import json
import logging
import sys
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Set

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
import os

# Load .env
current_dir = os.getcwd()
if current_dir.endswith('Lead-Router-Pro'):
    dotenv_path = os.path.join(current_dir, '.env')
else:
    dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')

load_dotenv(dotenv_path)

from config import AppConfig
from api.services.ghl_api import GoHighLevelAPI
from api.services.location_service import location_service
from api.services.field_mapper import field_mapper

# Setup logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ghl_truth_sync.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class GHLTruthSync:
    """Sync that treats GoHighLevel as the single source of truth"""
    
    def __init__(self):
        """Initialize with GHL API and field mappings"""
        try:
            # Initialize GHL API
            self.ghl_api = GoHighLevelAPI(
                private_token=AppConfig.GHL_PRIVATE_TOKEN,
                location_id=AppConfig.GHL_LOCATION_ID,
                agency_api_key=AppConfig.GHL_AGENCY_API_KEY,
                company_id=AppConfig.GHL_COMPANY_ID
            )
            
            # Get account
            self.account = self._get_or_create_account()
            if not self.account:
                raise Exception("Could not get or create account")
            self.account_id = self.account['id']
            
            # Use field mappings from field_reference.json via field_mapper
            # These are the current GHL field IDs from the system
            self.vendor_field_ids = {
                'ghl_user_id': 'HXVNT4y8OynNokWAfO2D',              # GHL User ID
                'vendor_company_name': 'JexVrg2VNhnwIX7YlyJV',      # Vendor Company Name
                'service_categories': '72qwwzy4AUfTCBJvBIEf',       # Service Categories Selections
                'services_offered': 'pAq9WBsIuFUAZuwz3YY4',         # Services Provided
                'service_zip_codes': 'yDcN0FmwI3xacyxAuTWs',        # Service Zip Codes
                'last_lead_assigned': 'NbsJTMv3EkxqNfwx8Jh4',       # Last Lead Assigned
                'lead_close_percentage': 'OwHQipU7xdrHCpVswtnW',    # Lead Close %
                'taking_new_work': 'bTFOs5zXYt85AvDJJUAb',          # Taking New Work?
            }
            
            self.lead_field_ids = {
                'specific_service_needed': 'FT85QGi0tBq1AfVGNJ9v',  # Specific Service Needed
                'primary_service_category': 'HRqfv0HnUydNRLKWhk27', # Primary Service Category
                'zip_code_of_service': 'y3Xo7qsFEQumoFugTeCq',     # Zip Code of Service
                'vessel_make': 'n90eUaRDbnifWJgUIQ2g',             # Vessel Make
                'vessel_model': 'Jqv9F5W40Y4AAmevXJOu',            # Vessel Model
                'vessel_year': '8HWqslCRX6hXl6lWYrWZ',             # Vessel Year
                'vessel_length': 'dpKUiZjU45sGJQWP0vHY',           # Vessel Length (ft)
                'vessel_location': 'DaGiQVL4fxiYOdx7ZnCr',         # Vessel Location/Slip #
                'budget_range': 'Y2AZebrGIcBP14KNFqBr',            # Budget Range
                'desired_timeline': 'mPeGj5K7CXLu46CXGhNc',        # Desired Timeline
                'special_requests': 'CmT8lJDbNJ5UKNvPOHQ8',        # Special Requests/Notes
            }
            
            logger.info("✅ GHL Truth Sync initialized")
            logger.info(f"📋 Vendor field mappings: {len(self.vendor_field_ids)} fields")
            logger.info(f"📋 Lead field mappings: {len(self.lead_field_ids)} fields")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize: {e}")
            raise
    
    def _get_or_create_account(self) -> Optional[Dict[str, Any]]:
        """Get existing account or create default account"""
        try:
            conn = sqlite3.connect('smart_lead_router.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, company_name, ghl_location_id 
                FROM accounts 
                WHERE ghl_location_id = ?
            """, (AppConfig.GHL_LOCATION_ID,))
            
            account = cursor.fetchone()
            
            if account:
                conn.close()
                return {
                    'id': account[0],
                    'company_name': account[1], 
                    'ghl_location_id': account[2]
                }
            
            # Create default account
            account_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO accounts (
                    id, company_name, industry, ghl_location_id,
                    ghl_private_token, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (
                account_id, "Digital Marine LLC", "marine",
                AppConfig.GHL_LOCATION_ID, AppConfig.GHL_PRIVATE_TOKEN
            ))
            
            conn.commit()
            conn.close()
            
            return {
                'id': account_id,
                'company_name': "Digital Marine LLC",
                'ghl_location_id': AppConfig.GHL_LOCATION_ID
            }
            
        except Exception as e:
            logger.error(f"❌ Error with account: {e}")
            return None
    
    def sync_all_data(self) -> bool:
        """Main sync function - GHL is truth"""
        
        print("🔄 GHL AS SINGLE SOURCE OF TRUTH SYNC")
        print("=" * 50)
        print("Step 1: Validate existing database records against GHL")
        print("Step 2: Remove records not found in GHL")
        print("Step 3: Add new records from GHL not in database")
        print("")
        
        try:
            # Step 1: Validate vendors
            print("VALIDATING VENDORS...")
            vendor_results = self._validate_vendors()
            
            # Step 2: Validate leads  
            print("\nVALIDATING LEADS...")
            leads_results = self._validate_leads()
            
            # Step 3: Add new records from GHL
            print("\nADDING NEW RECORDS FROM GHL...")
            new_vendor_results = self._add_new_vendors_from_ghl()
            new_lead_results = self._add_new_leads_from_ghl()
            
            # Results
            print(f"\n📊 SYNC RESULTS:")
            print(f"   VENDORS:")
            print(f"      ✅ Updated: {vendor_results['updated']}")
            print(f"      🗑️  Deleted: {vendor_results['deleted']}")
            print(f"      ➕ Added New: {new_vendor_results['added']}")
            print(f"      ⚠️  Errors: {vendor_results['errors']}")
            
            print(f"   LEADS:")
            print(f"      ✅ Updated: {leads_results['updated']}")
            print(f"      🗑️  Deleted: {leads_results['deleted']}")
            print(f"      ➕ Added New: {new_lead_results['added']}")
            print(f"      ⚠️  Errors: {leads_results['errors']}")
            
            # Verify
            print(f"\nVERIFYING SYNC...")
            self._verify_sync()
            
            total_changes = (vendor_results['updated'] + vendor_results['deleted'] + 
                           leads_results['updated'] + leads_results['deleted'] +
                           new_vendor_results['added'] + new_lead_results['added'])
            
            if total_changes > 0:
                print(f"\n🎉 SYNC SUCCESSFUL! {total_changes} total changes made")
                print("   ✅ Database now matches GHL (single source of truth)")
                return True
            else:
                print(f"\n✅ SYNC COMPLETE - Database already in sync with GHL")
                return True
                
        except Exception as e:
            logger.error(f"❌ Sync failed: {e}")
            return False
    
    def _validate_vendors(self) -> Dict[str, int]:
        """Validate each vendor in database against GHL"""
        
        try:
            conn = sqlite3.connect('smart_lead_router.db')
            cursor = conn.cursor()
            
            # Get all vendors from database
            cursor.execute("""
                SELECT id, ghl_contact_id, name, email, phone, company_name,
                       service_categories, services_offered, coverage_states,
                       coverage_counties, coverage_type, last_lead_assigned, 
                       lead_close_percentage, taking_new_work, ghl_user_id
                FROM vendors
                WHERE account_id = ?
            """, (self.account_id,))
            
            db_vendors = cursor.fetchall()
            conn.close()
            
            updated = 0
            deleted = 0
            errors = 0
            
            for vendor in db_vendors:
                vendor_id = vendor[0]
                ghl_contact_id = vendor[1]
                
                if not ghl_contact_id:
                    # No GHL ID - delete this vendor
                    self._delete_vendor(vendor_id)
                    deleted += 1
                    logger.info(f"🗑️  Deleted vendor {vendor[2]} - no GHL contact ID")
                    continue
                
                try:
                    # Look up contact in GHL
                    ghl_contact = self.ghl_api.get_contact_by_id(ghl_contact_id)
                    
                    if not ghl_contact:
                        # Not found in GHL - delete from database
                        self._delete_vendor(vendor_id)
                        deleted += 1
                        logger.info(f"🗑️  Deleted vendor {vendor[2]} - not found in GHL")
                    else:
                        # Found in GHL - check if update needed
                        if self._vendor_needs_update(vendor, ghl_contact):
                            vendor_data = self._extract_vendor_data(ghl_contact)
                            if vendor_data:
                                vendor_data['id'] = vendor_id  # Keep existing ID
                                if self._update_vendor(vendor_data):
                                    updated += 1
                                    logger.info(f"✅ Updated vendor {vendor[2]} from GHL")
                                else:
                                    errors += 1
                            else:
                                # Contact exists but is no longer a vendor
                                self._delete_vendor(vendor_id)
                                deleted += 1
                                logger.info(f"🗑️  Deleted vendor {vendor[2]} - no longer has vendor fields in GHL")
                        
                except Exception as e:
                    errors += 1
                    logger.error(f"❌ Error validating vendor {vendor[2]}: {e}")
            
            return {'updated': updated, 'deleted': deleted, 'errors': errors}
            
        except Exception as e:
            logger.error(f"❌ Error validating vendors: {e}")
            return {'updated': 0, 'deleted': 0, 'errors': 0}
    
    def _validate_leads(self) -> Dict[str, int]:
        """Validate each lead in database against GHL"""
        
        try:
            conn = sqlite3.connect('smart_lead_router.db')
            cursor = conn.cursor()
            
            # Get all leads from database
            cursor.execute("""
                SELECT id, ghl_contact_id, customer_name, customer_email, 
                       customer_phone, specific_service_requested, 
                       customer_zip_code, service_county, service_state,
                       service_details
                FROM leads
                WHERE account_id = ?
            """, (self.account_id,))
            
            db_leads = cursor.fetchall()
            conn.close()
            
            updated = 0
            deleted = 0
            errors = 0
            
            for lead in db_leads:
                lead_id = lead[0]
                ghl_contact_id = lead[1]
                
                if not ghl_contact_id:
                    # No GHL ID - delete this lead
                    self._delete_lead(lead_id)
                    deleted += 1
                    logger.info(f"🗑️  Deleted lead {lead[2]} - no GHL contact ID")
                    continue
                
                try:
                    # Look up contact in GHL
                    ghl_contact = self.ghl_api.get_contact_by_id(ghl_contact_id)
                    
                    if not ghl_contact:
                        # Not found in GHL - delete from database
                        self._delete_lead(lead_id)
                        deleted += 1
                        logger.info(f"🗑️  Deleted lead {lead[2]} - not found in GHL")
                    else:
                        # Found in GHL - check if update needed
                        if self._lead_needs_update(lead, ghl_contact):
                            lead_data = self._extract_lead_data(ghl_contact)
                            if lead_data:
                                lead_data['id'] = lead_id  # Keep existing ID
                                if self._update_lead(lead_data):
                                    updated += 1
                                    logger.info(f"✅ Updated lead {lead[2]} from GHL")
                                else:
                                    errors += 1
                            else:
                                # Contact exists but is no longer a lead
                                self._delete_lead(lead_id)
                                deleted += 1
                                logger.info(f"🗑️  Deleted lead {lead[2]} - no longer has lead fields in GHL")
                        
                except Exception as e:
                    errors += 1
                    logger.error(f"❌ Error validating lead {lead[2]}: {e}")
            
            return {'updated': updated, 'deleted': deleted, 'errors': errors}
            
        except Exception as e:
            logger.error(f"❌ Error validating leads: {e}")
            return {'updated': 0, 'deleted': 0, 'errors': 0}
    
    def _add_new_vendors_from_ghl(self) -> Dict[str, int]:
        """Add vendors that exist in GHL but not in database"""
        
        try:
            # Get all vendor GHL IDs from database
            conn = sqlite3.connect('smart_lead_router.db')
            cursor = conn.cursor()
            cursor.execute("SELECT ghl_contact_id FROM vendors WHERE account_id = ?", (self.account_id,))
            existing_ghl_ids = set(row[0] for row in cursor.fetchall() if row[0])
            conn.close()
            
            # Get all contacts from GHL
            all_contacts = self.ghl_api.search_contacts(query="", limit=200)
            added = 0
            
            if all_contacts:
                for contact in all_contacts:
                    contact_id = contact.get('id')
                    
                    # Skip if already in database
                    if contact_id in existing_ghl_ids:
                        continue
                    
                    # Check if this is a vendor (has GHL User ID)
                    custom_fields = contact.get('customFields', [])
                    has_ghl_user_id = any(
                        field.get('id') == self.vendor_field_ids['ghl_user_id'] and 
                        field.get('value', '').strip()
                        for field in custom_fields
                    )
                    
                    if has_ghl_user_id:
                        vendor_data = self._extract_vendor_data(contact)
                        if vendor_data and self._save_vendor(vendor_data):
                            added += 1
                            logger.info(f"➕ Added new vendor from GHL: {vendor_data['name']}")
            
            return {'added': added}
            
        except Exception as e:
            logger.error(f"❌ Error adding new vendors: {e}")
            return {'added': 0}
    
    def _add_new_leads_from_ghl(self) -> Dict[str, int]:
        """Add leads that exist in GHL but not in database"""
        
        try:
            # Get all lead GHL IDs from database
            conn = sqlite3.connect('smart_lead_router.db')
            cursor = conn.cursor()
            cursor.execute("SELECT ghl_contact_id FROM leads WHERE account_id = ?", (self.account_id,))
            existing_ghl_ids = set(row[0] for row in cursor.fetchall() if row[0])
            conn.close()
            
            # Get all contacts from GHL
            all_contacts = self.ghl_api.search_contacts(query="", limit=200)
            added = 0
            
            if all_contacts:
                for contact in all_contacts:
                    contact_id = contact.get('id')
                    
                    # Skip if already in database
                    if contact_id in existing_ghl_ids:
                        continue
                    
                    custom_fields = contact.get('customFields', [])
                    
                    # Check for specific service needed (indicates a lead)
                    has_service_request = any(
                        field.get('id') == self.lead_field_ids['specific_service_needed'] and 
                        field.get('value', '').strip()
                        for field in custom_fields
                    )
                    
                    # Exclude vendors (no GHL User ID = lead)
                    has_ghl_user_id = any(
                        field.get('id') == self.vendor_field_ids['ghl_user_id'] and 
                        field.get('value', '').strip()
                        for field in custom_fields
                    )
                    
                    if has_service_request and not has_ghl_user_id:
                        lead_data = self._extract_lead_data(contact)
                        if lead_data and self._save_lead(lead_data):
                            added += 1
                            logger.info(f"➕ Added new lead from GHL: {lead_data['customer_name']}")
            
            return {'added': added}
            
        except Exception as e:
            logger.error(f"❌ Error adding new leads: {e}")
            return {'added': 0}
    
    def _vendor_needs_update(self, db_vendor: tuple, ghl_contact: Dict[str, Any]) -> bool:
        """Check if vendor data differs between database and GHL"""
        
        # Extract GHL data
        ghl_data = self._extract_vendor_data(ghl_contact)
        if not ghl_data:
            return False
        
        # Compare key fields
        db_name = db_vendor[2]
        db_email = db_vendor[3]
        db_phone = db_vendor[4]
        db_company = db_vendor[5]
        
        if (db_name != ghl_data.get('name') or
            db_email != ghl_data.get('email') or
            db_phone != ghl_data.get('phone') or
            db_company != ghl_data.get('company_name')):
            return True
        
        # Compare service categories and coverage
        db_categories = db_vendor[6]
        db_coverage_type = db_vendor[7]
        db_coverage_states = db_vendor[8]
        db_coverage_counties = db_vendor[9]
        
        if (db_categories != ghl_data.get('service_categories') or
            db_coverage_type != ghl_data.get('coverage_type') or
            db_coverage_states != ghl_data.get('coverage_states') or
            db_coverage_counties != ghl_data.get('coverage_counties')):
            return True
        
        return False
    
    def _lead_needs_update(self, db_lead: tuple, ghl_contact: Dict[str, Any]) -> bool:
        """Check if lead data differs between database and GHL"""
        
        # Extract GHL data
        ghl_data = self._extract_lead_data(ghl_contact)
        if not ghl_data:
            return False
        
        # Compare key fields
        db_name = db_lead[2]
        db_email = db_lead[3]
        db_phone = db_lead[4]
        db_service = db_lead[5]
        db_zip = db_lead[6]
        
        if (db_name != ghl_data.get('customer_name') or
            db_email != ghl_data.get('customer_email') or
            db_phone != ghl_data.get('customer_phone') or
            db_service != ghl_data.get('specific_service_requested') or
            db_zip != ghl_data.get('customer_zip_code')):
            return True
        
        return False
    
    def _extract_vendor_data(self, contact: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract vendor data from GHL contact"""
        
        contact_id = contact.get('id')
        
        try:
            # Extract custom fields
            custom_fields = contact.get('customFields', [])
            field_data = {}
            
            # Map GHL fields to our field names
            for field in custom_fields:
                field_id = field.get('id', '')
                field_value = field.get('value', '') or field.get('fieldValue', '')
                
                # Map vendor fields
                for field_name, ghl_id in self.vendor_field_ids.items():
                    if field_id == ghl_id:
                        field_data[field_name] = field_value
                        break
            
            # Check required field
            ghl_user_id = field_data.get('ghl_user_id', '').strip()
            if not ghl_user_id:
                return None
            
            # Build vendor data
            vendor_data = {
                'id': str(uuid.uuid4()),
                'account_id': self.account_id,
                'ghl_contact_id': contact_id,
                'ghl_user_id': ghl_user_id,
                'name': f"{contact.get('firstName', '')} {contact.get('lastName', '')}".strip(),
                'email': contact.get('email', ''),
                'phone': contact.get('phone', ''),
                'company_name': field_data.get('vendor_company_name', contact.get('companyName', '')),
                'service_categories': json.dumps(self._parse_list(field_data.get('service_categories', ''))),
                'services_offered': json.dumps(self._parse_list(field_data.get('services_offered', ''))),
                'last_lead_assigned': self._parse_date(field_data.get('last_lead_assigned', '')),
                'lead_close_percentage': self._parse_percentage(field_data.get('lead_close_percentage', '0')),
                'taking_new_work': self._parse_boolean(field_data.get('taking_new_work', 'true')),
                'status': 'active' if ghl_user_id else 'pending'
            }
            
            # Process coverage from Service Zip Codes field
            coverage_data = self._process_coverage(field_data.get('service_zip_codes', ''), contact)
            vendor_data.update(coverage_data)
            
            return vendor_data
            
        except Exception as e:
            logger.error(f"❌ Error extracting vendor data: {e}")
            return None
    
    def _extract_lead_data(self, contact: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract lead data from GHL contact"""
        
        contact_id = contact.get('id')
        
        try:
            # Extract custom fields
            custom_fields = contact.get('customFields', [])
            field_data = {}
            
            # Map GHL fields to our field names
            for field in custom_fields:
                field_id = field.get('id', '')
                field_value = field.get('value', '') or field.get('fieldValue', '')
                
                # Map lead fields
                for field_name, ghl_id in self.lead_field_ids.items():
                    if field_id == ghl_id:
                        field_data[field_name] = field_value
                        break
            
            # Check required field
            specific_service = field_data.get('specific_service_needed', '').strip()
            if not specific_service:
                return None
            
            # Build lead data
            lead_data = {
                'id': str(uuid.uuid4()),
                'account_id': self.account_id,
                'ghl_contact_id': contact_id,
                'ghl_opportunity_id': None,
                'customer_name': f"{contact.get('firstName', '')} {contact.get('lastName', '')}".strip(),
                'customer_email': contact.get('email', ''),
                'customer_phone': contact.get('phone', ''),
                'specific_service_requested': specific_service,
                'customer_zip_code': field_data.get('zip_code_of_service', ''),
                'service_zip_code': field_data.get('zip_code_of_service', ''),
                'status': 'unassigned',
                'priority': 'normal',
                'source': 'GHL Sync'
            }
            
            # Use Primary Service Category from GHL if available, otherwise derive it
            primary_category = field_data.get('primary_service_category', '').strip()
            if primary_category:
                lead_data['primary_service_category'] = primary_category
            else:
                # Derive service category from specific service if not provided
                lead_data['primary_service_category'] = self._derive_service_category(specific_service)
            
            # Convert ZIP to county/state
            zip_code = lead_data['customer_zip_code']
            if zip_code:
                try:
                    location_data = location_service.zip_to_location(zip_code)
                    if not location_data.get('error'):
                        lead_data['service_county'] = location_data.get('county', '')
                        lead_data['service_state'] = location_data.get('state', '')
                except Exception:
                    pass
            
            # Build service_details
            service_details = {}
            for field_name, field_value in field_data.items():
                if field_name not in ['specific_service_needed', 'zip_code_of_service'] and field_value:
                    service_details[field_name] = field_value
            
            lead_data['service_details'] = json.dumps(service_details)
            
            return lead_data
            
        except Exception as e:
            logger.error(f"❌ Error extracting lead data: {e}")
            return None
    
    def _process_coverage(self, service_zip_codes_raw: str, contact: Dict[str, Any]) -> Dict[str, Any]:
        """Process coverage from Service Zip Codes field - handles formatted coverage data"""
        
        coverage_counties = []
        coverage_states = set()
        coverage_type = 'county'
        
        if service_zip_codes_raw:
            # Check if this is formatted coverage data (from vendor widget)
            if service_zip_codes_raw.startswith(('COUNTIES:', 'STATES:', 'ZIP CODES:', 'GLOBAL', 'NATIONAL')):
                
                if service_zip_codes_raw.startswith('GLOBAL'):
                    coverage_type = 'global'
                    coverage_counties = []
                    coverage_states = set()
                    
                elif service_zip_codes_raw.startswith('NATIONAL'):
                    coverage_type = 'national'
                    coverage_counties = []
                    coverage_states = set()
                    
                elif service_zip_codes_raw.startswith('STATES:'):
                    coverage_type = 'state'
                    states_text = service_zip_codes_raw.replace('STATES:', '').strip()
                    if states_text:
                        state_list = [s.strip() for s in states_text.split(',') if s.strip()]
                        coverage_states = set(state_list)
                        coverage_counties = []
                        
                elif service_zip_codes_raw.startswith('COUNTIES:'):
                    coverage_type = 'county'
                    counties_text = service_zip_codes_raw.replace('COUNTIES:', '').strip()
                    if counties_text:
                        county_list = [c.strip() for c in counties_text.split(';') if c.strip()]
                        coverage_counties = county_list
                        # Extract states from county data
                        for county in county_list:
                            if ', ' in county:
                                state = county.split(', ')[-1]
                                coverage_states.add(state)
                                
                elif service_zip_codes_raw.startswith('ZIP CODES:'):
                    # Parse ZIP codes and convert to counties
                    zip_text = service_zip_codes_raw.replace('ZIP CODES:', '').strip()
                    if zip_text:
                        zip_codes = self._parse_zip_codes(zip_text)
                        for zip_code in zip_codes:
                            try:
                                location_data = location_service.zip_to_location(zip_code)
                                if not location_data.get('error'):
                                    county = location_data.get('county', '')
                                    state = location_data.get('state', '')
                                    
                                    if county and state:
                                        county_formatted = f"{county}, {state}"
                                        if county_formatted not in coverage_counties:
                                            coverage_counties.append(county_formatted)
                                            coverage_states.add(state)
                            except Exception:
                                pass
                        
                        # Determine coverage type based on results
                        if len(coverage_states) > 3:
                            coverage_type = 'national'
                        elif len(coverage_states) > 1:
                            coverage_type = 'state'
                        else:
                            coverage_type = 'county'
            else:
                # Check if this is direct county format like "Broward, FL; Miami-Dade, FL" 
                if ';' in service_zip_codes_raw and ',' in service_zip_codes_raw:
                    # Direct county format: "County, ST; County, ST"
                    county_list = [c.strip() for c in service_zip_codes_raw.split(';') if c.strip()]
                    coverage_counties = county_list
                    # Extract states from county data
                    for county in county_list:
                        if ', ' in county:
                            state = county.split(', ')[-1]
                            coverage_states.add(state)
                    
                    # Determine coverage type
                    if len(coverage_states) > 3:
                        coverage_type = 'national'
                    elif len(coverage_states) > 1:
                        coverage_type = 'state'
                    else:
                        coverage_type = 'county'
                        
                elif service_zip_codes_raw.upper() in ['USA', 'UNITED STATES', 'NATIONAL', 'NATIONWIDE']:
                    # National coverage
                    coverage_type = 'national'
                    coverage_counties = []
                    coverage_states = set()
                    
                elif service_zip_codes_raw.upper() in ['NONE', 'NULL', '']:
                    # No coverage
                    coverage_type = 'county'
                    coverage_counties = []
                    coverage_states = set()
                    
                elif len(service_zip_codes_raw) == 2 and service_zip_codes_raw.upper() in ['FL', 'CA', 'TX', 'NY', 'AL', 'GA', 'NC', 'SC', 'VA']:
                    # Single state code
                    coverage_type = 'state'
                    coverage_states = {service_zip_codes_raw.upper()}
                    coverage_counties = []
                    
                elif ',' in service_zip_codes_raw and all(len(s.strip()) == 2 for s in service_zip_codes_raw.split(',') if s.strip()):
                    # Multiple state codes like "AL, FL, GA"  
                    state_list = [s.strip().upper() for s in service_zip_codes_raw.split(',') if s.strip()]
                    coverage_type = 'state' if len(state_list) <= 3 else 'national'
                    coverage_states = set(state_list)
                    coverage_counties = []
                    
                elif 'County' in service_zip_codes_raw:
                    # County names with "County" suffix like "Monroe County, Miami Dade County"
                    county_list = [c.strip() for c in service_zip_codes_raw.split(',') if c.strip()]
                    coverage_counties = []
                    for county_raw in county_list:
                        # Remove "County" suffix and add FL (most common)
                        county_clean = county_raw.replace(' County', '').strip()
                        if county_clean:
                            coverage_counties.append(f"{county_clean}, FL")
                            coverage_states.add('FL')
                    
                    coverage_type = 'county' if len(coverage_states) <= 1 else 'state'
                    
                elif ',' in service_zip_codes_raw and not ';' in service_zip_codes_raw:
                    # Comma-separated counties without state like "Miami Dade, Broward"
                    county_list = [c.strip() for c in service_zip_codes_raw.split(',') if c.strip()]
                    coverage_counties = []
                    for county_raw in county_list:
                        # Add FL as default state (most common in our data)
                        county_clean = county_raw.replace(' County', '').strip()
                        if county_clean:
                            coverage_counties.append(f"{county_clean}, FL")
                            coverage_states.add('FL')
                    
                    coverage_type = 'county'
                    
                elif service_zip_codes_raw.startswith('[') and service_zip_codes_raw.endswith(']'):
                    # Array-like format like "['Broward, FL', 'Palm Beach, FL']"
                    try:
                        # Try to parse as Python list string
                        import ast
                        county_list = ast.literal_eval(service_zip_codes_raw)
                        if isinstance(county_list, list):
                            coverage_counties = county_list
                            # Extract states
                            for county in county_list:
                                if ', ' in county:
                                    state = county.split(', ')[-1]
                                    coverage_states.add(state)
                            coverage_type = 'county' if len(coverage_states) <= 1 else 'state'
                    except:
                        # If parsing fails, treat as empty
                        coverage_type = 'county'
                        coverage_counties = []
                        coverage_states = set()
                        
                else:
                    # Legacy format - treat as raw ZIP codes
                    zip_codes = self._parse_zip_codes(service_zip_codes_raw)
                    for zip_code in zip_codes:
                        try:
                            location_data = location_service.zip_to_location(zip_code)
                            if not location_data.get('error'):
                                county = location_data.get('county', '')
                                state = location_data.get('state', '')
                                
                                if county and state:
                                    county_formatted = f"{county}, {state}"
                                    if county_formatted not in coverage_counties:
                                        coverage_counties.append(county_formatted)
                                        coverage_states.add(state)
                        except Exception:
                            pass
                
                # Determine coverage type
                if len(coverage_states) > 3:
                    coverage_type = 'national'
                elif len(coverage_states) > 1:
                    coverage_type = 'state'
                else:
                    coverage_type = 'county'
        
        return {
            'coverage_type': coverage_type,
            'coverage_states': json.dumps(list(coverage_states)),
            'coverage_counties': json.dumps(coverage_counties)
        }
    
    def _save_vendor(self, vendor_data: Dict[str, Any]) -> bool:
        """Save new vendor to database"""
        
        try:
            conn = sqlite3.connect('smart_lead_router.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO vendors (
                    id, account_id, ghl_contact_id, ghl_user_id, name, email, phone,
                    company_name, service_categories, services_offered, coverage_type,
                    coverage_states, coverage_counties, last_lead_assigned, lead_close_percentage,
                    status, taking_new_work, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (
                vendor_data['id'], vendor_data['account_id'], vendor_data['ghl_contact_id'],
                vendor_data['ghl_user_id'], vendor_data['name'], vendor_data['email'],
                vendor_data['phone'], vendor_data['company_name'], vendor_data['service_categories'],
                vendor_data['services_offered'], vendor_data['coverage_type'],
                vendor_data['coverage_states'], vendor_data['coverage_counties'],
                vendor_data['last_lead_assigned'], vendor_data['lead_close_percentage'],
                vendor_data['status'], vendor_data['taking_new_work']
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving vendor: {e}")
            return False
    
    def _update_vendor(self, vendor_data: Dict[str, Any]) -> bool:
        """Update existing vendor in database"""
        
        try:
            conn = sqlite3.connect('smart_lead_router.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE vendors SET
                    ghl_user_id = ?, name = ?, email = ?, phone = ?,
                    company_name = ?, service_categories = ?, services_offered = ?,
                    coverage_type = ?, coverage_states = ?, coverage_counties = ?,
                    last_lead_assigned = ?, lead_close_percentage = ?, taking_new_work = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                vendor_data['ghl_user_id'], vendor_data['name'], vendor_data['email'],
                vendor_data['phone'], vendor_data['company_name'], vendor_data['service_categories'],
                vendor_data['services_offered'], vendor_data['coverage_type'],
                vendor_data['coverage_states'], vendor_data['coverage_counties'],
                vendor_data['last_lead_assigned'], vendor_data['lead_close_percentage'],
                vendor_data['taking_new_work'], vendor_data['id']
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating vendor: {e}")
            return False
    
    def _delete_vendor(self, vendor_id: str) -> bool:
        """Delete vendor from database"""
        
        try:
            conn = sqlite3.connect('smart_lead_router.db')
            cursor = conn.cursor()
            cursor.execute("DELETE FROM vendors WHERE id = ?", (vendor_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"❌ Error deleting vendor: {e}")
            return False
    
    def _save_lead(self, lead_data: Dict[str, Any]) -> bool:
        """Save new lead to database"""
        
        try:
            conn = sqlite3.connect('smart_lead_router.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO leads (
                    id, account_id, ghl_contact_id, ghl_opportunity_id, customer_name,
                    customer_email, customer_phone, primary_service_category, specific_service_requested,
                    customer_zip_code, service_county, service_state, service_zip_code,
                    status, priority, source, service_details, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (
                lead_data['id'], lead_data['account_id'], lead_data['ghl_contact_id'],
                lead_data.get('ghl_opportunity_id'), lead_data['customer_name'],
                lead_data['customer_email'], lead_data['customer_phone'],
                lead_data['primary_service_category'], lead_data['specific_service_requested'],
                lead_data['customer_zip_code'], lead_data.get('service_county', ''),
                lead_data.get('service_state', ''), lead_data['service_zip_code'],
                lead_data['status'], lead_data['priority'], lead_data['source'],
                lead_data['service_details']
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving lead: {e}")
            return False
    
    def _update_lead(self, lead_data: Dict[str, Any]) -> bool:
        """Update existing lead in database"""
        
        try:
            conn = sqlite3.connect('smart_lead_router.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE leads SET
                    customer_name = ?, customer_email = ?, customer_phone = ?,
                    primary_service_category = ?, specific_service_requested = ?,
                    customer_zip_code = ?, service_county = ?, service_state = ?,
                    service_zip_code = ?, service_details = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                lead_data['customer_name'], lead_data['customer_email'], lead_data['customer_phone'],
                lead_data['primary_service_category'], lead_data['specific_service_requested'],
                lead_data['customer_zip_code'], lead_data.get('service_county', ''),
                lead_data.get('service_state', ''), lead_data['service_zip_code'],
                lead_data['service_details'], lead_data['id']
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating lead: {e}")
            return False
    
    def _delete_lead(self, lead_id: str) -> bool:
        """Delete lead from database"""
        
        try:
            conn = sqlite3.connect('smart_lead_router.db')
            cursor = conn.cursor()
            cursor.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"❌ Error deleting lead: {e}")
            return False
    
    def _verify_sync(self) -> None:
        """Verify sync results"""
        
        try:
            conn = sqlite3.connect('smart_lead_router.db')
            cursor = conn.cursor()
            
            # Vendor stats
            cursor.execute("SELECT COUNT(*) FROM vendors WHERE account_id = ?", (self.account_id,))
            total_vendors = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM vendors WHERE coverage_counties != '[]' AND account_id = ?", (self.account_id,))
            vendors_with_coverage = cursor.fetchone()[0]
            
            # Lead stats
            cursor.execute("SELECT COUNT(*) FROM leads WHERE account_id = ?", (self.account_id,))
            total_leads = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'unassigned' AND account_id = ?", (self.account_id,))
            unassigned_leads = cursor.fetchone()[0]
            
            print(f"\n📊 DATABASE STATUS:")
            print(f"   Vendors: {total_vendors} total, {vendors_with_coverage} with coverage")
            print(f"   Leads: {total_leads} total, {unassigned_leads} unassigned")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error verifying sync: {e}")
    
    # Utility methods
    def _parse_list(self, value: str) -> List[str]:
        """Parse comma-separated list"""
        if not value:
            return []
        return [v.strip() for v in value.split(',') if v.strip()]
    
    def _parse_boolean(self, value: str) -> bool:
        """Parse boolean from string"""
        if not value:
            return True
        return value.lower() in ['yes', 'true', '1', 'active', 'available']
    
    def _parse_percentage(self, value: str) -> float:
        """Parse percentage value"""
        if not value:
            return 0.0
        try:
            clean = value.replace('%', '').strip()
            pct = float(clean)
            if pct <= 1.0:
                pct *= 100
            return max(0.0, min(100.0, pct))
        except:
            return 0.0
    
    def _parse_date(self, value: str) -> Optional[str]:
        """Parse date value"""
        if not value:
            return None
        try:
            from datetime import datetime
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S']:
                try:
                    parsed = datetime.strptime(value, fmt)
                    return parsed.isoformat()
                except ValueError:
                    continue
        except:
            pass
        return None
    
    def _parse_zip_codes(self, zip_codes_raw: str) -> List[str]:
        """Parse ZIP codes from raw string"""
        if not zip_codes_raw:
            return []
        
        # Normalize separators
        normalized = zip_codes_raw.replace(';', ',').replace('\n', ',').replace('\r', ',')
        
        zip_codes = []
        for zip_code in normalized.split(','):
            zip_code = zip_code.strip()
            
            # Handle ZIP+4
            if '-' in zip_code:
                zip_code = zip_code.split('-')[0].strip()
            elif len(zip_code) == 9 and zip_code.isdigit():
                zip_code = zip_code[:5]
            
            # Validate 5-digit ZIP
            if zip_code and len(zip_code) == 5 and zip_code.isdigit():
                if zip_code not in zip_codes:
                    zip_codes.append(zip_code)
        
        return zip_codes
    
    def _derive_service_category(self, specific_service: str) -> str:
        """Derive primary service category from specific service"""
        service_lower = specific_service.lower()
        
        # Use same logic as webhook_routes.py
        if any(word in service_lower for word in ['engine', 'motor', 'generator', 'propulsion']):
            return 'Engines and Generators'
        elif any(word in service_lower for word in ['maintenance', 'cleaning', 'detailing', 'oil', 'wash']):
            return 'Boat Maintenance'
        elif any(word in service_lower for word in ['electrical', 'plumbing', 'ac', 'air conditioning', 'sound']):
            return 'Marine Systems'
        elif any(word in service_lower for word in ['repair', 'fiberglass', 'welding', 'hull']):
            return 'Boat and Yacht Repair'
        elif any(word in service_lower for word in ['dock', 'slip', 'mooring', 'marina']):
            return 'Docking and Storage'
        else:
            return 'General Services'


def main():
    """Main execution"""
    print("🚀 GHL AS SINGLE SOURCE OF TRUTH SYNC")
    print("=" * 50)
    print("This script validates database records against GoHighLevel")
    print("Any discrepancies are resolved by updating the database")
    print("")
    
    try:
        sync = GHLTruthSync()
        success = sync.sync_all_data()
        
        if success:
            print(f"\n🎉 SYNC COMPLETED SUCCESSFULLY!")
            print("   ✅ Database now matches GoHighLevel (single source of truth)")
            print("   ✅ All records validated and synchronized")
        else:
            print(f"\n❌ SYNC FAILED!")
            print("   Check logs for details")
        
    except Exception as e:
        print(f"❌ Critical error: {e}")
        logger.exception("GHL truth sync failed")


if __name__ == '__main__':
    main()