"""
Application Insights Integration Service
Provides monitoring and telemetry for health checks and dependency tracking
"""

import logging
from typing import Dict, Optional, Any
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class SeverityLevel(int, Enum):
    """Application Insights severity levels"""
    VERBOSE = 0
    INFORMATION = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4


class ApplicationInsightsService:
    """
    Service for integrating with Azure Application Insights
    Provides telemetry tracking for health checks and dependencies
    """

    def __init__(self, instrumentation_key: Optional[str] = None):
        """
        Initialize Application Insights service

        Args:
            instrumentation_key: Azure Application Insights instrumentation key
        """
        self.instrumentation_key = instrumentation_key
        self.enabled = False
        self.client = None

        if instrumentation_key:
            try:
                from opencensus.ext.azure.log_exporter import AzureLogHandler
                from opencensus.ext.azure.trace_exporter import AzureExporter
                from opencensus.trace.samplers import ProbabilitySampler
                from opencensus.trace import config_integration
                from opencensus.trace.tracer import Tracer

                # Configure integrations
                config_integration.trace_integrations(['logging', 'requests'])

                # Set up logging handler
                self.log_handler = AzureLogHandler(
                    connection_string=f'InstrumentationKey={instrumentation_key}'
                )

                # Set up trace exporter
                self.trace_exporter = AzureExporter(
                    connection_string=f'InstrumentationKey={instrumentation_key}'
                )

                # Create tracer
                self.tracer = Tracer(
                    exporter=self.trace_exporter,
                    sampler=ProbabilitySampler(1.0)  # Sample 100% of requests
                )

                self.enabled = True
                logger.info("Application Insights integration enabled")

            except ImportError:
                logger.warning(
                    "Application Insights dependencies not installed. "
                    "Install with: pip install opencensus-ext-azure"
                )
            except Exception as e:
                logger.error(f"Failed to initialize Application Insights: {e}")
        else:
            logger.info("Application Insights instrumentation key not provided, telemetry disabled")

    def track_health_check(
        self,
        resource_name: str,
        status: str,
        response_time_ms: float,
        message: Optional[str] = None,
        error: Optional[str] = None
    ):
        """
        Track a health check result

        Args:
            resource_name: Name of the resource being checked
            status: Health status (healthy, degraded, down)
            response_time_ms: Response time in milliseconds
            message: Optional status message
            error: Optional error message
        """
        if not self.enabled:
            return

        try:
            severity = self._get_severity_from_status(status)

            # Build custom properties
            properties = {
                'resource_name': resource_name,
                'health_status': status,
                'response_time_ms': response_time_ms,
                'check_timestamp': datetime.utcnow().isoformat()
            }

            if message:
                properties['message'] = message
            if error:
                properties['error'] = error

            # Log the health check
            log_message = f"Health check: {resource_name} - {status}"
            if error:
                log_message += f" - {error}"

            logger.log(
                self._severity_to_log_level(severity),
                log_message,
                extra={'custom_dimensions': properties}
            )

            # Track as a custom metric
            self._track_metric(
                name=f"HealthCheck.{resource_name}.ResponseTime",
                value=response_time_ms,
                properties=properties
            )

            # Track availability
            self._track_availability(
                name=resource_name,
                success=(status == "healthy"),
                duration_ms=response_time_ms,
                message=message or error
            )

        except Exception as e:
            logger.error(f"Failed to track health check in Application Insights: {e}")

    def track_dependency_failure(
        self,
        dependency_name: str,
        error_message: str,
        duration_ms: float
    ):
        """
        Track a dependency failure

        Args:
            dependency_name: Name of the failed dependency
            error_message: Error message
            duration_ms: Duration of the failed request
        """
        if not self.enabled:
            return

        try:
            properties = {
                'dependency_name': dependency_name,
                'error': error_message,
                'duration_ms': duration_ms,
                'timestamp': datetime.utcnow().isoformat()
            }

            logger.error(
                f"Dependency failure: {dependency_name} - {error_message}",
                extra={'custom_dimensions': properties}
            )

            # Track as dependency telemetry
            self._track_dependency(
                name=dependency_name,
                duration_ms=duration_ms,
                success=False,
                result_code="Failed",
                properties=properties
            )

        except Exception as e:
            logger.error(f"Failed to track dependency failure: {e}")

    def track_metric(
        self,
        name: str,
        value: float,
        properties: Optional[Dict[str, Any]] = None
    ):
        """
        Track a custom metric

        Args:
            name: Metric name
            value: Metric value
            properties: Optional custom properties
        """
        if not self.enabled:
            return

        try:
            self._track_metric(name, value, properties)
        except Exception as e:
            logger.error(f"Failed to track metric: {e}")

    def track_event(
        self,
        name: str,
        properties: Optional[Dict[str, Any]] = None
    ):
        """
        Track a custom event

        Args:
            name: Event name
            properties: Optional event properties
        """
        if not self.enabled:
            return

        try:
            logger.info(
                f"Event: {name}",
                extra={'custom_dimensions': properties or {}}
            )
        except Exception as e:
            logger.error(f"Failed to track event: {e}")

    def _track_metric(
        self,
        name: str,
        value: float,
        properties: Optional[Dict[str, Any]] = None
    ):
        """Internal method to track metrics"""
        # In a real implementation, this would use the Application Insights SDK
        # For now, we log the metric
        logger.info(
            f"Metric: {name} = {value}",
            extra={'custom_dimensions': properties or {}}
        )

    def _track_dependency(
        self,
        name: str,
        duration_ms: float,
        success: bool,
        result_code: str,
        properties: Optional[Dict[str, Any]] = None
    ):
        """Internal method to track dependencies"""
        # In a real implementation, this would use the Application Insights SDK
        logger.info(
            f"Dependency: {name} - Success: {success}, Duration: {duration_ms}ms",
            extra={'custom_dimensions': properties or {}}
        )

    def _track_availability(
        self,
        name: str,
        success: bool,
        duration_ms: float,
        message: Optional[str] = None
    ):
        """Internal method to track availability"""
        # In a real implementation, this would use the Application Insights SDK
        logger.info(
            f"Availability: {name} - Success: {success}, Duration: {duration_ms}ms",
            extra={'custom_dimensions': {'message': message}}
        )

    def _get_severity_from_status(self, status: str) -> SeverityLevel:
        """Map health status to severity level"""
        status_map = {
            "healthy": SeverityLevel.INFORMATION,
            "degraded": SeverityLevel.WARNING,
            "down": SeverityLevel.ERROR
        }
        return status_map.get(status.lower(), SeverityLevel.WARNING)

    def _severity_to_log_level(self, severity: SeverityLevel) -> int:
        """Convert Application Insights severity to Python log level"""
        level_map = {
            SeverityLevel.VERBOSE: logging.DEBUG,
            SeverityLevel.INFORMATION: logging.INFO,
            SeverityLevel.WARNING: logging.WARNING,
            SeverityLevel.ERROR: logging.ERROR,
            SeverityLevel.CRITICAL: logging.CRITICAL
        }
        return level_map.get(severity, logging.INFO)


# Global Application Insights service instance
# Initialize with instrumentation key from environment
app_insights = None

def get_app_insights_service() -> ApplicationInsightsService:
    """Get or create Application Insights service instance"""
    global app_insights

    if app_insights is None:
        # Try to get instrumentation key from environment
        import os
        instrumentation_key = os.getenv("APPLICATIONINSIGHTS_INSTRUMENTATION_KEY")
        app_insights = ApplicationInsightsService(instrumentation_key)

    return app_insights
