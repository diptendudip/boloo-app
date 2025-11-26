# Enhanced Health Check System

Comprehensive health monitoring for the Boloo backend API with dependency tracking and Azure Application Insights integration.

## Overview

The health check system provides multiple endpoints for monitoring service health, dependency availability, and system diagnostics.

## Endpoints

### 1. Basic Health Check
**Endpoint:** `GET /health`

**Purpose:** Simple backward-compatible health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-23T10:30:00.000Z",
  "version": "1.0.0",
  "environment": "production"
}
```

**Status Codes:**
- `200 OK` - Service is running

---

### 2. Liveness Probe
**Endpoint:** `GET /health/live`

**Purpose:** Kubernetes/container liveness probe - checks if the service process is alive

**Use Case:** Container orchestrators use this to determine if the container should be restarted

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-23T10:30:00.000Z",
  "version": "1.0.0",
  "environment": "production"
}
```

**Status Codes:**
- `200 OK` - Service process is alive

**Important:** This endpoint does NOT check dependencies. It only verifies the service process is running.

---

### 3. Readiness Probe
**Endpoint:** `GET /health/ready`

**Purpose:** Kubernetes/container readiness probe - checks if the service can accept traffic

**Use Case:** Container orchestrators use this to determine if traffic should be routed to the instance

**Response (Healthy):**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-23T10:30:00.000Z",
  "version": "1.0.0",
  "dependencies": [
    {
      "name": "PostgreSQL Database",
      "status": "healthy",
      "response_time_ms": 5.2,
      "message": "Database operational with 42 tables",
      "error": null
    },
    {
      "name": "Azure OpenAI API",
      "status": "healthy",
      "response_time_ms": 120.5,
      "message": "Azure OpenAI operational (deployment: gpt-4o-mini)",
      "error": null
    },
    {
      "name": "Azure Speech API",
      "status": "healthy",
      "response_time_ms": 95.0,
      "message": "Azure Speech API operational, token obtained",
      "error": null
    }
  ],
  "ready": true
}
```

**Response (Degraded):**
```json
{
  "status": "degraded",
  "timestamp": "2025-11-23T10:30:00.000Z",
  "version": "1.0.0",
  "dependencies": [
    {
      "name": "Redis Cache",
      "status": "degraded",
      "response_time_ms": 500.0,
      "message": "Redis connected but data operation failed",
      "error": "Could not retrieve test value"
    }
  ],
  "ready": true
}
```

**Response (Service Down - 503):**
```json
{
  "detail": {
    "status": "down",
    "timestamp": "2025-11-23T10:30:00.000Z",
    "version": "1.0.0",
    "dependencies": [
      {
        "name": "PostgreSQL Database",
        "status": "down",
        "response_time_ms": 0,
        "message": null,
        "error": "Connection refused"
      }
    ],
    "ready": false
  }
}
```

**Status Codes:**
- `200 OK` - Service is ready (all dependencies healthy or degraded)
- `503 Service Unavailable` - Service is not ready (one or more critical dependencies down)

---

### 4. Detailed Health Diagnostics
**Endpoint:** `GET /health/detailed`

**Purpose:** Comprehensive health diagnostics with metrics and configuration summary

**Use Case:** Admin dashboards, debugging, comprehensive monitoring

**Security:** Should be restricted to admin users in production (authentication commented out for now)

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-23T10:30:00.000Z",
  "version": "1.0.0",
  "environment": "production",
  "uptime_seconds": 3600.5,
  "dependencies": [
    {
      "name": "PostgreSQL Database",
      "status": "healthy",
      "response_time_ms": 5.2,
      "message": "Database operational with 42 tables",
      "error": null
    },
    {
      "name": "Azure OpenAI API",
      "status": "healthy",
      "response_time_ms": 120.5,
      "message": "Azure OpenAI operational (deployment: gpt-4o-mini)",
      "error": null
    }
  ],
  "metrics": {
    "total_dependencies": 10,
    "healthy_count": 9,
    "degraded_count": 1,
    "down_count": 0,
    "health_percentage": 90.0,
    "average_response_time_ms": 85.3,
    "critical_errors": []
  },
  "configuration": {
    "app_name": "Boloo",
    "environment": "production",
    "debug_mode": false,
    "database_configured": true,
    "redis_configured": true,
    "azure_openai_configured": true,
    "azure_speech_configured": true,
    "anthropic_configured": true,
    "smtp_configured": true,
    "minio_configured": true
  }
}
```

**Status Codes:**
- `200 OK` - Always returns 200 with detailed diagnostics

---

## Dependencies Monitored

### Internal Resources
1. **PostgreSQL Database**
   - Connection check
   - Query execution test
   - Table count verification

2. **Redis Cache**
   - Connection check
   - Read/write operations test

3. **MinIO Storage**
   - Connection check
   - Bucket existence verification
   - Object listing test

4. **API Endpoints**
   - `/health` - Health check endpoint
   - `/v1/entities` - Entities API
   - `/v1/taxonomies` - Taxonomies API

### External Resources
1. **Azure OpenAI API**
   - Authentication check
   - Deployment availability
   - Test chat completion request

2. **Azure Speech Services**
   - Token endpoint check
   - Authentication verification

3. **Claude AI API (Anthropic)**
   - API availability
   - Authentication check
   - Test message request

4. **SMTP Email Service**
   - Server connection
   - Authentication check

5. **Network Connectivity**
   - External connectivity test

---

## Health Status Levels

### Service Status
- **`healthy`** - Service is fully operational
- **`degraded`** - Service is operational but with warnings (partial dependencies)
- **`down`** - Service is not operational (critical dependencies down)

### Dependency Status
- **`healthy`** - Dependency is fully operational
- **`degraded`** - Dependency is partially operational (slow or limited)
- **`down`** - Dependency is not operational

---

## Application Insights Integration

The health check system automatically tracks telemetry in Azure Application Insights:

### Tracked Metrics
- **Health Check Results** - Status and response time for each dependency
- **Dependency Failures** - Failed dependency checks with error details
- **Availability** - Uptime tracking for each service
- **Custom Metrics** - Response times and health percentages

### Configuration
Set the `APPLICATIONINSIGHTS_INSTRUMENTATION_KEY` environment variable:

```bash
export APPLICATIONINSIGHTS_INSTRUMENTATION_KEY="your-instrumentation-key-here"
```

### Querying in Application Insights

**View health check metrics:**
```kusto
customMetrics
| where name startswith "HealthCheck."
| summarize avg(value) by name, bin(timestamp, 5m)
| render timechart
```

**View dependency failures:**
```kusto
traces
| where severityLevel >= 3  // Error or Critical
| where customDimensions.dependency_name != ""
| project timestamp, dependency_name=customDimensions.dependency_name, error=customDimensions.error
| order by timestamp desc
```

**Availability report:**
```kusto
traces
| where customDimensions.resource_name != ""
| extend status = customDimensions.health_status
| summarize
    total = count(),
    healthy = countif(status == "healthy"),
    degraded = countif(status == "degraded"),
    down = countif(status == "down")
    by bin(timestamp, 1h)
| extend health_percentage = (healthy * 100.0 / total)
| render timechart
```

---

## Kubernetes Deployment

### Liveness Probe Configuration
```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

### Readiness Probe Configuration
```yaml
readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  successThreshold: 1
  failureThreshold: 3
```

---

## Monitoring Recommendations

### Alerting Rules

1. **Critical Alert - Service Down**
   - Trigger: `/health/ready` returns 503 for > 2 minutes
   - Action: Page on-call engineer

2. **Warning Alert - Degraded Performance**
   - Trigger: Health percentage < 80% for > 5 minutes
   - Action: Notify team channel

3. **Info Alert - Dependency Slow**
   - Trigger: Average response time > 1000ms for > 10 minutes
   - Action: Log for investigation

### Dashboard Widgets

1. **Health Score**
   - Type: Single value
   - Metric: Current health percentage
   - Refresh: 30 seconds

2. **Dependency Status**
   - Type: Status grid
   - Metrics: Individual dependency health
   - Refresh: 1 minute

3. **Response Time Trends**
   - Type: Line chart
   - Metrics: Average response times by dependency
   - Time range: Last 24 hours

4. **Availability SLA**
   - Type: Single value
   - Metric: Uptime percentage (last 30 days)
   - Target: 99.9%

---

## Testing

Run the comprehensive test suite:

```bash
# Run all health check tests
pytest tests/test_health_endpoints.py -v

# Run specific test class
pytest tests/test_health_endpoints.py::TestReadinessProbe -v

# Run with coverage
pytest tests/test_health_endpoints.py --cov=app.routers.health --cov-report=html
```

---

## Common Issues

### Issue: Readiness probe returns 503
**Cause:** One or more critical dependencies are down

**Debugging:**
1. Check `/health/detailed` for specific failing dependencies
2. Review Application Insights for error details
3. Check dependency service logs
4. Verify network connectivity and credentials

### Issue: High response times
**Cause:** Dependencies are slow or network latency

**Debugging:**
1. Check `response_time_ms` in `/health/detailed`
2. Review Application Insights performance metrics
3. Check database query performance
4. Verify external API rate limits

### Issue: Application Insights not tracking
**Cause:** Missing or incorrect instrumentation key

**Debugging:**
1. Verify `APPLICATIONINSIGHTS_INSTRUMENTATION_KEY` environment variable
2. Check service logs for initialization errors
3. Ensure `opencensus-ext-azure` package is installed

---

## Migration from Legacy Health Check

The new system is backward compatible. The legacy `/health` endpoint still works.

**Migration Steps:**

1. Update monitoring tools to use `/health/ready` for readiness checks
2. Update Kubernetes probes to use `/health/live` and `/health/ready`
3. Configure Application Insights instrumentation key
4. Update dashboards to use detailed health metrics
5. Remove legacy health check monitoring (after validation)

---

## Future Enhancements

- [ ] Admin authentication for `/health/detailed` endpoint
- [ ] Configurable timeout values per dependency
- [ ] Dependency circuit breakers
- [ ] Health check result caching
- [ ] WebSocket real-time health streaming
- [ ] Custom dependency plugins
- [ ] Integration with PagerDuty/OpsGenie
- [ ] Synthetic transaction monitoring

---

## Support

For issues or questions:
- Create an issue in the GitHub repository
- Contact the DevOps team
- Check Application Insights for detailed diagnostics
