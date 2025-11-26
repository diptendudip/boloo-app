"""
Location schemas for signup and reports
"""

from pydantic import BaseModel, Field
from typing import Optional


class LocationCapture(BaseModel):
    """
    Location data captured during signup or report filing.

    Can be populated via:
    1. GPS coordinates (user shares location) → auto-detect boundaries
    2. Manual address entry → validate with hybrid validator
    """

    # GPS coordinates (if user shares location)
    lat: Optional[float] = Field(None, description="GPS latitude")
    lng: Optional[float] = Field(None, description="GPS longitude")

    # Manual address fields (if user types address)
    street: Optional[str] = Field(None, max_length=255, description="Street/mohalla address")
    village: Optional[str] = Field(None, max_length=255, description="Village/town name")
    panchayat: Optional[str] = Field(None, max_length=255, description="Gram panchayat")
    block: Optional[str] = Field(None, max_length=255, description="Block/Tehsil")
    subdivision: Optional[str] = Field(None, max_length=255, description="Subdivision")
    district: Optional[str] = Field(None, max_length=255, description="District")
    state: Optional[str] = Field(None, max_length=255, description="State")

    # Automatically detected from GPS or validated address
    formatted_address: Optional[str] = Field(None, description="Full formatted address")

    class Config:
        json_schema_extra = {
            "example": {
                "lat": 19.123,
                "lng": 81.456,
                "street": "कोटेवार पारा",
                "village": "मादर",
                "panchayat": "मादर",
                "block": "लोहंडीगुड़ा",
                "district": "बस्तर",
                "state": "Chhattisgarh"
            }
        }


class LocationResponse(BaseModel):
    """Response after processing location (GPS or text)."""

    street: Optional[str] = None
    village: Optional[str] = None
    panchayat: Optional[str] = None
    block: Optional[str] = None
    subdivision: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = "India"
    lat: Optional[float] = None
    lng: Optional[float] = None
    formatted_address: Optional[str] = None
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    source: str = Field("unknown", description="Detection source (gps, nominatim, mappls, etc.)")

    class Config:
        json_schema_extra = {
            "example": {
                "village": "Dongriguda",
                "panchayat": "Madar",
                "block": "Lohandiguda",
                "district": "Bastar",
                "state": "Chhattisgarh",
                "country": "India",
                "lat": 19.123,
                "lng": 81.456,
                "formatted_address": "Dongriguda, Lohandiguda Block, Bastar District, Chhattisgarh, India",
                "confidence": 0.9,
                "source": "mappls"
            }
        }
