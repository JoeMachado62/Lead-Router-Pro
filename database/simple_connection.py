# database/simple_connection.py
# Enhanced version with structured lead storage capabilities

import sqlite3
import logging
from typing import Dict, List, Any, Optional
import json 
import uuid 
from datetime import datetime
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

logger = logging.getLogger(__name__)

class SimpleDatabase:
    def __init__(self, db_path: str = None):
        # Use absolute path to ensure consistent database location
        if db_path is None:
            # Always use the database in the Lead-Router-Pro project directory
            project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(project_dir, "smart_lead_router.db")
        self.db_path = db_path
        logger.info(f"📁 Using database file: {self.db_path}")
        self.init_database()
    
    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def init_database(self):
        """Initialize database with enhanced schema"""
        conn = None
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            # Create accounts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS accounts (
                    id TEXT PRIMARY KEY,
                    ghl_location_id TEXT UNIQUE,
                    company_name TEXT NOT NULL,
                    industry TEXT DEFAULT 'general',
                    subscription_tier TEXT DEFAULT 'starter',
                    settings TEXT DEFAULT '{}',
                    ghl_private_token TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP 
                )
            ''')
            
            # Create vendors table - FIXED to use actual field names
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vendors (
                    id TEXT PRIMARY KEY,
                    account_id TEXT,
                    name TEXT NOT NULL,
                    company_name TEXT,
                    email TEXT,
                    phone TEXT,
                    ghl_contact_id TEXT UNIQUE, 
                    ghl_user_id TEXT UNIQUE,    
                    service_categories TEXT DEFAULT '[]',
                    services_offered TEXT DEFAULT '[]',  -- ACTUAL field name
                    coverage_type TEXT DEFAULT 'county',  -- ACTUAL field name
                    coverage_states TEXT DEFAULT '[]',   -- ACTUAL field name
                    coverage_counties TEXT DEFAULT '[]', -- ACTUAL field name
                    last_lead_assigned TIMESTAMP,
                    lead_close_percentage REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'pending', 
                    taking_new_work BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (account_id) REFERENCES accounts (id)
                )
            ''')
            
            # Create enhanced leads table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS leads (
                    id TEXT PRIMARY KEY,
                    account_id TEXT,
                    vendor_id TEXT,
                    ghl_contact_id TEXT, 
                    ghl_opportunity_id TEXT,
                    service_category TEXT,
                    customer_name TEXT,
                    customer_email TEXT,
                    customer_phone TEXT,
                    service_details TEXT DEFAULT '{}',
                    estimated_value REAL DEFAULT 0,
                    priority_score REAL DEFAULT 0,
                    priority TEXT DEFAULT 'normal',
                    source TEXT DEFAULT 'elementor',
                    status TEXT DEFAULT 'new',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (account_id) REFERENCES accounts (id),
                    FOREIGN KEY (vendor_id) REFERENCES vendors (id)
                )
            ''')
            
            # Check if enhanced columns exist and add them if needed
            cursor.execute("PRAGMA table_info(leads)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Add enhanced columns if they don't exist
            enhanced_columns = [
                ("service_zip_code", "TEXT"),
                ("service_city", "TEXT"), 
                ("service_state", "TEXT"),
                ("service_county", "TEXT"),
                ("specific_services", "TEXT DEFAULT '[]'"),
                ("service_complexity", "TEXT DEFAULT 'simple'"),
                ("estimated_duration", "TEXT DEFAULT 'medium'"),
                ("requires_emergency_response", "BOOLEAN DEFAULT 0"),
                ("classification_confidence", "REAL DEFAULT 0.0"),
                ("classification_reasoning", "TEXT")
            ]
            
            for column_name, column_def in enhanced_columns:
                if column_name not in columns:
                    cursor.execute(f"ALTER TABLE leads ADD COLUMN {column_name} {column_def}")
                    logger.info(f"✅ Added enhanced column: {column_name}")
            
            # Create activity log table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS activity_log (
                    id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    event_data TEXT DEFAULT '{}',
                    lead_id TEXT,
                    vendor_id TEXT,
                    account_id TEXT,
                    success BOOLEAN DEFAULT 1,
                    error_message TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            logger.info("✅ Database initialized with enhanced schema")
            
        except Exception as e:
            logger.error(f"❌ Database initialization error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        conn = None
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            # Get table counts
            cursor.execute("SELECT COUNT(*) FROM accounts")
            account_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM vendors")
            vendor_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM leads")
            lead_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM activity_log")
            activity_count = cursor.fetchone()[0]
            
            # Get recent activity
            cursor.execute("SELECT COUNT(*) FROM activity_log WHERE timestamp > datetime('now', '-24 hours')")
            recent_activity = cursor.fetchone()[0]
            
            return {
                "database_file": self.db_path,
                "accounts": account_count,
                "vendors": vendor_count,
                "leads": lead_count,
                "activity_logs": activity_count,
                "recent_activity_24h": recent_activity,
                "database_healthy": True
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting database stats: {e}")
            return {"database_healthy": False, "error": str(e)}
        finally:
            if conn:
                conn.close()

    def log_activity(self, event_type: str, event_data: Dict[str, Any] = None, 
                    lead_id: str = None, vendor_id: str = None, account_id: str = None,
                    success: bool = True, error_message: str = None) -> str:
        """Log activity to database"""
        conn = None
        try:
            activity_id = str(uuid.uuid4())
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO activity_log (id, event_type, event_data, lead_id, vendor_id, account_id, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (activity_id, event_type, json.dumps(event_data or {}), lead_id, vendor_id, account_id, success, error_message))
            
            conn.commit()
            return activity_id
            
        except Exception as e:
            logger.error(f"❌ Error logging activity: {e}")
            return ""
        finally:
            if conn:
                conn.close()

    # =======================
    # ACCOUNT MANAGEMENT
    # =======================
    
    def create_account(self, company_name: str, industry: str = "general", 
                      ghl_location_id: str = None, ghl_private_token: str = None) -> str:
        """Create new account"""
        conn = None
        try:
            account_id = str(uuid.uuid4())
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO accounts (id, company_name, industry, ghl_location_id, ghl_private_token)
                VALUES (?, ?, ?, ?, ?)
            ''', (account_id, company_name, industry, ghl_location_id, ghl_private_token))
            
            conn.commit()
            logger.info(f"✅ Account created: {account_id}")
            return account_id
            
        except Exception as e:
            logger.error(f"❌ Account creation error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def get_account_by_ghl_location_id(self, ghl_location_id: str) -> Optional[Dict[str, Any]]:
        """Get account by GHL location ID"""
        conn = None
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, ghl_location_id, company_name, industry, subscription_tier, 
                       settings, ghl_private_token, created_at, updated_at
                FROM accounts WHERE ghl_location_id = ?
            ''', (ghl_location_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0], "ghl_location_id": row[1], "company_name": row[2],
                    "industry": row[3], "subscription_tier": row[4], 
                    "settings": json.loads(row[5]) if row[5] else {},
                    "ghl_private_token": row[6], "created_at": row[7], "updated_at": row[8]
                }
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting account by GHL location ID: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_account_setting(self, account_id: str, setting_key: str) -> Optional[Any]:
        """
        Get a specific account setting by key
        
        Args:
            account_id: Account UUID
            setting_key: Setting key to retrieve (e.g., 'lead_routing_performance_percentage')
            
        Returns:
            Setting value or None if not found
        """
        conn = None
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            # Get settings JSON from accounts table
            cursor.execute('SELECT settings FROM accounts WHERE id = ?', (account_id,))
            result = cursor.fetchone()
            
            if not result:
                logger.warning(f"Account {account_id} not found")
                return None
                
            settings = json.loads(result[0] or '{}')
            return settings.get(setting_key)
            
        except Exception as e:
            logger.error(f"Error getting account setting {setting_key} for {account_id}: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def upsert_account_setting(self, account_id: str, setting_key: str, setting_value: Any) -> bool:
        """
        Create or update a specific account setting
        
        Args:
            account_id: Account UUID
            setting_key: Setting key to update (e.g., 'lead_routing_performance_percentage')
            setting_value: New setting value (can be int, string, bool, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        conn = None
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            # Get current settings
            cursor.execute('SELECT settings FROM accounts WHERE id = ?', (account_id,))
            result = cursor.fetchone()
            
            if not result:
                logger.error(f"Account {account_id} not found - cannot update setting")
                return False
                
            # Update settings JSON
            current_settings = json.loads(result[0] or '{}')
            current_settings[setting_key] = setting_value
            
            # Save back to database
            cursor.execute(
                'UPDATE accounts SET settings = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                (json.dumps(current_settings), account_id)
            )
            
            conn.commit()
            logger.debug(f"✅ Updated account setting {setting_key} = {setting_value} for {account_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating account setting {setting_key} for {account_id}: {e}")
            return False
        finally:
            if conn:
                conn.close()

    # =======================
    # VENDOR MANAGEMENT
    # =======================
    
    def create_vendor(self, account_id: str, name: str, email: str, 
                     company_name: str = "", phone: str = "",
                     ghl_contact_id: str = None, status: str = "pending",
                     service_categories: str = "", services_offered: str = "",
                     coverage_counties: str = "") -> str:
        """Create new vendor - FIXED to include services_offered parameter"""
        conn = None
        try:
            vendor_id = str(uuid.uuid4())
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO vendors (id, account_id, name, company_name, email, phone, 
                                   ghl_contact_id, status, service_categories, services_offered, coverage_counties)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (vendor_id, account_id, name, company_name, email, phone,
                  ghl_contact_id, status, service_categories, services_offered, coverage_counties))
            
            conn.commit()
            logger.info(f"✅ Vendor created: {vendor_id}")
            return vendor_id
            
        except Exception as e:
            logger.error(f"❌ Vendor creation error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def get_vendors(self, account_id: str = None, status: str = None) -> List[Dict[str, Any]]:
        """Get vendors with optional filtering - FIXED to use actual database field names"""
        conn = None
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            # Build dynamic query
            conditions = []
            params = []
            
            if account_id:
                conditions.append("account_id = ?")
                params.append(account_id)
            
            if status:
                conditions.append("status = ?")
                params.append(status)
            
            where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
            
            # FIXED: Use actual database field names
            cursor.execute(f'''
                SELECT id, account_id, name, company_name, email, phone, ghl_contact_id, 
                       ghl_user_id, service_categories, services_offered, coverage_type,
                       coverage_states, coverage_counties, last_lead_assigned, lead_close_percentage,
                       status, taking_new_work, created_at, updated_at
                FROM vendors{where_clause}
            ''', params)
            
            vendors_list = []
            for row in cursor.fetchall():
                vendor = {
                    "id": row[0], "account_id": row[1], "name": row[2], "company_name": row[3],
                    "email": row[4], "phone": row[5], "ghl_contact_id": row[6], "ghl_user_id": row[7],
                    "service_categories": json.loads(row[8]) if row[8] else [],
                    "services_offered": json.loads(row[9]) if row[9] else [],  # ACTUAL field name
                    "coverage_type": row[10], # ACTUAL field name
                    "coverage_states": json.loads(row[11]) if row[11] else [],  # ACTUAL field name  
                    "coverage_counties": json.loads(row[12]) if row[12] else [],  # ACTUAL field name
                    "last_lead_assigned": row[13], "lead_close_percentage": row[14],
                    "status": row[15], "taking_new_work": bool(row[16]),
                    "created_at": row[17], "updated_at": row[18]
                }
                vendors_list.append(vendor)
            
            return vendors_list
            
        except Exception as e:
            logger.error(f"❌ Get vendors error: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_vendor_by_email_and_account(self, email: str, account_id: str) -> Optional[Dict[str, Any]]:
        """Get vendor by email and account ID - FIXED to use correct column names"""
        conn = None
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            # FIXED: Use service_categories instead of services_provided
            cursor.execute('''
                SELECT id, account_id, name, company_name, email, phone, ghl_contact_id, 
                       ghl_user_id, service_categories, status, taking_new_work
                FROM vendors WHERE email = ? AND account_id = ?
            ''', (email.lower().strip(), account_id))
            
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0], "account_id": row[1], "name": row[2], "company_name": row[3],
                    "email": row[4], "phone": row[5], "ghl_contact_id": row[6], "ghl_user_id": row[7],
                    "service_categories": json.loads(row[8]) if row[8] else [],  # FIXED name
                    "status": row[9], "taking_new_work": bool(row[10])
                }
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting vendor by email: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def update_vendor_status(self, vendor_id: str, status: str, ghl_user_id: str = None) -> bool:
        """Update vendor status and optional GHL user ID"""
        conn = None
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            if ghl_user_id:
                cursor.execute('''
                    UPDATE vendors 
                    SET status = ?, ghl_user_id = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                ''', (status, ghl_user_id, vendor_id))
            else:
                cursor.execute('''
                    UPDATE vendors 
                    SET status = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                ''', (status, vendor_id))
            
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"❌ Error updating vendor status: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def update_vendor_ghl_user_id(self, vendor_id: str, ghl_user_id: str) -> bool:
        """Update vendor with GHL User ID - ENSURE this method exists"""
        conn = None
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE vendors 
                SET ghl_user_id = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (ghl_user_id, vendor_id))
            
            conn.commit()
            logger.info(f"✅ Updated vendor {vendor_id} with GHL User ID: {ghl_user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating vendor GHL user ID: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def create_routing_vendor(self, vendor_data: Dict[str, Any]) -> str:
        """
        Create optimized vendor record for efficient lead routing.
        This is used by the county-based vendor creation system.
        
        Args:
            vendor_data: Dictionary containing all vendor routing data
                - account_id: Account ID
                - name: Vendor name
                - email: Vendor email
                - ghl_user_id: GHL User ID for assignments
                - ghl_contact_id: GHL Contact ID
                - primary_service_category: Primary service category
                - secondary_service_categories: JSON array of secondary services
                - service_coverage_type: "county" (or "zip" for legacy)
                - service_counties: JSON array of "County, State" entries
                - service_states: JSON array of state abbreviations
                - status: Vendor status ("active", "pending", etc.)
                - taking_new_work: Boolean for availability
                
        Returns:
            Vendor ID string
        """
        conn = None
        try:
            vendor_id = str(uuid.uuid4())
            conn = self._get_conn()
            cursor = conn.cursor()
            
            # Validate required fields
            required_fields = ['account_id', 'name', 'email', 'ghl_contact_id']
            for field in required_fields:
                if not vendor_data.get(field):
                    raise ValueError(f"Required field '{field}' is missing from vendor_data")
            
            # FIXED: Use actual database field names  
            cursor.execute('''
                INSERT INTO vendors (
                    id, account_id, name, email, ghl_user_id, ghl_contact_id,
                    services_offered, coverage_type, coverage_counties, coverage_states,
                    status, taking_new_work, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (
                vendor_id,
                vendor_data['account_id'],
                vendor_data['name'],
                vendor_data['email'],
                vendor_data.get('ghl_user_id'),
                vendor_data['ghl_contact_id'],
                vendor_data.get('secondary_service_categories', '[]'),  # Store as JSON for services_offered field
                vendor_data.get('service_coverage_type', 'county'),
                vendor_data.get('service_counties', '[]'),
                vendor_data.get('service_states', '[]'),
                vendor_data.get('status', 'active'),
                vendor_data.get('taking_new_work', True)
            ))
            
            conn.commit()
            logger.info(f"✅ Routing vendor created: {vendor_id}")
            return vendor_id
            
        except Exception as e:
            logger.error(f"❌ Routing vendor creation error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    # =======================
    # ORIGINAL LEAD MANAGEMENT (LEGACY)
    # =======================
    
    def create_lead(self, service_category: str, customer_name: str = "", 
                   customer_email: str = "", customer_phone: Optional[str] = None, 
                   service_details: Optional[Dict] = None,
                   account_id: Optional[str] = None, vendor_id: Optional[str] = None,
                   ghl_contact_id: Optional[str] = None, ghl_opportunity_id: Optional[str] = None,
                   priority: str = "normal", source: str = "elementor") -> str:
        """Create lead (legacy method - maintained for backward compatibility)"""
        conn = None
        try:
            lead_id_str = str(uuid.uuid4())
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO leads (id, account_id, vendor_id, ghl_contact_id, ghl_opportunity_id, service_category, 
                                 customer_name, customer_email, customer_phone, service_details, priority, source, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (lead_id_str, account_id, vendor_id, ghl_contact_id, ghl_opportunity_id, service_category,
                  customer_name, customer_email.lower().strip() if customer_email else None, customer_phone,
                  json.dumps(service_details or {}), priority, source))
            conn.commit()
            logger.info(f"✅ Lead created: {lead_id_str}" + (f" with opportunity ID: {ghl_opportunity_id}" if ghl_opportunity_id else ""))
            return lead_id_str
        except Exception as e:
            logger.error(f"❌ Lead creation error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    # =======================
    # ENHANCED LEAD MANAGEMENT
    # =======================
    
    def create_enhanced_lead(self, 
                           customer_data: Dict,
                           classification_result: Dict,
                           account_id: Optional[str] = None,
                           vendor_id: Optional[str] = None,
                           ghl_contact_id: Optional[str] = None,
                           ghl_opportunity_id: Optional[str] = None,
                           source: str = "elementor") -> str:
        """
        Create lead with enhanced structured data storage.
        
        Args:
            customer_data: Basic customer info (name, email, phone)
            classification_result: Result from EnhancedServiceClassifier
            account_id: Account ID
            vendor_id: Assigned vendor ID (if any)
            ghl_contact_id: GHL contact ID
            ghl_opportunity_id: GHL opportunity ID
            source: Lead source
            
        Returns:
            Lead ID string
        """
        conn = None
        try:
            lead_id = str(uuid.uuid4())
            conn = self._get_conn()
            cursor = conn.cursor()
            
            # Calculate estimated value based on service complexity
            estimated_value = self._calculate_estimated_value(classification_result)
            
            # Calculate priority score
            priority_score = self._calculate_priority_score(classification_result)
            
            # Determine priority level
            priority_level = classification_result.get("priority_level", "normal")
            
            # Build minimal service_details with only essential data
            essential_service_details = {
                "service_summary": {
                    "category": classification_result["primary_category"],
                    "services": classification_result["specific_services"],
                    "complexity": classification_result["service_complexity"]
                },
                "routing_info": {
                    "primary_category": classification_result["primary_category"],
                    "specific_services": classification_result["specific_services"],
                    "coverage_requirements": classification_result["coverage_area"]
                },
                "classification_meta": {
                    "confidence": classification_result["confidence"],
                    "reasoning": classification_result["reasoning"],
                    "method": "enhanced_classifier"
                }
            }
            
            # Insert with enhanced schema
            cursor.execute('''
                INSERT INTO leads (
                    id, account_id, vendor_id, ghl_contact_id, ghl_opportunity_id, 
                    service_category, customer_name, customer_email, customer_phone,
                    service_zip_code, service_city, service_state, service_county,
                    specific_services, service_complexity, estimated_duration,
                    requires_emergency_response, classification_confidence, classification_reasoning,
                    service_details, estimated_value, priority_score, priority, source,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (
                lead_id,
                account_id,
                vendor_id,
                ghl_contact_id,
                ghl_opportunity_id,
                classification_result["primary_category"],
                customer_data.get("name", ""),
                customer_data.get("email", "").lower().strip() if customer_data.get("email") else None,
                customer_data.get("phone", ""),
                classification_result["coverage_area"]["zip_code"],
                classification_result["coverage_area"]["city"],
                classification_result["coverage_area"]["state"],
                classification_result["coverage_area"]["county"],
                json.dumps(classification_result["specific_services"]),
                classification_result["service_complexity"],
                classification_result["estimated_duration"],
                classification_result["requires_emergency_response"],
                classification_result["confidence"],
                classification_result["reasoning"],
                json.dumps(essential_service_details),
                estimated_value,
                priority_score,
                priority_level,
                source
            ))
            
            conn.commit()
            
            logger.info(f"✅ Enhanced lead created: {lead_id}")
            logger.info(f"   Category: {classification_result['primary_category']}")
            logger.info(f"   Services: {classification_result['specific_services']}")
            logger.info(f"   Location: {classification_result['coverage_area']['zip_code']}")
            logger.info(f"   Priority: {priority_level}")
            logger.info(f"   Estimated Value: ${estimated_value}")
            
            return lead_id
            
        except Exception as e:
            logger.error(f"❌ Enhanced lead creation error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def _calculate_estimated_value(self, classification_result: Dict) -> float:
        """Calculate estimated value based on service complexity and type"""
        base_values = {
            "Boat Maintenance": 500.0,
            "Engines and Generators": 1500.0,
            "Marine Systems": 1200.0,
            "Boat and Yacht Repair": 2000.0,
            "Boat Hauling and Yacht Delivery": 3000.0,
            "Boat Towing": 300.0,
            "Boat Charters and Rentals": 800.0,
            "Dock and Slip Rental": 200.0,
            "Fuel Delivery": 150.0,
            "Buying or Selling a Boat": 5000.0,
            "Boater Resources": 400.0,
            "Maritime Education and Training": 300.0,
            "Yacht Management": 2000.0,
            "Docks, Seawalls and Lifts": 2500.0,
            "Waterfront Property": 10000.0
        }
        
        base_value = base_values.get(classification_result["primary_category"], 500.0)
        
        # Adjust based on complexity
        complexity_multipliers = {
            "simple": 1.0,
            "moderate": 1.5,
            "complex": 2.0
        }
        
        complexity_multiplier = complexity_multipliers.get(classification_result["service_complexity"], 1.0)
        
        # Adjust based on number of services
        service_count = len(classification_result["specific_services"])
        service_multiplier = 1.0 + (service_count - 1) * 0.2
        
        # Emergency services get premium
        emergency_multiplier = 1.5 if classification_result["requires_emergency_response"] else 1.0
        
        estimated_value = base_value * complexity_multiplier * service_multiplier * emergency_multiplier
        
        return round(estimated_value, 2)
    
    def _calculate_priority_score(self, classification_result: Dict) -> float:
        """Calculate priority score for lead routing"""
        base_score = 0.5
        
        # Higher score for emergency services
        if classification_result["requires_emergency_response"]:
            base_score += 0.3
        
        # Higher score for complex services
        complexity_scores = {
            "simple": 0.1,
            "moderate": 0.2,
            "complex": 0.3
        }
        base_score += complexity_scores.get(classification_result["service_complexity"], 0.1)
        
        # Higher score for multiple services
        service_count = len(classification_result["specific_services"])
        base_score += min(service_count * 0.1, 0.3)
        
        # Higher score for high-value categories
        high_value_categories = ["Boat Hauling and Yacht Delivery", "Buying or Selling a Boat", "Waterfront Property"]
        if classification_result["primary_category"] in high_value_categories:
            base_score += 0.2
        
        return min(base_score, 1.0)

    def get_lead_routing_data(self, lead_id: str) -> Optional[Dict]:
        """
        Get essential routing data for a lead.
        This is what vendors need to see, not the raw form data.
        """
        conn = None
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    id, service_category, specific_services, service_zip_code, 
                    service_city, service_state, service_county, service_complexity,
                    estimated_duration, requires_emergency_response, estimated_value,
                    priority_score, priority, customer_name, customer_email, 
                    customer_phone, created_at, classification_confidence
                FROM leads 
                WHERE id = ?
            ''', (lead_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    "lead_id": row[0],
                    "service_category": row[1],
                    "specific_services": json.loads(row[2]) if row[2] else [],
                    "service_location": {
                        "zip_code": row[3],
                        "city": row[4],
                        "state": row[5],
                        "county": row[6]
                    },
                    "service_details": {
                        "complexity": row[7],
                        "estimated_duration": row[8],
                        "requires_emergency": bool(row[9])
                    },
                    "business_info": {
                        "estimated_value": row[10],
                        "priority_score": row[11],
                        "priority_level": row[12]
                    },
                    "customer_info": {
                        "name": row[13],
                        "email": row[14],
                        "phone": row[15]
                    },
                    "meta": {
                        "created_at": row[16],
                        "classification_confidence": row[17]
                    }
                }
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting lead routing data for {lead_id}: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def find_leads_for_routing(self, 
                              service_category: str = None,
                              zip_code: str = None,
                              state: str = None,
                              priority_level: str = None,
                              unassigned_only: bool = True) -> List[Dict]:
        """
        Find leads that match specific routing criteria.
        This enables efficient vendor matching.
        """
        conn = None
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            # Build dynamic query based on criteria
            conditions = []
            params = []
            
            if service_category:
                conditions.append("service_category = ?")
                params.append(service_category)
            
            if zip_code:
                conditions.append("service_zip_code = ?")
                params.append(zip_code)
            
            if state:
                conditions.append("service_state = ?")
                params.append(state)
            
            if priority_level:
                conditions.append("priority = ?")
                params.append(priority_level)
            
            if unassigned_only:
                conditions.append("vendor_id IS NULL")
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            query = f'''
                SELECT 
                    id, service_category, specific_services, service_zip_code,
                    service_city, service_state, priority, estimated_value,
                    priority_score, requires_emergency_response, created_at
                FROM leads 
                WHERE {where_clause}
                ORDER BY priority_score DESC, created_at ASC
            '''
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            leads = []
            for row in rows:
                leads.append({
                    "lead_id": row[0],
                    "service_category": row[1],
                    "specific_services": json.loads(row[2]) if row[2] else [],
                    "service_zip_code": row[3],
                    "service_city": row[4],
                    "service_state": row[5],
                    "priority": row[6],
                    "estimated_value": row[7],
                    "priority_score": row[8],
                    "requires_emergency": bool(row[9]),
                    "created_at": row[10]
                })
            
            return leads
            
        except Exception as e:
            logger.error(f"❌ Error finding leads for routing: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_lead_statistics(self, account_id: str = None) -> Dict:
        """Get statistics about leads for analytics"""
        conn = None
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            where_clause = "WHERE account_id = ?" if account_id else ""
            params = [account_id] if account_id else []
            
            # Get basic stats
            cursor.execute(f'''
                SELECT 
                    COUNT(*) as total_leads,
                    COUNT(CASE WHEN vendor_id IS NOT NULL THEN 1 END) as assigned_leads,
                    COUNT(CASE WHEN requires_emergency_response = 1 THEN 1 END) as emergency_leads,
                    AVG(estimated_value) as avg_value,
                    AVG(priority_score) as avg_priority_score
                FROM leads 
                {where_clause}
            ''', params)
            
            row = cursor.fetchone()
            basic_stats = {
                "total_leads": row[0],
                "assigned_leads": row[1],
                "unassigned_leads": row[0] - row[1],
                "emergency_leads": row[2],
                "avg_estimated_value": round(row[3] or 0, 2),
                "avg_priority_score": round(row[4] or 0, 2)
            }
            
            # Get category breakdown
            cursor.execute(f'''
                SELECT service_category, COUNT(*) as count
                FROM leads 
                {where_clause}
                GROUP BY service_category
                ORDER BY count DESC
            ''', params)
            
            category_stats = {}
            for row in cursor.fetchall():
                category_stats[row[0]] = row[1]
            
            return {
                "basic_stats": basic_stats,
                "category_breakdown": category_stats,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting lead statistics: {e}")
            return {"error": str(e)}
        finally:
            if conn:
                conn.close()

    # =======================
    # LEGACY METHODS (MAINTAINED FOR BACKWARD COMPATIBILITY)
    # =======================

    def get_leads(self, account_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get leads with optional account filtering (legacy method)"""
        conn = None
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            sql_query = "SELECT id, account_id, vendor_id, ghl_contact_id, service_category, customer_name, customer_email, customer_phone, service_details, estimated_value, priority_score, status, created_at FROM leads"
            params = []
            if account_id:
                sql_query += " WHERE account_id = ?"
                params.append(account_id)
            
            cursor.execute(sql_query, params)
            
            leads_list = []
            for row in cursor.fetchall():
                leads_list.append({
                    "id": row[0], "account_id": row[1], "vendor_id": row[2], 
                    "ghl_contact_id": row[3], "service_category": row[4], 
                    "customer_name": row[5], "customer_email": row[6], 
                    "customer_phone": row[7], "service_details": json.loads(row[8]) if row[8] else {},
                    "estimated_value": row[9], "priority_score": row[10], 
                    "status": row[11], "created_at": row[12]
                })
            
            return leads_list
            
        except Exception as e:
            logger.error(f"❌ Get leads error: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def update_lead_opportunity_id(self, lead_id: str, ghl_opportunity_id: str) -> bool:
        """Update lead with GHL opportunity ID"""
        conn = None
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE leads 
                SET ghl_opportunity_id = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (ghl_opportunity_id, lead_id))
            
            if cursor.rowcount > 0:
                conn.commit()
                logger.info(f"✅ Updated lead {lead_id} with opportunity ID {ghl_opportunity_id}")
                return True
            else:
                logger.warning(f"⚠️ No lead found with ID {lead_id} to update with opportunity ID")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating lead {lead_id} with opportunity ID {ghl_opportunity_id}: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def assign_lead_to_vendor(self, lead_id: str, vendor_id: str) -> bool:
        """Assign a lead to a specific vendor"""
        conn = None
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE leads 
                SET vendor_id = ?, status = 'assigned', updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (vendor_id, lead_id))
            
            if cursor.rowcount > 0:
                conn.commit()
                logger.info(f"✅ Assigned lead {lead_id} to vendor {vendor_id}")
                return True
            else:
                logger.warning(f"⚠️ No lead found with ID {lead_id} to assign to vendor")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error assigning lead {lead_id} to vendor {vendor_id}: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_lead_by_id(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific lead by its ID"""
        conn = None
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, account_id, vendor_id, ghl_contact_id, ghl_opportunity_id, 
                       service_category, customer_name, customer_email, customer_phone, 
                       service_details, estimated_value, priority_score, status, 
                       created_at, updated_at
                FROM leads WHERE id = ?
            ''', (lead_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0], "account_id": row[1], "vendor_id": row[2], 
                    "ghl_contact_id": row[3], "ghl_opportunity_id": row[4],
                    "service_category": row[5], "customer_name": row[6], 
                    "customer_email": row[7], "customer_phone": row[8],
                    "service_details": json.loads(row[9]) if row[9] else {},
                    "estimated_value": row[10], "priority_score": row[11], 
                    "status": row[12], "created_at": row[13], "updated_at": row[14]
                }
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting lead {lead_id}: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_lead_by_ghl_contact_id(self, ghl_contact_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific lead by GHL contact ID - CRITICAL for bulk assignment workflow"""
        conn = None
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, account_id, vendor_id, ghl_contact_id, ghl_opportunity_id, 
                       service_category, customer_name, customer_email, customer_phone, 
                       service_details, priority_score, status, 
                       service_county, service_state, service_zip_code,
                       created_at, updated_at
                FROM leads WHERE ghl_contact_id = ?
            ''', (ghl_contact_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0], "account_id": row[1], "vendor_id": row[2], 
                    "ghl_contact_id": row[3], "ghl_opportunity_id": row[4],
                    "service_category": row[5], "customer_name": row[6], 
                    "customer_email": row[7], "customer_phone": row[8],
                    "service_details": json.loads(row[9]) if row[9] else {},
                    "priority_score": row[10], 
                    "status": row[11], "service_county": row[12], 
                    "service_state": row[13], "customer_zip_code": row[14],
                    "created_at": row[15], "updated_at": row[16]
                }
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting lead by GHL contact ID {ghl_contact_id}: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def unassign_lead_from_vendor(self, lead_id: str) -> bool:
        """Remove vendor assignment from lead (for reassignment workflow)"""
        conn = None
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE leads 
                SET vendor_id = NULL, status = 'unassigned', updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (lead_id,))
            
            if cursor.rowcount > 0:
                conn.commit()
                logger.info(f"✅ Unassigned lead {lead_id} from vendor")
                return True
            else:
                logger.warning(f"⚠️ No lead found with ID {lead_id} to unassign")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error unassigning lead {lead_id}: {e}")
            return False
        finally:
            if conn:
                conn.close()

# Global database instance
db = SimpleDatabase()

# SQLAlchemy setup for authentication system  
# Fix: Use absolute path to ensure consistent database location
if "DATABASE_URL" not in os.environ:
    # Get the same absolute path used by SimpleDatabase
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_file_path = os.path.join(project_dir, "smart_lead_router.db")
    DATABASE_URL = f"sqlite:///{db_file_path}"
else:
    DATABASE_URL = os.getenv("DATABASE_URL")

# Create SQLAlchemy engine
auth_engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=auth_engine)

def get_db() -> Session:
    """
    SQLAlchemy dependency injection for authentication system
    Yields a database session that automatically closes after use
    """
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()

def get_db_session() -> Session:
    """
    Get a SQLAlchemy session for direct use (must be closed manually)
    """
    return SessionLocal()
