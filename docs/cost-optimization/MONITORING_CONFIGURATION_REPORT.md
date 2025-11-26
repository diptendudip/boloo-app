# Boloo App - Monitoring Configuration Report

**Date:** November 22, 2025
**Resource Group:** boloo-production-rg
**Subscription:** 417b3ad6-5fc1-47a3-917d-21cf4e3eddfc

---

## Executive Summary

✅ **Status:** Monitoring and alerts fully configured with email notifications

**Key Achievements:**
- 8 metric alerts configured and active
- Email notification action group created
- Database firewall security issue resolved
- Application Insights operational
- All alerts connected to notification system

**Critical Security Fix:**
- ❌ Removed dangerous firewall rule allowing all IPs (0.0.0.0 - 255.255.255.255)
- ✅ Implemented Azure-only database access

---

## 1. Application Insights

### Configuration Status: ✅ Active

**Resource Details:**
```yaml
Name: boloo-backend-insights
Resource Group: boloo-production-rg
Location: South India
Application Type: Web
Retention Period: 90 days
Instrumentation Key: 33aad16e-9560-4cf8-8ced-b42fde933cf2
Application ID: e695fd11-449b-42fb-b440-91ac421d883a
```

**Connection String:**
```
InstrumentationKey=33aad16e-9560-4cf8-8ced-b42fde933cf2;IngestionEndpoint=https://southindia-0.in.applicationinsights.azure.com/;LiveEndpoint=https://southindia.livediagnostics.monitor.azure.com/;ApplicationId=e695fd11-449b-42fb-b440-91ac421d883a
```

**Azure Portal Link:**
```
https://portal.azure.com/#@1cad08ec-88ce-4fad-861f-73474b7eb2d7/resource/subscriptions/417b3ad6-5fc1-47a3-917d-21cf4e3eddfc/resourceGroups/boloo-production-rg/providers/microsoft.insights/components/boloo-backend-insights/overview
```

---

## 2. Alert Configuration

### Summary: ✅ 8 Alerts Active with Notifications

All alerts are configured with:
- Evaluation frequency: 1 minute
- Window size: 5 minutes
- Connected to email notification action group

### Backend API Alerts (4)

#### 2.1 HTTP 5xx Server Errors
```yaml
Alert Name: boloo-http-5xx-errors
Metric: Http5xx
Condition: Count > 10 in 5 minutes
Severity: 2 (Warning)
Action: Email to admin@boloo.com
Status: ✅ Active
```

**Purpose:** Detect server-side errors indicating backend issues

#### 2.2 High Response Time
```yaml
Alert Name: boloo-high-response-time
Metric: HttpResponseTime
Condition: Average > 5 seconds in 5 minutes
Severity: 2 (Warning)
Action: Email to admin@boloo.com
Status: ✅ Active
```

**Purpose:** Identify performance degradation affecting user experience

#### 2.3 High CPU Usage
```yaml
Alert Name: boloo-high-cpu
Metric: CpuTime
Condition: Total > 240 seconds in 5 minutes (80% utilization)
Severity: 2 (Warning)
Action: Email to admin@boloo.com
Status: ✅ Active
```

**Purpose:** Detect resource exhaustion requiring scaling

#### 2.4 HTTP 4xx Client Errors
```yaml
Alert Name: boloo-http-4xx-errors
Metric: Http4xx
Condition: Total > 50 in 5 minutes
Severity: 3 (Informational)
Action: Email to admin@boloo.com
Status: ✅ Active
```

**Purpose:** Monitor client-side errors (authentication, validation, etc.)

### Database Alerts (4)

#### 2.5 Database CPU Usage
```yaml
Alert Name: boloo-db-cpu-alert
Metric: cpu_percent
Condition: Average > 80%
Severity: 2 (Warning)
Action: Email to admin@boloo.com
Status: ✅ Active
```

**Purpose:** Prevent database performance degradation

#### 2.6 Database Memory Usage
```yaml
Alert Name: boloo-db-memory-alert
Metric: memory_percent
Condition: Average > 85%
Severity: 2 (Warning)
Action: Email to admin@boloo.com
Status: ✅ Active
```

**Purpose:** Detect memory pressure requiring investigation

#### 2.7 Active Database Connections
```yaml
Alert Name: boloo-db-connections-alert
Metric: active_connections
Condition: Average > 80 connections
Severity: 3 (Informational)
Action: Email to admin@boloo.com
Status: ✅ Active
```

**Purpose:** Monitor connection pool utilization

#### 2.8 Database Connection Failures
```yaml
Alert Name: boloo-db-failed-connections
Metric: connections_failed
Condition: Total > 10 in 5 minutes
Severity: 2 (Warning)
Action: Email to admin@boloo.com
Status: ✅ Active
```

**Purpose:** Identify authentication or network issues

---

## 3. Action Group Configuration

### Status: ✅ Created and Connected

**Action Group Details:**
```yaml
Name: boloo-alert-notifications
Short Name: BolooAlert
Resource Group: boloo-production-rg
Status: Enabled
```

**Email Receivers:**
```yaml
- Name: AdminEmail
  Address: admin@boloo.com
  Status: ✅ Enabled
```

**Connected Alerts:** All 8 metric alerts

**Resource ID:**
```
/subscriptions/417b3ad6-5fc1-47a3-917d-21cf4e3eddfc/resourceGroups/boloo-production-rg/providers/microsoft.insights/actionGroups/boloo-alert-notifications
```

### How to Add More Recipients

**Add email recipient:**
```bash
az monitor action-group update \
  --resource-group boloo-production-rg \
  --name boloo-alert-notifications \
  --add-action email DevTeam YOUR_EMAIL@example.com
```

**Add SMS notification:**
```bash
az monitor action-group update \
  --resource-group boloo-production-rg \
  --name boloo-alert-notifications \
  --add-action sms DevLead 91 YOUR_PHONE_NUMBER
```

---

## 4. Database Security Configuration

### Status: ✅ Security Improved

**Critical Security Issue Resolved:**

**BEFORE (INSECURE):**
```
Rule: AllowAll_2025-11-21_15-10-4
Start IP: 0.0.0.0
End IP: 255.255.255.255
Status: ❌ ALLOWS ENTIRE INTERNET - CRITICAL SECURITY RISK
```

**AFTER (SECURE):**
```
Rule: AllowAzureServices
Start IP: 0.0.0.0
End IP: 0.0.0.0
Status: ✅ Allows only Azure internal services
```

### Database Configuration

**Resource Details:**
```yaml
Database Name: boloo-database
Server Type: PostgreSQL Flexible Server
Version: PostgreSQL 14.19
SKU: Standard_B1ms (Burstable)
Storage: 32 GB (P4 tier)
Location: Central India
Availability Zone: 2
```

**Security Features:**
- ✅ SSL/TLS Enforced (Azure default)
- ✅ Password Authentication Enabled
- ✅ Firewall restricted to Azure services
- ✅ Backup retention: 7 days
- ❌ Active Directory Auth: Disabled
- ❌ Geo-redundant backup: Disabled (cost optimization)
- ❌ High Availability: Disabled (cost optimization)

**Backend API Outbound IPs (for reference):**
```
52.172.55.168
13.71.112.41
13.71.124.204
13.71.115.16
13.71.122.35
```

### Current Firewall Rules

```bash
# View current rules
az postgres flexible-server firewall-rule list \
  --resource-group boloo-production-rg \
  --name boloo-database \
  --output table
```

**Output:**
```
Name               StartIpAddress  EndIpAddress
-----------------  --------------  --------------
AllowAzureServices 0.0.0.0         0.0.0.0
```

---

## 5. Available Metrics

### Backend API Metrics

| Metric Name | Unit | Current Alert | Description |
|------------|------|---------------|-------------|
| CpuTime | Seconds | ✅ > 240s | Total CPU time consumed |
| Http5xx | Count | ✅ > 10 | Server errors |
| Http4xx | Count | ✅ > 50 | Client errors |
| HttpResponseTime | Seconds | ✅ > 5s | Average response time |
| MemoryWorkingSet | Bytes | ⚠️ Recommended | Current memory usage |
| Requests | Count | - | Total HTTP requests |
| Http2xx | Count | - | Successful responses |
| BytesReceived | Bytes | - | Incoming bandwidth |
| BytesSent | Bytes | - | Outgoing bandwidth |

### Database Metrics

| Metric Name | Unit | Current Alert | Description |
|------------|------|---------------|-------------|
| cpu_percent | Percent | ✅ > 80% | CPU utilization |
| memory_percent | Percent | ✅ > 85% | Memory utilization |
| active_connections | Count | ✅ > 80 | Current active connections |
| connections_failed | Count | ✅ > 10 | Failed connection attempts |
| connections_succeeded | Count | - | Successful connections |
| cpu_credits_consumed | Count | - | CPU credits used (burstable) |
| cpu_credits_remaining | Count | - | CPU credits available |
| max_connections | Count | - | Maximum allowed connections |

---

## 6. Cost Monitoring

### Status: ⚠️ Limited (Subscription Type)

**Budget Configuration:**
```
ERROR: Cost Management supports only Enterprise Agreement, Web direct and
Microsoft Customer Agreement offer types.
Current Offer: MS-AZR-0036P (Free Trial/MSDN)
```

**Workaround:**
- Monitor costs manually via Azure Portal
- Set up custom alerts when subscription type changes
- Use Azure Cost Analysis in portal

**Current Approximate Monthly Costs:**
```
Backend API (B1): ~$13/month
Database (B1ms): ~$12/month
App Insights: Free tier (limited data)
Static Web App: Free tier
Total Estimated: ~$25/month
```

---

## 7. Logging Configuration

### Web Server Logging: ✅ Enabled

**Backend API Logging:**
```bash
az webapp log config \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --application-logging filesystem \
  --level information \
  --detailed-error-messages true \
  --failed-request-tracing true
```

**Current Configuration:**
- Web Server Logging: Filesystem (3 days retention)
- Detailed Error Messages: ✅ Enabled
- Failed Request Tracing: ✅ Enabled
- Application Logging: ⚠️ Set to filesystem (consider upgrading to blob storage for production)

### Log Streaming

**View live logs:**
```bash
az webapp log tail \
  --name boloo-backend-api \
  --resource-group boloo-production-rg
```

**Download logs:**
```bash
az webapp log download \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --log-file boloo-logs-$(date +%Y%m%d).zip
```

---

## 8. Recommended Next Steps

### Immediate (Optional)
1. **Add SMS notifications** to action group for critical alerts
2. **Implement health check endpoint** in backend API
3. **Integrate Application Insights SDK** for custom telemetry

### Short-term
1. **Create availability tests** (ping tests) for web app and API
2. **Setup custom dashboards** in Azure Portal
3. **Document performance baselines** after initial production usage
4. **Add specific admin IPs** to database firewall if needed

### Long-term
1. **Implement distributed tracing** with App Insights
2. **Setup user analytics** and session tracking
3. **Create custom KQL queries** for advanced analytics
4. **Consider Application Gateway** with WAF for enhanced security

---

## 9. Testing and Verification

### Verify Alerts Are Working

**List all configured alerts:**
```bash
az monitor metrics alert list \
  --resource-group boloo-production-rg \
  --output table
```

**Expected Output:**
```
Description                                                 Enabled    Name
----------------------------------------------------------  ---------  ---------------------------
Alert when HTTP 5xx errors exceed 10 in 5 minutes           True       boloo-http-5xx-errors
Alert when average response time exceeds 5 seconds          True       boloo-high-response-time
Alert when CPU time exceeds 240 seconds                     True       boloo-high-cpu
Alert when HTTP 4xx errors exceed 50 in 5 minutes           True       boloo-http-4xx-errors
Alert when database CPU exceeds 80%                         True       boloo-db-cpu-alert
Alert when database memory exceeds 85%                      True       boloo-db-memory-alert
Alert when active database connections exceed 80            True       boloo-db-connections-alert
Alert when database connection failures exceed 10           True       boloo-db-failed-connections
```

### Test Email Notifications

**Trigger a test notification:**
```bash
# This will send a test email to admin@boloo.com
az monitor action-group test-notifications create \
  --action-group-name boloo-alert-notifications \
  --resource-group boloo-production-rg \
  --notification-type Email \
  --receiver-name AdminEmail
```

### Check Metrics

**View recent backend metrics:**
```bash
az monitor metrics list \
  --resource "/subscriptions/417b3ad6-5fc1-47a3-917d-21cf4e3eddfc/resourceGroups/boloo-production-rg/providers/Microsoft.Web/sites/boloo-backend-api" \
  --metric Http5xx,Http4xx,HttpResponseTime \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --interval PT5M
```

**View database connection metrics:**
```bash
az monitor metrics list \
  --resource "/subscriptions/417b3ad6-5fc1-47a3-917d-21cf4e3eddfc/resourceGroups/boloo-production-rg/providers/Microsoft.DBforPostgreSQL/flexibleServers/boloo-database" \
  --metric active_connections,connections_failed \
  --interval PT5M
```

---

## 10. Security Summary

### Critical Security Issues Resolved

✅ **Database Firewall - FIXED**
- **Before:** Database accessible from entire internet (0.0.0.0 - 255.255.255.255)
- **After:** Restricted to Azure services only
- **Risk Mitigated:** Unauthorized access, data breach, DDoS attacks

### Current Security Posture

**Strengths:**
- ✅ SSL/TLS enforced on database
- ✅ Firewall properly configured
- ✅ Application Insights collecting security events
- ✅ Monitoring and alerting active
- ✅ Audit trail via Azure activity logs

**Areas for Improvement:**
- ⚠️ Consider Azure Active Directory authentication for database
- ⚠️ Implement Application Gateway with WAF
- ⚠️ Enable Azure Defender for enhanced threat protection (paid)
- ⚠️ Setup Azure Private Link for database (paid, enhanced security)

---

## 11. Documentation References

**Main Monitoring Guide:**
```
/Users/diptendu/boloo app/boloo-app/docs/MONITORING_SETUP.md
```

**Related Documentation:**
- Cloud Architecture: `/docs/CLOUD_ARCHITECTURE.md`
- Deployment Guide: `/docs/PRODUCTION_DEPLOYMENT_CHECKLIST.md`
- Troubleshooting: `/docs/CLOUD_TROUBLESHOOTING.md`

**Azure Documentation:**
- [Application Insights](https://docs.microsoft.com/azure/azure-monitor/app/app-insights-overview)
- [Azure Monitor Alerts](https://docs.microsoft.com/azure/azure-monitor/alerts/alerts-overview)
- [PostgreSQL Flexible Server](https://docs.microsoft.com/azure/postgresql/flexible-server/overview)

---

## Appendix A: Quick Reference Commands

### View All Resources
```bash
az resource list \
  --resource-group boloo-production-rg \
  --output table
```

### Check Alert Status
```bash
az monitor metrics alert show \
  --resource-group boloo-production-rg \
  --name boloo-http-5xx-errors
```

### View Action Group
```bash
az monitor action-group show \
  --resource-group boloo-production-rg \
  --name boloo-alert-notifications
```

### Check Database Firewall
```bash
az postgres flexible-server firewall-rule list \
  --resource-group boloo-production-rg \
  --name boloo-database \
  --output table
```

### Stream Logs
```bash
az webapp log tail \
  --name boloo-backend-api \
  --resource-group boloo-production-rg
```

---

**Report Generated:** November 22, 2025
**Next Review:** December 22, 2025
**Maintained By:** DevOps Team
