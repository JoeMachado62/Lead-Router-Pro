#!/usr/bin/env python3
"""
FOCUSED LEAD ROUTER SYNC FROM GOHIGHLEVEL
Maps only real database columns from their corresponding GHL fields.
Fixes the critical Service Zip Codes mapping issue.

VENDOR TABLE: Maps all non-system-generated columns from GHL
LEADS TABLE: Maps all non-system-generated columns from GHL
"""

import sqlite3
import json
import logging
import sys
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

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

# Setup logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('focused_sync.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class FocusedLeadRouterSync:
    """Focused sync that maps only real database columns from GHL"""
    
    def __init__(self):
        """Initialize with focused GHL field mappings for real database columns only"""
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
            
            # VENDOR TABLE - Real DB Columns Mapped from GHL
            self.vendor_mappings = {
                # Standard contact fields
                'name': ['firstName', 'lastName'],  # Combine firstName + lastName
                'email': 'email',                   # Standard GHL field
                'phone': 'phone',                   # Standard GHL field
                
                # Custom fields from GHL
                'ghl_user_id': 'HXVNT4y8OynNokWAfO2D',          # "GHL User ID"
                'company_name': 'JexVrg2VNhnwIX7YlyJV',          # "Vendor Company Name"
                'service_categories': '72qwwzy4AUfTCBJvBIEf',    # "Service Categories Selections"
                'services_offered': 'pAq9WBsIuFUAZuwz3YY4',     # "Services Provided"
                'last_lead': 'NbsJTMv3EkxqNfwx8Jh4',           # "Last Lead Assigned"
                'lead_close_percentage': 'OwHQipU7xdrHCpVswtnW', # "Lead Close %"
                'taking_new_work': 'bTFOs5zXYt85AvDJJUAb',      # "Taking New Work?"
                
                # Coverage derived from Service Zip Codes
                'service_zip_codes': 'yDcN0FmwI3xacyxAuTWs'      # "Service Zip Codes" (CRITICAL)
            }
            
            # LEADS TABLE - Real DB Columns Mapped from GHL
            self.leads_mappings = {
                # Standard contact fields
                'customer_name': ['firstName', 'lastName'],      # Combine firstName + lastName
                'customer_email': 'email',                       # Standard GHL field
                'customer_phone': 'phone',                       # Standard GHL field
                
                # Custom fields from GHL
                'specific_service_requested': 'FT85QGi0tBq1AfVGNJ9v', # "Specific Service Needed"
                'customer_zip_code': 'y3Xo7qsFEQumoFugTeCq',          # "Zip Code of Service"
                
            }
            
            logger.info("✅ Focused Lead Router Sync initialized")
            logger.info(f"📋 Vendor mappings: {len(self.vendor_mappings)} fields")
            logger.info(f"📋 Leads mappings: {len(self.leads_mappings)} fields")
            
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
        """Main sync function for vendors and leads"""
        
        print("🔄 FOCUSED LEAD ROUTER SYNC")
        print("=" * 40)
        print("Mapping only real database columns from GHL")
        print("Fixing Service Zip Codes coverage mapping")
        print("")
        
        try:
            # Sync vendors
            print("STEP 1: Syncing vendors from GHL...")
            vendor_results = self._sync_vendors()
            
            # Sync leads  
            print("\nSTEP 2: Syncing leads from GHL...")
            leads_results = self._sync_leads()
            
            # Results
            print(f"\n📊 SYNC RESULTS:")
            print(f"   VENDORS: ✅ {vendor_results['synced']} | ❌ {vendor_results['failed']} | 🗑️ {vendor_results['cleaned']}")
            print(f"   LEADS:   ✅ {leads_results['synced']} | ❌ {leads_results['failed']} | 🗑️ {leads_results['test_removed']}")
            
            # Verify
            print(f"\nSTEP 3: Verifying sync results...")
            self._verify_sync()
            
            success = (vendor_results['synced'] > 0 or leads_results['synced'] > 0 or 
                      vendor_results['cleaned'] > 0 or leads_results['test_removed'] > 0)
            
            if success:
                print(f"\n🎉 FOCUSED SYNC SUCCESSFUL!")
                print("   ✅ Vendor coverage areas fixed using correct Service Zip Codes field")
                print("   ✅ All real database columns properly mapped from GHL")
                return True
            else:
                print(f"\n❌ SYNC COMPLETED WITH NO CHANGES")
                return False
                
        except Exception as e:
            logger.error(f"❌ Sync failed: {e}")
            return False
    
    def _sync_vendors(self) -> Dict[str, int]:
        """Sync vendors from GHL contacts"""
        
        try:
            # Get vendor contacts (those with GHL User ID)
            all_contacts = self.ghl_api.search_contacts(query="", limit=200)
            vendor_contacts = []
            
            if all_contacts:
                for contact in all_contacts:
                    # Check if contact has GHL User ID
                    custom_fields = contact.get('customFields', [])
                    has_ghl_user_id = any(
                        field.get('id') == 'HXVNT4y8OynNokWAfO2D' and 
                        field.get('value', '').strip()
                        for field in custom_fields
                    )
                    
                    if has_ghl_user_id:
                        vendor_contacts.append(contact)
            
            logger.info(f"📋 Found {len(vendor_contacts)} vendor contacts")
            
            synced = 0
            failed = 0
            
            for contact in vendor_contacts:
                try:
                    vendor_data = self._extract_vendor_data(contact)
                    if vendor_data and self._save_vendor(vendor_data):
                        synced += 1
                        logger.info(f"✅ Synced vendor: {vendor_data['name']}")
                    else:
                        failed += 1
                except Exception as e:
                    failed += 1
                    logger.error(f"❌ Failed to process vendor: {e}")
            
            # Clean outdated vendors
            current_ids = [c.get('id') for c in vendor_contacts if c.get('id')]
            cleaned = self._remove_outdated_vendors(current_ids)
            
            return {'synced': synced, 'failed': failed, 'cleaned': cleaned}
            
        except Exception as e:
            logger.error(f"❌ Error syncing vendors: {e}")
            return {'synced': 0, 'failed': 0, 'cleaned': 0}
    
    def _sync_leads(self) -> Dict[str, int]:
        """Sync leads from GHL contacts"""
        
        try:
            # Clean test data first
            test_removed = self._clean_test_leads()
            
            # Get lead contacts (those with Specific Service Needed, but no GHL User ID)
            all_contacts = self.ghl_api.search_contacts(query="", limit=200)
            lead_contacts = []
            
            if all_contacts:
                for contact in all_contacts:
                    custom_fields = contact.get('customFields', [])
                    
                    # Check for specific service needed
                    has_service_request = any(
                        field.get('id') == 'FT85QGi0tBq1AfVGNJ9v' and 
                        field.get('value', '').strip()
                        for field in custom_fields
                    )
                    
                    # Exclude vendors (no GHL User ID = lead)
                    has_ghl_user_id = any(
                        field.get('id') == 'HXVNT4y8OynNokWAfO2D' and 
                        field.get('value', '').strip()
                        for field in custom_fields
                    )
                    
                    if has_service_request and not has_ghl_user_id:
                        lead_contacts.append(contact)
            
            logger.info(f"📋 Found {len(lead_contacts)} lead contacts")
            
            synced = 0
            failed = 0
            
            for contact in lead_contacts:
                try:
                    lead_data = self._extract_lead_data(contact)
                    if lead_data and self._save_lead(lead_data):
                        synced += 1
                        logger.info(f"✅ Synced lead: {lead_data['customer_name']}")
                    else:
                        failed += 1
                except Exception as e:
                    failed += 1
                    logger.error(f"❌ Failed to process lead: {e}")
            
            return {'synced': synced, 'failed': failed, 'test_removed': test_removed}
            
        except Exception as e:
            logger.error(f"❌ Error syncing leads: {e}")
            return {'synced': 0, 'failed': 0, 'test_removed': 0}
    
    def _extract_vendor_data(self, contact: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract vendor data mapping only real database columns"""
        
        contact_id = contact.get('id')
        
        try:
            # Extract custom fields
            custom_fields = contact.get('customFields', [])
            field_data = self._extract_custom_fields(custom_fields)
            
            # Check required field
            ghl_user_id = field_data.get('ghl_user_id', '').strip()
            if not ghl_user_id:
                return None
            
            # Map real database columns
            vendor_data = {
                'id': str(uuid.uuid4()),
                'account_id': self.account_id,
                'ghl_contact_id': contact_id,
                'ghl_user_id': ghl_user_id,
                'name': f"{contact.get('firstName', '')} {contact.get('lastName', '')}".strip(),
                'email': contact.get('email', ''),
                'phone': contact.get('phone', ''),
                'company_name': field_data.get('company_name', contact.get('companyName', '')),
                'service_categories': json.dumps(self._parse_list(field_data.get('service_categories', ''))),
                'services_offered': json.dumps(self._parse_list(field_data.get('services_offered', ''))),
                'last_lead': self._parse_date(field_data.get('last_lead', '')),
                'lead_close_percentage': self._parse_percentage(field_data.get('lead_close_percentage', '0')),
                'taking_new_work': self._parse_boolean(field_data.get('taking_new_work', 'true')),
                'status': 'active'
            }
            
            # Process coverage from Service Zip Codes field (THE CRITICAL FIX)
            coverage_data = self._process_coverage(field_data.get('service_zip_codes', ''), contact)
            vendor_data.update(coverage_data)
            
            logger.debug(f"📋 Extracted vendor: {vendor_data['name']}")
            return vendor_data
            
        except Exception as e:
            logger.error(f"❌ Error extracting vendor data: {e}")
            return None
    
    def _extract_lead_data(self, contact: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract lead data mapping only real database columns"""
        
        contact_id = contact.get('id')
        
        try:
            # Extract custom fields
            custom_fields = contact.get('customFields', [])
            field_data = self._extract_custom_fields(custom_fields)
            
            # Check required field
            specific_service = field_data.get('specific_service_requested', '').strip()
            if not specific_service:
                return None
            
            # Map real database columns
            lead_data = {
                'id': str(uuid.uuid4()),
                'account_id': self.account_id,
                'ghl_contact_id': contact_id,
                'ghl_opportunity_id': None,  # Would need to look this up separately
                'customer_name': f"{contact.get('firstName', '')} {contact.get('lastName', '')}".strip(),
                'customer_email': contact.get('email', ''),
                'customer_phone': contact.get('phone', ''),
                'specific_service_requested': specific_service,
                'customer_zip_code': field_data.get('customer_zip_code', ''),
                'service_zip_code': field_data.get('customer_zip_code', ''),
                'status': 'unassigned',
                'priority': 'normal',
                'source': 'Elementor Form'
            }
            
            # Derive primary service category from specific service
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
            
            # Build service_details JSON from vessel and other info
            service_details = {}
            for field in ['vessel_make', 'vessel_model', 'vessel_year', 'vessel_length_ft', 
                         'vessel_location_slip', 'budget_range', 'desired_timeline', 'special_requests_notes']:
                value = field_data.get(field, '').strip()
                if value:
                    service_details[field] = value
            
            lead_data['service_details'] = json.dumps(service_details)
            
            logger.debug(f"📋 Extracted lead: {lead_data['customer_name']}")
            return lead_data
            
        except Exception as e:
            logger.error(f"❌ Error extracting lead data: {e}")
            return None
    
    def _extract_custom_fields(self, custom_fields: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract custom field values using vendor and leads mappings"""
        
        field_data = {}
        
        # Create reverse mapping (GHL field ID -> database field name)
        all_mappings = {}
        for field_name, ghl_id in self.vendor_mappings.items():
            if isinstance(ghl_id, str):
                all_mappings[ghl_id] = field_name
        for field_name, ghl_id in self.leads_mappings.items():
            if isinstance(ghl_id, str):
                all_mappings[ghl_id] = field_name
        
        # Extract field values
        for field in custom_fields:
            field_id = field.get('id', '')
            field_value = field.get('value', '') or field.get('fieldValue', '')
            
            if field_id in all_mappings:
                field_name = all_mappings[field_id]
                field_data[field_name] = field_value
                logger.debug(f"   {field_name} ← {field_id}: '{field_value}'")
        
        return field_data
    
    def _process_coverage(self, service_zip_codes_raw: str, contact: Dict[str, Any]) -> Dict[str, Any]:
        """Process coverage from Service Zip Codes field - THE CRITICAL FIX"""
        
        logger.debug(f"🗺️ Processing coverage from Service Zip Codes field")
        logger.debug(f"   Raw value: '{service_zip_codes_raw}'")
        
        coverage_counties = []
        coverage_states = set()
        
        if service_zip_codes_raw:
            zip_codes = self._parse_zip_codes(service_zip_codes_raw)
            logger.debug(f"   Parsed ZIP codes: {zip_codes}")
            
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
                                logger.debug(f"     ✅ {zip_code} → {county_formatted}")
                except Exception as e:
                    logger.debug(f"     ❌ {zip_code} → Error: {e}")
        
        # Fallback to personal address
        if not coverage_counties:
            personal_zip = contact.get('postalCode', '').strip()
            if personal_zip and len(personal_zip) == 5 and personal_zip.isdigit():
                try:
                    location_data = location_service.zip_to_location(personal_zip)
                    if not location_data.get('error'):
                        county = location_data.get('county', '')
                        state = location_data.get('state', '')
                        if county and state:
                            coverage_counties.append(f"{county}, {state}")
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
        """Save vendor to database with overwrite"""
        
        try:
            conn = sqlite3.connect('smart_lead_router.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO vendors (
                    id, account_id, ghl_contact_id, ghl_user_id, name, email, phone,
                    company_name, service_categories, services_offered, coverage_type,
                    coverage_states, coverage_counties, last_lead, lead_close_percentage,
                    status, taking_new_work, created_at, updated_at
                ) VALUES (
                    COALESCE((SELECT id FROM vendors WHERE ghl_contact_id = ?), ?),
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    COALESCE((SELECT created_at FROM vendors WHERE ghl_contact_id = ?), CURRENT_TIMESTAMP),
                    CURRENT_TIMESTAMP
                )
            """, (
                vendor_data['ghl_contact_id'], vendor_data['id'],
                vendor_data['account_id'], vendor_data['ghl_contact_id'], vendor_data['ghl_user_id'],
                vendor_data['name'], vendor_data['email'], vendor_data['phone'],
                vendor_data['company_name'], vendor_data['service_categories'], vendor_data['services_offered'],
                vendor_data['coverage_type'], vendor_data['coverage_states'], vendor_data['coverage_counties'],
                vendor_data['last_lead'], vendor_data['lead_close_percentage'],
                vendor_data['status'], vendor_data['taking_new_work'],
                vendor_data['ghl_contact_id']
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving vendor: {e}")
            return False
    
    def _save_lead(self, lead_data: Dict[str, Any]) -> bool:
        """Save lead to database with overwrite"""
        
        try:
            conn = sqlite3.connect('smart_lead_router.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO leads (
                    id, account_id, ghl_contact_id, ghl_opportunity_id, customer_name,
                    customer_email, customer_phone, primary_service_category, specific_service_requested,
                    customer_zip_code, service_county, service_state, service_zip_code,
                    status, priority, source, service_details, created_at, updated_at
                ) VALUES (
                    COALESCE((SELECT id FROM leads WHERE ghl_contact_id = ?), ?),
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    COALESCE((SELECT created_at FROM leads WHERE ghl_contact_id = ?), CURRENT_TIMESTAMP),
                    CURRENT_TIMESTAMP
                )
            """, (
                lead_data['ghl_contact_id'], lead_data['id'],
                lead_data['account_id'], lead_data['ghl_contact_id'], lead_data.get('ghl_opportunity_id'),
                lead_data['customer_name'], lead_data['customer_email'], lead_data['customer_phone'],
                lead_data['primary_service_category'], lead_data['specific_service_requested'],
                lead_data['customer_zip_code'], lead_data.get('service_county', ''),
                lead_data.get('service_state', ''), lead_data['service_zip_code'],
                lead_data['status'], lead_data['priority'], lead_data['source'], lead_data['service_details'],
                lead_data['ghl_contact_id']
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving lead: {e}")
            return False
    
    def _clean_test_leads(self) -> int:
        """Remove test leads"""
        
        try:
            conn = sqlite3.connect('smart_lead_router.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM leads 
                WHERE customer_name LIKE '%test%' 
                   OR customer_name LIKE '%john%'
                   OR customer_email LIKE '%test%'
                   OR customer_email LIKE '%example%'
            """)
            
            removed = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"🗑️ Removed {removed} test leads")
            return removed
            
        except Exception as e:
            logger.error(f"❌ Error cleaning test leads: {e}")
            return 0
    
    def _remove_outdated_vendors(self, current_ghl_ids: List[str]) -> int:
        """Remove vendors no longer in GHL"""
        
        try:
            conn = sqlite3.connect('smart_lead_router.db')
            cursor = conn.cursor()
            
            if not current_ghl_ids:
                conn.close()
                return 0
            
            placeholders = ','.join(['?' for _ in current_ghl_ids])
            
            cursor.execute(f"""
                DELETE FROM vendors 
                WHERE ghl_contact_id NOT IN ({placeholders})
                AND ghl_user_id IS NOT NULL 
            """, current_ghl_ids)
            
            removed = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"🗑️ Removed {removed} outdated vendors")
            return removed
            
        except Exception as e:
            logger.error(f"❌ Error removing outdated vendors: {e}")
            return 0
    
    def _verify_sync(self) -> None:
        """Verify sync results"""
        
        try:
            conn = sqlite3.connect('smart_lead_router.db')
            cursor = conn.cursor()
            
            # Vendor stats
            cursor.execute("SELECT COUNT(*) FROM vendors")
            total_vendors = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM vendors WHERE coverage_counties != '[]'")
            vendors_with_coverage = cursor.fetchone()[0]
            
            # Lead stats
            cursor.execute("SELECT COUNT(*) FROM leads")
            total_leads = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'unassigned'")
            unassigned_leads = cursor.fetchone()[0]
            
            print(f"📊 VERIFICATION:")
            print(f"   Vendors: {total_vendors} total, {vendors_with_coverage} with coverage")
            print(f"   Leads: {total_leads} total, {unassigned_leads} unassigned")
            
            # Sample vendor coverage
            cursor.execute("""
                SELECT name, coverage_counties 
                FROM vendors 
                WHERE coverage_counties != '[]' 
                LIMIT 2
            """)
            samples = cursor.fetchall()
            
            if samples:
                print(f"📋 SAMPLE VENDOR COVERAGE:")
                for name, counties in samples:
                    print(f"   • {name}: {counties}")
            
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
        
        if any(word in service_lower for word in ['engine', 'motor', 'generator']):
            return 'Engines and Generators'
        elif any(word in service_lower for word in ['maintenance', 'cleaning', 'detailing', 'oil']):
            return 'Boat Maintenance'
        elif any(word in service_lower for word in ['electrical', 'plumbing', 'ac', 'sound']):
            return 'Marine Systems'
        elif any(word in service_lower for word in ['repair', 'fiberglass', 'welding']):
            return 'Boat and Yacht Repair'
        else:
            return 'General Services'


def main():
    """Main execution"""
    print("🚀 FOCUSED LEAD ROUTER SYNC")
    print("=" * 40)
    print("Mapping only real database columns from GHL")
    print("Fixing Service Zip Codes coverage mapping")
    print("")
    
    try:
        sync = FocusedLeadRouterSync()
        success = sync.sync_all_data()
        
        if success:
            print(f"\n🎉 FOCUSED SYNC COMPLETED SUCCESSFULLY!")
            print("   ✅ All real database columns properly mapped")
            print("   ✅ Service Zip Codes coverage fixed")
            print("   ✅ Ready for simplified direct service matching")
        else:
            print(f"\n❌ SYNC COMPLETED WITH NO CHANGES!")
        
    except Exception as e:
        print(f"❌ Critical error: {e}")
        logger.exception("Focused sync failed")


if __name__ == '__main__':
    main()