#!/usr/bin/env python3
"""
VENDOR SYNC SCRIPT FROM GOHIGHLEVEL
Populates the new vendor table structure with proper multi-level routing data.

EXTRACTS FROM GHL:
- Service categories and specific services offered
- Coverage areas (with ZIP→County conversion)
- Routing fields (last_lead_assigned, lead_close_percentage)
- All contact information and GHL IDs

POPULATES NEW SCHEMA:
- service_categories (JSON array)
- services_offered (JSON array) 
- coverage_counties (JSON array with "County, State" format)
- last_lead_assigned, lead_close_percentage for routing algorithms
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

# Load environment variables - Fixed for venv execution
from dotenv import load_dotenv
import os

# Load .env from project root, not script directory
# When running from venv, we need to find the project root
current_dir = os.getcwd()
if current_dir.endswith('Lead-Router-Pro'):
    # We're in project root
    dotenv_path = os.path.join(current_dir, '.env')
else:
    # We're in a different directory, look for Lead-Router-Pro
    dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')

load_dotenv(dotenv_path)

from config import AppConfig
from api.services.ghl_api import GoHighLevelAPI
from api.services.location_service import location_service
from api.services.service_categories import service_manager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VendorSyncFromGHL:
    """Sync vendors from GoHighLevel to new database structure"""
    
    def __init__(self):
        """Initialize GHL API and account information"""
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
            
            # GHL field mappings from user specifications
            self.field_mappings = {
                'specific_service_needed': 'FT85QGi0tBq1AfVGNJ9v',
                'last_lead_assigned': 'NbsJTMv3EkxqNfwx8Jh4', 
                'lead_close_percentage': 'OwHQipU7xdrHCpVswtnW',
                'services_provided': 'pAq9WBsIuFUAZuwz3YY4',
                'primary_service_category': 'HRqfv0HnUydNRLKWhk27',
                'service_categories_selections': '72qwwzy4AUfTCBJvBIEf',
                'ghl_user_id': 'HXVNT4y8OynNokWAfO2D',
                'service_zip_codes': 'yDcN0FmwI3xacyxAuTWs'
            }
            
            logger.info("✅ VendorSyncFromGHL initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize VendorSyncFromGHL: {e}")
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
    
    def sync_all_vendors(self) -> bool:
        """Main function to sync all vendors from GHL"""
        
        print("🔄 SYNCING VENDORS FROM GOHIGHLEVEL")
        print("=" * 45)
        print("Extracting vendor data with proper multi-level routing structure")
        print("Only syncing contacts with active GHL User IDs")
        print("")
        
        try:
            # Step 1: Clean up invalid vendors (without ghl_user_id)
            print("STEP 1: Cleaning up invalid vendors from database...")
            cleanup_results = self._cleanup_invalid_vendors()
            
            if cleanup_results['removed_count'] > 0:
                print(f"✅ Cleaned up {cleanup_results['removed_count']} invalid vendors")
                print(f"   - Vendors without GHL User ID: {cleanup_results['no_user_id_count']}")
            else:
                print("✅ No invalid vendors to clean up")
            
            # Step 2: Get vendor contacts from GHL
            print(f"\nSTEP 2: Fetching vendor contacts from GoHighLevel...")
            vendor_contacts = self._get_vendor_contacts_from_ghl()
            
            if not vendor_contacts:
                print("❌ No vendor contacts found in GoHighLevel")
                return False
            
            print(f"✅ Found {len(vendor_contacts)} potential vendor contacts in GHL")
            
            # Step 3: Filter and process each vendor
            print(f"\nSTEP 3: Processing vendor data (filtering for GHL User IDs)...")
            processed_vendors = []
            failed_vendors = []
            skipped_no_user_id = []
            
            for contact in vendor_contacts:
                try:
                    vendor_data = self._process_vendor_contact(contact)
                    if vendor_data:
                        processed_vendors.append(vendor_data)
                        print(f"   ✅ {contact.get('firstName', '')} {contact.get('lastName', '')} (User ID: {vendor_data.get('ghl_user_id', 'N/A')})")
                    else:
                        # Check if it was skipped due to missing ghl_user_id
                        custom_fields = contact.get('customFields', [])
                        custom_data = self._extract_custom_fields(custom_fields)
                        if not custom_data.get('ghl_user_id'):
                            skipped_no_user_id.append(contact)
                            print(f"   ⚠️ Skipped: {contact.get('firstName', '')} {contact.get('lastName', '')} (No GHL User ID)")
                        else:
                            failed_vendors.append(contact)
                            print(f"   ❌ Failed: {contact.get('firstName', '')} {contact.get('lastName', '')}")
                except Exception as e:
                    failed_vendors.append(contact)
                    print(f"   ❌ Error processing {contact.get('firstName', '')}: {e}")
            
            # Step 4: Insert vendors into database
            print(f"\nSTEP 4: Inserting {len(processed_vendors)} valid vendors into database...")
            inserted_count = self._insert_vendors_to_database(processed_vendors)
            
            # Step 5: Clean up vendors that are no longer in GHL
            print(f"\nSTEP 5: Cleaning up vendors no longer in GoHighLevel...")
            ghl_contact_ids = [contact.get('id') for contact in vendor_contacts if contact.get('id')]
            removed_outdated = self._remove_outdated_vendors(ghl_contact_ids)
            
            if removed_outdated > 0:
                print(f"✅ Removed {removed_outdated} vendors no longer in GHL")
            else:
                print("✅ No outdated vendors to remove")
            
            # Report results
            print(f"\n📊 VENDOR SYNC RESULTS:")
            print(f"   ✅ Successfully synced: {inserted_count}")
            print(f"   ⚠️ Skipped (no User ID): {len(skipped_no_user_id)}")
            print(f"   ❌ Failed to process: {len(failed_vendors)}")
            print(f"   🗑️ Cleaned up invalid: {cleanup_results['removed_count']}")
            print(f"   🗑️ Removed outdated: {removed_outdated}")
            print(f"   📋 Total contacts found: {len(vendor_contacts)}")
            
            if inserted_count > 0 or cleanup_results['removed_count'] > 0 or removed_outdated > 0:
                # Step 6: Verify database content
                self._verify_vendor_data()
                
                print(f"\n🎉 VENDOR SYNC SUCCESSFUL!")
                print("   ✅ Only vendors with GHL User IDs are synced")
                print("   ✅ Invalid vendors cleaned up from database")
                print("   ✅ Vendors populated with multi-level routing data")
                print("   ✅ Service categories and specific services extracted")
                print("   ✅ Coverage areas properly formatted")
                print("   ✅ Routing fields (performance + round-robin) populated")
                return True
            else:
                print(f"\n❌ VENDOR SYNC COMPLETED WITH NO CHANGES!")
                print("   No vendors were inserted, cleaned up, or removed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error in vendor sync: {e}")
            return False
    
    def _get_vendor_contacts_from_ghl(self) -> List[Dict[str, Any]]:
        """Get all vendor contacts from GoHighLevel"""
        try:
            # Search for contacts with vendor-related tags
            vendor_tags = ['vendor', 'contractor', 'service-provider', 'partner']
            all_vendor_contacts = []
            
            for tag in vendor_tags:
                try:
                    contacts = self.ghl_api.search_contacts(query=tag, limit=100)
                    if contacts:
                        # Filter to avoid duplicates
                        for contact in contacts:
                            contact_id = contact.get('id')
                            if contact_id and not any(v.get('id') == contact_id for v in all_vendor_contacts):
                                all_vendor_contacts.append(contact)
                except Exception as e:
                    logger.warning(f"⚠️ Error searching for tag '{tag}': {e}")
                    continue
            
            # Also try getting all contacts and filtering by custom fields
            try:
                all_contacts = self.ghl_api.search_contacts(query="", limit=200)
                if all_contacts:
                    for contact in all_contacts:
                        # Check if contact has vendor-related custom fields
                        custom_fields = contact.get('customFields', [])
                        is_vendor = False
                        
                        for field in custom_fields:
                            field_id = field.get('id', '')
                            # Check for known vendor fields
                            if field_id in self.field_mappings.values():
                                is_vendor = True
                                break
                        
                        # Add to vendor list if not already present
                        if is_vendor:
                            contact_id = contact.get('id')
                            if contact_id and not any(v.get('id') == contact_id for v in all_vendor_contacts):
                                all_vendor_contacts.append(contact)
                                
            except Exception as e:
                logger.warning(f"⚠️ Error getting all contacts: {e}")
            
            logger.info(f"📋 Found {len(all_vendor_contacts)} potential vendor contacts")
            return all_vendor_contacts
            
        except Exception as e:
            logger.error(f"❌ Error fetching vendor contacts: {e}")
            return []
    
    def _cleanup_invalid_vendors(self) -> Dict[str, int]:
        """Remove vendors from database that don't have a ghl_user_id"""
        try:
            conn = sqlite3.connect('smart_lead_router.db')
            cursor = conn.cursor()
            
            # Count vendors without ghl_user_id
            cursor.execute("""
                SELECT COUNT(*) FROM vendors 
                WHERE ghl_user_id IS NULL OR ghl_user_id = ''
            """)
            no_user_id_count = cursor.fetchone()[0]
            
            # Remove vendors without ghl_user_id
            cursor.execute("""
                DELETE FROM vendors 
                WHERE ghl_user_id IS NULL OR ghl_user_id = ''
            """)
            
            removed_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Cleaned up {removed_count} vendors without GHL User ID")
            
            return {
                'removed_count': removed_count,
                'no_user_id_count': no_user_id_count
            }
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up invalid vendors: {e}")
            return {
                'removed_count': 0,
                'no_user_id_count': 0
            }
    
    def _remove_outdated_vendors(self, current_ghl_contact_ids: List[str]) -> int:
        """Remove vendors that are no longer in the GHL contact list"""
        try:
            conn = sqlite3.connect('smart_lead_router.db')
            cursor = conn.cursor()
            
            if not current_ghl_contact_ids:
                # If no contacts found, don't remove anything to be safe
                conn.close()
                return 0
            
            # Create placeholders for the SQL IN clause
            placeholders = ','.join(['?' for _ in current_ghl_contact_ids])
            
            # Remove vendors whose ghl_contact_id is not in the current GHL list
            # Only remove vendors that have a ghl_user_id (to avoid removing manually added vendors)
            cursor.execute(f"""
                DELETE FROM vendors 
                WHERE ghl_contact_id NOT IN ({placeholders})
                AND ghl_user_id IS NOT NULL 
                AND ghl_user_id != ''
            """, current_ghl_contact_ids)
            
            removed_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Removed {removed_count} vendors no longer in GHL")
            
            return removed_count
            
        except Exception as e:
            logger.error(f"❌ Error removing outdated vendors: {e}")
            return 0
    
    def _process_vendor_contact(self, contact: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single vendor contact into database format"""
        try:
            # Extract custom field data first to check for ghl_user_id
            custom_fields = contact.get('customFields', [])
            custom_data = self._extract_custom_fields(custom_fields)
            
            # Skip vendors without ghl_user_id
            ghl_user_id = custom_data.get('ghl_user_id', '')
            if not ghl_user_id or ghl_user_id.strip() == '':
                logger.debug(f"⚠️ Skipping vendor {contact.get('firstName', '')} {contact.get('lastName', '')} - No GHL User ID")
                return None
            
            # Basic contact information
            vendor_data = {
                'id': str(uuid.uuid4()),
                'account_id': self.account_id,
                'ghl_contact_id': contact.get('id'),
                'name': f"{contact.get('firstName', '')} {contact.get('lastName', '')}".strip(),
                'email': contact.get('email', ''),
                'phone': contact.get('phone', ''),
                'company_name': contact.get('companyName', ''),
                'status': 'active',
                'taking_new_work': True
            }
            
            # Process service data
            service_data = self._process_service_data(custom_data)
            vendor_data.update(service_data)
            
            # Process coverage data 
            coverage_data = self._process_coverage_data(contact, custom_data)
            vendor_data.update(coverage_data)
            
            # Process routing data
            routing_data = self._process_routing_data(custom_data)
            vendor_data.update(routing_data)
            
            return vendor_data
            
        except Exception as e:
            logger.error(f"❌ Error processing vendor contact: {e}")
            return None
    
    def _extract_custom_fields(self, custom_fields: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract custom field values by field ID"""
        extracted = {}
        
        for field in custom_fields:
            field_id = field.get('id', '')
            field_value = field.get('value', '')
            
            # Map known field IDs to readable names
            for field_name, expected_id in self.field_mappings.items():
                if field_id == expected_id:
                    extracted[field_name] = field_value
                    break
        
        return extracted
    
    def _process_service_data(self, custom_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process service categories and specific services offered"""
        
        service_categories = []
        services_offered = []
        
        # Extract primary service category
        primary_category = custom_data.get('primary_service_category', '')
        if primary_category and service_manager.is_valid_category(primary_category):
            service_categories.append(primary_category)
        
        # Extract from service categories selections
        category_selections = custom_data.get('service_categories_selections', '')
        if category_selections:
            if ',' in category_selections:
                categories = [c.strip() for c in category_selections.split(',') if c.strip()]
            else:
                categories = [category_selections.strip()] if category_selections.strip() else []
            
            for category in categories:
                if service_manager.is_valid_category(category) and category not in service_categories:
                    service_categories.append(category)
        
        # Extract specific services provided
        services_provided = custom_data.get('services_provided', '')
        if services_provided:
            if ',' in services_provided:
                services = [s.strip() for s in services_provided.split(',') if s.strip()]
            else:
                services = [services_provided.strip()] if services_provided.strip() else []
            
            for service in services:
                if service and service not in services_offered:
                    services_offered.append(service)
        
        # Also check specific service needed field
        specific_service = custom_data.get('specific_service_needed', '')
        if specific_service and specific_service not in services_offered:
            services_offered.append(specific_service)
        
        return {
            'service_categories': json.dumps(service_categories),
            'services_offered': json.dumps(services_offered)
        }
    
    def _process_coverage_data(self, contact: Dict[str, Any], custom_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process coverage areas with ZIP→County conversion from Service Zip Codes field"""
        
        # Default to county-based coverage
        coverage_type = 'county'
        coverage_counties = []
        coverage_states = set()
        
        contact_name = f"{contact.get('firstName', '')} {contact.get('lastName', '')}".strip()
        
        # Extract service zip codes from custom field
        service_zip_codes_raw = custom_data.get('service_zip_codes', '')
        
        if service_zip_codes_raw:
            logger.info(f"📍 Processing service coverage for {contact_name}")
            logger.debug(f"   Raw service zip codes: {service_zip_codes_raw}")
            
            # Parse service zip codes (handle various formats)
            service_zip_codes = self._parse_zip_codes(service_zip_codes_raw)
            
            if service_zip_codes:
                logger.info(f"   Found {len(service_zip_codes)} service zip codes: {service_zip_codes}")
                
                # Convert each zip code to county
                for zip_code in service_zip_codes:
                    try:
                        location_data = location_service.zip_to_location(zip_code)
                        if not location_data.get('error'):
                            county = location_data.get('county', '')
                            state_code = location_data.get('state', '')
                            if county and state_code:
                                county_formatted = f"{county}, {state_code}"
                                if county_formatted not in coverage_counties:
                                    coverage_counties.append(county_formatted)
                                    coverage_states.add(state_code)
                                    logger.info(f"   ✅ ZIP {zip_code} → {county_formatted}")
                            else:
                                logger.warning(f"   ⚠️ ZIP {zip_code} - County/State not found in location data")
                        else:
                            logger.warning(f"   ⚠️ ZIP {zip_code} - Location service error: {location_data.get('error')}")
                    except Exception as e:
                        logger.warning(f"   ⚠️ Error processing ZIP {zip_code}: {e}")
            else:
                logger.warning(f"   ⚠️ No valid zip codes parsed from: {service_zip_codes_raw}")
        else:
            # Fallback: try vendor's personal address if no service zip codes
            logger.warning(f"⚠️ No 'Service Zip Codes' field found for {contact_name}")
            personal_zip = contact.get('postalCode', '').strip()
            if personal_zip and len(personal_zip) == 5 and personal_zip.isdigit():
                logger.info(f"   🏠 Trying personal ZIP as fallback: {personal_zip}")
                try:
                    location_data = location_service.zip_to_location(personal_zip)
                    if not location_data.get('error'):
                        county = location_data.get('county', '')
                        state_code = location_data.get('state', '')
                        if county and state_code:
                            county_formatted = f"{county}, {state_code}"
                            coverage_counties.append(county_formatted)
                            coverage_states.add(state_code)
                            logger.info(f"   ✅ Personal ZIP {personal_zip} → {county_formatted}")
                except Exception as e:
                    logger.warning(f"   ⚠️ Error processing personal ZIP {personal_zip}: {e}")
        
        # Final validation
        if not coverage_counties:
            logger.warning(f"❌ No coverage areas found for vendor {contact_name}")
            logger.warning(f"   This vendor will have empty coverage areas - manual configuration needed")
        else:
            logger.info(f"✅ {contact_name} coverage areas: {coverage_counties}")
        
        return {
            'coverage_type': coverage_type,
            'coverage_counties': json.dumps(coverage_counties),
            'coverage_states': json.dumps(list(coverage_states))
        }
    
    def _parse_zip_codes(self, zip_codes_raw: str) -> List[str]:
        """Parse zip codes from raw string input handling various formats"""
        if not zip_codes_raw or not zip_codes_raw.strip():
            return []
        
        # Common separators: comma, semicolon, newline, space
        # Replace common separators with commas for consistent parsing
        normalized = zip_codes_raw.replace(';', ',').replace('\n', ',').replace('\r', ',')
        
        # Split by comma and clean up
        zip_codes = []
        for zip_code in normalized.split(','):
            zip_code = zip_code.strip()
            # Validate zip code format (5 digits)
            if zip_code and len(zip_code) == 5 and zip_code.isdigit():
                zip_codes.append(zip_code)
            elif zip_code and len(zip_code) > 5:
                # Handle ZIP+4 format (12345-6789 or 123456789)
                if '-' in zip_code:
                    base_zip = zip_code.split('-')[0].strip()
                    if len(base_zip) == 5 and base_zip.isdigit():
                        zip_codes.append(base_zip)
                elif len(zip_code) == 9 and zip_code.isdigit():
                    zip_codes.append(zip_code[:5])
        
        # Also try space-separated if comma separation didn't work
        if not zip_codes and ' ' in zip_codes_raw:
            for zip_code in zip_codes_raw.split():
                zip_code = zip_code.strip()
                if len(zip_code) == 5 and zip_code.isdigit():
                    zip_codes.append(zip_code)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_zip_codes = []
        for zip_code in zip_codes:
            if zip_code not in seen:
                seen.add(zip_code)
                unique_zip_codes.append(zip_code)
        
        return unique_zip_codes
    
    def _process_routing_data(self, custom_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process routing fields for performance and round-robin algorithms"""
        
        # Extract last lead assigned date
        last_assigned = custom_data.get('last_lead_assigned', '')
        last_lead_assigned = None
        
        if last_assigned:
            try:
                # Try to parse various date formats
                from datetime import datetime
                for date_format in ['%Y-%m-%d', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S']:
                    try:
                        parsed_date = datetime.strptime(last_assigned, date_format)
                        last_lead_assigned = parsed_date.isoformat()
                        break
                    except ValueError:
                        continue
            except Exception:
                pass
        
        # Extract lead close percentage
        close_percentage = custom_data.get('lead_close_percentage', '')
        lead_close_percentage = 0.0
        
        if close_percentage:
            try:
                # Handle percentage formats (e.g., "85%", "0.85", "85")
                if isinstance(close_percentage, str):
                    clean_percentage = close_percentage.replace('%', '').strip()
                    percentage_value = float(clean_percentage)
                    # Normalize to 0-100 range
                    if percentage_value <= 1.0:
                        lead_close_percentage = percentage_value * 100
                    else:
                        lead_close_percentage = percentage_value
                else:
                    lead_close_percentage = float(close_percentage)
                    
                # Ensure within valid range
                lead_close_percentage = max(0.0, min(100.0, lead_close_percentage))
                
            except (ValueError, TypeError):
                lead_close_percentage = 0.0
        
        # Extract GHL User ID
        ghl_user_id = custom_data.get('ghl_user_id', '')
        
        return {
            'last_lead_assigned': last_lead_assigned,
            'lead_close_percentage': lead_close_percentage,
            'ghl_user_id': ghl_user_id if ghl_user_id else None
        }
    
    def _insert_vendors_to_database(self, vendors: List[Dict[str, Any]]) -> int:
        """Insert processed vendors into the new database structure"""
        
        if not vendors:
            return 0
        
        try:
            conn = sqlite3.connect('smart_lead_router.db')
            cursor = conn.cursor()
            
            # Insert vendors with new schema
            insert_sql = """
                INSERT INTO vendors (
                    id, account_id, ghl_contact_id, ghl_user_id, name, email, phone, 
                    company_name, service_categories, services_offered, coverage_type,
                    coverage_states, coverage_counties, last_lead_assigned, 
                    lead_close_percentage, status, taking_new_work, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
            
            inserted_count = 0
            
            for vendor in vendors:
                try:
                    cursor.execute(insert_sql, (
                        vendor['id'],
                        vendor['account_id'], 
                        vendor['ghl_contact_id'],
                        vendor.get('ghl_user_id'),
                        vendor['name'],
                        vendor['email'],
                        vendor['phone'],
                        vendor['company_name'],
                        vendor['service_categories'],
                        vendor['services_offered'],
                        vendor['coverage_type'],
                        vendor['coverage_states'],
                        vendor['coverage_counties'],
                        vendor.get('last_lead_assigned'),
                        vendor['lead_close_percentage'],
                        vendor['status'],
                        vendor['taking_new_work']
                    ))
                    inserted_count += 1
                    
                except sqlite3.IntegrityError as e:
                    logger.warning(f"⚠️ Vendor {vendor['name']} already exists or integrity error: {e}")
                except Exception as e:
                    logger.error(f"❌ Error inserting vendor {vendor['name']}: {e}")
            
            conn.commit()
            conn.close()
            
            return inserted_count
            
        except Exception as e:
            logger.error(f"❌ Error inserting vendors to database: {e}")
            return 0
    
    def _verify_vendor_data(self) -> None:
        """Verify the synced vendor data"""
        
        print(f"\n🔍 VERIFYING SYNCED VENDOR DATA:")
        print("-" * 40)
        
        try:
            conn = sqlite3.connect('smart_lead_router.db')
            cursor = conn.cursor()
            
            # Get vendor summary
            cursor.execute("SELECT COUNT(*) FROM vendors")
            total_vendors = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM vendors WHERE service_categories != '[]'")
            vendors_with_categories = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM vendors WHERE services_offered != '[]'")
            vendors_with_services = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM vendors WHERE coverage_counties != '[]'")
            vendors_with_coverage = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM vendors WHERE ghl_user_id IS NOT NULL")
            vendors_with_user_id = cursor.fetchone()[0]
            
            print(f"📊 Total vendors: {total_vendors}")
            print(f"🛠️ Vendors with service categories: {vendors_with_categories}")
            print(f"⚙️ Vendors with specific services: {vendors_with_services}")
            print(f"🗺️ Vendors with coverage areas: {vendors_with_coverage}")
            print(f"👤 Vendors with GHL User IDs: {vendors_with_user_id}")
            
            # Show sample vendor data
            cursor.execute("""
                SELECT name, service_categories, services_offered, coverage_counties, 
                       lead_close_percentage, ghl_user_id
                FROM vendors LIMIT 3
            """)
            sample_vendors = cursor.fetchall()
            
            print(f"\n📋 SAMPLE VENDOR DATA:")
            for vendor in sample_vendors:
                name, categories, services, coverage, close_pct, user_id = vendor
                print(f"   • {name}:")
                print(f"     Categories: {categories}")
                print(f"     Services: {services}")
                print(f"     Coverage: {coverage}")
                print(f"     Close %: {close_pct}%")
                print(f"     User ID: {user_id}")
                print()
            
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error verifying vendor data: {e}")


def main():
    """Main execution function"""
    print("🔄 VENDOR SYNC FROM GOHIGHLEVEL")
    print("=" * 40)
    print("Syncing vendors to new multi-level routing database structure")
    print("")
    
    try:
        # Initialize sync service
        vendor_sync = VendorSyncFromGHL()
        
        # Execute sync
        success = vendor_sync.sync_all_vendors()
        
        if success:
            print(f"\n🎉 VENDOR SYNC COMPLETED SUCCESSFULLY!")
            print("   ✅ Database populated with proper multi-level routing data")
            print("   ✅ Ready for service category + specific service matching")
            print("   ✅ Ready for county-based location matching")
            print("   ✅ Ready for performance + round-robin routing")
        else:
            print(f"\n❌ VENDOR SYNC FAILED!")
            print("   Check error messages above for details")
        
    except Exception as e:
        print(f"❌ Critical error in vendor sync: {e}")
        logger.exception("Vendor sync failed")


if __name__ == '__main__':
    main()
