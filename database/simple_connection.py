# database/simple_connection.py

import sqlite3
import logging
from typing import Dict, List, Any, Optional
import json 
import uuid 
from datetime import datetime

logger = logging.getLogger(__name__)

class SimpleDatabase:
    def __init__(self, db_path: str = "smart_lead_router.db"):
        self.db_path = db_path
        self.init_database()
    
    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def init_database(self):
        conn = None
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
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
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vendors (
                    id TEXT PRIMARY KEY,
                    account_id TEXT,
                    name TEXT NOT NULL,
                    company_name TEXT,
                    email TEXT, /* Consider UNIQUE constraint if email must be unique per account or globally */
                    phone TEXT,
                    ghl_contact_id TEXT UNIQUE, 
                    ghl_user_id TEXT UNIQUE,    
                    services_provided TEXT DEFAULT '[]',
                    service_areas TEXT DEFAULT '[]',
                    status TEXT DEFAULT 'pending', 
                    taking_new_work BOOLEAN DEFAULT 1,
                    performance_score REAL DEFAULT 0.8,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (account_id) REFERENCES accounts (id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS leads (
                    id TEXT PRIMARY KEY,
                    account_id TEXT,
                    vendor_id TEXT,
                    ghl_contact_id TEXT, 
                    service_category TEXT,
                    customer_name TEXT,
                    customer_email TEXT,
                    customer_phone TEXT,
                    service_details TEXT DEFAULT '{}',
                    estimated_value REAL DEFAULT 0,
                    priority_score REAL DEFAULT 0,
                    status TEXT DEFAULT 'new', 
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (account_id) REFERENCES accounts (id),
                    FOREIGN KEY (vendor_id) REFERENCES vendors (id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS activity_log (
                    id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    event_data_json TEXT,
                    related_contact_id TEXT, 
                    related_vendor_id TEXT,  
                    success BOOLEAN,
                    error_message TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS account_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id TEXT NOT NULL,
                    setting_key TEXT NOT NULL,
                    setting_value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(account_id, setting_key),
                    FOREIGN KEY (account_id) REFERENCES accounts(id)
                )
            """)
            conn.commit()
            logger.info("✅ Database initialized/verified successfully.")
        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
            # raise # Optionally re-raise if startup should fail
        finally:
            if conn:
                conn.close()

    def log_activity(self, event_type: str, event_data: Dict, 
                     lead_id: Optional[str] = None, 
                     vendor_id: Optional[str] = None, 
                     success: bool = True, 
                     error_message: Optional[str] = None):
        conn = None 
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            log_id_str = str(uuid.uuid4()) # Renamed to avoid conflict with lead_id parameter
            event_data_str = json.dumps(event_data) if event_data is not None else '{}'

            cursor.execute("""
                INSERT INTO activity_log (id, event_type, event_data_json, related_contact_id, related_vendor_id, success, error_message, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (log_id_str, event_type, event_data_str, lead_id, vendor_id, success, error_message))
            conn.commit()
            logger.debug(f"Activity logged: {event_type} - ID {log_id_str}")
        except Exception as ex:
            logger.error(f"Failed to log activity: {ex}. Data: {event_type}, {event_data}")
        finally:
            if conn:
                conn.close()

    def create_account(self, company_name: str, industry: str = "marine", 
                       ghl_location_id: Optional[str] = None, 
                       ghl_private_token: Optional[str] = None) -> str:
        conn = None
        try:
            account_id_str = str(uuid.uuid4())
            effective_ghl_location_id = ghl_location_id or f"temp_loc_{int(datetime.now().timestamp())}_{str(uuid.uuid4())[:4]}"
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO accounts (id, ghl_location_id, company_name, industry, ghl_private_token, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (account_id_str, effective_ghl_location_id, company_name, industry, ghl_private_token))
            conn.commit()
            logger.info(f"✅ Account created: {account_id_str} for company {company_name}")
            return account_id_str
        except sqlite3.IntegrityError as ie:
            logger.error(f"Account creation integrity error (possibly duplicate ghl_location_id '{effective_ghl_location_id}'): {str(ie)}")
            raise 
        except Exception as e:
            logger.error(f"Account creation error: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()

    def get_account_by_id(self, account_id: str) -> Optional[Dict[str, Any]]:
        conn = None
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT id, company_name, industry, ghl_location_id, ghl_private_token, settings FROM accounts WHERE id = ?", (account_id,))
            row = cursor.fetchone()
            if row:
                return {"id": row[0], "company_name": row[1], "industry": row[2], "ghl_location_id": row[3], 
                        "ghl_private_token": row[4], "settings": json.loads(row[5]) if row[5] else {}}
            return None
        except Exception as e:
            logger.error(f"Error getting account by ID {account_id}: {str(e)}")
            return None
        finally:
            if conn:
                conn.close()

    def get_account_by_ghl_location_id(self, ghl_location_id: str) -> Optional[Dict[str, Any]]:
        conn = None
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            # Ensure we query the correct table and columns as defined
            cursor.execute("SELECT id, company_name, industry, ghl_location_id, ghl_private_token, settings FROM accounts WHERE ghl_location_id = ?", (ghl_location_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0], "company_name": row[1], "industry": row[2],
                    "ghl_location_id": row[3], "ghl_private_token": row[4],
                    "settings": json.loads(row[5]) if row[5] else {}
                }
            logger.warning(f"No SaaS account found for GHL Location ID: {ghl_location_id}")
            return None # Explicitly return None if not found
        except Exception as e:
            logger.error(f"Error getting account by GHL Location ID {ghl_location_id}: {str(e)}")
            return None
        finally:
            if conn:
                conn.close()

    def get_accounts(self) -> List[Dict[str, Any]]:
        conn = None
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT id, ghl_location_id, company_name, industry, subscription_tier, settings, created_at FROM accounts")
            accounts_data = cursor.fetchall()
            
            accounts_list = []
            for acc_row in accounts_data:
                accounts_list.append({
                    "id": acc_row[0], "ghl_location_id": acc_row[1], "company_name": acc_row[2], 
                    "industry": acc_row[3], "subscription_tier": acc_row[4],
                    "settings": json.loads(acc_row[5]) if acc_row[5] else {}, "created_at": acc_row[6]
                })
            return accounts_list
        except Exception as e:
            logger.error(f"Get accounts error: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()

    def create_vendor(self, account_id: str, name: str, email: str, 
                      company_name: str = "", phone: str = "",
                      ghl_contact_id: Optional[str] = None, status: str = "pending") -> str:
        conn = None
        try:
            vendor_id_str = str(uuid.uuid4())
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO vendors (id, account_id, name, email, company_name, phone, ghl_contact_id, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (vendor_id_str, account_id, name, email.lower().strip(), company_name, phone, ghl_contact_id, status))
            conn.commit()
            logger.info(f"✅ Vendor created: {vendor_id_str} with email {email}")
            return vendor_id_str
        except sqlite3.IntegrityError as ie:
            logger.error(f"Vendor creation integrity error (duplicate email or ghl_contact_id for '{email}'?): {str(ie)}")
            existing_vendor = self.get_vendor_by_email_and_account(email, account_id)
            if existing_vendor: return existing_vendor['id']
            raise
        except Exception as e:
            logger.error(f"Vendor creation error for {email}: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
    
    def get_vendor_by_email_and_account(self, email: str, account_id: str) -> Optional[Dict[str, Any]]:
        conn = None
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, company_name, email, phone, ghl_contact_id, status FROM vendors WHERE lower(email) = lower(?) AND account_id = ?", (email.strip(), account_id))
            row = cursor.fetchone()
            if row: return {"id": row[0], "name": row[1], "company_name": row[2], "email": row[3], 
                            "phone": row[4], "ghl_contact_id": row[5], "status": row[6]}
            return None
        except Exception as e:
            logger.error(f"Error getting vendor by email {email} for account {account_id}: {str(e)}")
            return None
        finally:
            if conn:
                conn.close()

    def update_vendor_ghl_contact_id(self, vendor_id: str, ghl_contact_id: str):
        conn = None
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute("UPDATE vendors SET ghl_contact_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (ghl_contact_id, vendor_id))
            conn.commit()
            logger.info(f"Updated vendor {vendor_id} with GHL Contact ID {ghl_contact_id}")
        except Exception as e:
            logger.error(f"Error updating vendor GHL Contact ID for {vendor_id}: {e}")
        finally:
            if conn:
                conn.close()

    def update_vendor_status(self, vendor_id: str, status: str, ghl_user_id: Optional[str] = None):
        conn = None
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            if ghl_user_id:
                cursor.execute("UPDATE vendors SET status = ?, ghl_user_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", 
                               (status, ghl_user_id, vendor_id))
            else:
                cursor.execute("UPDATE vendors SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", 
                               (status, vendor_id))
            conn.commit()
            logger.info(f"Updated vendor {vendor_id} status to {status}" + (f" with GHL User ID {ghl_user_id}" if ghl_user_id else ""))
        except Exception as e:
            logger.error(f"Error updating vendor status for {vendor_id}: {e}")
        finally:
            if conn:
                conn.close()

    def get_vendors(self, account_id: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = None
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            sql_query = "SELECT id, account_id, name, company_name, email, phone, services_provided, service_areas, status, taking_new_work, performance_score, created_at, ghl_contact_id, ghl_user_id FROM vendors"
            params = []
            if account_id:
                sql_query += " WHERE account_id = ?"
                params.append(account_id)
            
            cursor.execute(sql_query, tuple(params))
            vendors_data = cursor.fetchall()
            
            vendors_list = []
            for v_row in vendors_data:
                vendors_list.append({
                    "id": v_row[0], "account_id": v_row[1], "name": v_row[2], "company_name": v_row[3],
                    "email": v_row[4], "phone": v_row[5], 
                    "services_provided": json.loads(v_row[6]) if v_row[6] else [],
                    "service_areas": json.loads(v_row[7]) if v_row[7] else [],
                    "status": v_row[8], "taking_new_work": bool(v_row[9]),
                    "performance_score": v_row[10], "created_at": v_row[11],
                    "ghl_contact_id": v_row[12], "ghl_user_id": v_row[13]
                })
            return vendors_list
        except Exception as e:
            logger.error(f"Get vendors error: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()
    
    def create_lead(self, service_category: str, customer_name: str = "", 
                   customer_email: str = "", customer_phone: Optional[str] = None, 
                   service_details: Optional[Dict] = None,
                   account_id: Optional[str] = None, vendor_id: Optional[str] = None,
                   ghl_contact_id: Optional[str] = None) -> str: # Added customer_phone, ghl_contact_id
        conn = None
        try:
            lead_id_str = str(uuid.uuid4())
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO leads (id, account_id, vendor_id, ghl_contact_id, service_category, 
                                 customer_name, customer_email, customer_phone, service_details, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (lead_id_str, account_id, vendor_id, ghl_contact_id, service_category,
                  customer_name, customer_email.lower().strip() if customer_email else None, customer_phone,
                  json.dumps(service_details or {})))
            conn.commit()
            logger.info(f"✅ Lead created: {lead_id_str}")
            return lead_id_str
        except Exception as e:
            logger.error(f"Lead creation error: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()

    def get_leads(self, account_id: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = None
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            sql_query = "SELECT id, account_id, vendor_id, ghl_contact_id, service_category, customer_name, customer_email, customer_phone, service_details, estimated_value, priority_score, status, created_at FROM leads"
            params = []
            if account_id:
                sql_query += " WHERE account_id = ?"
                params.append(account_id)
            
            cursor.execute(sql_query, tuple(params))
            leads_data = cursor.fetchall()
            
            leads_list = []
            for l_row in leads_data:
                leads_list.append({
                    "id": l_row[0], "account_id": l_row[1], "vendor_id": l_row[2], "ghl_contact_id": l_row[3],
                    "service_category": l_row[4], "customer_name": l_row[5], "customer_email": l_row[6],
                    "customer_phone": l_row[7], "service_details": json.loads(l_row[8]) if l_row[8] else {},
                    "estimated_value": l_row[9], "priority_score": l_row[10], "status": l_row[11],
                    "created_at": l_row[12]
                })
            return leads_list
        except Exception as e:
            logger.error(f"Get leads error: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()

    def get_stats(self) -> Dict[str, int]:
        conn = None
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM accounts")
            account_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM vendors")
            vendor_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM leads")
            lead_count = cursor.fetchone()[0]
            return {"accounts": account_count, "vendors": vendor_count, "leads": lead_count}
        except Exception as e:
            logger.error(f"Get stats error: {str(e)}")
            return {"accounts": 0, "vendors": 0, "leads": 0}
        finally:
            if conn:
                conn.close()

    def upsert_account_setting(self, account_id: str, setting_key: str, setting_value: Any) -> None:
        conn = None
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            value_to_store = json.dumps(setting_value) if isinstance(setting_value, (dict, list)) else str(setting_value)
            cursor.execute("""
                INSERT INTO account_settings (account_id, setting_key, setting_value, created_at, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT(account_id, setting_key) DO UPDATE SET 
                    setting_value = excluded.setting_value, 
                    updated_at = CURRENT_TIMESTAMP
            """, (account_id, setting_key, value_to_store))
            conn.commit()
            logger.info(f"Upserted setting '{setting_key}' for account {account_id}")
        except Exception as e:
            logger.error(f"Error upserting setting for account {account_id}: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def get_account_setting(self, account_id: str, setting_key: str) -> Optional[Any]:
        conn = None
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT setting_value FROM account_settings WHERE account_id = ? AND setting_key = ?", (account_id, setting_key))
            row = cursor.fetchone()
            if row and row[0] is not None:
                try:
                    if row[0].startswith('{') and row[0].endswith('}'): return json.loads(row[0])
                    if row[0].startswith('[') and row[0].endswith(']'): return json.loads(row[0])
                except json.JSONDecodeError: pass 
                return row[0]
            return None
        except Exception as e:
            logger.error(f"Error getting setting '{setting_key}' for account {account_id}: {e}")
            return None
        finally:
            if conn:
                conn.close()

# Global database instance
db = SimpleDatabase()