"""
Test Suite for Authentication Persistence and OTP Verification

This test suite validates:
- OTP verification updates user.phone_verified
- JWT tokens include phone_verified field
- Token validation works correctly
- Expired tokens are rejected
- Invalid tokens return 401
- OTP verification timestamp is recorded
"""

import pytest
import jwt
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.auth import create_access_token, verify_token
from app.database import get_db
from fastapi.testclient import TestClient

client = TestClient(app)

# Test Configuration
TEST_SECRET_KEY = "test_secret_key_for_jwt_tokens"
TEST_ALGORITHM = "HS256"
TEST_PHONE_NUMBER = "+1234567890"
TEST_OTP = "123456"


class TestOTPVerification:
    """Test OTP verification functionality"""

    @pytest.fixture
    def mock_db(self):
        """Create mock database connection"""
        db = MagicMock()
        cursor = MagicMock()
        db.cursor.return_value = cursor
        return db, cursor

    def test_otp_verification_updates_phone_verified(self, mock_db):
        """Test that OTP verification sets phone_verified to True"""
        db, cursor = mock_db

        # Mock user exists and OTP is correct
        cursor.fetchone.return_value = {
            'id': 1,
            'phone_number': TEST_PHONE_NUMBER,
            'otp': TEST_OTP,
            'phone_verified': False
        }

        with patch('app.database.get_db', return_value=db):
            response = client.post(
                "/auth/verify-otp",
                json={
                    "phone_number": TEST_PHONE_NUMBER,
                    "otp": TEST_OTP
                }
            )

        assert response.status_code == 200
        assert 'access_token' in response.json()

        # Verify that UPDATE was called with phone_verified=1
        update_calls = [call for call in cursor.execute.call_args_list
                       if 'UPDATE' in str(call) and 'phone_verified' in str(call)]
        assert len(update_calls) > 0, "phone_verified should be updated"

    def test_otp_verification_records_timestamp(self, mock_db):
        """Test that OTP verification timestamp is recorded"""
        db, cursor = mock_db

        cursor.fetchone.return_value = {
            'id': 1,
            'phone_number': TEST_PHONE_NUMBER,
            'otp': TEST_OTP,
            'phone_verified': False
        }

        with patch('app.database.get_db', return_value=db):
            response = client.post(
                "/auth/verify-otp",
                json={
                    "phone_number": TEST_PHONE_NUMBER,
                    "otp": TEST_OTP
                }
            )

        assert response.status_code == 200

        # Check that verified_at timestamp was set
        update_calls = cursor.execute.call_args_list
        timestamp_set = any('verified_at' in str(call) or 'CURRENT_TIMESTAMP' in str(call)
                          for call in update_calls)
        assert timestamp_set, "Verification timestamp should be recorded"

    def test_invalid_otp_returns_error(self, mock_db):
        """Test that invalid OTP returns appropriate error"""
        db, cursor = mock_db

        cursor.fetchone.return_value = {
            'id': 1,
            'phone_number': TEST_PHONE_NUMBER,
            'otp': '000000',  # Different OTP
            'phone_verified': False
        }

        with patch('app.database.get_db', return_value=db):
            response = client.post(
                "/auth/verify-otp",
                json={
                    "phone_number": TEST_PHONE_NUMBER,
                    "otp": TEST_OTP
                }
            )

        assert response.status_code == 400 or response.status_code == 401
        assert 'access_token' not in response.json()

    def test_nonexistent_phone_returns_error(self, mock_db):
        """Test that verification with non-existent phone returns error"""
        db, cursor = mock_db

        cursor.fetchone.return_value = None

        with patch('app.database.get_db', return_value=db):
            response = client.post(
                "/auth/verify-otp",
                json={
                    "phone_number": "+9999999999",
                    "otp": TEST_OTP
                }
            )

        assert response.status_code == 404 or response.status_code == 400


class TestJWTTokens:
    """Test JWT token generation and validation"""

    def test_jwt_includes_phone_verified_field(self):
        """Test that JWT tokens include phone_verified field"""
        user_data = {
            'user_id': 1,
            'phone_number': TEST_PHONE_NUMBER,
            'phone_verified': True
        }

        with patch('app.auth.SECRET_KEY', TEST_SECRET_KEY):
            with patch('app.auth.ALGORITHM', TEST_ALGORITHM):
                token = create_access_token(user_data)

        # Decode token without verification to inspect payload
        decoded = jwt.decode(token, options={"verify_signature": False})

        assert 'phone_verified' in decoded
        assert decoded['phone_verified'] is True
        assert decoded['user_id'] == 1
        assert decoded['phone_number'] == TEST_PHONE_NUMBER

    def test_jwt_verified_false_for_unverified_user(self):
        """Test that phone_verified is False for unverified users"""
        user_data = {
            'user_id': 2,
            'phone_number': TEST_PHONE_NUMBER,
            'phone_verified': False
        }

        with patch('app.auth.SECRET_KEY', TEST_SECRET_KEY):
            with patch('app.auth.ALGORITHM', TEST_ALGORITHM):
                token = create_access_token(user_data)

        decoded = jwt.decode(token, options={"verify_signature": False})

        assert 'phone_verified' in decoded
        assert decoded['phone_verified'] is False

    def test_token_expiration_included(self):
        """Test that tokens include expiration time"""
        user_data = {
            'user_id': 1,
            'phone_number': TEST_PHONE_NUMBER,
            'phone_verified': True
        }

        with patch('app.auth.SECRET_KEY', TEST_SECRET_KEY):
            with patch('app.auth.ALGORITHM', TEST_ALGORITHM):
                token = create_access_token(user_data)

        decoded = jwt.decode(token, options={"verify_signature": False})

        assert 'exp' in decoded
        assert decoded['exp'] > time.time()


class TestTokenValidation:
    """Test token validation endpoint"""

    @pytest.fixture
    def valid_token(self):
        """Generate a valid token for testing"""
        user_data = {
            'user_id': 1,
            'phone_number': TEST_PHONE_NUMBER,
            'phone_verified': True
        }

        with patch('app.auth.SECRET_KEY', TEST_SECRET_KEY):
            with patch('app.auth.ALGORITHM', TEST_ALGORITHM):
                return create_access_token(user_data)

    def test_verify_endpoint_accepts_valid_token(self, valid_token):
        """Test that /auth/verify accepts valid tokens"""
        with patch('app.auth.SECRET_KEY', TEST_SECRET_KEY):
            with patch('app.auth.ALGORITHM', TEST_ALGORITHM):
                response = client.get(
                    "/auth/verify",
                    headers={"Authorization": f"Bearer {valid_token}"}
                )

        assert response.status_code == 200
        data = response.json()
        assert data['valid'] is True
        assert data['phone_verified'] is True

    def test_verify_endpoint_rejects_invalid_token(self):
        """Test that /auth/verify rejects invalid tokens"""
        invalid_token = "invalid.token.here"

        with patch('app.auth.SECRET_KEY', TEST_SECRET_KEY):
            with patch('app.auth.ALGORITHM', TEST_ALGORITHM):
                response = client.get(
                    "/auth/verify",
                    headers={"Authorization": f"Bearer {invalid_token}"}
                )

        assert response.status_code == 401
        assert response.json()['detail'] == 'Invalid token'

    def test_verify_endpoint_rejects_expired_token(self):
        """Test that expired tokens are rejected"""
        # Create token with past expiration
        payload = {
            'user_id': 1,
            'phone_number': TEST_PHONE_NUMBER,
            'phone_verified': True,
            'exp': datetime.utcnow() - timedelta(hours=1)  # Expired 1 hour ago
        }

        expired_token = jwt.encode(payload, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)

        with patch('app.auth.SECRET_KEY', TEST_SECRET_KEY):
            with patch('app.auth.ALGORITHM', TEST_ALGORITHM):
                response = client.get(
                    "/auth/verify",
                    headers={"Authorization": f"Bearer {expired_token}"}
                )

        assert response.status_code == 401
        assert 'expired' in response.json()['detail'].lower() or \
               'invalid' in response.json()['detail'].lower()

    def test_verify_endpoint_requires_authorization_header(self):
        """Test that /auth/verify requires Authorization header"""
        response = client.get("/auth/verify")

        assert response.status_code == 401 or response.status_code == 403

    def test_verify_endpoint_rejects_malformed_bearer(self):
        """Test that malformed Bearer format is rejected"""
        response = client.get(
            "/auth/verify",
            headers={"Authorization": "NotBearer token123"}
        )

        assert response.status_code == 401 or response.status_code == 403


class TestAuthPersistence:
    """Test authentication persistence across sessions"""

    @pytest.fixture
    def authenticated_user(self, mock_db):
        """Create authenticated user session"""
        db, cursor = mock_db

        cursor.fetchone.return_value = {
            'id': 1,
            'phone_number': TEST_PHONE_NUMBER,
            'otp': TEST_OTP,
            'phone_verified': True
        }

        with patch('app.database.get_db', return_value=db):
            response = client.post(
                "/auth/verify-otp",
                json={
                    "phone_number": TEST_PHONE_NUMBER,
                    "otp": TEST_OTP
                }
            )

        return response.json()['access_token']

    def test_token_persists_user_state(self):
        """Test that token contains all necessary user state"""
        user_data = {
            'user_id': 1,
            'phone_number': TEST_PHONE_NUMBER,
            'phone_verified': True,
            'created_at': datetime.utcnow().isoformat()
        }

        with patch('app.auth.SECRET_KEY', TEST_SECRET_KEY):
            with patch('app.auth.ALGORITHM', TEST_ALGORITHM):
                token = create_access_token(user_data)

        decoded = jwt.decode(token, options={"verify_signature": False})

        # Verify all user state is preserved
        assert decoded['user_id'] == user_data['user_id']
        assert decoded['phone_number'] == user_data['phone_number']
        assert decoded['phone_verified'] == user_data['phone_verified']

    def test_multiple_tokens_for_same_user(self):
        """Test that multiple tokens can be issued for the same user"""
        user_data = {
            'user_id': 1,
            'phone_number': TEST_PHONE_NUMBER,
            'phone_verified': True
        }

        with patch('app.auth.SECRET_KEY', TEST_SECRET_KEY):
            with patch('app.auth.ALGORITHM', TEST_ALGORITHM):
                token1 = create_access_token(user_data)
                time.sleep(0.1)  # Ensure different timestamps
                token2 = create_access_token(user_data)

        # Both tokens should be valid
        decoded1 = jwt.decode(token1, options={"verify_signature": False})
        decoded2 = jwt.decode(token2, options={"verify_signature": False})

        assert decoded1['user_id'] == decoded2['user_id']
        assert token1 != token2  # Different tokens


class TestSecurityFeatures:
    """Test security features of authentication system"""

    def test_token_signature_validation(self):
        """Test that token signatures are validated"""
        # Create token with wrong secret
        payload = {
            'user_id': 1,
            'phone_number': TEST_PHONE_NUMBER,
            'phone_verified': True,
            'exp': datetime.utcnow() + timedelta(hours=1)
        }

        tampered_token = jwt.encode(payload, "wrong_secret", algorithm=TEST_ALGORITHM)

        with patch('app.auth.SECRET_KEY', TEST_SECRET_KEY):
            with patch('app.auth.ALGORITHM', TEST_ALGORITHM):
                response = client.get(
                    "/auth/verify",
                    headers={"Authorization": f"Bearer {tampered_token}"}
                )

        assert response.status_code == 401

    def test_token_payload_tampering_detected(self):
        """Test that tampered token payloads are detected"""
        user_data = {
            'user_id': 1,
            'phone_number': TEST_PHONE_NUMBER,
            'phone_verified': False
        }

        with patch('app.auth.SECRET_KEY', TEST_SECRET_KEY):
            with patch('app.auth.ALGORITHM', TEST_ALGORITHM):
                token = create_access_token(user_data)

        # Try to decode and modify payload (will break signature)
        parts = token.split('.')
        assert len(parts) == 3  # header.payload.signature

        # Token should be rejected if modified
        tampered = parts[0] + '.tampered.' + parts[2]

        with patch('app.auth.SECRET_KEY', TEST_SECRET_KEY):
            with patch('app.auth.ALGORITHM', TEST_ALGORITHM):
                response = client.get(
                    "/auth/verify",
                    headers={"Authorization": f"Bearer {tampered}"}
                )

        assert response.status_code == 401

    def test_otp_cannot_be_reused(self, mock_db):
        """Test that OTP cannot be used multiple times"""
        db, cursor = mock_db

        cursor.fetchone.return_value = {
            'id': 1,
            'phone_number': TEST_PHONE_NUMBER,
            'otp': TEST_OTP,
            'phone_verified': False
        }

        with patch('app.database.get_db', return_value=db):
            # First verification
            response1 = client.post(
                "/auth/verify-otp",
                json={
                    "phone_number": TEST_PHONE_NUMBER,
                    "otp": TEST_OTP
                }
            )

            # Update mock to reflect verified state
            cursor.fetchone.return_value = {
                'id': 1,
                'phone_number': TEST_PHONE_NUMBER,
                'otp': None,  # OTP should be cleared
                'phone_verified': True
            }

            # Second verification attempt
            response2 = client.post(
                "/auth/verify-otp",
                json={
                    "phone_number": TEST_PHONE_NUMBER,
                    "otp": TEST_OTP
                }
            )

        assert response1.status_code == 200
        # Second attempt should fail (OTP already used or cleared)
        assert response2.status_code != 200


# Test execution summary
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
