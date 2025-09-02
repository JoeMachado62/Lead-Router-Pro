#!/usr/bin/env python3
"""
Script to clean up webhook_routes.py by removing duplicate service definitions
"""

with open('/root/Lead-Router-Pro/api/routes/webhook_routes.py', 'r') as f:
    lines = f.readlines()

# Find the start and end of the duplicate section
start_line = None
end_line = None

for i, line in enumerate(lines):
    if '# --- CORRECT SERVICE CATEGORIES AND SERVICES FROM CSV ---' in line:
        start_line = i
    if start_line and 'async def parse_webhook_payload(request: Request)' in line and i > start_line:
        end_line = i
        break

if start_line and end_line:
    print(f"Found duplicate section from line {start_line+1} to {end_line}")
    
    # Create new content
    new_lines = lines[:start_line]
    new_lines.append('\n')
    new_lines.append('# Service mappings have been moved to api.services.service_mapper\n')
    new_lines.append('# The duplicate inline definitions have been removed for better modularity\n')
    new_lines.append('\n')
    new_lines.extend(lines[end_line:])
    
    # Write back
    with open('/root/Lead-Router-Pro/api/routes/webhook_routes.py', 'w') as f:
        f.writelines(new_lines)
    
    print(f"Removed {end_line - start_line} lines of duplicate code")
else:
    print("Could not find the duplicate section")