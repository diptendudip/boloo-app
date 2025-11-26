# Azure Monitoring Setup - Boloo Backend API

## Overview

This document details the monitoring and alerting configuration for the Boloo Backend API deployed on Azure App Service.

**Last Updated**: 2025-11-21
**Status**: Fully Configured ✅

---

## 1. Application Insights

### Configuration

- **Resource Name**: `boloo-backend-insights`
- **Location**: South India
- **Application Type**: Web
- **Retention**: 90 days
- **Instrumentation Key**: `33aad16e-9560-4cf8-8ced-b42fde933cf2`
- **Application ID**: `e695fd11-449b-42fb-b440-91ac421d883a`

### Connection String

```
InstrumentationKey=33aad16e-9560-4cf8-8ced-b42fde933cf2;IngestionEndpoint=https://southindia-0.in.applicationinsights.azure.com/;LiveEndpoint=https://southindia.livediagnostics.monitor.azure.com/;ApplicationId=e695fd11-449b-42fb-b440-91ac421d883a
```

### Portal Access

```bash
# Application Insights Dashboard
https://portal.azure.com/#@/resource/subscriptions/417b3ad6-5fc1-47a3-917d-21cf4e3eddfc/resourceGroups/boloo-production-rg/providers/microsoft.insights/components/boloo-backend-insights/overview
```

---

## 2. Logging Configuration

### Enabled Logs

- ✅ **Application Logging**: Filesystem (Level: Off - can be enabled)
- ✅ **Web Server Logging**: Filesystem (3 days retention, 100MB)
- ✅ **Detailed Error Messages**: Enabled
- ✅ **Failed Request Tracing**: Enabled

### Log Streaming

```bash
# Stream live logs
az webapp log tail --name boloo-backend-api --resource-group boloo-production-rg

# Download logs archive
az webapp log download \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --log-file boloo-logs.zip
```

### Log Locations

- **Docker Logs**: `LogFiles/2025_11_21_lw0sdlwk000F7X_default_docker.log`
- **Application Diagnostics**: `LogFiles/Application/diagnostics-*.txt`
- **Deployment Logs**: `deployments/*/log.log`
- **Kudu Traces**: `LogFiles/kudu/trace/*.xml`

---

## 3. Metric Alerts

### Alert 1: HTTP 5xx Errors

- **Name**: `boloo-http-5xx-errors`
- **Metric**: `Http5xx`
- **Condition**: Count > 10
- **Time Window**: 5 minutes
- **Evaluation Frequency**: 1 minute
- **Severity**: 2 (Warning)
- **Description**: Triggers when HTTP 5xx errors exceed 10 in 5 minutes

```bash
az monitor metrics alert show \
  --name boloo-http-5xx-errors \
  --resource-group boloo-production-rg
```

### Alert 2: High Response Time

- **Name**: `boloo-high-response-time`
- **Metric**: `HttpResponseTime`
- **Condition**: Average > 5 seconds
- **Time Window**: 5 minutes
- **Evaluation Frequency**: 1 minute
- **Severity**: 2 (Warning)
- **Description**: Triggers when average response time exceeds 5 seconds

```bash
az monitor metrics alert show \
  --name boloo-high-response-time \
  --resource-group boloo-production-rg
```

### Alert 3: High CPU Usage

- **Name**: `boloo-high-cpu`
- **Metric**: `CpuTime`
- **Condition**: Total > 240 seconds
- **Time Window**: 5 minutes
- **Evaluation Frequency**: 1 minute
- **Severity**: 2 (Warning)
- **Description**: Triggers when CPU time exceeds 240 seconds (80% of 5 minutes)

```bash
az monitor metrics alert show \
  --name boloo-high-cpu \
  --resource-group boloo-production-rg
```

---

## 4. Available Metrics

The following metrics are available for monitoring:

| Metric | Unit | Description |
|--------|------|-------------|
| CpuTime | Seconds | Total CPU time consumed |
| Requests | Count | Number of HTTP requests |
| BytesReceived | Bytes | Incoming network traffic |
| BytesSent | Bytes | Outgoing network traffic |
| Http101 | Count | HTTP 101 responses |
| Http2xx | Count | HTTP 2xx successful responses |
| Http3xx | Count | HTTP 3xx redirect responses |
| Http401 | Count | HTTP 401 unauthorized responses |
| Http403 | Count | HTTP 403 forbidden responses |
| Http404 | Count | HTTP 404 not found responses |
| Http4xx | Count | HTTP 4xx client error responses |
| Http5xx | Count | HTTP 5xx server error responses |
| MemoryWorkingSet | Bytes | Current memory usage |
| AverageMemoryWorkingSet | Bytes | Average memory usage |
| AverageResponseTime | Seconds | Average response time |
| HttpResponseTime | Seconds | HTTP response time |
| InstanceCount | Count | Number of instances |
| HealthCheckStatus | Count | Health check status |
| FileSystemUsage | Bytes | File system usage |

### Query Metrics

```bash
# View CPU metrics
az monitor metrics list \
  --resource "/subscriptions/417b3ad6-5fc1-47a3-917d-21cf4e3eddfc/resourceGroups/boloo-production-rg/providers/Microsoft.Web/sites/boloo-backend-api" \
  --metric CpuTime \
  --start-time 2025-11-21T00:00:00Z \
  --interval PT1H

# View HTTP 5xx errors
az monitor metrics list \
  --resource "/subscriptions/417b3ad6-5fc1-47a3-917d-21cf4e3eddfc/resourceGroups/boloo-production-rg/providers/Microsoft.Web/sites/boloo-backend-api" \
  --metric Http5xx \
  --start-time 2025-11-21T00:00:00Z \
  --interval PT5M
```

---

## 5. Current Application Status

### Deployment Status

- ✅ **Deployment**: Successful
- ✅ **Application**: Running (Gunicorn on port 8000)
- ⚠️ **Framework Detection**: Using default app (no framework detected)
- ⚠️ **Virtual Environment**: Not found (`/home/site/wwwroot/antenv` missing)

### Identified Issues from Logs

#### Issue 1: No Framework Detected
```
No framework detected; using default app from /opt/defaultsite
Generating `gunicorn` command for 'application:app'
```

**Impact**: The application is using Azure's default app instead of the actual FastAPI application.

**Resolution Required**:
1. Configure startup command in App Service
2. Ensure proper project structure
3. Add `oryx-manifest.toml` for framework detection

#### Issue 2: Missing Virtual Environment
```
WARNING: Could not find virtual environment directory /home/site/wwwroot/antenv.
WARNING: Could not find package directory /home/site/wwwroot/__oryx_packages__.
```

**Impact**: Dependencies may not be properly isolated.

**Resolution Required**: Configure Oryx build to create virtual environment.

#### Issue 3: All API Endpoints Return 404
```
GET /api/v1/cases - 404
POST /api/v1/triage/process - 404
GET /api - 404
```

**Impact**: API is not accessible; only default page works.

**Root Cause**: Application is running default Gunicorn app, not the FastAPI application.

---

## 6. Monitoring Commands

### Real-time Monitoring

```bash
# Stream application logs
az webapp log tail --name boloo-backend-api --resource-group boloo-production-rg

# Monitor metrics in real-time
az monitor metrics list \
  --resource "/subscriptions/417b3ad6-5fc1-47a3-917d-21cf4e3eddfc/resourceGroups/boloo-production-rg/providers/Microsoft.Web/sites/boloo-backend-api" \
  --metric Http5xx,HttpResponseTime,CpuTime \
  --interval PT1M

# Check application health
curl https://boloo-backend-api.azurewebsites.net/
```

### Alert Management

```bash
# List all alerts
az monitor metrics alert list --resource-group boloo-production-rg -o table

# List alert incidents
az monitor alert-rule-incidents list \
  --resource-group boloo-production-rg \
  --rule-name boloo-http-5xx-errors

# Disable an alert
az monitor metrics alert update \
  --name boloo-http-5xx-errors \
  --resource-group boloo-production-rg \
  --enabled false

# Enable an alert
az monitor metrics alert update \
  --name boloo-high-response-time \
  --resource-group boloo-production-rg \
  --enabled true
```

### Diagnostics

```bash
# Run diagnostics
az webapp show \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --query "state,healthCheckPath,httpsOnly,outboundIpAddresses" -o json

# Check environment variables
az webapp config appsettings list \
  --name boloo-backend-api \
  --resource-group boloo-production-rg -o table

# View deployment logs
az webapp deployment list-publishing-profiles \
  --name boloo-backend-api \
  --resource-group boloo-production-rg
```

---

## 7. Recommended Actions

### Immediate (Critical)

1. **Fix Application Startup**
   - Configure startup command: `gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000`
   - Update App Service Configuration
   - Verify FastAPI application is accessible

2. **Enable Application Logging**
   ```bash
   az webapp log config \
     --name boloo-backend-api \
     --resource-group boloo-production-rg \
     --application-logging filesystem \
     --level information
   ```

3. **Add Health Check Endpoint**
   - Configure: `/health` or `/api/health`
   - Monitor application availability

### Short-term (High Priority)

1. **Configure Action Groups for Alerts**
   - Add email notifications
   - Add SMS notifications
   - Add webhook integrations

2. **Enable Application Insights SDK**
   - Add `opencensus-ext-azure` to requirements.txt
   - Configure Application Insights in FastAPI app
   - Track custom events and dependencies

3. **Set up Availability Tests**
   - Configure ping tests for critical endpoints
   - Set up multi-step web tests

### Long-term (Enhancement)

1. **Advanced Monitoring**
   - Custom metrics and events
   - Performance profiling
   - User analytics

2. **Log Analytics Integration**
   - Advanced query capabilities
   - Cross-resource analysis
   - Custom dashboards

3. **Automated Remediation**
   - Auto-scaling rules
   - Auto-healing rules
   - Runbook automation

---

## 8. Troubleshooting

### Application Not Responding

```bash
# Restart application
az webapp restart \
  --name boloo-backend-api \
  --resource-group boloo-production-rg

# Check container logs
az webapp log tail \
  --name boloo-backend-api \
  --resource-group boloo-production-rg | grep -i error
```

### High Memory Usage

```bash
# Check memory metrics
az monitor metrics list \
  --resource "/subscriptions/417b3ad6-5fc1-47a3-917d-21cf4e3eddfc/resourceGroups/boloo-production-rg/providers/Microsoft.Web/sites/boloo-backend-api" \
  --metric MemoryWorkingSet \
  --interval PT5M

# Scale up if needed
az appservice plan update \
  --name boloo-backend-plan \
  --resource-group boloo-production-rg \
  --sku B2
```

### Alert Not Triggering

```bash
# Verify alert configuration
az monitor metrics alert show \
  --name boloo-http-5xx-errors \
  --resource-group boloo-production-rg

# Check if alert is enabled
az monitor metrics alert list \
  --resource-group boloo-production-rg \
  --query "[?enabled==\`true\`].name" -o table
```

---

## 9. Resources

- [Azure Application Insights Documentation](https://docs.microsoft.com/en-us/azure/azure-monitor/app/app-insights-overview)
- [App Service Monitoring](https://docs.microsoft.com/en-us/azure/app-service/web-sites-monitor)
- [Azure Monitor Alerts](https://docs.microsoft.com/en-us/azure/azure-monitor/alerts/alerts-overview)
- [Kudu Dashboard](https://boloo-backend-api.scm.azurewebsites.net)

---

## Summary

✅ **Configured**:
- Application Insights with 90-day retention
- Web server logging (3 days, 100MB)
- Three metric alerts (5xx errors, response time, CPU)
- Failed request tracing
- Detailed error messages

⚠️ **Issues Identified**:
- Application not properly starting (using default app)
- Virtual environment not detected
- All API endpoints returning 404

🔧 **Next Steps**:
1. Fix application startup configuration
2. Configure alert action groups
3. Enable Application Insights SDK integration
4. Set up health check endpoint
