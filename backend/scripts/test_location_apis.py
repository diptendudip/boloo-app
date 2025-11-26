#!/usr/bin/env python3
"""
Test script for location APIs

Tests GPS boundary detection and address validation endpoints
without authentication (to show how the APIs work).
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def print_response(title: str, response: requests.Response):
    """Pretty print API response"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print(f"✅ Success!")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    else:
        print(f"❌ Error: {response.text}")

def test_gps_detection(lat: float, lng: float, language: str = "hi"):
    """Test GPS boundary detection endpoint"""
    url = f"{BASE_URL}/api/location/detect-from-gps"
    params = {
        "lat": lat,
        "lng": lng,
        "language": language
    }

    print(f"\n📍 Testing GPS detection for coordinates: {lat}, {lng}")
    response = requests.post(url, params=params)
    print_response(f"GPS Detection: {lat}, {lng}", response)
    return response

def test_address_validation(address: str, district_hint: str = None, state_hint: str = "Chhattisgarh"):
    """Test address validation endpoint"""
    url = f"{BASE_URL}/api/location/validate-address"
    params = {
        "address": address,
        "state_hint": state_hint
    }
    if district_hint:
        params["district_hint"] = district_hint

    print(f"\n📝 Testing address validation for: {address}")
    response = requests.post(url, params=params)
    print_response(f"Address Validation: {address}", response)
    return response

def main():
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                  BOLOO LOCATION API TESTING                     ║
║                                                                 ║
║  Testing free geocoding APIs (Mappls + Nominatim)              ║
╚═══════════════════════════════════════════════════════════════╝
""")

    # Test 1: GPS detection in Bastar (rural Chhattisgarh)
    print("\n" + "▶"*30 + " TEST 1: GPS Detection - Bastar " + "◀"*30)
    test_gps_detection(19.1136, 81.8094, "hi")

    # Test 2: GPS detection in Raipur (urban Chhattisgarh)
    print("\n" + "▶"*30 + " TEST 2: GPS Detection - Raipur " + "◀"*30)
    test_gps_detection(21.2514, 81.6296, "hi")

    # Test 3: GPS detection in Dantewada
    print("\n" + "▶"*30 + " TEST 3: GPS Detection - Dantewada " + "◀"*30)
    test_gps_detection(18.8933, 81.3532, "hi")

    # Test 4: Hindi address validation
    print("\n" + "▶"*30 + " TEST 4: Address Validation - Hindi " + "◀"*30)
    test_address_validation("मादर गाँव, बस्तर", district_hint="Bastar")

    # Test 5: English address validation
    print("\n" + "▶"*30 + " TEST 5: Address Validation - English " + "◀"*30)
    test_address_validation("Lohandiguda Block, Bastar District", district_hint="Bastar")

    # Test 6: District-only validation
    print("\n" + "▶"*30 + " TEST 6: Address Validation - District Only " + "◀"*30)
    test_address_validation("Bastar District, Chhattisgarh")

    # Test 7: GPS detection in English
    print("\n" + "▶"*30 + " TEST 7: GPS Detection - English Language " + "◀"*30)
    test_gps_detection(19.1136, 81.8094, "en")

    print("""
\n╔═══════════════════════════════════════════════════════════════╗
║                      TESTING COMPLETE                           ║
║                                                                 ║
║  Check the responses above to see how the APIs work.            ║
║  Note: Some endpoints require authentication in production.     ║
╚═══════════════════════════════════════════════════════════════╝
""")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to backend server")
        print("   Make sure the backend is running at http://localhost:8000")
        print("   Run: cd backend && python3 -m uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
