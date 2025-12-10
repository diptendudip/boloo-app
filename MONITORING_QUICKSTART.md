# Monitoring System - Quick Start Guide

## ⚡ 5-Minute Setup

### 1. Start Docker
```bash
cd "/Users/diptendu/boloo app/boloo-app"
docker-compose up -d postgres redis minio
```

### 2. Setup Database
```bash
cd backend
source venv/bin/activate
alembic upgrade head
python scripts/init_monitoring_resources.py
```

### 3. Start Backend
```bash
python -m app.main
# Server runs at: http://localhost:8000
```

### 4. Run Tests
```bash
# In new terminal
cd backend
./scripts/test_monitoring.sh
```

---

## 📊 Key Endpoints

| What | URL |
|------|-----|
| 📈 Dashboard | `GET /v1/monitoring/health/dashboard` |
| ⚡ Summary | `GET /v1/monitoring/health/summary` |
| 📋 All Resources | `GET /v1/monitoring/health/resources` |
| 🔍 Resource Details | `GET /v1/monitoring/health/resources/{name}` |
| 🚨 Alerts | `GET /v1/monitoring/health/alerts` |
| ▶️ Trigger Check | `POST /v1/monitoring/health/check` |
| 🔄 Restart Service | `POST /v1/monitoring/health/resources/{name}/restart` |
| 📚 API Docs | http://localhost:8000/docs |

---

## 🎨 Health Status

| Code | Color | Meaning |
|------|-------|---------|
| 2 | 🟢 GREEN | Fully operational + data available |
| 1 | 🟡 YELLOW | Responds but limited functionality |
| 0 | 🔴 RED | Down / Not operational |

---

## 📁 Files Created

```
backend/
├── app/
│   ├── models/resource_health.py         ✅ Database models
│   ├── routers/monitoring_v2.py          ✅ API endpoints
│   ├── services/health_monitor.py        ✅ Health checks
│   └── main.py                           ✅ Updated (includes new router)
├── alembic/versions/001_...              ✅ Migration
├── scripts/
│   ├── init_monitoring_resources.py      ✅ Setup script
│   └── test_monitoring.sh                ✅ Test script
docs/
├── MONITORING_SYSTEM.md                  ✅ Full documentation
├── MONITORING_TEST_GUIDE.md              ✅ Testing guide
├── MONITORING_IMPLEMENTATION_SUMMARY.md  ✅ Summary
└── MONITORING_QUICKSTART.md              ✅ This file
```

---

## 🧪 Quick Test

```bash
# 1. Basic health
curl http://localhost:8000/health

# 2. Trigger health check
curl -X POST http://localhost:8000/v1/monitoring/health/check

# 3. View dashboard
curl http://localhost:8000/v1/monitoring/health/dashboard | jq

# 4. Quick summary
curl http://localhost:8000/v1/monitoring/health/summary | jq
```

---

## 📦 What's Monitored

**Internal (6)**:
- PostgreSQL Database
- Redis Cache
- MinIO Storage
- API: Health Check
- API: Entities
- API: Taxonomies

**External (4)**:
- Azure Speech API
- Claude AI API
- SMTP Email Service
- Network Connectivity

---

## ⚠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| Docker not running | Start Docker Desktop |
| Can't connect to DB | `docker ps \| grep postgres` |
| Module not found | `source venv/bin/activate` |
| Tests fail | Ensure backend is running |

---

## ✅ Next Steps

1. ✅ **Test now** - Follow steps above
2. 🔄 **Add auto-checks** - Background worker (40% remaining)
3. 🎨 **Build UI** - Frontend dashboard
4. 🔔 **Add alerts** - Email/Slack notifications

---

## 📖 Full Docs

- **Complete Guide**: `docs/MONITORING_SYSTEM.md`
- **Test Guide**: `docs/MONITORING_TEST_GUIDE.md`
- **Summary**: `docs/MONITORING_IMPLEMENTATION_SUMMARY.md`
- **Project Status**: `docs/DEVELOPMENT_PHASES.md`

---

## 💡 Tips

- All health checks run **concurrently** (fast!)
- Check interval: Internal=60s, External=300s
- Auto-restart triggers at 5 minutes down
- Logs kept for 7 days by default
- Use `jq` for pretty JSON: `| jq`

**Status**: ✅ **60% Complete** - Ready for testing!
