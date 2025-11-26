"""
Enhanced Health Check Router
Provides comprehensive health endpoints with dependency checks
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
import logging

from app.database import get_db, engine
from app.config import settings
from app.services.health_monitor import HealthMonitorService
from app.utils.auth import get_current_admin_user

router = APIRouter()
logger = logging.getLogger(__name__)


class ServiceStatus(str, Enum):
    """Service health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"


class DependencyCheck(BaseModel):
    """Dependency health check result"""
    name: str = Field(..., description="Dependency name")
    status: ServiceStatus = Field(..., description="Health status")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    message: Optional[str] = Field(None, description="Status message")
    error: Optional[str] = Field(None, description="Error message if failed")


class HealthResponse(BaseModel):
    """Basic health check response"""
    status: ServiceStatus = Field(..., description="Overall service status")
    timestamp: datetime = Field(..., description="Check timestamp")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Environment name")


class ReadinessResponse(BaseModel):
    """Readiness probe response with dependency checks"""
    status: ServiceStatus = Field(..., description="Overall readiness status")
    timestamp: datetime = Field(..., description="Check timestamp")
    version: str = Field(..., description="Application version")
    dependencies: List[DependencyCheck] = Field(..., description="Dependency health checks")
    ready: bool = Field(..., description="Whether service is ready to accept traffic")


class DetailedHealthResponse(BaseModel):
    """Detailed health diagnostics response"""
    status: ServiceStatus = Field(..., description="Overall service status")
    timestamp: datetime = Field(..., description="Check timestamp")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Environment name")
    uptime_seconds: Optional[float] = Field(None, description="Service uptime in seconds")
    dependencies: List[DependencyCheck] = Field(..., description="All dependency checks")
    metrics: Dict = Field(..., description="Additional metrics and statistics")
    configuration: Dict = Field(..., description="Configuration summary")


# Track service start time for uptime calculation
service_start_time = datetime.utcnow()


@router.get("/health/live",
    response_model=HealthResponse,
    summary="Liveness Probe",
    description="Basic liveness check - returns 200 if service is running",
    tags=["Health"])
async def liveness_probe():
    """
    Liveness probe endpoint for Kubernetes/container orchestration.
    Returns 200 if the service process is alive.
    Does not check dependencies.
    """
    return HealthResponse(
        status=ServiceStatus.HEALTHY,
        timestamp=datetime.utcnow(),
        version="1.0.0",
        environment=settings.APP_ENV
    )


@router.get("/health/ready",
    response_model=ReadinessResponse,
    summary="Readiness Probe",
    description="Readiness check with all dependency health checks",
    tags=["Health"])
async def readiness_probe(db: Session = Depends(get_db)):
    """
    Readiness probe endpoint for Kubernetes/container orchestration.
    Checks all critical dependencies and returns 200 only if all are healthy.
    Returns 503 if any critical dependency is down.
    """
    monitor = HealthMonitorService(db)

    # Run health checks
    check_results = await monitor.perform_all_checks()

    # Convert results to dependency checks
    dependencies = []
    overall_healthy = True

    for result in check_results:
        # Map health status to service status
        if result["health_status"] == 2:  # HEALTHY
            dep_status = ServiceStatus.HEALTHY
        elif result["health_status"] == 1:  # PARTIAL
            dep_status = ServiceStatus.DEGRADED
            overall_healthy = False
        else:  # DOWN
            dep_status = ServiceStatus.DOWN
            overall_healthy = False

        dependencies.append(DependencyCheck(
            name=result["resource_name"],
            status=dep_status,
            response_time_ms=result.get("response_time_ms"),
            message=result.get("status_message"),
            error=result.get("error_message")
        ))

    # Determine overall status
    down_count = sum(1 for d in dependencies if d.status == ServiceStatus.DOWN)
    degraded_count = sum(1 for d in dependencies if d.status == ServiceStatus.DEGRADED)

    if down_count > 0:
        overall_status = ServiceStatus.DOWN
        ready = False
    elif degraded_count > 0:
        overall_status = ServiceStatus.DEGRADED
        ready = True  # Still ready but with warnings
    else:
        overall_status = ServiceStatus.HEALTHY
        ready = True

    response = ReadinessResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version="1.0.0",
        dependencies=dependencies,
        ready=ready
    )

    # Return 503 if service is not ready
    if not ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=response.model_dump()
        )

    return response


@router.get("/health/detailed",
    response_model=DetailedHealthResponse,
    summary="Detailed Health Diagnostics",
    description="Comprehensive health diagnostics - admin only",
    tags=["Health"])
async def detailed_health_check(
    db: Session = Depends(get_db),
    # current_user = Depends(get_current_admin_user)  # Uncomment when admin auth is ready
):
    """
    Detailed health diagnostics endpoint.
    Provides comprehensive information about service health, dependencies, and configuration.
    Should be restricted to admin users only in production.
    """
    monitor = HealthMonitorService(db)

    # Run all health checks
    check_results = await monitor.perform_all_checks()

    # Convert results to dependency checks
    dependencies = []
    critical_errors = []

    for result in check_results:
        # Map health status
        if result["health_status"] == 2:
            dep_status = ServiceStatus.HEALTHY
        elif result["health_status"] == 1:
            dep_status = ServiceStatus.DEGRADED
        else:
            dep_status = ServiceStatus.DOWN
            critical_errors.append({
                "service": result["resource_name"],
                "error": result.get("error_message", "Unknown error")
            })

        dependencies.append(DependencyCheck(
            name=result["resource_name"],
            status=dep_status,
            response_time_ms=result.get("response_time_ms"),
            message=result.get("status_message"),
            error=result.get("error_message")
        ))

    # Calculate overall status
    down_count = sum(1 for d in dependencies if d.status == ServiceStatus.DOWN)
    degraded_count = sum(1 for d in dependencies if d.status == ServiceStatus.DEGRADED)

    if down_count > 0:
        overall_status = ServiceStatus.DOWN
    elif degraded_count > 0:
        overall_status = ServiceStatus.DEGRADED
    else:
        overall_status = ServiceStatus.HEALTHY

    # Calculate uptime
    uptime = (datetime.utcnow() - service_start_time).total_seconds()

    # Gather metrics
    metrics = {
        "total_dependencies": len(dependencies),
        "healthy_count": sum(1 for d in dependencies if d.status == ServiceStatus.HEALTHY),
        "degraded_count": degraded_count,
        "down_count": down_count,
        "health_percentage": round(
            (sum(1 for d in dependencies if d.status == ServiceStatus.HEALTHY) / len(dependencies) * 100)
            if dependencies else 0,
            2
        ),
        "average_response_time_ms": round(
            sum(d.response_time_ms for d in dependencies if d.response_time_ms) /
            sum(1 for d in dependencies if d.response_time_ms)
            if any(d.response_time_ms for d in dependencies) else 0,
            2
        ),
        "critical_errors": critical_errors
    }

    # Configuration summary (hide sensitive data)
    configuration = {
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "debug_mode": settings.DEBUG,
        "database_configured": bool(settings.DATABASE_URL),
        "redis_configured": bool(settings.REDIS_URL),
        "azure_openai_configured": bool(settings.AZURE_OPENAI_ENDPOINT and settings.AZURE_OPENAI_API_KEY),
        "azure_speech_configured": bool(settings.AZURE_SPEECH_KEY and settings.AZURE_SPEECH_REGION),
        "anthropic_configured": bool(settings.ANTHROPIC_API_KEY),
        "smtp_configured": bool(settings.SMTP_USER and settings.SMTP_PASSWORD),
        "minio_configured": bool(settings.MINIO_ENDPOINT and settings.MINIO_ACCESS_KEY)
    }

    return DetailedHealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version="1.0.0",
        environment=settings.APP_ENV,
        uptime_seconds=uptime,
        dependencies=dependencies,
        metrics=metrics,
        configuration=configuration
    )


@router.get("/health",
    response_model=HealthResponse,
    summary="Basic Health Check",
    description="Simple health check endpoint",
    tags=["Health"])
async def basic_health_check():
    """
    Basic health check endpoint.
    Returns 200 if service is running.
    Backward compatible with existing /health endpoint.
    """
    return HealthResponse(
        status=ServiceStatus.HEALTHY,
        timestamp=datetime.utcnow(),
        version="1.0.0",
        environment=settings.APP_ENV
    )


@router.get("/health/demo-config",
    summary="Demo Config Debug",
    description="Debug endpoint to check demo configuration",
    tags=["Health"])
async def demo_config_check():
    """Debug endpoint to check demo account configuration."""
    import os
    from app.routers.auth import DEMO_PHONE_NUMBER, DEMO_OTP_CODE
    return {
        "demo_phone_number": DEMO_PHONE_NUMBER,
        "demo_otp_code": DEMO_OTP_CODE,
        "env_demo_phone": os.getenv("DEMO_PHONE_NUMBER", "NOT_SET"),
        "env_demo_otp": os.getenv("DEMO_OTP_CODE", "NOT_SET"),
        "timestamp": datetime.utcnow().isoformat()
    }
