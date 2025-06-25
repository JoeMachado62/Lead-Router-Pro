# api/services/ghl_api.py

import requests
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class GoHighLevelAPI:
    """Enhanced GHL API client with V1/V2 fallback support"""
    
    def __init__(self, location_api_key: Optional[str] = None, private_token: Optional[str] = None, location_id: Optional[str] = None, agency_api_key: Optional[str] = None, api_key: Optional[str] = None):
        # Store both API keys for fallback logic
        self.location_api_key = location_api_key or api_key  # V1 Location API Key (preferred)
        self.private_token = private_token  # V2 PIT Token (fallback)
        self.agency_api_key = agency_api_key
        self.location_id = location_id
        self.base_url = "https://services.leadconnectorhq.com"
        
        # Determine which API version to try first
        if self.location_api_key:
            self.primary_auth_type = "location_api"
            self.primary_headers = {
                "Accept": "application/json",
                "Authorization": f"Bearer {self.location_api_key}",
                "Content-Type": "application/json",
                "Version": "2021-07-28"
            }
            logger.info("🔑 Using V1 Location API Key as primary authentication")
        else:
            self.primary_auth_type = "pit_token"
            self.primary_headers = {
                "Accept": "application/json",  # Ensure Accept header is present for V2 API
                "Authorization": f"Bearer {self.private_token}",
                "Content-Type": "application/json",
                "Version": "2021-07-28"
            }
            logger.info("🔑 Using V2 PIT Token as primary authentication")
        
        # Set up fallback headers if both keys are available
        if self.location_api_key and self.private_token:
            if self.primary_auth_type == "location_api":
                self.fallback_auth_type = "pit_token"
                self.fallback_headers = {
                    "Accept": "application/json",  # Ensure Accept header is present
                    "Authorization": f"Bearer {self.private_token}",
                    "Content-Type": "application/json",
                    "Version": "2021-07-28"
                }
            else:
                self.fallback_auth_type = "location_api"
                self.fallback_headers = {
                    "Accept": "application/json",
                    "Authorization": f"Bearer {self.location_api_key}",
                    "Content-Type": "application/json",
                    "Version": "2021-07-28"
                }
            logger.info(f"🔄 Fallback authentication available: {self.fallback_auth_type}")
        else:
            self.fallback_headers = None
            self.fallback_auth_type = None
        
        # Validate at least one auth method is available
        if not self.location_api_key and not self.private_token:
            raise ValueError("Either location_api_key or private_token must be provided")
        
        # Agency API headers for user management operations
        if agency_api_key:
            self.agency_headers = {
                "Accept": "application/json",
                "Authorization": f"Bearer {agency_api_key}",
                "Content-Type": "application/json",
                "Version": "2021-07-28"
            }
        else:
            self.agency_headers = None
    
    def _make_request_with_fallback(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make request with automatic fallback between API key types"""
        
        # Try primary authentication first
        try:
            logger.debug(f"🔑 Trying {self.primary_auth_type} for {method} {url}")
            kwargs['headers'] = self.primary_headers
            response = requests.request(method, url, **kwargs)
            
            # If successful (2xx status), return immediately
            if 200 <= response.status_code < 300:
                logger.debug(f"✅ {self.primary_auth_type} succeeded: {response.status_code}")
                return response
                
            # If authentication error and fallback available, try fallback
            if response.status_code in [401, 403] and self.fallback_headers:
                logger.warning(f"🔄 {self.primary_auth_type} failed ({response.status_code}), trying {self.fallback_auth_type}")
                
                kwargs['headers'] = self.fallback_headers
                fallback_response = requests.request(method, url, **kwargs)
                
                if 200 <= fallback_response.status_code < 300:
                    logger.info(f"✅ {self.fallback_auth_type} succeeded: {fallback_response.status_code}")
                    return fallback_response
                else:
                    logger.error(f"❌ Both auth methods failed. Primary: {response.status_code}, Fallback: {fallback_response.status_code}")
                    return fallback_response  # Return the fallback response for error handling
            else:
                # No fallback available or not an auth error
                logger.debug(f"❌ {self.primary_auth_type} failed: {response.status_code} (no fallback attempted)")
                return response
                
        except Exception as e:
            logger.error(f"❌ Request exception with {self.primary_auth_type}: {e}")
            
            # Try fallback if available
            if self.fallback_headers:
                try:
                    logger.warning(f"🔄 Trying {self.fallback_auth_type} after exception")
                    kwargs['headers'] = self.fallback_headers
                    return requests.request(method, url, **kwargs)
                except Exception as fallback_e:
                    logger.error(f"❌ Fallback also failed: {fallback_e}")
                    raise fallback_e
            else:
                raise e
    
    def search_contacts(self, query: str = "", limit: int = 100) -> List[Dict]:
        """Search contacts in GHL with fallback authentication"""
        try:
            # Ensure limit doesn't exceed 100
            limit = min(limit, 100)
            
            url = f"{self.base_url}/contacts/"
            params = {
                "locationId": self.location_id,
                "limit": limit
            }
            
            if query:
                params["query"] = query
            
            logger.debug(f"Searching contacts with params: {params}")
            
            response = self._make_request_with_fallback("GET", url, params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get('contacts', [])
            else:
                logger.error(f"Failed to search contacts: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error searching contacts: {str(e)}")
            return []
    
    def get_contact_by_id(self, contact_id: str) -> Optional[Dict]:
        """Get contact details by ID with fallback authentication"""
        try:
            url = f"{self.base_url}/contacts/{contact_id}"
            response = self._make_request_with_fallback("GET", url)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('contact', {})
            else:
                logger.error(f"Failed to get contact: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error getting contact: {str(e)}")
            return None
    
    def create_contact(self, contact_data: Dict) -> Optional[Dict]:
        """Create a new contact in GHL with detailed error reporting and fallback authentication"""
        try:
            url = f"{self.base_url}/contacts/"
            
            # Prepare payload with locationId
            payload = {
                "locationId": self.location_id,
                **contact_data
            }
            
            # Ensure locationId is not overridden by contact_data
            payload["locationId"] = self.location_id
            
            # VERBOSE DEBUG LOGGING
            logger.info(f"🔍 GHL API CREATE CONTACT REQUEST:")
            logger.info(f"  📍 URL: {url}")
            logger.info(f"  🔑 Primary Auth: {self.primary_auth_type}")
            logger.info(f"  🏢 LocationId being used: {self.location_id}")
            logger.info(f"  📦 Payload Keys: {list(payload.keys())}")
            
            # Verify locationId is in payload
            if "locationId" in payload:
                logger.info(f"  ✅ LocationId is in payload: {payload['locationId']}")
            else:
                logger.error(f"  ❌ LocationId is MISSING from payload!")
            
            # Detailed custom fields debugging
            if 'customFields' in payload:
                custom_fields = payload['customFields']
                logger.info(f"  🏷️  CustomFields Type: {type(custom_fields)}")
                logger.info(f"  🏷️  CustomFields Length: {len(custom_fields) if isinstance(custom_fields, (list, dict)) else 'N/A'}")
                if isinstance(custom_fields, list):
                    logger.info(f"  ✅ CustomFields is ARRAY (correct format)")
                    for i, field in enumerate(custom_fields):
                        logger.info(f"    [{i}] ID: {field.get('id', 'missing')}, Value: {field.get('value', 'missing')}")
                else:
                    logger.error(f"  ❌ CustomFields is {type(custom_fields)} (should be array!)")
                    logger.error(f"  ❌ CustomFields content: {custom_fields}")
            else:
                logger.info(f"  📝 No customFields in payload")
                
            logger.info(f"  📋 Full Payload: {payload}")
            
            # Use fallback request system
            response = self._make_request_with_fallback("POST", url, json=payload)
            
            # VERBOSE RESPONSE LOGGING
            logger.info(f"🔍 GHL API CREATE CONTACT RESPONSE:")
            logger.info(f"  📈 Status Code: {response.status_code}")
            logger.info(f"  📄 Response Headers: {dict(response.headers)}")
            logger.info(f"  📝 Response Text: {response.text}")
            
            if response.status_code == 201:
                data = response.json()
                contact = data.get('contact', {})
                logger.info(f"  ✅ SUCCESS: Created contact ID: {contact.get('id')}")
                return contact
            else:
                # Return detailed error information instead of None
                error_details = {
                    "error": True,
                    "status_code": response.status_code,
                    "response_text": response.text,
                    "url": url,
                    "payload_keys": list(payload.keys()),
                    "locationId_in_payload": payload.get('locationId', 'MISSING!')
                }
                
                # Try to parse JSON error if possible
                try:
                    error_json = response.json()
                    error_details["error_json"] = error_json
                except:
                    pass
                
                logger.error(f"  ❌ FAILED to create contact: {response.status_code}")
                logger.error(f"  ❌ Error details: {error_details}")
                return error_details
                
        except Exception as e:
            error_details = {
                "error": True,
                "exception": str(e),
                "exception_type": e.__class__.__name__
            }
            logger.error(f"❌ Exception creating contact: {str(e)}")
            return error_details
    
    def update_contact(self, contact_id: str, update_data: Dict) -> bool:
        """Update contact in GHL with fallback authentication"""
        try:
            url = f"{self.base_url}/contacts/{contact_id}"
            
            # For updates, we don't include locationId in the body, just the data to update
            payload = update_data.copy()
            # Remove locationId if it exists in update_data
            payload.pop("locationId", None)
            payload.pop("id", None)
            
            logger.debug(f"Updating contact {contact_id} with payload: {payload}")
            
            response = self._make_request_with_fallback("PUT", url, json=payload)
            
            if response.status_code == 200:
                logger.debug(f"Successfully updated contact {contact_id}")
                return True
            else:
                logger.error(f"Failed to update contact: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error updating contact: {str(e)}")
            return False
    
    def create_opportunity(self, opportunity_data: Dict) -> Optional[Dict]:
        """Create opportunity in GHL with fallback authentication"""
        try:
            url = f"{self.base_url}/opportunities/"
            
            # Ensure locationId is in opportunity data
            payload = {
                "locationId": self.location_id,
                **opportunity_data
            }
            payload["locationId"] = self.location_id  # Ensure it's not overridden
            
            logger.debug(f"Creating GHL opportunity. URL: {url}, Payload: {payload}")

            # Use _make_request_with_fallback for robust API calls
            response = self._make_request_with_fallback("POST", url, json=payload)
            
            if response.status_code == 201:
                data = response.json()
                logger.info(f"Successfully created GHL opportunity: {data.get('opportunity', {}).get('id')}")
                return data.get('opportunity', {})
            else:
                error_text = response.text
                error_json_response = None
                try:
                    error_json_response = response.json()
                    logger.error(f"Failed to create GHL opportunity: {response.status_code} - {error_text} - JSON: {error_json_response}")
                except ValueError:
                    logger.error(f"Failed to create GHL opportunity: {response.status_code} - {error_text}")
                
                # Return a dictionary with error details, similar to create_contact
                return {
                    "error": True,
                    "status_code": response.status_code,
                    "response_text": response.text,
                    "error_json": error_json_response,
                    "message": "Failed to create GHL opportunity"
                }
                
        except Exception as e:
            logger.exception(f"Exception creating GHL opportunity: {str(e)}")
            # Return a dictionary with error details on exception
            return {
                "error": True,
                "exception": str(e),
                "exception_type": e.__class__.__name__,
                "message": f"Exception occurred: {str(e)}"
            }
    
    def get_pipelines(self) -> List[Dict]:
        """Get all pipelines for the location"""
        try:
            url = f"{self.base_url}/opportunities/pipelines"
            params = {"locationId": self.location_id}
            
            response = self._make_request_with_fallback("GET", url, params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get('pipelines', [])
            else:
                logger.error(f"Failed to get pipelines: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error getting pipelines: {str(e)}")
            return []
    
    def get_custom_fields(self) -> List[Dict]:
        """Get custom fields for the location"""
        try:
            url = f"{self.base_url}/locations/{self.location_id}/customFields"
            
            response = self._make_request_with_fallback("GET", url)
            if response.status_code == 200:
                data = response.json()
                return data.get('customFields', [])
            else:
                logger.error(f"Failed to get custom fields: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error getting custom fields: {str(e)}")
            return []
    
    def send_sms(self, contact_id: str, message: str) -> bool:
        """Send SMS to contact"""
        try:
            url = f"{self.base_url}/conversations/messages"
            payload = {
                "type": "SMS",
                "contactId": contact_id,
                "message": message,
                "locationId": self.location_id
            }
            
            response = self._make_request_with_fallback("POST", url, json=payload)
            if response.status_code == 201:
                return True
            else:
                logger.error(f"Failed to send SMS: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending SMS: {str(e)}")
            return False
    
    def send_email(self, contact_id: str, subject: str, html_body: str) -> bool:
        """Send email to contact"""
        try:
            url = f"{self.base_url}/conversations/messages"
            payload = {
                "type": "Email",
                "contactId": contact_id,
                "subject": subject,
                "html": html_body,
                "locationId": self.location_id
            }
            
            response = self._make_request_with_fallback("POST", url, json=payload)
            if response.status_code == 201:
                return True
            else:
                logger.error(f"Failed to send email: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False
    
    def create_user(self, user_data: Dict) -> Optional[Dict]:
        """Create a new user in GHL using V1 API endpoint with Agency API key"""
        try:
            if not self.agency_api_key:
                logger.error("Agency API key required for user creation")
                return None
            
            # CORRECTED: Use V1 API endpoint for user creation
            v1_base_url = "https://rest.gohighlevel.com"
            url = f"{v1_base_url}/v1/users/"
            
            # CORRECTED: V1 API headers with Agency API key
            v1_headers = {
                "Authorization": f"Bearer {self.agency_api_key}",
                "Content-Type": "application/json"
            }
            
            # CORRECTED: V1 API payload structure with locationIds array  
            # Generate a secure password if not provided
            password = user_data.get("password", "TempPass123!")
            
            payload = {
                "firstName": user_data.get("firstName", ""),
                "lastName": user_data.get("lastName", ""), 
                "email": user_data.get("email", ""),
                "phone": user_data.get("phone", ""),  # FIXED: Add phone number to payload
                "password": password,
                "type": user_data.get("type", "account"),  # V1 API: account, agency
                "role": user_data.get("role", "user"),     # V1 API: admin, user
                "locationIds": [self.location_id],         # CORRECTED: Must be array with location ID
                "permissions": user_data.get("permissions", {
                    "campaignsEnabled": False,
                    "campaignsReadOnly": True,
                    "contactsEnabled": True,
                    "workflowsEnabled": False,
                    "triggersEnabled": False,
                    "funnelsEnabled": False,
                    "websitesEnabled": False,
                    "opportunitiesEnabled": True,
                    "dashboardStatsEnabled": True,
                    "bulkRequestsEnabled": False,
                    "appointmentEnabled": True,
                    "reviewsEnabled": False,
                    "onlineListingsEnabled": False,
                    "phoneCallEnabled": True,
                    "conversationsEnabled": True,
                    "assignedDataOnly": True,  # Only see their assigned leads
                    "adwordsReportingEnabled": False,
                    "membershipEnabled": False,
                    "facebookAdsReportingEnabled": False,
                    "attributionsReportingEnabled": False,
                    "settingsEnabled": False,
                    "tagsEnabled": False,
                    "leadValueEnabled": True,
                    "marketingEnabled": False,
                    "agentReportingEnabled": True,
                    "botService": False,
                    "socialPlanner": False,
                    "bloggingEnabled": False,
                    "invoiceEnabled": False,
                    "affiliateManagerEnabled": False,
                    "contentAiEnabled": False,
                    "refundsEnabled": False,
                    "recordPaymentEnabled": False,
                    "cancelSubscriptionEnabled": False,
                    "paymentsEnabled": False,
                    "communitiesEnabled": False,
                    "exportPaymentsEnabled": False
                })
            }
            
            # VERBOSE LOGGING for V1 API request
            logger.info(f"🔐 Creating GHL user with V1 API. URL: {url}")
            logger.info(f"📋 V1 User payload DETAILED:")
            logger.info(f"  firstName: '{payload.get('firstName', 'MISSING')}'")
            logger.info(f"  lastName: '{payload.get('lastName', 'MISSING')}'")
            logger.info(f"  email: '{payload.get('email', 'MISSING')}'")
            logger.info(f"  phone: '{payload.get('phone', 'MISSING')}'")  # FIXED: Log phone number
            logger.info(f"  password: '{payload.get('password', 'MISSING')[:3]}***' (showing first 3 chars)")
            logger.info(f"  type: '{payload.get('type', 'MISSING')}'")
            logger.info(f"  role: '{payload.get('role', 'MISSING')}'")
            logger.info(f"  locationIds: {payload.get('locationIds', 'MISSING')}")
            logger.info(f"  permissions keys: {list(payload.get('permissions', {}).keys())}")
            logger.info(f"🔑 V1 Headers: Authorization: Bearer {self.agency_api_key[:10]}...{self.agency_api_key[-4:]}")
            logger.info(f"📋 Full V1 Payload: {payload}")
            
            # CORRECTED: Use V1 API endpoint and headers
            response = requests.post(url, headers=v1_headers, json=payload)
            
            logger.info(f"📈 V1 User Creation Response: Status={response.status_code}")
            logger.info(f"📄 V1 Response Headers: {dict(response.headers)}")
            logger.info(f"📄 V1 Response Text: {response.text}")
            
            # FIXED: Accept both 200 and 201 status codes
            if response.status_code in [200, 201]:
                data = response.json()
                user = data.get('user', data)  # Handle different response structures
                user_id = user.get('id') if isinstance(user, dict) else None
                logger.info(f"✅ Successfully created GHL user with V1 API: {user_id}")
                return user
            else:
                logger.error(f"❌ Failed to create user with V1 API: {response.status_code} - {response.text}")
                
                # Try to parse error response
                try:
                    error_data = response.json()
                    logger.error(f"📋 V1 API Error Details: {error_data}")
                except:
                    pass
                
                return {
                    "error": True,
                    "status_code": response.status_code,
                    "response_text": response.text,
                    "api_version": "V1",
                    "url": url
                }
        except Exception as e:
            logger.error(f"❌ Exception creating user with V1 API: {str(e)}")
            return {
                "error": True,
                "exception": str(e),
                "exception_type": e.__class__.__name__,
                "api_version": "V1"
            }
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email address using V1 API (matches create_user endpoint)"""
        try:
            # CORRECTED: Use V1 API base URL and endpoint for user lookup
            v1_base_url = "https://rest.gohighlevel.com"
            url = f"{v1_base_url}/v1/users"
            
            # Use Agency API key for V1 user operations
            if not self.agency_api_key:
                logger.warning("No agency API key available for V1 user lookup")
                return None
                
            v1_headers = {
                "Authorization": f"Bearer {self.agency_api_key}",
                "Content-Type": "application/json"
            }
            
            # V1 API might require different query parameters
            params = {"email": email}
            
            logger.info(f"🔍 V1 User lookup: {url} with email={email}")
            response = requests.get(url, headers=v1_headers, params=params)
            
            logger.info(f"📈 V1 User lookup response: Status={response.status_code}")
            logger.debug(f"📄 V1 User lookup response: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                users = data.get('users', [])
                for user in users:
                    if user.get('email', '').lower() == email.lower():
                        logger.info(f"✅ Found existing V1 user: {user.get('id')}")
                        return user
                logger.info(f"📋 No user found with email {email} in V1 API response")
                return None
            elif response.status_code == 404:
                logger.info(f"📋 V1 User lookup: No users found (404) - this is normal for new vendors")
                return None
            else:
                logger.error(f"❌ Failed to get users from V1 API: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"❌ Error getting user by email from V1 API: {str(e)}")
            return None
    
    def update_user(self, user_id: str, update_data: Dict) -> bool:
        """Update user in GHL"""
        try:
            url = f"{self.base_url}/locations/{self.location_id}/users/{user_id}"
            
            response = self._make_request_with_fallback("PUT", url, json=update_data)
            if response.status_code == 200:
                logger.info(f"Successfully updated user {user_id}")
                return True
            else:
                logger.error(f"Failed to update user: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error updating user: {str(e)}")
            return False
    
    def delete_user(self, user_id: str) -> bool:
        """Delete user from GHL location"""
        try:
            url = f"{self.base_url}/locations/{self.location_id}/users/{user_id}"
            
            response = self._make_request_with_fallback("DELETE", url)
            if response.status_code == 200:
                logger.info(f"Successfully deleted user {user_id}")
                return True
            else:
                logger.error(f"Failed to delete user: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}")
            return False
    
    def test_location_access(self) -> Dict:
        """Test if the token can access the location"""
        try:
            url = f"{self.base_url}/contacts/"
            params = {
                "locationId": self.location_id,
                "limit": 1
            }
            
            response = self._make_request_with_fallback("GET", url, params=params)
            
            return {
                "status_code": response.status_code,
                "can_access": response.status_code == 200,
                "response_text": response.text,
                "location_id": self.location_id,
                "headers_used": self.primary_headers
            }
        except Exception as e:
            return {
                "status_code": None,
                "can_access": False,
                "error": str(e),
                "location_id": self.location_id,
                "headers_used": self.primary_headers
            }
