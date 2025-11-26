# Smart Location Confirmation Implementation

## Overview

Implement smart location confirmation logic where the AI chat checks the user's profile location and asks for confirmation before proceeding with the report.

**Status**: 🔄 In Progress

---

## User Requirements

From user's request:

1. **Profile Location Display**: ✅ DONE - Added `GET /v1/users/me` endpoint
2. **Smart Chat Location Confirmation**: "the chat should ask the user if the address mentioned in the profile is the address should be used for location of the stated report"
3. **Profile Address Quoting**: "the ai should confirm with the user quoting the address from profile if that address should be used or the user wants to mention another address"
4. **Street-Level Override**: "reporters from same village or block should be able to change the street level address as in a village/panchayat different area where people face issue so panchayat/block will remain same only the street will be changed"

---

## Implementation Plan

### 1. Modify Chat Start Endpoint (`/v1/chat/start`)

**Location**: `app/routers/chat.py` lines 499-560

**Current Behavior**:
- Creates conversation
- Returns generic greeting

**New Behavior**:
- Check if user has location in profile:
  - `user.location_district` exists → User has saved location
  - Format location string for display
- Return enhanced greeting with location confirmation question

**Implementation**:

```python
@router.post("/start", response_model=ChatStartResponse)
async def start_chat_conversation(
    user_id: str,
    language: str = "hi",
    db: Session = Depends(get_db)
):
    # ... existing user fetch code ...

    # CHECK USER PROFILE LOCATION
    has_profile_location = bool(
        user.location_district and
        (user.location_village or user.location_block)
    )

    if has_profile_location:
        # Format location for display
        location_parts = []
        if user.location_street:
            location_parts.append(user.location_street)
        if user.location_village:
            location_parts.append(user.location_village)
        if user.location_panchayat:
            location_parts.append(f"पंचायत {user.location_panchayat}")
        if user.location_block:
            location_parts.append(f"ब्लॉक {user.location_block}")
        if user.location_district:
            location_parts.append(f"जिला {user.location_district}")

        formatted_location = ", ".join(location_parts)

        # Store in conversation metadata for later use
        conversation.metadata = {
            "profile_location_available": True,
            "profile_location_formatted": formatted_location,
            "profile_location_confirmed": False,  # Will be set to True when user confirms
            "location_data": {
                "street": user.location_street,
                "village": user.location_village,
                "panchayat": user.location_panchayat,
                "block": user.location_block,
                "subdivision": user.location_subdivision,
                "district": user.location_district,
                "state": user.location_state,
                "lat": user.location_lat,
                "lng": user.location_lng
            }
        }
        db.commit()

        # Generate greeting WITH location confirmation
        greeting_hi = f"""नमस्ते! मैं आपकी मदद के लिए यहाँ हूँ।

आपके प्रोफाइल में यह पता दर्ज है:
📍 {formatted_location}

क्या इस रिपोर्ट के लिए यही पता उपयोग करना है?

अगर समस्या किसी अलग जगह पर है (जैसे गाँव के किसी दूसरे क्षेत्र में), तो कृपया वह नया पता बताएं।"""

        greeting_en = f"""Hello! I'm here to help you.

Your profile has this address:
📍 {formatted_location}

Should we use this address for this report?

If the issue is at a different location (like a different area in the village), please let me know the new address."""

    else:
        # No profile location → Use default greeting
        greetings = conversation_service.generate_greeting(language)
        greeting_hi = greetings["hi"]
        greeting_en = greetings["en"]

    return ChatStartResponse(...)
```

### 2. Modify Chat Turn Logic (`/v1/chat/turn`)

**Location**: `app/routers/chat.py` lines 562+

**Current Behavior**:
- Asks for location if missing
- No awareness of profile location

**New Behavior**:
- Check conversation metadata for `profile_location_available`
- If available and not yet confirmed:
  - Look for confirmation in user's response ("हाँ", "yes", "ठीक है", etc.)
  - If confirmed → Auto-fill location from profile
  - If user provides new location → Extract and use that instead
- Allow street-level override (user can change street but keep village/block)

**Implementation Logic**:

```python
# Inside process_chat_turn()

# Check if profile location was offered and not yet confirmed
conversation_metadata = conversation.metadata or {}
profile_location_available = conversation_metadata.get("profile_location_available", False)
profile_location_confirmed = conversation_metadata.get("profile_location_confirmed", False)

if profile_location_available and not profile_location_confirmed:
    # User is responding to location confirmation question

    # Check for confirmation keywords
    confirmation_keywords_hi = ["हाँ", "हां", "जी हां", "ठीक है", "सही है", "वही", "यही"]
    confirmation_keywords_en = ["yes", "yeah", "yep", "correct", "ok", "okay", "right", "same"]

    user_message_lower = user_message.lower()
    is_confirmation = any(kw in user_message_lower for kw in confirmation_keywords_hi + confirmation_keywords_en)

    if is_confirmation:
        # User confirmed profile location → Auto-fill
        location_data = conversation_metadata.get("location_data", {})

        extracted_data["location"] = conversation_metadata.get("profile_location_formatted")
        extracted_data["location_street"] = location_data.get("street")
        extracted_data["location_village"] = location_data.get("village")
        extracted_data["location_panchayat"] = location_data.get("panchayat")
        extracted_data["location_block"] = location_data.get("block")
        extracted_data["location_district"] = location_data.get("district")
        extracted_data["location_state"] = location_data.get("state")
        extracted_data["location_lat"] = location_data.get("lat")
        extracted_data["location_lng"] = location_data.get("lng")

        # Mark as confirmed
        conversation_metadata["profile_location_confirmed"] = True
        conversation.metadata = conversation_metadata
        db.commit()

        logger.info(f"✅ User confirmed profile location for conversation {conversation_id}")

        # Continue with issue description question
        ai_response_hi = "धन्यवाद! अब कृपया बताएं कि क्या समस्या है?"
        ai_response_en = "Thank you! Now please tell me what the issue is?"

    else:
        # User is providing a different location → Extract it
        logger.info(f"🔄 User providing alternative location for conversation {conversation_id}")

        # Check if it's a street-level override (same village/block, different street)
        # This is handled by the completeness analyzer - it will extract the new location
        # and we'll merge it with profile location (keeping village/block if not mentioned)

        # Mark profile location as not used
        conversation_metadata["profile_location_confirmed"] = False
        conversation_metadata["profile_location_used"] = False
        conversation.metadata = conversation_metadata
        db.commit()
```

### 3. Add Helper Function for Location Merging

**Purpose**: When user provides partial location (e.g., only street), merge with profile location

```python
def merge_location_with_profile(
    extracted_location: Dict[str, Any],
    profile_location: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Merge extracted location with profile location.

    Use case: User says "कोटेवार पारा में" (just street name)
    → Keep village, panchayat, block, district from profile
    → Update only street

    Args:
        extracted_location: Location extracted from user's message
        profile_location: Location from user profile

    Returns:
        Merged location with user's changes and profile defaults
    """
    merged = profile_location.copy()

    # Override with extracted values if provided
    for key in ["street", "village", "panchayat", "block", "district", "state"]:
        if extracted_location.get(key):
            merged[key] = extracted_location[key]

    # If user provided GPS, use that
    if extracted_location.get("lat") and extracted_location.get("lng"):
        merged["lat"] = extracted_location["lat"]
        merged["lng"] = extracted_location["lng"]

    return merged
```

### 4. Update Response Models

**Add to `ChatStartResponse`**:

```python
class ChatStartResponse(BaseModel):
    success: bool
    conversation_id: str
    greeting_hi: str
    greeting_en: str
    in_training_mode: bool

    # NEW: Profile location info
    profile_location_available: bool = False
    profile_location_formatted: Optional[str] = None
```

---

## Example User Flows

### Flow 1: User Confirms Profile Location

```
[Chat Start]
AI: "आपके प्रोफाइल में यह पता दर्ज है: ग्राम मादर, ब्लॉक लोहंडीगुड़ा, जिला बस्तर। क्या इस रिपोर्ट के लिए यही पता उपयोग करना है?"

User: "हाँ"

AI: "धन्यवाद! अब कृपया बताएं कि क्या समस्या है?"

User: "हैंडपंप खराब है"

[Location auto-filled from profile, proceeds to collect issue details]
```

### Flow 2: User Provides Different Location

```
[Chat Start]
AI: "आपके प्रोफाइल में यह पता दर्ज है: ग्राम मादर, ब्लॉक लोहंडीगुड़ा, जिला बस्तर। क्या इस रिपोर्ट के लिए यही पता उपयोग करना है?"

User: "नहीं, समस्या डोंगरीगुड़ा में है"

AI: "ठीक है। कृपया बताएं कि डोंगरीगुड़ा में क्या समस्या है?"

[Extracts new location: village=डोंगरीगुड़ा, keeps block/district from profile if not mentioned]
```

### Flow 3: Street-Level Override

```
[Chat Start]
AI: "आपके प्रोफाइल में यह पता दर्ज है: कोटेवार पारा, ग्राम मादर, ब्लॉक लोहंडीगुड़ा। क्या इस रिपोर्ट के लिए यही पता उपयोग करना है?"

User: "नहीं, महारा पारा में है"

AI: "ठीक है। महारा पारा, मादर में क्या समस्या है?"

[Updates: street=महारा पारा, keeps village/block/district from profile]
```

### Flow 4: No Profile Location

```
[Chat Start]
AI: "नमस्ते! मैं आपकी मदद के लिए यहाँ हूँ। कृपया बताएं कि क्या समस्या है और कहाँ है?"

User: "मादर गाँव में हैंडपंप खराब है"

[Normal flow - asks for location if not clear]
```

---

## Implementation Checklist

- [x] Add `GET /v1/users/me` endpoint - DONE in `users.py:21-37`
- [ ] Modify `/v1/chat/start` to check profile location
- [ ] Add location confirmation to greeting
- [ ] Store location metadata in conversation
- [ ] Modify `/v1/chat/turn` to detect confirmation
- [ ] Auto-fill location on confirmation
- [ ] Handle alternative location provision
- [ ] Implement location merging logic
- [ ] Update response models
- [ ] Test all 4 user flows

---

## Database Changes

**None required** - All location fields already exist in User model.

---

## API Changes

### Modified Endpoints

#### `POST /v1/chat/start`

**Response Changes**:
```json
{
  "success": true,
  "conversation_id": "uuid",
  "greeting_hi": "नमस्ते! आपके प्रोफाइल में...",
  "greeting_en": "Hello! Your profile has...",
  "in_training_mode": false,
  "profile_location_available": true,  // NEW
  "profile_location_formatted": "ग्राम मादर, ब्लॉक लोहंडीगुड़ा, जिला बस्तर"  // NEW
}
```

---

## Testing Plan

1. **Test with profile location**:
   - User confirms → Location auto-fills
   - User provides different location → New location used
   - User provides partial location → Merges with profile

2. **Test without profile location**:
   - Normal flow works

3. **Test street-level override**:
   - User changes only street → Village/block/district retained

4. **Edge cases**:
   - User says "नहीं" but doesn't provide new location
   - User provides ambiguous location
   - User profile has incomplete location (only district, no village)

---

## Benefits

1. **Faster reporting**: Users with profile location can confirm with one word
2. **Flexibility**: Users can override location when needed
3. **Reduced friction**: No need to re-enter location every time
4. **Street-level precision**: Users can update specific area within village
5. **Better UX**: Clear confirmation flow with quoted address

---

## Next Steps After This

1. LGD data integration for validation
2. Mobile UI update to show location in profile
3. Analytics on location confirmation rates
