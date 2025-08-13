#!/usr/bin/env python3
"""
Script to fix miscategorized leads by:
1. Extracting correct data from service_details
2. Updating local database with correct category
3. Updating GHL contacts with correct custom fields
4. Running leads through reassignment process
"""

import json
import sqlite3
import logging
import sys
import time
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add project path
sys.path.append("/root/Lead-Router-Pro")

from config import AppConfig
from api.services.ghl_api import GoHighLevelAPI
from api.services.field_mapper import field_mapper
from api.services.lead_routing_service import lead_routing_service
from api.services.location_service import location_service
from comprehensive_service_mappings import (
    DOCKSIDE_PROS_SERVICE_CATEGORIES,
    validate_form_identifier
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LeadFixer:
    def __init__(self):
        self.db_path = "smart_lead_router.db"
        self.ghl_api = GoHighLevelAPI(
            location_id=AppConfig.GHL_LOCATION_ID,
            location_api_key=AppConfig.GHL_LOCATION_API if hasattr(AppConfig, 'GHL_LOCATION_API') else None,
            private_token=AppConfig.GHL_PRIVATE_TOKEN if AppConfig.GHL_PRIVATE_TOKEN else None
        )
        self.fixed_count = 0
        self.error_count = 0
        self.reassigned_count = 0
        
    def get_miscategorized_leads(self) -> List[Dict[str, Any]]:
        """Get all leads that were incorrectly categorized as Boater Resources"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = """
        SELECT 
            id, ghl_contact_id, ghl_opportunity_id, 
            primary_service_category, specific_service_requested,
            source, service_details, service_zip_code,
            customer_name, customer_email, customer_phone,
            vendor_id, status
        FROM leads 
        WHERE primary_service_category = 'Boater Resources'
        AND service_details IS NOT NULL
        ORDER BY created_at DESC
        """
        
        cursor.execute(query)
        leads = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        logger.info(f"Found {len(leads)} leads categorized as 'Boater Resources'")
        return leads
    
    def extract_correct_data(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """Extract correct service category and specific service from service_details"""
        try:
            service_details = json.loads(lead['service_details'])
            
            # Initialize result
            result = {
                'correct_category': None,
                'specific_service': None,
                'form_source': None,
                'zip_code': None,
                'needs_update': False
            }
            
            # Method 1: Check form_source for direct mapping
            form_source = service_details.get('form_source', '').replace(' (DSP)', '')
            if form_source:
                correct_category = validate_form_identifier(form_source)
                if correct_category and correct_category != 'Boater Resources':
                    result['correct_category'] = correct_category
                    result['form_source'] = form_source
                    result['needs_update'] = True
                    logger.info(f"✅ Found category from form_source: {form_source} → {correct_category}")
            
            # Method 2: Check GHL custom fields (for bulk assignments)
            if not result['correct_category'] and 'customFields' in service_details:
                for field in service_details.get('customFields', []):
                    # Look for service category field (O84LyhN1QjZ8Zz5mteCM)
                    if field.get('id') == 'O84LyhN1QjZ8Zz5mteCM':
                        category_value = field.get('value', '')
                        if category_value and category_value != 'Boater Resources':
                            result['correct_category'] = category_value
                            result['needs_update'] = True
                            logger.info(f"✅ Found category from custom field: {category_value}")
                    
                    # Look for specific service field (FT85QGi0tBq1AfVGNJ9v)
                    elif field.get('id') == 'FT85QGi0tBq1AfVGNJ9v':
                        result['specific_service'] = field.get('value', '')
                    
                    # Look for ZIP code field (y3Xo7qsFEQumoFugTeCq)
                    elif field.get('id') == 'y3Xo7qsFEQumoFugTeCq':
                        result['zip_code'] = str(field.get('value', ''))
            
            # Method 3: Check specific_service_needed field
            if not result['specific_service']:
                result['specific_service'] = service_details.get('specific_service_needed', '')
            
            # Method 4: Check zip_code_of_service
            if not result['zip_code']:
                result['zip_code'] = service_details.get('zip_code_of_service', '')
            
            # If still no ZIP, check the lead record
            if not result['zip_code'] and lead.get('service_zip_code'):
                result['zip_code'] = lead['service_zip_code']
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing service_details for lead {lead['id']}: {e}")
            return {'needs_update': False}
    
    def update_lead_in_database(self, lead_id: str, correct_category: str, specific_service: str) -> bool:
        """Update lead in local database with correct category"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = """
            UPDATE leads 
            SET primary_service_category = ?,
                specific_service_requested = ?,
                updated_at = ?
            WHERE id = ?
            """
            
            cursor.execute(query, (
                correct_category,
                specific_service or '',
                datetime.utcnow().isoformat(),
                lead_id
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Updated lead {lead_id} in database: {correct_category}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating lead {lead_id} in database: {e}")
            return False
    
    async def update_ghl_contact(self, contact_id: str, category: str, specific_service: str) -> bool:
        """Update GHL contact with correct custom fields"""
        try:
            # Get field IDs from field mapper
            category_field = field_mapper.get_ghl_field_details("primary_service_category")
            service_field = field_mapper.get_ghl_field_details("specific_service_requested")
            
            if not category_field or not service_field:
                logger.error(f"Could not find GHL field mappings for contact {contact_id}")
                return False
            
            # Prepare update data
            update_data = {
                'customFields': [
                    {
                        'id': category_field['id'],
                        'value': category
                    },
                    {
                        'id': service_field['id'],
                        'value': specific_service or ''
                    }
                ]
            }
            
            # Update contact
            result = self.ghl_api.update_contact(contact_id, update_data)
            
            if result.get('success'):
                logger.info(f"✅ Updated GHL contact {contact_id}: {category}")
                return True
            else:
                logger.error(f"Failed to update GHL contact {contact_id}: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating GHL contact {contact_id}: {e}")
            return False
    
    async def reassign_lead(self, lead: Dict[str, Any], category: str, zip_code: str) -> bool:
        """Run lead through reassignment process to find matching vendor"""
        try:
            if not zip_code:
                logger.warning(f"Cannot reassign lead {lead['id']} - no ZIP code")
                return False
            
            if lead.get('vendor_id'):
                logger.info(f"Lead {lead['id']} already has vendor {lead['vendor_id']}")
                return False
            
            # Use routing service to find vendor
            routing_result = lead_routing_service.route_lead_to_vendor(
                service_category=category,
                specific_service=lead.get('specific_service_requested', ''),
                zip_code=zip_code
            )
            
            if routing_result.get('vendor'):
                vendor = routing_result['vendor']
                vendor_id = vendor.get('id')
                
                # Update lead with vendor assignment
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE leads 
                    SET vendor_id = ?,
                        vendor_assigned_at = ?,
                        status = 'assigned',
                        updated_at = ?
                    WHERE id = ?
                """, (
                    vendor_id,
                    datetime.utcnow().isoformat(),
                    datetime.utcnow().isoformat(),
                    lead['id']
                ))
                
                conn.commit()
                conn.close()
                
                # Update GHL contact with vendor info
                if lead.get('ghl_contact_id'):
                    vendor_field = field_mapper.get_ghl_field_details("assigned_vendor")
                    if vendor_field:
                        await self.ghl_api.update_contact(lead['ghl_contact_id'], {
                            'customFields': [{
                                'id': vendor_field['id'],
                                'value': vendor.get('business_name', '')
                            }]
                        })
                
                logger.info(f"✅ Reassigned lead {lead['id']} to vendor {vendor.get('business_name')}")
                return True
            else:
                logger.info(f"No vendor found for lead {lead['id']} in {category} / {zip_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error reassigning lead {lead['id']}: {e}")
            return False
    
    async def fix_all_leads(self, dry_run: bool = False):
        """Main method to fix all miscategorized leads"""
        leads = self.get_miscategorized_leads()
        
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Starting lead fix process (dry_run={dry_run})")
        logger.info(f"Found {len(leads)} leads to process")
        logger.info(f"{'=' * 60}\n")
        
        for i, lead in enumerate(leads, 1):
            logger.info(f"\n[{i}/{len(leads)}] Processing lead {lead['id']}")
            logger.info(f"  Customer: {lead['customer_name']} ({lead['customer_email']})")
            logger.info(f"  Current category: {lead['primary_service_category']}")
            logger.info(f"  Source: {lead['source']}")
            
            # Extract correct data
            extracted = self.extract_correct_data(lead)
            
            if not extracted['needs_update']:
                logger.info(f"  ℹ️  No update needed - keeping as Boater Resources")
                continue
            
            if not extracted['correct_category']:
                logger.warning(f"  ⚠️  Could not determine correct category")
                continue
            
            logger.info(f"  ✅ Correct category: {extracted['correct_category']}")
            logger.info(f"  ✅ Specific service: {extracted['specific_service']}")
            logger.info(f"  ✅ ZIP code: {extracted['zip_code']}")
            
            if dry_run:
                logger.info(f"  🔵 DRY RUN - Would update to: {extracted['correct_category']}")
                continue
            
            # Update local database
            db_updated = self.update_lead_in_database(
                lead['id'],
                extracted['correct_category'],
                extracted['specific_service']
            )
            
            if db_updated:
                self.fixed_count += 1
                
                # Update GHL contact
                if lead.get('ghl_contact_id'):
                    await self.update_ghl_contact(
                        lead['ghl_contact_id'],
                        extracted['correct_category'],
                        extracted['specific_service']
                    )
                
                # Attempt reassignment if no vendor assigned
                if not lead.get('vendor_id') and extracted['zip_code']:
                    reassigned = await self.reassign_lead(
                        lead,
                        extracted['correct_category'],
                        extracted['zip_code']
                    )
                    if reassigned:
                        self.reassigned_count += 1
            else:
                self.error_count += 1
            
            # Rate limiting
            time.sleep(0.5)
        
        # Print summary
        logger.info(f"\n{'=' * 60}")
        logger.info(f"LEAD FIX SUMMARY")
        logger.info(f"{'=' * 60}")
        logger.info(f"Total leads processed: {len(leads)}")
        logger.info(f"✅ Successfully fixed: {self.fixed_count}")
        logger.info(f"🔄 Reassigned to vendors: {self.reassigned_count}")
        logger.info(f"❌ Errors: {self.error_count}")
        logger.info(f"{'=' * 60}\n")

async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix miscategorized leads')
    parser.add_argument('--dry-run', action='store_true', help='Run without making changes')
    parser.add_argument('--limit', type=int, help='Limit number of leads to process')
    args = parser.parse_args()
    
    fixer = LeadFixer()
    await fixer.fix_all_leads(dry_run=args.dry_run)

if __name__ == "__main__":
    asyncio.run(main())