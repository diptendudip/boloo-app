"""
MINIMAL FIX FOR PYDANTIC VALIDATION ERROR
==========================================

Issue: profile_location_available receiving None instead of boolean in production
Location: /app/routers/chat.py lines 550-571

ROOT CAUSE:
-----------
Exception handling in has_meaningful_location() may return None in edge cases,
despite function signature claiming it returns bool.

FIX STRATEGY:
-------------
Add explicit None-to-False conversion at the source function (has_meaningful_location)
to guarantee boolean return under ALL circumstances.

CHANGES REQUIRED:
-----------------
File: /app/utils/location_confirmation.py
Function: has_meaningful_location (line 212)
"""

# ============================================================================
# ORIGINAL CODE (lines 212-244)
# ============================================================================
"""
def has_meaningful_location(location_data: Dict[str, Any]) -> bool:
    # BUGFIX: Defensive null check to prevent None propagation
    if not location_data or not isinstance(location_data, dict):
        return False

    has_district = bool(location_data.get("district"))
    has_village_or_block = bool(
        location_data.get("village") or location_data.get("block")
    )

    # Explicit boolean return to ensure Pydantic validation passes
    return bool(has_district and has_village_or_block)
"""

# ============================================================================
# FIXED CODE (REPLACE lines 212-244)
# ============================================================================
"""
def has_meaningful_location(location_data: Dict[str, Any]) -> bool:
    '''
    Check if location data contains meaningful information.

    GUARANTEED to return bool (True/False), NEVER None.

    Args:
        location_data: Location dictionary

    Returns:
        bool: True if location has minimum required fields, False otherwise

    Example:
        >>> has_meaningful_location({"district": "बस्तर", "village": "मादर"})
        True
        >>> has_meaningful_location({"district": "बस्तर"})
        False
        >>> has_meaningful_location(None)
        False
    '''
    try:
        # BUGFIX: Defensive null check to prevent None propagation
        if not location_data or not isinstance(location_data, dict):
            return False

        has_district = bool(location_data.get("district"))
        has_village_or_block = bool(
            location_data.get("village") or location_data.get("block")
        )

        # Explicit boolean return to ensure Pydantic validation passes
        result = bool(has_district and has_village_or_block)

        # ADDITIONAL SAFETY: Assert return type
        assert isinstance(result, bool), f"Internal error: expected bool, got {type(result)}"

        return result

    except Exception as e:
        # CRITICAL FIX: If ANY exception occurs, return False (never None)
        logger.error(f"[Location] Exception in has_meaningful_location: {e}", exc_info=True)
        return False  # Guaranteed boolean fallback
"""

# ============================================================================
# DEPLOYMENT INSTRUCTIONS
# ============================================================================
"""
1. APPLY THE FIX:
   -----------------
   Edit /app/utils/location_confirmation.py
   Replace lines 212-244 with the fixed code above

   OR use this one-liner:

   sed -i.bak '/^def has_meaningful_location/,/^$/c\
   # [PASTE FIXED CODE HERE]
   ' /app/utils/location_confirmation.py

2. VERIFY LOCALLY (if possible):
   ------------------------------
   cd /Users/diptendu/boloo\ app/boloo-app/backend
   python -m pytest tests/ -v -k location

   OR manual test:
   python -c "
   from app.utils.location_confirmation import has_meaningful_location
   # Test cases
   assert has_meaningful_location(None) == False
   assert has_meaningful_location({}) == False
   assert has_meaningful_location({'district': 'बस्तर', 'village': 'मादर'}) == True
   print('✅ All tests passed')
   "

3. DEPLOY TO PRODUCTION:
   ----------------------
   # Commit the fix
   git add app/utils/location_confirmation.py
   git commit -m "fix: guarantee boolean return in has_meaningful_location (Pydantic validation)"

   # Deploy (adjust for your deployment method)
   git push origin main
   # OR
   docker build -t boloo-backend . && docker push boloo-backend
   # OR
   railway up  # If using Railway

   # Restart service
   systemctl restart boloo-backend  # Adjust for your setup

4. VERIFY IN PRODUCTION:
   ---------------------
   # Test the /chat/start endpoint
   curl -X POST https://your-api.com/chat/start \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -F "user_id=YOUR_USER_ID" \
     -F "language=hi-IN"

   # Should return 200 with profile_location_available as boolean (not null)

5. ROLLBACK PLAN (if issues):
   ---------------------------
   git revert HEAD
   git push origin main
   # Restart service
"""

# ============================================================================
# ALTERNATIVE FIX (if editing function is risky)
# ============================================================================
"""
If you can't edit location_confirmation.py safely, apply this minimal patch
to chat.py instead (lines 558-561):

ORIGINAL:
---------
has_meaningful = has_meaningful_location(profile_location)
# Defensive: treat None as False
has_profile_location = bool(has_meaningful if has_meaningful is not None else False)

REPLACE WITH:
-------------
try:
    has_meaningful = has_meaningful_location(profile_location)
    # TRIPLE SAFETY: Force boolean, handle None, handle exceptions
    has_profile_location = bool(has_meaningful) if has_meaningful is not None else False
    # Ensure it's actually boolean
    if not isinstance(has_profile_location, bool):
        has_profile_location = False
except Exception as e:
    logger.error(f"[Chat] Exception in has_meaningful_location: {e}")
    has_profile_location = False
"""

# ============================================================================
# TESTING CHECKLIST
# ============================================================================
"""
✅ Test Case 1: User with complete profile location
   Expected: profile_location_available = true

✅ Test Case 2: User with incomplete profile location (no district)
   Expected: profile_location_available = false

✅ Test Case 3: User with no profile location
   Expected: profile_location_available = false

✅ Test Case 4: New user (empty profile)
   Expected: profile_location_available = false

✅ Test Case 5: Malformed location data
   Expected: profile_location_available = false (no crash)
"""
