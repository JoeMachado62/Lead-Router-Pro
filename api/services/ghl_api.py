import requests
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class GoHighLevelAPI:
    """Enhanced GHL API client for multi-tenant operations"""
    
    def __init__(self, api_key: Optional[str] = None, private_token: Optional[str] = None, location_id: Optional[str] = None, agency_api_key: Optional[str] = None):
        # Support both new API key and legacy PIT token
        self.api_key = api_key
        self.private_token = private_token
        self.agency_api_key = agency_api_key
        self.location_id = location_id
        self.base_url = "https://services.leadconnectorhq.com"
        
        # Use API key if available, otherwise fall back to PIT token
        if api_key:
            self.headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Version": "2021-07-28"
            }
        elif private_token:
            self.headers = {
                "Authorization": f"Bearer {private_token}",
                "Content-Type": "application/json",
                "Version": "2021-07-28"
            }
        else:
            raise ValueError("Either api_key or private_token must be provided")
        
        # Agency API headers for user management operations
        if agency_api_key:
            self.agency_headers = {
                "Authorization": f"Bearer {agency_api_key}",
                "Content-Type": "application/json",
                "Version": "2021-07-28"
            }
        else:
            self.agency_headers = None
    
    def search_contacts(self, query: str = "", limit: int = 100) -> List[Dict]:
        """Search contacts in GHL"""
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
            
            response = requests.get(url, headers=self.headers, params=params)
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
        """Get contact details by ID"""
        try:
            url = f"{self.base_url}/contacts/{contact_id}"
            response = requests.get(url, headers=self.headers)
            
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
        """Create a new contact in GHL"""
        try:
            url = f"{self.base_url}/contacts/"
            payload = {
                "locationId": self.location_id,
                **contact_data
            }
            
            logger.debug(f"Final GHL payload: {payload}")
            
            response = requests.post(url, headers=self.headers, json=payload)
            if response.status_code == 201:
                data = response.json()
                return data.get('contact', {})
            else:
                logger.error(f"Failed to create contact: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error creating contact: {str(e)}")
            return None
    
    def update_contact(self, contact_id: str, update_data: Dict) -> bool:
        """Update contact in GHL"""
        try:
            url = f"{self.base_url}/contacts/{contact_id}"
            
            logger.debug(f"Updating contact {contact_id} with payload: {update_data}")
            
            response = requests.put(url, headers=self.headers, json=update_data)
            
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
        """Create opportunity in GHL"""
        try:
            url = f"{self.base_url}/opportunities/"
            response = requests.post(url, headers=self.headers, json=opportunity_data)
            
            if response.status_code == 201:
                data = response.json()
                return data.get('opportunity', {})
            else:
                logger.error(f"Failed to create opportunity: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error creating opportunity: {str(e)}")
            return None
    
    def get_pipelines(self) -> List[Dict]:
        """Get all pipelines for the location"""
        try:
            url = f"{self.base_url}/opportunities/pipelines"
            params = {"locationId": self.location_id}
            
            response = requests.get(url, headers=self.headers, params=params)
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
            
            response = requests.get(url, headers=self.headers)
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
            
            response = requests.post(url, headers=self.headers, json=payload)
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
            
            response = requests.post(url, headers=self.headers, json=payload)
            if response.status_code == 201:
                return True
            else:
                logger.error(f"Failed to send email: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False
    
    def create_user(self, user_data: Dict) -> Optional[Dict]:
        """Create a new user in GHL location using Agency API"""
        try:
            if not self.agency_headers:
                logger.error("Agency API key required for user creation")
                return None
            
            # Use Agency API endpoint for user creation
            url = f"{self.base_url}/locations/{self.location_id}/users"
            
            # Required fields for user creation
            payload = {
                "firstName": user_data.get("firstName"),
                "lastName": user_data.get("lastName"), 
                "email": user_data.get("email"),
                "phone": user_data.get("phone", ""),
                "type": user_data.get("type", "user"),  # user, admin, agency
                "role": user_data.get("role", "user"),  # user, admin, agency
                "permissions": user_data.get("permissions", {
                    "campaignsEnabled": True,
                    "campaignsReadOnly": False,
                    "contactsEnabled": True,
                    "workflowsEnabled": True,
                    "triggersEnabled": True,
                    "funnelsEnabled": True,
                    "websitesEnabled": True,
                    "opportunitiesEnabled": True,
                    "dashboardStatsEnabled": True,
                    "bulkRequestsEnabled": False,
                    "appointmentEnabled": True,
                    "reviewsEnabled": True,
                    "onlineListingsEnabled": True,
                    "phoneCallEnabled": True,
                    "conversationsEnabled": True,
                    "assignedDataOnly": False,
                    "adwordsReportingEnabled": True,
                    "membershipEnabled": True,
                    "facebookAdsReportingEnabled": True,
                    "attributionsReportingEnabled": True,
                    "settingsEnabled": False,
                    "tagsEnabled": True,
                    "leadValueEnabled": True,
                    "marketingEnabled": True,
                    "agentReportingEnabled": True,
                    "botService": True,
                    "socialPlanner": True,
                    "bloggingEnabled": True,
                    "invoiceEnabled": True,
                    "affiliateManagerEnabled": False,
                    "contentAiEnabled": True,
                    "refundsEnabled": False,
                    "recordPaymentEnabled": True,
                    "cancelSubscriptionEnabled": False,
                    "paymentsEnabled": True,
                    "communitiesEnabled": False,
                    "exportPaymentsEnabled": False
                })
            }
            
            logger.debug(f"Creating GHL user with Agency API. Payload: {payload}")
            
            # Use Agency API headers for user creation
            response = requests.post(url, headers=self.agency_headers, json=payload)
            if response.status_code == 201:
                data = response.json()
                logger.info(f"Successfully created GHL user with Agency API: {data.get('user', {}).get('id')}")
                return data.get('user', {})
            else:
                logger.error(f"Failed to create user with Agency API: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error creating user with Agency API: {str(e)}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email address"""
        try:
            url = f"{self.base_url}/locations/{self.location_id}/users"
            params = {"email": email}
            
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                data = response.json()
                users = data.get('users', [])
                for user in users:
                    if user.get('email', '').lower() == email.lower():
                        return user
                return None
            else:
                logger.error(f"Failed to get users: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error getting user by email: {str(e)}")
            return None
    
    def update_user(self, user_id: str, update_data: Dict) -> bool:
        """Update user in GHL"""
        try:
            url = f"{self.base_url}/locations/{self.location_id}/users/{user_id}"
            
            response = requests.put(url, headers=self.headers, json=update_data)
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
            
            response = requests.delete(url, headers=self.headers)
            if response.status_code == 200:
                logger.info(f"Successfully deleted user {user_id}")
                return True
            else:
                logger.error(f"Failed to delete user: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}")
            return False
