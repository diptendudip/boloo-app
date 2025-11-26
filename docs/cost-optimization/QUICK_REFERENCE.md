# Cost Optimization Quick Reference

**Status:** ✅ Phase 1 Complete (Nov 22, 2025)
**Total Monthly Cost:** ₹2,337.19 (~$28 USD)
**Projected Savings:** ₹50-150/month after 90 days

---

## ⚡ Quick Commands

### Verify All Optimizations
```bash
cd docs/cost-optimization
./verify-optimizations.sh
```

### Check Storage Lifecycle
```bash
az storage account management-policy show \
  --account-name boloostore2025 \
  --resource-group boloo-production-rg \
  -o table
```

### Check Database Settings
```bash
az postgres flexible-server parameter show \
  --server-name boloo-database \
  --resource-group boloo-production-rg \
  --name work_mem -o json
```

### Check Current Costs (if supported)
```bash
az consumption usage list \
  --start-date $(date -d '30 days ago' +%Y-%m-%d) \
  --end-date $(date +%Y-%m-%d) \
  -o table
```

---

## 📊 Current Infrastructure

| Resource | Type | SKU | Cost/Month |
|----------|------|-----|------------|
| boloo-app-plan | App Service | Basic B1 | ₹1,379.81 |
| boloo-database | PostgreSQL | B1ms | ₹915.75 |
| boloostore2025 | Storage | LRS | ₹41.63 |
| Others (5 resources) | Various | Free | ₹0.00 |

**Total:** ₹2,337.19/month

---

## ✅ Phase 1 Completed

- [x] Storage lifecycle policies (3 rules active)
- [x] Soft delete protection (7-day retention)
- [x] Database parameter tuning (work_mem, maintenance_work_mem)
- [x] HTTPS-only enforcement
- [x] Orphaned resource verification (0 found)

---

## 📈 Savings Timeline

| Month | Expected Savings | Cumulative |
|-------|-----------------|------------|
| Nov 2025 | ₹0 | ₹0 |
| Dec 2025 | ₹0-10 | ₹0-10 |
| Jan 2026 | ₹40-80 | ₹40-90 |
| Feb 2026+ | ₹50-150 | ₹90-240+ |

**Annual Projected:** ₹600-1,800

---

## 🎯 Phase 2 Opportunities

1. **Reserved Instances** - Save ₹688/month (30-40% off)
2. **App Service Right-sizing** - Save ₹546/month (if traffic allows)
3. **Storage Cool Tier** - Save 43% on archived data
4. **Database Backup** - Save ₹50-100/month (reduce retention)

**Total Phase 2 Potential:** ₹700-900/month

---

## 📁 Key Documents

- **Full Report:** `/docs/COST_OPTIMIZATION_PHASE1_COMPLETE.md`
- **Executive Summary:** `/docs/cost-optimization/PHASE1_EXECUTIVE_SUMMARY.md`
- **Savings Tracker:** `/docs/cost-optimization/SAVINGS_TRACKER.md`
- **Pricing Details:** `/docs/cost-optimization/azure-pricing-estimates.md`

---

## 🔔 Next Actions

### This Week
- [ ] Set up budget alert (₹5,000/month) in Azure Portal
- [ ] Tag all resources for cost tracking
- [ ] Schedule 30-day follow-up review

### This Month
- [ ] Monitor storage size weekly
- [ ] Collect performance metrics baseline
- [ ] Export cost data for trending

### Next 90 Days
- [ ] Validate lifecycle policy effectiveness
- [ ] Analyze 60-day performance data
- [ ] Decide on Phase 2 optimizations

---

## 🆘 Troubleshooting

### Storage Growing Despite Lifecycle Policies
```bash
# Check if policies are active
az storage account management-policy show \
  --account-name boloostore2025 \
  --resource-group boloo-production-rg

# List containers and sizes
az storage container list \
  --account-name boloostore2025 \
  --output table
```

### Database Performance Issues
```bash
# Check current parameters
az postgres flexible-server parameter list \
  --server-name boloo-database \
  --resource-group boloo-production-rg \
  --query "[?source=='user-override'].{Name:name,Value:value}" \
  -o table

# Revert to defaults if needed
az postgres flexible-server parameter set \
  --server-name boloo-database \
  --resource-group boloo-production-rg \
  --name work_mem \
  --value 4096
```

### Cost Spike Investigation
```bash
# List all resources and their SKUs
az resource list \
  --resource-group boloo-production-rg \
  --query "[].{Name:name,Type:type,SKU:sku}" \
  -o table

# Check App Service plan metrics
az monitor metrics list \
  --resource /subscriptions/$(az account show --query id -o tsv)/resourceGroups/boloo-production-rg/providers/Microsoft.Web/serverFarms/boloo-app-plan \
  --metric CpuPercentage \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ) \
  --interval PT1H
```

---

## 📞 Support

**Questions?** Review the full documentation in `/docs/cost-optimization/`

**Issues?** Run `./verify-optimizations.sh` to check all settings

**Concerns?** Contact DevOps team for assistance

---

**Last Updated:** November 22, 2025
**Next Review:** December 22, 2025
