# Health Check System - Quick Setup Guide

## 🚀 Quick Start

The enhanced health check system is already integrated into the Boloo backend. No additional setup required for basic functionality!

### Test the Endpoints

```bash
# Basic health check (backward compatible)
curl http://localhost:8000/health

# Liveness probe
curl http://localhost:8000/health/live

# Readiness probe (checks all dependencies)
curl http://localhost:8000/health/ready

# Detailed diagnostics
curl http://localhost:8000/health/detailed
```

---

## 📊 Optional: Enable Application Insights

For production monitoring with Azure Application Insights:

### Step 1: Install Dependencies

Uncomment the monitoring dependencies in `requirements.txt`:

```bash
# Uncomment these lines in requirements.txt:
opencensus-ext-azure==1.1.13
opencensus-ext-logging==0.1.1
opencensus-ext-requests==0.8.0

# Then install:
pip install opencensus-ext-azure opencensus-ext-logging opencensus-ext-requests
```

### Step 2: Get Instrumentation Key

1. Go to Azure Portal
2. Navigate to your Application Insights resource
3. Copy the Instrumentation Key from the Overview page

### Step 3: Set Environment Variable

Add to your `.env` file:

```bash
APPLICATIONINSIGHTS_INSTRUMENTATION_KEY=your-instrumentation-key-here
```

Or export in your shell:

```bash
export APPLICATIONINSIGHTS_INSTRUMENTATION_KEY="your-key-here"
```

### Step 4: Restart the Service

```bash
# Development
uvicorn app.main:app --reload

# Production
gunicorn app.main:app -k uvicorn.workers.UvicornWorker
```

### Step 5: Verify in Azure Portal

1. Go to Application Insights in Azure Portal
2. Navigate to "Logs" section
3. Run this query to see health check telemetry:

```kusto
traces
| where customDimensions.resource_name != ""
| project timestamp, resource_name=customDimensions.resource_name,
          health_status=customDimensions.health_status,
          response_time_ms=customDimensions.response_time_ms
| order by timestamp desc
| take 100
```

---

## 🔧 Configuration

### Environment Variables

All health checks use existing configuration from your `.env` file:

```bash
# Database (required)
DATABASE_URL=postgresql://user:pass@localhost:5432/boloo

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# MinIO (optional)
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# Azure OpenAI (required)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini

# Azure Speech (optional)
AZURE_SPEECH_KEY=your-speech-key
AZURE_SPEECH_REGION=centralindia

# Claude API (optional)
ANTHROPIC_API_KEY=your-claude-key

# SMTP (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Application Insights (optional)
APPLICATIONINSIGHTS_INSTRUMENTATION_KEY=your-instrumentation-key
```

---

## 🐳 Docker Deployment

### Update docker-compose.yml

Add health checks to your service definition:

```yaml
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}
      - APPLICATIONINSIGHTS_INSTRUMENTATION_KEY=${APPLICATIONINSIGHTS_INSTRUMENTATION_KEY}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/ready"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

---

## ☸️ Kubernetes Deployment

### Update your Deployment manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: boloo-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: boloo-backend
  template:
    metadata:
      labels:
        app: boloo-backend
    spec:
      containers:
      - name: backend
        image: boloo-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: APPLICATIONINSIGHTS_INSTRUMENTATION_KEY
          valueFrom:
            secretKeyRef:
              name: boloo-secrets
              key: app-insights-key

        # Liveness probe - restart if process is dead
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3

        # Readiness probe - route traffic only when ready
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          successThreshold: 1
          failureThreshold: 3

        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
```

---

## 📈 Monitoring Setup

### Azure Monitor Alert Rules

Create these alerts in Azure Portal:

#### Critical: Service Down
```
Resource: Application Insights
Alert condition: Custom log search
Query:
  traces
  | where customDimensions.health_status == "down"
  | summarize count() by bin(timestamp, 5m)
  | where count_ > 0

Threshold: Greater than 0
Evaluation frequency: 5 minutes
Action: Page on-call engineer
```

#### Warning: Degraded Service
```
Query:
  traces
  | where customDimensions.health_status == "degraded"
  | summarize count() by bin(timestamp, 10m)
  | where count_ > 2

Threshold: Greater than 2
Evaluation frequency: 10 minutes
Action: Notify team Slack channel
```

### Grafana Dashboard (Optional)

Import dashboard JSON or create panels:

1. **Health Score Gauge**
   - Query: `health_percentage` metric
   - Visualization: Gauge (0-100%)
   - Thresholds: Red < 80%, Yellow < 95%, Green >= 95%

2. **Dependency Status Table**
   - Query: Latest health check per dependency
   - Columns: Name, Status, Response Time, Last Check

3. **Response Time Chart**
   - Query: `response_time_ms` over time
   - Visualization: Line chart
   - Group by: `resource_name`

---

## 🧪 Testing

### Manual Testing

```bash
# Test all endpoints
curl http://localhost:8000/health
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
curl http://localhost:8000/health/detailed

# Format JSON output with jq
curl http://localhost:8000/health/detailed | jq

# Check only status code
curl -o /dev/null -s -w "%{http_code}\n" http://localhost:8000/health/ready
```

### Automated Testing

```bash
# Run health check tests
pytest tests/test_health_endpoints.py -v

# With coverage report
pytest tests/test_health_endpoints.py --cov=app.routers.health --cov-report=html

# Run specific test
pytest tests/test_health_endpoints.py::TestReadinessProbe::test_readiness_service_down -v
```

### Load Testing

```bash
# Install hey (HTTP load generator)
# brew install hey  # macOS
# apt-get install hey  # Ubuntu

# Test readiness endpoint under load
hey -n 1000 -c 10 http://localhost:8000/health/ready

# Test detailed endpoint
hey -n 100 -c 5 http://localhost:8000/health/detailed
```

---

## 🐛 Troubleshooting

### Issue: 503 Service Unavailable on /health/ready

**Diagnosis:**
```bash
# Check detailed health to see what's failing
curl http://localhost:8000/health/detailed | jq '.dependencies[] | select(.status != "healthy")'
```

**Common Causes:**
1. Database not running
2. Azure OpenAI credentials invalid
3. Network connectivity issues

**Solutions:**
- Check PostgreSQL: `pg_isready -h localhost -p 5432`
- Verify Azure credentials in `.env`
- Check firewall/network settings

### Issue: High Response Times

**Diagnosis:**
```bash
# Check response times
curl http://localhost:8000/health/detailed | jq '.metrics.average_response_time_ms'
```

**Solutions:**
- Check database connection pool settings
- Verify network latency to Azure services
- Review Application Insights for slow queries

### Issue: Application Insights Not Receiving Data

**Diagnosis:**
1. Check environment variable: `echo $APPLICATIONINSIGHTS_INSTRUMENTATION_KEY`
2. Check service logs for initialization errors
3. Verify package installation: `pip list | grep opencensus`

**Solutions:**
- Reinstall packages: `pip install opencensus-ext-azure`
- Verify instrumentation key is correct
- Check Azure Portal for data ingestion lag (5-10 minutes)

---

## 📚 Additional Resources

- [Full Documentation](./HEALTH_CHECKS.md)
- [FastAPI Health Check Best Practices](https://fastapi.tiangolo.com/)
- [Kubernetes Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [Azure Application Insights](https://docs.microsoft.com/en-us/azure/azure-monitor/app/app-insights-overview)

---

## ✅ Checklist

After setup, verify:

- [ ] `/health` returns 200 OK
- [ ] `/health/live` returns 200 OK
- [ ] `/health/ready` returns 200 OK (or 503 if dependencies down)
- [ ] `/health/detailed` shows all dependencies
- [ ] Application Insights receives telemetry (if enabled)
- [ ] Kubernetes probes configured (if using K8s)
- [ ] Monitoring alerts configured
- [ ] Tests pass: `pytest tests/test_health_endpoints.py`

---

## 🎯 Production Checklist

Before deploying to production:

- [ ] Application Insights instrumentation key configured
- [ ] Monitoring alerts set up and tested
- [ ] Kubernetes probes configured with appropriate timeouts
- [ ] Load testing completed successfully
- [ ] Admin authentication enabled for `/health/detailed`
- [ ] Log retention policy configured
- [ ] Backup monitoring system in place
- [ ] Runbook created for common issues
- [ ] Team trained on health check system
- [ ] Dashboard created and shared with team
