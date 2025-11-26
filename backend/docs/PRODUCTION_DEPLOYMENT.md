# Production Deployment Guide - Boloo Backend

## Overview
This guide covers production deployment for 100 concurrent users with optimal performance and reliability.

## System Requirements

### Recommended Azure Tier
- **B2 Basic** (3.5GB RAM, 2 vCPU) - Recommended for 100 users
- **B1 Basic** (1.75GB RAM, 1 vCPU) - Minimum (reduce workers to 1)

### Configuration for 100 Users
- **Workers**: 2 (configured in Dockerfile)
- **Connections**: ~50 per worker = 100 total
- **Memory**: ~1.5GB per worker = 3GB total
- **CPU**: 2 vCPU recommended

## Deployment Checklist

### 1. Environment Variables (CRITICAL)
Ensure these are set in production:

```bash
# Security (REQUIRED)
JWT_SECRET_KEY=<generate-with-secrets.token_urlsafe(32)>
APP_ENV=production
DEBUG=False

# Database (REQUIRED)
DATABASE_URL=postgresql://user:password@host:5432/boloo

# Azure Services (REQUIRED)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=<your-key>
AZURE_SPEECH_KEY=<your-key>
AZURE_SPEECH_REGION=centralindia

# Redis (REQUIRED)
REDIS_URL=redis://your-redis-host:6379/0

# CORS (REQUIRED)
ALLOWED_ORIGINS=https://your-frontend-domain.com

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
```

### 2. Docker Build & Deploy

```bash
# Build production image
docker build -t boloo-backend:production .

# Test locally
docker run -p 8000:8000 --env-file .env.production boloo-backend:production

# Push to Azure Container Registry
az acr login --name <your-registry>
docker tag boloo-backend:production <your-registry>.azurecr.io/boloo-backend:latest
docker push <your-registry>.azurecr.io/boloo-backend:latest
```

### 3. Database Migration

```bash
# Run migrations before deployment
alembic upgrade head

# Verify database connection
python -c "from app.database import engine; engine.connect()"
```

### 4. Health Checks

The application includes automatic health checks:
- **Endpoint**: `/health`
- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Start Period**: 60 seconds (allows app to warm up)
- **Retries**: 3

### 5. Worker Configuration

**For B2 Tier (3.5GB RAM):**
```dockerfile
ENV WEB_CONCURRENCY=2
ENV WORKERS=2
```

**For B1 Tier (1.75GB RAM):**
```dockerfile
ENV WEB_CONCURRENCY=1
ENV WORKERS=1
```

**For Scale-Out (B3+ or Premium):**
```dockerfile
ENV WEB_CONCURRENCY=4
ENV WORKERS=4
```

## Performance Optimization

### Memory Management
- Worker recycling: `--max-requests=1000` (prevents memory leaks)
- Preloading: `--preload` (better memory efficiency)
- Graceful shutdown: `--graceful-timeout=30`

### Connection Pooling
SQLAlchemy pool settings in `app/database.py`:
```python
pool_size=10          # Base connections per worker
max_overflow=20       # Overflow connections
pool_recycle=3600     # Recycle connections hourly
```

### Caching
Redis caching enabled for:
- User sessions
- API responses (10-minute TTL)
- LLM results (30-minute TTL)

## Monitoring

### Key Metrics to Monitor
1. **Response Time**: <200ms (p95)
2. **Error Rate**: <0.1%
3. **Memory Usage**: <80% of allocated
4. **CPU Usage**: <70% average
5. **Database Connections**: <80% of pool

### Azure Application Insights
Configure in Azure Portal:
- Application Insights resource
- Connection string in app settings
- Custom metrics dashboard

### Logging
All logs are JSON-formatted and sent to stdout/stderr:
```json
{
  "timestamp": "2025-01-23T10:30:00Z",
  "level": "INFO",
  "message": "Request processed",
  "request_id": "abc123",
  "duration_ms": 45
}
```

## Security Best Practices

### 1. Secrets Management
- Use Azure Key Vault for sensitive data
- Never commit `.env` files
- Rotate keys every 90 days

### 2. Network Security
- Enable HTTPS only
- Configure Azure Firewall rules
- Use Private Endpoints for database

### 3. Input Validation
All endpoints validate:
- Request size limits
- Content-Type headers
- SQL injection prevention
- XSS protection

## Scaling Strategy

### Horizontal Scaling (Recommended)
1. Add more App Service instances
2. Use Azure Load Balancer
3. Configure session affinity (sticky sessions)

### Vertical Scaling
1. B1 → B2: Double capacity (100 → 200 users)
2. B2 → B3: 4x capacity (200 → 400 users)
3. B3 → S1: Premium features + autoscaling

## Disaster Recovery

### Backup Strategy
1. **Database**: Daily automated backups (Azure PostgreSQL)
2. **Files**: Azure Blob Storage with geo-redundancy
3. **Configuration**: Infrastructure as Code (Terraform/ARM)

### Recovery Time Objective (RTO)
- Critical services: <1 hour
- Full system: <4 hours

### Recovery Point Objective (RPO)
- Database: <5 minutes (continuous backup)
- Files: <1 hour

## Cost Optimization

### Expected Monthly Costs (100 Users)
- App Service B2: $70/month
- PostgreSQL Basic: $30/month
- Redis Basic: $16/month
- Azure OpenAI: ~$20/month (usage-based)
- Azure Speech: ~$10/month (usage-based)
- **Total**: ~$150/month

### Cost Alerts
Configure in `app/config.py`:
```python
AZURE_COST_LIMIT_USD=20.0
AZURE_COST_WARNING_THRESHOLD=0.8
```

## Troubleshooting

### High Memory Usage
1. Check worker count: `ps aux | grep gunicorn`
2. Reduce workers if needed
3. Enable worker recycling

### Slow Response Times
1. Check database query performance
2. Verify Redis connectivity
3. Review Azure OpenAI latency

### Connection Pool Exhausted
1. Increase `pool_size` in database config
2. Reduce connection lifetime
3. Add read replicas

## Support Contacts
- DevOps: diptendudip@gmail.com
- Azure Cost Alerts: diptendudip@gmail.com
