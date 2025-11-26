# Monitoring System Testing Guide

## Prerequisites

Before testing, ensure you have:
- Docker Desktop installed and running
- Python 3.11+ with virtualenv
- curl or Postman for API testing

---

## Step-by-Step Testing Instructions

### Step 1: Start Docker Services

```bash
cd "/Users/diptendu/boloo app/boloo-app"

# Start infrastructure services
docker-compose up -d postgres redis minio

# Wait for services to be healthy (about 30 seconds)
docker-compose ps

# You should see:
# boloo-postgres   (healthy)
# boloo-redis      (healthy)
# boloo-minio      (healthy)
```

### Step 2: Activate Virtual Environment

```bash
cd backend
source venv/bin/activate
```

### Step 3: Run Database Migrations

```bash
# Create the monitoring tables
alembic upgrade head

# Verify migration worked
alembic current
```

Expected output: `001 (head)` or similar

### Step 4: Initialize Monitoring Resources

```bash
# Run the initialization script
python scripts/init_monitoring_resources.py
```

Expected output:
```
Initializing monitoring resources...

✓ Created: PostgreSQL Database
✓ Created: Redis Cache
✓ Created: MinIO Storage
✓ Created: API: Health Check
✓ Created: API: Entities
✓ Created: API: Taxonomies
✓ Created: Azure Speech API
✓ Created: Claude AI API
✓ Created: SMTP Email Service
✓ Created: Network Connectivity

============================================================
Monitoring Resources Initialized Successfully!
============================================================
Created: 10 resources
Updated: 0 resources
Total:   10 resources

Resources by type:
  Internal: 6
  External: 4
```

### Step 5: Start Backend Server

```bash
# Start the backend in one terminal
python -m app.main
```

Or using uvicorn directly:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Expected output:
```
INFO:     Starting Boloo API...
INFO:     Environment: development
INFO:     Creating database tables...
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 6: Test Basic Health Endpoint

In a new terminal:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "app": "Boloo",
  "environment": "development",
  "version": "1.0.0"
}
```

### Step 7: View API Documentation

Open your browser to: http://localhost:8000/docs

You should see FastAPI's interactive documentation with all endpoints, including the new Monitoring v2 endpoints.

### Step 8: Trigger Initial Health Check

```bash
curl -X POST http://localhost:8000/v1/monitoring/health/check
```

Expected response:
```json
{
  "message": "Health check initiated",
  "status": "running",
  "timestamp": "2025-10-26T..."
}
```

Wait 2-3 seconds for the background check to complete.

### Step 9: View Health Dashboard

```bash
curl http://localhost:8000/v1/monitoring/health/dashboard | jq
```

Expected response structure:
```json
{
  "timestamp": "2025-10-26T...",
  "overall_health": {
    "total_resources": 10,
    "healthy": 7,
    "partial": 2,
    "down": 1,
    "health_percentage": 70.0
  },
  "internal_resources": [
    {
      "resource_name": "PostgreSQL Database",
      "health_status": 2,
      "health_color": "green",
      "response_time_ms": 45.2,
      ...
    },
    ...
  ],
  "external_resources": [
    {
      "resource_name": "Azure Speech API",
      "health_status": 0,
      "health_color": "red",
      "error_message": "Azure Speech API not configured (missing credentials)",
      ...
    },
    ...
  ],
  "critical_alerts": [...]
}
```

### Step 10: View Health Summary

```bash
curl http://localhost:8000/v1/monitoring/health/summary | jq
```

Expected response:
```json
{
  "status": "partial",
  "status_color": "yellow",
  "resources": {
    "total": 10,
    "healthy": 7,
    "partial": 2,
    "down": 1
  },
  "health_score": 70.0,
  "last_check": "2025-10-26T...",
  "timestamp": "2025-10-26T..."
}
```

### Step 11: View All Resources

```bash
# Get all resources
curl http://localhost:8000/v1/monitoring/health/resources | jq

# Get only internal resources
curl "http://localhost:8000/v1/monitoring/health/resources?resource_type=internal" | jq

# Get only DOWN resources
curl "http://localhost:8000/v1/monitoring/health/resources?status=0" | jq
```

### Step 12: View Specific Resource Details

```bash
curl "http://localhost:8000/v1/monitoring/health/resources/PostgreSQL%20Database" | jq
```

Expected response:
```json
{
  "resource": {
    "resource_name": "PostgreSQL Database",
    "resource_type": "internal",
    "resource_category": "database",
    "health_status": 2,
    "health_color": "green",
    "response_time_ms": 45.2,
    "uptime_percentage": 100.0,
    ...
  },
  "statistics_24h": {
    "total_checks": 5,
    "failures": 0,
    "average_response_time_ms": 46.8,
    "uptime_percentage": 100.0
  },
  "recent_checks": [
    {
      "timestamp": "2025-10-26T...",
      "status": 2,
      "response_time_ms": 45.2,
      "message": "Database operational with 15 tables"
    },
    ...
  ],
  "dependencies": ["Network Connectivity"]
}
```

### Step 13: View Resource History

```bash
# Last 24 hours (default)
curl "http://localhost:8000/v1/monitoring/health/resources/PostgreSQL%20Database/history" | jq

# Last 48 hours
curl "http://localhost:8000/v1/monitoring/health/resources/PostgreSQL%20Database/history?hours=48" | jq
```

### Step 14: View Alerts

```bash
curl http://localhost:8000/v1/monitoring/health/alerts | jq
```

Expected response:
```json
{
  "total_alerts": 3,
  "critical": 1,
  "warning": 0,
  "info": 2,
  "alerts": [
    {
      "severity": "critical",
      "resource": "Azure Speech API",
      "resource_type": "external",
      "message": "Resource is DOWN for 5.2 minutes",
      "error": "Azure Speech API not configured (missing credentials)",
      "can_restart": false,
      "timestamp": "2025-10-26T..."
    },
    ...
  ]
}
```

### Step 15: Test Manual Restart (Optional)

**Note:** This only works if the restart_command is properly configured and you have Docker permissions.

```bash
# Try to restart Redis
curl -X POST http://localhost:8000/v1/monitoring/health/resources/Redis%20Cache/restart | jq
```

Expected response:
```json
{
  "message": "Restart initiated for Redis Cache",
  "restart_count": 1,
  "timestamp": "2025-10-26T..."
}
```

### Step 16: Verify Database Data

```bash
# Access PostgreSQL directly
docker exec -it boloo-postgres psql -U boloo -d boloo

# Inside PostgreSQL:
\dt  # List all tables
SELECT * FROM resource_health;
SELECT COUNT(*) FROM health_check_logs;
\q  # Quit
```

---

## Automated Test Script

Run the automated test script:

```bash
cd "/Users/diptendu/boloo app/boloo-app/backend"
./scripts/test_monitoring.sh
```

---

## Expected Results

### Internal Resources (Should be GREEN/HEALTHY)
- ✅ PostgreSQL Database - Status 2
- ✅ Redis Cache - Status 2
- ✅ MinIO Storage - Status 2
- ✅ API: Health Check - Status 2
- ✅ API: Entities - Status 2
- ✅ API: Taxonomies - Status 2

### External Resources (May be RED/DOWN if not configured)
- ⚠️ Azure Speech API - Status 0 (not configured)
- ⚠️ Claude AI API - Status 0 (not configured)
- ⚠️ SMTP Email Service - Status 0 (not configured)
- ✅ Network Connectivity - Status 2 (if internet available)

---

## Troubleshooting

### Issue: "Cannot connect to database"
**Solution:** Ensure Docker PostgreSQL is running:
```bash
docker ps | grep postgres
docker logs boloo-postgres
```

### Issue: "Redis connection refused"
**Solution:** Ensure Docker Redis is running:
```bash
docker ps | grep redis
docker logs boloo-redis
```

### Issue: "MinIO bucket not found"
**Solution:** Create the bucket:
```bash
# Access MinIO console: http://localhost:9001
# Login: minioadmin / minioadmin
# Create bucket: boloo-media
```

Or use mc (MinIO client):
```bash
docker exec boloo-minio mc mb /data/boloo-media
```

### Issue: "Alembic cannot connect to database"
**Solution:** The database URL might be wrong. Check:
```bash
# In backend/.env or app/config.py
DATABASE_URL=postgresql://boloo:boloo_dev_password@localhost:5432/boloo
```

### Issue: "Module not found" errors
**Solution:** Ensure you're in the virtual environment:
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: "Import error for monitoring_v2"
**Solution:** Ensure the file exists and Python can find it:
```bash
ls app/routers/monitoring_v2.py
python -c "from app.routers import monitoring_v2; print('OK')"
```

---

## Performance Benchmarks

Expected response times:
- Database check: 20-50ms
- Redis check: 5-15ms
- MinIO check: 50-150ms
- API endpoints: 20-100ms
- External APIs: 200-500ms

---

## Next Steps After Testing

1. **Configure External APIs** - Add API keys to `.env`:
   ```bash
   AZURE_SPEECH_KEY=your_key
   AZURE_SPEECH_REGION=centralindia
   ANTHROPIC_API_KEY=your_key
   SMTP_USER=your_email
   SMTP_PASSWORD=your_password
   ```

2. **Implement Background Worker** - Create Celery task for auto health checks

3. **Build Frontend Dashboard** - Create React/Next.js UI

4. **Set up Alerts** - Email/SMS notifications for critical failures

5. **Enable Auto-Restart** - Test restart functionality

---

## Clean Up

To stop services:
```bash
cd "/Users/diptendu/boloo app/boloo-app"
docker-compose down

# To also remove volumes (WARNING: deletes all data):
docker-compose down -v
```

---

## Questions?

Refer to:
- `docs/MONITORING_SYSTEM.md` - Full system documentation
- `docs/DEVELOPMENT_PHASES.md` - Overall project status
- FastAPI docs: http://localhost:8000/docs
