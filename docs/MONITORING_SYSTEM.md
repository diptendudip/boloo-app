# Boloo Monitoring System Documentation

## Overview
Comprehensive health monitoring system with internal/external resource categorization, 0-2 health rating system, auto-restart capabilities, and detailed tracking.

**Last Updated**: 2025-10-26

---

## Features Implemented

### 1. Health Rating System (0-2 Scale)
- **0 (RED)**: Resource is DOWN - Not operational
- **1 (YELLOW)**: Resource is PARTIAL - API responds but limited functionality
- **2 (GREEN)**: Resource is HEALTHY - Fully operational with data access

### 2. Resource Categorization

#### Internal Resources (Services we control)
- **PostgreSQL Database** - Primary data store
- **Redis Cache** - Session and cache management
- **MinIO Storage** - Object storage for media files
- **API Endpoints** - All REST API endpoints (/health, /v1/*)

#### External Resources (Third-party services)
- **Azure Speech API** - Speech-to-text and text-to-speech
- **Claude AI API** - AI processing for case intake
- **SMTP Service** - Email delivery
- **Network Connectivity** - General internet connectivity

### 3. Database Schema

#### `resource_health` Table
Stores current health status of all monitored resources:
- Resource identification (name, type, category)
- Health status (0-2 rating)
- Response metrics (response time, uptime percentage)
- Failure tracking (consecutive failures, total failures)
- Auto-restart configuration
- Dependencies tracking

#### `health_check_logs` Table
Historical log of all health checks:
- Check timestamp
- Health status at time of check
- Response time
- Status/error messages
- Metadata

### 4. Monitoring Service

**File**: `app/services/health_monitor.py`

Comprehensive health checking for:
- Database connectivity and query capability
- Redis connection and read/write operations
- MinIO storage access and bucket verification
- API endpoint availability and data response
- Azure Speech API token validation
- Claude API authentication and test requests
- SMTP server connection and authentication
- Network connectivity

### 5. API Endpoints

**File**: `app/routers/monitoring_v2.py`

#### GET `/v1/monitoring/health/dashboard`
Get comprehensive health dashboard with internal and external resources categorized.

**Response**:
```json
{
  "timestamp": "2025-10-26T...",
  "overall_health": {
    "total_resources": 10,
    "healthy": 8,
    "partial": 1,
    "down": 1,
    "health_percentage": 80.0
  },
  "internal_resources": [...],
  "external_resources": [...],
  "critical_alerts": [...]
}
```

#### GET `/v1/monitoring/health/resources`
Get all resources with optional filtering.

**Query Parameters**:
- `resource_type`: `internal` | `external`
- `status`: `0` | `1` | `2`

#### GET `/v1/monitoring/health/resources/{resource_name}`
Get detailed information about a specific resource including:
- Current status
- 24-hour statistics
- Recent check history
- Dependencies

#### POST `/v1/monitoring/health/check`
Manually trigger a health check for all resources (runs in background).

#### POST `/v1/monitoring/health/resources/{resource_name}/restart`
Manually restart a resource/service.
- Only works for internal resources
- Requires `restart_enabled=True`
- Executes restart command in background

#### GET `/v1/monitoring/health/resources/{resource_name}/history`
Get historical health data for a resource.

**Query Parameters**:
- `hours`: Number of hours to look back (default: 24, max: 168)

#### GET `/v1/monitoring/health/alerts`
Get all current health alerts categorized by severity:
- **Critical**: Resources that are DOWN
- **Warning**: Resources needing restart (down >5 mins)
- **Info**: Resources partially operational

#### GET `/v1/monitoring/health/summary`
Quick summary of system health (useful for status pages).

**Response**:
```json
{
  "status": "healthy|partial|degraded",
  "status_color": "green|yellow|red",
  "resources": {
    "total": 10,
    "healthy": 9,
    "partial": 1,
    "down": 0
  },
  "health_score": 90.0,
  "last_check": "2025-10-26T...",
  "timestamp": "2025-10-26T..."
}
```

#### DELETE `/v1/monitoring/health/logs/cleanup`
Clean up old health check logs.

**Query Parameters**:
- `days_to_keep`: Number of days to retain (default: 7)

---

## Auto-Restart Logic

Resources marked with `restart_enabled=True` and down for >5 minutes will be automatically restarted by the background worker.

**Restart Eligibility**:
1. Resource type must be `internal`
2. `restart_enabled` must be `True`
3. `restart_command` must be configured
4. Resource must be DOWN (status 0)
5. Down for more than 5 minutes

---

## Configuration

### Monitoring Frequency
Default check interval: **60 seconds** (configurable per resource)

Can be adjusted in `resource_health.check_interval_seconds` column.

### Timeout Settings
Default timeout: **10 seconds** (configurable per resource)

Can be adjusted in `resource_health.timeout_seconds` column.

---

## Next Steps

### Still To Implement:

1. **Background Health Check Worker**
   - Celery task or asyncio worker
   - Runs every 1-5 minutes
   - Automatically checks all resources
   - Auto-restart logic for failed services

2. **Service Management Utilities**
   - Restart scripts for each service
   - Docker service restart commands
   - Process manager integration (PM2/Supervisor)

3. **Frontend Dashboard**
   - React/Next.js monitoring dashboard
   - Real-time updates (WebSocket or polling)
   - Visual health indicators
   - Manual restart buttons
   - Resource dependency graph
   - Historical charts

4. **Initial Resource Registration**
   - Script to populate initial resources
   - Set restart commands for each service
   - Configure dependencies

5. **Testing**
   - Unit tests for health checks
   - Integration tests for monitoring endpoints
   - End-to-end testing with real services

---

## Usage Examples

### 1. Initialize Resources (First Time Setup)

Run this script to populate the database with monitored resources:

```python
from app.database import SessionLocal
from app.models.resource_health import ResourceHealth, ResourceType, ResourceCategory

db = SessionLocal()

resources = [
    ResourceHealth(
        resource_name="PostgreSQL Database",
        resource_type=ResourceType.INTERNAL,
        resource_category=ResourceCategory.DATABASE,
        restart_enabled=True,
        restart_command="docker restart boloo-postgres",
        check_interval_seconds=60
    ),
    ResourceHealth(
        resource_name="Redis Cache",
        resource_type=ResourceType.INTERNAL,
        resource_category=ResourceCategory.CACHE,
        restart_enabled=True,
        restart_command="docker restart boloo-redis",
        check_interval_seconds=60
    ),
    # ... add more resources
]

for resource in resources:
    db.add(resource)

db.commit()
```

### 2. Manual Health Check

```bash
curl -X POST http://localhost:8000/v1/monitoring/health/check
```

### 3. Get Dashboard Data

```bash
curl http://localhost:8000/v1/monitoring/health/dashboard
```

### 4. Restart a Service

```bash
curl -X POST http://localhost:8000/v1/monitoring/health/resources/Redis%20Cache/restart
```

### 5. View Resource History

```bash
curl "http://localhost:8000/v1/monitoring/health/resources/PostgreSQL%20Database/history?hours=24"
```

---

## Database Migration

To apply the monitoring tables to your database:

```bash
cd backend
source venv/bin/activate

# Run the migration
alembic upgrade head
```

---

## Integration with Main App

Add to `app/main.py`:

```python
from app.routers import monitoring_v2

# Include the new monitoring router
app.include_router(
    monitoring_v2.router,
    prefix="/v1/monitoring",
    tags=["Monitoring"]
)
```

---

## Monitoring Dashboard UI Design

### Layout:

```
┌─────────────────────────────────────────────────────────────┐
│  BOLOO SYSTEM HEALTH DASHBOARD                              │
│                                                             │
│  Overall Health: ● HEALTHY (90% uptime)  Last Check: 2m ago│
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  INTERNAL RESOURCES (Services We Control)                   │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ ● PostgreSQL Database          2  | 45ms | ↻ Restart  │ │
│  │ ● Redis Cache                   2  | 12ms | ↻ Restart  │ │
│  │ ● MinIO Storage                 2  | 89ms | ↻ Restart  │ │
│  │ ● API: Health Check             2  | 23ms | -          │ │
│  │ ◐ API: Cases                    1  | 156ms| -          │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  EXTERNAL RESOURCES (Third-Party Services)                  │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ ● Azure Speech API              2  | 234ms| -          │ │
│  │ ● Claude AI API                 2  | 187ms| -          │ │
│  │ ○ SMTP Service                  0  | -    | -          │ │
│  │ ● Network Connectivity          2  | 45ms | -          │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ALERTS & NOTIFICATIONS                                     │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ 🔴 CRITICAL: SMTP Service is DOWN for 15.2 minutes     │ │
│  │ 🟡 WARNING: API: Cases responding slowly (156ms)       │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

Color Legend:
● GREEN  = Status 2 (Healthy - Fully Operational)
◐ YELLOW = Status 1 (Partial - Limited Functionality)
○ RED    = Status 0 (Down - Not Operational)
```

---

## Dependencies File

The following resources should list their dependencies:

- **API Endpoints** → Database, Redis, MinIO
- **Database** → Network
- **Redis** → Network
- **MinIO** → Network
- **Azure Speech** → Network
- **Claude AI** → Network
- **SMTP** → Network

This enables dependency-aware health checking and restart logic.

---

## Files Created/Modified

### New Files:
1. `backend/app/models/resource_health.py` - Database models
2. `backend/app/services/health_monitor.py` - Health checking service
3. `backend/app/routers/monitoring_v2.py` - Enhanced API endpoints
4. `backend/alembic/versions/001_add_resource_health_monitoring_tables.py` - Migration
5. `docs/MONITORING_SYSTEM.md` - This documentation

### Modified Files:
1. `backend/app/models/__init__.py` - Added new models
2. `backend/alembic/env.py` - Configured for auto-migrations

---

## Notes

- All health checks run asynchronously for better performance
- Database is updated after each check cycle
- Historical data is retained for 7 days by default
- Manual cleanup endpoint available for maintenance
- Restart functionality requires proper Docker/service permissions
- Authentication should be added to restart/cleanup endpoints in production

---

## Questions or Issues?

Refer to the main development phases document: `docs/DEVELOPMENT_PHASES.md`
