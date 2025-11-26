"""
Test OTP verification state tracking

Tests for the OTP verification fields and JWT token updates.
"""

import pytest
from datetime import datetime, timedelta
from jose import jwt

from app.models.user import User
from app.routers.auth import create_access_token
from app.config import settings


class TestOTPVerificationFields:
    """Test OTP verification database fields"""

    def test_user_model_has_verification_fields(self, db_session):
        """Test that User model has OTP verification fields"""
        user = User(
            phone="+919876543210",
            email="test@boloo-users.local",
            role="citizen"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Check default values
        assert hasattr(user, 'phone_verified')
        assert hasattr(user, 'phone_verified_at')
        assert hasattr(user, 'last_otp_verified_at')

        assert user.phone_verified is False
        assert user.phone_verified_at is None
        assert user.last_otp_verified_at is None

    def test_user_verification_update(self, db_session):
        """Test updating user verification status"""
        user = User(
            phone="+919876543210",
            email="test@boloo-users.local",
            role="citizen"
        )
        db_session.add(user)
        db_session.commit()

        # Verify phone
        user.phone_verified = True
        user.phone_verified_at = datetime.utcnow()
        user.last_otp_verified_at = datetime.utcnow()

        db_session.commit()
        db_session.refresh(user)

        assert user.phone_verified is True
        assert user.phone_verified_at is not None
        assert user.last_otp_verified_at is not None

    def test_user_to_dict_includes_verification(self, db_session):
        """Test that to_dict() includes verification fields"""
        user = User(
            phone="+919876543210",
            email="test@boloo-users.local",
            role="citizen",
            phone_verified=True,
            phone_verified_at=datetime.utcnow(),
            last_otp_verified_at=datetime.utcnow()
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        user_dict = user.to_dict()

        assert 'phone_verified' in user_dict
        assert 'phone_verified_at' in user_dict
        assert 'last_otp_verified_at' in user_dict

        assert user_dict['phone_verified'] is True
        assert user_dict['phone_verified_at'] is not None
        assert user_dict['last_otp_verified_at'] is not None


class TestJWTTokenGeneration:
    """Test JWT token generation with OTP verification"""

    def test_jwt_token_includes_phone_verified(self):
        """Test that JWT token includes phone_verified field"""
        user_id = "test-user-id"
        phone_number = "+919876543210"

        token = create_access_token(
            user_id=user_id,
            phone_number=phone_number,
            phone_verified=True
        )

        # Decode token
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        assert 'phone_verified' in payload
        assert payload['phone_verified'] is True
        assert payload['phone_number'] == phone_number
        assert payload['sub'] == user_id

    def test_jwt_token_with_unverified_phone(self):
        """Test JWT token with unverified phone"""
        user_id = "test-user-id"

        token = create_access_token(
            user_id=user_id,
            phone_verified=False
        )

        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        assert payload['phone_verified'] is False

    def test_jwt_token_expiration(self):
        """Test JWT token expiration"""
        user_id = "test-user-id"

        token = create_access_token(
            user_id=user_id,
            phone_verified=True
        )

        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # Check expiration is set
        assert 'exp' in payload

        # Check expiration is in the future
        exp_time = datetime.fromtimestamp(payload['exp'])
        assert exp_time > datetime.utcnow()

        # Check expiration is approximately JWT_EXPIRATION_HOURS from now
        expected_exp = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
        time_diff = abs((exp_time - expected_exp).total_seconds())
        assert time_diff < 10  # Within 10 seconds


class TestOTPVerificationEndpoint:
    """Test /auth/verify endpoint"""

    @pytest.mark.asyncio
    async def test_verify_endpoint_with_valid_token(self, client, db_session):
        """Test /auth/verify with valid token"""
        # Create test user
        user = User(
            phone="+919876543210",
            email="test@boloo-users.local",
            role="citizen",
            phone_verified=True,
            phone_verified_at=datetime.utcnow()
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Create token
        token = create_access_token(
            user_id=str(user.id),
            phone_number=user.phone,
            phone_verified=True
        )

        # Test endpoint
        response = client.get(
            "/auth/verify",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200

        data = response.json()
        assert data['valid'] is True
        assert data['phone_verified'] is True
        assert data['user_id'] == str(user.id)
        assert data['phone_number'] == user.phone

    @pytest.mark.asyncio
    async def test_verify_endpoint_with_invalid_token(self, client):
        """Test /auth/verify with invalid token"""
        response = client.get(
            "/auth/verify",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401
        assert 'Invalid or expired token' in response.json()['detail']

    @pytest.mark.asyncio
    async def test_verify_endpoint_without_token(self, client):
        """Test /auth/verify without token"""
        response = client.get("/auth/verify")

        assert response.status_code == 401


class TestOTPVerificationFlow:
    """Integration test for full OTP verification flow"""

    @pytest.mark.asyncio
    async def test_complete_otp_flow_updates_verification_status(
        self, client, db_session, mock_msg91
    ):
        """Test that OTP verification updates user verification status"""
        phone = "+919876543210"

        # Step 1: Request OTP
        response = client.post(
            "/auth/otp/request",
            json={"phone_number": phone}
        )
        assert response.status_code == 200

        # Step 2: Verify OTP (mock will auto-verify)
        # Get the OTP code from mock
        otp_code = mock_msg91.get_last_otp(phone)

        response = client.post(
            "/auth/otp/verify",
            json={
                "phone_number": phone,
                "otp_code": otp_code
            }
        )

        assert response.status_code == 200

        data = response.json()

        # Check token is returned
        assert 'access_token' in data
        assert 'user' in data

        # Check user verification status
        user_data = data['user']
        assert user_data['phone_verified'] is True
        assert user_data['phone_verified_at'] is not None
        assert user_data['last_otp_verified_at'] is not None

        # Decode token and check payload
        token = data['access_token']
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        assert payload['phone_verified'] is True
        assert payload['phone_number'] == phone

        # Step 3: Verify database state
        user = db_session.query(User).filter(User.phone == phone).first()
        assert user is not None
        assert user.phone_verified is True
        assert user.phone_verified_at is not None
        assert user.last_otp_verified_at is not None


# Fixtures

@pytest.fixture
def db_session(app):
    """Create database session for testing"""
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(app):
    """Create test client"""
    from fastapi.testclient import TestClient

    return TestClient(app)


@pytest.fixture
def mock_msg91():
    """Mock MSG91 service"""
    class MockMSG91:
        def __init__(self):
            self.otps = {}

        async def send_otp(self, phone_number, db, otp_length=6):
            otp_code = "123456"  # Fixed OTP for testing
            self.otps[phone_number] = otp_code

            # Store in database
            from app.models.otp import OTP
            from datetime import datetime, timedelta

            otp = OTP(
                phone_number=phone_number,  # Use phone_number column
                otp_code=otp_code,
                expires_at=datetime.utcnow() + timedelta(minutes=5)
            )
            db.add(otp)
            db.commit()

            return {
                "message": "OTP sent successfully",
                "otp_for_testing": otp_code
            }

        def get_last_otp(self, phone_number):
            return self.otps.get(phone_number, "123456")

    return MockMSG91()
