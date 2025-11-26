"""
Location confirmation utility for smart chat location feature.

Provides keyword detection for location confirmation and helper functions
for location formatting and merging.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


# Confirmation keywords in Hindi and English
CONFIRMATION_KEYWORDS_HI = [
    "हाँ", "हां", "जी हां", "जी हाँ", "ठीक है", "सही है",
    "वही", "यही", "बिल्कुल", "सही", "ठीक", "हूँ", "हू"
]

CONFIRMATION_KEYWORDS_EN = [
    "yes", "yeah", "yep", "yup", "correct", "right",
    "ok", "okay", "sure", "fine", "exactly", "same"
]

# Rejection keywords
REJECTION_KEYWORDS_HI = [
    "नहीं", "ना", "नही", "गलत", "अलग"
]

REJECTION_KEYWORDS_EN = [
    "no", "nope", "nah", "wrong", "different", "not"
]


def is_location_confirmation(user_message: str) -> bool:
    """
    Check if user's message is confirming the location.

    Args:
        user_message: User's response message

    Returns:
        True if message contains confirmation keywords

    Example:
        >>> is_location_confirmation("हाँ")
        True
        >>> is_location_confirmation("नहीं, मादर में है")
        False
    """
    if not user_message:
        return False

    message_lower = user_message.lower().strip()

    # Check for confirmation keywords
    for keyword in CONFIRMATION_KEYWORDS_HI + CONFIRMATION_KEYWORDS_EN:
        if keyword in message_lower:
            logger.info(f"[Location] Confirmation detected: '{keyword}' in '{user_message[:50]}'")
            return True

    return False


def is_location_rejection(user_message: str) -> bool:
    """
    Check if user is rejecting the profile location.

    Args:
        user_message: User's response message

    Returns:
        True if message contains rejection keywords

    Example:
        >>> is_location_rejection("नहीं")
        True
        >>> is_location_rejection("हाँ वही है")
        False
    """
    if not user_message:
        return False

    message_lower = user_message.lower().strip()

    # Check for rejection keywords
    for keyword in REJECTION_KEYWORDS_HI + REJECTION_KEYWORDS_EN:
        if keyword in message_lower:
            logger.info(f"[Location] Rejection detected: '{keyword}' in '{user_message[:50]}'")
            return True

    return False


def format_location_display(
    street: Optional[str] = None,
    village: Optional[str] = None,
    panchayat: Optional[str] = None,
    block: Optional[str] = None,
    subdivision: Optional[str] = None,
    district: Optional[str] = None,
    state: Optional[str] = None
) -> str:
    """
    Format location fields into a human-readable Hindi string.

    Args:
        street: Street/mohalla name
        village: Village/town name
        panchayat: Gram panchayat name
        block: Block/tehsil name
        subdivision: Subdivision name
        district: District name
        state: State name

    Returns:
        Formatted location string in Hindi

    Example:
        >>> format_location_display(
        ...     street="कोटेवार पारा",
        ...     village="मादर",
        ...     block="लोहंडीगुड़ा",
        ...     district="बस्तर"
        ... )
        "कोटेवार पारा, ग्राम मादर, ब्लॉक लोहंडीगुड़ा, जिला बस्तर"
    """
    location_parts = []

    if street:
        location_parts.append(street)

    if village:
        location_parts.append(f"ग्राम {village}")

    if panchayat:
        location_parts.append(f"पंचायत {panchayat}")

    if block:
        location_parts.append(f"ब्लॉक {block}")

    if subdivision:
        location_parts.append(f"उपखंड {subdivision}")

    if district:
        location_parts.append(f"जिला {district}")

    if state and state.lower() not in ["छत्तीसगढ़", "chhattisgarh"]:
        # Only include state if not default (Chhattisgarh)
        location_parts.append(f"राज्य {state}")

    return ", ".join(location_parts) if location_parts else ""


def merge_location_with_profile(
    extracted_location: Dict[str, Any],
    profile_location: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Merge extracted location with profile location.

    Use case: User says "कोटेवार पारा में" (just street name)
    → Keep village, panchayat, block, district from profile
    → Update only street

    This supports street-level override while maintaining administrative boundaries.

    Args:
        extracted_location: Location extracted from user's message
        profile_location: Location from user profile

    Returns:
        Merged location with user's changes and profile defaults

    Example:
        >>> profile = {
        ...     "street": "महारा पारा",
        ...     "village": "मादर",
        ...     "block": "लोहंडीगुड़ा",
        ...     "district": "बस्तर"
        ... }
        >>> extracted = {"street": "कोटेवार पारा"}
        >>> merged = merge_location_with_profile(extracted, profile)
        >>> merged["street"]
        "कोटेवार पारा"
        >>> merged["village"]  # Kept from profile
        "मादर"
    """
    # Start with profile as base
    merged = profile_location.copy()

    # Override with extracted values if provided
    location_fields = [
        "street", "village", "panchayat", "block",
        "subdivision", "district", "state"
    ]

    for field in location_fields:
        if extracted_location.get(field):
            merged[field] = extracted_location[field]
            logger.info(f"[Location] Overriding {field}: {extracted_location[field]}")

    # If user provided GPS coordinates, use those
    if extracted_location.get("lat") and extracted_location.get("lng"):
        merged["lat"] = extracted_location["lat"]
        merged["lng"] = extracted_location["lng"]
        logger.info(f"[Location] GPS override: {merged['lat']}, {merged['lng']}")

    return merged


def has_meaningful_location(location_data: Dict[str, Any]) -> bool:
    """
    Check if location data contains meaningful information.

    A location is considered meaningful if it has at least:
    - District (required)
    - AND (Village OR Block)

    Args:
        location_data: Location dictionary

    Returns:
        True if location has minimum required fields (GUARANTEED bool, never None)

    Example:
        >>> has_meaningful_location({"district": "बस्तर", "village": "मादर"})
        True
        >>> has_meaningful_location({"district": "बस्तर"})
        False
        >>> has_meaningful_location(None)
        False
    """
    try:
        # BUGFIX: Defensive null check to prevent None propagation
        if not location_data or not isinstance(location_data, dict):
            return False

        # CRITICAL FIX: Check for meaningful values (not just key existence)
        # Handle None and empty strings properly
        district_val = location_data.get("district")
        village_val = location_data.get("village")
        block_val = location_data.get("block")

        # Convert to boolean safely: reject None and empty strings
        has_district = bool(district_val and str(district_val).strip())
        has_village = bool(village_val and str(village_val).strip())
        has_block = bool(block_val and str(block_val).strip())

        has_village_or_block = has_village or has_block

        # Explicit boolean return to ensure Pydantic validation passes
        result = bool(has_district and has_village_or_block)

        # Additional safety: Assert return type is actually boolean
        assert isinstance(result, bool), f"Internal error: expected bool, got {type(result)}"

        return result

    except Exception as e:
        # CRITICAL FIX: If ANY exception occurs, return False (never None)
        logger.error(f"[Location] Exception in has_meaningful_location: {e}", exc_info=True)
        return False  # Guaranteed boolean fallback


def extract_location_from_user_profile(user) -> Optional[Dict[str, Any]]:
    """
    Extract location data from user profile.

    Args:
        user: User model instance

    Returns:
        Location dictionary or None if no location in profile

    Example:
        >>> location = extract_location_from_user_profile(user)
        >>> location["village"]
        "मादर"
    """
    # BUGFIX: Defensive null check with explicit type checking
    if not user:
        logger.debug("[Location] extract_location_from_user_profile: user is None")
        return None

    # Check if user has meaningful location data
    # BUGFIX: Safe attribute access with explicit None handling for missing DB columns
    try:
        # DEFENSIVE: Use getattr with safe defaults for columns that might not exist in Azure DB yet
        district_raw = getattr(user, 'location_district', None)
        village_raw = getattr(user, 'location_village', None)
        block_raw = getattr(user, 'location_block', None)

        # Convert to boolean safely (handles None, empty string, etc.)
        has_district = bool(district_raw and str(district_raw).strip())
        has_village = bool(village_raw and str(village_raw).strip())
        has_block = bool(block_raw and str(block_raw).strip())

        if not (has_district and (has_village or has_block)):
            logger.debug(
                f"[Location] User {user.id} has insufficient location data: "
                f"district={has_district}, village={has_village}, block={has_block}"
            )
            return None

        # Safely extract all location fields with explicit type coercion
        # CRITICAL: All string fields use `or None` pattern to convert empty strings to None
        location_data = {
            "street": str(getattr(user, 'location_street', '') or '').strip() or None,
            "village": str(getattr(user, 'location_village', '') or '').strip() or None,
            "panchayat": str(getattr(user, 'location_panchayat', '') or '').strip() or None,
            "block": str(getattr(user, 'location_block', '') or '').strip() or None,
            "subdivision": str(getattr(user, 'location_subdivision', '') or '').strip() or None,
            "district": str(getattr(user, 'location_district', '') or '').strip() or None,
            "state": str(getattr(user, 'location_state', '') or '').strip() or None,
            "lat": getattr(user, 'location_lat', None),  # Numeric field - keep as-is
            "lng": getattr(user, 'location_lng', None),  # Numeric field - keep as-is
            "formatted_address": str(getattr(user, 'location_formatted_address', '') or '').strip() or None
        }

        logger.debug(f"[Location] Successfully extracted location for user {user.id}")
        return location_data

    except AttributeError as e:
        logger.warning(
            f"[Location] Failed to extract location from user profile: {e}. "
            f"User object may be missing location attributes (columns may not exist in DB yet)."
        )
        return None
    except Exception as e:
        logger.error(
            f"[Location] Unexpected error extracting location: {e}. "
            f"Returning None to prevent crashes.",
            exc_info=True
        )
        return None
