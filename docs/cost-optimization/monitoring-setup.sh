#!/bin/bash
# Cost Monitoring Setup Script for Boloo Production
# Note: Automated budgets require Enterprise Agreement or specific subscription types
# This script sets up resource tagging and monitoring helpers

set -e

RESOURCE_GROUP="boloo-production-rg"
SUBSCRIPTION_ID="417b3ad6-5fc1-47a3-917d-21cf4e3eddfc"

echo "🚀 Setting up cost monitoring for boloo-production-rg..."

# 1. Tag all resources for cost tracking
echo ""
echo "📊 Step 1: Tagging resources for cost tracking..."
RESOURCE_IDS=$(az resource list \
  --resource-group $RESOURCE_GROUP \
  --query "[].id" -o tsv)

for RESOURCE_ID in $RESOURCE_IDS; do
  echo "   Tagging: $RESOURCE_ID"
  az resource tag \
    --ids "$RESOURCE_ID" \
    --tags \
      Environment=Production \
      Project=Boloo \
      CostCenter=Operations \
      ManagedBy=DevOps \
      CreatedDate=$(date +%Y-%m-%d) \
    2>/dev/null || echo "   ⚠️  Failed to tag (might be locked resource)"
done

echo "✅ Resource tagging complete"

# 2. List current resource costs (if subscription supports it)
echo ""
echo "📊 Step 2: Checking cost management support..."
az consumption usage list \
  --start-date $(date -d '30 days ago' +%Y-%m-%d) \
  --end-date $(date +%Y-%m-%d) \
  --query "[].{Name:instanceName,Cost:pretaxCost,Currency:currency}" -o table \
  2>/dev/null || echo "⚠️  Cost Management API not available for this subscription type"

# 3. Create resource inventory
echo ""
echo "📊 Step 3: Creating resource inventory..."
az resource list \
  --resource-group $RESOURCE_GROUP \
  --query "[].{Name:name,Type:type,Location:location,SKU:sku.name,Tags:tags}" \
  -o json > /tmp/boloo-resources-$(date +%Y%m%d).json

echo "✅ Resource inventory saved to /tmp/boloo-resources-$(date +%Y%m%d).json"

# 4. Get current resource metrics
echo ""
echo "📊 Step 4: Collecting resource metrics..."

# App Service metrics
echo "   App Service Plan metrics..."
SUBSCRIPTION=$(az account show --query id -o tsv)
APP_SERVICE_ID="/subscriptions/$SUBSCRIPTION/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Web/serverFarms/boloo-app-plan"

az monitor metrics list \
  --resource $APP_SERVICE_ID \
  --metric CpuPercentage \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --interval PT1H \
  --aggregation Average \
  --query "value[].timeseries[].data[].[timeStamp,average]" \
  -o tsv > /tmp/boloo-cpu-metrics-$(date +%Y%m%d).tsv 2>/dev/null || echo "   ⚠️  Metrics collection failed"

echo "✅ Metrics collected to /tmp/boloo-cpu-metrics-$(date +%Y%m%d).tsv"

# 5. Storage account size check
echo ""
echo "📊 Step 5: Checking storage account usage..."
az storage account show-usage \
  --location southindia \
  --query "{Current:currentValue,Limit:limit,Name:name.value}" \
  -o table

echo ""
echo "✅ Cost monitoring setup complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Review tagged resources in Azure Portal → Cost Management"
echo "2. Manually create budget in Azure Portal:"
echo "   - Go to: Cost Management + Billing → Budgets"
echo "   - Budget Amount: ₹5,000/month"
echo "   - Alert Thresholds: 50%, 80%, 100%"
echo "   - Notification Email: your-email@example.com"
echo "3. Set up weekly cost review calendar reminder"
echo "4. Export cost data monthly for trending analysis"
echo ""
echo "📁 Generated Files:"
echo "   - /tmp/boloo-resources-$(date +%Y%m%d).json"
echo "   - /tmp/boloo-cpu-metrics-$(date +%Y%m%d).tsv"
echo ""
