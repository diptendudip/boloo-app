# Google Maps Integration Guide

## Overview

The Google Maps validator provides **optional** location validation and geocoding to enhance the existing deterministic location extraction.

**Status**: Optional enhancement (not required for basic functionality)
**Cost**: Pay-per-use (see pricing below)
**Setup time**: 5-10 minutes

## When to Use It

### ✅ Use Google Maps for:
1. **Validation**: Confirm extracted locations are real places
2. **Normalization**: Convert "डोंगरीगुड़ा" → "Dongriguda, Chhattisgarh"
3. **Coordinates**: Get lat/lng for mapping features
4. **Disambiguation**: When multiple villages have same name
5. **Government submission**: When officials need validated addresses

### ❌ Don't use it for:
- Primary location extraction (use deterministic parser first)
- Vague references without anchor ("यहाँ", "हमारे मोहल्ले")
- Production without API key (will gracefully skip)

## Setup (5 minutes)

### 1. Get Google Maps API Key

```bash
# Go to Google Cloud Console
https://console.cloud.google.com/

# Enable these APIs:
- Places API (new v1)
- Geocoding API

# Create API key with restrictions:
- Application restrictions: IP addresses (your server)
- API restrictions: Places API, Geocoding API only
```

### 2. Add to Environment

```bash
# backend/.env
GOOGLE_MAPS_API_KEY=AIzaSy...your-key-here
```

### 3. Verify

```bash
# Backend will log:
INFO: GoogleMapsValidator initialized

# Or will warn if not configured:
WARNING: Google Maps API key not configured - validation will be skipped
```

## Integration Examples

### Minimal Integration (Validation Only)

Add to `completeness_analyzer.py` after deterministic extraction:

```python
from app.services.google_maps_validator import GoogleMapsValidator

class CompletenessAnalyzer:
    def __init__(self):
        # ... existing code ...
        self.maps_validator = GoogleMapsValidator()  # Add this

    def analyze_completeness(self, transcript, ...):
        # ... existing extraction code ...

        # AFTER deterministic extraction succeeds:
        if result["extracted_data"].get("location"):
            location_text = result["extracted_data"]["location"]

            # Optional: Validate with Google Maps
            maps_result = self.maps_validator.validate_and_enrich_location(
                location_text=location_text,
                district_hint=extracted_district,  # From deterministic parser
                state_hint="Chhattisgarh"
            )

            if maps_result["is_valid"]:
                # Enrich with normalized name and coordinates
                result["extracted_data"]["location_normalized"] = maps_result["formatted_name"]
                result["extracted_data"]["location_lat"] = maps_result["lat"]
                result["extracted_data"]["location_lng"] = maps_result["lng"]
                result["extracted_data"]["location_confidence"] = maps_result["confidence"]

                logger.info(f"✅ Google Maps validated: {location_text} → {maps_result['formatted_name']}")
            else:
                logger.warning(f"⚠️ Google Maps couldn't validate: {location_text}")
                # Keep deterministic extraction result

        return result
```

### Full Integration (With Database Storage)

Modify `chat.py` to store coordinates in database:

```python
# In create_case_from_conversation():

location_data = {
    "raw": extracted["location"],
    "normalized": extracted.get("location_normalized"),
    "lat": extracted.get("location_lat"),
    "lng": extracted.get("location_lng"),
    "confidence": extracted.get("location_confidence", 0.0),
    "source": extracted.get("location_source", "deterministic_parser")
}

new_case = Case(
    # ... existing fields ...
    location_lat=location_data["lat"],
    location_lng=location_data["lng"],
    location_metadata=location_data  # Store full details in JSONB
)
```

### Advanced: GPS Fallback

If user shares GPS coordinates (future feature):

```python
def handle_user_location_share(lat: float, lng: float):
    """When user taps 'Share Location' in mobile app."""
    validator = GoogleMapsValidator()

    result = validator.reverse_geocode(lat=lat, lng=lng, language="hi")

    if result["is_valid"]:
        # Auto-fill location field
        extracted_data["location"] = result["formatted_name"]
        extracted_data["location_precision"] = "gps"
        extracted_data["location_lat"] = lat
        extracted_data["location_lng"] = lng

        # Ask user to confirm
        return f"क्या यह सही है: {result['formatted_name']}?"
```

## Cost Estimation

Google Maps Platform pricing (as of 2024):

**Places Text Search (new v1):**
- $17 per 1,000 requests
- Your usage: ~1 request per case submission
- 1,000 cases/month = $17/month
- 10,000 cases/month = $170/month

**Geocoding API:**
- $5 per 1,000 requests
- Your usage: Only if user shares GPS
- 1,000 GPS shares/month = $5/month

**Total estimated cost:**
- Low usage (1,000 cases/month): ~$20/month
- Medium usage (10,000 cases/month): ~$200/month
- Free tier: $200/month credit (enough for ~10K validations)

## Privacy & Compliance

**What Google receives:**
- Location text (e.g., "डोंगरीगुड़ा पंचायत, बस्तर")
- GPS coordinates (only if user explicitly shares)

**What Google does NOT receive:**
- User phone numbers
- Issue descriptions
- Personal information
- Audio recordings

**Terms compliance:**
- ✅ Can store Place IDs indefinitely
- ✅ Can cache results for 30 days (with restrictions)
- ❌ Cannot use data for ML training
- Review: https://cloud.google.com/maps-platform/terms

## Testing

### Test validation endpoint

```python
# In Python shell or Jupyter:
from app.services.google_maps_validator import GoogleMapsValidator

validator = GoogleMapsValidator()

# Test 1: Specific location
result = validator.validate_and_enrich_location(
    location_text="डोंगरीगुड़ा पंचायत, अलवा ब्लाक, बस्तर",
    district_hint="बस्तर",
    state_hint="Chhattisgarh"
)
print(result)

# Expected output:
# {
#     "is_valid": True,
#     "place_id": "ChIJ...",
#     "formatted_name": "Dongriguda, Chhattisgarh",
#     "lat": 19.xxx,
#     "lng": 81.xxx,
#     "confidence": 0.85
# }

# Test 2: Ambiguous location (should return low confidence)
result2 = validator.validate_and_enrich_location(
    location_text="हमारे मोहल्ले",  # Vague reference
    district_hint="बस्तर"
)
print(result2["is_valid"])  # False - no anchor provided

# Test 3: Reverse geocode
result3 = validator.reverse_geocode(lat=19.123, lng=81.456, language="hi")
print(result3["formatted_name"])
```

## Monitoring & Optimization

### Check usage in Google Cloud Console

```bash
# View API requests and costs
https://console.cloud.google.com/apis/dashboard

# Set up budget alerts
https://console.cloud.google.com/billing/budgets
```

### Optimize costs:

1. **Cache results**: Store validated locations in Redis (30-day TTL)
2. **Batch similar requests**: If same village mentioned multiple times
3. **Rate limiting**: Max 1 validation per case submission
4. **Fallback strategy**: Skip validation if API quota exceeded

### Example caching:

```python
import redis
import json

redis_client = redis.from_url(settings.REDIS_URL)

def validate_with_cache(location_text: str, district: str):
    """Validate with 30-day cache."""
    cache_key = f"maps:validation:{location_text}:{district}"

    # Check cache first
    cached = redis_client.get(cache_key)
    if cached:
        logger.info(f"Cache hit for {location_text}")
        return json.loads(cached)

    # Call Google Maps
    result = validator.validate_and_enrich_location(location_text, district)

    # Cache for 30 days (Maps TOS compliant)
    if result["is_valid"]:
        redis_client.setex(cache_key, 30 * 24 * 3600, json.dumps(result))

    return result
```

## Troubleshooting

### "API key not configured" warning

**Solution**: Add `GOOGLE_MAPS_API_KEY` to `.env` file

### "Places API returned 0 results"

**Reasons**:
1. Location too vague ("यहाँ")
2. Typo in location name
3. Location bias not accurate
4. Location not in Google Maps database

**Solution**: Fall back to deterministic parser result

### "REQUEST_DENIED" error

**Reasons**:
1. API key restrictions too strict
2. APIs not enabled in Google Cloud
3. Billing not enabled

**Solution**: Check Google Cloud Console → API & Services

### High costs

**Solution**:
1. Enable caching (see above)
2. Add rate limiting (max 1 request per case)
3. Set budget alerts in Google Cloud Console
4. Consider validating only high-priority cases

## Gradual Rollout Strategy

### Phase 1: Testing (Week 1)
- Enable for internal testing only
- Validate 100 test cases
- Verify accuracy and cost

### Phase 2: Pilot (Week 2-3)
- Enable for 10% of users (A/B test)
- Monitor accuracy improvements
- Track cost per validation

### Phase 3: Production (Week 4+)
- Roll out to all users if metrics good:
  - Accuracy > 85%
  - Cost < $200/month
  - User satisfaction improved

## Next Steps

1. **Get API key**: https://console.cloud.google.com/
2. **Add to .env**: `GOOGLE_MAPS_API_KEY=...`
3. **Test**: Run validation on 10 sample locations
4. **Integrate**: Add to completeness_analyzer (see examples above)
5. **Monitor**: Check usage/costs weekly

## Support

- Google Maps Platform Support: https://cloud.google.com/maps-platform/support
- Pricing calculator: https://mapsplatform.google.com/pricing/
- API documentation: https://developers.google.com/maps/documentation/places
