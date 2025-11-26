"""
Docker Container Smoke Tests

Quick validation tests for Docker deployment:
- Health endpoint responds
- Authentication endpoints functional
- Chat endpoint works with authenticated user
- Database connectivity verified

Run with: pytest tests/smoke/test_docker_deployment.py -v
"""

import pytest
import requests
import time
from typing import Dict, Optional


class DockerSmokeTest:
    """Smoke test suite for Docker deployment"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.timeout = 10  # seconds

    def wait_for_service(self, max_retries: int = 30, delay: int = 2) -> bool:
        """Wait for service to be ready"""
        print(f"\n⏳ Waiting for service at {self.base_url}...")

        for attempt in range(max_retries):
            try:
                response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
                if response.status_code == 200:
                    print(f"✅ Service is ready (attempt {attempt + 1})")
                    return True
            except requests.exceptions.RequestException:
                if attempt < max_retries - 1:
                    print(f"⏳ Attempt {attempt + 1}/{max_retries} - waiting {delay}s...")
                    time.sleep(delay)

        print(f"❌ Service not ready after {max_retries * delay} seconds")
        return False

    def test_health_endpoint(self) -> Dict:
        """Test health check endpoint"""
        print("\n🏥 Testing health endpoint...")

        try:
            response = requests.get(f"{self.base_url}/health", timeout=self.timeout)

            result = {
                "test": "health_endpoint",
                "passed": response.status_code == 200,
                "status_code": response.status_code,
                "response": response.json() if response.status_code == 200 else None
            }

            if result['passed']:
                print(f"✅ Health check passed: {result['response']}")
            else:
                print(f"❌ Health check failed: {response.status_code}")

            return result

        except Exception as e:
            print(f"❌ Health check error: {str(e)}")
            return {"test": "health_endpoint", "passed": False, "error": str(e)}

    def test_database_connection(self) -> Dict:
        """Test database connectivity via health endpoint"""
        print("\n🗄️  Testing database connection...")

        try:
            response = requests.get(f"{self.base_url}/health/db", timeout=self.timeout)

            result = {
                "test": "database_connection",
                "passed": response.status_code == 200,
                "status_code": response.status_code,
                "response": response.json() if response.status_code == 200 else None
            }

            if result['passed']:
                print(f"✅ Database connection successful")
            else:
                print(f"❌ Database connection failed")

            return result

        except Exception as e:
            print(f"❌ Database test error: {str(e)}")
            return {"test": "database_connection", "passed": False, "error": str(e)}

    def test_otp_request(self, phone_number: str = "+1234567890") -> Dict:
        """Test OTP request endpoint"""
        print(f"\n📞 Testing OTP request for {phone_number}...")

        try:
            response = requests.post(
                f"{self.base_url}/auth/request-otp",
                json={"phone_number": phone_number},
                timeout=self.timeout
            )

            result = {
                "test": "otp_request",
                "passed": response.status_code == 200,
                "status_code": response.status_code,
                "response": response.json() if response.status_code == 200 else None
            }

            if result['passed']:
                print(f"✅ OTP request successful")
            else:
                print(f"❌ OTP request failed: {response.status_code}")

            return result

        except Exception as e:
            print(f"❌ OTP request error: {str(e)}")
            return {"test": "otp_request", "passed": False, "error": str(e)}

    def test_otp_verification(self, phone_number: str = "+1234567890",
                             otp: str = "123456") -> Dict:
        """Test OTP verification endpoint"""
        print(f"\n✅ Testing OTP verification...")

        try:
            response = requests.post(
                f"{self.base_url}/auth/verify-otp",
                json={"phone_number": phone_number, "otp": otp},
                timeout=self.timeout
            )

            result = {
                "test": "otp_verification",
                "passed": response.status_code == 200,
                "status_code": response.status_code,
                "response": response.json() if response.status_code == 200 else None,
                "token": None
            }

            if result['passed'] and result['response']:
                result['token'] = result['response'].get('access_token')
                print(f"✅ OTP verification successful - token received")
            else:
                print(f"❌ OTP verification failed: {response.status_code}")

            return result

        except Exception as e:
            print(f"❌ OTP verification error: {str(e)}")
            return {"test": "otp_verification", "passed": False, "error": str(e)}

    def test_chat_endpoint(self, token: str) -> Dict:
        """Test chat endpoint with authentication"""
        print(f"\n💬 Testing chat endpoint...")

        try:
            response = requests.post(
                f"{self.base_url}/chat",
                headers={"Authorization": f"Bearer {token}"},
                json={"message": "Hello, this is a smoke test"},
                timeout=self.timeout
            )

            result = {
                "test": "chat_endpoint",
                "passed": response.status_code == 200,
                "status_code": response.status_code,
                "response": response.json() if response.status_code == 200 else None
            }

            if result['passed']:
                print(f"✅ Chat endpoint working correctly")
            else:
                print(f"❌ Chat endpoint failed: {response.status_code}")

            return result

        except Exception as e:
            print(f"❌ Chat endpoint error: {str(e)}")
            return {"test": "chat_endpoint", "passed": False, "error": str(e)}

    def test_token_verification(self, token: str) -> Dict:
        """Test token verification endpoint"""
        print(f"\n🔐 Testing token verification...")

        try:
            response = requests.get(
                f"{self.base_url}/auth/verify",
                headers={"Authorization": f"Bearer {token}"},
                timeout=self.timeout
            )

            result = {
                "test": "token_verification",
                "passed": response.status_code == 200,
                "status_code": response.status_code,
                "response": response.json() if response.status_code == 200 else None
            }

            if result['passed']:
                print(f"✅ Token verification successful")
            else:
                print(f"❌ Token verification failed: {response.status_code}")

            return result

        except Exception as e:
            print(f"❌ Token verification error: {str(e)}")
            return {"test": "token_verification", "passed": False, "error": str(e)}

    def run_all_tests(self) -> Dict:
        """Run complete smoke test suite"""
        print("\n" + "="*60)
        print("🚀 DOCKER DEPLOYMENT SMOKE TESTS")
        print("="*60)

        results = []

        # Wait for service
        if not self.wait_for_service():
            return {
                "success": False,
                "error": "Service not available",
                "results": []
            }

        # Test 1: Health endpoint
        results.append(self.test_health_endpoint())

        # Test 2: Database connection
        results.append(self.test_database_connection())

        # Test 3: OTP request
        results.append(self.test_otp_request())

        # Test 4: OTP verification (get token)
        auth_result = self.test_otp_verification()
        results.append(auth_result)

        # If we got a token, test authenticated endpoints
        if auth_result.get('token'):
            token = auth_result['token']

            # Test 5: Token verification
            results.append(self.test_token_verification(token))

            # Test 6: Chat endpoint
            results.append(self.test_chat_endpoint(token))
        else:
            print("\n⚠️  Skipping authenticated endpoint tests (no token)")

        # Calculate summary
        total = len(results)
        passed = sum(1 for r in results if r.get('passed'))
        failed = total - passed

        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")

        return {
            "success": failed == 0,
            "total": total,
            "passed": passed,
            "failed": failed,
            "results": results
        }


@pytest.fixture
def smoke_test():
    """Create smoke test instance"""
    return DockerSmokeTest()


class TestDockerDeployment:
    """Pytest test class for Docker deployment"""

    def test_service_availability(self, smoke_test):
        """Test that service is running and responding"""
        assert smoke_test.wait_for_service(), "Service should be available"

    def test_health_check(self, smoke_test):
        """Test health endpoint"""
        result = smoke_test.test_health_endpoint()
        assert result['passed'], "Health check should pass"

    def test_database_connectivity(self, smoke_test):
        """Test database connection"""
        result = smoke_test.test_database_connection()
        assert result['passed'], "Database should be connected"

    def test_authentication_flow(self, smoke_test):
        """Test complete authentication flow"""
        # Request OTP
        otp_req = smoke_test.test_otp_request()
        assert otp_req['passed'], "OTP request should succeed"

        # Verify OTP
        verify = smoke_test.test_otp_verification()
        assert verify['passed'], "OTP verification should succeed"
        assert verify.get('token'), "Should receive access token"

    def test_authenticated_endpoints(self, smoke_test):
        """Test endpoints requiring authentication"""
        # Get token first
        verify = smoke_test.test_otp_verification()
        assert verify['passed'], "OTP verification should succeed"

        token = verify.get('token')
        assert token, "Should have token"

        # Test token verification
        token_verify = smoke_test.test_token_verification(token)
        assert token_verify['passed'], "Token verification should succeed"

        # Test chat endpoint
        chat = smoke_test.test_chat_endpoint(token)
        assert chat['passed'], "Chat endpoint should work with valid token"


def run_smoke_tests():
    """Standalone function to run smoke tests"""
    tester = DockerSmokeTest()
    summary = tester.run_all_tests()

    # Exit with appropriate code
    exit(0 if summary['success'] else 1)


if __name__ == "__main__":
    run_smoke_tests()
