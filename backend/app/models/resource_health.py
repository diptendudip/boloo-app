"""
Resource Health Monitoring Model
Tracks health status of all system resources (internal and external)
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.database import Base


class ResourceType(str, enum.Enum):
    """Resource type classification"""
    INTERNAL = "internal"  # Services we control (API, DB, Redis, MinIO)
    EXTERNAL = "external"  # Third-party services (Azure, Claude, SMTP)


class ResourceCategory(str, enum.Enum):
    """Resource category for grouping"""
    API = "api"
    DATABASE = "database"
    CACHE = "cache"
    STORAGE = "storage"
    AI_SERVICE = "ai_service"
    SPEECH_SERVICE = "speech_service"
    EMAIL_SERVICE = "email_service"
    NETWORK = "network"
    WORKER = "worker"


class HealthStatus(int, enum.Enum):
    """
    Health status with 0-2 rating system:
    0 = RED (Not operational / Critical failure)
    1 = YELLOW (API responds but limited functionality)
    2 = GREEN (Active and data/full functionality available)
    """
    DOWN = 0  # RED: Not operational
    PARTIAL = 1  # YELLOW: Responding but limited
    HEALTHY = 2  # GREEN: Fully operational


class ResourceHealth(Base):
    """
    Tracks health status of all system resources
    Updated periodically by background worker
    """
    __tablename__ = "resource_health"

    id = Column(Integer, primary_key=True, index=True)

    # Resource identification
    resource_name = Column(String(100), unique=True, nullable=False, index=True)
    resource_type = Column(SQLEnum(ResourceType), nullable=False, index=True)
    resource_category = Column(SQLEnum(ResourceCategory), nullable=False)

    # Health status (0-2 rating)
    health_status = Column(Integer, default=0, nullable=False)  # 0=DOWN, 1=PARTIAL, 2=HEALTHY

    # Metrics
    response_time_ms = Column(Float, nullable=True)  # Response time in milliseconds
    last_check_at = Column(DateTime(timezone=True), nullable=True)
    last_success_at = Column(DateTime(timezone=True), nullable=True)
    last_failure_at = Column(DateTime(timezone=True), nullable=True)

    # Failure tracking
    consecutive_failures = Column(Integer, default=0)
    total_failures = Column(Integer, default=0)
    total_checks = Column(Integer, default=0)

    # Status details
    status_message = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    # Metadata
    endpoint_url = Column(String(500), nullable=True)  # For API endpoints
    dependencies = Column(JSON, nullable=True)  # List of dependent resources
    restart_enabled = Column(Boolean, default=False)  # Can this be auto-restarted?
    restart_command = Column(String(500), nullable=True)  # Command to restart service
    restart_count = Column(Integer, default=0)  # How many times restarted
    last_restart_at = Column(DateTime(timezone=True), nullable=True)

    # Check configuration
    check_interval_seconds = Column(Integer, default=60)  # How often to check
    timeout_seconds = Column(Integer, default=10)  # Timeout for health check

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<ResourceHealth {self.resource_name} [{self.health_status}]>"

    @property
    def is_healthy(self) -> bool:
        """Check if resource is fully healthy (status 2)"""
        return self.health_status == HealthStatus.HEALTHY.value

    @property
    def is_down(self) -> bool:
        """Check if resource is down (status 0)"""
        return self.health_status == HealthStatus.DOWN.value

    @property
    def needs_restart(self) -> bool:
        """Check if service needs restart (down for >5 mins and restart enabled)"""
        if not self.restart_enabled or not self.last_failure_at:
            return False

        # Check if down for more than 5 minutes
        down_duration = (datetime.utcnow() - self.last_failure_at).total_seconds()
        return self.is_down and down_duration > 300  # 5 minutes

    @property
    def uptime_percentage(self) -> float:
        """Calculate uptime percentage"""
        if self.total_checks == 0:
            return 0.0
        return ((self.total_checks - self.total_failures) / self.total_checks) * 100

    @property
    def health_color(self) -> str:
        """Get color indicator for health status"""
        if self.health_status == HealthStatus.HEALTHY.value:
            return "green"
        elif self.health_status == HealthStatus.PARTIAL.value:
            return "yellow"
        else:
            return "red"

    def to_dict(self) -> dict:
        """Convert to dictionary for API response"""
        return {
            "id": self.id,
            "resource_name": self.resource_name,
            "resource_type": self.resource_type.value if self.resource_type else None,
            "resource_category": self.resource_category.value if self.resource_category else None,
            "health_status": self.health_status,
            "health_color": self.health_color,
            "response_time_ms": self.response_time_ms,
            "last_check_at": self.last_check_at.isoformat() if self.last_check_at else None,
            "last_success_at": self.last_success_at.isoformat() if self.last_success_at else None,
            "last_failure_at": self.last_failure_at.isoformat() if self.last_failure_at else None,
            "consecutive_failures": self.consecutive_failures,
            "total_failures": self.total_failures,
            "total_checks": self.total_checks,
            "uptime_percentage": round(self.uptime_percentage, 2),
            "status_message": self.status_message,
            "error_message": self.error_message,
            "endpoint_url": self.endpoint_url,
            "dependencies": self.dependencies,
            "restart_enabled": self.restart_enabled,
            "restart_count": self.restart_count,
            "last_restart_at": self.last_restart_at.isoformat() if self.last_restart_at else None,
            "check_interval_seconds": self.check_interval_seconds,
            "needs_restart": self.needs_restart,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class HealthCheckLog(Base):
    """
    Detailed log of health check executions
    Useful for debugging and historical analysis
    """
    __tablename__ = "health_check_logs"

    id = Column(Integer, primary_key=True, index=True)
    resource_name = Column(String(100), nullable=False, index=True)
    check_timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    health_status = Column(Integer, nullable=False)
    response_time_ms = Column(Float, nullable=True)
    status_message = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    check_metadata = Column(JSON, nullable=True)  # Renamed from 'metadata' to avoid conflict

    def __repr__(self):
        return f"<HealthCheckLog {self.resource_name} at {self.check_timestamp}>"
