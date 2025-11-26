"""
Security Middleware - HTTPS Enforcement & Security Headers
Implements critical security fixes for production deployment
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, RedirectResponse
from typing import Callable
import logging

logger = logging.getLogger(__name__)


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """
    SECURITY FIX #1: Redirect all HTTP traffic to HTTPS in production

    Enforces HTTPS-only connections to prevent man-in-the-middle attacks
    and ensure all data transmission is encrypted.
    """

    def __init__(self, app, enabled: bool = True):
        super().__init__(app)
        self.enabled = enabled

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self.enabled:
            return await call_next(request)

        # Check if request is already HTTPS
        if request.url.scheme == "https":
            return await call_next(request)

        # Check for X-Forwarded-Proto header (reverse proxy scenarios)
        forwarded_proto = request.headers.get("X-Forwarded-Proto", "")
        if forwarded_proto == "https":
            return await call_next(request)

        # Redirect HTTP to HTTPS
        https_url = request.url.replace(scheme="https")
        logger.warning(
            f"SECURITY: Redirecting HTTP request to HTTPS: {request.url} -> {https_url}"
        )
        return RedirectResponse(url=str(https_url), status_code=301)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    SECURITY FIX #1: Add comprehensive security headers to all responses

    Implements:
    - HSTS (HTTP Strict Transport Security)
    - CSP (Content Security Policy)
    - X-Frame-Options (Clickjacking protection)
    - X-Content-Type-Options (MIME sniffing protection)
    - X-XSS-Protection (XSS protection for older browsers)
    - Referrer-Policy (Privacy protection)
    """

    def __init__(self, app, enabled: bool = True, hsts_max_age: int = 31536000):
        super().__init__(app)
        self.enabled = enabled
        self.hsts_max_age = hsts_max_age  # 1 year by default

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        if not self.enabled:
            return response

        # HSTS: Force HTTPS for 1 year, including all subdomains
        response.headers["Strict-Transport-Security"] = (
            f"max-age={self.hsts_max_age}; includeSubDomains; preload"
        )

        # CSP: Restrict resource loading to prevent XSS attacks
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none';"
        )

        # Clickjacking protection
        response.headers["X-Frame-Options"] = "DENY"

        # MIME sniffing protection
        response.headers["X-Content-Type-Options"] = "nosniff"

        # XSS protection (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer policy (privacy)
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions policy (disable unnecessary browser features)
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )

        return response
