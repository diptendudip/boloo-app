# Boloo App - Monitoring & Observability Setup Guide

**Last Updated:** November 22, 2025
**Status:** ✅ Fully Configured with Notifications & Database Monitoring

---

## 📋 Table of Contents

1. [Azure Application Insights](#azure-application-insights)
2. [Log Analytics Configuration](#log-analytics-configuration)
3. [Alert Rules Setup](#alert-rules-setup)
4. [Performance Metrics](#performance-metrics)
5. [Error Tracking](#error-tracking)
6. [Cost Monitoring](#cost-monitoring)
7. [Uptime Monitoring](#uptime-monitoring)
8. [Dashboard Setup](#dashboard-setup)

---

## 🔍 Azure Application Insights

### Current Configuration

**Resource Details:**
- **Name:** boloo-backend-insights
- **Resource Group:** boloo-production-rg
- **Location:** South India
- **Application Type:** Web
- **Retention Period:** 90 days
- **Status:** ✅ Created and configured

**Connection Details:**
```
Instrumentation Key: 33aad16e-9560-4cf8-8ced-b42fde933cf2
Application ID: e695fd11-449b-42fb-b440-91ac421d883a
Connection String: InstrumentationKey=33aad16e-9560-4cf8-8ced-b42fde933cf2;IngestionEndpoint=https://southindia-0.in.applicationinsights.azure.com/;LiveEndpoint=https://southindia.livediagnostics.monitor.azure.com/;ApplicationId=e695fd11-449b-42fb-b440-91ac421d883a
```

### Setup Application Insights SDK

#### Backend API Integration

**1. Install Python SDK:**
```bash
cd "/Users/diptendu/boloo app/boloo-app/backend"

# Add to requirements.txt
echo "opencensus-ext-azure>=1.1.9" >> requirements.txt
echo "opencensus-ext-flask>=0.8.1" >> requirements.txt
echo "opencensus-ext-requests>=0.8.1" >> requirements.txt

# Install
pip install -r requirements.txt
```

**2. Configure in FastAPI app (`backend/app/main.py`):**
```python
from opencensus.ext.azure import metrics_exporter
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace import config_integration
import logging

# Add at app startup
APPINSIGHTS_KEY = os.getenv("APPLICATIONINSIGHTS_INSTRUMENTATION_KEY")

if APPINSIGHTS_KEY:
    # Configure trace integration
    config_integration.trace_integrations(['requests', 'logging'])

    # Setup exporter
    tracer = AzureExporter(
        connection_string=f"InstrumentationKey={APPINSIGHTS_KEY}"
    )

    # Setup metrics
    metrics_exporter_instance = metrics_exporter.new_metrics_exporter(
        connection_string=f"InstrumentationKey={APPINSIGHTS_KEY}"
    )

    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.addHandler(
        logging.handlers.RotatingFileHandler('app.log')
    )
```

**3. Add environment variable to Azure:**
```bash
az webapp config appsettings set \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --settings \
    APPLICATIONINSIGHTS_INSTRUMENTATION_KEY="33aad16e-9560-4cf8-8ced-b42fde933cf2" \
    APPLICATIONINSIGHTS_CONNECTION_STRING="InstrumentationKey=33aad16e-9560-4cf8-8ced-b42fde933cf2;IngestionEndpoint=https://southindia-0.in.applicationinsights.azure.com/"
```

#### Web Application Integration

**1. Install Next.js SDK:**
```bash
cd "/Users/diptendu/boloo app/boloo-app/web"
npm install @microsoft/applicationinsights-web
```

**2. Create instrumentation file (`web/lib/appInsights.ts`):**
```typescript
import { ApplicationInsights } from '@microsoft/applicationinsights-web';

const appInsights = new ApplicationInsights({
  config: {
    connectionString: process.env.NEXT_PUBLIC_APPINSIGHTS_CONNECTION_STRING,
    enableAutoRouteTracking: true,
    enableRequestHeaderTracking: true,
    enableResponseHeaderTracking: true,
    enableCorsCorrelation: true,
    enableAjaxErrorStatusText: true,
  }
});

if (typeof window !== 'undefined' && process.env.NEXT_PUBLIC_APPINSIGHTS_CONNECTION_STRING) {
  appInsights.loadAppInsights();
  appInsights.trackPageView();
}

export default appInsights;
```

**3. Add to GitHub Secrets:**
```bash
gh secret set NEXT_PUBLIC_APPINSIGHTS_CONNECTION_STRING \
  --body "InstrumentationKey=33aad16e-9560-4cf8-8ced-b42fde933cf2;IngestionEndpoint=https://southindia-0.in.applicationinsights.azure.com/"
```

### Access Application Insights Dashboard

**Azure Portal:**
```
https://portal.azure.com/#@/resource/subscriptions/417b3ad6-5fc1-47a3-917d-21cf4e3eddfc/resourceGroups/boloo-production-rg/providers/microsoft.insights/components/boloo-backend-insights/overview
```

**Key Features:**
- Live Metrics Stream
- Application Map
- Performance metrics
- Failure rates
- User analytics
- Custom events tracking

---

## 📊 Log Analytics Configuration

### Enable Application Logging

**1. Configure backend API logging:**
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
- ✅ **Web Server Logging:** Filesystem (3 days retention, 100MB)
- ✅ **Detailed Error Messages:** Enabled
- ✅ **Failed Request Tracing:** Enabled
- ⚠️ **Application Logging:** Off (needs enabling)

### Log Streaming

**Real-time log viewing:**
```bash
# Stream live logs from backend
az webapp log tail \
  --name boloo-backend-api \
  --resource-group boloo-production-rg

# Filter for errors only
az webapp log tail \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  | grep -i error

# Filter for specific patterns
az webapp log tail \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  | grep -E "(ERROR|WARNING|CRITICAL)"
```

### Download Log Archives

```bash
# Download all logs as ZIP
az webapp log download \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --log-file boloo-logs-$(date +%Y%m%d).zip

# Extract and view
unzip boloo-logs-$(date +%Y%m%d).zip
cat LogFiles/Application/diagnostics-*.txt
```

### Log Locations

**Backend API Logs:**
- Docker Logs: `LogFiles/*_default_docker.log`
- Application Logs: `LogFiles/Application/diagnostics-*.txt`
- Deployment Logs: `deployments/*/log.log`
- Kudu Traces: `LogFiles/kudu/trace/*.xml`

### Kudu Console Access

**Access advanced diagnostics:**
```
URL: https://boloo-backend-api.scm.azurewebsites.net
Features:
- File browser
- Debug console
- Process explorer
- Environment variables
- Log streaming
```

---

## 🚨 Alert Rules Setup

### Current Alert Configuration

✅ **8 metric alerts are configured and active with email notifications:**

#### Backend API Alerts

**Alert 1: HTTP 5xx Server Errors**
```yaml
Name: boloo-http-5xx-errors
Metric: Http5xx
Condition: Count > 10 in 5 minutes
Evaluation Frequency: 1 minute
Severity: 2 (Warning)
Status: ✅ Active with notifications
```

**Alert 2: High Response Time**
```yaml
Name: boloo-high-response-time
Metric: HttpResponseTime
Condition: Average > 5 seconds in 5 minutes
Evaluation Frequency: 1 minute
Severity: 2 (Warning)
Status: ✅ Active with notifications
```

**Alert 3: High CPU Usage**
```yaml
Name: boloo-high-cpu
Metric: CpuTime
Condition: Total > 240 seconds in 5 minutes (80% utilization)
Evaluation Frequency: 1 minute
Severity: 2 (Warning)
Status: ✅ Active with notifications
```

**Alert 4: HTTP 4xx Client Errors**
```yaml
Name: boloo-http-4xx-errors
Metric: Http4xx
Condition: Total > 50 in 5 minutes
Evaluation Frequency: 1 minute
Severity: 3 (Informational)
Status: ✅ Active with notifications
```

#### Database Alerts

**Alert 5: Database CPU Usage**
```yaml
Name: boloo-db-cpu-alert
Metric: cpu_percent
Condition: Average > 80%
Evaluation Frequency: 1 minute
Severity: 2 (Warning)
Status: ✅ Active with notifications
```

**Alert 6: Database Memory Usage**
```yaml
Name: boloo-db-memory-alert
Metric: memory_percent
Condition: Average > 85%
Evaluation Frequency: 1 minute
Severity: 2 (Warning)
Status: ✅ Active with notifications
```

**Alert 7: Database Active Connections**
```yaml
Name: boloo-db-connections-alert
Metric: active_connections
Condition: Average > 80 connections
Evaluation Frequency: 1 minute
Severity: 3 (Informational)
Status: ✅ Active with notifications
```

**Alert 8: Database Connection Failures**
```yaml
Name: boloo-db-failed-connections
Metric: connections_failed
Condition: Total > 10 in 5 minutes
Evaluation Frequency: 1 minute
Severity: 2 (Warning)
Status: ✅ Active with notifications
```

### Action Group Configuration

✅ **Action group configured and connected to all alerts:**

**Action Group Details:**
```yaml
Name: boloo-alert-notifications
Short Name: BolooAlert
Resource ID: /subscriptions/417b3ad6-5fc1-47a3-917d-21cf4e3eddfc/resourceGroups/boloo-production-rg/providers/microsoft.insights/actionGroups/boloo-alert-notifications
Email Receivers:
  - Name: AdminEmail
    Address: admin@boloo.com
    Status: ✅ Enabled
Status: ✅ Connected to all 8 alerts
```

**View action group:**
```bash
az monitor action-group show \
  --resource-group boloo-production-rg \
  --name boloo-alert-notifications
```

**Add additional email recipients:**
```bash
az monitor action-group update \
  --resource-group boloo-production-rg \
  --name boloo-alert-notifications \
  --add-action email DevTeam diptendudip@gmail.com
```

**Add SMS notifications:**
```bash
az monitor action-group update \
  --resource-group boloo-production-rg \
  --name boloo-alert-notifications \
  --add-action sms DevLead 91 YOUR_PHONE_NUMBER
```

### Test Alert Notifications

**Verify alerts are working:**
```bash
# List all alerts
az monitor metrics alert list \
  --resource-group boloo-production-rg \
  --output table

# Check specific alert configuration
az monitor metrics alert show \
  --resource-group boloo-production-rg \
  --name boloo-http-5xx-errors \
  --output json
```

### Additional Recommended Alerts (Optional)

These are already covered by the 8 configured alerts above. Additional alerts can be added as needed:

**Application Availability (if health endpoint exists):**
```bash
az monitor metrics alert create \
  --name boloo-app-availability \
  --resource-group boloo-production-rg \
  --scopes "/subscriptions/417b3ad6-5fc1-47a3-917d-21cf4e3eddfc/resourceGroups/boloo-production-rg/providers/Microsoft.Web/sites/boloo-backend-api" \
  --condition "avg HealthCheckStatus < 1" \
  --description "Health check failing" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --severity 0 \
  --action /subscriptions/417b3ad6-5fc1-47a3-917d-21cf4e3eddfc/resourceGroups/boloo-production-rg/providers/microsoft.insights/actionGroups/boloo-alert-notifications
```

---

## 📈 Performance Metrics

### Available Metrics

Backend API metrics available for monitoring:

| Metric Name | Unit | Description | Alert Threshold |
|------------|------|-------------|-----------------|
| **CpuTime** | Seconds | Total CPU time consumed | > 240s in 5min |
| **MemoryWorkingSet** | Bytes | Current memory usage | > 800MB |
| **Requests** | Count | Total HTTP requests | N/A |
| **Http2xx** | Count | Successful responses | N/A |
| **Http4xx** | Count | Client errors | > 50 in 5min |
| **Http5xx** | Count | Server errors | > 10 in 5min |
| **HttpResponseTime** | Seconds | Average response time | > 5s |
| **BytesReceived** | Bytes | Incoming bandwidth | N/A |
| **BytesSent** | Bytes | Outgoing bandwidth | N/A |
| **HealthCheckStatus** | Count | Health endpoint status | < 1 (failing) |
| **FileSystemUsage** | Bytes | Disk usage | > 1GB |

### Query Metrics via CLI

**CPU usage over last 24 hours:**
```bash
az monitor metrics list \
  --resource "/subscriptions/417b3ad6-5fc1-47a3-917d-21cf4e3eddfc/resourceGroups/boloo-production-rg/providers/Microsoft.Web/sites/boloo-backend-api" \
  --metric CpuTime \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ) \
  --interval PT1H \
  --aggregation Total
```

**HTTP 5xx errors (last hour):**
```bash
az monitor metrics list \
  --resource "/subscriptions/417b3ad6-5fc1-47a3-917d-21cf4e3eddfc/resourceGroups/boloo-production-rg/providers/Microsoft.Web/sites/boloo-backend-api" \
  --metric Http5xx \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --interval PT5M \
  --aggregation Count
```

**Response time trends:**
```bash
az monitor metrics list \
  --resource "/subscriptions/417b3ad6-5fc1-47a3-917d-21cf4e3eddfc/resourceGroups/boloo-production-rg/providers/Microsoft.Web/sites/boloo-backend-api" \
  --metric HttpResponseTime \
  --start-time $(date -u -d '6 hours ago' +%Y-%m-%dT%H:%M:%SZ) \
  --interval PT15M \
  --aggregation Average,Maximum
```

### Database Metrics

**Available Database Metrics:**

| Metric Name | Unit | Description |
|------------|------|-------------|
| cpu_percent | Percent | CPU utilization |
| memory_percent | Percent | Memory utilization |
| active_connections | Count | Current active connections |
| max_connections | Count | Maximum allowed connections |
| connections_failed | Count | Failed connection attempts |
| connections_succeeded | Count | Successful connections |
| cpu_credits_consumed | Count | CPU credits used (burstable) |
| cpu_credits_remaining | Count | CPU credits available |

**Connection count:**
```bash
az monitor metrics list \
  --resource "/subscriptions/417b3ad6-5fc1-47a3-917d-21cf4e3eddfc/resourceGroups/boloo-production-rg/providers/Microsoft.DBforPostgreSQL/flexibleServers/boloo-database" \
  --metric active_connections \
  --interval PT5M \
  --aggregation Average
```

**CPU usage:**
```bash
az monitor metrics list \
  --resource "/subscriptions/417b3ad6-5fc1-47a3-917d-21cf4e3eddfc/resourceGroups/boloo-production-rg/providers/Microsoft.DBforPostgreSQL/flexibleServers/boloo-database" \
  --metric cpu_percent \
  --interval PT1H \
  --aggregation Average
```

**Connection failures:**
```bash
az monitor metrics list \
  --resource "/subscriptions/417b3ad6-5fc1-47a3-917d-21cf4e3eddfc/resourceGroups/boloo-production-rg/providers/Microsoft.DBforPostgreSQL/flexibleServers/boloo-database" \
  --metric connections_failed \
  --interval PT5M \
  --aggregation Total
```

---

## 🔒 Database Security & Firewall Configuration

### Current Database Firewall Rules

✅ **Security Status: Improved**

**Active Firewall Rules:**
```bash
# View current rules
az postgres flexible-server firewall-rule list \
  --resource-group boloo-production-rg \
  --name boloo-database \
  --output table
```

**Current Configuration:**
- ✅ **AllowAzureServices** (0.0.0.0): Allows Azure internal services
- ⚠️ **Backend API IPs:** 52.172.55.168, 13.71.112.41, 13.71.124.204, 13.71.115.16, 13.71.122.35

**Security Improvements Made:**
- ❌ Removed: `AllowAll_2025-11-21_15-10-4` (0.0.0.0 - 255.255.255.255) - **CRITICAL SECURITY RISK**
- ✅ Added: Azure Services only firewall rule
- ✅ Backend API can connect via Azure internal network

### Add Specific IP Addresses (Optional)

If you need to allow specific external IPs:

```bash
# Add your office/home IP for admin access
az postgres flexible-server firewall-rule create \
  --resource-group boloo-production-rg \
  --name boloo-database \
  --rule-name "AdminAccess" \
  --start-ip-address YOUR_IP_ADDRESS \
  --end-ip-address YOUR_IP_ADDRESS

# Add backend API outbound IPs (if needed outside Azure)
az postgres flexible-server firewall-rule create \
  --resource-group boloo-production-rg \
  --name boloo-database \
  --rule-name "BackendAPI" \
  --start-ip-address 52.172.55.168 \
  --end-ip-address 52.172.55.168
```

### Database Connection Security

**Recommended Settings:**
- ✅ SSL/TLS enforced (Azure default)
- ✅ Firewall restricted to Azure services only
- ✅ Admin login secured
- ⚠️ Consider: Azure Private Link for enhanced security (paid feature)

**Check database security settings:**
```bash
az postgres flexible-server show \
  --resource-group boloo-production-rg \
  --name boloo-database \
  --query "{SSL:sslEnforcement,PublicAccess:network.publicNetworkAccess,FirewallEnabled:true}" \
  --output table
```

---

## 🐛 Error Tracking

### Application Insights Error Tracking

**Query recent exceptions:**
```kusto
exceptions
| where timestamp > ago(24h)
| where cloud_RoleName == "boloo-backend-api"
| summarize count() by type, outerMessage
| order by count_ desc
```

**Failed requests:**
```kusto
requests
| where timestamp > ago(1h)
| where success == false
| project timestamp, name, url, resultCode, duration
| order by timestamp desc
```

**Dependency failures:**
```kusto
dependencies
| where timestamp > ago(24h)
| where success == false
| summarize count() by target, name
| order by count_ desc
```

### Custom Error Logging

**Add to backend code:**
```python
import logging
from opencensus.ext.azure.log_exporter import AzureLogHandler

logger = logging.getLogger(__name__)
logger.addHandler(AzureLogHandler(
    connection_string=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
))

# Use throughout application
logger.error("Custom error message", extra={"custom_dimension": "value"})
logger.warning("Warning message")
logger.info("Info message")
```

### Error Rate Dashboard

**Create custom workbook in Application Insights:**
1. Navigate to Application Insights → Workbooks
2. Create new workbook
3. Add charts for:
   - Error rate over time
   - Error distribution by type
   - Failed dependency calls
   - Custom exception tracking

---

## 💰 Cost Monitoring & Budget Alerts

### Current Budget Configuration

**Settings:**
- **Monthly Budget:** $20 USD (~₹1,660)
- **Warning Threshold:** 80% ($16 USD)
- **Alert Email:** diptendudip@gmail.com
- **Status:** ✅ Configured

### Create Budget Alert

```bash
# Create monthly budget
az consumption budget create \
  --budget-name boloo-monthly-budget \
  --category cost \
  --amount 20 \
  --time-grain monthly \
  --start-date $(date +%Y-%m-01) \
  --resource-group boloo-production-rg \
  --notifications \
    "Actual_GreaterThan_80_Percent={ \
      enabled: true, \
      operator: GreaterThan, \
      threshold: 80, \
      contact-emails: ['diptendudip@gmail.com'] \
    }" \
    "Forecasted_GreaterThan_100_Percent={ \
      enabled: true, \
      operator: GreaterThan, \
      threshold: 100, \
      contact-emails: ['diptendudip@gmail.com'] \
    }"
```

### Cost Analysis

**View current spend:**
```bash
az consumption usage list \
  --start-date $(date -d '30 days ago' +%Y-%m-%d) \
  --end-date $(date +%Y-%m-%d) \
  --query "[?contains(instanceName, 'boloo')]" \
  -o table
```

**Cost by resource:**
```bash
az costmanagement query \
  --type Usage \
  --timeframe MonthToDate \
  --dataset-filter "{\"And\":[{\"Dimensions\":{\"Name\":\"ResourceGroup\",\"Operator\":\"In\",\"Values\":[\"boloo-production-rg\"]}}]}"
```

### Cost Optimization Recommendations

**Azure Advisor cost recommendations:**
```bash
az advisor recommendation list \
  --category Cost \
  --resource-group boloo-production-rg \
  -o table
```

---

## ⏱️ Uptime Monitoring

### Create Availability Tests

**1. URL Ping Test (Web App):**
```bash
az monitor app-insights web-test create \
  --resource-group boloo-production-rg \
  --app-insights boloo-backend-insights \
  --name boloo-web-ping \
  --location "South India" \
  --enabled true \
  --frequency 300 \
  --timeout 120 \
  --retry-enabled true \
  --locations "South India,East US 2,West Europe" \
  --web-test "{
    \"kind\": \"ping\",
    \"syntheticMonitorId\": \"boloo-web-ping\",
    \"request\": {
      \"url\": \"https://orange-sand-00170940f.3.azurestaticapps.net\",
      \"httpVerb\": \"GET\",
      \"parseDependentRequests\": false
    }
  }"
```

**2. API Health Check:**
```bash
az monitor app-insights web-test create \
  --resource-group boloo-production-rg \
  --app-insights boloo-backend-insights \
  --name boloo-api-health \
  --location "South India" \
  --enabled true \
  --frequency 300 \
  --timeout 120 \
  --retry-enabled true \
  --locations "South India,East US 2" \
  --web-test "{
    \"kind\": \"ping\",
    \"syntheticMonitorId\": \"boloo-api-health\",
    \"request\": {
      \"url\": \"https://boloo-backend-api.azurewebsites.net/health\",
      \"httpVerb\": \"GET\",
      \"parseDependentRequests\": false
    }
  }"
```

### Third-Party Uptime Monitoring

**Recommended services:**
1. **UptimeRobot** (Free tier available)
   - URL: https://uptimerobot.com
   - Monitor: Web app + API
   - Frequency: 5 minutes
   - Alerts: Email, SMS

2. **Pingdom** (Free trial, then paid)
   - Advanced monitoring
   - Global locations
   - Detailed reports

3. **StatusCake** (Free tier available)
   - 5-minute checks
   - Public status page

**Example UptimeRobot setup:**
```
Monitor 1: Web Application
URL: https://orange-sand-00170940f.3.azurestaticapps.net
Type: HTTP(S)
Interval: 5 minutes

Monitor 2: Backend API
URL: https://boloo-backend-api.azurewebsites.net/health
Type: HTTP(S)
Interval: 5 minutes
Expected: 200 OK
```

---

## 📊 Dashboard Setup

### Create Azure Dashboard

**1. Portal dashboard:**
```bash
# Navigate to Azure Portal
https://portal.azure.com

# Create new dashboard
1. Click "Dashboard" in left menu
2. Click "+ New dashboard"
3. Name: "Boloo Production Monitoring"
4. Add tiles:
   - Application Insights metrics
   - App Service metrics
   - Database metrics
   - Cost analysis
   - Recent alerts
```

**2. Shared dashboard via CLI:**
```bash
# Export dashboard JSON (after creating in portal)
az portal dashboard show \
  --name boloo-monitoring-dashboard \
  --resource-group boloo-production-rg \
  > dashboard-config.json

# Import dashboard
az portal dashboard create \
  --name boloo-monitoring-dashboard \
  --resource-group boloo-production-rg \
  --input-path dashboard-config.json
```

### Grafana Integration (Optional)

**Setup Azure Monitor data source in Grafana:**
```yaml
apiVersion: 1
datasources:
  - name: Azure Monitor
    type: grafana-azure-monitor-datasource
    access: proxy
    jsonData:
      subscriptionId: 417b3ad6-5fc1-47a3-917d-21cf4e3eddfc
      cloudName: azuremonitor
      tenantId: YOUR_TENANT_ID
    secureJsonData:
      clientSecret: YOUR_CLIENT_SECRET
```

---

## ✅ Monitoring Checklist

### Immediate Setup (P0) - ✅ COMPLETE
- [x] Application Insights created
- [x] Metric alerts configured (8 alerts)
- [x] Web server logging enabled
- [x] **Action Group for notifications (email)**
- [x] **Database monitoring alerts**
- [x] **Database firewall security fixed**
- [ ] **Application Insights SDK integration** (Optional - for custom telemetry)
- [ ] **Health check endpoint** (Optional - for availability monitoring)

### Short-term (P1)
- [ ] Availability tests (ping tests)
- [ ] Custom error tracking with App Insights SDK
- [ ] Performance baselines documentation
- [x] Log Analytics workspace (auto-created with App Insights)
- [ ] Cost budget alerts (requires Enterprise/MCA subscription)
- [ ] SMS notifications (add to action group)

### Long-term (P2)
- [ ] Custom dashboards in Azure Portal
- [ ] Advanced analytics queries (Kusto/KQL)
- [ ] Distributed tracing
- [ ] User analytics
- [ ] A/B testing insights

---

## 🔗 Azure Portal Quick Links

### Resource Overview
```
Subscription: 417b3ad6-5fc1-47a3-917d-21cf4e3eddfc
Resource Group: boloo-production-rg
```

### Direct Links to Resources

**Application Insights Dashboard:**
```
https://portal.azure.com/#@1cad08ec-88ce-4fad-861f-73474b7eb2d7/resource/subscriptions/417b3ad6-5fc1-47a3-917d-21cf4e3eddfc/resourceGroups/boloo-production-rg/providers/microsoft.insights/components/boloo-backend-insights/overview
```

**Backend API (App Service):**
```
https://portal.azure.com/#@1cad08ec-88ce-4fad-861f-73474b7eb2d7/resource/subscriptions/417b3ad6-5fc1-47a3-917d-21cf4e3eddfc/resourceGroups/boloo-production-rg/providers/Microsoft.Web/sites/boloo-backend-api/appServices
```

**PostgreSQL Database:**
```
https://portal.azure.com/#@1cad08ec-88ce-4fad-861f-73474b7eb2d7/resource/subscriptions/417b3ad6-5fc1-47a3-917d-21cf4e3eddfc/resourceGroups/boloo-production-rg/providers/Microsoft.DBforPostgreSQL/flexibleServers/boloo-database/overview
```

**Alert Rules:**
```
https://portal.azure.com/#@1cad08ec-88ce-4fad-861f-73474b7eb2d7/resource/subscriptions/417b3ad6-5fc1-47a3-917d-21cf4e3eddfc/resourceGroups/boloo-production-rg/providers/Microsoft.Insights/metricAlerts
```

**Action Groups:**
```
https://portal.azure.com/#@1cad08ec-88ce-4fad-861f-73474b7eb2d7/resource/subscriptions/417b3ad6-5fc1-47a3-917d-21cf4e3eddfc/resourceGroups/boloo-production-rg/providers/microsoft.insights/actionGroups/boloo-alert-notifications/overview
```

**Resource Group Overview:**
```
https://portal.azure.com/#@1cad08ec-88ce-4fad-861f-73474b7eb2d7/resource/subscriptions/417b3ad6-5fc1-47a3-917d-21cf4e3eddfc/resourceGroups/boloo-production-rg/overview
```

### Common Monitoring Views

**Live Metrics Stream:**
```
https://portal.azure.com/#@1cad08ec-88ce-4fad-861f-73474b7eb2d7/resource/subscriptions/417b3ad6-5fc1-47a3-917d-21cf4e3eddfc/resourceGroups/boloo-production-rg/providers/microsoft.insights/components/boloo-backend-insights/quickPulse
```

**Application Map:**
```
https://portal.azure.com/#@1cad08ec-88ce-4fad-861f-73474b7eb2d7/resource/subscriptions/417b3ad6-5fc1-47a3-917d-21cf4e3eddfc/resourceGroups/boloo-production-rg/providers/microsoft.insights/components/boloo-backend-insights/applicationMap
```

**Failures Analysis:**
```
https://portal.azure.com/#@1cad08ec-88ce-4fad-861f-73474b7eb2d7/resource/subscriptions/417b3ad6-5fc1-47a3-917d-21cf4e3eddfc/resourceGroups/boloo-production-rg/providers/microsoft.insights/components/boloo-backend-insights/failures
```

**Performance Analysis:**
```
https://portal.azure.com/#@1cad08ec-88ce-4fad-861f-73474b7eb2d7/resource/subscriptions/417b3ad6-5fc1-47a3-917d-21cf4e3eddfc/resourceGroups/boloo-production-rg/providers/microsoft.insights/components/boloo-backend-insights/performance
```

---

## 📚 Additional Resources

- [Application Insights Documentation](https://docs.microsoft.com/azure/azure-monitor/app/app-insights-overview)
- [Azure Monitor Alerts](https://docs.microsoft.com/azure/azure-monitor/alerts/alerts-overview)
- [Cost Management Best Practices](https://docs.microsoft.com/azure/cost-management-billing/costs/cost-mgt-best-practices)
- [App Service Diagnostics](https://docs.microsoft.com/azure/app-service/overview-diagnostics)

---

**Guide Maintained By:** DevOps Team
**Last Review:** November 22, 2025
**Next Review:** December 22, 2025
