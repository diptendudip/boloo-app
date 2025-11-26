# Location API Testing Guide

## Overview

This guide shows how to test the free geocoding/location APIs integrated into the Boloo backend.

The system uses:
- **Mappls (MapmyIndia)** - Free tier: 5,000 requests/day
- **Nominatim (OpenStreetMap)** - Free tier: Unlimited with rate limiting
- **Hybrid Validator** - Automatically falls back between providers

## Backend Endpoints

### 1. GPS Boundary Detection

**Endpoint**: `POST /api/location/detect-from-gps`

**Use Case**: User shares GPS coordinates → System auto-detects village, block, district, etc.

**Parameters**:
- `lat` (float, required): Latitude
- `lng` (float, required): Longitude
- `language` (string, optional): `hi` or `en` (default: `hi`)

**Example - Bastar District, Chhattisgarh**:
```bash
curl -X POST "http://localhost:8000/api/location/detect-from-gps?lat=19.1136&lng=81.8094&language=hi" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected Response**:
```json
{
  "street": null,
  "village": "मादर",
  "panchayat": "मादर पंचायत",
  "block": "लोहंडीगुड़ा",
  "subdivision": null,
  "district": "बस्तर",
  "state": "छत्तीसगढ़",
  "country": "India",
  "lat": 19.1136,
  "lng": 81.8094,
  "formatted_address": "ग्राम मादर, ब्लॉक लोहंडीगुड़ा, जिला बस्तर, छत्तीसगढ़",
  "confidence": 0.85,
  "source": "mappls"
}
```

**More Test Coordinates**:
```bash
# Raipur, CG
curl -X POST "http://localhost:8000/api/location/detect-from-gps?lat=21.2514&lng=81.6296&language=hi"

# Dantewada, CG
curl -X POST "http://localhost:8000/api/location/detect-from-gps?lat=18.8933&lng=81.3532&language=hi"

# Kanker, CG
curl -X POST "http://localhost:8000/api/location/detect-from-gps?lat=20.2716&lng=81.4919&language=hi"
```

---

### 2. Address Validation

**Endpoint**: `POST /api/location/validate-address`

**Use Case**: User types address manually → System validates and normalizes it

**Parameters**:
- `address` (string, required): Full address or village name
- `district_hint` (string, optional): District name for better accuracy
- `state_hint` (string, optional): State name (default: `Chhattisgarh`)

**Example - Hindi Address**:
```bash
curl -X POST "http://localhost:8000/api/location/validate-address" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "address": "मादर गाँव, बस्तर",
    "state_hint": "Chhattisgarh"
  }'
```

**Example - English Address**:
```bash
curl -X POST "http://localhost:8000/api/location/validate-address" \
  -H "Content-Type: application/json" \
  -d '{
    "address": "Lohandiguda Block, Bastar District",
    "district_hint": "Bastar",
    "state_hint": "Chhattisgarh"
  }'
```

**Expected Response**:
```json
{
  "street": null,
  "village": "मादर",
  "panchayat": null,
  "block": "लोहंडीगुड़ा",
  "subdivision": null,
  "district": "बस्तर",
  "state": "छत्तीसगढ़",
  "country": "India",
  "lat": 19.1136,
  "lng": 81.8094,
  "formatted_address": "मादर, लोहंडीगुड़ा ब्लॉक, बस्तर जिला, छत्तीसगढ़",
  "confidence": 0.78,
  "source": "nominatim"
}
```

---

### 3. Update User Location

**Endpoint**: `POST /api/location/update-user-location`

**Use Case**: Save user's location to profile (used during signup or address update)

**Request Body**:
```json
{
  "street": "Main Road",
  "village": "मादर",
  "panchayat": "मादर पंचायत",
  "block": "लोहंडीगुड़ा",
  "district": "बस्तर",
  "state": "छत्तीसगढ़",
  "lat": 19.1136,
  "lng": 81.8094
}
```

**OR with GPS auto-detection**:
```json
{
  "lat": 19.1136,
  "lng": 81.8094,
  "street": "Main Road"
}
```

**Example**:
```bash
curl -X POST "http://localhost:8000/api/location/update-user-location" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "lat": 19.1136,
    "lng": 81.8094,
    "street": "Main Road"
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "message": "Location updated successfully",
  "location": {
    "street": "Main Road",
    "village": "मादर",
    "panchayat": "मादर पंचायत",
    "block": "लोहंडीगुड़ा",
    "subdivision": null,
    "district": "बस्तर",
    "state": "छत्तीसगढ़",
    "lat": 19.1136,
    "lng": 81.8094,
    "formatted_address": "Main Road, ग्राम मादर, ब्लॉक लोहंडीगुड़ा, जिला बस्तर, छत्तीसगढ़"
  }
}
```

---

## Testing from Mobile App

### UpdateAddressScreen

The new `UpdateAddressScreen` component provides a full UI for testing location APIs:

1. **GPS Detection**:
   - Tap "GPS से पता लगाएं" button
   - Grants location permission
   - Calls `/api/location/detect-from-gps`
   - Auto-fills form with detected address

2. **Manual Entry**:
   - Fill in village, district, etc.
   - Tap "पता सत्यापित करें" to validate
   - Calls `/api/location/validate-address`

3. **Save to Profile**:
   - Tap "सहेजें" to save
   - Calls `/api/location/update-user-location`
   - Updates user profile in database

**To Add to Navigation**:
```typescript
// In your stack navigator
<Stack.Screen
  name="UpdateAddress"
  component={UpdateAddressScreen}
  options={{ headerShown: false }}
/>
```

**To Navigate from ProfileScreen**:
```typescript
<TouchableOpacity onPress={() => navigation.navigate('UpdateAddress' as never)}>
  <Text>पता अपडेट करें / Update Address</Text>
</TouchableOpacity>
```

---

## API Provider Behavior

### Mappls (MapmyIndia)
- **Free Tier**: 5,000 requests/day
- **Accuracy**: Best for Indian locations (especially urban areas)
- **Language**: Supports Hindi natively
- **Coverage**: All of India

### Nominatim (OpenStreetMap)
- **Free Tier**: Unlimited with rate limiting (1 req/sec)
- **Accuracy**: Good for rural areas, variable for villages
- **Language**: Primarily English, some Hindi coverage
- **Coverage**: Worldwide

### Hybrid Validator Logic
```python
# Priority order:
1. Try Mappls first (better accuracy for India)
2. If Mappls fails or low confidence → Try Nominatim
3. Return best result based on confidence score
4. Minimum confidence threshold: 0.5
```

---

## Error Handling

### Low Confidence (< 0.5)
```json
{
  "detail": "Could not detect location from GPS coordinates. Please enter address manually."
}
```

### Invalid Address
```json
{
  "detail": "Could not validate address. Please check spelling or provide more details."
}
```

### Missing Required Fields
```json
{
  "detail": "Must provide either GPS coordinates or at least village/district"
}
```

---

## Testing Scenarios

### Scenario 1: Urban Location (High Accuracy)
```bash
# Raipur city center
curl -X POST "http://localhost:8000/api/location/detect-from-gps?lat=21.2514&lng=81.6296"
# Expected: High confidence (0.9+), detailed address
```

### Scenario 2: Rural Village (Moderate Accuracy)
```bash
# Remote village in Bastar
curl -X POST "http://localhost:8000/api/location/detect-from-gps?lat=18.8933&lng=81.3532"
# Expected: Moderate confidence (0.6-0.8), basic hierarchy
```

### Scenario 3: Hindi Address Validation
```bash
curl -X POST "http://localhost:8000/api/location/validate-address" \
  -H "Content-Type: application/json" \
  -d '{"address": "मादर गाँव, लोहंडीगुड़ा ब्लॉक, बस्तर जिला", "state_hint": "Chhattisgarh"}'
# Expected: Normalized Hindi address with lat/lng
```

### Scenario 4: Partial Address (Only District)
```bash
curl -X POST "http://localhost:8000/api/location/validate-address" \
  -H "Content-Type: application/json" \
  -d '{"address": "Bastar District", "state_hint": "Chhattisgarh"}'
# Expected: District-level location with approximate center coordinates
```

---

## Performance Metrics

### Expected Response Times
- GPS Detection: 200-800ms (Mappls), 500-1500ms (Nominatim)
- Address Validation: 300-1000ms (varies by provider)
- Database Update: < 100ms

### Rate Limits
- Mappls: 5,000/day = ~208 requests/hour = ~3.5 requests/minute
- Nominatim: 1 request/second = 3,600 requests/hour

### Caching Strategy
- Successful geocoding results cached for 24 hours
- Reduces API calls for frequently accessed locations
- Cache key: `{lat},{lng}` or `{address_hash}`

---

## Next Steps

### 1. Test All Three Endpoints
Run the curl commands above to see how each endpoint works.

### 2. Test Mobile UI
- Navigate to UpdateAddressScreen
- Try GPS detection
- Try manual entry with validation
- Save address and verify in ProfileScreen

### 3. Monitor API Usage
- Check logs for `source` field in responses
- Track Mappls vs Nominatim usage
- Monitor confidence scores

### 4. LGD Integration (Pending)
- Scrape authoritative data from https://lgdirectory.gov.in
- Add LGD codes to validation
- Cross-reference with free APIs for accuracy
