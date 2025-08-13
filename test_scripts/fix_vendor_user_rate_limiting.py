#!/usr/bin/env python3
"""
Fix for vendor user creation rate limiting and error handling
This script adds rate limiting to prevent overwhelming the GHL API
and improves error logging for debugging failed updates
"""

import time
import asyncio
from datetime import datetime, timedelta
from collections import deque

# Configuration
RATE_LIMIT_WINDOW = 60  # seconds
MAX_REQUESTS_PER_WINDOW = 20  # max vendor user creations per minute
REQUEST_DELAY = 3.0  # minimum seconds between requests

class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = deque()
    
    async def acquire(self):
        """Wait if necessary to respect rate limits"""
        now = datetime.now()
        
        # Remove old requests outside the window
        while self.requests and (now - self.requests[0]).total_seconds() > self.window_seconds:
            self.requests.popleft()
        
        # If at limit, wait until the oldest request expires
        if len(self.requests) >= self.max_requests:
            oldest = self.requests[0]
            wait_time = self.window_seconds - (now - oldest).total_seconds() + 0.1
            if wait_time > 0:
                print(f"⏳ Rate limit reached. Waiting {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)
                # Recursive call to recheck after waiting
                return await self.acquire()
        
        # Add this request to the queue
        self.requests.append(now)
        return True

# Create global rate limiter instance
vendor_creation_limiter = RateLimiter(MAX_REQUESTS_PER_WINDOW, RATE_LIMIT_WINDOW)

def get_webhook_update_code():
    """Returns the updated webhook code with rate limiting"""
    return '''
# Add these imports at the top of webhook_routes.py
from collections import deque
from datetime import datetime, timedelta

# Add rate limiter configuration after imports
class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = deque()
    
    async def acquire(self):
        """Wait if necessary to respect rate limits"""
        now = datetime.now()
        
        # Remove old requests outside the window
        while self.requests and (now - self.requests[0]).total_seconds() > self.window_seconds:
            self.requests.popleft()
        
        # If at limit, wait until the oldest request expires
        if len(self.requests) >= self.max_requests:
            oldest = self.requests[0]
            wait_time = self.window_seconds - (now - oldest).total_seconds() + 0.1
            if wait_time > 0:
                logger.info(f"⏳ Rate limit reached. Waiting {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)
                return await self.acquire()
        
        # Add this request to the queue
        self.requests.append(now)
        return True

# Create rate limiter for vendor creation (20 per minute)
vendor_creation_limiter = RateLimiter(max_requests=20, window_seconds=60)

# Then update the webhook handler to use the rate limiter:

@router.post("/ghl/vendor-user-creation")
async def handle_vendor_user_creation_webhook(request: Request):
    """
    Legacy webhook endpoint for GHL workflow to trigger vendor user creation.
    Direct processing only - NO AI.
    Now with rate limiting to prevent overwhelming GHL API.
    """
    start_time = time.time()
    
    # Apply rate limiting
    await vendor_creation_limiter.acquire()
    
    # Add minimum delay between requests
    await asyncio.sleep(3.0)  # 3 second minimum between vendor creations
    
    # Rest of the webhook code continues...
'''

def get_improved_error_logging():
    """Returns improved error logging code"""
    return '''
# Update the error logging section around line 2240 to capture more details:

except Exception as e:
    logger.error(f"❌ Failed to link vendor with GHL User ID: {str(e)}")
    logger.error(f"   Vendor Email: {vendor_email}")
    logger.error(f"   Account ID: {account_id if 'account_id' in locals() else 'Not set'}")
    logger.error(f"   User ID: {user_id}")
    logger.error(f"   Exception Type: {type(e).__name__}")
    
    # Log to activity log with full details
    simple_db_instance.log_activity(
        event_type="vendor_user_update_failed",
        event_data={
            "vendor_email": vendor_email,
            "user_id": user_id,
            "error": str(e),
            "error_type": type(e).__name__,
            "account_id": account_id if 'account_id' in locals() else None
        },
        success=False,
        error_message=str(e)
    )
    # Don't fail the webhook - the user was created successfully
'''

def get_batch_processing_script():
    """Returns a script to safely process vendors missing GHL user IDs"""
    return '''#!/usr/bin/env python3
"""
Batch process vendors that are missing GHL User IDs
This script safely processes vendors one at a time with proper delays
"""

import time
import sqlite3
from datetime import datetime
from api.services.ghl_api import GoHighLevelAPI
from config import AppConfig
from database.simple_connection import Database

def process_vendors_missing_user_ids():
    """Process vendors that don't have GHL user IDs"""
    
    # Initialize database
    db = Database()
    
    # Get vendors without GHL user IDs
    conn = sqlite3.connect('smart_lead_router.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, email, ghl_contact_id, account_id 
        FROM vendors 
        WHERE (ghl_user_id IS NULL OR ghl_user_id = '')
        AND ghl_contact_id IS NOT NULL
        AND email IS NOT NULL
        ORDER BY created_at
    """)
    
    vendors = cursor.fetchall()
    conn.close()
    
    print(f"Found {len(vendors)} vendors without GHL User IDs")
    
    # Initialize GHL API
    ghl_api = GoHighLevelAPI(
        location_api_key=AppConfig.GHL_API_KEY,
        private_token=AppConfig.GHL_PRIVATE_TOKEN,
        location_id=AppConfig.GHL_LOCATION_ID,
        agency_api_key=AppConfig.GHL_AGENCY_API_KEY,
        company_id=AppConfig.COMPANY_ID
    )
    
    processed = 0
    errors = 0
    
    for vendor_id, name, email, ghl_contact_id, account_id in vendors:
        print(f"\\nProcessing vendor: {name} ({email})")
        
        try:
            # Check if user already exists
            existing_user = ghl_api.get_user_by_email(email)
            
            if existing_user:
                user_id = existing_user.get('id')
                print(f"  ✅ Found existing GHL user: {user_id}")
                
                # Update vendor record
                if db.update_vendor_ghl_user_id(vendor_id, user_id):
                    print(f"  ✅ Updated vendor record with GHL User ID")
                    processed += 1
                else:
                    print(f"  ❌ Failed to update vendor record")
                    errors += 1
            else:
                print(f"  ⚠️  No GHL user found for {email}")
                print(f"     Consider triggering the vendor approval workflow for this contact")
                errors += 1
            
            # Rate limiting - wait between requests
            print(f"  ⏳ Waiting 5 seconds before next vendor...")
            time.sleep(5)
            
        except Exception as e:
            print(f"  ❌ Error processing vendor: {str(e)}")
            errors += 1
            continue
    
    print(f"\\n✅ Completed: {processed} vendors updated, {errors} errors")

if __name__ == "__main__":
    process_vendors_missing_user_ids()
'''

if __name__ == "__main__":
    print("=== Vendor User Creation Rate Limiting Fix ===\n")
    
    print("1. Update webhook_routes.py with rate limiting:")
    print("-" * 50)
    print(get_webhook_update_code())
    
    print("\n2. Improve error logging:")
    print("-" * 50)
    print(get_improved_error_logging())
    
    print("\n3. Batch processing script for missing user IDs:")
    print("-" * 50)
    print(get_batch_processing_script())
    
    print("\n=== Implementation Steps ===")
    print("1. Add rate limiting to the vendor user creation webhook")
    print("2. Improve error logging to capture why updates fail")
    print("3. Run the batch processing script to fix existing vendors")
    print("4. Monitor the activity logs for any future failures")