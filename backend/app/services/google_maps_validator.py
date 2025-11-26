"""
Google Maps API integration for location validation and geocoding.

This service acts as a SUPPLEMENTARY layer to validate and enhance location data
extracted by the deterministic parser in completeness_analyzer.py.

Use cases:
1. Validate that extracted location names are real places
2. Normalize location names to canonical forms
3. Get coordinates (lat/lng) for mapping
4. Resolve ambiguous cases
5. Handle transliteration variations
"""

import logging
import requests
from typing import Dict, Any, Optional, List, Tuple
from app.config import settings

logger = logging.getLogger(__name__)


class GoogleMapsValidatorError(Exception):
    """Base exception for Google Maps validator errors"""
    pass


class GoogleMapsValidator:
    """
    Validates and enriches location data using Google Maps Platform APIs.

    Uses Places API (new v1) for text search and Geocoding API for reverse geocoding.
    Respects privacy by only calling when user explicitly provides location info.
    """

    def __init__(self):
        """Initialize Google Maps validator with API key from settings."""
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        if not self.api_key:
            logger.warning("Google Maps API key not configured - validation will be skipped")

        # API endpoints
        self.places_text_search_url = "https://places.googleapis.com/v1/places:searchText"
        self.geocoding_url = "https://maps.googleapis.com/maps/api/geocode/json"

        logger.info("GoogleMapsValidator initialized")

    def validate_and_enrich_location(
        self,
        location_text: str,
        district_hint: Optional[str] = None,
        state_hint: Optional[str] = "Chhattisgarh"
    ) -> Dict[str, Any]:
        """
        Validate location text and enrich with structured data.

        Args:
            location_text: Raw location string (e.g., "डोंगरीगुड़ा पंचायत, अलवा ब्लाक, बस्तर")
            district_hint: Optional district name for location bias
            state_hint: Optional state name (default: Chhattisgarh)

        Returns:
            Dict containing:
                - is_valid: bool (True if location found in Google Maps)
                - place_id: str (Google Place ID for reference)
                - formatted_name: str (Canonical name from Google)
                - lat: float
                - lng: float
                - admin_hierarchy: Dict with village/panchayat/block/district/state
                - confidence: float (0.0-1.0)
                - source: str ("google_maps")

        Example:
            >>> validator = GoogleMapsValidator()
            >>> result = validator.validate_and_enrich_location(
            ...     "डोंगरीगुड़ा पंचायत अलवा ब्लाक बस्तर",
            ...     district_hint="बस्तर",
            ...     state_hint="Chhattisgarh"
            ... )
            >>> print(result)
            {
                "is_valid": True,
                "place_id": "ChIJ...",
                "formatted_name": "Dongriguda, Chhattisgarh",
                "lat": 19.123,
                "lng": 81.456,
                "admin_hierarchy": {...},
                "confidence": 0.85
            }
        """
        if not self.api_key:
            logger.warning("Google Maps API key not configured - skipping validation")
            return self._empty_result()

        if not location_text or not location_text.strip():
            return self._empty_result()

        try:
            # Build location bias (rectangular bounds) around state/district
            location_bias = self._build_location_bias(state_hint, district_hint)

            # Try Places Text Search with Hindi first
            result = self._search_places_text(
                query=location_text,
                location_bias=location_bias,
                language="hi"
            )

            # If no results, try with transliterated/English version
            if not result["is_valid"]:
                logger.info(f"No results in Hindi, trying transliterated query")
                transliterated = self._simple_transliterate(location_text)
                result = self._search_places_text(
                    query=transliterated,
                    location_bias=location_bias,
                    language="en"
                )

            return result

        except Exception as e:
            logger.error(f"Error in validate_and_enrich_location: {e}", exc_info=True)
            return self._empty_result()

    def reverse_geocode(
        self,
        lat: float,
        lng: float,
        language: str = "hi"
    ) -> Dict[str, Any]:
        """
        Reverse geocode coordinates to get location details.

        Useful when user shares GPS location or taps map.

        Args:
            lat: Latitude
            lng: Longitude
            language: Language code ("hi" or "en")

        Returns:
            Dict with location details (same format as validate_and_enrich_location)
        """
        if not self.api_key:
            return self._empty_result()

        try:
            params = {
                "latlng": f"{lat},{lng}",
                "language": language,
                "key": self.api_key,
                "result_type": "locality|sublocality|administrative_area_level_3"
            }

            response = requests.get(self.geocoding_url, params=params, timeout=5)
            response.raise_for_status()

            data = response.json()

            if data.get("status") == "OK" and data.get("results"):
                top_result = data["results"][0]
                return self._parse_geocoding_result(top_result, confidence=0.9)
            else:
                logger.warning(f"Reverse geocoding failed: {data.get('status')}")
                return self._empty_result()

        except Exception as e:
            logger.error(f"Error in reverse_geocode: {e}", exc_info=True)
            return self._empty_result()

    def _search_places_text(
        self,
        query: str,
        location_bias: Optional[Dict] = None,
        language: str = "hi"
    ) -> Dict[str, Any]:
        """Internal: Call Places Text Search API."""
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location,places.addressComponents"
        }

        body = {
            "textQuery": query,
            "languageCode": language,
            "regionCode": "IN",
            "maxResultCount": 5
        }

        if location_bias:
            body["locationBias"] = location_bias

        try:
            response = requests.post(
                self.places_text_search_url,
                headers=headers,
                json=body,
                timeout=5
            )
            response.raise_for_status()

            data = response.json()

            if data.get("places"):
                top_result = data["places"][0]
                return self._parse_places_result(top_result, confidence=0.85)
            else:
                logger.info(f"No places found for query: {query}")
                return self._empty_result()

        except Exception as e:
            logger.error(f"Places API error: {e}", exc_info=True)
            return self._empty_result()

    def _parse_places_result(self, place: Dict, confidence: float) -> Dict[str, Any]:
        """Parse Places API result into standardized format."""
        location = place.get("location", {})

        # Extract admin hierarchy from addressComponents
        admin_hierarchy = self._extract_admin_hierarchy(
            place.get("addressComponents", [])
        )

        return {
            "is_valid": True,
            "place_id": place.get("id", ""),
            "formatted_name": place.get("displayName", {}).get("text", ""),
            "formatted_address": place.get("formattedAddress", ""),
            "lat": location.get("latitude"),
            "lng": location.get("longitude"),
            "admin_hierarchy": admin_hierarchy,
            "confidence": confidence,
            "source": "google_places",
            "language": place.get("displayName", {}).get("languageCode", "hi")
        }

    def _parse_geocoding_result(self, result: Dict, confidence: float) -> Dict[str, Any]:
        """Parse Geocoding API result into standardized format."""
        location = result.get("geometry", {}).get("location", {})

        admin_hierarchy = self._extract_admin_hierarchy_geocoding(
            result.get("address_components", [])
        )

        return {
            "is_valid": True,
            "place_id": result.get("place_id", ""),
            "formatted_name": result.get("formatted_address", ""),
            "formatted_address": result.get("formatted_address", ""),
            "lat": location.get("lat"),
            "lng": location.get("lng"),
            "admin_hierarchy": admin_hierarchy,
            "confidence": confidence,
            "source": "google_geocoding"
        }

    def _extract_admin_hierarchy(self, components: List[Dict]) -> Dict[str, str]:
        """Extract village/panchayat/block/district/state from Places API addressComponents."""
        hierarchy = {}

        for component in components:
            types = component.get("types", [])
            name = component.get("longText", "")

            if "locality" in types:
                hierarchy["village"] = name
            elif "sublocality" in types or "sublocality_level_1" in types:
                hierarchy["panchayat"] = name
            elif "administrative_area_level_3" in types:
                hierarchy["block"] = name
            elif "administrative_area_level_2" in types:
                hierarchy["district"] = name
            elif "administrative_area_level_1" in types:
                hierarchy["state"] = name
            elif "country" in types:
                hierarchy["country"] = name

        return hierarchy

    def _extract_admin_hierarchy_geocoding(self, components: List[Dict]) -> Dict[str, str]:
        """Extract admin hierarchy from Geocoding API address_components."""
        hierarchy = {}

        for component in components:
            types = component.get("types", [])
            name = component.get("long_name", "")

            if "locality" in types:
                hierarchy["village"] = name
            elif "sublocality" in types:
                hierarchy["panchayat"] = name
            elif "administrative_area_level_3" in types:
                hierarchy["block"] = name
            elif "administrative_area_level_2" in types:
                hierarchy["district"] = name
            elif "administrative_area_level_1" in types:
                hierarchy["state"] = name
            elif "country" in types:
                hierarchy["country"] = name

        return hierarchy

    def _build_location_bias(
        self,
        state: Optional[str],
        district: Optional[str]
    ) -> Optional[Dict]:
        """
        Build rectangular location bias for API call.

        Centers on known regions in Chhattisgarh.
        """
        # Chhattisgarh state bounds (approximate)
        cg_bounds = {
            "low": {"latitude": 17.5, "longitude": 80.0},
            "high": {"latitude": 24.0, "longitude": 84.5}
        }

        # District-specific bounds (add more as needed)
        district_bounds = {
            "बस्तर": {
                "low": {"latitude": 18.5, "longitude": 80.8},
                "high": {"latitude": 20.0, "longitude": 82.5}
            },
            "bastar": {
                "low": {"latitude": 18.5, "longitude": 80.8},
                "high": {"latitude": 20.0, "longitude": 82.5}
            },
            # Add more districts as needed
        }

        # Try district-specific bounds first
        if district:
            district_key = district.lower().strip()
            if district_key in district_bounds:
                return {"rectangle": district_bounds[district_key]}

        # Fall back to state bounds
        if state and "chhattisgarh" in state.lower():
            return {"rectangle": cg_bounds}

        # Default to India (very broad)
        return {"rectangle": {
            "low": {"latitude": 8.0, "longitude": 68.0},
            "high": {"latitude": 35.0, "longitude": 97.0}
        }}

    def _simple_transliterate(self, text: str) -> str:
        """
        Simple Hindi to Latin transliteration.

        Note: This is basic. For production, use a proper transliteration library
        like 'indic-transliteration' or Google Translate API.
        """
        # Basic character mapping (extend as needed)
        transliteration_map = {
            "ड": "d", "ो": "o", "ं": "n", "ग": "g", "र": "r", "ी": "i",
            "गु": "gu", "ड़": "d", "ा": "a", "प": "p", "ञ": "n", "च": "ch",
            "य": "y", "त": "t", "अ": "a", "ल": "l", "व": "v", "ा": "a",
            "ब": "b", "स": "s", "टा": "ta", "ख": "kh", "ं": "m"
        }

        # This is a placeholder - replace with proper library
        # For now, just return original (API handles transliteration internally)
        return text

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result when validation fails or is skipped."""
        return {
            "is_valid": False,
            "place_id": None,
            "formatted_name": None,
            "formatted_address": None,
            "lat": None,
            "lng": None,
            "admin_hierarchy": {},
            "confidence": 0.0,
            "source": "validation_skipped"
        }
