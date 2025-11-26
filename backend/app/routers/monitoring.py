"""
Monitoring router - System health checks
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import httpx
import redis
import logging
from datetime import datetime

from app.database import get_db
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


async def check_database(db: Session) -> dict:
    """Check PostgreSQL connection"""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "message": "Database connected"}
    except Exception as e:
        return {"status": "unhealthy", "message": str(e)}


async def check_redis() -> dict:
    """Check Redis connection"""
    try:
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        return {"status": "healthy", "message": "Redis connected"}
    except Exception as e:
        return {"status": "unhealthy", "message": str(e)}


async def check_minio() -> dict:
    """Check MinIO/S3 storage"""
    try:
        from minio import Minio
        client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL
        )
        # Check if bucket exists
        exists = client.bucket_exists(settings.MINIO_BUCKET)
        if exists:
            return {"status": "healthy", "message": f"Bucket '{settings.MINIO_BUCKET}' accessible"}
        else:
            return {"status": "warning", "message": f"Bucket '{settings.MINIO_BUCKET}' not found"}
    except Exception as e:
        return {"status": "unhealthy", "message": str(e)}


async def check_azure_speech() -> dict:
    """Check Azure Speech API"""
    if not settings.AZURE_SPEECH_KEY:
        return {"status": "not_configured", "message": "Azure Speech not configured"}

    try:
        # Just check if credentials exist for MVP
        return {"status": "configured", "message": "Azure Speech credentials present"}
    except Exception as e:
        return {"status": "unhealthy", "message": str(e)}


async def check_claude_api() -> dict:
    """Check Claude API"""
    if not settings.ANTHROPIC_API_KEY:
        return {"status": "not_configured", "message": "Claude API not configured"}

    return {"status": "configured", "message": "Claude API key present"}


async def check_smtp() -> dict:
    """Check SMTP server"""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        return {"status": "not_configured", "message": "SMTP not configured"}

    return {"status": "configured", "message": "SMTP credentials present"}


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Comprehensive health check for all services
    Returns status of all endpoints and infrastructure
    """
    try:
        # Check all services
        database = await check_database(db)
        redis_status = await check_redis()
        minio = await check_minio()
        azure = await check_azure_speech()
        claude = await check_claude_api()
        smtp = await check_smtp()

        # API endpoints to monitor
        endpoints = [
            {"path": "/health", "name": "Health Check"},
            {"path": "/v1/auth/otp/request", "name": "OTP Request"},
            {"path": "/v1/cases", "name": "Cases List"},
            {"path": "/v1/entities", "name": "Entities List"},
            {"path": "/v1/taxonomies", "name": "Taxonomies List"},
            {"path": "/v1/admin/stats", "name": "Admin Stats"},
        ]

        # Overall health status
        all_healthy = all([
            database["status"] == "healthy",
            redis_status["status"] == "healthy"
        ])

        return {
            "overall_status": "healthy" if all_healthy else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "infrastructure": {
                "database": database,
                "redis": redis_status,
                "storage": minio,
            },
            "external_services": {
                "azure_speech": azure,
                "claude_api": claude,
                "smtp": smtp,
            },
            "api_endpoints": endpoints,
            "version": "1.0.0"
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return {
            "overall_status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@router.get("/metrics")
async def get_metrics(db: Session = Depends(get_db)):
    """Get system metrics"""
    from app.models import Case, User

    try:
        # Basic metrics
        total_cases = db.query(Case).count()
        total_users = db.query(User).count()

        # Cases by status
        from sqlalchemy import func
        cases_by_status = db.query(
            Case.status,
            func.count(Case.id).label('count')
        ).group_by(Case.status).all()

        # Recent activity (last 24 hours)
        from datetime import timedelta
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_cases = db.query(Case).filter(Case.created_at >= yesterday).count()

        return {
            "total_cases": total_cases,
            "total_users": total_users,
            "recent_cases_24h": recent_cases,
            "cases_by_status": {status: count for status, count in cases_by_status},
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Metrics retrieval failed: {e}", exc_info=True)
        return {"error": str(e)}
