# Azure Pricing Estimates - Boloo Production Resources

## Current Monthly Costs (Estimated)

### 1. App Service Plan (boloo-app-plan)
- **Tier:** Basic B1
- **Location:** South India
- **Specs:** 1 vCPU, 1.75 GB RAM
- **Monthly Cost:** ₹1,379.81 (~$16.50 USD)
- **730 hours/month**

### 2. PostgreSQL Flexible Server (boloo-database)
- **Tier:** Burstable Standard_B1ms
- **Location:** Central India
- **Specs:** 1 vCPU, 2 GB RAM
- **Storage:** 32 GB
- **Backup Retention:** 7 days
- **Monthly Compute Cost:** ₹832.50 (~$10.00 USD)
- **Monthly Storage Cost:** ₹83.25 (~$1.00 USD/32GB)
- **Total Database:** ₹915.75 (~$11.00 USD)

### 3. Storage Account (boloostore2025)
- **Tier:** Standard LRS
- **Location:** South India
- **Access Tier:** Hot
- **Estimated Usage:** ~5 GB
- **Monthly Cost:** ₹41.63 (~$0.50 USD)

### 4. Application Insights (boloo-backend-insights)
- **Data Ingestion:** ~1-2 GB/month (estimated)
- **Monthly Cost:** ₹0 (First 5 GB free)

### 5. Static Web Apps (2x Free Tier)
- **boloo-web-admin:** Free
- **boloo-citizen-app:** Free
- **Monthly Cost:** ₹0

### 6. Metric Alerts (3 alerts)
- **Monthly Cost:** ₹0 (Within free tier limits)

---

## **Total Current Monthly Cost: ₹2,337.19 (~$28.00 USD)**

---

## Azure Pricing References (India Prices)

### App Service (South India)
- **Free F1:** ₹0
- **Shared D1:** ₹833.33/month
- **Basic B1:** ₹1,379.81/month ⭐ Current
- **Standard S1:** ₹6,222.73/month
- **Premium P1v2:** ₹12,278.64/month

### PostgreSQL Flexible Server (Central India)
- **Burstable B1ms:** ₹832.50/month (1 vCPU, 2 GB) ⭐ Current
- **Burstable B2s:** ₹1,665.00/month (2 vCPU, 4 GB)
- **General Purpose D2s_v3:** ₹9,990.00/month (2 vCPU, 8 GB)

### Storage (South India)
- **Standard LRS Hot:** ₹1.45/GB/month ⭐ Current
- **Standard LRS Cool:** ₹0.83/GB/month
- **Standard LRS Archive:** ₹0.17/GB/month

---

## Cost Optimization Opportunities

### Immediate (Phase 1) ✅
1. **Storage Lifecycle Policies** - Save 20-30% on storage
2. **Database Parameter Tuning** - Improve performance without cost
3. **HTTPS-Only Enforcement** - Security improvement (no cost)
4. **Soft Delete Retention** - Data protection (minimal cost)

### Future (Phase 2)
1. **Consider Reserved Instances** - 30-40% savings for 1-year commitment
2. **Evaluate Shared D1 tier** if traffic is low - Save ₹546/month
3. **Storage Cool Tier** for old data - Save 43% on archived data
4. **Database Backup Optimization** - Reduce retention to 3 days if acceptable

---

## Regional Pricing Differences

| Service | South India | Central India | Difference |
|---------|-------------|---------------|------------|
| App Service B1 | ₹1,379.81 | ₹1,379.81 | Same |
| PostgreSQL B1ms | ₹832.50 | ₹832.50 | Same |
| Storage LRS | ₹1.45/GB | ₹1.45/GB | Same |

**Note:** No significant regional price differences in India regions for current services.

---

## Currency Conversion Reference
- **1 USD ≈ ₹83.50** (approximate, varies daily)
- Total monthly cost: **$28.00 USD** or **₹2,337.19 INR**
