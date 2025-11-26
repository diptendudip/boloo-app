"""
MapMyIndia (Mappls) location validator.

Best free option for Indian locations with 5K requests/day.
Better rural coverage than Google Maps in India.
"""

import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class MapplsValidator:
    """Validate locations using MapMyIndia (Mappls) API."""

    def __init__(self, api_key: str):
        """
        Initialize Mappls validator.

        Args:
            api_key: Mappls API key (get free at https://apis.mappls.com/console/)
        """
        self.api_key = api_key
        self.geocode_url = "https://atlas.mappls.com/api/places/geocode"
        self.reverse_url = "https://apis.mappls.com/advancedmaps/v1"

        logger.info("MapplsValidator initialized")

    def validate_and_enrich_location(
        self,
        location_text: str,
        district_hint: Optional[str] = None,
        state_hint: Optional[str] = "Chhattisgarh"
    ) -> Dict[str, Any]:
        """
        Validate location using Mappls Geocoding API.

        Free tier: 5,000 requests/day

        Args:
            location_text: Location to validate
            district_hint: Optional district for better results
            state_hint: Optional state (default: Chhattisgarh)

        Returns:
            Standardized location result dict
        """
        if not location_text:
            return self._empty_result()

        try:
            # Build query with hints
            query = f"{location_text}"
            if district_hint:
                query += f", {district_hint}"
            if state_hint:
                query += f", {state_hint}"
            query += ", India"

            # Call Geocoding API
            params = {
                "address": query,
                "access_token": self.api_key
            }

            response = requests.get(
                self.geocode_url,
                params=params,
                timeout=5
            )
            response.raise_for_status()

            data = response.json()

            if data.get("copResults"):
                result = data["copResults"][0]
                return self._parse_geocode_result(result)

            logger.info(f"No Mappls results for: {location_text}")
            return self._empty_result()

        except Exception as e:
            logger.error(f"Mappls error: {e}", exc_info=True)
            return self._empty_result()

    def reverse_geocode(
        self,
        lat: float,
        lng: float,
        language: str = "hi"
    ) -> Dict[str, Any]:
        """
        Reverse geocode coordinates using Mappls.

        Args:
            lat: Latitude
            lng: Longitude
            language: Language preference ("hi" or "en")

        Returns:
            Standardized location result dict
        """
        try:
            # Mappls reverse geocode endpoint
            url = f"{self.reverse_url}/{self.api_key}/rev_geocode"

            params = {
                "lat": lat,
                "lng": lng,
                "lang": language
            }

            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()

            data = response.json()

            if data.get("results"):
                result = data["results"][0]
                return self._parse_reverse_result(result)

            return self._empty_result()

        except Exception as e:
            logger.error(f"Mappls reverse error: {e}", exc_info=True)
            return self._empty_result()

    def _parse_geocode_result(self, result: Dict) -> Dict[str, Any]:
        """Parse geocoding result into standardized format."""
        return {
            "is_valid": True,
            "place_id": result.get("eLoc"),  # Mappls eLoc code
            "formatted_name": result.get("placeName", ""),
            "formatted_address": result.get("placeAddress", ""),
            "lat": float(result.get("latitude", 0)),
            "lng": float(result.get("longitude", 0)),
            "admin_hierarchy": {
                "village": result.get("village"),
                "panchayat": result.get("subSubLocality"),
                "block": result.get("subDistrict"),
                "district": result.get("district"),
                "state": result.get("state"),
                "country": "India"
            },
            "confidence": 0.9,  # Mappls has excellent India coverage
            "source": "mappls"
        }

    def _parse_reverse_result(self, result: Dict) -> Dict[str, Any]:
        """Parse reverse geocode result."""
        return {
            "is_valid": True,
            "place_id": result.get("eLoc"),
            "formatted_name": result.get("formatted_address", ""),
            "formatted_address": result.get("formatted_address", ""),
            "lat": float(result.get("lat", 0)),
            "lng": float(result.get("lng", 0)),
            "admin_hierarchy": {
                "street": result.get("street"),
                "village": result.get("village"),
                "panchayat": result.get("subSubLocality"),
                "block": result.get("subDistrict"),
                "district": result.get("district"),
                "state": result.get("state"),
                "country": "India"
            },
            "confidence": 0.9,
            "source": "mappls"
        }

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result."""
        return {
            "is_valid": False,
            "place_id": None,
            "formatted_name": None,
            "formatted_address": None,
            "lat": None,
            "lng": None,
            "admin_hierarchy": {},
            "confidence": 0.0,
            "source": "mappls_not_found"
        }
