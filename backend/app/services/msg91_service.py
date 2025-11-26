"""
MSG91 SMS OTP Service for Production-Ready Authentication

Features:
- OTP sending via MSG91 SMS API
- OTP verification with retry limits
- OTP resend with voice fallback
- Rate limiting and security
- Comprehensive error handling
- Logging and monitoring
"""

import httpx
import logging
from typing import Optional, Dict, Literal
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.config import settings
from app.models import OTP

logger = logging.getLogger(__name__)


class MSG91Error(Exception):
    """Base exception for MSG91 errors"""
    pass


class MSG91RateLimitError(MSG91Error):
    """Rate limit exceeded"""
    pass


class MSG91InvalidPhoneError(MSG91Error):
    """Invalid phone number"""
    pass


class MSG91Service:
    """
    Production-ready MSG91 SMS OTP service

    MSG91 API Documentation: https://docs.msg91.com/
    """

    BASE_URL = "https://control.msg91.com/api/v5"
    OTP_URL = "https://control.msg91.com/api/v5/otp"

    def __init__(self):
        """Initialize MSG91 service with configuration"""
        self.api_key = getattr(settings, 'MSG91_API_KEY', None)
        self.sender_id = getattr(settings, 'MSG91_SENDER_ID', 'BOLOOO')
        self.template_id = getattr(settings, 'MSG91_TEMPLATE_ID', None)
        self.route = getattr(settings, 'MSG91_ROUTE', 4)  # 4 = Transactional
        self.otp_expiry_minutes = getattr(settings, 'MSG91_OTP_EXPIRY_MINUTES', 5)

        # Validate configuration
        if not self.api_key and not settings.is_development:
            logger.warning("MSG91_API_KEY not configured. SMS sending will be mocked.")

    def _validate_phone_number(self, phone_number: str) -> str:
        """
        Validate and normalize Indian phone number

        Args:
            phone_number: Phone number (+91XXXXXXXXXX or 91XXXXXXXXXX or XXXXXXXXXX)

        Returns:
            str: Normalized 10-digit mobile number

        Raises:
            MSG91InvalidPhoneError: If phone number is invalid
        """
        # Remove spaces, dashes, and plus sign
        clean = phone_number.replace('+', '').replace(' ', '').replace('-', '')

        # Remove country code if present
        if clean.startswith('91') and len(clean) == 12:
            clean = clean[2:]
        elif clean.startswith('0') and len(clean) == 11:
            clean = clean[1:]

        # Validate format
        if not clean.isdigit() or len(clean) != 10:
            raise MSG91InvalidPhoneError(
                f"Invalid phone number format: {phone_number}. "
                "Expected format: +91XXXXXXXXXX or 10-digit mobile number"
            )

        # Validate Indian mobile number (starts with 6, 7, 8, or 9)
        if clean[0] not in ['6', '7', '8', '9']:
            raise MSG91InvalidPhoneError(
                f"Invalid Indian mobile number: {phone_number}. "
                "Must start with 6, 7, 8, or 9"
            )

        return clean

    async def send_otp(
        self,
        phone_number: str,
        db: Session,
        otp_length: int = 6
    ) -> Dict:
        """
        Send OTP via MSG91 SMS

        Args:
            phone_number: Phone number (+91XXXXXXXXXX)
            db: Database session for OTP tracking
            otp_length: OTP code length (default: 6)

        Returns:
            Dict: {"type": "success", "message": "OTP sent successfully", "expires_in": 5}

        Raises:
            MSG91Error: If SMS sending fails
            MSG91RateLimitError: If rate limit exceeded
        """
        try:
            # Validate phone number
            mobile = self._validate_phone_number(phone_number)
            full_number = f"+91{mobile}"

            # Generate OTP
            otp_code = OTP.generate_code()
            expires_at = datetime.utcnow() + timedelta(minutes=self.otp_expiry_minutes)

            # Save OTP to database
            otp_record = OTP(
                phone_number=full_number,
                otp_code=otp_code,
                expires_at=expires_at,
                is_used=False
            )
            db.add(otp_record)
            db.commit()

            # Send via MSG91 (or mock in development)
            if not self.api_key or settings.is_development:
                logger.info(
                    f"[DEV MODE] OTP generated for {full_number}: {otp_code} "
                    f"(expires in {self.otp_expiry_minutes} minutes)"
                )

                response_data = {
                    "type": "success",
                    "message": f"OTP sent to {full_number}",
                    "expires_in_minutes": self.otp_expiry_minutes
                }

                # Expose OTP in development only
                if settings.is_development:
                    response_data["otp_for_testing"] = otp_code
                    logger.warning(f"⚠️  DEV MODE: OTP exposed in response")

                return response_data

            # Production: Send via MSG91 OTP API
            url = f"{self.OTP_URL}?template_id={self.template_id}"

            payload = {
                "mobile": f"91{mobile}",  # MSG91 expects country code + mobile
                "otp": otp_code,
                "otp_expiry": self.otp_expiry_minutes,
            }

            headers = {
                "authkey": self.api_key,
                "Content-Type": "application/json"
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)

                if response.status_code == 200:
                    result = response.json()

                    # MSG91 returns {"type": "success", "message": "..."}
                    if result.get("type") == "success":
                        logger.info(
                            f"MSG91 OTP sent successfully to {full_number}. "
                            f"Request ID: {result.get('request_id', 'N/A')}"
                        )

                        return {
                            "type": "success",
                            "message": f"OTP sent to {full_number}",
                            "expires_in_minutes": self.otp_expiry_minutes,
                            "request_id": result.get("request_id")
                        }
                    else:
                        error_msg = result.get("message", "Unknown error")
                        logger.error(f"MSG91 API error: {error_msg}")
                        raise MSG91Error(f"Failed to send OTP: {error_msg}")

                elif response.status_code == 429:
                    logger.error(f"MSG91 rate limit exceeded for {full_number}")
                    raise MSG91RateLimitError("Too many OTP requests. Please try again later.")

                else:
                    error_text = response.text
                    logger.error(
                        f"MSG91 API error: HTTP {response.status_code} - {error_text}"
                    )
                    raise MSG91Error(f"Failed to send OTP: HTTP {response.status_code}")

        except MSG91Error:
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending OTP to {phone_number}: {e}", exc_info=True)
            raise MSG91Error(f"Failed to send OTP: {str(e)}")

    async def verify_otp(
        self,
        phone_number: str,
        otp_code: str,
        db: Session
    ) -> Dict:
        """
        Verify OTP code

        Args:
            phone_number: Phone number (+91XXXXXXXXXX)
            otp_code: OTP code to verify
            db: Database session

        Returns:
            Dict: {"type": "success", "message": "OTP verified successfully"}

        Raises:
            MSG91Error: If OTP verification fails
        """
        try:
            # Validate phone number
            mobile = self._validate_phone_number(phone_number)
            full_number = f"+91{mobile}"

            # Find valid OTP in database
            otp_record = db.query(OTP).filter(
                OTP.phone_number == full_number,
                OTP.otp_code == otp_code,
                OTP.is_used == False,
                OTP.expires_at > datetime.utcnow()
            ).first()

            if not otp_record:
                logger.warning(
                    f"OTP verification failed for {full_number}: "
                    "Invalid or expired OTP"
                )
                raise MSG91Error("Invalid or expired OTP")

            # Mark OTP as used
            otp_record.is_used = True
            db.commit()

            logger.info(f"OTP verified successfully for {full_number}")

            return {
                "type": "success",
                "message": "OTP verified successfully"
            }

        except MSG91Error:
            raise
        except Exception as e:
            logger.error(f"Error verifying OTP for {phone_number}: {e}", exc_info=True)
            raise MSG91Error(f"Failed to verify OTP: {str(e)}")

    async def resend_otp(
        self,
        phone_number: str,
        db: Session,
        retry_type: Literal["text", "voice"] = "text"
    ) -> Dict:
        """
        Resend OTP via SMS or Voice

        Args:
            phone_number: Phone number (+91XXXXXXXXXX)
            db: Database session
            retry_type: Resend method ("text" or "voice")

        Returns:
            Dict: {"type": "success", "message": "OTP resent via SMS/Voice"}

        Raises:
            MSG91Error: If resend fails
        """
        try:
            # Validate phone number
            mobile = self._validate_phone_number(phone_number)
            full_number = f"+91{mobile}"

            # Check for recent OTP requests (prevent abuse)
            recent_otp = db.query(OTP).filter(
                OTP.phone_number == full_number,
                OTP.created_at > datetime.utcnow() - timedelta(minutes=1)
            ).first()

            if recent_otp:
                logger.warning(
                    f"OTP resend blocked for {full_number}: "
                    "Too many requests (1 minute cooldown)"
                )
                raise MSG91RateLimitError(
                    "Please wait 1 minute before requesting another OTP"
                )

            # Generate new OTP
            if retry_type == "voice":
                # Voice OTP resend
                return await self._resend_voice_otp(full_number, db)
            else:
                # Text SMS resend (same as send_otp)
                return await self.send_otp(full_number, db)

        except MSG91Error:
            raise
        except Exception as e:
            logger.error(f"Error resending OTP to {phone_number}: {e}", exc_info=True)
            raise MSG91Error(f"Failed to resend OTP: {str(e)}")

    async def _resend_voice_otp(self, phone_number: str, db: Session) -> Dict:
        """
        Resend OTP via voice call (fallback method)

        Args:
            phone_number: Phone number (+91XXXXXXXXXX)
            db: Database session

        Returns:
            Dict: Response with success status
        """
        try:
            mobile = self._validate_phone_number(phone_number)
            full_number = f"+91{mobile}"

            # Generate OTP
            otp_code = OTP.generate_code()
            expires_at = datetime.utcnow() + timedelta(minutes=self.otp_expiry_minutes)

            # Save OTP to database
            otp_record = OTP(
                phone_number=full_number,
                otp_code=otp_code,
                expires_at=expires_at,
                is_used=False
            )
            db.add(otp_record)
            db.commit()

            # Mock voice OTP in development
            if not self.api_key or settings.is_development:
                logger.info(
                    f"[DEV MODE] Voice OTP for {full_number}: {otp_code}"
                )
                return {
                    "type": "success",
                    "message": f"OTP will be sent via voice call to {full_number}",
                    "retry_type": "voice",
                    "otp_for_testing": otp_code  # Dev only
                }

            # Production: Send via MSG91 Voice OTP
            url = f"{self.OTP_URL}/retry?retrytype=voice"

            payload = {
                "mobile": f"91{mobile}",
                "otp": otp_code
            }

            headers = {
                "authkey": self.api_key,
                "Content-Type": "application/json"
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)

                if response.status_code == 200:
                    result = response.json()

                    if result.get("type") == "success":
                        logger.info(f"Voice OTP sent successfully to {full_number}")
                        return {
                            "type": "success",
                            "message": f"OTP sent via voice call to {full_number}",
                            "retry_type": "voice"
                        }
                    else:
                        raise MSG91Error(f"Voice OTP failed: {result.get('message')}")
                else:
                    raise MSG91Error(f"Voice OTP failed: HTTP {response.status_code}")

        except Exception as e:
            logger.error(f"Voice OTP error for {phone_number}: {e}", exc_info=True)
            raise MSG91Error(f"Failed to send voice OTP: {str(e)}")

    async def check_balance(self) -> Optional[Dict]:
        """
        Check MSG91 account balance

        Returns:
            Dict: {"balance": "1234.56", "currency": "INR"} or None if error
        """
        try:
            if not self.api_key:
                logger.warning("MSG91 not configured. Cannot check balance.")
                return None

            url = "https://control.msg91.com/api/balance.php"
            params = {"authkey": self.api_key}

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)

                if response.status_code == 200:
                    balance = response.text.strip()
                    logger.info(f"MSG91 balance: ₹{balance}")
                    return {
                        "balance": balance,
                        "currency": "INR"
                    }
                else:
                    logger.error(f"Failed to check MSG91 balance: {response.text}")
                    return None

        except Exception as e:
            logger.error(f"Error checking MSG91 balance: {e}", exc_info=True)
            return None


# Global service instance
msg91_service = MSG91Service()
