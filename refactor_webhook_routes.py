#!/usr/bin/env python3
"""
Refactor webhook_routes.py to remove duplicate service mapping code
"""

import re

# Read the file
with open('/root/Lead-Router-Pro/api/routes/webhook_routes.py', 'r') as f:
    content = f.read()

# Remove the function definitions that are now in service_mapper
# These are between lines 461-779 approximately

# Pattern to match the three functions we want to remove
patterns_to_remove = [
    r'def get_direct_service_category\(form_identifier: str\) -> str:.*?(?=\n(?:def |async def |class |\n# |\nif __name__|$))',
    r'def get_specific_service_from_form\(form_identifier: str\) -> str:.*?(?=\n(?:def |async def |class |\n# |\nif __name__|$))',
    r'def find_matching_service\(specific_service_text: str\) -> str:.*?(?=\n(?:def |async def |class |\n# |\nif __name__|$))'
]

for pattern in patterns_to_remove:
    content = re.sub(pattern, '', content, flags=re.DOTALL)

# Clean up any multiple blank lines
content = re.sub(r'\n\n\n+', '\n\n', content)

# Write back
with open('/root/Lead-Router-Pro/api/routes/webhook_routes.py.cleaned', 'w') as f:
    f.write(content)

print("Created cleaned version at webhook_routes.py.cleaned")
print("Please review before replacing the original")