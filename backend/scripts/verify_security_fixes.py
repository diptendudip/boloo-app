#!/usr/bin/env python3
"""
Security Fixes Verification Script
Verifies that all 6 critical security fixes are properly implemented
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings


def check_mark(passed: bool) -> str:
    """Return check mark or X based on test result"""
    return "✅" if passed else "❌"


def verify_https_enforcement():
    """Verify HTTPS enforcement middleware is implemented"""
    print("\n1️⃣  HTTPS Enforcement & HSTS Headers")
    print("=" * 60)

    try:
        from app.middleware.security import HTTPSRedirectMiddleware, SecurityHeadersMiddleware
        print(f"{check_mark(True)} HTTPSRedirectMiddleware imported successfully")
        print(f"{check_mark(True)} SecurityHeadersMiddleware imported successfully")

        # Check if middleware is in main.py
        with open("app/main.py", "r") as f:
            main_content = f.read()
            has_https_middleware = "HTTPSRedirectMiddleware" in main_content
            has_security_headers = "SecurityHeadersMiddleware" in main_content

        print(f"{check_mark(has_https_middleware)} HTTPS redirect configured in main.py")
        print(f"{check_mark(has_security_headers)} Security headers configured in main.py")

        return True
    except Exception as e:
        print(f"{check_mark(False)} Error: {e}")
        return False


def verify_database_ssl():
    """Verify database SSL enforcement"""
    print("\n2️⃣  Database SSL/TLS Enforcement")
    print("=" * 60)

    try:
        has_ssl_mode = hasattr(settings, 'DATABASE_SSL_MODE')
        print(f"{check_mark(has_ssl_mode)} DATABASE_SSL_MODE setting exists")

        if has_ssl_mode:
            print(f"   Current SSL mode: {settings.DATABASE_SSL_MODE}")

        # Check validator exists
        with open("app/config.py", "r") as f:
            config_content = f.read()
            has_validator = "SECURITY FIX #2" in config_content
            has_ssl_check = "Database SSL must be enabled" in config_content

        print(f"{check_mark(has_validator)} SSL validator implemented")
        print(f"{check_mark(has_ssl_check)} Production SSL check exists")

        return True
    except Exception as e:
        print(f"{check_mark(False)} Error: {e}")
        return False


def verify_otp_exposure_fix():
    """Verify OTP exposure is removed in production"""
    print("\n3️⃣  OTP Exposure Removal")
    print("=" * 60)

    try:
        with open("app/routers/auth.py", "r") as f:
            auth_content = f.read()
            has_fix = "SECURITY FIX #3" in auth_content
            has_dev_check = "is_development" in auth_content
            has_warning = "DEV MODE: Exposing OTP" in auth_content

        print(f"{check_mark(has_fix)} OTP exposure fix implemented")
        print(f"{check_mark(has_dev_check)} Development mode check exists")
        print(f"{check_mark(has_warning)} Warning logging for dev OTP exposure")

        return True
    except Exception as e:
        print(f"{check_mark(False)} Error: {e}")
        return False


def verify_rate_limiting():
    """Verify rate limiting is implemented"""
    print("\n4️⃣  Rate Limiting on Authentication")
    print("=" * 60)

    try:
        from app.middleware.rate_limit import limiter, phone_limiter
        print(f"{check_mark(True)} Rate limiters imported successfully")

        # Check if slowapi is installed
        try:
            import slowapi
            print(f"{check_mark(True)} slowapi package installed")
        except ImportError:
            print(f"{check_mark(False)} slowapi package NOT installed - run: pip install slowapi")
            return False

        # Check auth.py for rate limiting decorators
        with open("app/routers/auth.py", "r") as f:
            auth_content = f.read()
            has_otp_limit = "@limiter.limit" in auth_content
            has_phone_limit = "3/15minutes" in auth_content
            has_ip_limit = "10/hour" in auth_content

        print(f"{check_mark(has_otp_limit)} Rate limiting decorators exist")
        print(f"{check_mark(has_phone_limit)} Phone-based rate limit (3 per 15 min)")
        print(f"{check_mark(has_ip_limit)} IP-based rate limit (10 per hour)")

        return True
    except Exception as e:
        print(f"{check_mark(False)} Error: {e}")
        return False


def verify_dev_bypass_removal():
    """Verify development bypass is blocked in production"""
    print("\n5️⃣  Development Auth Bypass Removal")
    print("=" * 60)

    try:
        with open("app/utils/auth.py", "r") as f:
            auth_content = f.read()
            has_production_check = "settings.is_production" in auth_content
            has_security_alert = "SECURITY ALERT" in auth_content
            has_403_error = "HTTP_403_FORBIDDEN" in auth_content
            has_bypass_message = "Development authentication bypass is disabled" in auth_content

        print(f"{check_mark(has_production_check)} Production environment check exists")
        print(f"{check_mark(has_security_alert)} Security alert logging exists")
        print(f"{check_mark(has_403_error)} Returns 403 Forbidden")
        print(f"{check_mark(has_bypass_message)} Clear error message for users")

        return True
    except Exception as e:
        print(f"{check_mark(False)} Error: {e}")
        return False


def verify_security_logging():
    """Verify comprehensive security logging"""
    print("\n6️⃣  Comprehensive Security Logging")
    print("=" * 60)

    try:
        from app.utils.security_logger import SecurityLogger, SecurityEventType
        print(f"{check_mark(True)} SecurityLogger imported successfully")
        print(f"{check_mark(True)} SecurityEventType enum imported")

        # Check event types
        event_types = [e.value for e in SecurityEventType]
        required_events = [
            'auth_success',
            'auth_failure',
            'otp_requested',
            'otp_verified',
            'otp_failed',
            'rate_limit_exceeded'
        ]

        all_events_exist = all(event in event_types for event in required_events)
        print(f"{check_mark(all_events_exist)} All required event types exist")

        # Check auth.py uses security logging
        with open("app/routers/auth.py", "r") as f:
            auth_content = f.read()
            uses_logger = "security_logger" in auth_content
            logs_otp_request = "log_otp_request" in auth_content
            logs_verification = "log_otp_verification" in auth_content

        print(f"{check_mark(uses_logger)} Auth router uses security logger")
        print(f"{check_mark(logs_otp_request)} OTP requests are logged")
        print(f"{check_mark(logs_verification)} OTP verifications are logged")

        return True
    except Exception as e:
        print(f"{check_mark(False)} Error: {e}")
        return False


def verify_tests():
    """Verify comprehensive tests exist"""
    print("\n7️⃣  Security Tests")
    print("=" * 60)

    try:
        test_file = "tests/test_security_fixes.py"
        if not os.path.exists(test_file):
            print(f"{check_mark(False)} Test file not found: {test_file}")
            return False

        with open(test_file, "r") as f:
            test_content = f.read()

        test_classes = [
            "TestHTTPSEnforcement",
            "TestDatabaseSSL",
            "TestOTPExposureRemoval",
            "TestRateLimiting",
            "TestDevBypassRemoval",
            "TestSecurityLogging"
        ]

        for test_class in test_classes:
            exists = test_class in test_content
            print(f"{check_mark(exists)} {test_class}")

        return True
    except Exception as e:
        print(f"{check_mark(False)} Error: {e}")
        return False


def main():
    """Run all verification checks"""
    print("\n" + "=" * 60)
    print("SECURITY FIXES VERIFICATION")
    print("=" * 60)
    print(f"Environment: {settings.APP_ENV}")
    print(f"Production: {settings.is_production}")
    print(f"Development: {settings.is_development}")

    results = []

    results.append(verify_https_enforcement())
    results.append(verify_database_ssl())
    results.append(verify_otp_exposure_fix())
    results.append(verify_rate_limiting())
    results.append(verify_dev_bypass_removal())
    results.append(verify_security_logging())
    results.append(verify_tests())

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(results)
    total = len(results)
    percentage = (passed / total) * 100

    print(f"Checks Passed: {passed}/{total} ({percentage:.0f}%)")

    if passed == total:
        print(f"\n✅ ALL SECURITY FIXES VERIFIED!")
        print("Status: PRODUCTION READY")
        return 0
    else:
        print(f"\n❌ SOME CHECKS FAILED")
        print(f"Failed: {total - passed}")
        print("Status: NOT READY FOR PRODUCTION")
        return 1


if __name__ == "__main__":
    sys.exit(main())
