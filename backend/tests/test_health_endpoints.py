"""
Test suite for enhanced health check endpoints
Tests all new health endpoints: /health, /health/live, /health/ready, /health/detailed
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock
from datetime import datetime

from app.main import app
from app.database import get_db
from app.services.health_monitor import HealthMonitorService
from app.models.resource_health import HealthStatus


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


class TestBasicHealthEndpoint:
    """Test basic /health endpoint"""

    def test_health_endpoint_returns_200(self, client):
        """Test that /health returns 200 OK"""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_endpoint_structure(self, client):
        """Test that /health returns expected structure"""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "environment" in data
        assert data["status"] == "healthy"

    def test_health_endpoint_timestamp_format(self, client):
        """Test that timestamp is in ISO format"""
        response = client.get("/health")
        data = response.json()

        # Should be parseable as datetime
        timestamp = datetime.fromisoformat(data["timestamp"])
        assert isinstance(timestamp, datetime)


class TestLivenessProbe:
    """Test /health/live liveness probe endpoint"""

    def test_liveness_always_returns_200(self, client):
        """Test that liveness probe always returns 200 when service is running"""
        response = client.get("/health/live")
        assert response.status_code == 200

    def test_liveness_response_structure(self, client):
        """Test liveness probe response structure"""
        response = client.get("/health/live")
        data = response.json()

        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert "environment" in data

    def test_liveness_no_dependency_checks(self, client):
        """Test that liveness probe doesn't include dependency checks"""
        response = client.get("/health/live")
        data = response.json()

        # Liveness should not have dependencies field
        assert "dependencies" not in data


class TestReadinessProbe:
    """Test /health/ready readiness probe endpoint"""

    @patch('app.services.health_monitor.HealthMonitorService.perform_all_checks')
    def test_readiness_all_healthy(self, mock_checks, client):
        """Test readiness probe when all dependencies are healthy"""
        # Mock all checks as healthy
        mock_checks.return_value = [
            {
                "resource_name": "PostgreSQL Database",
                "health_status": HealthStatus.HEALTHY.value,
                "response_time_ms": 5.0,
                "status_message": "Healthy",
                "error_message": None
            },
            {
                "resource_name": "Redis Cache",
                "health_status": HealthStatus.HEALTHY.value,
                "response_time_ms": 3.0,
                "status_message": "Healthy",
                "error_message": None
            }
        ]

        response = client.get("/health/ready")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["ready"] is True
        assert len(data["dependencies"]) == 2

    @patch('app.services.health_monitor.HealthMonitorService.perform_all_checks')
    def test_readiness_degraded_service(self, mock_checks, client):
        """Test readiness probe with degraded service (still ready but warning)"""
        mock_checks.return_value = [
            {
                "resource_name": "PostgreSQL Database",
                "health_status": HealthStatus.HEALTHY.value,
                "response_time_ms": 5.0,
                "status_message": "Healthy",
                "error_message": None
            },
            {
                "resource_name": "Redis Cache",
                "health_status": HealthStatus.PARTIAL.value,
                "response_time_ms": 50.0,
                "status_message": "Degraded",
                "error_message": "Slow response"
            }
        ]

        response = client.get("/health/ready")
        # Still returns 200 for degraded (partial) services
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "degraded"
        assert data["ready"] is True  # Still ready, just degraded

    @patch('app.services.health_monitor.HealthMonitorService.perform_all_checks')
    def test_readiness_service_down(self, mock_checks, client):
        """Test readiness probe when service is down (not ready)"""
        mock_checks.return_value = [
            {
                "resource_name": "PostgreSQL Database",
                "health_status": HealthStatus.DOWN.value,
                "response_time_ms": 0,
                "status_message": None,
                "error_message": "Connection refused"
            }
        ]

        response = client.get("/health/ready")
        # Returns 503 when critical service is down
        assert response.status_code == 503

        data = response.json()
        assert "detail" in data
        detail = data["detail"]
        assert detail["status"] == "down"
        assert detail["ready"] is False

    @patch('app.services.health_monitor.HealthMonitorService.perform_all_checks')
    def test_readiness_includes_all_dependencies(self, mock_checks, client):
        """Test that readiness includes all dependency checks"""
        mock_checks.return_value = [
            {
                "resource_name": "PostgreSQL Database",
                "health_status": HealthStatus.HEALTHY.value,
                "response_time_ms": 5.0,
                "status_message": "Healthy",
                "error_message": None
            },
            {
                "resource_name": "Azure OpenAI API",
                "health_status": HealthStatus.HEALTHY.value,
                "response_time_ms": 120.0,
                "status_message": "Operational",
                "error_message": None
            }
        ]

        response = client.get("/health/ready")
        data = response.json()

        assert "dependencies" in data
        assert len(data["dependencies"]) == 2

        # Check dependency structure
        for dep in data["dependencies"]:
            assert "name" in dep
            assert "status" in dep
            assert "response_time_ms" in dep


class TestDetailedHealthCheck:
    """Test /health/detailed endpoint"""

    @patch('app.services.health_monitor.HealthMonitorService.perform_all_checks')
    def test_detailed_health_structure(self, mock_checks, client):
        """Test detailed health check response structure"""
        mock_checks.return_value = [
            {
                "resource_name": "PostgreSQL Database",
                "health_status": HealthStatus.HEALTHY.value,
                "response_time_ms": 5.0,
                "status_message": "Healthy",
                "error_message": None
            }
        ]

        response = client.get("/health/detailed")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "environment" in data
        assert "uptime_seconds" in data
        assert "dependencies" in data
        assert "metrics" in data
        assert "configuration" in data

    @patch('app.services.health_monitor.HealthMonitorService.perform_all_checks')
    def test_detailed_health_metrics(self, mock_checks, client):
        """Test that detailed health includes comprehensive metrics"""
        mock_checks.return_value = [
            {
                "resource_name": "PostgreSQL Database",
                "health_status": HealthStatus.HEALTHY.value,
                "response_time_ms": 10.0,
                "status_message": "Healthy",
                "error_message": None
            },
            {
                "resource_name": "Redis Cache",
                "health_status": HealthStatus.PARTIAL.value,
                "response_time_ms": 20.0,
                "status_message": "Degraded",
                "error_message": "Slow"
            },
            {
                "resource_name": "Azure OpenAI API",
                "health_status": HealthStatus.DOWN.value,
                "response_time_ms": 0,
                "status_message": None,
                "error_message": "Connection failed"
            }
        ]

        response = client.get("/health/detailed")
        data = response.json()

        metrics = data["metrics"]
        assert metrics["total_dependencies"] == 3
        assert metrics["healthy_count"] == 1
        assert metrics["degraded_count"] == 1
        assert metrics["down_count"] == 1
        assert "health_percentage" in metrics
        assert "average_response_time_ms" in metrics
        assert "critical_errors" in metrics

    @patch('app.services.health_monitor.HealthMonitorService.perform_all_checks')
    def test_detailed_health_configuration_summary(self, mock_checks, client):
        """Test that detailed health includes configuration summary"""
        mock_checks.return_value = []

        response = client.get("/health/detailed")
        data = response.json()

        config = data["configuration"]
        assert "app_name" in config
        assert "environment" in config
        assert "debug_mode" in config
        assert "database_configured" in config
        assert "azure_openai_configured" in config
        assert "azure_speech_configured" in config

        # Configuration values should be booleans
        assert isinstance(config["database_configured"], bool)
        assert isinstance(config["azure_openai_configured"], bool)

    @patch('app.services.health_monitor.HealthMonitorService.perform_all_checks')
    def test_detailed_health_uptime_calculation(self, mock_checks, client):
        """Test that uptime is calculated correctly"""
        mock_checks.return_value = []

        response = client.get("/health/detailed")
        data = response.json()

        uptime = data["uptime_seconds"]
        assert isinstance(uptime, (int, float))
        assert uptime >= 0

    @patch('app.services.health_monitor.HealthMonitorService.perform_all_checks')
    def test_detailed_health_critical_errors(self, mock_checks, client):
        """Test that critical errors are tracked"""
        mock_checks.return_value = [
            {
                "resource_name": "PostgreSQL Database",
                "health_status": HealthStatus.DOWN.value,
                "response_time_ms": 0,
                "status_message": None,
                "error_message": "Connection refused"
            },
            {
                "resource_name": "Azure OpenAI API",
                "health_status": HealthStatus.DOWN.value,
                "response_time_ms": 0,
                "status_message": None,
                "error_message": "Authentication failed"
            }
        ]

        response = client.get("/health/detailed")
        data = response.json()

        critical_errors = data["metrics"]["critical_errors"]
        assert len(critical_errors) == 2

        # Check error structure
        for error in critical_errors:
            assert "service" in error
            assert "error" in error


class TestHealthCheckIntegration:
    """Integration tests for health check system"""

    @patch('app.services.health_monitor.HealthMonitorService.perform_all_checks')
    def test_all_endpoints_consistency(self, mock_checks, client):
        """Test that all health endpoints return consistent version info"""
        mock_checks.return_value = []

        live_response = client.get("/health/live")
        ready_response = client.get("/health/ready")
        detailed_response = client.get("/health/detailed")
        basic_response = client.get("/health")

        # All should return same version
        assert live_response.json()["version"] == "1.0.0"
        assert ready_response.json()["version"] == "1.0.0"
        assert detailed_response.json()["version"] == "1.0.0"
        assert basic_response.json()["version"] == "1.0.0"

    @patch('app.services.health_monitor.HealthMonitorService.perform_all_checks')
    def test_readiness_vs_liveness_difference(self, mock_checks, client):
        """Test that readiness checks dependencies but liveness does not"""
        # Mock a down database
        mock_checks.return_value = [
            {
                "resource_name": "PostgreSQL Database",
                "health_status": HealthStatus.DOWN.value,
                "response_time_ms": 0,
                "status_message": None,
                "error_message": "Connection failed"
            }
        ]

        # Liveness should still return 200
        liveness = client.get("/health/live")
        assert liveness.status_code == 200
        assert liveness.json()["status"] == "healthy"

        # Readiness should return 503
        readiness = client.get("/health/ready")
        assert readiness.status_code == 503
        assert readiness.json()["detail"]["ready"] is False
