"""
Security Event Logging - Audit Trail & Threat Detection
Implements comprehensive logging for security-critical events
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class SecurityEventType(Enum):
    """Security event types for categorization"""
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    OTP_REQUESTED = "otp_requested"
    OTP_VERIFIED = "otp_verified"
    OTP_FAILED = "otp_failed"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    HTTPS_REDIRECT = "https_redirect"
    INVALID_TOKEN = "invalid_token"


class SecurityLogger:
    """
    SECURITY FIX #6: Comprehensive security event logging

    Logs all authentication attempts, rate limiting violations,
    and suspicious activity patterns for audit and threat detection.
    """

    @staticmethod
    def log_event(
        event_type: SecurityEventType,
        user_id: Optional[str] = None,
        phone_number: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log a security event with context

        Args:
            event_type: Type of security event
            user_id: User ID (if authenticated)
            phone_number: Phone number (for auth events)
            ip_address: Client IP address
            user_agent: User agent string
            success: Whether the operation succeeded
            reason: Failure reason (if applicable)
            metadata: Additional context
        """
        # Sanitize phone number for logging (mask middle digits)
        masked_phone = None
        if phone_number:
            if len(phone_number) > 6:
                masked_phone = f"{phone_number[:3]}****{phone_number[-3:]}"
            else:
                masked_phone = "***"

        # Build log message
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type.value,
            "user_id": user_id,
            "phone_number": masked_phone,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "success": success,
            "reason": reason,
            "metadata": metadata or {}
        }

        # Log at appropriate level
        if success:
            logger.info(f"SECURITY_EVENT: {log_data}")
        elif event_type in [
            SecurityEventType.RATE_LIMIT_EXCEEDED,
            SecurityEventType.SUSPICIOUS_ACTIVITY,
            SecurityEventType.UNAUTHORIZED_ACCESS
        ]:
            logger.warning(f"SECURITY_WARNING: {log_data}")
        else:
            logger.error(f"SECURITY_FAILURE: {log_data}")

    @staticmethod
    def log_auth_attempt(
        phone_number: str,
        ip_address: str,
        user_agent: str,
        success: bool,
        reason: Optional[str] = None
    ):
        """Log authentication attempt"""
        SecurityLogger.log_event(
            event_type=SecurityEventType.AUTH_SUCCESS if success else SecurityEventType.AUTH_FAILURE,
            phone_number=phone_number,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            reason=reason
        )

    @staticmethod
    def log_otp_request(
        phone_number: str,
        ip_address: str,
        user_agent: str,
        success: bool = True
    ):
        """Log OTP request"""
        SecurityLogger.log_event(
            event_type=SecurityEventType.OTP_REQUESTED,
            phone_number=phone_number,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success
        )

    @staticmethod
    def log_otp_verification(
        phone_number: str,
        user_id: Optional[str],
        ip_address: str,
        user_agent: str,
        success: bool,
        reason: Optional[str] = None
    ):
        """Log OTP verification attempt"""
        SecurityLogger.log_event(
            event_type=SecurityEventType.OTP_VERIFIED if success else SecurityEventType.OTP_FAILED,
            user_id=user_id,
            phone_number=phone_number,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            reason=reason
        )

    @staticmethod
    def log_rate_limit_exceeded(
        ip_address: str,
        endpoint: str,
        limit: str
    ):
        """Log rate limit violation"""
        SecurityLogger.log_event(
            event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
            ip_address=ip_address,
            success=False,
            reason=f"Rate limit exceeded for {endpoint}",
            metadata={"endpoint": endpoint, "limit": limit}
        )

    @staticmethod
    def log_suspicious_activity(
        description: str,
        ip_address: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log suspicious activity pattern"""
        SecurityLogger.log_event(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            user_id=user_id,
            ip_address=ip_address,
            success=False,
            reason=description,
            metadata=metadata
        )

    @staticmethod
    def log_unauthorized_access(
        user_id: str,
        resource: str,
        ip_address: str,
        reason: str
    ):
        """Log unauthorized access attempt"""
        SecurityLogger.log_event(
            event_type=SecurityEventType.UNAUTHORIZED_ACCESS,
            user_id=user_id,
            ip_address=ip_address,
            success=False,
            reason=reason,
            metadata={"resource": resource}
        )


# Global instance
security_logger = SecurityLogger()
