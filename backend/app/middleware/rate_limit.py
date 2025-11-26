"""
Rate Limiting Middleware - DoS Protection
Implements rate limiting for authentication endpoints
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request
import logging

logger = logging.getLogger(__name__)


def get_phone_number_key(request: Request) -> str:
    """
    Extract phone number from request for rate limiting

    Used for phone-based rate limiting (3 OTP requests per 15 min per phone)
    """
    try:
        # Try to get phone from request body
        if hasattr(request, "_json"):
            body = request._json
            if isinstance(body, dict) and "phone_number" in body:
                return f"phone:{body['phone_number']}"
    except Exception:
        pass

    # Fallback to IP-based limiting
    return get_remote_address(request)


# Initialize limiter with Redis backend for distributed rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per hour"],  # Global default
    storage_uri="redis://localhost:6379/1",  # Use Redis DB 1 for rate limits
    strategy="fixed-window"
)


# Phone-specific limiter for OTP requests
phone_limiter = Limiter(
    key_func=get_phone_number_key,
    storage_uri="redis://localhost:6379/1",
    strategy="fixed-window"
)
