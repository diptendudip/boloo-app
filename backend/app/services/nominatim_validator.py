"""
Nominatim (OpenStreetMap) location validator.

Free alternative to Google Maps using OpenStreetMap data.
Public API for testing, self-host for production.
"""

import logging
import requests
from typing import Dict, Any, Optional
from time import sleep

logger = logging.getLogger(__name__)


class NominatimValidator:
    """
    Validate locations using Nominatim (OpenStreetMap Geocoding).

    Free, privacy-friendly alternative to Google Maps.
    Uses public API for testing, recommend self-hosting for production.
    """

    def __init__(self, base_url: str = "https://nominatim.openstreetmap.org"):
        """
        Initialize Nominatim validator.

        Args:
            base_url: Nominatim API endpoint (default: public OSM)
                     For production, self-host at http://localhost:8080
        """
        self.base_url = base_url
        self.headers = {
            "User-Agent": "BolooApp/1.0 (diptendudip@gmail.com)"  # Required by OSM
        }
        logger.info(f"NominatimValidator initialized (endpoint: {base_url})")

    def validate_and_enrich_location(
        self,
        location_text: str,
        district_hint: Optional[str] = None,
        state_hint: Optional[str] = "Chhattisgarh"
    ) -> Dict[str, Any]:
        """
        Validate location text using Nominatim search.

        Args:
            location_text: Raw location (e.g., "डोंगरीगुड़ा पंचायत, बस्तर")
            district_hint: Optional district for better results
            state_hint: Optional state (default: Chhattisgarh)

        Returns:
            {
                "is_valid": bool,
                "place_id": str,
                "formatted_name": str,
                "lat": float,
                "lng": float,
                "admin_hierarchy": {...},
                "confidence": float (0.0-1.0),
                "source": "nominatim"
            }
        """
        if not location_text or not location_text.strip():
            return self._empty_result()

        try:
            # Build search query with bias
            query = self._build_query(location_text, district_hint, state_hint)

            # Call Nominatim search API
            params = {
                "q": query,
                "format": "json",
                "addressdetails": 1,
                "limit": 5,
                "countrycodes": "in",
                "accept-language": "hi,en"
            }

            # Rate limiting: Public OSM API allows 1 request/second
            sleep(1)  # Be respectful to public API

            response = requests.get(
                f"{self.base_url}/search",
                params=params,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()

            results = response.json()

            if results:
                # Take best match
                top_result = results[0]
                return self._parse_result(top_result)
            else:
                logger.info(f"No results found for: {location_text}")
                return self._empty_result()

        except Exception as e:
            logger.error(f"Nominatim error: {e}", exc_info=True)
            return self._empty_result()

    def reverse_geocode(
        self,
        lat: float,
        lng: float,
        language: str = "hi"
    ) -> Dict[str, Any]:
        """
        Reverse geocode coordinates to location details.

        Args:
            lat: Latitude
            lng: Longitude
            language: Language code ("hi" or "en")

        Returns:
            Same format as validate_and_enrich_location()
        """
        try:
            params = {
                "lat": lat,
                "lon": lng,
                "format": "json",
                "addressdetails": 1,
                "accept-language": f"{language},en"
            }

            sleep(1)  # Rate limiting

            response = requests.get(
                f"{self.base_url}/reverse",
                params=params,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()

            result = response.json()
            return self._parse_result(result, confidence=0.9)

        except Exception as e:
            logger.error(f"Reverse geocode error: {e}", exc_info=True)
            return self._empty_result()

    def _build_query(
        self,
        location_text: str,
        district: Optional[str],
        state: Optional[str]
    ) -> str:
        """Build search query with geographic bias."""
        parts = [location_text]

        if district:
            parts.append(district)
        if state:
            parts.append(state)

        parts.append("India")

        return ", ".join(parts)

    def _parse_result(self, result: Dict, confidence: float = 0.75) -> Dict[str, Any]:
        """Parse Nominatim result into standardized format."""
        address = result.get("address", {})

        # Extract admin hierarchy
        admin_hierarchy = {
            "village": address.get("village") or address.get("hamlet"),
            "panchayat": address.get("suburb") or address.get("neighbourhood"),
            "block": address.get("county"),
            "district": address.get("state_district"),
            "state": address.get("state"),
            "country": address.get("country")
        }

        # Clean up None values
        admin_hierarchy = {k: v for k, v in admin_hierarchy.items() if v}

        return {
            "is_valid": True,
            "place_id": str(result.get("place_id")),
            "formatted_name": result.get("display_name", ""),
            "formatted_address": result.get("display_name", ""),
            "lat": float(result.get("lat", 0)),
            "lng": float(result.get("lon", 0)),
            "admin_hierarchy": admin_hierarchy,
            "confidence": confidence,
            "source": "nominatim",
            "osm_type": result.get("osm_type"),
            "osm_id": result.get("osm_id")
        }

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result when validation fails."""
        return {
            "is_valid": False,
            "place_id": None,
            "formatted_name": None,
            "formatted_address": None,
            "lat": None,
            "lng": None,
            "admin_hierarchy": {},
            "confidence": 0.0,
            "source": "nominatim_not_found"
        }
