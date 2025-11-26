"""
OTP Verification Middleware

This middleware checks if users have verified their phone via OTP
for protected endpoints in production mode.
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
import logging
from typing import List

from app.config import settings

logger = logging.getLogger(__name__)


class OTPVerificationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce OTP verification for protected endpoints.

    In production mode, this ensures users have verified their phone
    before accessing protected resources.
    """

    # Endpoints that bypass OTP verification check
    BYPASS_PATHS: List[str] = [
        "/auth/otp/request",
        "/auth/otp/verify",
        "/auth/otp/resend",
        "/auth/verify",
        "/auth/profile",
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
    ]

    # Path prefixes that bypass OTP check
    BYPASS_PREFIXES: List[str] = [
        "/auth/",
        "/static/",
        "/public/",
    ]

    def __init__(self, app, enforce_in_production: bool = True):
        """
        Initialize OTP verification middleware.

        Args:
            app: FastAPI application instance
            enforce_in_production: If True, only enforce in production mode
        """
        super().__init__(app)
        self.enforce_in_production = enforce_in_production

    async def dispatch(self, request: Request, call_next):
        """
        Process request and check OTP verification status.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler

        Returns:
            Response from next handler or 403 if OTP not verified
        """
        # Skip middleware if not in production (when enforce_in_production is True)
        if self.enforce_in_production and not settings.is_production:
            return await call_next(request)

        # Check if path should bypass OTP verification
        if self._should_bypass(request.path):
            return await call_next(request)

        # Extract and verify JWT token
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            # No token, let the endpoint handle authentication
            return await call_next(request)

        try:
            token = auth_header.replace("Bearer ", "")

            # Decode JWT
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )

            # Check OTP verification status
            phone_verified = payload.get("phone_verified", False)

            if not phone_verified:
                logger.warning(
                    f"OTP verification required for user {payload.get('sub')} "
                    f"accessing {request.path}"
                )

                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "detail": "Phone verification required. Please verify your phone number via OTP.",
                        "error_code": "OTP_VERIFICATION_REQUIRED",
                        "phone_verified": False
                    }
                )

        except JWTError as e:
            # Invalid token, let the endpoint handle it
            logger.debug(f"JWT decode error in OTP middleware: {e}")
            pass

        except Exception as e:
            logger.error(f"OTP middleware error: {e}", exc_info=True)
            # Don't block request on middleware errors
            pass

        # Continue to next middleware/handler
        return await call_next(request)

    def _should_bypass(self, path: str) -> bool:
        """
        Check if path should bypass OTP verification.

        Args:
            path: Request path

        Returns:
            True if path should bypass check, False otherwise
        """
        # Check exact path matches
        if path in self.BYPASS_PATHS:
            return True

        # Check path prefixes
        for prefix in self.BYPASS_PREFIXES:
            if path.startswith(prefix):
                return True

        return False
