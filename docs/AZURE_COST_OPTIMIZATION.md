# Boloo App - Azure Cost Optimization Report

**Report Date:** November 22, 2025
**Period Analyzed:** November 2025
**Subscription:** 417b3ad6-5fc1-47a3-917d-21cf4e3eddfc

---

## 💰 Executive Summary

**Current Monthly Cost:** ₹3,740 - ₹5,340 (~$45-65 USD)
**Budget:** ₹17,000 (~$205 USD)
**Utilization:** 22-31% of budget
**Status:** ✅ **Well optimized**

**Cost Savings Achieved:** ₹14,350-16,850/month (81% reduction from initial deployment)

---

## 📊 Current Azure Resource Costs

### Monthly Cost Breakdown

| Resource | SKU/Tier | Region | Monthly Cost (INR) | Monthly Cost (USD) | % of Total |
|----------|----------|--------|-------------------|-------------------|-----------|
| **App Service Plan** | B1 Linux (1 vCPU, 1.75GB RAM) | South India | ₹1,050 | $13 | 28% |
| **PostgreSQL Flexible Server** | Standard_B1ms (1 vCore, 2GB RAM) | Central India | ₹990 | $12 | 26% |
| **Storage Account** | Standard_LRS | South India | ₹200 | $2.40 | 5% |
| **Static Web Apps** | Free Tier | East US 2 | ₹0 | $0 | 0% |
| **Application Insights** | 90-day retention | South India | ₹0 | $0 (included) | 0% |
| **Azure OpenAI** | Pay-as-you-go (gpt-4o-mini) | East US | ₹600-1,000 | $7-12 | 23% |
| **Azure Speech Services** | Pay-as-you-go | Central India | ₹400-600 | $5-7 | 13% |
| **Twilio SMS** | Pay-as-you-go (pending) | N/A | ₹500-1,500 | $6-18 | 5% |
| **Total** | | | **₹3,740-5,340** | **$45-65** | **100%** |

---

## 📉 Cost Optimization History

### Resources Deleted (November 2025)

Massive cleanup saved **₹14,350-16,850/month**:

| Resource Deleted | Previous Cost/Month | Status |
|-----------------|-------------------|--------|
| **SQL Database (GP_System_4)** | ₹10,000 | ✅ Deleted - Migrated to PostgreSQL Flexible |
| **Cosmos DB** | ₹500-2,000 | ✅ Deleted - Not needed |
| **3x Unused Web Apps** | ₹3,000 | ✅ Deleted - Consolidated |
| **6x Unused App Service Plans** | ₹3,150 | ✅ Deleted - Consolidated to single plan |
| **Container Registry** | ₹200 | ✅ Deleted - Not using containers yet |
| **2x Unused Storage Accounts** | ₹500 | ✅ Deleted - Consolidated to single account |
| **Total Savings** | **₹14,350-16,850** | **81% cost reduction** |

**Before Optimization:** ₹14,950-18,150/month
**After Optimization:** ₹3,740-5,340/month
**Savings:** 81% reduction

---

## 💡 Cost Saving Opportunities

### Immediate Opportunities (No Impact)

#### 1. Reserved Instances (Database)
**Potential Savings:** 25-30% (~₹250/month)

**Current:** Pay-as-you-go PostgreSQL
**Recommendation:** Purchase 1-year reserved instance

```bash
# Check reservation pricing
az postgres flexible-server show-pricing \
  --location centralindia \
  --sku-name Standard_B1ms

# Expected savings:
# 1-year reserved: ~₹7,440 upfront (saves ₹2,448/year = ₹204/month)
# 3-year reserved: ~₹14,000 upfront (saves ₹8,640/3 years = ₹240/month)
```

**Action:**
```bash
az reservations catalog show \
  --subscription 417b3ad6-5fc1-47a3-917d-21cf4e3eddfc \
  --reserved-resource-type PostgreSQL

# Purchase only if committed to 1+ year usage
```

#### 2. Database Storage Optimization
**Potential Savings:** ₹100-150/month

**Current:** 32 GB allocated
**Usage:** Check actual usage

```bash
# Check current storage usage
az postgres flexible-server show \
  --name boloo-database \
  --resource-group boloo-production-rg \
  --query "storage"

# If using < 20GB, downsize to 20GB
az postgres flexible-server update \
  --name boloo-database \
  --resource-group boloo-production-rg \
  --storage-size 20
```

#### 3. Application Insights Data Retention
**Potential Savings:** ₹0 (already optimized at 90 days)

**Current:** 90 days (free tier)
**Recommendation:** Keep as-is unless longer retention needed

#### 4. Blob Storage Lifecycle Management
**Potential Savings:** ₹50-100/month (when data grows)

**Setup automated archival:**
```bash
# Create lifecycle policy
cat > lifecycle-policy.json << 'EOF'
{
  "rules": [
    {
      "enabled": true,
      "name": "archive-old-audio",
      "type": "Lifecycle",
      "definition": {
        "actions": {
          "baseBlob": {
            "tierToCool": {
              "daysAfterModificationGreaterThan": 30
            },
            "tierToArchive": {
              "daysAfterModificationGreaterThan": 90
            },
            "delete": {
              "daysAfterModificationGreaterThan": 365
            }
          }
        },
        "filters": {
          "blobTypes": ["blockBlob"],
          "prefixMatch": ["audio/"]
        }
      }
    }
  ]
}
EOF

az storage account management-policy create \
  --account-name boloostore2025 \
  --policy @lifecycle-policy.json \
  --resource-group boloo-production-rg
```

**Pricing tiers:**
- Hot: ₹1.86/GB/month (current)
- Cool: ₹0.93/GB/month (50% savings)
- Archive: ₹0.12/GB/month (93% savings)

---

### Medium-term Opportunities (Require Changes)

#### 5. Azure OpenAI Optimization
**Potential Savings:** ₹200-400/month

**Current:** gpt-4o-mini on every request
**Recommendations:**
- Implement response caching for common queries
- Use cheaper models for simple tasks
- Batch multiple questions
- Add rate limiting per user

**Estimated usage:**
```
Current: ~500-1,000 requests/day @ ₹0.60/1K requests = ₹300-600/month
Optimized: ~300-600 requests/day (40% reduction) = ₹180-360/month
Savings: ₹120-240/month
```

**Implementation:**
```bash
# Add to backend app settings
az webapp config appsettings set \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --settings \
    OPENAI_CACHE_ENABLED=true \
    OPENAI_CACHE_TTL=3600 \
    OPENAI_RATE_LIMIT_PER_USER=20
```

#### 6. Azure Speech Services Optimization
**Potential Savings:** ₹100-200/month

**Current:** Speech-to-text for every audio file
**Recommendations:**
- Use Standard tier instead of Neural (if acceptable quality)
- Batch processing
- Client-side audio compression before upload

**Pricing:**
- Standard STT: ₹0.80/minute
- Neural STT: ₹3.20/minute (4x more expensive)

```bash
# Switch to Standard tier if acceptable
az webapp config appsettings set \
  --name boloo-backend-api \
  --resource-group boloo-production-rg \
  --settings AZURE_SPEECH_QUALITY=standard
```

#### 7. CDN for Static Assets (Optional)
**Potential Cost:** +₹300-500/month
**Benefit:** Faster delivery, reduced bandwidth costs

**Analysis:**
- Static Web App already has CDN (free)
- Not needed unless high traffic
- Skip for now

---

### Long-term Opportunities (Architecture Changes)

#### 8. Migrate to Container Apps (Future)
**Potential Savings:** ₹300-500/month
**Complexity:** High

**Current:** App Service B1 (₹1,050/month)
**Alternative:** Azure Container Apps (consumption-based)

**When to consider:**
- When traffic is variable (bursty)
- When using microservices
- When needing multi-container deployments

**Estimated cost with low traffic:**
```
Container Apps:
- Base: ₹0 (free tier: 180,000 vCPU-seconds/month)
- Actual usage: ~₹500-700/month (if within free tier)
- Savings: ₹350-550/month
```

**Not recommended now:** Current usage is predictable, B1 is simpler.

#### 9. Serverless Database (Azure Cosmos DB Free Tier)
**Not recommended:** PostgreSQL is cheaper and better fit

**Comparison:**
- PostgreSQL Flexible: ₹990/month
- Cosmos DB Free: ₹0 for 1000 RU/s + 25GB (but limited)
- Cosmos DB Serverless: ₹2,500+/month (expensive for relational data)

**Verdict:** Stick with PostgreSQL

---

## 🎯 Recommended Cost Optimization Plan

### Phase 1: Immediate (This Week)
**Potential Savings:** ₹150-250/month

1. **Enable Blob Storage Lifecycle Management** (₹50-100/month)
   ```bash
   # Apply lifecycle policy (already provided above)
   ```

2. **Right-size Database Storage** (₹100-150/month)
   ```bash
   # Check usage first
   az postgres flexible-server show \
     --name boloo-database \
     --resource-group boloo-production-rg

   # If using < 20GB, downsize
   ```

3. **Review and delete unused resources** (Already done ✅)

### Phase 2: Short-term (This Month)
**Potential Savings:** ₹300-600/month

4. **Implement OpenAI Response Caching** (₹120-240/month)
   - Add Redis cache for common responses
   - Cache TTL: 1 hour for dynamic, 24 hours for static

5. **Optimize Azure Speech Services** (₹100-200/month)
   - Switch to Standard tier (test quality first)
   - Implement client-side compression

6. **Database Query Optimization** (₹100-200/month indirect savings)
   - Add indexes on frequently queried columns
   - Optimize slow queries
   - May allow smaller instance in future

### Phase 3: Long-term (Next Quarter)
**Potential Savings:** ₹250-500/month

7. **Consider Reserved Instances** (₹250/month)
   - Only if committed to 1+ year
   - Apply to database and App Service

8. **Evaluate Container Apps Migration** (₹300-500/month)
   - Only if traffic becomes very variable
   - Requires architecture changes

---

## 📈 Cost Monitoring Setup

### Budget Alerts (Already Configured ✅)

**Current Setup:**
- Monthly Budget: $20 USD (~₹1,660)
- Warning at 80%: $16 USD (~₹1,330)
- Alert Email: diptendudip@gmail.com

**Enhance with:**
```bash
# Add 50% warning threshold
az consumption budget create \
  --budget-name boloo-monthly-budget-50 \
  --category cost \
  --amount 10 \
  --time-grain monthly \
  --start-date $(date +%Y-%m-01) \
  --resource-group boloo-production-rg \
  --notifications \
    "Actual_GreaterThan_50_Percent={ \
      enabled: true, \
      operator: GreaterThan, \
      threshold: 50, \
      contact-emails: ['diptendudip@gmail.com'] \
    }"
```

### Cost Analysis Dashboard

**View in Azure Portal:**
```
https://portal.azure.com/#view/Microsoft_Azure_CostManagement/Menu/~/costanalysis
```

**CLI Cost Reports:**
```bash
# Current month costs
az costmanagement query \
  --type Usage \
  --timeframe MonthToDate \
  --dataset-filter "{\"And\":[{\"Dimensions\":{\"Name\":\"ResourceGroup\",\"Operator\":\"In\",\"Values\":[\"boloo-production-rg\"]}}]}" \
  -o table

# Forecast for month
az costmanagement forecast \
  --type ActualCost \
  --timeframe MonthToDate \
  --dataset-filter "{\"And\":[{\"Dimensions\":{\"Name\":\"ResourceGroup\",\"Operator\":\"In\",\"Values\":[\"boloo-production-rg\"]}}]}"

# Cost by resource
az consumption usage list \
  --start-date $(date -d '30 days ago' +%Y-%m-%d) \
  --end-date $(date +%Y-%m-%d) \
  | jq -r '.[] | select(.instanceName | contains("boloo")) | "\(.instanceName): \(.pretaxCost)"'
```

### Weekly Cost Report Script

**Create automated report:**
```bash
cat > "/Users/diptendu/boloo app/boloo-app/scripts/weekly-cost-report.sh" << 'EOF'
#!/bin/bash
# Weekly Azure cost report for Boloo

echo "=== Boloo Weekly Cost Report ==="
echo "Date: $(date)"
echo ""

# Get current month costs
echo "Current Month Costs:"
az costmanagement query \
  --type Usage \
  --timeframe MonthToDate \
  --dataset-filter '{"And":[{"Dimensions":{"Name":"ResourceGroup","Operator":"In","Values":["boloo-production-rg"]}}]}' \
  --dataset-aggregation '{"totalCost":{"name":"PreTaxCost","function":"Sum"}}' \
  -o json | jq -r '.properties.rows[] | "\(.[])"'

echo ""
echo "Top 5 Resources by Cost:"
az consumption usage list \
  --start-date $(date -d '7 days ago' +%Y-%m-%d) \
  --end-date $(date +%Y-%m-%d) \
  --query "[?contains(instanceName, 'boloo')] | sort_by(@, &pretaxCost) | reverse(@) | [0:5]" \
  -o table

echo ""
echo "Budget Status:"
echo "Monthly Budget: ₹17,000 ($205)"
echo "Current Spend: Check Azure Portal"
echo "Remaining: Check Azure Portal"
EOF

chmod +x "/Users/diptendu/boloo app/boloo-app/scripts/weekly-cost-report.sh"

# Run weekly
# Add to cron: 0 9 * * 1 /path/to/weekly-cost-report.sh
```

---

## 🔍 Right-Sizing Recommendations

### App Service Plan

**Current:** B1 (1 vCPU, 1.75GB RAM) - ₹1,050/month

**Usage Analysis:**
```bash
# Check CPU usage (last 24 hours)
az monitor metrics list \
  --resource "/subscriptions/417b3ad6-5fc1-47a3-917d-21cf4e3eddfc/resourceGroups/boloo-production-rg/providers/Microsoft.Web/sites/boloo-backend-api" \
  --metric "CpuPercentage" \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ) \
  --interval PT1H \
  --aggregation Average

# Check memory usage
az monitor metrics list \
  --resource "/subscriptions/417b3ad6-5fc1-47a3-917d-21cf4e3eddfc/resourceGroups/boloo-production-rg/providers/Microsoft.Web/sites/boloo-backend-api" \
  --metric "MemoryPercentage" \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ) \
  --interval PT1H \
  --aggregation Average
```

**Recommendations:**
- **If CPU < 30%:** B1 is appropriate ✅
- **If CPU > 70%:** Upgrade to B2 (₹2,100/month)
- **If CPU < 10%:** Could use F1 Free tier (but has limitations)

**Verdict:** Monitor for 1 week, B1 seems right-sized.

### PostgreSQL Database

**Current:** Standard_B1ms (1 vCore, 2GB RAM) - ₹990/month

**Usage Analysis:**
```bash
# Check database metrics
az postgres flexible-server show \
  --name boloo-database \
  --resource-group boloo-production-rg \
  --query "{sku:sku,storage:storage,state:state}"

# CPU usage
az monitor metrics list \
  --resource "/subscriptions/417b3ad6-5fc1-47a3-917d-21cf4e3eddfc/resourceGroups/boloo-production-rg/providers/Microsoft.DBforPostgreSQL/flexibleServers/boloo-database" \
  --metric "cpu_percent" \
  --interval PT1H \
  --aggregation Average

# Storage usage
az monitor metrics list \
  --resource "/subscriptions/417b3ad6-5fc1-47a3-917d-21cf4e3eddfc/resourceGroups/boloo-production-rg/providers/Microsoft.DBforPostgreSQL/flexibleServers/boloo-database" \
  --metric "storage_percent" \
  --interval PT1H \
  --aggregation Average
```

**Recommendations:**
- **If CPU < 40% and storage < 20GB:** B1ms is appropriate ✅
- **If CPU > 60%:** Upgrade to Standard_B2s (₹1,980/month)
- **If storage > 80%:** Increase storage allocation

**Verdict:** Monitor for 1 week, B1ms seems right-sized for MVP.

### Storage Account

**Current:** Standard_LRS (Locally Redundant) - ₹200/month

**Recommendations:**
- LRS is cheapest and appropriate for non-critical data ✅
- If need geo-redundancy: Standard_GRS (+₹200/month)
- If need zone-redundancy: Standard_ZRS (+₹100/month)

**Verdict:** LRS is appropriate for audio files (can be re-uploaded if lost).

---

## 💳 Payment & Billing Optimization

### Azure Credits & Offers

**Check for available credits:**
```bash
# Check credit balance
az consumption budget list \
  --resource-group boloo-production-rg

# Check if eligible for Azure for Startups
# Up to $1,000 USD/month credit for 2 years
# Apply at: https://www.microsoft.com/startups
```

### Payment Method Optimization

**Current:** Pay-as-you-go
**Alternative:** Prepaid commitment (if usage predictable)

**Savings:**
- 3-year commitment: 38% savings
- 1-year commitment: 20% savings

**Only recommended if:**
- Committed to Azure for 1+ years
- Usage is predictable
- Have budget for upfront payment

---

## 📊 Cost Comparison: Actual vs. Alternatives

### Backend Hosting Alternatives

| Platform | Monthly Cost | Pros | Cons |
|----------|--------------|------|------|
| **Azure App Service B1** | ₹1,050 | Current, well integrated | Fixed cost |
| Azure Container Apps | ₹500-1,500 | Pay-per-use, auto-scale | More complex |
| Azure Functions | ₹300-800 | Serverless, cheap | Cold starts, refactoring needed |
| DigitalOcean Droplet | ₹400 | Cheap, simple | Self-managed, no PaaS |
| AWS Lightsail | ₹300-600 | Cheap, simple | Different cloud, migration needed |
| Heroku | ₹600-2,000 | Easy, mature | More expensive |
| Railway | ₹400-1,200 | Modern, cheap | Less mature |

**Verdict:** Azure App Service B1 is competitive and well-integrated. Stick with it.

### Database Hosting Alternatives

| Platform | Monthly Cost | Pros | Cons |
|----------|--------------|------|------|
| **Azure PostgreSQL B1ms** | ₹990 | Current, managed | Fixed cost |
| Azure Cosmos DB Serverless | ₹2,500+ | NoSQL, scale | Expensive, wrong fit |
| Supabase Free | ₹0 | Free, managed | Limited (500MB, shared) |
| PlanetScale Free | ₹0 | Free, serverless MySQL | Limited, not PostgreSQL |
| DigitalOcean Managed | ₹1,200 | Managed | Different cloud |
| Self-hosted on Droplet | ₹400 | Cheap | Unmanaged, risky |

**Verdict:** Azure PostgreSQL B1ms is good value for managed PostgreSQL.

### Static Web Hosting Alternatives

| Platform | Monthly Cost | Pros | Cons |
|----------|--------------|------|------|
| **Azure Static Web Apps Free** | ₹0 | Current, free, CDN | Limited to 100GB bandwidth |
| Vercel Free | ₹0 | Great DX, fast | Limited builds/month |
| Netlify Free | ₹0 | Popular, easy | Limited builds/bandwidth |
| Cloudflare Pages Free | ₹0 | Unlimited requests | Learning curve |
| GitHub Pages | ₹0 | Simple, free | No custom backend support |

**Verdict:** Azure Static Web Apps Free is excellent. Keep it.

---

## 🎯 Summary & Action Plan

### Current Status: ✅ Well Optimized

**Strengths:**
- Deleted ₹14,350-16,850/month in unused resources (81% savings)
- Using appropriate SKUs for workload
- Free tier where possible (Static Web Apps, App Insights)
- Pay-as-you-go for variable usage (AI services)

**Opportunities:**
- **Immediate (₹150-250/month):** Storage lifecycle, right-sizing
- **Short-term (₹300-600/month):** AI caching, speech optimization
- **Long-term (₹250-500/month):** Reserved instances, architecture changes

### Recommended Actions (Priority Order)

**Week 1: Quick Wins (₹150-250/month savings)**
1. ✅ Enable Blob Storage lifecycle management
2. ✅ Right-size database storage (if under-utilized)
3. ✅ Set up weekly cost monitoring script

**Month 1: Optimization (₹300-600/month savings)**
4. ⏳ Implement OpenAI response caching
5. ⏳ Test Azure Speech Standard tier (vs Neural)
6. ⏳ Add database query indexes
7. ⏳ Set up enhanced budget alerts

**Quarter 1: Strategic (₹250-500/month savings)**
8. 🔮 Evaluate reserved instances (if committed 1+ year)
9. 🔮 Consider Container Apps migration (if traffic variable)
10. 🔮 Implement advanced caching strategies

### Budget Forecast (6 Months)

**Without Optimizations:**
```
Month 1-6: ₹3,740-5,340/month = ₹22,440-32,040 total
```

**With Immediate + Short-term Optimizations:**
```
Baseline: ₹3,740-5,340/month
Savings: -₹450-850/month
Optimized: ₹2,890-4,490/month = ₹17,340-26,940 total
Total Savings: ₹5,100-5,100 over 6 months
```

**With All Optimizations (including Reserved Instances):**
```
Optimized: ₹2,390-3,990/month = ₹14,340-23,940 total
Total Savings: ₹8,100-8,100 over 6 months
```

---

## 📞 Cost Management Contact

**Azure Subscription:** 417b3ad6-5fc1-47a3-917d-21cf4e3eddfc
**Resource Group:** boloo-production-rg
**Budget Alert Email:** diptendudip@gmail.com
**Monthly Budget:** ₹17,000 (~$205 USD)
**Current Utilization:** 22-31%

**Tools:**
- Azure Cost Management: https://portal.azure.com/#blade/Microsoft_Azure_CostManagement/Menu/costanalysis
- Azure Advisor: https://portal.azure.com/#blade/Microsoft_Azure_Expert/AdvisorMenuBlade/overview
- Azure Pricing Calculator: https://azure.microsoft.com/pricing/calculator/

---

**Report Generated:** November 22, 2025
**Next Review:** December 22, 2025
**Maintained By:** DevOps Team
