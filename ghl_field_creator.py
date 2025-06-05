import pandas as pd
import requests
import json
import time
from typing import Dict, List, Optional

class GoHighLevelFieldCreator:
    def __init__(self, private_token: str, location_id: str):
        """
        Initialize the GHL API client with Private Integration Token
        
        Args:
            private_token: Private Integration Token
            location_id: The location/sub-account ID
        """
        self.private_token = private_token
        self.location_id = location_id
        self.base_url = "https://services.leadconnectorhq.com"
        
        # Headers for Private Integration Token
        self.headers = {
            "Authorization": f"Bearer {private_token}",
            "Content-Type": "application/json",
            "Version": "2021-07-28"
        }
        
        # Cache for folder IDs
        self.vendor_folder_id = None
        self.default_folder_id = None
    
    def get_existing_custom_fields(self) -> Dict:
        """Get all existing custom fields and folders"""
        try:
            url = f"{self.base_url}/locations/{self.location_id}/customFields"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                fields = data.get('customFields', [])
                
                # Find folder IDs
                for field in fields:
                    if field.get('name') == 'Vendor Contacts' and field.get('documentType') == 'folder':
                        self.vendor_folder_id = field.get('id')
                    elif field.get('documentType') == 'folder' and not self.default_folder_id:
                        self.default_folder_id = field.get('id')
                
                print(f"📋 Found {len(fields)} existing custom fields")
                if self.vendor_folder_id:
                    print(f"📁 Found 'Vendor Contacts' folder: {self.vendor_folder_id}")
                else:
                    print("⚠️ 'Vendor Contacts' folder not found - will create vendor fields in default location")
                
                return {"success": True, "fields": fields}
            else:
                print(f"❌ Failed to get custom fields: {response.status_code}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            print(f"❌ Error getting custom fields: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def map_field_type(self, csv_field_type: str) -> str:
        """Map CSV field types to GHL API field types - Simplified for data storage"""
        mapping = {
            "Single Line": "TEXT",
            "Multi Line": "LARGE_TEXT", 
            "Number": "NUMERICAL",
            "Date Picker": "DATE",
            # Convert dropdown types to text for simple data storage
            "Dropdown (Single)": "TEXT",
            "Dropdown (Multiple)": "LARGE_TEXT",  # Multi-line for multiple selections
            "Checkbox": "TEXT",  # Store "Yes"/"No" as text
            "Radio": "TEXT"
        }
        return mapping.get(csv_field_type, "TEXT")
    
    def extract_api_name(self, merge_token: str) -> str:
        """Extract the API name from merge token"""
        if not merge_token:
            return ""
        
        try:
            clean_token = merge_token.replace("{{", "").replace("}}", "").strip()
            parts = clean_token.split(".")
            if len(parts) >= 2:
                return parts[1]
        except:
            pass
        
        return ""
    
    def parse_options(self, options_str: str) -> List[str]:
        """Parse field options from CSV string"""
        if not options_str or options_str.lower() in ['text', 'text field']:
            return []
        
        if '"' in options_str:
            options = [opt.strip().strip('"').strip("'") for opt in options_str.split('",')]
            return [opt for opt in options if opt]
        
        if ',' in options_str:
            return [opt.strip() for opt in options_str.split(',') if opt.strip()]
        
        return []
    
    def field_exists(self, field_name: str, existing_fields: List[Dict]) -> bool:
        """Check if a field with the given name already exists"""
        for field in existing_fields:
            if field.get('name') == field_name and field.get('documentType') == 'field':
                return True
        return False
    
    def create_custom_field(self, field_data: Dict, existing_fields: List[Dict]) -> Dict:
        """Create a single custom field"""
        field_name = field_data["Label / Field Name"]
        field_type = self.map_field_type(field_data["GHL Field Type to Select"])
        api_name = self.extract_api_name(field_data["Merge Token (Unique Key)"])
        options = self.parse_options(field_data.get("Field Values/Options", ""))
        
        # Determine field type first (needed for conflict checking)
        merge_token = field_data["Merge Token (Unique Key)"]
        is_vendor_field = "vendor.sp_" in merge_token or "contact.sp_" in merge_token
        
        # Handle field name conflicts
        if field_name == "Company Name":
            field_name = "Vendor Company Name"
            print(f"🔄 Renamed 'Company Name' to 'Vendor Company Name' to avoid conflict")
        elif field_name == "Preferred Contact Method" and is_vendor_field:
            field_name = "Vendor Preferred Contact Method"
            print(f"🔄 Renamed vendor 'Preferred Contact Method' to 'Vendor Preferred Contact Method' to avoid conflict")
        
        # Check if field already exists
        if self.field_exists(field_name, existing_fields):
            print(f"⏭️ Skipping {field_name} - already exists")
            return {"success": True, "field": field_name, "skipped": True}
        
        # Create the payload
        payload = {
            "name": field_name,
            "dataType": field_type,
            "model": "contact"
        }
        
        # Add parent folder for vendor fields
        if is_vendor_field and self.vendor_folder_id:
            payload["parentId"] = self.vendor_folder_id
        
        # Add placeholder for text fields (now all fields are text-based)
        if field_type in ["TEXT", "LARGE_TEXT"]:
            # Create helpful placeholders for converted dropdown fields
            original_type = field_data["GHL Field Type to Select"]
            if "Dropdown" in original_type and options:
                # Show first few options as examples
                example_options = options[:3] if len(options) >= 3 else options
                if len(options) > 3:
                    placeholder = f"e.g., {', '.join(example_options)}, etc."
                else:
                    placeholder = f"e.g., {', '.join(example_options)}"
                payload["placeholder"] = placeholder
            elif "Checkbox" in original_type:
                payload["placeholder"] = "Yes/No"
            else:
                payload["placeholder"] = f"Enter {field_name.lower()}"
        
        # No dropdown option logic needed - everything is now simple text storage
        
        field_category = "VENDOR" if is_vendor_field else "CLIENT"
        original_type = field_data["GHL Field Type to Select"]
        print(f"Creating {field_category} field: {field_name}")
        print(f"  Original: {original_type} → Simplified: {field_type}")
        if options and "Dropdown" in original_type:
            print(f"  Will store options as text: {options[:3]}{'...' if len(options) > 3 else ''}")
        
        try:
            url = f"{self.base_url}/locations/{self.location_id}/customFields"
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code == 201:
                print(f"✅ Successfully created: {field_name}")
                return {"success": True, "field": field_name, "data": response.json()}
            else:
                print(f"❌ Failed to create {field_name}: {response.status_code}")
                print(f"   Response: {response.text}")
                return {"success": False, "field": field_name, "error": response.text}
                
        except Exception as e:
            print(f"❌ Error creating {field_name}: {str(e)}")
            return {"success": False, "field": field_name, "error": str(e)}
    
    def process_csv_file(self, csv_file_path: str, delay_seconds: float = 1.5):
        """Process the CSV file and create all custom fields"""
        try:
            # Get existing fields first
            existing_result = self.get_existing_custom_fields()
            if not existing_result["success"]:
                return {"error": "Failed to get existing custom fields"}
            
            existing_fields = existing_result["fields"]
            
            # Read CSV file
            df = pd.read_csv(csv_file_path, encoding='cp1252')
            print(f"📄 Loaded {len(df)} rows from CSV")
            
            # Filter fields to create (exclude built-in and do-not-create fields)
            fields_to_create = df[
                (df["GHL Field Type to Select"].notna()) &
                (~df["GHL Field Type to Select"].str.contains("Built", na=False)) &
                (~df["Notes"].str.contains("do NOT create", na=False))
            ]
            
            print(f"🎯 Found {len(fields_to_create)} fields to create")
            
            # Separate client and vendor fields
            client_fields = fields_to_create[
                fields_to_create["Merge Token (Unique Key)"].str.contains("contact.cl_", na=False)
            ]
            
            vendor_fields = fields_to_create[
                (fields_to_create["Merge Token (Unique Key)"].str.contains("vendor.sp_", na=False)) |
                (fields_to_create["Merge Token (Unique Key)"].str.contains("contact.sp_", na=False))
            ]
            
            print(f"👥 Client fields (cl_): {len(client_fields)}")
            print(f"🏢 Vendor fields (sp_): {len(vendor_fields)}")
            
            results = {
                "client_fields": [],
                "vendor_fields": [],
                "success_count": 0,
                "error_count": 0,
                "skipped_count": 0
            }
            
            # Create client fields
            print("\n🔄 Creating CLIENT fields...")
            for _, field in client_fields.iterrows():
                result = self.create_custom_field(field.to_dict(), existing_fields)
                results["client_fields"].append(result)
                
                if result["success"]:
                    if result.get("skipped"):
                        results["skipped_count"] += 1
                    else:
                        results["success_count"] += 1
                else:
                    results["error_count"] += 1
                
                time.sleep(delay_seconds)  # Rate limiting
            
            # Create vendor fields  
            print(f"\n🔄 Creating VENDOR fields...")
            if self.vendor_folder_id:
                print(f"📁 Placing vendor fields in 'Vendor Contacts' folder")
            else:
                print(f"📁 Placing vendor fields in default location")
                
            for _, field in vendor_fields.iterrows():
                result = self.create_custom_field(field.to_dict(), existing_fields)
                results["vendor_fields"].append(result)
                
                if result["success"]:
                    if result.get("skipped"):
                        results["skipped_count"] += 1
                    else:
                        results["success_count"] += 1
                else:
                    results["error_count"] += 1
                    
                time.sleep(delay_seconds)  # Rate limiting
            
            # Summary
            print(f"\n📊 SUMMARY:")
            print(f"✅ Successfully created: {results['success_count']} fields")
            print(f"⏭️ Skipped (already exist): {results['skipped_count']} fields")
            print(f"❌ Failed to create: {results['error_count']} fields")
            
            return results
            
        except Exception as e:
            print(f"❌ Error processing CSV: {str(e)}")
            return {"error": str(e)}

def main():
    """Main function to run the field creator"""
    
    # Configuration - Using the working Private Integration Token
    PRIVATE_TOKEN = "pit-c361d89c-d943-4812-9839-8e3223c2f31a"
    LOCATION_ID = "ilmrtA1Vk6rvcy4BswKg"
    CSV_FILE_PATH = "Custom Fileds DSP.csv"
    
    # Validate configuration
    if not PRIVATE_TOKEN or not LOCATION_ID:
        print("❌ Missing API credentials!")
        return
    
    # Create the field creator instance
    creator = GoHighLevelFieldCreator(PRIVATE_TOKEN, LOCATION_ID)
    
    # Process the CSV file
    print("🚀 Starting GoHighLevel Custom Field Creation...")
    print(f"📁 CSV File: {CSV_FILE_PATH}")
    print(f"🎯 Location: DIGITAL MARINE LLC ({LOCATION_ID})")
    print(f"🔑 Using: Private Integration Token")
    print("-" * 60)
    
    results = creator.process_csv_file(CSV_FILE_PATH, delay_seconds=1.5)
    
    if "error" not in results:
        print("\n🎉 Process completed!")
        
        # Save results to JSON file for review
        with open("field_creation_results.json", "w") as f:
            json.dump(results, f, indent=2)
        print("📄 Results saved to: field_creation_results.json")
        
        print("\n💡 All dropdown fields have been converted to text fields for simple data storage!")
        print("   This is perfect for storing form submissions from your WordPress site.")
    else:
        print(f"\n💥 Process failed: {results['error']}")

if __name__ == "__main__":
    main()