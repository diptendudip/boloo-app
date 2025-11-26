"""
Authentication router - OTP-based auth with security enhancements
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import JWTError, jwt
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging
import os

from app.database import get_db
from app.models import User, OTP
from app.services.email import send_otp_email
from app.services.msg91_service import msg91_service, MSG91Error, MSG91RateLimitError, MSG91InvalidPhoneError
from app.config import settings
from app.utils.security_logger import security_logger, SecurityEventType

router = APIRouter()
logger = logging.getLogger(__name__)

# SECURITY FIX #4: Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# HTTP Bearer security for token verification
security = HTTPBearer(auto_error=False)

# Demo account configuration - for overseas funders without Indian phone numbers
# This number with fixed OTP allows funders to test the app
# Can be configured via DEMO_PHONE_NUMBER environment variable
# Default: +919999999999 (starts with 9) to pass Indian mobile validation
DEMO_PHONE_NUMBER = os.getenv("DEMO_PHONE_NUMBER", "+919999999999")
DEMO_OTP_CODE = os.getenv("DEMO_OTP_CODE", "123456")
DEMO_USER_CONFIG = {
    "name": "Demo User (Funder)",
    "location_district": "Demo District",
    "location_state": "Demo State",
    "location_formatted_address": "Demo Location for Funders/Investors"
}


# Pydantic models
class OTPRequest(BaseModel):
    phone_number: str  # Format: +91XXXXXXXXXX


class OTPVerify(BaseModel):
    phone_number: str
    otp_code: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict


class OTPResend(BaseModel):
    phone_number: str
    retry_type: str = "text"  # "text" or "voice"


class ProfileUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    email: str | None = None  # Simple string, no validation needed for MVP


def create_access_token(user_id: str, phone_number: str = None, phone_verified: bool = False) -> str:
    """Create JWT access token with OTP verification status"""
    expires_delta = timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    expire = datetime.utcnow() + expires_delta

    to_encode = {
        "sub": user_id,
        "exp": expire,
        "type": "access",
        "phone_verified": phone_verified
    }

    # Add phone number to payload if provided
    if phone_number:
        to_encode["phone_number"] = phone_number

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


@router.post("/otp/request")
@limiter.limit("3/15minutes", key_func=get_remote_address)  # Rate limit by IP (body not available in key_func)
@limiter.limit("10/hour", key_func=get_remote_address)
async def request_otp(
    otp_request: OTPRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Request OTP via MSG91 SMS.
    Creates or updates user if not exists.

    SECURITY: Rate limited to 3 requests per phone per 15 minutes
    and 10 requests per IP per hour.
    """
    try:
        # Get client info for security logging
        client_ip = get_remote_address(request)
        user_agent = request.headers.get("user-agent", "unknown")

        # SECURITY FIX #6: Log OTP request
        security_logger.log_otp_request(
            phone_number=otp_request.phone_number,
            ip_address=client_ip,
            user_agent=user_agent
        )

        # Validate phone number format
        if not otp_request.phone_number.startswith('+91') or len(otp_request.phone_number) != 13:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number must be in format: +91XXXXXXXXXX"
            )

        # Check if user exists, create if not
        user = db.query(User).filter(User.phone == otp_request.phone_number).first()

        if not user:
            # PRODUCTION-READY: Auto-generate email from phone for rural users without email
            # This handles users who only have phone numbers (no email address)
            # Format: 919876543210@boloo-users.local (removes +)
            auto_generated_email = f"{otp_request.phone_number.replace('+', '')}@boloo-users.local"

            # Check if this is the demo account
            is_demo = otp_request.phone_number == DEMO_PHONE_NUMBER

            user = User(
                phone=otp_request.phone_number,
                email=auto_generated_email,  # Required by database constraint
                role="citizen",
                name=DEMO_USER_CONFIG["name"] if is_demo else None,
                location_district=DEMO_USER_CONFIG["location_district"] if is_demo else None,
                location_state=DEMO_USER_CONFIG["location_state"] if is_demo else None,
                location_formatted_address=DEMO_USER_CONFIG["location_formatted_address"] if is_demo else None
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Created new user: {otp_request.phone_number} with auto-generated email: {auto_generated_email}")

        # Handle DEMO account - don't send actual SMS
        if otp_request.phone_number == DEMO_PHONE_NUMBER:
            logger.info(f"Demo account OTP request: {otp_request.phone_number} - using fixed OTP")

            # Create OTP record with fixed demo code
            demo_otp = OTP(
                phone_number=otp_request.phone_number,
                otp_code=DEMO_OTP_CODE,
                expires_at=datetime.utcnow() + timedelta(hours=24),  # Demo OTP valid for 24 hours
                is_used=False
            )
            db.add(demo_otp)
            db.commit()

            return {
                "success": True,
                "message": f"OTP sent to {otp_request.phone_number}",
                "phone_number": otp_request.phone_number,
                "expires_in_minutes": 1440,  # 24 hours for demo
                "is_demo": True
            }

        # Send OTP via MSG91
        try:
            msg91_response = await msg91_service.send_otp(
                phone_number=otp_request.phone_number,
                db=db,
                otp_length=6
            )

            logger.info(
                f"OTP request processed for {otp_request.phone_number}. "
                f"IP: {client_ip}"
            )

            return {
                "success": True,
                "message": msg91_response.get("message", "OTP sent successfully"),
                "phone_number": otp_request.phone_number,
                "expires_in_minutes": msg91_response.get("expires_in_minutes", 5),
                # Include OTP in dev mode only (for testing)
                **({
                    "otp_for_testing": msg91_response.get("otp_for_testing")
                } if settings.is_development and "otp_for_testing" in msg91_response else {})
            }

        except MSG91InvalidPhoneError as e:
            logger.warning(f"Invalid phone number format: {otp_request.phone_number}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        except MSG91RateLimitError as e:
            logger.warning(
                f"MSG91 rate limit exceeded for {otp_request.phone_number}. "
                f"IP: {client_ip}"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=str(e)
            )

        except MSG91Error as e:
            logger.error(
                f"MSG91 error for {otp_request.phone_number}: {e}. "
                f"IP: {client_ip}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send OTP: {str(e)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error requesting OTP: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to request OTP: {str(e)}"
        )


@router.post("/otp/verify", response_model=TokenResponse)
@limiter.limit("5/minute")
async def verify_otp(
    otp_verify: OTPVerify,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Verify SMS OTP and return JWT token

    SECURITY: Rate limited to 5 attempts per minute per IP
    """
    try:
        # Get client info for security logging
        client_ip = get_remote_address(request)
        user_agent = request.headers.get("user-agent", "unknown")

        # Find valid OTP
        otp = db.query(OTP).filter(
            OTP.phone_number == otp_verify.phone_number,
            OTP.otp_code == otp_verify.otp_code,
            OTP.is_used == False,
            OTP.expires_at > datetime.utcnow()
        ).first()

        if not otp:
            # SECURITY FIX #6: Log failed OTP verification
            security_logger.log_otp_verification(
                phone_number=otp_verify.phone_number,
                user_id=None,
                ip_address=client_ip,
                user_agent=user_agent,
                success=False,
                reason="Invalid or expired OTP"
            )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired OTP"
            )

        # Mark OTP as used
        otp.is_used = True
        db.commit()

        # Get user
        user = db.query(User).filter(User.phone == otp_verify.phone_number).first()

        if not user:
            # SECURITY FIX #6: Log user not found
            security_logger.log_otp_verification(
                phone_number=otp_verify.phone_number,
                user_id=None,
                ip_address=client_ip,
                user_agent=user_agent,
                success=False,
                reason="User not found"
            )

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Update is_first_timer on first successful login
        if user.is_first_timer:
            user.is_first_timer = False

        # PRODUCTION MODE: Update OTP verification status
        user.phone_verified = True
        user.phone_verified_at = datetime.utcnow()
        user.last_otp_verified_at = datetime.utcnow()

        db.commit()
        db.refresh(user)

        # Create access token with OTP verification status
        access_token = create_access_token(
            user_id=str(user.id),
            phone_number=user.phone,
            phone_verified=user.phone_verified
        )

        # SECURITY FIX #6: Log successful authentication
        security_logger.log_otp_verification(
            phone_number=otp_verify.phone_number,
            user_id=str(user.id),
            ip_address=client_ip,
            user_agent=user_agent,
            success=True
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying OTP: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify OTP"
        )


@router.post("/otp/resend")
@limiter.limit("2/10minutes", key_func=get_remote_address)  # Rate limit by IP (body not available in key_func)
async def resend_otp(
    otp_resend: OTPResend,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Resend OTP via SMS or Voice.

    SECURITY: Rate limited to 2 resends per phone per 10 minutes
    """
    try:
        client_ip = get_remote_address(request)
        user_agent = request.headers.get("user-agent", "unknown")

        # Validate retry_type
        if otp_resend.retry_type not in ["text", "voice"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="retry_type must be 'text' or 'voice'"
            )

        # Resend OTP via MSG91
        try:
            msg91_response = await msg91_service.resend_otp(
                phone_number=otp_resend.phone_number,
                db=db,
                retry_type=otp_resend.retry_type
            )

            logger.info(
                f"OTP resend ({otp_resend.retry_type}) processed for {otp_resend.phone_number}. "
                f"IP: {client_ip}"
            )

            return {
                "success": True,
                "message": msg91_response.get("message", "OTP resent successfully"),
                "retry_type": otp_resend.retry_type,
                "phone_number": otp_resend.phone_number,
                "expires_in_minutes": msg91_response.get("expires_in_minutes", 5),
                # Include OTP in dev mode only (for testing)
                **({
                    "otp_for_testing": msg91_response.get("otp_for_testing")
                } if settings.is_development and "otp_for_testing" in msg91_response else {})
            }

        except MSG91InvalidPhoneError as e:
            logger.warning(f"Invalid phone number format on resend: {otp_resend.phone_number}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        except MSG91RateLimitError as e:
            logger.warning(
                f"MSG91 rate limit exceeded on resend for {otp_resend.phone_number}. "
                f"IP: {client_ip}"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=str(e)
            )

        except MSG91Error as e:
            logger.error(
                f"MSG91 error on resend for {otp_resend.phone_number}: {e}. "
                f"IP: {client_ip}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to resend OTP: {str(e)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resending OTP: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend OTP"
        )


@router.get("/verify")
async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Verify JWT token and return verification status.
    This endpoint checks if the token is valid and returns the OTP verification status.

    Returns:
        - valid: Token validity
        - user_id: User ID from token
        - phone_verified: OTP verification status
        - phone_number: User's phone number
    """
    try:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No authentication token provided"
            )

        token = credentials.credentials

        # Decode JWT
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID"
            )

        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        return {
            "valid": True,
            "user_id": str(user.id),
            "phone_verified": user.phone_verified,
            "phone_number": user.phone,
            "phone_verified_at": user.phone_verified_at.isoformat() if user.phone_verified_at else None,
            "last_otp_verified_at": user.last_otp_verified_at.isoformat() if user.last_otp_verified_at else None
        }

    except JWTError as e:
        logger.error(f"JWT validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify token"
        )


@router.put("/profile")
async def update_profile(
    profile: ProfileUpdate,
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Update user profile with name, address, and email.
    This should be called after OTP verification if profile details are missing.

    Like a social media account - collect once during signup, use for all reports.
    """
    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Update fields if provided
        if profile.name is not None:
            user.name = profile.name

        if profile.address is not None:
            user.address = profile.address

        if profile.email is not None:
            user.email = profile.email

        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)

        logger.info(f"Updated profile for user {user_id}")

        return {
            "success": True,
            "message": "Profile updated successfully",
            "user": user.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )
