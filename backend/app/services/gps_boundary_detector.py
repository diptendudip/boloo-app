"""
GPS to Administrative Boundary Detection Module

Converts GPS coordinates (lat, lng) to administrative boundaries:
- Block, Subdivision, District, State

Uses hybrid approach with free validators for $0 cost.
"""

import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AdminBoundary:
    """Administrative boundary information detected from GPS."""
    street: Optional[str] = None
    village: Optional[str] = None
    panchayat: Optional[str] = None
    block: Optional[str] = None
    subdivision: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = "India"

    # GPS coordinates
    lat: Optional[float] = None
    lng: Optional[float] = None

    # Metadata
    confidence: float = 0.0
    source: str = "unknown"
    formatted_address: Optional[str] = None


class GPSBoundaryDetector:
    """
    Detect administrative boundaries from GPS coordinates.

    Features:
    - Reverse geocoding (GPS → address)
    - Administrative hierarchy extraction
    - Multi-source validation (Nominatim, Mappls)
    - Offline caching for performance

    Use Case: Signup flow where user shares GPS location
    """

    def __init__(self):
        """Initialize GPS boundary detector with available validators."""
        # Import validators lazily to avoid circular dependencies
        from app.services.nominatim_validator import NominatimValidator

        self.nominatim = NominatimValidator()

        # Initialize Mappls if API key available
        self.mappls = None
        try:
            from app.services.mappls_validator import MapplsValidator
            from app.config import settings

            if settings.MAPPLS_API_KEY:
                self.mappls = MapplsValidator(settings.MAPPLS_API_KEY)
                logger.info("Mappls validator initialized for GPS detection")
        except Exception as e:
            logger.warning(f"Mappls not available: {e}")

        logger.info("GPSBoundaryDetector initialized")

    def detect_from_gps(
        self,
        lat: float,
        lng: float,
        language: str = "hi"
    ) -> AdminBoundary:
        """
        Detect administrative boundaries from GPS coordinates.

        Args:
            lat: Latitude
            lng: Longitude
            language: Preferred language for results ("hi" or "en")

        Returns:
            AdminBoundary with detected hierarchy

        Example:
            >>> detector = GPSBoundaryDetector()
            >>> boundary = detector.detect_from_gps(19.123, 81.456)
            >>> print(boundary.district)  # "Bastar"
            >>> print(boundary.block)      # "Lohandiguda"
            >>> print(boundary.village)    # "Dongriguda"
        """
        if not lat or not lng:
            return self._empty_boundary()

        # Validate coordinates are in India
        if not self._is_india_coordinate(lat, lng):
            logger.warning(f"Coordinates outside India: {lat}, {lng}")
            return self._empty_boundary()

        # Try Mappls first (best India coverage)
        if self.mappls:
            logger.info(f"Trying Mappls reverse geocode: {lat}, {lng}")
            result = self._try_mappls_reverse(lat, lng)
            if result and result.confidence >= 0.8:
                logger.info(f"✅ Mappls detected: {result.district}, {result.block}")
                return result

        # Fallback to Nominatim (OpenStreetMap)
        logger.info(f"Trying Nominatim reverse geocode: {lat}, {lng}")
        result = self._try_nominatim_reverse(lat, lng, language)
        if result and result.confidence >= 0.7:
            logger.info(f"✅ Nominatim detected: {result.district}, {result.block}")
            return result

        logger.warning(f"⚠️ Could not detect boundaries for: {lat}, {lng}")
        return self._empty_boundary()

    def detect_from_address(
        self,
        address: str,
        district_hint: Optional[str] = None,
        state_hint: Optional[str] = "Chhattisgarh"
    ) -> AdminBoundary:
        """
        Detect administrative boundaries from text address.

        Useful when user types address instead of sharing GPS.

        Args:
            address: Text address (e.g., "Dongriguda, Bastar")
            district_hint: Optional district for better results
            state_hint: Optional state (default: Chhattisgarh)

        Returns:
            AdminBoundary with detected hierarchy
        """
        from app.services.location_validator import HybridLocationValidator

        validator = HybridLocationValidator()
        result = validator.validate_and_enrich_location(
            location_text=address,
            district_hint=district_hint,
            state_hint=state_hint
        )

        if result["is_valid"]:
            return self._result_to_boundary(result)
        else:
            return self._empty_boundary()

    def _try_mappls_reverse(
        self,
        lat: float,
        lng: float
    ) -> Optional[AdminBoundary]:
        """Try reverse geocoding with Mappls."""
        if not self.mappls:
            return None

        try:
            result = self.mappls.reverse_geocode(lat, lng)
            if result["is_valid"]:
                return self._result_to_boundary(result)
        except Exception as e:
            logger.error(f"Mappls reverse error: {e}", exc_info=True)

        return None

    def _try_nominatim_reverse(
        self,
        lat: float,
        lng: float,
        language: str
    ) -> Optional[AdminBoundary]:
        """Try reverse geocoding with Nominatim."""
        try:
            result = self.nominatim.reverse_geocode(lat, lng, language)
            if result["is_valid"]:
                return self._result_to_boundary(result)
        except Exception as e:
            logger.error(f"Nominatim reverse error: {e}", exc_info=True)

        return None

    def _result_to_boundary(self, result: Dict[str, Any]) -> AdminBoundary:
        """Convert validator result to AdminBoundary."""
        hierarchy = result.get("admin_hierarchy", {})

        return AdminBoundary(
            street=hierarchy.get("street"),
            village=hierarchy.get("village"),
            panchayat=hierarchy.get("panchayat"),
            block=hierarchy.get("block") or hierarchy.get("county"),
            subdivision=hierarchy.get("subdivision"),
            district=hierarchy.get("district") or hierarchy.get("state_district"),
            state=hierarchy.get("state"),
            country=hierarchy.get("country", "India"),
            lat=result.get("lat"),
            lng=result.get("lng"),
            confidence=result.get("confidence", 0.0),
            source=result.get("source", "unknown"),
            formatted_address=result.get("formatted_address")
        )

    def _is_india_coordinate(self, lat: float, lng: float) -> bool:
        """Check if coordinates are within India bounds."""
        # India approximate bounds
        return (
            6.0 <= lat <= 36.0 and
            68.0 <= lng <= 97.5
        )

    def _empty_boundary(self) -> AdminBoundary:
        """Return empty boundary when detection fails."""
        return AdminBoundary(
            confidence=0.0,
            source="detection_failed"
        )


# Utility functions for easy usage

def detect_boundaries_from_gps(
    lat: float,
    lng: float,
    language: str = "hi"
) -> AdminBoundary:
    """
    Convenience function to detect boundaries from GPS.

    Usage:
        from app.services.gps_boundary_detector import detect_boundaries_from_gps

        boundary = detect_boundaries_from_gps(19.123, 81.456)
        print(f"District: {boundary.district}")
        print(f"Block: {boundary.block}")
    """
    detector = GPSBoundaryDetector()
    return detector.detect_from_gps(lat, lng, language)


def detect_boundaries_from_address(
    address: str,
    district_hint: Optional[str] = None
) -> AdminBoundary:
    """
    Convenience function to detect boundaries from text address.

    Usage:
        from app.services.gps_boundary_detector import detect_boundaries_from_address

        boundary = detect_boundaries_from_address("Dongriguda, Bastar")
        print(f"Block: {boundary.block}")
    """
    detector = GPSBoundaryDetector()
    return detector.detect_from_address(address, district_hint)
