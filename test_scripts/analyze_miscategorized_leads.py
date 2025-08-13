#!/usr/bin/env python3
"""
Script to analyze miscategorized leads and show what needs to be fixed
This version doesn't require GHL API access - just analyzes the database
"""

import json
import sqlite3
import logging
import sys
from typing import Dict, List, Any
from collections import defaultdict

# Add project path
sys.path.append("/root/Lead-Router-Pro")

from comprehensive_service_mappings import (
    DOCKSIDE_PROS_SERVICE_CATEGORIES,
    validate_form_identifier
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LeadAnalyzer:
    def __init__(self):
        self.db_path = "smart_lead_router.db"
        
    def get_miscategorized_leads(self) -> List[Dict[str, Any]]:
        """Get all leads that were incorrectly categorized as Boater Resources"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = """
        SELECT 
            id, ghl_contact_id, primary_service_category, 
            specific_service_requested, source, service_details, 
            service_zip_code, customer_name, customer_email,
            vendor_id, status, created_at
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
                'needs_update': False,
                'extraction_method': None
            }
            
            # Method 1: Check form_source for direct mapping
            form_source = service_details.get('form_source', '').replace(' (DSP)', '')
            if form_source:
                correct_category = validate_form_identifier(form_source)
                if correct_category and correct_category != 'Boater Resources':
                    result['correct_category'] = correct_category
                    result['form_source'] = form_source
                    result['needs_update'] = True
                    result['extraction_method'] = 'form_source'
            
            # Method 2: Check GHL custom fields (for bulk assignments)
            if not result['correct_category'] and 'customFields' in service_details:
                for field in service_details.get('customFields', []):
                    # Look for service category field (O84LyhN1QjZ8Zz5mteCM)
                    if field.get('id') == 'O84LyhN1QjZ8Zz5mteCM':
                        category_value = field.get('value', '')
                        if category_value and category_value != 'Boater Resources':
                            result['correct_category'] = category_value
                            result['needs_update'] = True
                            result['extraction_method'] = 'custom_field'
                    
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
            return {'needs_update': False, 'extraction_method': 'parse_error'}
    
    def analyze_all_leads(self):
        """Analyze all miscategorized leads and generate report"""
        leads = self.get_miscategorized_leads()
        
        # Statistics
        stats = {
            'total_leads': len(leads),
            'fixable_leads': 0,
            'unfixable_leads': 0,
            'by_category': defaultdict(int),
            'by_extraction_method': defaultdict(int),
            'missing_zip': 0,
            'has_vendor': 0
        }
        
        fixable_leads = []
        unfixable_leads = []
        
        print(f"\n{'=' * 80}")
        print(f"ANALYZING {len(leads)} MISCATEGORIZED LEADS")
        print(f"{'=' * 80}\n")
        
        for i, lead in enumerate(leads, 1):
            print(f"[{i:3d}/{len(leads)}] {lead['customer_name']} ({lead['customer_email']})")
            print(f"         Lead ID: {lead['id']}")
            print(f"         Source: {lead['source']}")
            print(f"         Created: {lead['created_at']}")
            
            # Extract correct data
            extracted = self.extract_correct_data(lead)
            
            if extracted['needs_update']:
                print(f"    ✅   Correct category: {extracted['correct_category']}")
                print(f"         Specific service: {extracted['specific_service']}")
                print(f"         ZIP code: {extracted['zip_code']}")
                print(f"         Method: {extracted['extraction_method']}")
                
                stats['fixable_leads'] += 1
                stats['by_category'][extracted['correct_category']] += 1
                stats['by_extraction_method'][extracted['extraction_method']] += 1
                
                if not extracted['zip_code']:
                    stats['missing_zip'] += 1
                    print(f"    ⚠️    Missing ZIP code - cannot route to vendor")
                
                if lead.get('vendor_id'):
                    stats['has_vendor'] += 1
                    print(f"    ℹ️    Already has vendor: {lead['vendor_id']}")
                
                fixable_leads.append({
                    'lead': lead,
                    'extracted': extracted
                })
            else:
                print(f"    ❌   Cannot determine correct category")
                print(f"         Method: {extracted.get('extraction_method', 'unknown')}")
                stats['unfixable_leads'] += 1
                unfixable_leads.append(lead)
            
            print()
        
        # Generate summary report
        print(f"\n{'=' * 80}")
        print(f"SUMMARY REPORT")
        print(f"{'=' * 80}")
        print(f"Total leads analyzed: {stats['total_leads']}")
        print(f"✅ Fixable leads: {stats['fixable_leads']} ({stats['fixable_leads']/stats['total_leads']*100:.1f}%)")
        print(f"❌ Unfixable leads: {stats['unfixable_leads']} ({stats['unfixable_leads']/stats['total_leads']*100:.1f}%)")
        print(f"⚠️  Missing ZIP codes: {stats['missing_zip']}")
        print(f"ℹ️  Already have vendors: {stats['has_vendor']}")
        
        print(f"\nCorrect categories found:")
        for category, count in sorted(stats['by_category'].items()):
            print(f"  {category}: {count}")
        
        print(f"\nExtraction methods:")
        for method, count in stats['by_extraction_method'].items():
            print(f"  {method}: {count}")
        
        # Show sample of fixable leads
        if fixable_leads:
            print(f"\nSample of fixable leads (first 5):")
            for item in fixable_leads[:5]:
                lead = item['lead']
                extracted = item['extracted']
                print(f"  • {lead['customer_name']} → {extracted['correct_category']}")
        
        # Show unfixable leads
        if unfixable_leads:
            print(f"\nUnfixable leads (need manual review):")
            for lead in unfixable_leads[:10]:  # Show first 10
                print(f"  • {lead['customer_name']} ({lead['id']}) - {lead['source']}")
        
        print(f"\n{'=' * 80}")
        print(f"RECOMMENDATIONS:")
        print(f"1. Update comprehensive mappings and run fix script")
        print(f"2. {stats['fixable_leads']} leads can be automatically fixed")
        print(f"3. {stats['unfixable_leads']} leads need manual review")
        print(f"4. {stats['missing_zip']} leads missing ZIP codes - update forms")
        print(f"{'=' * 80}\n")

def main():
    """Main entry point"""
    analyzer = LeadAnalyzer()
    analyzer.analyze_all_leads()

if __name__ == "__main__":
    main()