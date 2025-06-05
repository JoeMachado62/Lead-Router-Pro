import pandas as pd
import requests
import json
import time
from typing import Dict, List, Optional

class GoHighLevelFieldUpdater:
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
        
        # Track field mappings for CSV update
        self.field_mappings = {}
        
    def get_all_custom_fields(self) -> Dict:
        """Get all existing custom fields with their GHL-generated keys"""
        try:
            url = f"{self.base_url}/locations/{self.location_id}/customFields"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                fields = data.get('customFields', [])
                
                print(f"📋 Found {len(fields)} total custom fields")
                
                # Extract field data for mapping
                field_data = {}
                for field in fields:
                    if field.get('documentType') == 'field':
                        field_name = field.get('name')
                        field_key = field.get('fieldKey')
                        field_id = field.get('id')
                        
                        field_data[field_name] = {
                            'fieldKey': field_key,
                            'id': field_id,
                            'dataType': field.get('dataType', ''),
                            'model': field.get('model', '')
                        }
                
                print(f"🔑 Found {len(field_data)} actual fields (excluding folders)")
                return {"success": True, "fields": field_data}
            else:
                print(f"❌ Failed to get custom fields: {response.status_code}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            print(f"❌ Error getting custom fields: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def normalize_field_name(self, name: str) -> str:
        """Normalize field names for matching (handle renamed fields)"""
        # Handle the renamed fields
        if name == "Company Name":
            return "Vendor Company Name"
        elif name == "Preferred Contact Method":
            # This is tricky - we need to check context to know if it's vendor or client
            return name  # Will handle in matching logic
        return name
    
    def find_matching_field(self, csv_field_name: str, merge_token: str, ghl_fields: Dict) -> Optional[Dict]:
        """Find the matching GHL field for a CSV row"""
        
        # Handle NaN/None values
        if pd.isna(csv_field_name) or pd.isna(merge_token):
            return None
        
        # Convert to string to handle any float values
        csv_field_name = str(csv_field_name).strip()
        merge_token = str(merge_token).strip()
        
        # Handle special cases for renamed fields
        normalized_name = self.normalize_field_name(csv_field_name)
        
        # For "Preferred Contact Method", check if it's vendor field
        if csv_field_name == "Preferred Contact Method":
            is_vendor = "vendor.sp_" in merge_token or "contact.sp_" in merge_token
            if is_vendor:
                normalized_name = "Vendor Preferred Contact Method"
        
        # Direct name match
        if normalized_name in ghl_fields:
            return ghl_fields[normalized_name]
        
        # Fuzzy matching for slight differences
        for ghl_name, ghl_data in ghl_fields.items():
            if csv_field_name.lower().replace(" ", "") == ghl_name.lower().replace(" ", ""):
                return ghl_data
        
        return None
    
    def update_csv_with_field_keys(self, csv_file_path: str, output_path: str = None):
        """Update the CSV file with actual GHL field keys"""
        
        if output_path is None:
            output_path = csv_file_path.replace('.csv', '_updated.csv')
        
        try:
            # Get all GHL fields
            fields_result = self.get_all_custom_fields()
            if not fields_result["success"]:
                return {"error": "Failed to get GHL fields"}
            
            ghl_fields = fields_result["fields"]
            
            # Read CSV file
            df = pd.read_csv(csv_file_path, encoding='cp1252')
            print(f"📄 Loaded {len(df)} rows from CSV")
            
            # Track updates
            updates = {
                "matched": 0,
                "not_found": 0,
                "built_in": 0,
                "do_not_create": 0,
                "updated_rows": []
            }
            
            # Process each row
            for index, row in df.iterrows():
                field_name = row["Label / Field Name"]
                field_type = row["GHL Field Type to Select"]
                merge_token = row["Merge Token (Unique Key)"]
                notes = row.get("Notes", "")
                
                # Handle NaN/None values by converting to strings
                field_name = str(field_name).strip() if pd.notna(field_name) else ""
                field_type = str(field_type).strip() if pd.notna(field_type) else ""
                merge_token = str(merge_token).strip() if pd.notna(merge_token) else ""
                notes = str(notes).strip() if pd.notna(notes) else ""
                
                # Skip empty rows
                if not field_name or field_name == "nan":
                    continue
                
                # Skip built-in fields
                if "Built" in field_type:
                    updates["built_in"] += 1
                    print(f"⏭️ Skipping built-in field: {field_name}")
                    continue
                
                # Skip do-not-create fields
                if "do NOT create" in notes:
                    updates["do_not_create"] += 1
                    print(f"⏭️ Skipping do-not-create field: {field_name}")
                    continue
                
                # Find matching GHL field
                ghl_field = self.find_matching_field(field_name, merge_token, ghl_fields)
                
                if ghl_field:
                    # Update the merge token with actual GHL field key
                    old_token = merge_token
                    
                    # Determine prefix based on original token
                    if "contact.cl_" in merge_token:
                        new_token = f"{{{{ contact.{ghl_field['fieldKey']} }}}}"
                    elif "vendor.sp_" in merge_token or "contact.sp_" in merge_token:
                        new_token = f"{{{{ contact.{ghl_field['fieldKey']} }}}}"
                    else:
                        new_token = f"{{{{ contact.{ghl_field['fieldKey']} }}}}"
                    
                    # Update the dataframe
                    df.at[index, "Merge Token (Unique Key)"] = new_token
                    
                    updates["matched"] += 1
                    updates["updated_rows"].append({
                        "field_name": field_name,
                        "old_token": old_token,
                        "new_token": new_token,
                        "ghl_field_key": ghl_field['fieldKey'],
                        "ghl_field_id": ghl_field['id']
                    })
                    
                    print(f"✅ Updated {field_name}")
                    print(f"   Old: {old_token}")
                    print(f"   New: {new_token}")
                    
                else:
                    updates["not_found"] += 1
                    print(f"❌ Could not find GHL field for: {field_name}")
            
            # Save updated CSV
            df.to_csv(output_path, index=False, encoding='cp1252')
            
            # Summary
            print(f"\n📊 UPDATE SUMMARY:")
            print(f"✅ Successfully updated: {updates['matched']} fields")
            print(f"⏭️ Skipped (built-in): {updates['built_in']} fields")
            print(f"⏭️ Skipped (do not create): {updates['do_not_create']} fields")
            print(f"❌ Not found in GHL: {updates['not_found']} fields")
            print(f"📄 Updated CSV saved to: {output_path}")
            
            return {
                "success": True,
                "updates": updates,
                "output_file": output_path
            }
            
        except Exception as e:
            print(f"❌ Error updating CSV: {str(e)}")
            return {"error": str(e)}
    
    def create_field_reference_json(self, csv_file_path: str, output_path: str = "field_reference.json"):
        """Create a JSON reference file with all field mappings"""
        
        try:
            # Get all GHL fields
            fields_result = self.get_all_custom_fields()
            if not fields_result["success"]:
                return {"error": "Failed to get GHL fields"}
            
            ghl_fields = fields_result["fields"]
            
            # Read CSV file
            df = pd.read_csv(csv_file_path, encoding='cp1252')
            
            # Create comprehensive reference
            field_reference = {
                "client_fields": {},
                "vendor_fields": {},
                "all_ghl_fields": ghl_fields,
                "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Process each CSV row
            for _, row in df.iterrows():
                field_name = row["Label / Field Name"]
                merge_token = row["Merge Token (Unique Key)"]
                field_type = row["GHL Field Type to Select"]
                
                # Skip built-in and do-not-create fields
                if "Built" in str(field_type) or "do NOT create" in str(row.get("Notes", "")):
                    continue
                
                # Find matching GHL field
                ghl_field = self.find_matching_field(field_name, merge_token, ghl_fields)
                
                if ghl_field:
                    field_info = {
                        "csv_name": field_name,
                        "ghl_name": field_name if field_name in ghl_fields else self.normalize_field_name(field_name),
                        "ghl_field_key": ghl_field['fieldKey'],
                        "ghl_field_id": ghl_field['id'],
                        "data_type": ghl_field['dataType'],
                        "merge_token": f"{{{{ contact.{ghl_field['fieldKey']} }}}}",
                        "original_csv_token": merge_token
                    }
                    
                    # Categorize by client/vendor
                    if "contact.cl_" in str(merge_token):
                        field_reference["client_fields"][field_name] = field_info
                    elif "vendor.sp_" in str(merge_token) or "contact.sp_" in str(merge_token):
                        field_reference["vendor_fields"][field_name] = field_info
            
            # Save reference file
            with open(output_path, 'w') as f:
                json.dump(field_reference, f, indent=2)
            
            print(f"📄 Field reference saved to: {output_path}")
            return {"success": True, "reference_file": output_path}
            
        except Exception as e:
            print(f"❌ Error creating field reference: {str(e)}")
            return {"error": str(e)}

def main():
    """Main function to run the field updater"""
    
    # Configuration
    PRIVATE_TOKEN = "pit-c361d89c-d943-4812-9839-8e3223c2f31a"
    LOCATION_ID = "ilmrtA1Vk6rvcy4BswKg"
    CSV_FILE_PATH = "Custom Fileds DSP.csv"
    UPDATED_CSV_PATH = "Custom_Fields_DSP_Updated.csv"
    
    # Validate configuration
    if not PRIVATE_TOKEN or not LOCATION_ID:
        print("❌ Missing API credentials!")
        return
    
    # Create the field updater instance
    updater = GoHighLevelFieldUpdater(PRIVATE_TOKEN, LOCATION_ID)
    
    print("🚀 Starting GoHighLevel Field Key Update Process...")
    print(f"📁 CSV File: {CSV_FILE_PATH}")
    print(f"🎯 Location: DIGITAL MARINE LLC ({LOCATION_ID})")
    print(f"🔑 Using: Private Integration Token")
    print("-" * 60)
    
    # Update CSV with actual field keys
    print("\n🔄 Step 1: Updating CSV with GHL field keys...")
    update_result = updater.update_csv_with_field_keys(CSV_FILE_PATH, UPDATED_CSV_PATH)
    
    if update_result.get("success"):
        print(f"\n✅ CSV successfully updated!")
        
        # Create comprehensive field reference
        print("\n🔄 Step 2: Creating field reference JSON...")
        reference_result = updater.create_field_reference_json(UPDATED_CSV_PATH)
        
        if reference_result.get("success"):
            print(f"\n🎉 Process completed successfully!")
            print(f"\n📋 Files created:")
            print(f"   • Updated CSV: {UPDATED_CSV_PATH}")
            print(f"   • Field Reference: field_reference.json")
            print(f"\n💡 You can now use the updated merge tokens in your AI automations!")
        else:
            print(f"\n⚠️ CSV updated but failed to create reference: {reference_result.get('error')}")
    else:
        print(f"\n💥 Process failed: {update_result.get('error')}")

if __name__ == "__main__":
    main()