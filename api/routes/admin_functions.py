# api/routes/admin_functions.py

import logging
import json
import uuid
import sys
import os
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import datetime

# Import the proven components used by vendor widget
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from database.simple_connection import db as simple_db_instance
from api.services.ghl_api import GoHighLevelAPI
from api.services.field_mapper import field_mapper
from api.services.location_service import location_service
from config import AppConfig

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/admin", tags=["Admin Functions"])

@router.post("/sync-database")
async def sync_database():
    """
    Enhanced V2 database sync endpoint with bi-directional sync capabilities
    
    This function now:
    1. Fetches ALL contacts from GHL to discover new vendors/leads
    2. Updates existing vendor and lead records with ALL fields from GHL
    3. Creates new local records for GHL contacts not in database
    4. Detects and handles deleted GHL records
    5. Provides comprehensive statistics about the sync operation
    """
    try:
        logger.info("🔄 Database sync initiated from admin dashboard")
        
        # Import the enhanced sync V2 module (bi-directional) from services
        from api.services.enhanced_db_sync_v2 import EnhancedDatabaseSync
        
        # Initialize the sync service
        sync_service = EnhancedDatabaseSync()
        
        # Run the synchronization
        results = sync_service.sync_all()
        
        # Prepare response
        if results['success']:
            logger.info(f"✅ Sync completed: {results['message']}")
            
            return {
                "status": "success",  # Frontend expects 'status' not 'success'
                "success": True,
                "message": results['message'],
                # Frontend expects these at root level
                "vendors": {
                    "checked": results['stats'].get('vendors_checked', 0),
                    "updated": results['stats'].get('vendors_updated', 0),
                    "added": results['stats'].get('vendors_created', 0),  # Frontend expects 'added' not 'created'
                    "deleted": results['stats'].get('vendors_deactivated', 0),  # Using deactivated count
                    "created": results['stats'].get('vendors_created', 0),
                    "deactivated": results['stats'].get('vendors_deactivated', 0)
                },
                "leads": {
                    "checked": results['stats'].get('leads_checked', 0),
                    "updated": results['stats'].get('leads_updated', 0),
                    "added": results['stats'].get('leads_created', 0),  # Frontend expects 'added' not 'created'
                    "deleted": results['stats'].get('leads_deleted', 0),
                    "created": results['stats'].get('leads_created', 0)
                },
                "stats": {
                    "ghl_contacts_fetched": results['stats'].get('ghl_contacts_fetched', 0),
                    "errors": len(results['stats'].get('errors', [])),
                    "duration": results.get('duration', 0)
                },
                "timestamp": datetime.now().isoformat()
            }
        else:
            error_msg = results.get('error', 'Unknown error during sync')
            logger.error(f"❌ Sync failed: {error_msg}")
            
            return {
                "status": "error",  # Frontend expects 'status'
                "success": False,
                "message": f"Sync failed: {error_msg}",
                "vendors": {"updated": 0, "added": 0, "deleted": 0},
                "leads": {"updated": 0, "added": 0, "deleted": 0},
                "stats": results.get('stats', {}),
                "timestamp": datetime.now().isoformat()
            }
            
    except ImportError as e:
        logger.error(f"❌ Failed to import enhanced sync module: {e}")
        return {
            "status": "error",
            "success": False,
            "message": "Enhanced sync module not found. Please ensure enhanced_db_sync_v2.py is in api/services/.",
            "vendors": {"updated": 0, "added": 0, "deleted": 0},
            "leads": {"updated": 0, "added": 0, "deleted": 0},
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Unexpected error during sync: {e}")
        return {
            "status": "error",
            "success": False,
            "message": f"Unexpected error: {str(e)}",
            "vendors": {"updated": 0, "added": 0, "deleted": 0},
            "leads": {"updated": 0, "added": 0, "deleted": 0},
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


async def _sync_vendor_using_widget_logic(contact: Dict[str, Any], account_id: str, 
                                         ghl_user_id: str, vendor_company_name: str,
                                         service_categories: str, services_offered: str, 
                                         service_zip_codes: str) -> str:
    """Sync vendor using exact same logic as vendor widget"""
    try:
        vendor_email = contact.get('email', '')
        if not vendor_email:
            return "skipped"
        
        # Check if vendor exists (same as widget)
        existing_vendor = simple_db_instance.get_vendor_by_email_and_account(vendor_email, account_id)
        
        # Process service categories - EXPERIMENT: assume GHL returns it as array already
        service_categories_json = json.dumps([])
        if service_categories:
            try:
                # If it's already a list/array from GHL, use it directly
                if isinstance(service_categories, list):
                    service_categories_json = json.dumps(service_categories)
                    logger.info(f"📋 EXPERIMENT: Got service_categories as array: {service_categories}")
                # If it's a string that looks like JSON array, parse it
                elif isinstance(service_categories, str) and service_categories.startswith('[') and service_categories.endswith(']'):
                    categories_list = json.loads(service_categories)
                    service_categories_json = json.dumps(categories_list)
                    logger.info(f"📋 EXPERIMENT: Parsed service_categories from JSON string: {categories_list}")
                # If it's a comma-separated string, split it
                elif isinstance(service_categories, str):
                    categories_list = [cat.strip() for cat in service_categories.split(',') if cat.strip()]
                    service_categories_json = json.dumps(categories_list)
                    logger.info(f"📋 EXPERIMENT: Split service_categories from comma string: {categories_list}")
                else:
                    logger.info(f"📋 EXPERIMENT: Unknown service_categories type: {type(service_categories)} = {service_categories}")
                    service_categories_json = json.dumps([str(service_categories)])
            except Exception as e:
                logger.error(f"📋 EXPERIMENT: Error processing service_categories: {e}")
                service_categories_json = json.dumps([str(service_categories)])
        
        # Process services offered (same as widget)
        services_offered_json = json.dumps([])
        if services_offered:
            try:
                if services_offered.startswith('[') and services_offered.endswith(']'):
                    services_list = json.loads(services_offered)
                else:
                    services_list = [srv.strip() for srv in services_offered.split(',') if srv.strip()]
                services_offered_json = json.dumps(services_list)
            except:
                services_offered_json = json.dumps([services_offered])
        
        # Process coverage (same as widget logic)
        coverage_type = 'county'
        coverage_states_json = json.dumps([])
        coverage_counties_json = json.dumps([])
        
        if service_zip_codes:
            # Use same coverage processing as widget
            coverage_result = _process_coverage_like_widget(service_zip_codes)
            coverage_type = coverage_result['type']
            coverage_states_json = coverage_result['states']
            coverage_counties_json = coverage_result['counties']
        
        vendor_name = f"{contact.get('firstName', '')} {contact.get('lastName', '')}".strip()
        vendor_phone = contact.get('phone', '')
        
        # PAUL DEBUG: Check vendor lookup after processing
        if vendor_email == 'Paul.minnucci@allclassdetailing.com':
            logger.info(f"🎯 PAUL VENDOR LOOKUP (after processing):")
            logger.info(f"   vendor_email: {vendor_email}")
            logger.info(f"   account_id: {account_id}")
            logger.info(f"   existing_vendor found: {existing_vendor is not None}")
            if existing_vendor:
                logger.info(f"   existing_vendor ID: {existing_vendor.get('id')}")
                logger.info(f"   existing service_categories: {existing_vendor.get('service_categories')}")
            logger.info(f"   service_categories raw: {service_categories}")
            logger.info(f"   service_categories_json to save: {service_categories_json}")
        
        if existing_vendor:
            # Update existing vendor (same fields as widget creates)
            logger.info(f"🔄 Updating existing vendor: {vendor_email}")
            
            # Update the vendor using direct SQL since we don't have update_vendor method
            vendor_id = existing_vendor['id']
            try:
                import sqlite3
                conn = sqlite3.connect('smart_lead_router.db')
                cursor = conn.cursor()
                
                # Update vendor with synced data from GHL
                cursor.execute("""
                    UPDATE vendors SET 
                        name = ?, 
                        company_name = ?,
                        phone = ?,
                        service_categories = ?,
                        services_offered = ?,
                        coverage_type = ?,
                        coverage_states = ?,
                        coverage_counties = ?,
                        updated_at = datetime('now')
                    WHERE id = ?
                """, (
                    vendor_name,
                    vendor_company_name or '',
                    vendor_phone,
                    service_categories_json,
                    services_offered_json,
                    coverage_type,
                    coverage_states_json,
                    coverage_counties_json,
                    vendor_id
                ))
                
                conn.commit()
                conn.close()
                
                logger.info(f"✅ Updated vendor {vendor_email} with service_categories: {service_categories_json}")
                return "updated"
                
            except Exception as e:
                logger.error(f"❌ Error updating vendor {vendor_email}: {e}")
                return "error"
        else:
            # Create new vendor (same as widget)
            vendor_id = simple_db_instance.create_vendor(
                account_id=account_id,
                name=vendor_name,
                email=vendor_email,
                company_name=vendor_company_name or '',
                phone=vendor_phone,
                ghl_contact_id=contact.get('id'),
                status='active' if ghl_user_id else 'pending',
                service_categories=service_categories_json,
                services_offered=services_offered_json,
                coverage_type=coverage_type,
                coverage_states=coverage_states_json,
                coverage_counties=coverage_counties_json,
                primary_service_category='',
                taking_new_work=True
            )
            logger.info(f"✅ Created vendor: {vendor_email}")
            return "added"
            
    except Exception as e:
        logger.error(f"❌ Error syncing vendor {contact.get('email', 'unknown')}: {e}")
        return "error"


async def _sync_lead_using_widget_logic(contact: Dict[str, Any], account_id: str,
                                       specific_service: str, zip_code_of_service: str,
                                       mapped_payload: Dict[str, Any]) -> str:
    """Sync lead using exact same logic as vendor widget"""
    try:
        customer_email = contact.get('email', '')
        if not customer_email:
            return "skipped"
        
        # Check if lead exists
        existing_lead = simple_db_instance.get_lead_by_email(customer_email)
        
        # Process location (same as widget)
        service_county = ""
        service_state = ""
        
        if zip_code_of_service and len(zip_code_of_service) == 5 and zip_code_of_service.isdigit():
            location_data = location_service.zip_to_location(zip_code_of_service)
            if not location_data.get('error'):
                county = location_data.get('county', '')
                state = location_data.get('state', '')
                if county and state:
                    service_county = f"{county}, {state}"
                    service_state = state
        
        # Build service details from mapped payload (same as widget)
        service_details = {}
        standard_lead_fields = {
            "firstName", "lastName", "email", "phone", "primary_service_category",
            "customer_zip_code", "specific_service_requested"
        }
        
        for field_key, field_value in mapped_payload.items():
            if field_value and field_value != "" and field_key not in standard_lead_fields:
                service_details[field_key] = field_value
        
        customer_name = f"{contact.get('firstName', '')} {contact.get('lastName', '')}".strip()
        
        if existing_lead:
            logger.info(f"🔄 Updating existing lead: {customer_email}")
            return "updated"
        else:
            # Create new lead (same as widget)
            lead_id = simple_db_instance.create_lead(
                account_id=account_id,
                customer_name=customer_name,
                customer_email=customer_email,
                customer_phone=contact.get('phone', ''),
                primary_service_category='General Services',
                specific_service_requested=specific_service,
                customer_zip_code=zip_code_of_service or '',
                service_county=service_county,
                service_state=service_state,
                service_zip_code=zip_code_of_service or '',
                priority='normal',
                source='GHL Sync',
                ghl_contact_id=contact.get('id'),
                service_details_json=json.dumps(service_details),
                status='unassigned'
            )
            logger.info(f"✅ Created lead: {customer_email}")
            return "added"
            
    except Exception as e:
        logger.error(f"❌ Error syncing lead {contact.get('email', 'unknown')}: {e}")
        return "error"


def _process_coverage_like_widget(service_zip_codes: str) -> Dict[str, Any]:
    """Process coverage data using same logic as vendor widget"""
    coverage_type = 'county'
    coverage_states = []
    coverage_counties = []
    
    if not service_zip_codes:
        return {
            'type': coverage_type,
            'states': json.dumps(coverage_states),
            'counties': json.dumps(coverage_counties)
        }
    
    # Handle different formats (same as widget)
    if service_zip_codes.upper() in ['USA', 'UNITED STATES', 'NATIONAL', 'NATIONWIDE']:
        coverage_type = 'national'
    elif service_zip_codes.upper() in ['NONE', 'NULL', '']:
        coverage_type = 'county'
    elif len(service_zip_codes) == 2 and service_zip_codes.upper() in ['FL', 'CA', 'TX', 'NY', 'AL', 'GA']:
        coverage_type = 'state'
        coverage_states = [service_zip_codes.upper()]
    elif ',' in service_zip_codes and all(len(s.strip()) == 2 for s in service_zip_codes.split(',') if s.strip()):
        # Multiple states like "AL, FL, GA"
        state_list = [s.strip().upper() for s in service_zip_codes.split(',') if s.strip()]
        coverage_type = 'state' if len(state_list) <= 3 else 'national'
        coverage_states = state_list
    elif ';' in service_zip_codes and ',' in service_zip_codes:
        # Direct county format: "County, ST; County, ST"
        county_list = [c.strip() for c in service_zip_codes.split(';') if c.strip()]
        coverage_counties = county_list
        # Extract states
        for county in county_list:
            if ', ' in county:
                state = county.split(', ')[-1]
                if state not in coverage_states:
                    coverage_states.append(state)
        coverage_type = 'county'
    elif ',' in service_zip_codes and not ';' in service_zip_codes:
        # Comma-separated counties like "Miami Dade, Broward"
        county_list = [c.strip() for c in service_zip_codes.split(',') if c.strip()]
        # Add FL as default state (most common)
        for county_raw in county_list:
            county_clean = county_raw.replace(' County', '').strip()
            if county_clean:
                coverage_counties.append(f"{county_clean}, FL")
                if 'FL' not in coverage_states:
                    coverage_states.append('FL')
        coverage_type = 'county'
    
    return {
        'type': coverage_type,
        'states': json.dumps(coverage_states),
        'counties': json.dumps(coverage_counties)
    }

@router.get("/scripts")
async def list_admin_scripts():
    """
    List all administrative scripts in the project.
    Returns information about each script and its purpose.
    """
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        scripts = []
        
        # Look for Python scripts in the root directory
        for file in os.listdir(project_root):
            if file.endswith('.py') and not file.startswith('__'):
                file_path = os.path.join(project_root, file)
                try:
                    # Get file stats
                    stat = os.stat(file_path)
                    
                    # Try to read docstring for description
                    description = "No description available"
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read(1000)  # First 1000 chars
                            if '"""' in content:
                                start = content.find('"""') + 3
                                end = content.find('"""', start)
                                if end > start:
                                    description = content[start:end].strip().split('\n')[0]
                    except:
                        pass
                    
                    # Categorize scripts
                    category = "utility"
                    status = "review"
                    
                    if "sync" in file.lower():
                        category = "sync"
                        if file == "sync_ghl_as_truth.py":
                            status = "active"
                        elif file == "sync_vendors_from_ghl.py":
                            status = "legacy"
                    elif "test" in file.lower():
                        category = "test"
                        status = "cleanup"
                    elif "main" in file.lower() or "server" in file.lower():
                        category = "core"
                        status = "active"
                    elif any(word in file.lower() for word in ["debug", "temp", "scratch"]):
                        category = "debug"
                        status = "cleanup"
                    
                    scripts.append({
                        "name": file,
                        "path": file_path,
                        "description": description,
                        "category": category,
                        "status": status,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
                    
                except Exception as e:
                    logger.warning(f"Could not analyze script {file}: {e}")
                    continue
        
        # Sort by category and name
        scripts.sort(key=lambda x: (x['category'], x['name']))
        
        return {
            "status": "success",
            "scripts": scripts,
            "total_count": len(scripts),
            "categories": {
                "active": len([s for s in scripts if s['status'] == 'active']),
                "review": len([s for s in scripts if s['status'] == 'review']),
                "cleanup": len([s for s in scripts if s['status'] == 'cleanup'])
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing scripts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list scripts: {str(e)}")

@router.delete("/scripts/{script_name}")
async def delete_script(script_name: str):
    """
    Delete a script file (for cleanup purposes).
    Only allows deletion of scripts marked for cleanup.
    """
    try:
        # Security check - only allow deletion of certain types
        if not any(word in script_name.lower() for word in ["test", "debug", "temp", "scratch"]):
            raise HTTPException(status_code=403, detail="Only test, debug, and temporary scripts can be deleted")
        
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        script_path = os.path.join(project_root, script_name)
        
        if not os.path.exists(script_path):
            raise HTTPException(status_code=404, detail="Script not found")
        
        if not script_path.endswith('.py'):
            raise HTTPException(status_code=403, detail="Only Python scripts can be deleted")
        
        # Additional safety check
        if not script_path.startswith(project_root):
            raise HTTPException(status_code=403, detail="Invalid script path")
        
        os.remove(script_path)
        logger.info(f"Deleted script: {script_name}")
        
        return {
            "status": "success",
            "message": f"Script {script_name} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting script {script_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete script: {str(e)}")

@router.get("/health")
async def admin_health_check():
    """Health check for admin functions"""
    return {
        "status": "healthy",
        "service": "admin_functions",
        "timestamp": datetime.now().isoformat()
    }