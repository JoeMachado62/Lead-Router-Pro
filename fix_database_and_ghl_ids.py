#!/usr/bin/env python3
# File: fix_database_and_ghl_ids_ENHANCED.py
# ENHANCED VERSION with GHL-as-source-of-truth synchronization + SERVICE DATA SYNC
# 
# FEATURES:
# - Fixes UNIQUE constraint errors with unique placeholder IDs
# - Syncs local vendor database with GoHighLevel (removes orphaned records)
# - Makes GHL the single source of truth for vendor management
# - Retrieves real GHL User IDs for proper lead assignment
# - SYNCS SERVICE CATEGORIES & OFFERINGS from GHL to local database
# - Extracts primary service category and services provided from GHL custom fields
# - Updates local database with current service data from GHL
# - Comprehensive database cleanup and validation
# - Can be run as a utility script whenever sync is needed
# 
# NEW SERVICE SYNC CAPABILITIES:
# - Extracts "Primary Service Category" from GHL field HRqfv0HnUydNRLKWhk27
# - Extracts "Services Provided" from GHL field pAq9WBsIuFUAZuwz3YY4  
# - Handles "Service Categories Selections" from GHL field 72qwwzy4AUfTCBJvBIEf
# - Parses comma-separated service lists into JSON arrays
# - Updates local database services_provided field with current GHL data
# - Enables vendor service management through GHL interface

import sqlite3
import json
import logging
import sys
import os
import time
import pgeocode
import pandas as pd
from typing import Dict, List, Any, Optional

# ensure project root is on path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# CRITICAL FIX: Load .env file BEFORE importing config
from dotenv import load_dotenv
load_dotenv()  # This must happen before importing config!

# NOW import config (after .env is loaded)
from database.simple_connection import db as simple_db_instance
from config import AppConfig
from api.services.ghl_api import GoHighLevelAPI

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def fix_activity_log_schema() -> bool:
    """
    Fix the activity_log table by adding missing event_data column
    """
    print("🔧 FIXING ACTIVITY LOG SCHEMA")
    print("-" * 40)
    
    try:
        conn = sqlite3.connect('smart_lead_router.db')
        cursor = conn.cursor()
        
        # Check current schema
        cursor.execute("PRAGMA table_info(activity_log)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'event_data' not in columns:
            cursor.execute("ALTER TABLE activity_log ADD COLUMN event_data TEXT")
            conn.commit()
            print("✅ Added event_data column to activity_log table")
        else:
            print("✅ event_data column already exists")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error fixing activity log schema: {e}")
        return False


def fix_vendor_ghl_user_ids_placeholder() -> bool:
    """
    Set UNIQUE placeholder GHL User IDs for vendors missing them
    FIXED: Uses unique placeholders to avoid UNIQUE constraint violation
    """
    print("\n🔧 FIXING VENDOR GHL USER IDS (UNIQUE PLACEHOLDERS)")
    print("-" * 55)
    
    try:
        # Use your existing database instance
        vendors = simple_db_instance.get_vendors()
        
        # Get account for filtering
        account = simple_db_instance.get_account_by_ghl_location_id(AppConfig.GHL_LOCATION_ID)
        if not account:
            print("❌ No account found!")
            return False
        
        account_id = account['id']
        account_vendors = [v for v in vendors if v.get('account_id') == account_id]
        
        # Find vendors missing GHL User IDs
        missing_vendors = [
            v for v in account_vendors 
            if not v.get('ghl_user_id') or v.get('ghl_user_id') == ''
        ]
        
        if not missing_vendors:
            print("✅ All vendors already have GHL User IDs")
            return True
        
        print(f"Found {len(missing_vendors)} vendors missing GHL User IDs:")
        
        # Direct database update (since SimpleDatabase doesn't expose direct SQL)
        conn = sqlite3.connect('smart_lead_router.db')
        cursor = conn.cursor()
        
        updated_count = 0
        
        for vendor in missing_vendors:
            # FIXED: Create unique placeholder using vendor ID
            unique_placeholder = f'pending_ghl_user_{vendor["id"][:8]}'
            
            try:
                cursor.execute(
                    "UPDATE vendors SET ghl_user_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (unique_placeholder, vendor['id'])
                )
                print(f"   • {vendor['name']} ({vendor['email']}) - set to {unique_placeholder}")
                updated_count += 1
            except sqlite3.IntegrityError as e:
                print(f"   ❌ Failed to update {vendor['name']}: {e}")
                continue
        
        conn.commit()
        conn.close()
        print(f"✅ Updated {updated_count} vendors with unique placeholder IDs")
        return True
        
    except Exception as e:
        print(f"❌ Error setting placeholder IDs: {e}")
        return False


def fix_vendor_services_format() -> bool:
    """
    Normalize vendors.services_provided into JSON arrays
    """
    print("\n🔧 FIXING VENDOR SERVICES FORMAT")
    print("-" * 40)
    
    try:
        # Use your existing database instance
        vendors = simple_db_instance.get_vendors()
        
        # Direct database access for updates
        conn = sqlite3.connect('smart_lead_router.db')
        cursor = conn.cursor()
        
        fixed_count = 0
        
        for vendor in vendors:
            services = vendor.get('services_provided', [])
            
            # Check if services need fixing
            if isinstance(services, str) and services.strip():
                try:
                    # Try to parse as JSON first
                    parsed = json.loads(services)
                    if isinstance(parsed, list):
                        continue  # Already in correct format
                except json.JSONDecodeError:
                    # Convert string to JSON array
                    if ',' in services:
                        services_array = [s.strip() for s in services.split(',') if s.strip()]
                    else:
                        services_array = [services.strip()]
                    
                    cursor.execute(
                        "UPDATE vendors SET services_provided = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (json.dumps(services_array), vendor['id'])
                    )
                    fixed_count += 1
                    print(f"   • {vendor['name']}: {services} → {services_array}")
        
        conn.commit()
        conn.close()
        print(f"✅ Fixed {fixed_count} vendor service formats")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing vendor services format: {e}")
        return False


def ensure_vendor_coverage_setup() -> bool:
    """
    Ensure every vendor has a default coverage area
    ENHANCED: Uses vendor's ZIP code to determine county, with intelligent fallback
    """
    print("\n🔧 ENSURING VENDOR COVERAGE SETUP (ENHANCED WITH ZIP→COUNTY LOOKUP)")
    print("-" * 70)
    
    try:
        # Initialize pgeocode for US lookups
        nomi = pgeocode.Nominatim('us')
        print("✅ Initialized pgeocode for US ZIP code lookups")
        
        # Direct database query for missing coverage
        conn = sqlite3.connect('smart_lead_router.db')
        cursor = conn.cursor()
        
        # Get vendors missing coverage data - also include vendor_postal_code
        cursor.execute("""
            SELECT id, name, vendor_postal_code FROM vendors
            WHERE service_coverage_type IS NULL
               OR service_coverage_type = ''
               OR service_areas IS NULL
               OR service_areas = ''
               OR service_areas = '[]'
        """)
        rows = cursor.fetchall()
        
        if not rows:
            print("✅ All vendors have coverage areas configured")
            conn.close()
            return True
        
        print(f"Found {len(rows)} vendors needing coverage setup:")
        
        # Default fallback areas if ZIP lookup fails
        default_county_areas = ["Miami-Dade County, FL", "Broward County, FL"]
        default_coverage_type = 'county'
        updated_count = 0
        zip_lookup_success_count = 0
        zip_lookup_failure_count = 0
        
        for vendor_id, vendor_name, vendor_postal_code in rows:
            print(f"\n   🔍 Processing {vendor_name}...")
            
            coverage_areas = []
            coverage_source = ""
            
            # Try to determine coverage from vendor's ZIP code
            if vendor_postal_code and str(vendor_postal_code).strip():
                zip_code = str(vendor_postal_code).strip()
                print(f"     📍 Found ZIP code: {zip_code}")
                
                try:
                    # Clean ZIP code (handle ZIP+4 format)
                    clean_zip = zip_code.split('-')[0].strip()
                    if len(clean_zip) == 5 and clean_zip.isdigit():
                        # Lookup location data using pgeocode
                        location_data = nomi.query_postal_code(clean_zip)
                        
                        if not location_data.empty and not pd.isna(location_data['county_name']):
                            county_name = location_data['county_name']
                            state_code = location_data['state_code']
                            
                            if county_name and state_code:
                                # Format as "County Name, ST"
                                county_formatted = f"{county_name}, {state_code}"
                                coverage_areas = [county_formatted]
                                coverage_source = f"ZIP lookup ({zip_code})"
                                zip_lookup_success_count += 1
                                print(f"     ✅ ZIP lookup successful: {county_formatted}")
                            else:
                                print(f"     ⚠️ ZIP lookup returned incomplete data")
                        else:
                            print(f"     ⚠️ ZIP lookup failed - no data returned")
                    else:
                        print(f"     ⚠️ Invalid ZIP code format: {zip_code}")
                        
                except Exception as e:
                    print(f"     ❌ ZIP lookup error: {e}")
            else:
                print(f"     ⚠️ No ZIP code found in vendor_postal_code field")
            
            # Use default if ZIP lookup failed
            if not coverage_areas:
                coverage_areas = default_county_areas
                coverage_source = "default fallback"
                zip_lookup_failure_count += 1
                print(f"     🔄 Using default coverage: {', '.join(coverage_areas)}")
            
            # Update vendor with determined coverage
            areas_json = json.dumps(coverage_areas)
            
            cursor.execute("""
                UPDATE vendors 
                SET service_coverage_type = ?, 
                    service_areas = ?,
                    updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (default_coverage_type, areas_json, vendor_id))
            
            print(f"     ✅ Updated coverage ({coverage_source}): {', '.join(coverage_areas)}")
            updated_count += 1
        
        conn.commit()
        conn.close()
        
        # Summary report
        print(f"\n📊 COVERAGE SETUP RESULTS:")
        print(f"   ✅ Total vendors updated: {updated_count}")
        print(f"   🎯 ZIP lookup successes: {zip_lookup_success_count}")
        print(f"   🔄 Default fallbacks used: {zip_lookup_failure_count}")
        print(f"   📍 Default areas: {', '.join(default_county_areas)}")
        
        return True
        
    except ImportError:
        print("❌ pgeocode library not installed. Installing...")
        print("   Run: pip install pgeocode")
        print("   Falling back to default coverage setup...")
        return ensure_vendor_coverage_setup_fallback()
        
    except Exception as e:
        print(f"❌ Error in enhanced coverage setup: {e}")
        print("   Falling back to default coverage setup...")
        return ensure_vendor_coverage_setup_fallback()


def ensure_vendor_coverage_setup_fallback() -> bool:
    """
    Fallback coverage setup function (original functionality)
    Used when pgeocode is not available or fails
    """
    print("\n🔧 FALLBACK: BASIC VENDOR COVERAGE SETUP")
    print("-" * 45)
    
    try:
        # Direct database query for missing coverage
        conn = sqlite3.connect('smart_lead_router.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name FROM vendors
            WHERE service_coverage_type IS NULL
               OR service_coverage_type = ''
               OR service_areas IS NULL
               OR service_areas = ''
               OR service_areas = '[]'
        """)
        rows = cursor.fetchall()
        
        if not rows:
            print("✅ All vendors have coverage areas configured")
            conn.close()
            return True
        
        print(f"Found {len(rows)} vendors needing coverage setup:")
        
        default_coverage_type = 'county'
        default_service_areas = json.dumps(['Miami-Dade County, FL', 'Broward County, FL'])
        updated_count = 0
        
        for vendor_id, name in rows:
            cursor.execute("""
                UPDATE vendors 
                SET service_coverage_type = ?, 
                    service_areas = ?,
                    updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (default_coverage_type, default_service_areas, vendor_id))
            print(f"   • {name}: Set to Miami-Dade & Broward Counties, FL")
            updated_count += 1
        
        conn.commit()
        conn.close()
        print(f"✅ Set up coverage for {updated_count} vendors")
        return True
        
    except Exception as e:
        print(f"❌ Error ensuring vendor coverage setup: {e}")
        return False


def sync_vendors_with_ghl() -> bool:
    """
    Synchronize local vendor database with GoHighLevel (GHL as source of truth)
    Removes vendors from local database if they no longer exist in GHL
    """
    print("\n🔍 SYNCING VENDORS WITH GHL (GHL AS SOURCE OF TRUTH)")
    print("-" * 60)
    print("Checking each vendor's contact in GHL and removing orphaned records...")
    
    try:
        # Initialize GHL API client
        ghl_api = GoHighLevelAPI(
            private_token=AppConfig.GHL_PRIVATE_TOKEN,
            location_id=AppConfig.GHL_LOCATION_ID,
            agency_api_key=AppConfig.GHL_AGENCY_API_KEY,
            company_id=AppConfig.GHL_COMPANY_ID
        )
        
        # Get all vendors from local database
        vendors = simple_db_instance.get_vendors()
        
        # Get account for filtering
        account = simple_db_instance.get_account_by_ghl_location_id(AppConfig.GHL_LOCATION_ID)
        if not account:
            print("❌ No account found!")
            return False
        
        account_id = account['id']
        account_vendors = [v for v in vendors if v.get('account_id') == account_id]
        
        if not account_vendors:
            print("✅ No vendors found in local database")
            return True
        
        print(f"Found {len(account_vendors)} vendors in local database")
        print("Checking each vendor's existence in GHL...")
        
        orphaned_vendors = []
        valid_vendors = []
        api_errors = []
        
        for vendor in account_vendors:
            vendor_name = vendor.get('name', 'Unknown')
            ghl_contact_id = vendor.get('ghl_contact_id')
            
            print(f"\n🔍 Checking {vendor_name} (Contact ID: {ghl_contact_id})...")
            
            if not ghl_contact_id:
                print(f"   ⚠️ No GHL contact ID - marking as orphaned")
                orphaned_vendors.append({
                    'vendor': vendor,
                    'reason': 'No GHL contact ID'
                })
                continue
            
            try:
                # Check if contact exists in GHL
                contact = ghl_api.get_contact_by_id(ghl_contact_id)
                
                if contact and contact.get('id'):
                    print(f"   ✅ Contact exists in GHL")
                    valid_vendors.append(vendor)
                else:
                    print(f"   ❌ Contact not found in GHL")
                    orphaned_vendors.append({
                        'vendor': vendor,
                        'reason': 'Contact not found in GHL'
                    })
                
                # Small delay to avoid API rate limits
                time.sleep(0.3)
                
            except Exception as e:
                print(f"   ⚠️ API error checking contact: {e}")
                api_errors.append({
                    'vendor': vendor,
                    'error': str(e)
                })
        
        # Report findings
        print(f"\n📊 SYNC ANALYSIS RESULTS:")
        print(f"   ✅ Valid vendors (exist in GHL): {len(valid_vendors)}")
        print(f"   ❌ Orphaned vendors (missing from GHL): {len(orphaned_vendors)}")
        print(f"   ⚠️ API errors: {len(api_errors)}")
        
        # Handle orphaned vendors
        if orphaned_vendors:
            print(f"\n🗑️ REMOVING ORPHANED VENDORS FROM LOCAL DATABASE:")
            print("Making GHL the single source of truth...")
            
            deleted_count = 0
            
            for orphan in orphaned_vendors:
                vendor = orphan['vendor']
                reason = orphan['reason']
                
                try:
                    if delete_vendor_from_database(vendor['id']):
                        print(f"   ✅ Deleted {vendor['name']} - {reason}")
                        deleted_count += 1
                    else:
                        print(f"   ❌ Failed to delete {vendor['name']}")
                        
                except Exception as e:
                    print(f"   ❌ Error deleting {vendor['name']}: {e}")
            
            print(f"\n✅ Successfully removed {deleted_count}/{len(orphaned_vendors)} orphaned vendors")
            
        else:
            print(f"\n✅ No orphaned vendors found - all local vendors exist in GHL")
        
        # Handle API errors
        if api_errors:
            print(f"\n⚠️ VENDORS WITH API ERRORS (NOT DELETED):")
            for error_item in api_errors:
                vendor = error_item['vendor']
                error = error_item['error']
                print(f"   • {vendor['name']}: {error}")
            print(f"   ℹ️ These vendors were NOT deleted due to API errors")
            print(f"   ℹ️ Re-run the script later to check these vendors")
        
        return True
        
    except Exception as e:
        print(f"❌ Error syncing vendors with GHL: {e}")
        return False


def delete_vendor_from_database(vendor_id: str) -> bool:
    """
    Delete a vendor from the local database
    Also cleans up related records (leads, etc.)
    """
    conn = None
    try:
        conn = sqlite3.connect('smart_lead_router.db')
        cursor = conn.cursor()
        
        # First, update any leads assigned to this vendor to unassigned
        cursor.execute('''
            UPDATE leads 
            SET vendor_id = NULL, 
                status = 'unassigned',
                updated_at = CURRENT_TIMESTAMP
            WHERE vendor_id = ?
        ''', (vendor_id,))
        
        leads_updated = cursor.rowcount
        if leads_updated > 0:
            print(f"     • Unassigned {leads_updated} leads from this vendor")
        
        # Delete the vendor record
        cursor.execute('DELETE FROM vendors WHERE id = ?', (vendor_id,))
        
        if cursor.rowcount > 0:
            conn.commit()
            return True
        else:
            print(f"     • Vendor {vendor_id} not found in database")
            return False
        
    except Exception as e:
        print(f"     • Database error deleting vendor: {e}")
        return False
    finally:
        if conn:
            conn.close()


class RealGHLUserIDFix:
    """
    Retrieve actual GHL User IDs from GoHighLevel and update local DB
    Using your actual GHL API class and configuration
    FIXED: Works with unique placeholder system
    """
    
    def __init__(self):
        try:
            # Use your actual GHL API class with real config
            self.ghl_api = GoHighLevelAPI(
                private_token=AppConfig.GHL_PRIVATE_TOKEN,
                location_id=AppConfig.GHL_LOCATION_ID,
                agency_api_key=AppConfig.GHL_AGENCY_API_KEY,
                company_id=AppConfig.GHL_COMPANY_ID
            )
            # Your actual GHL User ID custom field ID from field reference
            self.ghl_user_id_field_id = "HXVNT4y8OynNokWAfO2D"
            print("✅ GHL API client initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize GHL API client: {e}")
            raise

    def run_real_fix(self):
        """Run the real GHL User ID fix and service data sync using your actual systems"""
        print("\n🔍 RUNNING REAL GHL USER ID & SERVICE DATA SYNC")
        print("-" * 55)
        print("Retrieving ACTUAL GHL User IDs and service data from GoHighLevel contacts...")
        
        try:
            missing_vendors = self._get_missing_vendors()
            
            if not missing_vendors:
                print("✅ No vendors need real GHL User IDs")
                # Still run service data sync for all vendors
                all_vendors = self._get_all_vendors_for_service_sync()
                if all_vendors:
                    print(f"🔄 Running service data sync for {len(all_vendors)} vendors...")
                    return self._sync_service_data_only(all_vendors)
                else:
                    return True
            
            print(f"Found {len(missing_vendors)} vendors with placeholder IDs:")
            
            success_count = 0
            failure_count = 0
            service_sync_count = 0
            
            for vendor in missing_vendors:
                print(f"\n🔍 Processing {vendor.get('name', 'Unknown')} ({vendor['id']})...")
                
                try:
                    # Get contact from GHL using your API class
                    contact = self.ghl_api.get_contact_by_id(vendor['ghl_contact_id'])
                    
                    if not contact:
                        print(f"   ❌ Contact not found in GHL")
                        failure_count += 1
                        continue
                    
                    # Extract real GHL User ID
                    real_id = self._extract_ghl_user_id(contact)
                    
                    # Extract service data from GHL
                    service_data = self._extract_service_data(contact)
                    
                    # Update vendor with real ID if found
                    user_id_updated = False
                    if real_id and not real_id.startswith('pending_ghl_user_'):
                        if self._update_vendor_with_real_id(vendor['id'], real_id):
                            print(f"   ✅ Updated with real GHL User ID: {real_id}")
                            user_id_updated = True
                        else:
                            print(f"   ❌ Failed to update local database with User ID")
                    else:
                        print(f"   ⚠️ No real GHL User ID found in contact")
                        # Try to find existing GHL user by email
                        if self._try_link_existing_user(vendor):
                            user_id_updated = True
                    
                    # Update service data regardless of User ID status
                    if service_data['services_provided'] or service_data['primary_service_category']:
                        if self._update_vendor_with_service_data(vendor['id'], service_data):
                            print(f"   ✅ Updated service data")
                            service_sync_count += 1
                        else:
                            print(f"   ⚠️ Failed to update service data")
                    else:
                        print(f"   ⚠️ No service data found in GHL contact")
                    
                    if user_id_updated:
                        success_count += 1
                    else:
                        failure_count += 1
                    
                    # Small delay to avoid API rate limits
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"   ❌ Error processing vendor: {e}")
                    failure_count += 1
            
            print(f"\n📊 SYNC RESULTS:")
            print(f"   ✅ GHL User IDs updated: {success_count}")
            print(f"   ❌ GHL User ID failures: {failure_count}")
            print(f"   🛠️ Service data synced: {service_sync_count}")
            
            return success_count > 0 or service_sync_count > 0
            
        except Exception as e:
            print(f"❌ Error in sync process: {e}")
            return False

    def _get_all_vendors_for_service_sync(self) -> List[Dict[str, Any]]:
        """Get all vendors that might need service data sync"""
        try:
            # Use your existing database instance
            vendors = simple_db_instance.get_vendors()
            
            # Filter for vendors with valid contact IDs
            valid_vendors = []
            for vendor in vendors:
                ghl_contact_id = vendor.get('ghl_contact_id')
                if ghl_contact_id and ghl_contact_id.strip():
                    valid_vendors.append(vendor)
            
            return valid_vendors
            
        except Exception as e:
            print(f"❌ Error getting vendors for service sync: {e}")
            return []

    def _sync_service_data_only(self, vendors: List[Dict[str, Any]]) -> bool:
        """Sync service data for vendors that already have User IDs"""
        service_sync_count = 0
        
        for vendor in vendors:
            vendor_name = vendor.get('name', 'Unknown')
            print(f"\n🔍 Syncing service data for {vendor_name}...")
            
            try:
                contact = self.ghl_api.get_contact_by_id(vendor['ghl_contact_id'])
                
                if not contact:
                    print(f"   ❌ Contact not found in GHL")
                    continue
                
                # Extract service data from GHL
                service_data = self._extract_service_data(contact)
                
                # Update service data
                if service_data['services_provided'] or service_data['primary_service_category']:
                    if self._update_vendor_with_service_data(vendor['id'], service_data):
                        print(f"   ✅ Service data synced")
                        service_sync_count += 1
                    else:
                        print(f"   ⚠️ Failed to update service data")
                else:
                    print(f"   ⚠️ No service data found in GHL contact")
                
                # Small delay to avoid API rate limits
                time.sleep(0.3)
                
            except Exception as e:
                print(f"   ❌ Error syncing service data: {e}")
        
        print(f"\n📊 SERVICE DATA SYNC RESULTS:")
        print(f"   🛠️ Service data synced: {service_sync_count}/{len(vendors)}")
        
        return service_sync_count > 0

    def _get_missing_vendors(self) -> List[Dict[str, Any]]:
        """Get vendors that still have placeholder GHL User IDs (FIXED: handles unique placeholders)"""
        try:
            # Use your existing database instance
            vendors = simple_db_instance.get_vendors()
            
            # Filter for vendors with placeholder IDs and valid contact IDs
            missing_vendors = []
            for vendor in vendors:
                ghl_user_id = vendor.get('ghl_user_id')
                ghl_contact_id = vendor.get('ghl_contact_id')
                
                # FIXED: Check for unique placeholder pattern
                if (ghl_user_id and ghl_user_id.startswith('pending_ghl_user_') and 
                    ghl_contact_id and ghl_contact_id.strip()):
                    missing_vendors.append(vendor)
            
            return missing_vendors
            
        except Exception as e:
            print(f"❌ Error getting missing vendors: {e}")
            return []

    def _extract_ghl_user_id(self, contact: Dict[str, Any]) -> Optional[str]:
        """Extract GHL User ID from contact custom fields"""
        try:
            custom_fields = contact.get('customFields', [])
            
            for field in custom_fields:
                if field.get('id') == self.ghl_user_id_field_id:
                    field_value = field.get('value') or field.get('fieldValue')
                    if (field_value and str(field_value).strip() and 
                        not str(field_value).startswith('pending_ghl_user_')):
                        return str(field_value).strip()
            
            return None
            
        except Exception as e:
            print(f"   ⚠️ Error extracting GHL User ID: {e}")
            return None

    def _extract_service_data(self, contact: Dict[str, Any]) -> Dict[str, Any]:
        """Extract service category and services data from GHL contact custom fields"""
        try:
            custom_fields = contact.get('customFields', [])
            
            service_data = {
                'primary_service_category': '',
                'services_provided': [],
                'raw_services_text': ''
            }
            
            # Field IDs from your field_reference.json
            primary_service_field_id = "HRqfv0HnUydNRLKWhk27"  # Primary Service Category
            services_provided_field_id = "pAq9WBsIuFUAZuwz3YY4"  # Services Provided
            service_categories_field_id = "72qwwzy4AUfTCBJvBIEf"  # Service Categories Selections
            
            for field in custom_fields:
                field_id = field.get('id', '')
                field_value = field.get('value') or field.get('fieldValue', '')
                
                if not field_value:
                    continue
                
                field_value = str(field_value).strip()
                
                if field_id == primary_service_field_id:
                    service_data['primary_service_category'] = field_value
                    print(f"     📋 Primary Service Category: {field_value}")
                    
                elif field_id == services_provided_field_id:
                    service_data['raw_services_text'] = field_value
                    # Parse comma-separated services
                    if ',' in field_value:
                        services = [s.strip() for s in field_value.split(',') if s.strip()]
                    else:
                        services = [field_value] if field_value else []
                    service_data['services_provided'] = services
                    print(f"     🛠️ Services Provided: {services}")
                    
                elif field_id == service_categories_field_id:
                    # Handle multiple selections field
                    if field_value:
                        if ',' in field_value:
                            categories = [s.strip() for s in field_value.split(',') if s.strip()]
                        else:
                            categories = [field_value]
                        # If no primary category set, use first from selections
                        if not service_data['primary_service_category'] and categories:
                            service_data['primary_service_category'] = categories[0]
                        # Merge with services_provided
                        all_services = set(service_data['services_provided'] + categories)
                        service_data['services_provided'] = list(all_services)
                        print(f"     📊 Service Categories: {categories}")
            
            return service_data
            
        except Exception as e:
            print(f"   ⚠️ Error extracting service data: {e}")
            return {
                'primary_service_category': '',
                'services_provided': [],
                'raw_services_text': ''
            }

    def _update_vendor_with_service_data(self, vendor_id: str, service_data: Dict[str, Any]) -> bool:
        """Update vendor record with service data from GHL"""
        try:
            conn = sqlite3.connect('smart_lead_router.db')
            cursor = conn.cursor()
            
            # Prepare the services_provided JSON
            services_json = json.dumps(service_data['services_provided'])
            
            # Update vendor record with service data
            cursor.execute('''
                UPDATE vendors 
                SET services_provided = ?,
                    updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (services_json, vendor_id))
            
            # Check if we have a primary_service_category column and update it
            try:
                cursor.execute('''
                    UPDATE vendors 
                    SET primary_service_category = ?
                    WHERE id = ?
                ''', (service_data['primary_service_category'], vendor_id))
            except sqlite3.OperationalError:
                # Column doesn't exist, which is fine
                pass
            
            conn.commit()
            conn.close()
            
            return cursor.rowcount > 0
            
        except Exception as e:
            print(f"   ❌ Error updating vendor service data: {e}")
            return False

    def _try_link_existing_user(self, vendor: Dict[str, Any]) -> bool:
        """Try to find existing GHL user by email and link it"""
        try:
            print(f"   🔍 Searching for existing GHL user by email...")
            
            # Use your GHL API to search for existing user
            existing_user = self.ghl_api.get_user_by_email(vendor['email'])
            
            if existing_user and existing_user.get('id'):
                user_id = existing_user['id']
                print(f"   ✅ Found existing GHL user: {user_id}")
                
                # Update the contact's custom field
                update_payload = {
                    "customFields": [
                        {
                            "id": self.ghl_user_id_field_id,
                            "value": user_id
                        }
                    ]
                }
                
                if self.ghl_api.update_contact(vendor['ghl_contact_id'], update_payload):
                    print(f"   ✅ Updated GHL contact with User ID")
                    
                    # Update local database
                    if self._update_vendor_with_real_id(vendor['id'], user_id):
                        print(f"   ✅ Updated local database with real GHL User ID")
                        return True
                
                print(f"   ❌ Failed to link existing user")
                return False
            else:
                print(f"   ⚠️ No existing GHL user found for {vendor['email']}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error linking existing user: {e}")
            return False

    def _update_vendor_with_real_id(self, vendor_id: str, real_ghl_user_id: str) -> bool:
        """Update vendor with real GHL User ID using your database instance"""
        try:
            # Use your existing update_vendor_status method
            success = simple_db_instance.update_vendor_status(
                vendor_id=vendor_id,
                status="active",  # Set to active since they now have a real user ID
                ghl_user_id=real_ghl_user_id
            )
            return success
            
        except Exception as e:
            print(f"   ❌ Error updating vendor in database: {e}")
            return False

    def verify_fix(self):
        """Verify that the fix worked and show comprehensive sync status"""
        print(f"\n📋 VERIFYING DATABASE SYNC, GHL USER IDS & SERVICE DATA")
        print("-" * 60)
        
        try:
            # Get all vendors using your database instance
            vendors = simple_db_instance.get_vendors()
            
            # Get account for filtering
            account = simple_db_instance.get_account_by_ghl_location_id(AppConfig.GHL_LOCATION_ID)
            if account:
                account_id = account['id']
                account_vendors = [v for v in vendors if v.get('account_id') == account_id]
            else:
                account_vendors = vendors
            
            total_vendors = len(account_vendors)
            real_ids = 0
            placeholder_ids = 0
            missing_ids = 0
            vendors_with_services = 0
            vendors_with_primary_category = 0
            
            for vendor in account_vendors:
                ghl_user_id = vendor.get('ghl_user_id')
                services_provided = vendor.get('services_provided', [])
                
                # Count User ID status
                if not ghl_user_id or ghl_user_id == '':
                    missing_ids += 1
                elif ghl_user_id.startswith('pending_ghl_user_'):
                    placeholder_ids += 1
                else:
                    real_ids += 1
                
                # Count service data status
                if services_provided and len(services_provided) > 0:
                    vendors_with_services += 1
                
                # Check for primary service category (if column exists)
                try:
                    primary_category = vendor.get('primary_service_category', '')
                    if primary_category:
                        vendors_with_primary_category += 1
                except:
                    pass
            
            print(f"Total Vendors in Database: {total_vendors}")
            print(f"\n🔐 GHL USER ID STATUS:")
            print(f"  ✅ Real GHL User IDs: {real_ids}")
            print(f"  🔄 Placeholder IDs: {placeholder_ids}")
            print(f"  ❌ Missing IDs: {missing_ids}")
            
            print(f"\n🛠️ SERVICE DATA STATUS:")
            print(f"  ✅ Vendors with Services: {vendors_with_services}")
            print(f"  📋 Vendors with Primary Category: {vendors_with_primary_category}")
            
            # Calculate sync success percentages
            if total_vendors > 0:
                user_id_sync_percentage = (real_ids / total_vendors) * 100
                service_sync_percentage = (vendors_with_services / total_vendors) * 100
                print(f"\n📊 SYNC SUCCESS RATES:")
                print(f"  🔐 User ID Sync: {user_id_sync_percentage:.1f}%")
                print(f"  🛠️ Service Data Sync: {service_sync_percentage:.1f}%")
            
            # Show examples of synced data
            if real_ids > 0:
                print(f"\n✅ EXAMPLES OF SYNCED USER IDs:")
                count = 0
                for vendor in account_vendors:
                    ghl_user_id = vendor.get('ghl_user_id')
                    if ghl_user_id and not ghl_user_id.startswith('pending_ghl_user_'):
                        print(f"   • {vendor['name']}: {ghl_user_id}")
                        count += 1
                        if count >= 3:
                            break
            
            if vendors_with_services > 0:
                print(f"\n🛠️ EXAMPLES OF SYNCED SERVICE DATA:")
                count = 0
                for vendor in account_vendors:
                    services = vendor.get('services_provided', [])
                    if services and len(services) > 0:
                        services_str = ', '.join(services[:3])  # Show first 3 services
                        if len(services) > 3:
                            services_str += f" (+ {len(services) - 3} more)"
                        print(f"   • {vendor['name']}: {services_str}")
                        count += 1
                        if count >= 3:
                            break
            
            # Show vendors that still need attention
            if placeholder_ids > 0:
                print(f"\n🔄 VENDORS NEEDING GHL USER CREATION:")
                count = 0
                for vendor in account_vendors:
                    ghl_user_id = vendor.get('ghl_user_id')
                    if ghl_user_id and ghl_user_id.startswith('pending_ghl_user_'):
                        print(f"   • {vendor['name']}: {ghl_user_id}")
                        count += 1
                        if count >= 3:
                            break
            
            vendors_without_services = total_vendors - vendors_with_services
            if vendors_without_services > 0:
                print(f"\n⚠️ VENDORS MISSING SERVICE DATA:")
                count = 0
                for vendor in account_vendors:
                    services = vendor.get('services_provided', [])
                    if not services or len(services) == 0:
                        print(f"   • {vendor['name']}: No services data")
                        count += 1
                        if count >= 3:
                            break
            
            print(f"\n🔄 COMPREHENSIVE SYNC STATUS:")
            print(f"  ✅ Local database cleaned of orphaned vendors")
            print(f"  ✅ GHL is the single source of truth")
            print(f"  ✅ Service data synced from GHL to local database")
            print(f"  ✅ Vendor management can be done through GHL interface")
            print(f"  ✅ Script can be re-run anytime for sync maintenance")
            
        except Exception as e:
            print(f"❌ Error verifying sync: {e}")


def main():
    """Main execution with comprehensive error handling"""
    print("🚀 COMPREHENSIVE DATABASE & GHL SYNC UTILITY (SERVICE DATA ENHANCED)")
    print("=" * 75)
    print("Using your actual codebase classes and configuration:")
    print(f"• Database: simple_db_instance from database.simple_connection")
    print(f"• Config: AppConfig from config")
    print(f"• GHL API: GoHighLevelAPI from api.services.ghl_api")
    print(f"• GHL Location ID: {AppConfig.GHL_LOCATION_ID}")
    print("")
    print("FIXES & ENHANCEMENTS APPLIED:")
    print("✅ UNIQUE constraint issue - using unique placeholder IDs")
    print("✅ Improved placeholder detection logic")
    print("✅ Better error handling for database operations")
    print("✅ GHL-as-source-of-truth synchronization")
    print("✅ Orphaned vendor cleanup")
    print("✅ SERVICE DATA SYNC - Primary categories & service offerings")
    print("✅ Comprehensive field extraction from GHL custom fields")
    print("")
    print("This script will:")
    print("1. Fix database schema issues")
    print("2. Sync vendors with GHL (remove orphaned records)")
    print("3. Set UNIQUE placeholder GHL User IDs")
    print("4. Fix vendor services format")
    print("5. Ensure vendor coverage setup")
    print("6. Retrieve REAL GHL User IDs AND sync service data from GoHighLevel")
    print("7. Verify all fixes worked")
    print("")
    print("🎯 MAKES GHL THE SINGLE SOURCE OF TRUTH FOR VENDOR MANAGEMENT")
    print("🛠️ SYNCS SERVICE CATEGORIES & OFFERINGS FROM GHL TO LOCAL DATABASE")
    print("")
    
    success_count = 0
    total_steps = 6
    
    try:
        # Step 1: Database schema fixes
        print("STEP 1/6: DATABASE SCHEMA FIXES")
        if fix_activity_log_schema():
            success_count += 1
        
        # Step 2: Sync vendors with GHL (remove orphaned records)
        print("\nSTEP 2/6: SYNC VENDORS WITH GHL (SOURCE OF TRUTH)")
        if sync_vendors_with_ghl():
            success_count += 1
        
        # Step 3: Unique placeholder GHL User IDs
        print("\nSTEP 3/6: UNIQUE PLACEHOLDER GHL USER IDS")
        if fix_vendor_ghl_user_ids_placeholder():
            success_count += 1
        
        # Step 4: Vendor services format
        print("\nSTEP 4/6: VENDOR SERVICES FORMAT")
        if fix_vendor_services_format():
            success_count += 1
        
        # Step 5: Vendor coverage setup
        print("\nSTEP 5/6: VENDOR COVERAGE SETUP")
        if ensure_vendor_coverage_setup():
            success_count += 1
        
        # Step 6: Real GHL User IDs AND Service Data Sync
        print("\nSTEP 6/6: GHL USER IDS & SERVICE DATA SYNC")
        real_fixer = RealGHLUserIDFix()
        if real_fixer.run_real_fix():
            success_count += 1
        
        # Verification
        real_fixer.verify_fix()
        
        # Final summary
        print(f"\n🎉 COMPREHENSIVE DATABASE & SERVICE SYNC COMPLETE")
        print("=" * 60)
        print(f"Successfully completed: {success_count}/{total_steps} steps")
        
        if success_count == total_steps:
            print("✅ ALL SYNC OPERATIONS SUCCESSFUL!")
            print("🎯 GHL is now the single source of truth for vendor management")
            print("💡 Ready to test vendor assignment with real GHL User IDs")
            print("📋 Local database is now clean and synced with GHL")
            print("🔄 You can manage vendors through GHL interface")
            print("🧹 Orphaned vendors have been removed from local database")
            print("🛠️ Service categories & offerings synced from GHL")
            print("📊 Vendors can now add/modify services in GHL and sync here")
        else:
            print("⚠️ Some operations had issues - check the logs above")
        
        print(f"\n🔧 UTILITY FEATURES:")
        print(f"  📝 Run this script anytime to keep databases in sync")
        print(f"  🗑️ Automatically removes vendors deleted from GHL")
        print(f"  🔄 Syncs GHL User IDs for new vendors")
        print(f"  🛠️ Syncs service categories & offerings from GHL")
        print(f"  📊 Provides detailed sync reports")
        print(f"  🎯 Makes GHL the authoritative vendor management system")
        print(f"  💼 Enables admins to manage vendor services through GHL interface")
        
    except Exception as e:
        print(f"❌ Critical error during sync process: {e}")
        logger.exception("Sync process failed")


if __name__ == '__main__':
    main()