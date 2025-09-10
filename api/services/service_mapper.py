"""
Service Mapper Module - REDIRECTS TO service_categories.py
===========================================================
This module now acts as a compatibility layer, redirecting all functionality
to the centralized service_categories.py module.

All service data is now maintained in service_categories.py as the single source of truth.
"""

import logging
from typing import Optional, List, Dict

# Import everything from the centralized service_categories module
from api.services.service_categories import (
    SERVICE_CATEGORIES,
    LEVEL_3_SERVICES,
    get_direct_service_category,
    get_specific_service,
    find_matching_service,
    DOCKSIDE_PROS_CATEGORIES,
    DOCKSIDE_PROS_SERVICES,
    service_manager
)

logger = logging.getLogger(__name__)

# Log that we're using the redirected version
logger.info("✅ service_mapper.py is now redirecting to service_categories.py (single source of truth)")

# ============================================================================
# BACKWARD COMPATIBILITY EXPORTS
# These maintain the same interface as the original service_mapper.py
# ============================================================================

# Re-export the main function with its original name
get_service_category = get_direct_service_category

# Additional specific form mappings for exact backward compatibility
FORM_TO_SPECIFIC_SERVICE = {
    "boat-detailing": "Boat Detailing",
    "bottom-painting": "Bottom Painting",
    "ceramic-coating": "Ceramic Coating",
    "oil-change": "Oil Change",
    "bilge-cleaning": "Bilge Cleaning",
    "jet-ski-maintenance": "Jet Ski Maintenance",
    "barnacle-cleaning": "Barnacle Cleaning",
    "yacht-fire-detection": "Fire and Safety Equipment and Services",
    "boat-wrapping": "Boat Wrapping and Marine Protection Film",
    "marine-protection-film": "Boat Wrapping and Marine Protection Film",
    "fiberglass-repair": "Fiberglass Repair",
    "welding-fabrication": "Welding & Metal Fabrication",
    "carpentry-woodwork": "Carpentry & Woodwork",
    "riggers-masts": "Riggers & Masts",
    "jet-ski-repair": "Jet Ski Repair",
    "boat-canvas-upholstery": "Boat Canvas and Upholstery",
    "boat-decking": "Boat Decking and Yacht Flooring",
    "yacht-flooring": "Boat Decking and Yacht Flooring",
}

def get_direct_service_category_with_logging(form_identifier: str) -> str:
    """
    Wrapper that adds specific logging for debugging.
    Calls the centralized function from service_categories.py
    """
    logger.debug(f"🔍 Looking up category for form identifier: {form_identifier}")
    result = get_direct_service_category(form_identifier)
    logger.debug(f"✅ Mapped '{form_identifier}' → '{result}'")
    return result

# Optional: Override if you need the logging version
# get_service_category = get_direct_service_category_with_logging

# ============================================================================
# DEPRECATED NOTICE
# ============================================================================
def deprecated_notice():
    """
    This function is called to notify that service_mapper.py is deprecated.
    All functionality has been moved to service_categories.py
    """
    logger.warning(
        "⚠️ DEPRECATED: service_mapper.py is now a redirect layer. "
        "Please update your imports to use api.services.service_categories directly."
    )

# Log the deprecation notice on module import (commented out to avoid spam)
# deprecated_notice()

# ============================================================================
# MODULE EXPORTS
# Maintaining exact same exports as original for backward compatibility
# ============================================================================

__all__ = [
    'get_service_category',
    'get_direct_service_category',
    'get_specific_service',
    'find_matching_service',
    'DOCKSIDE_PROS_CATEGORIES',
    'DOCKSIDE_PROS_SERVICES',
    'FORM_TO_SPECIFIC_SERVICE',
    'SERVICE_CATEGORIES',
    'LEVEL_3_SERVICES'
]