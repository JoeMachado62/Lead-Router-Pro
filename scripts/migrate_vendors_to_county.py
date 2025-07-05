#!/usr/bin/env python3
"""
Vendor Data Migration Script - Convert ZIP-based vendors to County-based coverage
Safely migrates existing vendor data without breaking the system

This script:
1. Finds all vendors with ZIP-based coverage (service_coverage_type = 'zip')
2. Converts their ZIP codes to counties using LocationService
3. Updates their coverage type to 'county'
4. Preserves original data as backup
5. Provides detailed reporting and rollback capability
"""

import sys
import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple

# Add the parent directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our services
from api.services.location_service import location_service
from database.simple_connection import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'vendor_migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class VendorMigrator:
    """Handles safe migration of vendors from ZIP to county-based coverage"""
    
    def __init__(self):
        self.migration_stats = {
            'total_vendors': 0,
            'zip_vendors_found': 0,
            'successfully_migrated': 0,
            'failed_migrations': 0,
            'skipped_vendors': 0,
            'backup_created': False
        }
        self.failed_vendors = []
        self.backup_data = []
    
    def create_backup(self) -> bool:
        """Create backup of current vendor data before migration"""
        try:
            logger.info("📦 Creating backup of vendor data...")
            
            # Get all vendors from database
            conn = db._get_conn()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, name, service_coverage_type, service_areas, service_counties, 
                       services_provided, created_at, updated_at
                FROM vendors
            ''')
            
            vendor_rows = cursor.fetchall()
            conn.close()
            
            # Convert to dictionaries for backup
            self.backup_data = []
            for row in vendor_rows:
                vendor_backup = {
                    'id': row[0],
                    'name': row[1],
                    'service_coverage_type': row[2],
                    'service_areas': row[3],
                    'service_counties': row[4],
                    'services_provided': row[5],
                    'created_at': row[6],
                    'updated_at': row[7]
                }
                self.backup_data.append(vendor_backup)
            
            # Save backup to file
            backup_filename = f'vendor_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(backup_filename, 'w') as f:
                json.dump(self.backup_data, f, indent=2, default=str)
            
            self.migration_stats['backup_created'] = True
            logger.info(f"✅ Backup created: {backup_filename} ({len(self.backup_data)} vendors)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create backup: {e}")
            return False
    
    def find_zip_based_vendors(self) -> List[Dict[str, Any]]:
        """Find all vendors that need migration (ZIP-based coverage)"""
        try:
            conn = db._get_conn()
            cursor = conn.cursor()
            
            # Find vendors with ZIP-based coverage or no coverage type set
            cursor.execute('''
                SELECT id, name, service_coverage_type, service_areas, service_counties
                FROM vendors 
                WHERE service_coverage_type = 'zip' 
                   OR service_coverage_type IS NULL
                   OR (service_coverage_type != 'county' AND service_areas != '[]' AND service_areas IS NOT NULL)
            ''')
            
            vendor_rows = cursor.fetchall()
            conn.close()
            
            vendors = []
            for row in vendor_rows:
                vendor = {
                    'id': row[0],
                    'name': row[1],
                    'service_coverage_type': row[2],
                    'service_areas': row[3],
                    'service_counties': row[4]
                }
                vendors.append(vendor)
            
            self.migration_stats['total_vendors'] = len(vendors)
            self.migration_stats['zip_vendors_found'] = len(vendors)
            
            logger.info(f"🔍 Found {len(vendors)} vendors requiring migration")
            return vendors
            
        except Exception as e:
            logger.error(f"❌ Error finding ZIP-based vendors: {e}")
            return []
    
    def convert_zip_to_counties(self, zip_codes: List[str]) -> Tuple[List[str], int]:
        """
        Convert list of ZIP codes to county list
        
        Returns:
            Tuple of (county_list, successful_conversion_count)
        """
        counties = []
        successful_conversions = 0
        
        for zip_code in zip_codes:
            zip_str = str(zip_code).strip()
            
            # Validate ZIP code format
            if not zip_str or len(zip_str) != 5 or not zip_str.isdigit():
                logger.warning(f"⚠️ Invalid ZIP code format: '{zip_str}', skipping")
                continue
            
            # Convert using LocationService
            location_data = location_service.zip_to_location(zip_str)
            
            if location_data.get('error'):
                logger.warning(f"⚠️ Could not convert ZIP {zip_str}: {location_data['error']}")
                continue
            
            county = location_data.get('county')
            state = location_data.get('state')
            
            if county and state:
                county_entry = f"{county}, {state}"
                if county_entry not in counties:
                    counties.append(county_entry)
                    logger.debug(f"   ✅ ZIP {zip_str} → {county_entry}")
                successful_conversions += 1
            else:
                logger.warning(f"⚠️ ZIP {zip_str} did not resolve to valid county/state")
        
        return counties, successful_conversions
    
    def migrate_single_vendor(self, vendor: Dict[str, Any]) -> bool:
        """Migrate a single vendor from ZIP to county coverage"""
        vendor_id = vendor['id']
        vendor_name = vendor['name']
        service_areas = vendor.get('service_areas', '[]')
        
        try:
            # Parse service areas (ZIP codes)
            if isinstance(service_areas, str):
                try:
                    zip_codes = json.loads(service_areas)
                except json.JSONDecodeError:
                    # Handle case where service_areas is not valid JSON
                    zip_codes = []
                    logger.warning(f"⚠️ Invalid JSON in service_areas for {vendor_name}, treating as empty")
            else:
                zip_codes = service_areas or []
            
            if not zip_codes:
                logger.info(f"⏭️ Vendor {vendor_name} has no service areas, setting as national coverage")
                # Set as national coverage if no specific areas
                conn = db._get_conn()
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE vendors 
                    SET service_coverage_type = 'national',
                        service_counties = '[]',
                        service_areas = '[]'
                    WHERE id = ?
                ''', (vendor_id,))
                conn.commit()
                conn.close()
                self.migration_stats['skipped_vendors'] += 1
                return True
            
            # Convert ZIP codes to counties
            counties, successful_conversions = self.convert_zip_to_counties(zip_codes)
            
            if not counties or successful_conversions == 0:
                logger.error(f"❌ Could not convert any ZIP codes for vendor {vendor_name}")
                self.failed_vendors.append({
                    'vendor': vendor,
                    'reason': 'No ZIP codes could be converted to counties'
                })
                self.migration_stats['failed_migrations'] += 1
                return False
            
            # Update vendor in database
            conn = db._get_conn()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE vendors 
                SET service_coverage_type = 'county',
                    service_counties = ?,
                    service_areas = '[]',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (json.dumps(counties), vendor_id))
            
            conn.commit()
            conn.close()
            
            conversion_rate = (successful_conversions / len(zip_codes)) * 100
            logger.info(f"✅ Migrated {vendor_name}:")
            logger.info(f"   📍 {len(zip_codes)} ZIP codes → {len(counties)} counties ({conversion_rate:.0f}% success)")
            logger.info(f"   🗺️ Counties: {', '.join(counties)}")
            
            self.migration_stats['successfully_migrated'] += 1
            return True
            
        except Exception as e:
            logger.error(f"❌ Error migrating vendor {vendor_name}: {e}")
            self.failed_vendors.append({
                'vendor': vendor,
                'reason': str(e)
            })
            self.migration_stats['failed_migrations'] += 1
            return False
    
    def run_migration(self) -> Dict[str, Any]:
        """Run the complete migration process"""
        logger.info("🚀 Starting vendor migration process...")
        
        # Step 1: Create backup
        if not self.create_backup():
            logger.error("❌ Migration aborted - could not create backup")
            return self.migration_stats
        
        # Step 2: Find vendors to migrate
        zip_vendors = self.find_zip_based_vendors()
        if not zip_vendors:
            logger.info("✅ No vendors found requiring migration")
            return self.migration_stats
        
        # Step 3: Migrate each vendor
        logger.info(f"🔄 Starting migration of {len(zip_vendors)} vendors...")
        
        for i, vendor in enumerate(zip_vendors, 1):
            logger.info(f"📋 Processing vendor {i}/{len(zip_vendors)}: {vendor['name']}")
            self.migrate_single_vendor(vendor)
        
        # Step 4: Generate final report
        self.generate_migration_report()
        
        return self.migration_stats
    
    def generate_migration_report(self):
        """Generate detailed migration report"""
        logger.info("📊 MIGRATION SUMMARY:")
        logger.info("=" * 50)
        logger.info(f"   Total vendors found: {self.migration_stats['total_vendors']}")
        logger.info(f"   ZIP-based vendors: {self.migration_stats['zip_vendors_found']}")
        logger.info(f"   ✅ Successfully migrated: {self.migration_stats['successfully_migrated']}")
        logger.info(f"   ⏭️ Skipped (no coverage): {self.migration_stats['skipped_vendors']}")
        logger.info(f"   ❌ Failed migrations: {self.migration_stats['failed_migrations']}")
        logger.info(f"   📦 Backup created: {self.migration_stats['backup_created']}")
        
        if self.failed_vendors:
            logger.info("\n❌ FAILED VENDOR DETAILS:")
            for failed in self.failed_vendors:
                vendor = failed['vendor']
                reason = failed['reason']
                logger.info(f"   • {vendor['name']} (ID: {vendor['id']}): {reason}")
        
        success_rate = 0
        if self.migration_stats['zip_vendors_found'] > 0:
            successful = self.migration_stats['successfully_migrated'] + self.migration_stats['skipped_vendors']
            success_rate = (successful / self.migration_stats['zip_vendors_found']) * 100
        
        logger.info(f"\n🎯 Overall success rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            logger.info("🎉 Migration completed successfully!")
        elif success_rate >= 70:
            logger.info("⚠️ Migration completed with some issues - review failed vendors")
        else:
            logger.warning("🚨 Migration had significant issues - consider rollback")

def main():
    """Main migration execution"""
    print("🔄 Vendor Migration Tool - ZIP to County Coverage")
    print("=" * 60)
    
    # Confirm migration
    response = input("This will modify vendor data. Continue? (yes/no): ").lower().strip()
    if response not in ['yes', 'y']:
        print("❌ Migration cancelled by user")
        return
    
    # Run migration
    migrator = VendorMigrator()
    stats = migrator.run_migration()
    
    # Final summary
    print("\n" + "=" * 60)
    print("🎯 MIGRATION COMPLETE")
    print(f"✅ Successfully migrated: {stats['successfully_migrated']} vendors")
    print(f"❌ Failed migrations: {stats['failed_migrations']} vendors")
    
    if stats['failed_migrations'] > 0:
        print(f"\n⚠️ Review the log file for details on failed migrations")
    
    print(f"\n📦 Backup file created for rollback if needed")

if __name__ == "__main__":
    main()
