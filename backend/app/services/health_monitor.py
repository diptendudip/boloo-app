"""
Health Monitoring Service
Performs comprehensive health checks on all system resources
"""

import asyncio
import time
import httpx
import redis
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config import settings
from app.models.resource_health import (
    ResourceHealth,
    HealthCheckLog,
    ResourceType,
    ResourceCategory,
    HealthStatus
)
from app.services.app_insights import get_app_insights_service

logger = logging.getLogger(__name__)


class HealthMonitorService:
    """Service to monitor health of all system resources"""

    def __init__(self, db: Session):
        self.db = db
        self.timeout = 10  # seconds
        self.app_insights = get_app_insights_service()

    async def check_database(self) -> Dict:
        """Check PostgreSQL database connection and functionality"""
        start_time = time.time()
        resource_name = "PostgreSQL Database"

        try:
            # Basic connectivity check
            self.db.execute(text("SELECT 1"))

            # Check if we can query data
            result = self.db.execute(text("SELECT COUNT(*) FROM information_schema.tables"))
            table_count = result.scalar()

            response_time_ms = (time.time() - start_time) * 1000

            return {
                "resource_name": resource_name,
                "health_status": HealthStatus.HEALTHY.value,  # 2 - can connect and query data
                "response_time_ms": response_time_ms,
                "status_message": f"Database operational with {table_count} tables",
                "error_message": None
            }

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Database check failed: {e}")
            return {
                "resource_name": resource_name,
                "health_status": HealthStatus.DOWN.value,  # 0 - not operational
                "response_time_ms": response_time_ms,
                "status_message": None,
                "error_message": str(e)
            }

    async def check_redis(self) -> Dict:
        """Check Redis cache connection and functionality"""
        start_time = time.time()
        resource_name = "Redis Cache"

        try:
            r = redis.from_url(settings.REDIS_URL, socket_connect_timeout=self.timeout)

            # Basic connectivity check
            r.ping()

            # Check if we can set and get data
            test_key = "health_check_test"
            r.set(test_key, "test_value", ex=10)
            value = r.get(test_key)

            response_time_ms = (time.time() - start_time) * 1000

            if value:
                return {
                    "resource_name": resource_name,
                    "health_status": HealthStatus.HEALTHY.value,  # 2 - can connect and read/write
                    "response_time_ms": response_time_ms,
                    "status_message": "Redis operational, read/write successful",
                    "error_message": None
                }
            else:
                return {
                    "resource_name": resource_name,
                    "health_status": HealthStatus.PARTIAL.value,  # 1 - connected but limited
                    "response_time_ms": response_time_ms,
                    "status_message": "Redis connected but data operation failed",
                    "error_message": "Could not retrieve test value"
                }

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Redis check failed: {e}")
            return {
                "resource_name": resource_name,
                "health_status": HealthStatus.DOWN.value,  # 0 - not operational
                "response_time_ms": response_time_ms,
                "status_message": None,
                "error_message": str(e)
            }

    async def check_minio(self) -> Dict:
        """Check MinIO/S3 storage connection and functionality"""
        start_time = time.time()
        resource_name = "MinIO Storage"

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

            response_time_ms = (time.time() - start_time) * 1000

            if exists:
                # Try to list objects to verify read access
                try:
                    list(client.list_objects(settings.MINIO_BUCKET, max_keys=1))
                    return {
                        "resource_name": resource_name,
                        "health_status": HealthStatus.HEALTHY.value,  # 2 - can connect and access data
                        "response_time_ms": response_time_ms,
                        "status_message": f"Bucket '{settings.MINIO_BUCKET}' accessible and readable",
                        "error_message": None
                    }
                except Exception as list_error:
                    return {
                        "resource_name": resource_name,
                        "health_status": HealthStatus.PARTIAL.value,  # 1 - bucket exists but can't read
                        "response_time_ms": response_time_ms,
                        "status_message": f"Bucket '{settings.MINIO_BUCKET}' exists but limited access",
                        "error_message": str(list_error)
                    }
            else:
                return {
                    "resource_name": resource_name,
                    "health_status": HealthStatus.PARTIAL.value,  # 1 - connected but bucket missing
                    "response_time_ms": response_time_ms,
                    "status_message": f"Connected but bucket '{settings.MINIO_BUCKET}' not found",
                    "error_message": "Bucket does not exist"
                }

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"MinIO check failed: {e}")
            return {
                "resource_name": resource_name,
                "health_status": HealthStatus.DOWN.value,  # 0 - not operational
                "response_time_ms": response_time_ms,
                "status_message": None,
                "error_message": str(e)
            }

    async def check_api_endpoint(self, endpoint_path: str, endpoint_name: str) -> Dict:
        """Check if an API endpoint is responding"""
        start_time = time.time()
        resource_name = f"API: {endpoint_name}"

        try:
            url = f"http://localhost:8000{endpoint_path}"
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)

            response_time_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                # Try to parse JSON to verify data is available
                try:
                    data = response.json()
                    return {
                        "resource_name": resource_name,
                        "health_status": HealthStatus.HEALTHY.value,  # 2 - responds and returns data
                        "response_time_ms": response_time_ms,
                        "status_message": f"Endpoint responding with data (HTTP {response.status_code})",
                        "error_message": None
                    }
                except Exception:
                    return {
                        "resource_name": resource_name,
                        "health_status": HealthStatus.PARTIAL.value,  # 1 - responds but no valid data
                        "response_time_ms": response_time_ms,
                        "status_message": f"Endpoint responding but invalid data (HTTP {response.status_code})",
                        "error_message": "Could not parse response"
                    }
            else:
                return {
                    "resource_name": resource_name,
                    "health_status": HealthStatus.PARTIAL.value,  # 1 - responds but with error
                    "response_time_ms": response_time_ms,
                    "status_message": f"Endpoint responding with HTTP {response.status_code}",
                    "error_message": f"Non-200 status code: {response.status_code}"
                }

        except httpx.TimeoutException:
            response_time_ms = (time.time() - start_time) * 1000
            return {
                "resource_name": resource_name,
                "health_status": HealthStatus.DOWN.value,  # 0 - timeout
                "response_time_ms": response_time_ms,
                "status_message": None,
                "error_message": "Request timeout"
            }
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"API endpoint check failed for {endpoint_path}: {e}")
            return {
                "resource_name": resource_name,
                "health_status": HealthStatus.DOWN.value,  # 0 - not operational
                "response_time_ms": response_time_ms,
                "status_message": None,
                "error_message": str(e)
            }

    async def check_azure_speech(self) -> Dict:
        """Check Azure Speech Services availability"""
        start_time = time.time()
        resource_name = "Azure Speech API"

        if not settings.AZURE_SPEECH_KEY or not settings.AZURE_SPEECH_REGION:
            return {
                "resource_name": resource_name,
                "health_status": HealthStatus.DOWN.value,  # 0 - not configured
                "response_time_ms": 0,
                "status_message": None,
                "error_message": "Azure Speech API not configured (missing credentials)"
            }

        try:
            # Make a test request to Azure Speech token endpoint
            url = f"https://{settings.AZURE_SPEECH_REGION}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
            headers = {"Ocp-Apim-Subscription-Key": settings.AZURE_SPEECH_KEY}

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers)

            response_time_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                return {
                    "resource_name": resource_name,
                    "health_status": HealthStatus.HEALTHY.value,  # 2 - can authenticate and get token
                    "response_time_ms": response_time_ms,
                    "status_message": "Azure Speech API operational, token obtained",
                    "error_message": None
                }
            elif response.status_code == 401:
                return {
                    "resource_name": resource_name,
                    "health_status": HealthStatus.DOWN.value,  # 0 - authentication failed
                    "response_time_ms": response_time_ms,
                    "status_message": None,
                    "error_message": "Authentication failed (invalid credentials)"
                }
            else:
                return {
                    "resource_name": resource_name,
                    "health_status": HealthStatus.PARTIAL.value,  # 1 - API reachable but error
                    "response_time_ms": response_time_ms,
                    "status_message": f"API reachable but returned HTTP {response.status_code}",
                    "error_message": f"Unexpected status code: {response.status_code}"
                }

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Azure Speech check failed: {e}")
            return {
                "resource_name": resource_name,
                "health_status": HealthStatus.DOWN.value,  # 0 - not reachable
                "response_time_ms": response_time_ms,
                "status_message": None,
                "error_message": str(e)
            }

    async def check_azure_openai(self) -> Dict:
        """Check Azure OpenAI API availability"""
        start_time = time.time()
        resource_name = "Azure OpenAI API"

        if not settings.AZURE_OPENAI_ENDPOINT or not settings.AZURE_OPENAI_API_KEY:
            return {
                "resource_name": resource_name,
                "health_status": HealthStatus.DOWN.value,  # 0 - not configured
                "response_time_ms": 0,
                "status_message": None,
                "error_message": "Azure OpenAI not configured (missing credentials)"
            }

        try:
            # Make a lightweight test request to chat completions endpoint
            url = f"{settings.AZURE_OPENAI_ENDPOINT}/openai/deployments/{settings.AZURE_OPENAI_DEPLOYMENT_NAME}/chat/completions?api-version={settings.AZURE_OPENAI_API_VERSION}"
            headers = {
                "api-key": settings.AZURE_OPENAI_API_KEY,
                "Content-Type": "application/json"
            }
            # Minimal test payload
            data = {
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 5,
                "temperature": 0
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, json=data)

            response_time_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                return {
                    "resource_name": resource_name,
                    "health_status": HealthStatus.HEALTHY.value,  # 2 - can make API calls
                    "response_time_ms": response_time_ms,
                    "status_message": f"Azure OpenAI operational (deployment: {settings.AZURE_OPENAI_DEPLOYMENT_NAME})",
                    "error_message": None
                }
            elif response.status_code == 401:
                return {
                    "resource_name": resource_name,
                    "health_status": HealthStatus.DOWN.value,  # 0 - authentication failed
                    "response_time_ms": response_time_ms,
                    "status_message": None,
                    "error_message": "Authentication failed (invalid API key)"
                }
            elif response.status_code == 404:
                return {
                    "resource_name": resource_name,
                    "health_status": HealthStatus.DOWN.value,  # 0 - deployment not found
                    "response_time_ms": response_time_ms,
                    "status_message": None,
                    "error_message": f"Deployment '{settings.AZURE_OPENAI_DEPLOYMENT_NAME}' not found"
                }
            else:
                return {
                    "resource_name": resource_name,
                    "health_status": HealthStatus.PARTIAL.value,  # 1 - API reachable but error
                    "response_time_ms": response_time_ms,
                    "status_message": f"API reachable but returned HTTP {response.status_code}",
                    "error_message": f"Unexpected status code: {response.status_code}"
                }

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Azure OpenAI check failed: {e}")
            return {
                "resource_name": resource_name,
                "health_status": HealthStatus.DOWN.value,  # 0 - not reachable
                "response_time_ms": response_time_ms,
                "status_message": None,
                "error_message": str(e)
            }

    async def check_claude_api(self) -> Dict:
        """Check Claude API (Anthropic) availability"""
        start_time = time.time()
        resource_name = "Claude AI API"

        if not settings.ANTHROPIC_API_KEY:
            return {
                "resource_name": resource_name,
                "health_status": HealthStatus.DOWN.value,  # 0 - not configured
                "response_time_ms": 0,
                "status_message": None,
                "error_message": "Claude API not configured (missing API key)"
            }

        try:
            # Make a lightweight test request
            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "x-api-key": settings.ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            # Minimal test payload
            data = {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "test"}]
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, json=data)

            response_time_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                return {
                    "resource_name": resource_name,
                    "health_status": HealthStatus.HEALTHY.value,  # 2 - can make API calls
                    "response_time_ms": response_time_ms,
                    "status_message": "Claude API operational, test request successful",
                    "error_message": None
                }
            elif response.status_code == 401:
                return {
                    "resource_name": resource_name,
                    "health_status": HealthStatus.DOWN.value,  # 0 - authentication failed
                    "response_time_ms": response_time_ms,
                    "status_message": None,
                    "error_message": "Authentication failed (invalid API key)"
                }
            else:
                return {
                    "resource_name": resource_name,
                    "health_status": HealthStatus.PARTIAL.value,  # 1 - API reachable but error
                    "response_time_ms": response_time_ms,
                    "status_message": f"API reachable but returned HTTP {response.status_code}",
                    "error_message": f"Unexpected status code: {response.status_code}"
                }

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Claude API check failed: {e}")
            return {
                "resource_name": resource_name,
                "health_status": HealthStatus.DOWN.value,  # 0 - not reachable
                "response_time_ms": response_time_ms,
                "status_message": None,
                "error_message": str(e)
            }

    async def check_smtp(self) -> Dict:
        """Check SMTP email server availability"""
        start_time = time.time()
        resource_name = "SMTP Email Service"

        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            return {
                "resource_name": resource_name,
                "health_status": HealthStatus.DOWN.value,  # 0 - not configured
                "response_time_ms": 0,
                "status_message": None,
                "error_message": "SMTP not configured (missing credentials)"
            }

        try:
            import aiosmtplib

            # Test connection to SMTP server
            async with aiosmtplib.SMTP(
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                timeout=self.timeout
            ) as smtp:
                await smtp.connect()
                await smtp.ehlo()

                response_time_ms = (time.time() - start_time) * 1000

                # Try to authenticate
                try:
                    await smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    return {
                        "resource_name": resource_name,
                        "health_status": HealthStatus.HEALTHY.value,  # 2 - can connect and authenticate
                        "response_time_ms": response_time_ms,
                        "status_message": "SMTP server operational, authentication successful",
                        "error_message": None
                    }
                except Exception as auth_error:
                    return {
                        "resource_name": resource_name,
                        "health_status": HealthStatus.PARTIAL.value,  # 1 - connected but can't auth
                        "response_time_ms": response_time_ms,
                        "status_message": "SMTP server connected but authentication failed",
                        "error_message": str(auth_error)
                    }

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"SMTP check failed: {e}")
            return {
                "resource_name": resource_name,
                "health_status": HealthStatus.DOWN.value,  # 0 - not reachable
                "response_time_ms": response_time_ms,
                "status_message": None,
                "error_message": str(e)
            }

    async def check_network(self) -> Dict:
        """Check general network connectivity"""
        start_time = time.time()
        resource_name = "Network Connectivity"

        try:
            # Test connectivity to a reliable external service
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get("https://www.google.com", follow_redirects=True)

            response_time_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                return {
                    "resource_name": resource_name,
                    "health_status": HealthStatus.HEALTHY.value,  # 2 - network operational
                    "response_time_ms": response_time_ms,
                    "status_message": "Network connectivity operational",
                    "error_message": None
                }
            else:
                return {
                    "resource_name": resource_name,
                    "health_status": HealthStatus.PARTIAL.value,  # 1 - limited connectivity
                    "response_time_ms": response_time_ms,
                    "status_message": "Network partially operational",
                    "error_message": f"Unexpected status code: {response.status_code}"
                }

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Network check failed: {e}")
            return {
                "resource_name": resource_name,
                "health_status": HealthStatus.DOWN.value,  # 0 - no connectivity
                "response_time_ms": response_time_ms,
                "status_message": None,
                "error_message": str(e)
            }

    async def perform_all_checks(self) -> List[Dict]:
        """Perform all health checks concurrently"""
        logger.info("Starting comprehensive health checks...")

        # Define all checks with their categorization
        checks = [
            # Internal resources
            ("database", self.check_database(), ResourceType.INTERNAL, ResourceCategory.DATABASE),
            ("redis", self.check_redis(), ResourceType.INTERNAL, ResourceCategory.CACHE),
            ("minio", self.check_minio(), ResourceType.INTERNAL, ResourceCategory.STORAGE),
            ("api_health", self.check_api_endpoint("/health", "Health Check"), ResourceType.INTERNAL, ResourceCategory.API),
            ("api_entities", self.check_api_endpoint("/v1/entities", "Entities"), ResourceType.INTERNAL, ResourceCategory.API),
            ("api_taxonomies", self.check_api_endpoint("/v1/taxonomies", "Taxonomies"), ResourceType.INTERNAL, ResourceCategory.API),

            # External resources
            ("azure_openai", self.check_azure_openai(), ResourceType.EXTERNAL, ResourceCategory.AI_SERVICE),
            ("azure_speech", self.check_azure_speech(), ResourceType.EXTERNAL, ResourceCategory.SPEECH_SERVICE),
            ("claude_api", self.check_claude_api(), ResourceType.EXTERNAL, ResourceCategory.AI_SERVICE),
            ("smtp", self.check_smtp(), ResourceType.EXTERNAL, ResourceCategory.EMAIL_SERVICE),
            ("network", self.check_network(), ResourceType.EXTERNAL, ResourceCategory.NETWORK),
        ]

        # Run all checks concurrently
        results = []
        for check_name, check_coroutine, resource_type, resource_category in checks:
            try:
                result = await check_coroutine
                result["resource_type"] = resource_type
                result["resource_category"] = resource_category
                results.append(result)
            except Exception as e:
                logger.error(f"Check {check_name} failed with exception: {e}")
                results.append({
                    "resource_name": check_name,
                    "resource_type": resource_type,
                    "resource_category": resource_category,
                    "health_status": HealthStatus.DOWN.value,
                    "response_time_ms": 0,
                    "status_message": None,
                    "error_message": str(e)
                })

        logger.info(f"Completed {len(results)} health checks")
        return results

    def update_resource_health(self, check_result: Dict) -> ResourceHealth:
        """Update or create ResourceHealth record in database"""
        resource = self.db.query(ResourceHealth).filter(
            ResourceHealth.resource_name == check_result["resource_name"]
        ).first()

        now = datetime.utcnow()
        is_success = check_result["health_status"] == HealthStatus.HEALTHY.value

        if not resource:
            # Create new resource record
            resource = ResourceHealth(
                resource_name=check_result["resource_name"],
                resource_type=check_result["resource_type"],
                resource_category=check_result["resource_category"],
                health_status=check_result["health_status"],
                response_time_ms=check_result["response_time_ms"],
                last_check_at=now,
                last_success_at=now if is_success else None,
                last_failure_at=now if not is_success else None,
                consecutive_failures=0 if is_success else 1,
                total_failures=0 if is_success else 1,
                total_checks=1,
                status_message=check_result.get("status_message"),
                error_message=check_result.get("error_message")
            )
            self.db.add(resource)
        else:
            # Update existing resource
            resource.health_status = check_result["health_status"]
            resource.response_time_ms = check_result["response_time_ms"]
            resource.last_check_at = now
            resource.total_checks += 1

            if is_success:
                resource.last_success_at = now
                resource.consecutive_failures = 0
            else:
                resource.last_failure_at = now
                resource.consecutive_failures += 1
                resource.total_failures += 1

            resource.status_message = check_result.get("status_message")
            resource.error_message = check_result.get("error_message")

        # Create log entry
        log_entry = HealthCheckLog(
            resource_name=check_result["resource_name"],
            check_timestamp=now,
            health_status=check_result["health_status"],
            response_time_ms=check_result["response_time_ms"],
            status_message=check_result.get("status_message"),
            error_message=check_result.get("error_message")
        )
        self.db.add(log_entry)

        self.db.commit()
        self.db.refresh(resource)

        # Track in Application Insights
        self._track_health_check_in_insights(check_result)

        return resource

    def _track_health_check_in_insights(self, check_result: Dict):
        """Track health check results in Application Insights"""
        try:
            # Map health status to status string
            status_map = {
                HealthStatus.HEALTHY.value: "healthy",
                HealthStatus.PARTIAL.value: "degraded",
                HealthStatus.DOWN.value: "down"
            }
            status = status_map.get(check_result["health_status"], "unknown")

            # Track health check
            self.app_insights.track_health_check(
                resource_name=check_result["resource_name"],
                status=status,
                response_time_ms=check_result["response_time_ms"],
                message=check_result.get("status_message"),
                error=check_result.get("error_message")
            )

            # Track dependency failure if not healthy
            if check_result["health_status"] != HealthStatus.HEALTHY.value:
                self.app_insights.track_dependency_failure(
                    dependency_name=check_result["resource_name"],
                    error_message=check_result.get("error_message", "Health check failed"),
                    duration_ms=check_result["response_time_ms"]
                )

        except Exception as e:
            logger.error(f"Failed to track health check in Application Insights: {e}")

    async def run_health_checks_and_save(self) -> List[ResourceHealth]:
        """Run all health checks and save results to database"""
        check_results = await self.perform_all_checks()

        resources = []
        for result in check_results:
            resource = self.update_resource_health(result)
            resources.append(resource)

        return resources

    def get_all_resources(self) -> List[ResourceHealth]:
        """Get all resources from database"""
        return self.db.query(ResourceHealth).all()

    def get_internal_resources(self) -> List[ResourceHealth]:
        """Get only internal resources"""
        return self.db.query(ResourceHealth).filter(
            ResourceHealth.resource_type == ResourceType.INTERNAL
        ).all()

    def get_external_resources(self) -> List[ResourceHealth]:
        """Get only external resources"""
        return self.db.query(ResourceHealth).filter(
            ResourceHealth.resource_type == ResourceType.EXTERNAL
        ).all()

    def get_unhealthy_resources(self) -> List[ResourceHealth]:
        """Get resources that are not fully healthy"""
        return self.db.query(ResourceHealth).filter(
            ResourceHealth.health_status < HealthStatus.HEALTHY.value
        ).all()

    def get_resources_needing_restart(self) -> List[ResourceHealth]:
        """Get internal resources that need to be restarted"""
        five_mins_ago = datetime.utcnow() - timedelta(minutes=5)

        return self.db.query(ResourceHealth).filter(
            ResourceHealth.resource_type == ResourceType.INTERNAL,
            ResourceHealth.restart_enabled == True,
            ResourceHealth.health_status == HealthStatus.DOWN.value,
            ResourceHealth.last_failure_at <= five_mins_ago
        ).all()
