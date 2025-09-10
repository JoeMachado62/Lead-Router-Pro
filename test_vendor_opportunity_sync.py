#!/usr/bin/env python3
"""
Diagnostic and Fix Script for Vendor Assignment to GoHighLevel Opportunities
This script identifies leads with vendor assignments in the database but missing
assignedTo field in GHL opportunities, then fixes them.
"""

import os
import sys
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import AppConfig
from api.services.ghl_api_v2_optimized import OptimizedGoHighLevelAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VendorOpportunitySyncFixer:
    def __init__(self):
        self.db_path = 'smart_lead_router.db'
        self.ghl_api = OptimizedGoHighLevelAPI(
            private_token=AppConfig.GHL_PRIVATE_TOKEN,
            location_id=AppConfig.GHL_LOCATION_ID,
            agency_api_key=AppConfig.GHL_AGENCY_API_KEY
        )
        
    def get_mismatched_assignments(self) -> List[Dict]:
        """Find leads with vendor assignments but potentially missing GHL opportunity assignments"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get leads with vendors and opportunities from last 7 days
        query = """
            SELECT 
                l.id as lead_id,
                l.customer_name,
                l.ghl_opportunity_id,
                l.vendor_id,
                v.company_name,
                v.ghl_user_id,
                l.created_at
            FROM leads l
            INNER JOIN vendors v ON l.vendor_id = v.id
            WHERE l.vendor_id IS NOT NULL 
            AND l.ghl_opportunity_id IS NOT NULL
            AND v.ghl_user_id IS NOT NULL
            AND l.created_at > datetime('now', '-7 days')
            ORDER BY l.created_at DESC
        """
        
        cursor.execute(query)
        results = []
        
        for row in cursor.fetchall():
            results.append({
                'lead_id': row[0],
                'customer_name': row[1],
                'opportunity_id': row[2],
                'vendor_id': row[3],
                'vendor_company': row[4],
                'vendor_ghl_user_id': row[5],
                'created_at': row[6]
            })
        
        conn.close()
        return results
    
    def check_opportunity_assignment(self, opportunity_id: str) -> Optional[str]:
        """Check if an opportunity is assigned to a user in GHL"""
        try:
            opportunity = self.ghl_api.get_opportunity_by_id(opportunity_id)
            if opportunity:
                assigned_to = opportunity.get('assignedTo')
                return assigned_to
            return None
        except Exception as e:
            logger.error(f"Error checking opportunity {opportunity_id}: {e}")
            return None
    
    def fix_opportunity_assignment(self, opportunity_id: str, vendor_ghl_user_id: str) -> bool:
        """Fix opportunity assignment in GHL"""
        try:
            logger.info(f"🔧 Fixing opportunity {opportunity_id} - assigning to {vendor_ghl_user_id}")
            
            update_data = {
                'assignedTo': vendor_ghl_user_id,
                'pipelineId': AppConfig.PIPELINE_ID,
                'pipelineStageId': AppConfig.NEW_LEAD_STAGE_ID
            }
            
            success = self.ghl_api.update_opportunity(opportunity_id, update_data)
            
            if success:
                logger.info(f"✅ Successfully assigned opportunity {opportunity_id} to vendor")
                return True
            else:
                logger.error(f"❌ Failed to assign opportunity {opportunity_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error fixing opportunity {opportunity_id}: {e}")
            return False
    
    def run_diagnostic_and_fix(self):
        """Run the diagnostic and fix process"""
        logger.info("=" * 80)
        logger.info("VENDOR OPPORTUNITY SYNC DIAGNOSTIC & FIX")
        logger.info("=" * 80)
        
        # Get potentially mismatched assignments
        assignments = self.get_mismatched_assignments()
        logger.info(f"Found {len(assignments)} leads with vendor assignments to check")
        
        issues_found = 0
        issues_fixed = 0
        already_correct = 0
        
        for assignment in assignments:
            lead_id = assignment['lead_id'][:8]
            customer = assignment['customer_name'][:30] if assignment['customer_name'] else 'Unknown'
            opp_id = assignment['opportunity_id']
            vendor = assignment['vendor_company']
            vendor_ghl_user = assignment['vendor_ghl_user_id']
            
            logger.info(f"\n📋 Checking Lead {lead_id} - {customer}")
            logger.info(f"   Vendor: {vendor} (GHL User: {vendor_ghl_user})")
            logger.info(f"   Opportunity: {opp_id}")
            
            # Check current assignment in GHL
            current_assigned = self.check_opportunity_assignment(opp_id)
            
            if current_assigned is None:
                logger.warning(f"   ⚠️  Opportunity not found in GHL or error occurred")
                continue
            
            if current_assigned == vendor_ghl_user:
                logger.info(f"   ✅ Already correctly assigned")
                already_correct += 1
            elif current_assigned == "":
                logger.warning(f"   ❌ NOT ASSIGNED in GHL - Fixing...")
                issues_found += 1
                
                if self.fix_opportunity_assignment(opp_id, vendor_ghl_user):
                    issues_fixed += 1
                    logger.info(f"   ✅ FIXED - Assigned to {vendor}")
                else:
                    logger.error(f"   ❌ FAILED to fix assignment")
            else:
                logger.warning(f"   ⚠️  Assigned to different user: {current_assigned} (expected: {vendor_ghl_user})")
                issues_found += 1
                # Could add logic here to reassign if needed
        
        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total leads checked: {len(assignments)}")
        logger.info(f"Already correctly assigned: {already_correct}")
        logger.info(f"Issues found: {issues_found}")
        logger.info(f"Issues fixed: {issues_fixed}")
        
        if issues_found > issues_fixed:
            logger.warning(f"⚠️  {issues_found - issues_fixed} issues could not be fixed")
        
        return {
            'total_checked': len(assignments),
            'already_correct': already_correct,
            'issues_found': issues_found,
            'issues_fixed': issues_fixed
        }

def main():
    """Main execution"""
    try:
        fixer = VendorOpportunitySyncFixer()
        results = fixer.run_diagnostic_and_fix()
        
        # Return exit code based on results
        if results['issues_found'] > results['issues_fixed']:
            sys.exit(1)  # Some issues remain
        else:
            sys.exit(0)  # All good
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()