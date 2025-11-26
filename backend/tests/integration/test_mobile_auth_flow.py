"""
Mobile Integration Tests for Authentication Flow

This test suite simulates mobile app behavior:
- Login with OTP
- Token saved to AsyncStorage
- App restart simulation
- Auto-login verification
- Logout flow
- OTP re-verification

Run with: pytest tests/integration/test_mobile_auth_flow.py -v
"""

import pytest
import requests
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Optional


class MockAsyncStorage:
    """Simulates React Native AsyncStorage"""

    def __init__(self):
        self.storage: Dict[str, str] = {}

    def setItem(self, key: str, value: str):
        """Store item in mock storage"""
        self.storage[key] = value
        print(f"📱 AsyncStorage.setItem: {key}")

    def getItem(self, key: str) -> Optional[str]:
        """Retrieve item from mock storage"""
        value = self.storage.get(key)
        print(f"📱 AsyncStorage.getItem: {key} = {'Found' if value else 'None'}")
        return value

    def removeItem(self, key: str):
        """Remove item from mock storage"""
        if key in self.storage:
            del self.storage[key]
            print(f"📱 AsyncStorage.removeItem: {key}")

    def clear(self):
        """Clear all storage"""
        self.storage.clear()
        print("📱 AsyncStorage.clear: All data cleared")

    def getAllKeys(self):
        """Get all storage keys"""
        return list(self.storage.keys())


class MobileAuthClient:
    """Simulates mobile app authentication client"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.storage = MockAsyncStorage()
        self.current_token: Optional[str] = None

    def request_otp(self, phone_number: str) -> Dict:
        """Request OTP for phone number"""
        print(f"\n📞 Requesting OTP for {phone_number}")
        response = requests.post(
            f"{self.base_url}/auth/request-otp",
            json={"phone_number": phone_number}
        )
        return {
            "status_code": response.status_code,
            "data": response.json() if response.status_code == 200 else None
        }

    def verify_otp(self, phone_number: str, otp: str) -> Dict:
        """Verify OTP and login"""
        print(f"\n✅ Verifying OTP for {phone_number}")
        response = requests.post(
            f"{self.base_url}/auth/verify-otp",
            json={
                "phone_number": phone_number,
                "otp": otp
            }
        )

        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')

            if token:
                # Simulate saving to AsyncStorage
                self.storage.setItem('access_token', token)
                self.storage.setItem('phone_number', phone_number)
                self.storage.setItem('login_timestamp', str(int(time.time())))
                self.current_token = token
                print(f"🔐 Token saved to AsyncStorage")

        return {
            "status_code": response.status_code,
            "data": response.json() if response.status_code == 200 else None
        }

    def check_auto_login(self) -> bool:
        """Check if auto-login is possible (simulates app restart)"""
        print("\n🔄 Simulating app restart - checking auto-login")

        # Clear in-memory state
        self.current_token = None

        # Try to retrieve token from storage
        stored_token = self.storage.getItem('access_token')

        if not stored_token:
            print("❌ No token found in storage")
            return False

        # Verify token is still valid
        response = requests.get(
            f"{self.base_url}/auth/verify",
            headers={"Authorization": f"Bearer {stored_token}"}
        )

        if response.status_code == 200:
            self.current_token = stored_token
            print("✅ Auto-login successful - token is valid")
            return True
        else:
            print(f"❌ Token invalid: {response.json()}")
            # Clear invalid token
            self.storage.removeItem('access_token')
            return False

    def logout(self):
        """Logout and clear all stored data"""
        print("\n🚪 Logging out")
        self.current_token = None
        self.storage.removeItem('access_token')
        self.storage.removeItem('phone_number')
        self.storage.removeItem('login_timestamp')
        print("✅ Logout complete - storage cleared")

    def send_chat_message(self, message: str) -> Dict:
        """Send chat message (requires authentication)"""
        print(f"\n💬 Sending chat message: '{message[:50]}...'")

        if not self.current_token:
            print("❌ No active token")
            return {"status_code": 401, "data": None}

        response = requests.post(
            f"{self.base_url}/chat",
            headers={"Authorization": f"Bearer {self.current_token}"},
            json={"message": message}
        )

        return {
            "status_code": response.status_code,
            "data": response.json() if response.status_code == 200 else None
        }

    def get_storage_info(self) -> Dict:
        """Get current storage state for debugging"""
        return {
            "keys": self.storage.getAllKeys(),
            "has_token": self.storage.getItem('access_token') is not None,
            "phone_number": self.storage.getItem('phone_number')
        }


class TestMobileAuthFlow:
    """Test complete mobile authentication flow"""

    @pytest.fixture
    def client(self):
        """Create mobile client instance"""
        return MobileAuthClient()

    @pytest.fixture
    def test_phone(self):
        """Test phone number"""
        return "+1234567890"

    @pytest.fixture
    def test_otp(self):
        """Test OTP (in dev mode, this is usually 123456)"""
        return "123456"

    def test_01_complete_login_flow(self, client, test_phone, test_otp):
        """Test: Request OTP -> Verify OTP -> Token Saved"""
        print("\n" + "="*60)
        print("TEST 1: Complete Login Flow")
        print("="*60)

        # Step 1: Request OTP
        otp_response = client.request_otp(test_phone)
        assert otp_response['status_code'] == 200, "OTP request should succeed"

        # Step 2: Verify OTP
        verify_response = client.verify_otp(test_phone, test_otp)
        assert verify_response['status_code'] == 200, "OTP verification should succeed"
        assert 'access_token' in verify_response['data'], "Should receive access token"

        # Step 3: Verify token is saved
        storage_info = client.get_storage_info()
        assert storage_info['has_token'], "Token should be saved to storage"
        assert storage_info['phone_number'] == test_phone, "Phone number should be saved"

        print("\n✅ TEST 1 PASSED: Login flow complete")

    def test_02_auto_login_after_restart(self, client, test_phone, test_otp):
        """Test: Login -> Restart App -> Auto-login Works"""
        print("\n" + "="*60)
        print("TEST 2: Auto-login After App Restart")
        print("="*60)

        # Step 1: Initial login
        client.verify_otp(test_phone, test_otp)
        assert client.current_token is not None, "Should have token after login"

        # Step 2: Simulate app restart
        auto_login_success = client.check_auto_login()
        assert auto_login_success, "Auto-login should succeed with valid token"
        assert client.current_token is not None, "Should restore token from storage"

        print("\n✅ TEST 2 PASSED: Auto-login successful")

    def test_03_logout_clears_tokens(self, client, test_phone, test_otp):
        """Test: Login -> Logout -> Storage Cleared"""
        print("\n" + "="*60)
        print("TEST 3: Logout Clears All Data")
        print("="*60)

        # Step 1: Login
        client.verify_otp(test_phone, test_otp)
        assert client.get_storage_info()['has_token'], "Should have token after login"

        # Step 2: Logout
        client.logout()

        # Step 3: Verify everything is cleared
        storage_info = client.get_storage_info()
        assert not storage_info['has_token'], "Token should be cleared"
        assert len(storage_info['keys']) == 0, "All storage should be cleared"
        assert client.current_token is None, "Current token should be None"

        print("\n✅ TEST 3 PASSED: Logout cleared all data")

    def test_04_auto_login_fails_after_logout(self, client, test_phone, test_otp):
        """Test: Login -> Logout -> Restart -> No Auto-login"""
        print("\n" + "="*60)
        print("TEST 4: Auto-login Fails After Logout")
        print("="*60)

        # Step 1: Login and logout
        client.verify_otp(test_phone, test_otp)
        client.logout()

        # Step 2: Try to auto-login
        auto_login_success = client.check_auto_login()
        assert not auto_login_success, "Auto-login should fail after logout"
        assert client.current_token is None, "Should not have token"

        print("\n✅ TEST 4 PASSED: Auto-login properly blocked after logout")

    def test_05_chat_requires_authentication(self, client, test_phone, test_otp):
        """Test: Chat Endpoint Requires Valid Token"""
        print("\n" + "="*60)
        print("TEST 5: Chat Requires Authentication")
        print("="*60)

        # Step 1: Try to send message without login
        response = client.send_chat_message("Hello without login")
        assert response['status_code'] == 401, "Chat should fail without authentication"

        # Step 2: Login
        client.verify_otp(test_phone, test_otp)

        # Step 3: Send message with authentication
        response = client.send_chat_message("Hello with authentication")
        assert response['status_code'] == 200, "Chat should succeed with valid token"

        print("\n✅ TEST 5 PASSED: Chat authentication working")

    def test_06_token_persistence_across_restarts(self, client, test_phone, test_otp):
        """Test: Login -> Restart -> Chat -> Restart -> Chat"""
        print("\n" + "="*60)
        print("TEST 6: Token Persists Across Multiple Restarts")
        print("="*60)

        # Step 1: Login
        client.verify_otp(test_phone, test_otp)

        # Step 2: First restart
        client.check_auto_login()
        response1 = client.send_chat_message("Message after restart 1")
        assert response1['status_code'] == 200, "Chat should work after restart 1"

        # Step 3: Second restart
        client.check_auto_login()
        response2 = client.send_chat_message("Message after restart 2")
        assert response2['status_code'] == 200, "Chat should work after restart 2"

        print("\n✅ TEST 6 PASSED: Token persists across multiple restarts")

    def test_07_otp_reverification_flow(self, client, test_phone, test_otp):
        """Test: Logout -> Re-login -> New Token Issued"""
        print("\n" + "="*60)
        print("TEST 7: OTP Re-verification After Logout")
        print("="*60)

        # Step 1: First login
        verify1 = client.verify_otp(test_phone, test_otp)
        token1 = verify1['data']['access_token']

        # Step 2: Logout
        client.logout()

        # Step 3: Re-login
        verify2 = client.verify_otp(test_phone, test_otp)
        token2 = verify2['data']['access_token']

        # Tokens should be different (new token issued)
        assert token1 != token2, "New token should be issued on re-login"

        print("\n✅ TEST 7 PASSED: Re-verification works correctly")

    def test_08_storage_isolation(self, client, test_phone, test_otp):
        """Test: Multiple Logout/Login Cycles Don't Corrupt Storage"""
        print("\n" + "="*60)
        print("TEST 8: Storage Isolation Across Multiple Cycles")
        print("="*60)

        for cycle in range(3):
            print(f"\n--- Cycle {cycle + 1} ---")

            # Login
            client.verify_otp(test_phone, test_otp)
            assert client.get_storage_info()['has_token'], f"Cycle {cycle + 1}: Login failed"

            # Verify chat works
            response = client.send_chat_message(f"Message in cycle {cycle + 1}")
            assert response['status_code'] == 200, f"Cycle {cycle + 1}: Chat failed"

            # Logout
            client.logout()
            assert not client.get_storage_info()['has_token'], f"Cycle {cycle + 1}: Logout failed"

        print("\n✅ TEST 8 PASSED: Storage remains consistent across cycles")


class TestTokenExpiration:
    """Test token expiration handling"""

    @pytest.fixture
    def client(self):
        return MobileAuthClient()

    def test_expired_token_rejected(self, client):
        """Test: Expired Token Should Be Rejected"""
        print("\n" + "="*60)
        print("TEST: Expired Token Handling")
        print("="*60)

        # This test would need a way to create an expired token
        # In production, you might need to wait or manipulate server time

        # For now, test with an obviously invalid token
        client.storage.setItem('access_token', 'expired.invalid.token')

        auto_login = client.check_auto_login()
        assert not auto_login, "Expired/invalid token should be rejected"

        print("\n✅ TEST PASSED: Expired tokens are rejected")


# Run summary
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 MOBILE AUTH INTEGRATION TESTS")
    print("="*60)
    print("\nThese tests simulate complete mobile app authentication flows.")
    print("Make sure the backend server is running on http://localhost:8000")
    print("\nRun with: pytest tests/integration/test_mobile_auth_flow.py -v\n")

    pytest.main([__file__, "-v", "--tb=short", "-s"])
