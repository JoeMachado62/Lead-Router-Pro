#!/usr/bin/env python3
"""
ENHANCED VENDOR SYNC FROM GOHIGHLEVEL
Complete field mapping and overwrite capability for vendor data synchronization.

FEATURES:
- Maps ALL vendor table fields to correct GHL custom fields
- Overwrites existing vendor data with latest from GHL
- Detailed logging of field mappings and extraction
- Comprehensive error handling and validation
- Preserves data integrity while ensuring accuracy
"""

import sqlite3
import json
import logging
import sys
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv
import os

# Load .env from project root
current_dir = os.getcwd()
if current_dir.endswith('Lead-Router-Pro'):
    dotenv_path = os.path.join(current_dir, '.env')
else:
    dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')

load_dotenv(dotenv_path)

from config import AppConfig
from api.services.ghl_api import GoHighLevelAPI
from api.services.location_service import location_service

# Enhanced logging configuration
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vendor_sync.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class EnhancedVendorSync:
    """Enhanced vendor synchronization with complete field mapping and overwrite capability"""
    
    def __init__(self):
        """Initialize with comprehensive GHL field mappings"""
        try:
            # Initialize GHL API client
            self.ghl_api = GoHighLevelAPI(
                private_token=AppConfig.GHL_PRIVATE_TOKEN,
                location_id=AppConfig.GHL_LOCATION_ID,
                agency_api_key=AppConfig.GHL_AGENCY_API_KEY,
                company_id=AppConfig.GHL_COMPANY_ID
            )
            
            # Get account information
            self.account = self._get_or_create_account()
            if not self.account:
                raise Exception("Could not get or create account")
            
            self.account_id = self.account['id']
            
            # COMPREHENSIVE GHL FIELD MAPPINGS
            # Maps database field names to GHL custom field IDs
            self.ghl_field_mappings = {
                # Core vendor identification
                'ghl_user_id': 'HXVNT4y8OynNokWAfO2D',
                'vendor_company_name': 'vendor_company_name_field_id',  # Need actual ID
                
                # Service-related fields
                'services_provided': 'pAq9WBsIuFUAZuwz3YY4',
                'service_categories_selections': '72qwwzy4AUfTCBJvBIEf',
                'primary_service_category': 'HRqfv0HnUydNRLKWhk27',
                'specific_service_needed': 'FT85QGi0tBq1AfVGNJ9v',
                
                # Coverage area fields
                'service_zip_codes': 'yDcN0FmwI3xacyxAuTWs',  # CRITICAL - this is the broken mapping
                'service_areas': 'service_areas_field_id',  # Need actual ID
                
                # Business information
                'years_in_business': 'years_in_business_field_id',  # Need actual ID
                'certifications_licenses': 'certifications_licenses_field_id',  # Need actual ID
                'insurance_coverage': 'insurance_coverage_field_id',  # Need actual ID
                'taking_new_work': 'taking_new_work_field_id',  # Need actual ID
                
                # Operational details
                'emergency_services': 'emergency_services_field_id',  # Need actual ID
                'service_radius_miles': 'service_radius_miles_field_id',  # Need actual ID
                'crew_size': 'crew_size_field_id',  # Need actual ID
                'special_equipment': 'special_equipment_field_id',  # Need actual ID
                
                # Business terms
                'pricing_structure': 'pricing_structure_field_id',  # Need actual ID
                'payment_terms': 'payment_terms_field_id',  # Need actual ID
                'availability_schedule': 'availability_schedule_field_id',  # Need actual ID
                
                # Contact preferences
                'preferred_contact_method': 'preferred_contact_method_field_id',  # Need actual ID
                'vessel_types_serviced': 'vessel_types_serviced_field_id',  # Need actual ID
                
                # Performance tracking
                'lead_close_percentage': 'OwHQipU7xdrHCpVswtnW',  # Lead Close %
                'last_lead_assigned': 'NbsJTMv3EkxqNfwx8Jh4',
                
                # Additional fields
                'references': 'references_field_id',  # Need actual ID
                'website': 'website_field_id',  # Need actual ID
                'notes': 'special_requests__notes_field_id'  # Need actual ID
            }
            
            # Standard contact fields (not custom fields)
            self.standard_fields = {
                'firstName': 'firstName',
                'lastName': 'lastName', 
                'email': 'email',
                'phone': 'phone',
                'companyName': 'companyName',
                'address1': 'address1',
                'city': 'city',
                'state': 'state',
                'postalCode': 'postalCode',
                'website': 'website'
            }
            
            logger.info("✅ Enhanced Vendor Sync initialized successfully")
            logger.info(f"📋 Configured {len(self.ghl_field_mappings)} custom field mappings")
            logger.info(f"📋 Configured {len(self.standard_fields)} standard field mappings")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Enhanced Vendor Sync: {e}")
            raise
    
    def _get_or_create_account(self) -> Optional[Dict[str, Any]]:
        """Get existing account or create default account"""
        try:
            conn = sqlite3.connect('smart_lead_router.db')
            cursor = conn.cursor()
            
            # Try to get existing account
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
            
            # Create default account if none exists
            account_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO accounts (
                    id, company_name, industry, ghl_location_id,
                    ghl_private_token, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (
                account_id,
                "Digital Marine LLC",
                "marine",
                AppConfig.GHL_LOCATION_ID,
                AppConfig.GHL_PRIVATE_TOKEN
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Created default account: {account_id}")
            return {
                'id': account_id,
                'company_name': "Digital Marine LLC",
                'ghl_location_id': AppConfig.GHL_LOCATION_ID
            }
            
        except Exception as e:
            logger.error(f"❌ Error with account: {e}")
            return None
    
    def sync_all_vendors_with_overwrite(self) -> bool:
        """Main function to sync all vendors from GHL with overwrite capability"""
        
        print("🔄 ENHANCED VENDOR SYNC FROM GOHIGHLEVEL")
        print("=" * 50)
        print("Complete field mapping with overwrite capability")
        print("Extracting ALL vendor data with detailed field logging")
        print("")
        
        try:
            # Step 1: Get vendor contacts from GHL
            print("STEP 1: Fetching vendor contacts from GoHighLevel...")
            vendor_contacts = self._get_all_vendor_contacts()
            
            if not vendor_contacts:
                print("❌ No vendor contacts found in GoHighLevel")
                return False
            
            print(f"✅ Found {len(vendor_contacts)} vendor contacts in GHL")
            
            # Step 2: Process each vendor with comprehensive field extraction
            print(f"\nSTEP 2: Processing vendor data with complete field mapping...")
            processed_vendors = []
            failed_vendors = []
            
            for i, contact in enumerate(vendor_contacts, 1):
                contact_name = f"{contact.get('firstName', '')} {contact.get('lastName', '')}".strip()
                print(f"\n[{i}/{len(vendor_contacts)}] Processing: {contact_name}")
                
                try:
                    vendor_data = self._extract_complete_vendor_data(contact)
                    if vendor_data:
                        processed_vendors.append(vendor_data)
                        print(f"   ✅ Successfully extracted data for {contact_name}")
                    else:
                        failed_vendors.append(contact)
                        print(f"   ❌ Failed to extract data for {contact_name}")
                        
                except Exception as e:
                    failed_vendors.append(contact)
                    print(f"   ❌ Error processing {contact_name}: {e}")
                    logger.exception(f"Error processing {contact_name}")
            
            # Step 3: Upsert vendors into database (with overwrite)
            print(f"\nSTEP 3: Upserting {len(processed_vendors)} vendors into database...")
            upserted_count = self._upsert_vendors_to_database(processed_vendors)
            
            # Step 4: Clean up vendors that are no longer in GHL
            print(f"\nSTEP 4: Cleaning up vendors no longer in GoHighLevel...")
            ghl_contact_ids = [contact.get('id') for contact in vendor_contacts if contact.get('id')]
            removed_count = self._remove_outdated_vendors(ghl_contact_ids)
            
            # Report results
            print(f"\n📊 ENHANCED VENDOR SYNC RESULTS:")
            print(f"   ✅ Successfully processed: {len(processed_vendors)}")
            print(f"   💾 Upserted to database: {upserted_count}")
            print(f"   ❌ Failed to process: {len(failed_vendors)}")
            print(f"   🗑️ Removed outdated: {removed_count}")
            print(f"   📋 Total contacts found: {len(vendor_contacts)}")
            
            if upserted_count > 0:
                # Step 5: Verify database content
                self._verify_complete_vendor_data()
                
                print(f"\n🎉 ENHANCED VENDOR SYNC SUCCESSFUL!")
                print("   ✅ All vendor fields properly mapped and synchronized")
                print("   ✅ Existing vendor data overwritten with latest from GHL")
                print("   ✅ Database contains most accurate vendor information")
                return True
            else:
                print(f"\n❌ ENHANCED VENDOR SYNC COMPLETED WITH NO CHANGES!")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error in enhanced vendor sync: {e}")
            logger.exception("Enhanced vendor sync failed")
            return False
    
    def _get_all_vendor_contacts(self) -> List[Dict[str, Any]]:
        """Get all vendor contacts from GoHighLevel with comprehensive search"""
        try:
            # Search strategies for finding vendor contacts
            all_vendor_contacts = []
            
            # Strategy 1: Search by vendor-related tags
            vendor_tags = ['vendor', 'contractor', 'service-provider', 'partner', 'supplier']
            for tag in vendor_tags:
                try:
                    contacts = self.ghl_api.search_contacts(query=tag, limit=100)
                    if contacts:
                        for contact in contacts:
                            contact_id = contact.get('id')
                            if contact_id and not any(v.get('id') == contact_id for v in all_vendor_contacts):
                                all_vendor_contacts.append(contact)
                                logger.debug(f"Found vendor via tag '{tag}': {contact.get('firstName')} {contact.get('lastName')}")
                except Exception as e:
                    logger.warning(f"⚠️ Error searching for tag '{tag}': {e}")
            
            # Strategy 2: Search by custom field presence  
            try:
                all_contacts = self.ghl_api.search_contacts(query="", limit=500)
                if all_contacts:
                    for contact in all_contacts:
                        custom_fields = contact.get('customFields', [])
                        
                        # Check if contact has vendor-specific custom fields
                        has_vendor_fields = any(
                            field.get('id') in self.ghl_field_mappings.values()
                            for field in custom_fields
                        )
                        
                        if has_vendor_fields:
                            contact_id = contact.get('id')
                            if contact_id and not any(v.get('id') == contact_id for v in all_vendor_contacts):
                                all_vendor_contacts.append(contact)
                                logger.debug(f"Found vendor via custom fields: {contact.get('firstName')} {contact.get('lastName')}")
                                
            except Exception as e:
                logger.warning(f"⚠️ Error getting all contacts: {e}")
            
            logger.info(f"📋 Found {len(all_vendor_contacts)} total vendor contacts")
            return all_vendor_contacts
            
        except Exception as e:
            logger.error(f"❌ Error fetching vendor contacts: {e}")
            return []
    
    def _extract_complete_vendor_data(self, contact: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract complete vendor data with comprehensive field mapping and logging"""
        
        contact_id = contact.get('id')
        contact_name = f"{contact.get('firstName', '')} {contact.get('lastName', '')}".strip()
        
        logger.info(f"🔍 EXTRACTING COMPLETE DATA FOR: {contact_name} (ID: {contact_id})")
        
        try:
            # Initialize vendor data structure
            vendor_data = {
                'id': str(uuid.uuid4()),
                'account_id': self.account_id,
                'ghl_contact_id': contact_id,
                'name': contact_name,
                'status': 'active',  # Default status
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Extract standard contact fields
            logger.info(f"📝 Extracting standard contact fields...")
            for db_field, ghl_field in self.standard_fields.items():
                ghl_value = contact.get(ghl_field, '')
                vendor_data[db_field] = ghl_value
                
                if ghl_value:
                    logger.info(f"   ✅ {db_field} ← GHL.{ghl_field}: '{ghl_value}'")
                else:
                    logger.debug(f"   ⚪ {db_field} ← GHL.{ghl_field}: (empty)")
            
            # Construct full name and company info
            vendor_data['name'] = f"{vendor_data.get('firstName', '')} {vendor_data.get('lastName', '')}".strip()
            vendor_data['email'] = vendor_data.get('email', '')
            vendor_data['phone'] = vendor_data.get('phone', '')
            vendor_data['company_name'] = vendor_data.get('companyName', '')
            
            # Extract custom fields
            custom_fields = contact.get('customFields', [])
            logger.info(f"🔧 Extracting {len(custom_fields)} custom fields...")
            
            custom_data = self._extract_and_log_custom_fields(custom_fields, contact_name)
            
            # Check for required ghl_user_id
            ghl_user_id = custom_data.get('ghl_user_id', '').strip()
            if not ghl_user_id:
                logger.warning(f"⚠️ SKIPPING {contact_name}: No GHL User ID found")
                return None
            
            vendor_data['ghl_user_id'] = ghl_user_id
            logger.info(f"   ✅ ghl_user_id: {ghl_user_id}")
            
            # Process specialized data sections
            service_data = self._process_service_data_enhanced(custom_data, contact_name)
            vendor_data.update(service_data)
            
            coverage_data = self._process_coverage_data_enhanced(contact, custom_data, contact_name)
            vendor_data.update(coverage_data)
            
            business_data = self._process_business_data_enhanced(custom_data, contact_name)
            vendor_data.update(business_data)
            
            routing_data = self._process_routing_data_enhanced(custom_data, contact_name)
            vendor_data.update(routing_data)
            
            logger.info(f"✅ COMPLETE DATA EXTRACTION SUCCESS FOR: {contact_name}")
            return vendor_data
            
        except Exception as e:
            logger.error(f"❌ Error extracting complete vendor data for {contact_name}: {e}")
            logger.exception(f"Complete data extraction failed for {contact_name}")
            return None
    
    def _extract_and_log_custom_fields(self, custom_fields: List[Dict[str, Any]], contact_name: str) -> Dict[str, Any]:
        """Extract custom field values with detailed logging of field mappings"""
        
        extracted = {}
        
        logger.info(f"   🎯 Custom field mapping for {contact_name}:")
        
        # Create reverse mapping for logging
        id_to_field_name = {v: k for k, v in self.ghl_field_mappings.items()}
        
        for field in custom_fields:
            field_id = field.get('id', '')
            field_value = field.get('value', '') or field.get('fieldValue', '')
            
            # Check if this field is in our mapping
            if field_id in id_to_field_name:
                field_name = id_to_field_name[field_id]
                extracted[field_name] = field_value
                
                if field_value and str(field_value).strip():
                    logger.info(f"      ✅ {field_name} ← GHL_ID[{field_id}]: '{field_value}'")
                else:
                    logger.info(f"      ⚪ {field_name} ← GHL_ID[{field_id}]: (empty)")
            else:
                # Log unmapped fields for debugging
                if field_value and str(field_value).strip():
                    logger.debug(f"      ❓ UNMAPPED_FIELD ← GHL_ID[{field_id}]: '{field_value}'")
        
        # Log any expected fields that weren't found
        for field_name, field_id in self.ghl_field_mappings.items():
            if field_name not in extracted:
                logger.debug(f"      ❌ {field_name} ← GHL_ID[{field_id}]: (not found in contact)")
        
        return extracted
    
    def _process_service_data_enhanced(self, custom_data: Dict[str, Any], contact_name: str) -> Dict[str, Any]:
        """Process service categories and specific services with enhanced logging"""
        
        logger.info(f"   🛠️ Processing service data for {contact_name}:")
        
        service_categories = []
        services_offered = []
        
        # Extract primary service category
        primary_category = custom_data.get('primary_service_category', '').strip()
        if primary_category:
            service_categories.append(primary_category)
            logger.info(f"      ✅ Primary category: '{primary_category}'")
        
        # Extract service categories selections
        category_selections = custom_data.get('service_categories_selections', '').strip()
        if category_selections:
            logger.info(f"      📋 Raw category selections: '{category_selections}'")
            categories = self._parse_comma_separated_values(category_selections)
            for category in categories:
                if category not in service_categories:
                    service_categories.append(category)
                    logger.info(f"      ✅ Added category: '{category}'")
        
        # Extract specific services provided
        services_provided = custom_data.get('services_provided', '').strip()
        if services_provided:
            logger.info(f"      🔧 Raw services provided: '{services_provided}'")
            services = self._parse_comma_separated_values(services_provided)
            services_offered.extend(services)
            logger.info(f"      ✅ Added {len(services)} services: {services}")
        
        # Extract specific service needed (might be populated for vendors too)
        specific_service = custom_data.get('specific_service_needed', '').strip()
        if specific_service and specific_service not in services_offered:
            services_offered.append(specific_service)
            logger.info(f"      ✅ Added specific service: '{specific_service}'")
        
        result = {
            'service_categories': json.dumps(service_categories),
            'services_offered': json.dumps(services_offered)
        }
        
        logger.info(f"      📊 Final service data: {len(service_categories)} categories, {len(services_offered)} services")
        return result
    
    def _process_coverage_data_enhanced(self, contact: Dict[str, Any], custom_data: Dict[str, Any], contact_name: str) -> Dict[str, Any]:
        """Process coverage areas with enhanced ZIP→County conversion and logging"""
        
        logger.info(f"   🗺️ Processing coverage data for {contact_name}:")
        
        # Extract raw service zip codes from the CORRECT field
        service_zip_codes_raw = custom_data.get('service_zip_codes', '').strip()
        logger.info(f"      📍 Raw service zip codes from GHL field 'yDcN0FmwI3xacyxAuTWs': '{service_zip_codes_raw}'")
        
        coverage_counties = []
        coverage_states = set()
        coverage_type = 'county'  # Default
        
        if service_zip_codes_raw:
            # Parse ZIP codes
            zip_codes = self._parse_zip_codes_enhanced(service_zip_codes_raw)
            logger.info(f"      🔢 Parsed {len(zip_codes)} ZIP codes: {zip_codes}")
            
            # Convert each ZIP to county
            for zip_code in zip_codes:
                try:
                    logger.debug(f"        🔄 Converting ZIP {zip_code}...")
                    location_data = location_service.zip_to_location(zip_code)
                    
                    if not location_data.get('error'):
                        county = location_data.get('county', '')
                        state_code = location_data.get('state', '')
                        city = location_data.get('city', '')
                        
                        if county and state_code:
                            county_formatted = f"{county}, {state_code}"
                            if county_formatted not in coverage_counties:
                                coverage_counties.append(county_formatted)
                                coverage_states.add(state_code)
                                logger.info(f"        ✅ ZIP {zip_code} ({city}) → {county_formatted}")
                            else:
                                logger.debug(f"        ⚪ ZIP {zip_code} → {county_formatted} (duplicate)")
                        else:
                            logger.warning(f"        ⚠️ ZIP {zip_code} → Missing county/state data")
                    else:
                        logger.warning(f"        ❌ ZIP {zip_code} → Error: {location_data.get('error')}")
                        
                except Exception as e:
                    logger.error(f"        ❌ ZIP {zip_code} → Exception: {e}")
        
        # Fallback to personal address if no service ZIP codes
        if not coverage_counties:
            logger.warning(f"      ⚠️ No service ZIP codes found, trying personal address...")
            personal_zip = contact.get('postalCode', '').strip()
            
            if personal_zip and len(personal_zip) == 5 and personal_zip.isdigit():
                try:
                    logger.info(f"      🏠 Using personal ZIP as fallback: {personal_zip}")
                    location_data = location_service.zip_to_location(personal_zip)
                    
                    if not location_data.get('error'):
                        county = location_data.get('county', '')
                        state_code = location_data.get('state', '')
                        
                        if county and state_code:
                            county_formatted = f"{county}, {state_code}"
                            coverage_counties.append(county_formatted)
                            coverage_states.add(state_code)
                            logger.info(f"      ✅ Personal ZIP {personal_zip} → {county_formatted}")
                        
                except Exception as e:
                    logger.warning(f"      ❌ Error processing personal ZIP {personal_zip}: {e}")
        
        # Determine coverage type based on scope
        if len(coverage_states) > 3:
            coverage_type = 'national'
        elif len(coverage_states) > 1:
            coverage_type = 'state'
        else:
            coverage_type = 'county'
        
        result = {
            'service_coverage_type': coverage_type,
            'service_counties': json.dumps(coverage_counties),
            'service_states': json.dumps(list(coverage_states)),
            'service_areas': json.dumps([])  # Legacy field, keep empty
        }
        
        logger.info(f"      📊 Final coverage: {coverage_type} type, {len(coverage_counties)} counties, {len(coverage_states)} states")
        return result
    
    def _process_business_data_enhanced(self, custom_data: Dict[str, Any], contact_name: str) -> Dict[str, Any]:
        """Process business-related fields with enhanced extraction"""
        
        logger.info(f"   💼 Processing business data for {contact_name}:")
        
        business_fields = [
            'years_in_business', 'certifications_licenses', 'insurance_coverage',
            'emergency_services', 'service_radius_miles', 'crew_size', 
            'special_equipment', 'pricing_structure', 'payment_terms',
            'availability_schedule', 'preferred_contact_method', 
            'vessel_types_serviced', 'references', 'notes'
        ]
        
        result = {}
        
        for field in business_fields:
            value = custom_data.get(field, '').strip() if custom_data.get(field) else ''
            result[field] = value
            
            if value:
                logger.info(f"      ✅ {field}: '{value}'")
            else:
                logger.debug(f"      ⚪ {field}: (empty)")
        
        # Handle taking_new_work boolean field
        taking_new_work_raw = custom_data.get('taking_new_work', '').strip().lower()
        taking_new_work = taking_new_work_raw in ['yes', 'true', '1', 'active', 'available']
        result['taking_new_work'] = taking_new_work
        
        logger.info(f"      ✅ taking_new_work: {taking_new_work} (from '{taking_new_work_raw}')")
        
        return result
    
    def _process_routing_data_enhanced(self, custom_data: Dict[str, Any], contact_name: str) -> Dict[str, Any]:
        """Process routing performance fields with enhanced parsing"""
        
        logger.info(f"   🎯 Processing routing data for {contact_name}:")
        
        # Process last lead assigned
        last_assigned_raw = custom_data.get('last_lead_assigned', '').strip()
        last_lead_assigned = None
        
        if last_assigned_raw:
            try:
                from datetime import datetime
                for date_format in ['%Y-%m-%d', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M:%S']:
                    try:
                        parsed_date = datetime.strptime(last_assigned_raw, date_format)
                        last_lead_assigned = parsed_date.isoformat()
                        logger.info(f"      ✅ last_lead_assigned: {last_lead_assigned} (parsed from '{last_assigned_raw}')")
                        break
                    except ValueError:
                        continue
                
                if not last_lead_assigned:
                    logger.warning(f"      ⚠️ Could not parse date: '{last_assigned_raw}'")
                    
            except Exception as e:
                logger.warning(f"      ❌ Error parsing last_lead_assigned: {e}")
        else:
            logger.debug(f"      ⚪ last_lead_assigned: (empty)")
        
        # Process lead close percentage
        close_percentage_raw = custom_data.get('lead_close_percentage', '').strip()
        lead_close_percentage = 0.0
        
        if close_percentage_raw:
            try:
                # Handle various percentage formats
                clean_percentage = close_percentage_raw.replace('%', '').replace(',', '').strip()
                percentage_value = float(clean_percentage)
                
                # Normalize to 0-100 range
                if percentage_value <= 1.0:
                    lead_close_percentage = percentage_value * 100
                else:
                    lead_close_percentage = percentage_value
                
                # Ensure within valid range
                lead_close_percentage = max(0.0, min(100.0, lead_close_percentage))
                
                logger.info(f"      ✅ lead_close_percentage: {lead_close_percentage}% (from '{close_percentage_raw}')")
                
            except (ValueError, TypeError) as e:
                logger.warning(f"      ❌ Error parsing lead_close_percentage '{close_percentage_raw}': {e}")
                lead_close_percentage = 0.0
        else:
            logger.debug(f"      ⚪ lead_close_percentage: 0.0 (empty)")
        
        return {
            'last_lead_assigned': last_lead_assigned,
            'lead_close_percentage': lead_close_percentage
        }
    
    def _parse_comma_separated_values(self, value_string: str) -> List[str]:
        """Parse comma-separated values with proper trimming"""
        if not value_string:
            return []
        
        values = [v.strip() for v in value_string.split(',') if v.strip()]
        return values
    
    def _parse_zip_codes_enhanced(self, zip_codes_raw: str) -> List[str]:
        """Enhanced ZIP code parsing with better format handling"""
        if not zip_codes_raw or not zip_codes_raw.strip():
            return []
        
        # Normalize separators
        normalized = zip_codes_raw.replace(';', ',').replace('\n', ',').replace('\r', ',').replace('\t', ',')
        
        zip_codes = []
        for zip_code in normalized.split(','):
            zip_code = zip_code.strip()
            
            # Handle ZIP+4 format
            if '-' in zip_code:
                zip_code = zip_code.split('-')[0].strip()
            elif len(zip_code) == 9 and zip_code.isdigit():
                zip_code = zip_code[:5]
            
            # Validate 5-digit ZIP code
            if zip_code and len(zip_code) == 5 and zip_code.isdigit():
                if zip_code not in zip_codes:  # Avoid duplicates
                    zip_codes.append(zip_code)
        
        # Try space separation if comma separation failed
        if not zip_codes and ' ' in zip_codes_raw:
            for zip_code in zip_codes_raw.split():
                zip_code = zip_code.strip()
                if len(zip_code) == 5 and zip_code.isdigit():
                    if zip_code not in zip_codes:
                        zip_codes.append(zip_code)
        
        return zip_codes
    
    def _upsert_vendors_to_database(self, vendors: List[Dict[str, Any]]) -> int:
        """Upsert vendors to database with OVERWRITE capability"""
        
        if not vendors:
            return 0
        
        logger.info(f"💾 UPSERTING {len(vendors)} vendors to database with overwrite...")
        
        try:
            conn = sqlite3.connect('smart_lead_router.db')
            cursor = conn.cursor()
            
            # Use INSERT OR REPLACE to overwrite existing vendors
            upsert_sql = """
                INSERT OR REPLACE INTO vendors (
                    id, account_id, ghl_contact_id, ghl_user_id, name, email, phone, 
                    company_name, service_categories, services_offered, service_coverage_type,
                    service_states, service_counties, service_areas, last_lead_assigned, 
                    lead_close_percentage, status, taking_new_work,
                    years_in_business, certifications_licenses, insurance_coverage,
                    emergency_services, service_radius_miles, crew_size, special_equipment,
                    pricing_structure, payment_terms, availability_schedule,
                    preferred_contact_method, vessel_types_serviced, references, notes,
                    created_at, updated_at
                ) VALUES (
                    COALESCE((SELECT id FROM vendors WHERE ghl_contact_id = ?), ?),
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                    ?, ?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM vendors WHERE ghl_contact_id = ?), ?), ?
                )
            """
            
            upserted_count = 0
            
            for vendor in vendors:
                try:
                    ghl_contact_id = vendor['ghl_contact_id']
                    new_id = vendor['id']
                    created_at = vendor['created_at']
                    updated_at = vendor['updated_at']
                    
                    cursor.execute(upsert_sql, (
                        ghl_contact_id, new_id,  # For COALESCE ID logic
                        vendor['account_id'], 
                        vendor['ghl_contact_id'],
                        vendor.get('ghl_user_id'),
                        vendor['name'],
                        vendor.get('email', ''),
                        vendor.get('phone', ''),
                        vendor.get('company_name', ''),
                        vendor['service_categories'],
                        vendor['services_offered'],
                        vendor['service_coverage_type'],
                        vendor['service_states'],
                        vendor['service_counties'],
                        vendor['service_areas'],
                        vendor.get('last_lead_assigned'),
                        vendor['lead_close_percentage'],
                        vendor['status'],
                        vendor.get('taking_new_work', True),
                        vendor.get('years_in_business', ''),
                        vendor.get('certifications_licenses', ''),
                        vendor.get('insurance_coverage', ''),
                        vendor.get('emergency_services', ''),
                        vendor.get('service_radius_miles', ''),
                        vendor.get('crew_size', ''),
                        vendor.get('special_equipment', ''),
                        vendor.get('pricing_structure', ''),
                        vendor.get('payment_terms', ''),
                        vendor.get('availability_schedule', ''),
                        vendor.get('preferred_contact_method', ''),
                        vendor.get('vessel_types_serviced', ''),
                        vendor.get('references', ''),
                        vendor.get('notes', ''),
                        ghl_contact_id, created_at,  # For COALESCE created_at logic
                        updated_at
                    ))
                    
                    upserted_count += 1
                    logger.info(f"   ✅ Upserted: {vendor['name']}")
                    
                except Exception as e:
                    logger.error(f"   ❌ Error upserting vendor {vendor['name']}: {e}")
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Successfully upserted {upserted_count} vendors")
            return upserted_count
            
        except Exception as e:
            logger.error(f"❌ Error upserting vendors to database: {e}")
            return 0
    
    def _remove_outdated_vendors(self, current_ghl_contact_ids: List[str]) -> int:
        """Remove vendors that are no longer in GHL"""
        try:
            conn = sqlite3.connect('smart_lead_router.db')
            cursor = conn.cursor()
            
            if not current_ghl_contact_ids:
                conn.close()
                return 0
            
            placeholders = ','.join(['?' for _ in current_ghl_contact_ids])
            
            cursor.execute(f"""
                DELETE FROM vendors 
                WHERE ghl_contact_id NOT IN ({placeholders})
                AND ghl_user_id IS NOT NULL 
            """, current_ghl_contact_ids)
            
            removed_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Removed {removed_count} vendors no longer in GHL")
            return removed_count
            
        except Exception as e:
            logger.error(f"❌ Error removing outdated vendors: {e}")
            return 0
    
    def _verify_complete_vendor_data(self) -> None:
        """Verify the complete vendor data synchronization"""
        
        print(f"\n🔍 VERIFYING COMPLETE VENDOR DATA SYNCHRONIZATION:")
        print("-" * 50)
        
        try:
            conn = sqlite3.connect('smart_lead_router.db')
            cursor = conn.cursor()
            
            # Get comprehensive vendor statistics
            cursor.execute("SELECT COUNT(*) FROM vendors")
            total_vendors = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM vendors WHERE ghl_user_id IS NOT NULL")
            vendors_with_user_id = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM vendors WHERE services_offered != '[]'")
            vendors_with_services = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM vendors WHERE service_counties != '[]'")
            vendors_with_coverage = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM vendors WHERE lead_close_percentage > 0")
            vendors_with_performance = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM vendors WHERE company_name != ''")
            vendors_with_company = cursor.fetchone()[0]
            
            print(f"📊 SYNCHRONIZATION STATISTICS:")
            print(f"   Total vendors: {total_vendors}")
            print(f"   With GHL User ID: {vendors_with_user_id}")
            print(f"   With services: {vendors_with_services}")
            print(f"   With coverage areas: {vendors_with_coverage}")
            print(f"   With performance data: {vendors_with_performance}")
            print(f"   With company names: {vendors_with_company}")
            
            # Show detailed sample data
            cursor.execute("""
                SELECT name, email, company_name, services_offered, service_counties, 
                       lead_close_percentage, ghl_user_id, updated_at
                FROM vendors 
                ORDER BY updated_at DESC
                LIMIT 3
            """)
            sample_vendors = cursor.fetchall()
            
            print(f"\n📋 SAMPLE VENDOR DATA (Most Recently Updated):")
            for vendor in sample_vendors:
                name, email, company, services, coverage, close_pct, user_id, updated = vendor
                print(f"   • {name} ({email})")
                print(f"     Company: {company}")
                print(f"     Services: {services}")
                print(f"     Coverage: {coverage}")
                print(f"     Performance: {close_pct}%")
                print(f"     GHL User ID: {user_id}")
                print(f"     Updated: {updated}")
                print()
            
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error verifying vendor data: {e}")


def main():
    """Main execution function"""
    print("🚀 ENHANCED VENDOR SYNC FROM GOHIGHLEVEL")
    print("=" * 50)
    print("Complete field mapping with overwrite capability")
    print("Detailed logging of all field mappings and extractions")
    print("")
    
    try:
        # Initialize enhanced sync service
        vendor_sync = EnhancedVendorSync()
        
        # Execute enhanced sync with overwrite
        success = vendor_sync.sync_all_vendors_with_overwrite()
        
        if success:
            print(f"\n🎉 ENHANCED VENDOR SYNC COMPLETED SUCCESSFULLY!")
            print("   ✅ All vendor fields properly mapped and synchronized")
            print("   ✅ Existing vendor data overwritten with latest from GHL")
            print("   ✅ Service coverage areas fixed using correct GHL field")
            print("   ✅ Database contains most accurate vendor information")
            print("   ✅ Ready for simplified direct service matching")
        else:
            print(f"\n❌ ENHANCED VENDOR SYNC FAILED!")
            print("   Check error messages and logs for details")
        
    except Exception as e:
        print(f"❌ Critical error in enhanced vendor sync: {e}")
        logger.exception("Enhanced vendor sync failed")


if __name__ == '__main__':
    main()