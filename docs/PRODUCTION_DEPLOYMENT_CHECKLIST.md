# Production Deployment Checklist

## Overview

This comprehensive checklist ensures a secure, performant, and reliable production deployment of the Boloo application. Follow each section carefully before launching to production.

## Table of Contents

1. [Pre-Launch Checklist](#pre-launch-checklist)
2. [Security Hardening](#security-hardening)
3. [Performance Optimization](#performance-optimization)
4. [Monitoring and Alerting](#monitoring-and-alerting)
5. [Backup Verification](#backup-verification)
6. [Domain and SSL](#domain-and-ssl)
7. [Load Testing](#load-testing)
8. [Database Readiness](#database-readiness)
9. [Third-Party Integrations](#third-party-integrations)
10. [Documentation](#documentation)
11. [Go-Live Procedure](#go-live-procedure)

---

## Pre-Launch Checklist

### Environment Configuration

- [ ] **Production environment variables configured**
  ```bash
  # Verify all required environment variables are set
  az webapp config appsettings list \
    --name boloo-backend-api \
    --resource-group boloo-rg
  ```
  Required variables:
  - [ ] `NODE_ENV=production`
  - [ ] `DATABASE_URL` (from Key Vault)
  - [ ] `REDIS_URL` (from Key Vault)
  - [ ] `JWT_SECRET` (from Key Vault)
  - [ ] `STRIPE_API_KEY` (from Key Vault)
  - [ ] `SENDGRID_API_KEY` (from Key Vault)
  - [ ] `AZURE_STORAGE_CONNECTION_STRING` (from Key Vault)
  - [ ] `API_BASE_URL=https://api.bultoo.com`

- [ ] **Key Vault secrets configured**
  ```bash
  # List all secrets
  az keyvault secret list --vault-name boloo-keyvault

  # Verify secret references in App Service
  az webapp config appsettings list \
    --name boloo-backend-api \
    --resource-group boloo-rg \
    --query "[?contains(value, 'keyvault')]"
  ```

- [ ] **Managed Identity enabled and configured**
  ```bash
  # Enable system-assigned managed identity
  az webapp identity assign \
    --name boloo-backend-api \
    --resource-group boloo-rg

  # Grant Key Vault access
  az keyvault set-policy \
    --name boloo-keyvault \
    --object-id <managed-identity-id> \
    --secret-permissions get list
  ```

### Infrastructure Validation

- [ ] **All Azure resources provisioned**
  - [ ] App Service (boloo-backend-api)
  - [ ] App Service Plan (P1V2 or higher)
  - [ ] PostgreSQL Flexible Server
  - [ ] Redis Cache
  - [ ] Storage Account
  - [ ] Key Vault
  - [ ] Application Insights
  - [ ] Log Analytics Workspace

- [ ] **Resource tags applied**
  ```bash
  # Apply standard tags
  az resource tag \
    --tags Environment=Production Project=Boloo CostCenter=Engineering \
    --ids <resource-id>
  ```
  Required tags:
  - [ ] Environment: Production
  - [ ] Project: Boloo
  - [ ] CostCenter: Engineering
  - [ ] Owner: [Team/Person]

- [ ] **Virtual Network configured (if applicable)**
  - [ ] VNet created with appropriate subnets
  - [ ] Network Security Groups (NSG) configured
  - [ ] Service endpoints enabled
  - [ ] Private endpoints configured

### Application Validation

- [ ] **Latest code deployed to staging**
  ```bash
  # Deploy to staging slot
  az webapp deployment source config-zip \
    --name boloo-backend-api \
    --resource-group boloo-rg \
    --slot staging \
    --src ./deploy.zip
  ```

- [ ] **Database migrations applied**
  ```bash
  # Run migrations on production database (test on staging first!)
  npm run db:migrate:prod

  # Verify schema version
  npm run db:version
  ```

- [ ] **Seed data loaded (if needed)**
  ```bash
  # Load essential reference data
  npm run db:seed:production
  ```

- [ ] **All tests passing**
  - [ ] Unit tests: `npm run test:unit`
  - [ ] Integration tests: `npm run test:integration`
  - [ ] E2E tests: `npm run test:e2e`
  - [ ] API tests: `npm run test:api`

---

## Security Hardening

### Authentication & Authorization

- [ ] **JWT configuration secured**
  - [ ] Strong secret key (minimum 256 bits)
  - [ ] Appropriate token expiration (15-60 minutes)
  - [ ] Refresh token rotation enabled
  - [ ] Token revocation mechanism tested

- [ ] **Password policies enforced**
  - [ ] Minimum length: 8 characters
  - [ ] Complexity requirements: uppercase, lowercase, numbers, symbols
  - [ ] Password hashing: bcrypt with cost factor ≥ 12
  - [ ] Account lockout after 5 failed attempts

- [ ] **Role-Based Access Control (RBAC) configured**
  - [ ] User roles defined (customer, merchant, admin)
  - [ ] Permission boundaries tested
  - [ ] Admin access restricted and monitored

### API Security

- [ ] **HTTPS enforced**
  ```bash
  # Enable HTTPS only
  az webapp update \
    --name boloo-backend-api \
    --resource-group boloo-rg \
    --https-only true
  ```

- [ ] **CORS configured properly**
  ```javascript
  // In production config
  const corsOptions = {
    origin: [
      'https://admin.bultoo.com',
      'https://www.bultoo.com'
    ],
    credentials: true,
    maxAge: 3600
  };
  ```

- [ ] **Rate limiting enabled**
  - [ ] API rate limits: 100 requests/minute per IP
  - [ ] Authentication rate limits: 5 attempts/minute
  - [ ] Rate limit headers included in responses

- [ ] **Input validation implemented**
  - [ ] Request body validation (Joi/Yup)
  - [ ] SQL injection prevention (parameterized queries)
  - [ ] XSS prevention (input sanitization)
  - [ ] CSRF protection (tokens)

- [ ] **Security headers configured**
  ```javascript
  // helmet.js middleware configuration
  {
    contentSecurityPolicy: true,
    hsts: { maxAge: 31536000 },
    frameguard: { action: 'deny' },
    noSniff: true,
    xssFilter: true
  }
  ```

### Database Security

- [ ] **SSL/TLS enforced for database connections**
  ```bash
  # Verify SSL requirement
  az postgres flexible-server parameter show \
    --server-name boloo-postgres-server \
    --resource-group boloo-rg \
    --name require_secure_transport
  ```

- [ ] **Database user permissions restricted**
  ```sql
  -- Application user should have minimal permissions
  GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
  REVOKE CREATE ON SCHEMA public FROM app_user;
  ```

- [ ] **Database firewall rules configured**
  - [ ] Only allow Azure services (App Service, Functions)
  - [ ] No public internet access
  - [ ] Admin access from specific IPs only

- [ ] **Sensitive data encrypted**
  - [ ] Encryption at rest enabled (TDE)
  - [ ] Encryption in transit (SSL)
  - [ ] Sensitive columns encrypted (credit cards, SSN)

### Storage Security

- [ ] **Storage account access restricted**
  - [ ] Public access disabled
  - [ ] Shared Access Signatures (SAS) with expiration
  - [ ] Managed Identity for application access
  - [ ] Firewall rules configured

- [ ] **Blob soft delete enabled**
  ```bash
  az storage blob service-properties delete-policy update \
    --account-name boloostorage \
    --enable true \
    --days-retained 7
  ```

### Key Vault Security

- [ ] **Access policies configured**
  - [ ] Managed Identity has Get/List permissions only
  - [ ] Admin access limited to specific users
  - [ ] No direct secret values in code or config

- [ ] **Soft delete and purge protection enabled**
  ```bash
  az keyvault update \
    --name boloo-keyvault \
    --enable-soft-delete true \
    --enable-purge-protection true
  ```

- [ ] **Access logging enabled**
  - [ ] Diagnostic settings configured
  - [ ] Logs sent to Log Analytics
  - [ ] Alerts for unauthorized access attempts

### Security Scanning

- [ ] **Vulnerability scan completed**
  - [ ] Dependencies audited: `npm audit`
  - [ ] High/Critical vulnerabilities fixed
  - [ ] OWASP Top 10 checklist reviewed

- [ ] **Code security review**
  - [ ] Static code analysis (SonarQube/CodeQL)
  - [ ] Secrets not committed to repository
  - [ ] No hardcoded credentials

- [ ] **Penetration testing (if applicable)**
  - [ ] Third-party security assessment
  - [ ] Vulnerabilities addressed
  - [ ] Report documented

---

## Performance Optimization

### Application Performance

- [ ] **Caching strategy implemented**
  - [ ] Redis cache for sessions
  - [ ] API response caching
  - [ ] Static asset caching (CDN)
  - [ ] Cache invalidation strategy tested

- [ ] **Database queries optimized**
  ```bash
  # Analyze slow queries
  SELECT query, calls, total_time, mean_time
  FROM pg_stat_statements
  ORDER BY mean_time DESC
  LIMIT 10;
  ```
  - [ ] Indexes created for frequently queried columns
  - [ ] N+1 queries eliminated
  - [ ] Query execution plans reviewed
  - [ ] Connection pooling configured

- [ ] **Code optimizations applied**
  - [ ] Async/await used appropriately
  - [ ] Memory leaks checked and fixed
  - [ ] Bundle size optimized (frontend)
  - [ ] Lazy loading implemented

### Infrastructure Performance

- [ ] **Auto-scaling configured**
  ```bash
  # Configure auto-scale rules
  az monitor autoscale create \
    --resource-group boloo-rg \
    --resource boloo-backend-api \
    --resource-type Microsoft.Web/serverfarms \
    --min-count 2 \
    --max-count 10 \
    --count 2
  ```
  Rules configured:
  - [ ] Scale out when CPU > 70%
  - [ ] Scale out when memory > 80%
  - [ ] Scale in when CPU < 30%

- [ ] **CDN configured**
  - [ ] Static assets served via CDN
  - [ ] Appropriate cache headers set
  - [ ] Compression enabled (gzip/brotli)

- [ ] **Database connection pooling**
  ```javascript
  // PostgreSQL pool configuration
  const pool = new Pool({
    max: 20, // Maximum connections
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 2000
  });
  ```

### Monitoring Baselines

- [ ] **Performance baselines established**
  - [ ] Average response time: < 200ms
  - [ ] P95 response time: < 500ms
  - [ ] P99 response time: < 1000ms
  - [ ] Error rate: < 0.1%
  - [ ] Availability: > 99.9%

---

## Monitoring and Alerting

### Application Insights

- [ ] **Application Insights configured**
  ```bash
  # Configure Application Insights
  az monitor app-insights component create \
    --app boloo-appinsights \
    --location eastus \
    --resource-group boloo-rg
  ```

- [ ] **Instrumentation key configured**
  - [ ] App Service instrumentation enabled
  - [ ] Custom events tracked
  - [ ] Dependencies monitored

- [ ] **Telemetry validated**
  - [ ] Request telemetry flowing
  - [ ] Exception tracking working
  - [ ] Custom metrics logged
  - [ ] User analytics configured

### Log Analytics

- [ ] **Log Analytics workspace configured**
  - [ ] All resources logging to workspace
  - [ ] Log retention set (30-90 days)
  - [ ] Diagnostic settings enabled

- [ ] **Key queries saved**
  ```kusto
  // Error tracking query
  AppServiceConsoleLogs
  | where LogLevel == "Error"
  | summarize count() by ExceptionType, bin(TimeGenerated, 1h)

  // Performance query
  AppRequests
  | summarize avg(DurationMs), percentile(DurationMs, 95)
    by bin(TimeGenerated, 5m)
  ```

### Alerts Configuration

- [ ] **Critical alerts configured**
  - [ ] **API Availability < 99%**
    ```bash
    az monitor metrics alert create \
      --name "API-Availability-Low" \
      --resource-group boloo-rg \
      --scopes <app-service-id> \
      --condition "avg availability < 99" \
      --window-size 5m \
      --evaluation-frequency 1m
    ```

  - [ ] **Error rate > 5%**
  - [ ] **Response time P95 > 1000ms**
  - [ ] **Database connection failures**
  - [ ] **SSL certificate expiration < 30 days**

- [ ] **Warning alerts configured**
  - [ ] CPU usage > 70%
  - [ ] Memory usage > 80%
  - [ ] Disk space > 85%
  - [ ] Failed backup
  - [ ] High Redis memory usage

- [ ] **Action groups configured**
  - [ ] Email notifications
  - [ ] SMS for critical alerts (optional)
  - [ ] Teams/Slack integration
  - [ ] PagerDuty integration (if applicable)

### Health Checks

- [ ] **Health check endpoint configured**
  ```javascript
  // /health endpoint
  app.get('/health', async (req, res) => {
    const health = {
      uptime: process.uptime(),
      status: 'healthy',
      timestamp: Date.now(),
      checks: {
        database: await checkDatabase(),
        redis: await checkRedis(),
        storage: await checkStorage()
      }
    };

    const status = Object.values(health.checks).every(c => c.status === 'healthy')
      ? 200 : 503;

    res.status(status).json(health);
  });
  ```

- [ ] **Health check interval configured**
  - [ ] App Service health check: 30 seconds
  - [ ] Unhealthy threshold: 3 consecutive failures
  - [ ] Health check path: `/health`

---

## Backup Verification

### Database Backups

- [ ] **Automated backups configured**
  ```bash
  # Verify backup configuration
  az postgres flexible-server backup show \
    --resource-group boloo-rg \
    --server-name boloo-postgres-server
  ```
  - [ ] Backup retention: 7 days minimum
  - [ ] Geo-redundant backup enabled
  - [ ] Point-in-time restore tested

- [ ] **Manual backup taken before deployment**
  ```bash
  # Create manual backup
  az postgres flexible-server backup create \
    --resource-group boloo-rg \
    --server-name boloo-postgres-server \
    --backup-name pre-prod-deployment-$(date +%Y%m%d)
  ```

- [ ] **Backup restoration tested**
  - [ ] Restore to test server verified
  - [ ] Restoration time documented (RTO)
  - [ ] Data integrity validated

### Storage Backups

- [ ] **Blob snapshot schedule configured**
  ```bash
  # Enable versioning and soft delete
  az storage account blob-service-properties update \
    --account-name boloostorage \
    --enable-versioning true \
    --enable-delete-retention true \
    --delete-retention-days 7
  ```

- [ ] **Backup storage account configured**
  - [ ] Geo-redundant storage (GRS)
  - [ ] Access tier appropriate for backups
  - [ ] Lifecycle policies configured

### Configuration Backups

- [ ] **Infrastructure as Code (IaC) committed**
  - [ ] ARM templates / Terraform files in Git
  - [ ] Environment-specific configurations
  - [ ] Secrets management documented

- [ ] **Application configuration exported**
  ```bash
  # Export App Service configuration
  az webapp config appsettings list \
    --name boloo-backend-api \
    --resource-group boloo-rg \
    > app-config-backup-$(date +%Y%m%d).json
  ```

---

## Domain and SSL

### Custom Domain Configuration

- [ ] **DNS records configured**
  - [ ] A record or CNAME for `api.bultoo.com`
  - [ ] CNAME for `admin.bultoo.com`
  - [ ] TXT record for domain verification
  - [ ] DNS propagation verified

- [ ] **Custom domain added to App Service**
  ```bash
  # Add custom domain
  az webapp config hostname add \
    --webapp-name boloo-backend-api \
    --resource-group boloo-rg \
    --hostname api.bultoo.com
  ```

- [ ] **Domain verification completed**
  ```bash
  # Verify domain
  nslookup api.bultoo.com
  dig api.bultoo.com
  ```

### SSL Certificate

- [ ] **SSL certificate provisioned**
  ```bash
  # Create managed certificate
  az webapp config ssl create \
    --name boloo-backend-api \
    --resource-group boloo-rg \
    --hostname api.bultoo.com
  ```

- [ ] **SSL binding configured**
  - [ ] SNI SSL type
  - [ ] Certificate bound to custom domain
  - [ ] HTTPS-only enforced

- [ ] **SSL verification**
  ```bash
  # Test SSL certificate
  echo | openssl s_client -servername api.bultoo.com \
    -connect api.bultoo.com:443 2>/dev/null | \
    openssl x509 -noout -dates

  # Check SSL Labs rating
  # Visit: https://www.ssllabs.com/ssltest/analyze.html?d=api.bultoo.com
  ```
  - [ ] Valid certificate
  - [ ] No browser warnings
  - [ ] SSL Labs grade: A or higher
  - [ ] Certificate auto-renewal configured

### Security Headers

- [ ] **HSTS enabled**
  ```javascript
  // Helmet configuration
  app.use(helmet.hsts({
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true
  }));
  ```

- [ ] **Security headers verified**
  ```bash
  # Check security headers
  curl -I https://api.bultoo.com
  ```
  Expected headers:
  - [ ] `Strict-Transport-Security`
  - [ ] `X-Content-Type-Options: nosniff`
  - [ ] `X-Frame-Options: DENY`
  - [ ] `Content-Security-Policy`

---

## Load Testing

### Test Environment

- [ ] **Staging environment matches production**
  - [ ] Same App Service Plan tier
  - [ ] Same database configuration
  - [ ] Production-like data volume

### Load Test Scenarios

- [ ] **Baseline load test**
  ```bash
  # Artillery load test configuration
  artillery run \
    --target https://staging-api.bultoo.com \
    --config baseline-test.yml
  ```
  Configuration:
  - [ ] 100 concurrent users
  - [ ] 10-minute duration
  - [ ] Expected: 0% error rate, P95 < 500ms

- [ ] **Peak load test**
  - [ ] 500 concurrent users
  - [ ] 30-minute duration
  - [ ] Expected: < 1% error rate, P95 < 1000ms

- [ ] **Stress test**
  - [ ] Gradually increase to 1000+ users
  - [ ] Identify breaking point
  - [ ] Document maximum capacity

- [ ] **Soak test (optional for critical apps)**
  - [ ] 200 concurrent users
  - [ ] 24-hour duration
  - [ ] Monitor for memory leaks

### Test Results

- [ ] **Performance metrics documented**
  ```
  Baseline Test Results:
  - Average Response Time: ___ms
  - P95 Response Time: ___ms
  - P99 Response Time: ___ms
  - Error Rate: ___%
  - Throughput: ___requests/sec
  - Resource Utilization: CPU __%, Memory ___%
  ```

- [ ] **Bottlenecks identified and addressed**
  - [ ] Database query optimization
  - [ ] Caching improvements
  - [ ] Auto-scaling tuned

- [ ] **Load test report generated**
  - [ ] Graphs and charts
  - [ ] Recommendations documented
  - [ ] Action items tracked

---

## Database Readiness

### Schema and Data

- [ ] **Database schema validated**
  - [ ] All migrations applied
  - [ ] Schema version documented
  - [ ] Rollback scripts prepared

- [ ] **Indexes optimized**
  ```sql
  -- Verify indexes
  SELECT schemaname, tablename, indexname
  FROM pg_indexes
  WHERE schemaname = 'public';

  -- Check for missing indexes
  SELECT * FROM pg_stat_user_tables
  WHERE seq_scan > 1000 AND idx_scan = 0;
  ```

- [ ] **Data validation**
  - [ ] Reference data loaded
  - [ ] Test data removed
  - [ ] Data integrity constraints verified

### Performance Tuning

- [ ] **Connection pooling configured**
  ```javascript
  const pool = new Pool({
    host: process.env.DB_HOST,
    database: process.env.DB_NAME,
    max: 20,
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 2000
  });
  ```

- [ ] **Query performance analyzed**
  ```sql
  -- Enable pg_stat_statements
  CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

  -- Analyze slow queries
  SELECT query, mean_time, calls
  FROM pg_stat_statements
  ORDER BY mean_time DESC
  LIMIT 20;
  ```

- [ ] **Database parameters tuned**
  - [ ] `shared_buffers`: 25% of RAM
  - [ ] `effective_cache_size`: 75% of RAM
  - [ ] `work_mem`: Appropriate for workload
  - [ ] `max_connections`: 100-200

### Backup and Recovery

- [ ] **Point-in-time restore tested**
  - [ ] Restore to 5 minutes ago verified
  - [ ] Restoration time documented

- [ ] **Failover tested (if using HA)**
  - [ ] Automatic failover verified
  - [ ] Application reconnection tested
  - [ ] Failover time documented

---

## Third-Party Integrations

### Payment Gateway (Stripe)

- [ ] **Production API keys configured**
  - [ ] Live API key in Key Vault
  - [ ] Test mode disabled
  - [ ] Webhook signing secret configured

- [ ] **Webhooks configured**
  ```bash
  # Verify webhook endpoint
  curl -X POST https://api.bultoo.com/webhooks/stripe \
    -H "Content-Type: application/json" \
    -d '{"test": "webhook"}'
  ```
  - [ ] Webhook URL: `https://api.bultoo.com/webhooks/stripe`
  - [ ] Events subscribed: payment_intent.succeeded, charge.failed
  - [ ] SSL verification enabled

- [ ] **Payment flow tested**
  - [ ] Test payment in staging
  - [ ] Refund tested
  - [ ] Webhook handling verified

### Email Service (SendGrid)

- [ ] **SendGrid API key configured**
  - [ ] Production API key in Key Vault
  - [ ] Sender authentication completed
  - [ ] Domain authentication (SPF, DKIM)

- [ ] **Email templates configured**
  - [ ] Welcome email
  - [ ] Order confirmation
  - [ ] Password reset
  - [ ] Receipt/invoice

- [ ] **Email delivery tested**
  - [ ] Test email sent successfully
  - [ ] Email lands in inbox (not spam)
  - [ ] Unsubscribe link works

### SMS Service (if applicable)

- [ ] **SMS provider configured (Twilio)**
  - [ ] Account SID and Auth Token in Key Vault
  - [ ] Phone number verified
  - [ ] Message templates created

- [ ] **SMS delivery tested**
  - [ ] OTP delivery verified
  - [ ] Notification delivery verified

### Analytics (if applicable)

- [ ] **Google Analytics configured**
  - [ ] Tracking ID added
  - [ ] Events tracked
  - [ ] Goals configured

- [ ] **Application Insights custom events**
  - [ ] Business events tracked (orders, signups)
  - [ ] Custom dimensions configured

---

## Documentation

### Technical Documentation

- [ ] **API documentation updated**
  - [ ] OpenAPI/Swagger spec current
  - [ ] Authentication documented
  - [ ] Error codes documented
  - [ ] Examples provided

- [ ] **Architecture documentation**
  - [ ] System architecture diagram
  - [ ] Data flow diagrams
  - [ ] Infrastructure diagram
  - [ ] Security architecture

- [ ] **Runbooks created**
  - [ ] Deployment procedure
  - [ ] Rollback procedure
  - [ ] Incident response
  - [ ] Common troubleshooting

### Operational Documentation

- [ ] **Configuration management**
  - [ ] Environment variables documented
  - [ ] Feature flags documented
  - [ ] Secrets rotation procedure

- [ ] **Monitoring and alerting**
  - [ ] Alert definitions
  - [ ] On-call rotation
  - [ ] Escalation procedures

- [ ] **Backup and recovery**
  - [ ] Backup schedule
  - [ ] Recovery procedures
  - [ ] RTO/RPO documented

### User Documentation

- [ ] **Admin user guide**
  - [ ] Login procedure
  - [ ] Common tasks
  - [ ] Troubleshooting

- [ ] **API integration guide** (for partners)
  - [ ] Authentication
  - [ ] API endpoints
  - [ ] Code examples

---

## Go-Live Procedure

### Pre-Deployment (T-24 hours)

- [ ] **Final code review**
  - [ ] All PRs merged
  - [ ] Code freeze initiated
  - [ ] Release notes prepared

- [ ] **Stakeholder notification**
  - [ ] Deployment schedule communicated
  - [ ] Maintenance window announced (if applicable)
  - [ ] Support team briefed

- [ ] **Pre-deployment backup**
  ```bash
  # Database backup
  az postgres flexible-server backup create \
    --name pre-deployment-backup \
    --resource-group boloo-rg \
    --server-name boloo-postgres-server

  # Configuration backup
  az webapp config appsettings list \
    --name boloo-backend-api \
    --resource-group boloo-rg \
    > config-backup.json
  ```

### Deployment (T-0)

- [ ] **Deploy to staging slot**
  ```bash
  # Deploy application
  az webapp deployment source config-zip \
    --name boloo-backend-api \
    --resource-group boloo-rg \
    --slot staging \
    --src ./deploy.zip
  ```

- [ ] **Run smoke tests on staging**
  - [ ] Health check: `curl https://boloo-backend-api-staging.azurewebsites.net/health`
  - [ ] API endpoints tested
  - [ ] Database connectivity verified

- [ ] **Swap to production**
  ```bash
  # Swap staging to production
  az webapp deployment slot swap \
    --name boloo-backend-api \
    --resource-group boloo-rg \
    --slot staging \
    --target-slot production
  ```

### Post-Deployment (T+1 hour)

- [ ] **Verify production health**
  ```bash
  # Check health endpoint
  curl https://api.bultoo.com/health

  # Monitor logs
  az webapp log tail \
    --name boloo-backend-api \
    --resource-group boloo-rg
  ```

- [ ] **Run production smoke tests**
  - [ ] User login flow
  - [ ] Order creation flow
  - [ ] Payment processing
  - [ ] Email/SMS delivery

- [ ] **Monitor metrics**
  - [ ] Error rate < 1%
  - [ ] Response time < 500ms (P95)
  - [ ] CPU usage normal
  - [ ] Memory usage stable

- [ ] **Database verification**
  ```sql
  -- Check active connections
  SELECT count(*) FROM pg_stat_activity;

  -- Check for errors
  SELECT * FROM pg_stat_database WHERE datname = 'boloo_production';
  ```

### Post-Deployment (T+24 hours)

- [ ] **Performance review**
  - [ ] Application Insights dashboard reviewed
  - [ ] No critical alerts
  - [ ] Resource utilization within limits

- [ ] **User feedback**
  - [ ] No major incidents reported
  - [ ] Support tickets reviewed

- [ ] **Documentation update**
  - [ ] Deployment notes added
  - [ ] Known issues documented
  - [ ] Rollback plan updated

### Rollback Procedure (if needed)

- [ ] **Identify issue**
  - [ ] Error logs analyzed
  - [ ] Root cause identified
  - [ ] Decision to rollback made

- [ ] **Execute rollback**
  ```bash
  # Swap back to previous slot
  az webapp deployment slot swap \
    --name boloo-backend-api \
    --resource-group boloo-rg \
    --slot production \
    --target-slot staging
  ```

- [ ] **Verify rollback**
  - [ ] Health check passes
  - [ ] Application functional
  - [ ] Metrics normal

- [ ] **Database rollback (if needed)**
  ```bash
  # Point-in-time restore
  az postgres flexible-server restore \
    --resource-group boloo-rg \
    --name boloo-postgres-server-restored \
    --source-server boloo-postgres-server \
    --restore-time "2024-01-15T10:00:00Z"
  ```

---

## Sign-Off Checklist

### Development Team

- [ ] **Lead Developer**: All code reviewed and approved
- [ ] **Backend Developer**: API endpoints tested and documented
- [ ] **Database Administrator**: Schema optimized and backups verified
- [ ] **DevOps Engineer**: Infrastructure configured and monitored

### Quality Assurance

- [ ] **QA Lead**: All tests passed (unit, integration, E2E)
- [ ] **QA Engineer**: User acceptance testing completed
- [ ] **Performance Tester**: Load testing completed and documented

### Operations

- [ ] **Operations Manager**: Runbooks reviewed and approved
- [ ] **Security Officer**: Security scan completed, vulnerabilities addressed
- [ ] **Compliance Officer**: Regulatory requirements met (if applicable)

### Business

- [ ] **Product Manager**: Features complete and documented
- [ ] **Project Manager**: Timeline and budget approved
- [ ] **Stakeholder**: Business requirements met

---

## Post-Launch Monitoring (Week 1)

### Daily Checks

- [ ] **Health dashboard reviewed**
- [ ] **Error logs analyzed**
- [ ] **Performance metrics checked**
- [ ] **User feedback reviewed**
- [ ] **Support tickets triaged**

### Weekly Review

- [ ] **Incident report generated**
- [ ] **Performance trends analyzed**
- [ ] **Cost analysis reviewed**
- [ ] **Optimization opportunities identified**
- [ ] **Lessons learned documented**

---

## Emergency Contacts

```
On-Call Rotation:
- Primary: [Name] - [Phone] - [Email]
- Secondary: [Name] - [Phone] - [Email]
- Escalation: [Name] - [Phone] - [Email]

Vendor Support:
- Azure Support: https://portal.azure.com (Support + troubleshooting)
- Stripe Support: support@stripe.com
- SendGrid Support: support@sendgrid.com

Internal Contacts:
- DevOps Team: devops@company.com
- Security Team: security@company.com
- Management: [Name] - [Email]
```

---

## Next Steps After Launch

1. **Monitor performance** for first 48 hours continuously
2. **Review and optimize** based on production data
3. **Schedule post-mortem** meeting (1 week after launch)
4. **Update documentation** based on lessons learned
5. **Plan next iteration** of features and improvements

---

## Additional Resources

- [Domain Configuration Guide](./DOMAIN_CONFIGURATION_GUIDE.md)
- [Cloud Architecture](./CLOUD_ARCHITECTURE.md)
- [Environment Setup](./ENVIRONMENT_SETUP.md)
- [Development Roadmap](./DEVELOPMENT_ROADMAP.md)

