#!/usr/bin/env python3
"""
Script to restore lead data from GoHighLevel without overwriting good data
This will sync ALL leads and preserve existing data while filling in missing fields
"""

import logging
import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.services.ghl_api import GoHighLevelAPI
from api.services.location_service import location_service
from config import AppConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LeadDataRestorer:
    def __init__(self):
        self.ghl_api = GoHighLevelAPI(
            location_id=AppConfig.GHL_LOCATION_ID,
            location_api_key=AppConfig.GHL_LOCATION_API_KEY if hasattr(AppConfig, 'GHL_LOCATION_API_KEY') else None,
            private_token=AppConfig.GHL_PRIVATE_TOKEN
        )
        self.db_path = 'smart_lead_router.db'
        
        # Map GHL custom field IDs to database columns
        self.field_mapping = {
            'FT85QGi0tBq1AfVGNJ9v': 'specific_service_requested',  # Specific Service Needed
            'HRqfv0HnUydNRLKWhk27': 'primary_service_category',    # Primary Service Category (CORRECTED)
            'y3Xo7qsFEQumoFugTeCq': 'customer_zip_code',           # Zip Code of Service
            # Add more as needed
        }
        
    def get_all_ghl_contacts(self) -> List[Dict[str, Any]]:
        """Fetch ALL contacts from GHL, not just unassigned"""
        try:
            logger.info("🔄 Fetching ALL contacts from GoHighLevel...")
            
            # Use the search_contacts method which returns a list
            contacts = self.ghl_api.search_contacts(query="")  # Empty query gets all
            
            if isinstance(contacts, list):
                logger.info(f"✅ Found {len(contacts)} total contacts in GHL")
                return contacts
            else:
                logger.error(f"Unexpected response format: {type(contacts)}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching GHL contacts: {e}")
            return []
    
    def extract_lead_data_from_contact(self, contact: Dict[str, Any]) -> Dict[str, Any]:
        """Extract lead data from GHL contact, including custom fields"""
        lead_data = {
            'ghl_contact_id': contact.get('id'),
            'customer_name': f"{contact.get('firstName', '')} {contact.get('lastName', '')}".strip(),
            'customer_email': contact.get('email', ''),
            'customer_phone': contact.get('phone', ''),
            'customer_zip_code': contact.get('postalCode', ''),
        }
        
        # Extract custom fields
        custom_fields = contact.get('customFields', {})
        
        # Handle custom fields as either dict or list
        if isinstance(custom_fields, dict):
            for field_id, field_value in custom_fields.items():
                if field_id in self.field_mapping and field_value:
                    db_column = self.field_mapping[field_id]
                    lead_data[db_column] = field_value
        elif isinstance(custom_fields, list):
            for field in custom_fields:
                if isinstance(field, dict):
                    field_id = field.get('id')
                    field_value = field.get('value', '')
                    if field_id in self.field_mapping and field_value:
                        db_column = self.field_mapping[field_id]
                        lead_data[db_column] = field_value
        
        # Process ZIP to get county/state if we have a ZIP
        if lead_data.get('customer_zip_code'):
            zip_code = str(lead_data['customer_zip_code'])  # Convert to string in case it's int
            if len(zip_code) == 5 and zip_code.isdigit():
                location_data = location_service.zip_to_location(zip_code)
                if not location_data.get('error'):
                    county = location_data.get('county', '')
                    state = location_data.get('state', '')
                    if county and state:
                        lead_data['service_county'] = f"{county}, {state}"
                        lead_data['service_state'] = state
        
        # Smart service category detection
        if not lead_data.get('primary_service_category') or lead_data.get('primary_service_category') == 'Boater Resources':
            # Try to derive from specific service
            specific_service = lead_data.get('specific_service_requested', '')
            if specific_service:
                lead_data['primary_service_category'] = self.derive_category_from_service(specific_service)
        
        return lead_data
    
    def derive_category_from_service(self, specific_service: str) -> str:
        """Derive service category from specific service text"""
        service_lower = specific_service.lower()
        
        # Service category mappings
        category_mappings = {
            'ac': 'Marine Systems',
            'air conditioning': 'Marine Systems',
            'hvac': 'Marine Systems',
            'heating': 'Marine Systems',
            'cooling': 'Marine Systems',
            'engine': 'Engines and Generators',
            'generator': 'Engines and Generators',
            'motor': 'Engines and Generators',
            'electrical': 'Marine Electrical',
            'wiring': 'Marine Electrical',
            'battery': 'Marine Electrical',
            'electronics': 'Marine Electronics',
            'navigation': 'Marine Electronics',
            'radar': 'Marine Electronics',
            'gps': 'Marine Electronics',
            'fiberglass': 'Boat and Yacht Repair',
            'hull': 'Boat and Yacht Repair',
            'paint': 'Boat and Yacht Repair',
            'canvas': 'Marine Canvas and Upholstery',
            'upholstery': 'Marine Canvas and Upholstery',
            'cushion': 'Marine Canvas and Upholstery',
            'dock': 'Docks, Seawalls and Lifts',
            'lift': 'Docks, Seawalls and Lifts',
            'seawall': 'Docks, Seawalls and Lifts',
            'tow': 'Boat Towing',
            'salvage': 'Boat Towing',
            'haul': 'Boat Hauling and Yacht Delivery',
            'transport': 'Boat Hauling and Yacht Delivery',
            'delivery': 'Boat Hauling and Yacht Delivery',
        }
        
        for keyword, category in category_mappings.items():
            if keyword in service_lower:
                logger.info(f"🎯 Derived category '{category}' from service '{specific_service}'")
                return category
        
        # Don't default to Boater Resources if we can't determine
        return ''
    
    def update_lead_smart(self, lead_data: Dict[str, Any]) -> bool:
        """Update lead in database WITHOUT overwriting existing good data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # First, get existing lead data
            cursor.execute('''
                SELECT id, primary_service_category, specific_service_requested,
                       customer_zip_code, service_county, service_state, source,
                       customer_name, customer_email, customer_phone
                FROM leads WHERE ghl_contact_id = ?
            ''', (lead_data['ghl_contact_id'],))
            
            existing = cursor.fetchone()
            
            if existing:
                lead_id = existing[0]
                
                # Build update query only for fields that need updating
                updates = []
                params = []
                
                # Only update if new value is better than existing
                if lead_data.get('primary_service_category') and (not existing[1] or existing[1] == 'Boater Resources'):
                    updates.append('primary_service_category = ?')
                    params.append(lead_data['primary_service_category'])
                
                if lead_data.get('specific_service_requested') and not existing[2]:
                    updates.append('specific_service_requested = ?')
                    params.append(lead_data['specific_service_requested'])
                
                if lead_data.get('customer_zip_code') and not existing[3]:
                    updates.append('customer_zip_code = ?')
                    params.append(lead_data['customer_zip_code'])
                
                if lead_data.get('service_county') and not existing[4]:
                    updates.append('service_county = ?')
                    params.append(lead_data['service_county'])
                
                if lead_data.get('service_state') and not existing[5]:
                    updates.append('service_state = ?')
                    params.append(lead_data['service_state'])
                
                # NEVER overwrite source field - preserve original
                # NEVER overwrite created_at
                
                if updates:
                    updates.append('updated_at = CURRENT_TIMESTAMP')
                    params.append(lead_id)
                    
                    query = f"UPDATE leads SET {', '.join(updates)} WHERE id = ?"
                    cursor.execute(query, params)
                    conn.commit()
                    
                    logger.info(f"✅ Updated lead {lead_id} with {len(updates)-1} fields from GHL")
                else:
                    logger.info(f"⏭️ Lead {lead_id} already has complete data, skipping")
                
                conn.close()
                return True
            else:
                logger.info(f"🆕 Lead not found for GHL contact {lead_data['ghl_contact_id']}, skipping creation")
                conn.close()
                return False
                
        except Exception as e:
            logger.error(f"Error updating lead: {e}")
            if conn:
                conn.close()
            return False
    
    def restore_all_leads(self):
        """Main restoration process"""
        logger.info("="*60)
        logger.info("LEAD DATA RESTORATION FROM GOHIGHLEVEL")
        logger.info("="*60)
        
        # Get all contacts from GHL
        contacts = self.get_all_ghl_contacts()
        
        if not contacts:
            logger.error("No contacts found in GHL")
            return
        
        # Process each contact
        updated = 0
        skipped = 0
        errors = 0
        
        for i, contact in enumerate(contacts, 1):
            try:
                # Check if this contact could be a lead
                # Instead of requiring specific fields, check if it has basic lead info
                contact_id = contact.get('id')
                email = contact.get('email', '')
                
                # Skip if no email or contact ID
                if not contact_id or not email:
                    skipped += 1
                    continue
                
                # Check if this contact exists in our leads table
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM leads WHERE ghl_contact_id = ?', (contact_id,))
                exists = cursor.fetchone()[0] > 0
                conn.close()
                
                if not exists:
                    # Not in our leads table, skip
                    skipped += 1
                    continue
                
                # Extract lead data
                lead_data = self.extract_lead_data_from_contact(contact)
                
                # Update database (smart update - won't overwrite good data)
                if self.update_lead_smart(lead_data):
                    updated += 1
                else:
                    skipped += 1
                
                # Progress indicator
                if i % 10 == 0:
                    logger.info(f"Progress: {i}/{len(contacts)} contacts processed")
                    
            except Exception as e:
                logger.error(f"Error processing contact {contact.get('id')}: {e}")
                errors += 1
        
        # Summary
        logger.info("="*60)
        logger.info("RESTORATION COMPLETE")
        logger.info(f"✅ Updated: {updated} leads")
        logger.info(f"⏭️ Skipped: {skipped} contacts")
        logger.info(f"❌ Errors: {errors}")
        logger.info("="*60)

def main():
    """Run the restoration process"""
    restorer = LeadDataRestorer()
    restorer.restore_all_leads()

if __name__ == "__main__":
    main()