"""
Enhanced Monitoring Router - v2
Provides comprehensive health monitoring with internal/external categorization,
restart capabilities, and detailed resource tracking
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

from app.database import get_db
from app.config import settings
from app.models.resource_health import ResourceHealth, HealthCheckLog, ResourceType, HealthStatus
from app.services.health_monitor import HealthMonitorService
from app.utils.auth import get_current_admin_user  # For protected endpoints

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health/dashboard")
async def get_health_dashboard(db: Session = Depends(get_db)):
    """
    Get comprehensive health dashboard with all resources
    categorized by internal and external
    """
    monitor = HealthMonitorService(db)

    # Get resources categorized
    internal_resources = monitor.get_internal_resources()
    external_resources = monitor.get_external_resources()

    # Calculate overall health
    all_resources = internal_resources + external_resources
    total_resources = len(all_resources)
    healthy_count = sum(1 for r in all_resources if r.health_status == HealthStatus.HEALTHY.value)
    partial_count = sum(1 for r in all_resources if r.health_status == HealthStatus.PARTIAL.value)
    down_count = sum(1 for r in all_resources if r.health_status == HealthStatus.DOWN.value)

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "overall_health": {
            "total_resources": total_resources,
            "healthy": healthy_count,
            "partial": partial_count,
            "down": down_count,
            "health_percentage": round((healthy_count / total_resources * 100) if total_resources > 0 else 0, 2)
        },
        "internal_resources": [r.to_dict() for r in internal_resources],
        "external_resources": [r.to_dict() for r in external_resources],
        "critical_alerts": [
            {
                "resource": r.resource_name,
                "message": f"Down for {(datetime.utcnow() - r.last_failure_at).total_seconds() / 60:.1f} minutes" if r.last_failure_at else "Status unknown",
                "severity": "critical"
            }
            for r in all_resources if r.health_status == HealthStatus.DOWN.value
        ]
    }


@router.get("/health/resources")
async def get_all_resources(
    resource_type: Optional[str] = None,
    status: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get all monitored resources with optional filtering
    Query params:
    - resource_type: internal|external
    - status: 0|1|2 (DOWN|PARTIAL|HEALTHY)
    """
    monitor = HealthMonitorService(db)

    query = db.query(ResourceHealth)

    if resource_type:
        try:
            resource_type_enum = ResourceType(resource_type)
            query = query.filter(ResourceHealth.resource_type == resource_type_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid resource_type. Use 'internal' or 'external'")

    if status is not None:
        if status not in [0, 1, 2]:
            raise HTTPException(status_code=400, detail="Invalid status. Use 0 (DOWN), 1 (PARTIAL), or 2 (HEALTHY)")
        query = query.filter(ResourceHealth.health_status == status)

    resources = query.all()

    return {
        "count": len(resources),
        "resources": [r.to_dict() for r in resources]
    }


@router.get("/health/resources/{resource_name}")
async def get_resource_details(resource_name: str, db: Session = Depends(get_db)):
    """Get detailed information about a specific resource including history"""
    resource = db.query(ResourceHealth).filter(
        ResourceHealth.resource_name == resource_name
    ).first()

    if not resource:
        raise HTTPException(status_code=404, detail=f"Resource '{resource_name}' not found")

    # Get recent check logs (last 24 hours)
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_logs = db.query(HealthCheckLog).filter(
        HealthCheckLog.resource_name == resource_name,
        HealthCheckLog.check_timestamp >= yesterday
    ).order_by(HealthCheckLog.check_timestamp.desc()).limit(100).all()

    # Calculate stats
    if recent_logs:
        avg_response_time = sum(log.response_time_ms for log in recent_logs if log.response_time_ms) / len(recent_logs)
        failure_count = sum(1 for log in recent_logs if log.health_status != HealthStatus.HEALTHY.value)
    else:
        avg_response_time = 0
        failure_count = 0

    return {
        "resource": resource.to_dict(),
        "statistics_24h": {
            "total_checks": len(recent_logs),
            "failures": failure_count,
            "average_response_time_ms": round(avg_response_time, 2) if recent_logs else 0,
            "uptime_percentage": round(((len(recent_logs) - failure_count) / len(recent_logs) * 100) if recent_logs else 0, 2)
        },
        "recent_checks": [
            {
                "timestamp": log.check_timestamp.isoformat(),
                "status": log.health_status,
                "response_time_ms": log.response_time_ms,
                "message": log.status_message or log.error_message
            }
            for log in recent_logs[:20]  # Last 20 checks
        ],
        "dependencies": resource.dependencies or []
    }


@router.post("/health/check")
async def trigger_health_check(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Manually trigger a health check for all resources
    Runs in background and updates database
    """
    async def run_check():
        monitor = HealthMonitorService(db)
        try:
            await monitor.run_health_checks_and_save()
            logger.info("Manual health check completed successfully")
        except Exception as e:
            logger.error(f"Manual health check failed: {e}", exc_info=True)

    background_tasks.add_task(run_check)

    return {
        "message": "Health check initiated",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/health/resources/{resource_name}/restart")
async def restart_resource(
    resource_name: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    # current_user = Depends(get_current_admin_user)  # Uncomment when auth is ready
):
    """
    Manually restart a resource/service
    Only works for internal resources with restart_enabled=True
    """
    resource = db.query(ResourceHealth).filter(
        ResourceHealth.resource_name == resource_name
    ).first()

    if not resource:
        raise HTTPException(status_code=404, detail=f"Resource '{resource_name}' not found")

    if resource.resource_type != ResourceType.INTERNAL:
        raise HTTPException(status_code=400, detail="Can only restart internal resources")

    if not resource.restart_enabled:
        raise HTTPException(status_code=400, detail=f"Restart not enabled for '{resource_name}'")

    if not resource.restart_command:
        raise HTTPException(status_code=400, detail=f"No restart command configured for '{resource_name}'")

    # Execute restart in background
    def execute_restart():
        import subprocess
        try:
            logger.info(f"Executing restart for {resource_name}: {resource.restart_command}")
            result = subprocess.run(
                resource.restart_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )

            # Update resource
            resource.restart_count += 1
            resource.last_restart_at = datetime.utcnow()
            resource.consecutive_failures = 0  # Reset failure count after restart
            db.commit()

            logger.info(f"Restart completed for {resource_name}. Exit code: {result.returncode}")

            if result.returncode != 0:
                logger.error(f"Restart stderr: {result.stderr}")

        except subprocess.TimeoutExpired:
            logger.error(f"Restart command timeout for {resource_name}")
        except Exception as e:
            logger.error(f"Restart failed for {resource_name}: {e}", exc_info=True)

    background_tasks.add_task(execute_restart)

    return {
        "message": f"Restart initiated for {resource_name}",
        "restart_count": resource.restart_count + 1,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/resources/{resource_name}/history")
async def get_resource_history(
    resource_name: str,
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """
    Get historical health check data for a resource
    Query param hours: number of hours to look back (default 24, max 168 = 7 days)
    """
    if hours > 168:
        hours = 168  # Cap at 7 days

    time_ago = datetime.utcnow() - timedelta(hours=hours)

    logs = db.query(HealthCheckLog).filter(
        HealthCheckLog.resource_name == resource_name,
        HealthCheckLog.check_timestamp >= time_ago
    ).order_by(HealthCheckLog.check_timestamp.asc()).all()

    if not logs:
        raise HTTPException(status_code=404, detail=f"No history found for '{resource_name}'")

    # Aggregate data by hour for visualization
    hourly_data = {}
    for log in logs:
        hour_key = log.check_timestamp.replace(minute=0, second=0, microsecond=0)
        if hour_key not in hourly_data:
            hourly_data[hour_key] = {
                "timestamp": hour_key.isoformat(),
                "checks": 0,
                "healthy": 0,
                "partial": 0,
                "down": 0,
                "avg_response_time_ms": []
            }

        hourly_data[hour_key]["checks"] += 1
        if log.health_status == HealthStatus.HEALTHY.value:
            hourly_data[hour_key]["healthy"] += 1
        elif log.health_status == HealthStatus.PARTIAL.value:
            hourly_data[hour_key]["partial"] += 1
        else:
            hourly_data[hour_key]["down"] += 1

        if log.response_time_ms:
            hourly_data[hour_key]["avg_response_time_ms"].append(log.response_time_ms)

    # Calculate averages
    for hour_data in hourly_data.values():
        if hour_data["avg_response_time_ms"]:
            hour_data["avg_response_time_ms"] = round(
                sum(hour_data["avg_response_time_ms"]) / len(hour_data["avg_response_time_ms"]), 2
            )
        else:
            hour_data["avg_response_time_ms"] = 0

    return {
        "resource_name": resource_name,
        "period_hours": hours,
        "total_checks": len(logs),
        "hourly_data": list(hourly_data.values())
    }


@router.get("/health/alerts")
async def get_health_alerts(db: Session = Depends(get_db)):
    """Get all current health alerts and resources needing attention"""
    monitor = HealthMonitorService(db)

    # Get resources that are down or need restart
    down_resources = db.query(ResourceHealth).filter(
        ResourceHealth.health_status == HealthStatus.DOWN.value
    ).all()

    needs_restart = monitor.get_resources_needing_restart()

    partial_resources = db.query(ResourceHealth).filter(
        ResourceHealth.health_status == HealthStatus.PARTIAL.value
    ).all()

    alerts = []

    # Critical: Down resources
    for resource in down_resources:
        down_duration = (datetime.utcnow() - resource.last_failure_at).total_seconds() / 60 if resource.last_failure_at else 0
        alerts.append({
            "severity": "critical",
            "resource": resource.resource_name,
            "resource_type": resource.resource_type.value,
            "message": f"Resource is DOWN for {down_duration:.1f} minutes",
            "error": resource.error_message,
            "can_restart": resource.restart_enabled,
            "timestamp": resource.last_check_at.isoformat() if resource.last_check_at else None
        })

    # Warning: Resources needing restart
    for resource in needs_restart:
        alerts.append({
            "severity": "warning",
            "resource": resource.resource_name,
            "resource_type": resource.resource_type.value,
            "message": f"Resource has been down >5 minutes and needs restart",
            "error": resource.error_message,
            "can_restart": True,
            "restart_count": resource.restart_count,
            "timestamp": resource.last_check_at.isoformat() if resource.last_check_at else None
        })

    # Info: Partial resources
    for resource in partial_resources:
        alerts.append({
            "severity": "info",
            "resource": resource.resource_name,
            "resource_type": resource.resource_type.value,
            "message": f"Resource is partially operational",
            "error": resource.error_message,
            "can_restart": resource.restart_enabled,
            "timestamp": resource.last_check_at.isoformat() if resource.last_check_at else None
        })

    return {
        "total_alerts": len(alerts),
        "critical": len([a for a in alerts if a["severity"] == "critical"]),
        "warning": len([a for a in alerts if a["severity"] == "warning"]),
        "info": len([a for a in alerts if a["severity"] == "info"]),
        "alerts": alerts
    }


@router.get("/health/summary")
async def get_health_summary(db: Session = Depends(get_db)):
    """
    Get a quick summary of system health
    Useful for status pages and quick checks
    """
    all_resources = db.query(ResourceHealth).all()

    if not all_resources:
        return {
            "status": "unknown",
            "message": "No health data available yet",
            "timestamp": datetime.utcnow().isoformat()
        }

    total = len(all_resources)
    healthy = sum(1 for r in all_resources if r.health_status == HealthStatus.HEALTHY.value)
    partial = sum(1 for r in all_resources if r.health_status == HealthStatus.PARTIAL.value)
    down = sum(1 for r in all_resources if r.health_status == HealthStatus.DOWN.value)

    # Determine overall status
    if down > 0:
        status = "degraded"
        status_color = "red"
    elif partial > 0:
        status = "partial"
        status_color = "yellow"
    else:
        status = "healthy"
        status_color = "green"

    return {
        "status": status,
        "status_color": status_color,
        "resources": {
            "total": total,
            "healthy": healthy,
            "partial": partial,
            "down": down
        },
        "health_score": round((healthy / total * 100) if total > 0 else 0, 1),
        "last_check": max((r.last_check_at for r in all_resources if r.last_check_at), default=None).isoformat() if all_resources else None,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.delete("/health/logs/cleanup")
async def cleanup_old_logs(
    days_to_keep: int = 7,
    db: Session = Depends(get_db),
    # current_user = Depends(get_current_admin_user)  # Uncomment when auth is ready
):
    """
    Delete health check logs older than specified days
    Default: keeps 7 days of logs
    """
    if days_to_keep < 1:
        raise HTTPException(status_code=400, detail="days_to_keep must be at least 1")

    cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

    deleted_count = db.query(HealthCheckLog).filter(
        HealthCheckLog.check_timestamp < cutoff_date
    ).delete()

    db.commit()

    return {
        "message": f"Cleaned up health check logs older than {days_to_keep} days",
        "deleted_count": deleted_count,
        "timestamp": datetime.utcnow().isoformat()
    }
