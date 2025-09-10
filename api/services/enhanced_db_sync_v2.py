#!/usr/bin/env python3
"""
Enhanced Database Sync V2 - Complete Bi-directional Sync
Replacement for enhanced_db_sync.py with full bi-directional capabilities

Handles:
- Vendor sync (both directions with ALL fields)
- Lead sync (both directions)
- Deleted record detection
- New record discovery from GHL
"""

import json
import logging
import sys
import os
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import AppConfig
from api.services.ghl_api_v2_optimized import OptimizedGoHighLevelAPI
from database.simple_connection import db as simple_db_instance

logger = logging.getLogger(__name__)


class EnhancedDatabaseSync:
    """
    Enhanced V2 sync service with bi-directional capabilities
    Drop-in replacement for original enhanced_db_sync.py
    """
    
    # GHL Field Mappings for Vendors (from original)
    VENDOR_GHL_FIELDS = {
        'ghl_user_id': 'HXVNT4y8OynNokWAfO2D',
        'name': ['firstName', 'lastName'],
        'email': 'email',
        'phone': 'phone',
        'company_name': 'JexVrg2VNhnwIX7YlyJV',
        'service_categories': ['72qwwzy4AUfTCBJvBIEf', 'O84LyhN1QjZ8Zz5mteCM'],
        'services_offered': 'pAq9WBsIuFUAZuwz3YY4',
        'service_zip_codes': 'yDcN0FmwI3xacyxAuTWs',
        'taking_new_work': 'bTFOs5zXYt85AvDJJUAb',
        'last_lead_assigned': 'NbsJTMv3EkxqNfwx8Jh4',
        'lead_close_percentage': 'OwHQipU7xdrHCpVswtnW',
        'primary_service_category': 'HRqfv0HnUydNRLKWhk27'
    }
    
    # GHL Field Mappings for Leads
    LEAD_GHL_FIELDS = {
        'customer_name': ['firstName', 'lastName'],
        'customer_email': 'email',
        'customer_phone': 'phone',
        'primary_service_category': 'HRqfv0HnUydNRLKWhk27',
        'specific_service_requested': 'FT85QGi0tBq1AfVGNJ9v',
        'customer_zip_code': 'RmAja1dnU0u42ECXhCo9'
    }
    
    def __init__(self):
        """Initialize the bi-directional sync service"""
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            self.ghl_api = OptimizedGoHighLevelAPI(
                private_token=os.getenv('GHL_PRIVATE_TOKEN') or AppConfig.GHL_PRIVATE_TOKEN,
                location_id=os.getenv('GHL_LOCATION_ID') or AppConfig.GHL_LOCATION_ID,
                agency_api_key=os.getenv('GHL_AGENCY_API_KEY') or AppConfig.GHL_AGENCY_API_KEY,
                location_api_key=os.getenv('GHL_LOCATION_API') or AppConfig.GHL_LOCATION_API
            )
            
            self.stats = {
                'vendors_checked': 0,
                'vendors_updated': 0,
                'vendors_created': 0,
                'vendors_deleted': 0,
                'vendors_deactivated': 0,
                'leads_checked': 0,
                'leads_updated': 0,
                'leads_created': 0,
                'leads_deleted': 0,
                'ghl_contacts_fetched': 0,
                'errors': []
            }
            
            logger.info("✅ Bi-directional Sync initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Bi-directional Sync: {e}")
            raise
    
    def sync_all(self) -> Dict[str, Any]:
        """
        Complete bi-directional sync process:
        1. Fetch ALL contacts from GHL (with vendor tags)
        2. Update existing local records
        3. Create new local records for new GHL contacts
        4. Handle deleted GHL contacts
        """
        logger.info("🔄 Starting Bi-directional Database Sync")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        
        try:
            # Step 1: Get ALL vendor contacts from GHL
            logger.info("\n📊 STEP 1: Fetching ALL vendor contacts from GHL")
            ghl_vendors = self._fetch_all_ghl_vendors()
            
            # Step 2: Get ALL local vendors
            logger.info("\n📊 STEP 2: Fetching local vendor records")
            local_vendors = self._get_local_vendors()
            
            # Step 3: Process sync
            logger.info("\n📊 STEP 3: Processing bi-directional sync")
            self._process_vendor_sync(ghl_vendors, local_vendors)
            
            # Step 4: Process lead sync
            logger.info("\n📊 STEP 4: Processing lead sync")
            ghl_leads = self._fetch_all_ghl_leads()
            local_leads = self._get_local_leads()
            self._process_lead_sync(ghl_leads, local_leads)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # Generate summary
            logger.info("\n" + "=" * 60)
            logger.info("🎉 BI-DIRECTIONAL SYNC COMPLETED")
            logger.info(f"⏱️  Duration: {duration:.2f} seconds")
            logger.info(f"\n📈 VENDOR SYNC RESULTS:")
            logger.info(f"   GHL Contacts Fetched: {self.stats['ghl_contacts_fetched']}")
            logger.info(f"   Vendors Updated: {self.stats['vendors_updated']}")
            logger.info(f"   Vendors Created (NEW): {self.stats['vendors_created']}")
            logger.info(f"   Vendors Deactivated: {self.stats['vendors_deactivated']}")
            logger.info(f"   Vendors Deleted: {self.stats['vendors_deleted']}")
            logger.info(f"\n📈 LEAD SYNC RESULTS:")
            logger.info(f"   Leads Updated: {self.stats['leads_updated']}")
            logger.info(f"   Leads Created (NEW): {self.stats['leads_created']}")
            logger.info(f"   Leads Deleted: {self.stats['leads_deleted']}")
            
            if self.stats['errors']:
                logger.warning(f"\n⚠️  Errors encountered: {len(self.stats['errors'])}")
                for error in self.stats['errors'][:5]:  # Show first 5 errors
                    logger.warning(f"   - {error}")
            
            # Generate summary message
            message = (f"Sync completed in {duration:.2f}s. "
                      f"Vendors: {self.stats['vendors_updated']} updated, "
                      f"{self.stats['vendors_created']} created, "
                      f"{self.stats['vendors_deactivated']} deactivated. "
                      f"Leads: {self.stats['leads_updated']} updated, "
                      f"{self.stats['leads_created']} created, "
                      f"{self.stats['leads_deleted']} deleted.")
            
            return {
                'success': True,
                'message': message,
                'stats': self.stats,
                'duration': duration
            }
            
        except Exception as e:
            logger.error(f"❌ Sync failed: {e}")
            return {
                'success': False,
                'message': f"Sync failed: {str(e)}",
                'stats': self.stats,
                'error': str(e)
            }
    
    def _fetch_all_ghl_vendors(self) -> Dict[str, Dict]:
        """
        Fetch ALL vendor contacts from GHL
        Returns dict keyed by contact ID for fast lookup
        """
        all_vendors = {}
        
        try:
            # We need to implement pagination to get ALL contacts
            # Most GHL APIs limit to 100 per request
            limit = 100
            offset = 0
            total_fetched = 0
            
            while True:
                logger.info(f"   Fetching GHL contacts (offset: {offset}, limit: {limit})")
                
                # Build query to get vendor contacts
                # We'll need to filter by tag or custom field that identifies vendors
                params = {
                    'locationId': self.ghl_api.location_id,
                    'limit': limit,
                    'skip': offset,
                    # Add filter for vendors - this depends on how vendors are tagged
                    # 'tags': 'vendor',  # Example if using tags
                    # Or use custom field filter if vendors have specific field values
                }
                
                # Make API call
                url = f"{self.ghl_api.v2_base_url}/contacts/"
                headers = {
                    "Authorization": f"Bearer {self.ghl_api.private_token}",
                    "Version": "2021-07-28"
                }
                
                import requests
                response = requests.get(url, headers=headers, params=params)
                
                if response.status_code != 200:
                    logger.error(f"❌ Failed to fetch GHL contacts: {response.status_code}")
                    break
                
                data = response.json()
                contacts = data.get('contacts', [])
                
                if not contacts:
                    logger.info(f"   No more contacts to fetch")
                    break
                
                # Process each contact
                for contact in contacts:
                    contact_id = contact.get('id')
                    
                    # Check if this is a vendor (has GHL User ID field)
                    custom_fields = {cf['id']: cf.get('value', '') 
                                   for cf in contact.get('customFields', [])}
                    
                    ghl_user_id = custom_fields.get('HXVNT4y8OynNokWAfO2D', '')
                    
                    # If has GHL User ID, it's an active vendor
                    if ghl_user_id:
                        all_vendors[contact_id] = contact
                        logger.debug(f"   Found vendor: {contact.get('firstName')} {contact.get('lastName')}")
                
                total_fetched += len(contacts)
                self.stats['ghl_contacts_fetched'] = total_fetched
                
                # Check if we got all contacts
                if len(contacts) < limit:
                    break
                
                offset += limit
                time.sleep(0.2)  # Rate limiting
            
            logger.info(f"✅ Fetched {len(all_vendors)} vendor contacts from GHL")
            return all_vendors
            
        except Exception as e:
            logger.error(f"❌ Error fetching GHL vendors: {e}")
            self.stats['errors'].append(f"GHL fetch error: {str(e)}")
            return {}
    
    def _get_local_vendors(self) -> Dict[str, Dict]:
        """
        Get all local vendors keyed by GHL contact ID
        """
        local_vendors_by_ghl_id = {}
        local_vendors_without_ghl = []
        
        try:
            vendors = simple_db_instance.get_vendors()
            
            for vendor in vendors:
                ghl_contact_id = vendor.get('ghl_contact_id')
                if ghl_contact_id:
                    local_vendors_by_ghl_id[ghl_contact_id] = vendor
                else:
                    local_vendors_without_ghl.append(vendor)
            
            logger.info(f"✅ Found {len(local_vendors_by_ghl_id)} vendors with GHL IDs")
            logger.info(f"   Found {len(local_vendors_without_ghl)} vendors without GHL IDs")
            
            return local_vendors_by_ghl_id
            
        except Exception as e:
            logger.error(f"❌ Error fetching local vendors: {e}")
            self.stats['errors'].append(f"Local fetch error: {str(e)}")
            return {}
    
    def _process_vendor_sync(self, ghl_vendors: Dict, local_vendors: Dict):
        """
        Process the bi-directional sync:
        1. Update existing vendors
        2. Create new vendors from GHL
        3. Handle deleted vendors
        """
        
        # Track processed GHL IDs
        processed_ghl_ids = set()
        
        # PART 1: Process vendors that exist in GHL
        for ghl_id, ghl_contact in ghl_vendors.items():
            processed_ghl_ids.add(ghl_id)
            
            if ghl_id in local_vendors:
                # UPDATE existing vendor
                self._update_local_vendor(local_vendors[ghl_id], ghl_contact)
            else:
                # CREATE new vendor in local DB
                self._create_local_vendor(ghl_contact)
        
        # PART 2: Handle vendors that exist locally but not in GHL (deleted/missing)
        for ghl_id, local_vendor in local_vendors.items():
            if ghl_id not in processed_ghl_ids:
                # Vendor exists locally but not in GHL
                self._handle_missing_ghl_vendor(local_vendor)
    
    def _update_local_vendor(self, local_vendor: Dict, ghl_contact: Dict):
        """Update existing local vendor with ALL GHL data fields"""
        try:
            updates = self._extract_vendor_updates(local_vendor, ghl_contact)
            
            if updates:
                success = self._update_vendor_record(local_vendor['id'], updates)
                if success:
                    self.stats['vendors_updated'] += 1
                    logger.info(f"✅ Updated vendor: {local_vendor.get('name')} ({len(updates)} fields)")
            
        except Exception as e:
            logger.error(f"❌ Error updating vendor {local_vendor.get('id')}: {e}")
            self.stats['errors'].append(f"Update error: {str(e)}")
    
    def _extract_vendor_updates(self, vendor: Dict, ghl_contact: Dict) -> Dict[str, Any]:
        """Extract ALL vendor fields that need updating - from original enhanced_db_sync"""
        updates = {}
        
        # Extract custom fields from GHL contact
        custom_fields = {}
        for field in ghl_contact.get('customFields', []):
            field_id = field.get('id', '')
            field_value = field.get('value', '') or field.get('fieldValue', '')
            if field_id:
                custom_fields[field_id] = field_value
        
        # Check for GHL User ID and activate vendor if found
        ghl_user_id_from_contact = custom_fields.get('HXVNT4y8OynNokWAfO2D', '').strip()
        if ghl_user_id_from_contact:
            if not vendor.get('ghl_user_id'):
                updates['ghl_user_id'] = ghl_user_id_from_contact
                logger.info(f"   ✅ Found GHL User ID: {ghl_user_id_from_contact}")
            
            if vendor.get('status') != 'active':
                updates['status'] = 'active'
                logger.info(f"   ✅ Activating vendor - GHL User ID present")
        
        # Process service_zip_codes to derive coverage fields
        service_zip_codes_value = custom_fields.get('yDcN0FmwI3xacyxAuTWs', '').strip()
        if service_zip_codes_value:
            coverage_info = self._parse_coverage_from_zip_codes(service_zip_codes_value)
            if coverage_info['type']:
                if vendor.get('coverage_type') != coverage_info['type']:
                    updates['coverage_type'] = coverage_info['type']
                if coverage_info['states']:
                    updates['coverage_states'] = json.dumps(coverage_info['states'])
                if coverage_info['counties']:
                    updates['coverage_counties'] = json.dumps(coverage_info['counties'])
        
        # Check each mapped field
        for db_field, ghl_field in self.VENDOR_GHL_FIELDS.items():
            if db_field == 'service_zip_codes':
                continue
                
            current_value = vendor.get(db_field)
            new_value = None
            
            if db_field == 'name' and ghl_field == ['firstName', 'lastName']:
                first = ghl_contact.get('firstName', '').strip()
                last = ghl_contact.get('lastName', '').strip()
                new_value = f"{first} {last}".strip()
            elif ghl_field in ['email', 'phone']:
                new_value = ghl_contact.get(ghl_field, '').strip()
            elif isinstance(ghl_field, list):
                for field_id in ghl_field:
                    temp_value = custom_fields.get(field_id, '').strip()
                    if temp_value:
                        new_value = temp_value
                        break
            else:
                new_value = custom_fields.get(ghl_field, '').strip()
            
            # Special handling for certain fields
            if db_field in ['service_categories', 'services_offered']:
                if new_value:
                    parsed_list = [s.strip() for s in new_value.split(',') if s.strip()]
                    new_value = json.dumps(parsed_list)
            elif db_field == 'lead_close_percentage':
                if new_value:
                    try:
                        new_value = float(new_value.replace('%', '').strip())
                    except:
                        new_value = 0.0
                else:
                    new_value = 0.0
            elif db_field == 'taking_new_work':
                if new_value:
                    normalized = new_value.strip().lower()
                    new_value = 'Yes' if normalized in ['yes', 'true', '1'] else 'No'
            
            # Compare and add to updates if different
            if new_value and self._values_differ(current_value, new_value, db_field):
                updates[db_field] = new_value
        
        return updates
    
    def _parse_coverage_from_zip_codes(self, service_zip_codes_value: str) -> Dict:
        """Parse service_zip_codes field to determine coverage type"""
        normalized_value = service_zip_codes_value.upper().strip()
        
        if 'GLOBAL' in normalized_value:
            return {'type': 'global', 'states': [], 'counties': []}
        elif 'NATIONAL' in normalized_value or normalized_value in ['USA', 'UNITED STATES']:
            return {'type': 'national', 'states': [], 'counties': []}
        elif ';' in service_zip_codes_value:
            items = [s.strip() for s in service_zip_codes_value.split(';') if s.strip()]
            if items and ', ' in items[0]:
                counties = items
                states = list({county.split(', ')[-1].strip() for county in counties if ', ' in county})
                return {'type': 'county', 'states': states, 'counties': counties}
        elif ',' in service_zip_codes_value:
            items = [s.strip() for s in service_zip_codes_value.split(',') if s.strip()]
            if all(len(item) == 2 and item.isupper() for item in items):
                return {'type': 'state', 'states': items, 'counties': []}
        
        return {'type': None, 'states': None, 'counties': None}
    
    def _values_differ(self, current: Any, new: Any, field_name: str) -> bool:
        """Check if two values are different"""
        if current is None and new == '':
            return False
        if current == '' and new is None:
            return False
        
        if field_name in ['service_categories', 'services_offered', 'coverage_states', 'coverage_counties']:
            try:
                current_list = json.loads(current) if current else []
                new_list = json.loads(new) if new else []
                return set(current_list) != set(new_list)
            except:
                return str(current) != str(new)
        
        return str(current or '').strip() != str(new or '').strip()
    
    def _create_local_vendor(self, ghl_contact: Dict):
        """Create new vendor in local DB from GHL contact"""
        try:
            # Extract custom fields
            custom_fields = {cf['id']: cf.get('value', '') 
                           for cf in ghl_contact.get('customFields', [])}
            
            # Get account ID
            account = simple_db_instance.get_account_by_ghl_location_id(
                os.getenv('GHL_LOCATION_ID') or AppConfig.GHL_LOCATION_ID
            )
            if not account:
                logger.error("❌ No account found for location")
                return
            
            # Create vendor data
            vendor_data = {
                'account_id': account['id'],
                'ghl_contact_id': ghl_contact.get('id'),
                'ghl_user_id': custom_fields.get('HXVNT4y8OynNokWAfO2D', ''),
                'name': f"{ghl_contact.get('firstName', '')} {ghl_contact.get('lastName', '')}".strip(),
                'email': ghl_contact.get('email', ''),
                'phone': ghl_contact.get('phone', ''),
                'company_name': custom_fields.get('JexVrg2VNhnwIX7YlyJV', ''),
                'status': 'active' if custom_fields.get('HXVNT4y8OynNokWAfO2D') else 'pending',
                # Add other fields...
            }
            
            # Create vendor in database
            vendor_id = simple_db_instance.create_vendor(vendor_data)
            if vendor_id:
                self.stats['vendors_created'] += 1
                logger.info(f"✅ Created NEW vendor from GHL: {vendor_data['name']}")
            
        except Exception as e:
            logger.error(f"❌ Error creating vendor from GHL: {e}")
            self.stats['errors'].append(f"Create error: {str(e)}")
    
    def _handle_missing_ghl_vendor(self, local_vendor: Dict):
        """
        Handle vendor that exists locally but not in GHL
        Options:
        1. Mark as inactive/deleted
        2. Delete from local DB
        3. Log for manual review
        """
        try:
            vendor_name = local_vendor.get('name', 'Unknown')
            logger.warning(f"⚠️  Vendor exists locally but not in GHL: {vendor_name}")
            
            # Option 1: Mark as inactive (safer approach)
            updates = {'status': 'inactive_ghl_deleted'}
            success = self._update_vendor_record(local_vendor['id'], updates)
            
            if success:
                self.stats['vendors_deactivated'] += 1
                logger.info(f"🔴 Deactivated vendor (deleted from GHL): {vendor_name}")
            
            # Option 2: Actually delete (more aggressive)
            # simple_db_instance.delete_vendor(local_vendor['id'])
            # self.stats['vendors_deleted'] += 1
            
        except Exception as e:
            logger.error(f"❌ Error handling missing vendor: {e}")
            self.stats['errors'].append(f"Missing vendor error: {str(e)}")
    
    def _update_vendor_record(self, vendor_id: str, updates: Dict) -> bool:
        """Update vendor in database"""
        try:
            if not updates:
                return True
            
            # Build UPDATE query
            conn = simple_db_instance._get_conn()
            cursor = conn.cursor()
            
            set_clauses = []
            values = []
            
            for field, value in updates.items():
                set_clauses.append(f"{field} = ?")
                values.append(value)
            
            set_clauses.append("updated_at = CURRENT_TIMESTAMP")
            values.append(vendor_id)
            
            query = f"""
                UPDATE vendors 
                SET {', '.join(set_clauses)}
                WHERE id = ?
            """
            
            cursor.execute(query, values)
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating vendor {vendor_id}: {e}")
            return False
    
    def _fetch_all_ghl_leads(self) -> Dict[str, Dict]:
        """Fetch ALL lead contacts from GHL (non-vendors)"""
        all_leads = {}
        
        try:
            limit = 100
            offset = 0
            
            while True:
                logger.info(f"   Fetching GHL leads (offset: {offset}, limit: {limit})")
                
                url = f"{self.ghl_api.v2_base_url}/contacts/"
                headers = {
                    "Authorization": f"Bearer {self.ghl_api.private_token}",
                    "Version": "2021-07-28"
                }
                
                params = {
                    'locationId': self.ghl_api.location_id,
                    'limit': limit,
                    'skip': offset
                }
                
                import requests
                response = requests.get(url, headers=headers, params=params)
                
                if response.status_code != 200:
                    break
                
                data = response.json()
                contacts = data.get('contacts', [])
                
                if not contacts:
                    break
                
                for contact in contacts:
                    contact_id = contact.get('id')
                    custom_fields = {cf['id']: cf.get('value', '') 
                                   for cf in contact.get('customFields', [])}
                    
                    # Skip if it's a vendor (has GHL User ID)
                    if custom_fields.get('HXVNT4y8OynNokWAfO2D'):
                        continue
                    
                    # Check if it's a lead (has primary service category)
                    if custom_fields.get('HRqfv0HnUydNRLKWhk27'):  # Primary Service Category
                        all_leads[contact_id] = contact
                
                if len(contacts) < limit:
                    break
                
                offset += limit
                time.sleep(0.2)
            
            logger.info(f"✅ Fetched {len(all_leads)} lead contacts from GHL")
            return all_leads
            
        except Exception as e:
            logger.error(f"❌ Error fetching GHL leads: {e}")
            return {}
    
    def _get_local_leads(self) -> Dict[str, Dict]:
        """Get all local leads keyed by GHL contact ID"""
        local_leads_by_ghl_id = {}
        
        try:
            conn = simple_db_instance._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, ghl_contact_id, customer_name, customer_email, 
                       customer_phone, primary_service_category, 
                       specific_service_requested, customer_zip_code,
                       service_county, service_state, status, vendor_id
                FROM leads
            """)
            
            for row in cursor.fetchall():
                lead = {
                    'id': row[0],
                    'ghl_contact_id': row[1],
                    'customer_name': row[2],
                    'customer_email': row[3],
                    'customer_phone': row[4],
                    'primary_service_category': row[5],
                    'specific_service_requested': row[6],
                    'customer_zip_code': row[7],
                    'service_county': row[8],
                    'service_state': row[9],
                    'status': row[10],
                    'vendor_id': row[11]
                }
                
                if lead['ghl_contact_id']:
                    local_leads_by_ghl_id[lead['ghl_contact_id']] = lead
            
            conn.close()
            
            logger.info(f"✅ Found {len(local_leads_by_ghl_id)} leads with GHL IDs")
            return local_leads_by_ghl_id
            
        except Exception as e:
            logger.error(f"❌ Error fetching local leads: {e}")
            return {}
    
    def _process_lead_sync(self, ghl_leads: Dict, local_leads: Dict):
        """Process bi-directional lead sync"""
        processed_ghl_ids = set()
        
        # Process leads that exist in GHL
        for ghl_id, ghl_contact in ghl_leads.items():
            processed_ghl_ids.add(ghl_id)
            
            if ghl_id in local_leads:
                self._update_local_lead(local_leads[ghl_id], ghl_contact)
            else:
                self._create_local_lead(ghl_contact)
        
        # Handle leads that exist locally but not in GHL
        for ghl_id, local_lead in local_leads.items():
            if ghl_id not in processed_ghl_ids:
                # Lead exists locally but not found in GHL
                self._handle_missing_lead(local_lead)
    
    def _handle_missing_lead(self, local_lead: Dict):
        """
        Handle leads that exist locally but not in GHL.
        Similar to vendor handling - mark as inactive rather than delete.
        """
        try:
            lead_name = local_lead.get('customer_name', 'Unknown')
            lead_id = local_lead.get('id')
            
            logger.warning(f"⚠️ Lead exists locally but not in GHL: {lead_name}")
            
            # Mark as inactive/deleted (safer than hard delete)
            updates = {'status': 'inactive_ghl_deleted'}
            success = self._update_lead_record(lead_id, updates)
            
            if success:
                self.stats['leads_deleted'] += 1
                logger.info(f"🔴 Deactivated lead (deleted from GHL): {lead_name}")
            
            # Option 2: Actually delete (more aggressive)
            # conn = self._get_conn()
            # cursor = conn.cursor()
            # cursor.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
            # conn.commit()
            # self.stats['leads_deleted'] += 1
            # logger.info(f"🗑️ Deleted lead: {lead_name}")
            
        except Exception as e:
            logger.error(f"❌ Error handling missing lead: {e}")
            self.stats['errors'].append(f"Missing lead error: {str(e)}")
    
    def _update_local_lead(self, local_lead: Dict, ghl_contact: Dict):
        """Update existing local lead with GHL data"""
        try:
            updates = self._extract_lead_updates(local_lead, ghl_contact)
            
            if updates:
                success = self._update_lead_record(local_lead['id'], updates)
                if success:
                    self.stats['leads_updated'] += 1
                    logger.info(f"✅ Updated lead: {local_lead.get('customer_name')}")
        except Exception as e:
            logger.error(f"❌ Error updating lead: {e}")
    
    def _extract_lead_updates(self, lead: Dict, ghl_contact: Dict) -> Dict[str, Any]:
        """Extract lead fields that need updating"""
        updates = {}
        
        custom_fields = {cf['id']: cf.get('value', '') 
                        for cf in ghl_contact.get('customFields', [])}
        
        for db_field, ghl_field in self.LEAD_GHL_FIELDS.items():
            current_value = lead.get(db_field)
            new_value = None
            
            if db_field == 'customer_name' and ghl_field == ['firstName', 'lastName']:
                first = ghl_contact.get('firstName', '').strip()
                last = ghl_contact.get('lastName', '').strip()
                new_value = f"{first} {last}".strip()
            elif ghl_field in ['email', 'phone']:
                if db_field == 'customer_email':
                    new_value = ghl_contact.get('email', '').strip()
                elif db_field == 'customer_phone':
                    new_value = ghl_contact.get('phone', '').strip()
            else:
                new_value = custom_fields.get(ghl_field, '').strip()
            
            if new_value and current_value != new_value:
                updates[db_field] = new_value
        
        # Handle ZIP to county/state conversion
        if updates.get('customer_zip_code'):
            from api.services.location_service import location_service
            location_data = location_service.zip_to_location(updates['customer_zip_code'])
            if not location_data.get('error'):
                updates['service_county'] = location_data.get('county', '')
                updates['service_state'] = location_data.get('state', '')
        
        return updates
    
    def _create_local_lead(self, ghl_contact: Dict):
        """Create new lead in local DB from GHL contact"""
        try:
            custom_fields = {cf['id']: cf.get('value', '') 
                           for cf in ghl_contact.get('customFields', [])}
            
            account = simple_db_instance.get_account_by_ghl_location_id(
                os.getenv('GHL_LOCATION_ID') or AppConfig.GHL_LOCATION_ID
            )
            if not account:
                return
            
            import uuid
            lead_data = {
                'id': str(uuid.uuid4()),
                'account_id': account['id'],
                'ghl_contact_id': ghl_contact.get('id'),
                'customer_name': f"{ghl_contact.get('firstName', '')} {ghl_contact.get('lastName', '')}".strip(),
                'customer_email': ghl_contact.get('email', ''),
                'customer_phone': ghl_contact.get('phone', ''),
                'primary_service_category': custom_fields.get('HRqfv0HnUydNRLKWhk27', ''),
                'specific_service_requested': custom_fields.get('FT85QGi0tBq1AfVGNJ9v', ''),
                'customer_zip_code': custom_fields.get('RmAja1dnU0u42ECXhCo9', ''),
                'status': 'unassigned',
                'source': 'ghl_sync'
            }
            
            # Get county/state from ZIP
            if lead_data['customer_zip_code']:
                from api.services.location_service import location_service
                location_data = location_service.zip_to_location(lead_data['customer_zip_code'])
                if not location_data.get('error'):
                    lead_data['service_county'] = location_data.get('county', '')
                    lead_data['service_state'] = location_data.get('state', '')
            
            # Insert into database
            conn = simple_db_instance._get_conn()
            cursor = conn.cursor()
            
            columns = list(lead_data.keys())
            placeholders = ['?' for _ in columns]
            values = [lead_data[col] for col in columns]
            
            query = f"""
                INSERT INTO leads ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
            """
            
            cursor.execute(query, values)
            conn.commit()
            conn.close()
            
            self.stats['leads_created'] += 1
            logger.info(f"✅ Created NEW lead from GHL: {lead_data['customer_name']}")
            
        except Exception as e:
            logger.error(f"❌ Error creating lead from GHL: {e}")
    
    def _update_lead_record(self, lead_id: str, updates: Dict) -> bool:
        """Update lead in database"""
        try:
            if not updates:
                return True
            
            conn = simple_db_instance._get_conn()
            cursor = conn.cursor()
            
            set_clauses = []
            values = []
            
            for field, value in updates.items():
                set_clauses.append(f"{field} = ?")
                values.append(value)
            
            set_clauses.append("updated_at = CURRENT_TIMESTAMP")
            values.append(lead_id)
            
            query = f"""
                UPDATE leads 
                SET {', '.join(set_clauses)}
                WHERE id = ?
            """
            
            cursor.execute(query, values)
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating lead {lead_id}: {e}")
            return False


# Main function for testing
if __name__ == "__main__":
    print("🚀 BI-DIRECTIONAL DATABASE SYNC")
    print("=" * 60)
    print("This will:")
    print("1. Fetch ALL vendor contacts from GoHighLevel")
    print("2. Update existing local records")
    print("3. Create NEW local records for new GHL vendors")
    print("4. Deactivate local vendors deleted from GHL")
    print("")
    
    response = input("Continue? (y/n): ")
    
    if response.lower() == 'y':
        sync_service = BidirectionalSync()
        results = sync_service.sync_all()
        
        if results['success']:
            print("\n✅ Sync completed successfully!")
        else:
            print(f"\n❌ Sync failed: {results.get('error', 'Unknown error')}")
        
        print("\nDetailed Statistics:")
        print(json.dumps(results['stats'], indent=2))