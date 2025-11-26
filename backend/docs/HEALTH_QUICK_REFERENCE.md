# Health Check System - Quick Reference Card

## 🎯 Endpoints at a Glance

| Endpoint | Use Case | Checks Dependencies? | Returns 503? |
|----------|----------|---------------------|--------------|
| `/health` | Legacy compatibility | ❌ No | ❌ No |
| `/health/live` | Kubernetes liveness | ❌ No | ❌ No |
| `/health/ready` | Kubernetes readiness | ✅ Yes | ✅ Yes (if down) |
| `/health/detailed` | Admin diagnostics | ✅ Yes | ❌ No |

---

## 🔗 Quick Test Commands

```bash
# Basic health (always 200)
curl http://localhost:8000/health

# Liveness probe (always 200 if running)
curl http://localhost:8000/health/live

# Readiness probe (200 if ready, 503 if not)
curl http://localhost:8000/health/ready

# Detailed diagnostics (always 200)
curl http://localhost:8000/health/detailed | jq

# Check only status code
curl -o /dev/null -s -w "%{http_code}\n" http://localhost:8000/health/ready
```

---

## 📊 Dependencies Monitored

### Internal (Always Critical)
- ✅ PostgreSQL Database
- ✅ Redis Cache
- ✅ MinIO Storage
- ✅ API Endpoints

### External (May Be Optional)
- ✅ Azure OpenAI API
- ✅ Azure Speech Services
- ✅ Claude AI API
- ✅ SMTP Email
- ✅ Network

---

## 🚨 Health Status Levels

| Status | Meaning | HTTP Code |
|--------|---------|-----------|
| `healthy` | All good ✅ | 200 |
| `degraded` | Works but slow ⚠️ | 200 |
| `down` | Not working ❌ | 503 (readiness only) |

---

## 🐳 Docker Health Check

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health/ready"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

---

## ☸️ Kubernetes Probes

```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
```

---

## 📊 Application Insights (Optional)

```bash
# Enable telemetry
export APPLICATIONINSIGHTS_INSTRUMENTATION_KEY="your-key"

# Or in .env
APPLICATIONINSIGHTS_INSTRUMENTATION_KEY=your-key-here
```

---

## 🧪 Test Suite

```bash
# Run all health tests
pytest tests/test_health_endpoints.py -v

# Run with coverage
pytest tests/test_health_endpoints.py --cov=app.routers.health

# Specific test
pytest tests/test_health_endpoints.py::TestReadinessProbe -v
```

---

## 🔍 Common Responses

### ✅ Healthy System
```json
{
  "status": "healthy",
  "ready": true,
  "dependencies": [...]
}
```

### ⚠️ Degraded System
```json
{
  "status": "degraded",
  "ready": true,
  "dependencies": [
    {"name": "Redis", "status": "degraded", "error": "Slow response"}
  ]
}
```

### ❌ Down System (503)
```json
{
  "detail": {
    "status": "down",
    "ready": false,
    "dependencies": [
      {"name": "Database", "status": "down", "error": "Connection refused"}
    ]
  }
}
```

---

## 🛠️ Troubleshooting

### 503 on /health/ready?
```bash
# Check what's failing
curl http://localhost:8000/health/detailed | jq '.dependencies[] | select(.status != "healthy")'
```

### High response times?
```bash
# Check average response time
curl http://localhost:8000/health/detailed | jq '.metrics.average_response_time_ms'
```

### App Insights not working?
```bash
# Verify key is set
echo $APPLICATIONINSIGHTS_INSTRUMENTATION_KEY

# Check package installed
pip list | grep opencensus
```

---

## 📚 Documentation

- **Full docs:** `docs/HEALTH_CHECKS.md`
- **Setup guide:** `docs/HEALTH_SETUP_GUIDE.md`
- **Implementation:** `docs/HEALTH_IMPLEMENTATION_SUMMARY.md`

---

## 🚀 Production Checklist

- [ ] `/health/ready` returns 200
- [ ] Kubernetes probes configured
- [ ] App Insights enabled
- [ ] Alerts configured
- [ ] Dashboard created
- [ ] Tests passing
- [ ] Load tested

---

## 💡 Pro Tips

1. **Use /health/live for container restart logic** (doesn't check dependencies)
2. **Use /health/ready for load balancer routing** (checks dependencies)
3. **Use /health/detailed for debugging** (shows all details)
4. **Monitor health_percentage metric** (aim for >95%)
5. **Set up alerts on consecutive failures** (not single failures)

---

## 🔗 Quick Links

- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Readiness: http://localhost:8000/health/ready
- Detailed: http://localhost:8000/health/detailed
