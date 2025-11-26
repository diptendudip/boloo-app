"""
Location API endpoints for signup and report filing
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.location import LocationCapture, LocationResponse
from app.services.gps_boundary_detector import GPSBoundaryDetector
from app.services.location_validator import HybridLocationValidator
from app.models.user import User
from app.utils.auth import get_current_user_or_dev

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/location", tags=["location"])


@router.post("/detect-from-gps", response_model=LocationResponse)
async def detect_from_gps(
    lat: float,
    lng: float,
    language: str = "hi",
    current_user: User = Depends(get_current_user_or_dev),
    db: Session = Depends(get_db)
):
    """
    Detect administrative boundaries from GPS coordinates.

    Use case: During signup, user shares GPS location from phone.
    System auto-detects block, district, state, etc.

    **Free**: Uses Mappls (5K/day free) or Nominatim (unlimited).
    """
    try:
        logger.info(f"Detecting boundaries for GPS: {lat}, {lng}")

        detector = GPSBoundaryDetector()
        boundary = detector.detect_from_gps(lat, lng, language)

        if boundary.confidence < 0.5:
            logger.warning(f"Low confidence detection: {boundary.confidence}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Could not detect location from GPS coordinates. Please enter address manually."
            )

        return LocationResponse(
            street=boundary.street,
            village=boundary.village,
            panchayat=boundary.panchayat,
            block=boundary.block,
            subdivision=boundary.subdivision,
            district=boundary.district,
            state=boundary.state,
            country=boundary.country,
            lat=boundary.lat,
            lng=boundary.lng,
            formatted_address=boundary.formatted_address,
            confidence=boundary.confidence,
            source=boundary.source
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GPS detection error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to detect location from GPS"
        )


@router.post("/validate-address", response_model=LocationResponse)
async def validate_address(
    address: str,
    district_hint: str = None,
    state_hint: str = "Chhattisgarh",
    current_user: User = Depends(get_current_user_or_dev),
    db: Session = Depends(get_db)
):
    """
    Validate and normalize text address.

    Use case: User types address manually during signup.
    System validates it and auto-fills block, district, etc.

    **Free**: Uses hybrid validator (Mappls + Nominatim).
    """
    try:
        logger.info(f"Validating address: {address}")

        validator = HybridLocationValidator()
        result = validator.validate_and_enrich_location(
            location_text=address,
            district_hint=district_hint,
            state_hint=state_hint
        )

        if not result["is_valid"]:
            logger.warning(f"Address validation failed: {address}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Could not validate address. Please check spelling or provide more details."
            )

        hierarchy = result.get("admin_hierarchy", {})

        return LocationResponse(
            street=hierarchy.get("street"),
            village=hierarchy.get("village"),
            panchayat=hierarchy.get("panchayat"),
            block=hierarchy.get("block"),
            subdivision=hierarchy.get("subdivision"),
            district=hierarchy.get("district"),
            state=hierarchy.get("state"),
            country=hierarchy.get("country", "India"),
            lat=result.get("lat"),
            lng=result.get("lng"),
            formatted_address=result.get("formatted_address"),
            confidence=result.get("confidence", 0.0),
            source=result.get("source", "unknown")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Address validation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate address"
        )


@router.post("/update-user-location")
async def update_user_location(
    location: LocationCapture,
    current_user: User = Depends(get_current_user_or_dev),
    db: Session = Depends(get_db)
):
    """
    Update user's location during signup.

    Accepts either:
    1. GPS coordinates (lat/lng) → auto-detects boundaries
    2. Manual address fields → validates and normalizes

    **Use case**: Called during signup after user provides location.
    """
    try:
        logger.info(f"Updating location for user {current_user.id}")

        # If GPS provided, detect boundaries
        if location.lat and location.lng:
            detector = GPSBoundaryDetector()
            boundary = detector.detect_from_gps(location.lat, location.lng)

            if boundary.confidence >= 0.7:
                # Use detected boundaries
                current_user.location_street = location.street or boundary.street
                current_user.location_village = boundary.village
                current_user.location_panchayat = boundary.panchayat
                current_user.location_block = boundary.block
                current_user.location_subdivision = boundary.subdivision
                current_user.location_district = boundary.district
                current_user.location_state = boundary.state
                current_user.location_lat = boundary.lat
                current_user.location_lng = boundary.lng
                current_user.location_formatted_address = boundary.formatted_address
                current_user.location_metadata = {
                    "source": boundary.source,
                    "confidence": boundary.confidence,
                    "detection_method": "gps"
                }
            else:
                # Fall back to manual fields
                logger.warning(f"GPS detection failed, using manual fields")
                current_user.location_street = location.street
                current_user.location_village = location.village
                current_user.location_panchayat = location.panchayat
                current_user.location_block = location.block
                current_user.location_subdivision = location.subdivision
                current_user.location_district = location.district
                current_user.location_state = location.state
                current_user.location_lat = location.lat
                current_user.location_lng = location.lng
                current_user.location_metadata = {
                    "source": "manual",
                    "detection_method": "gps_failed"
                }

        # If manual address provided without GPS
        elif location.village or location.district:
            # Validate address if possible
            if location.village and location.district:
                validator = HybridLocationValidator()
                result = validator.validate_and_enrich_location(
                    location_text=location.village,
                    district_hint=location.district,
                    state_hint=location.state or "Chhattisgarh"
                )

                if result["is_valid"]:
                    hierarchy = result.get("admin_hierarchy", {})
                    current_user.location_street = location.street
                    current_user.location_village = hierarchy.get("village") or location.village
                    current_user.location_panchayat = hierarchy.get("panchayat") or location.panchayat
                    current_user.location_block = hierarchy.get("block") or location.block
                    current_user.location_subdivision = location.subdivision
                    current_user.location_district = hierarchy.get("district") or location.district
                    current_user.location_state = hierarchy.get("state") or location.state
                    current_user.location_lat = result.get("lat")
                    current_user.location_lng = result.get("lng")
                    current_user.location_formatted_address = result.get("formatted_address")
                    current_user.location_metadata = {
                        "source": result.get("source"),
                        "confidence": result.get("confidence", 0.0),
                        "detection_method": "address_validation"
                    }
                else:
                    # Use manual fields as-is
                    current_user.location_street = location.street
                    current_user.location_village = location.village
                    current_user.location_panchayat = location.panchayat
                    current_user.location_block = location.block
                    current_user.location_subdivision = location.subdivision
                    current_user.location_district = location.district
                    current_user.location_state = location.state
                    current_user.location_metadata = {
                        "source": "manual",
                        "detection_method": "validation_failed"
                    }
            else:
                # Insufficient data for validation
                current_user.location_street = location.street
                current_user.location_village = location.village
                current_user.location_panchayat = location.panchayat
                current_user.location_block = location.block
                current_user.location_subdivision = location.subdivision
                current_user.location_district = location.district
                current_user.location_state = location.state
                current_user.location_metadata = {
                    "source": "manual",
                    "detection_method": "insufficient_data"
                }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must provide either GPS coordinates or at least village/district"
            )

        db.commit()
        db.refresh(current_user)

        logger.info(f"✅ Location updated for user {current_user.id}: {current_user.location_district}, {current_user.location_block}")

        return {
            "success": True,
            "message": "Location updated successfully",
            "location": {
                "street": current_user.location_street,
                "village": current_user.location_village,
                "panchayat": current_user.location_panchayat,
                "block": current_user.location_block,
                "subdivision": current_user.location_subdivision,
                "district": current_user.location_district,
                "state": current_user.location_state,
                "lat": current_user.location_lat,
                "lng": current_user.location_lng,
                "formatted_address": current_user.location_formatted_address
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Location update error: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update location"
        )
