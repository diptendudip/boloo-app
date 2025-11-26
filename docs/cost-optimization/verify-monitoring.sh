#!/bin/bash

# Boloo App - Monitoring Verification Script
# Usage: bash verify-monitoring.sh

echo "=================================================="
echo "Boloo App - Monitoring Configuration Verification"
echo "=================================================="
echo ""

RESOURCE_GROUP="boloo-production-rg"
BACKEND_API="boloo-backend-api"
DATABASE="boloo-database"
APP_INSIGHTS="boloo-backend-insights"
ACTION_GROUP="boloo-alert-notifications"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "1. Verifying Application Insights..."
if az monitor app-insights component show \
  --resource-group $RESOURCE_GROUP \
  --app $APP_INSIGHTS \
  --query "name" -o tsv &>/dev/null; then
  echo -e "${GREEN}✓${NC} Application Insights: Active"
else
  echo -e "${RED}✗${NC} Application Insights: Not Found"
fi

echo ""
echo "2. Verifying Action Group..."
if az monitor action-group show \
  --resource-group $RESOURCE_GROUP \
  --name $ACTION_GROUP \
  --query "name" -o tsv &>/dev/null; then
  EMAIL_COUNT=$(az monitor action-group show \
    --resource-group $RESOURCE_GROUP \
    --name $ACTION_GROUP \
    --query "length(emailReceivers)" -o tsv)
  echo -e "${GREEN}✓${NC} Action Group: Active ($EMAIL_COUNT email recipients)"
else
  echo -e "${RED}✗${NC} Action Group: Not Found"
fi

echo ""
echo "3. Verifying Alerts..."
ALERT_COUNT=$(az monitor metrics alert list \
  --resource-group $RESOURCE_GROUP \
  --query "length([?enabled==\`true\`])" -o tsv)

if [ "$ALERT_COUNT" -eq 8 ]; then
  echo -e "${GREEN}✓${NC} Alerts: $ALERT_COUNT/8 configured and enabled"
else
  echo -e "${YELLOW}!${NC} Alerts: $ALERT_COUNT/8 enabled (expected 8)"
fi

echo ""
echo "4. Verifying Database Security..."
FIREWALL_RULES=$(az postgres flexible-server firewall-rule list \
  --resource-group $RESOURCE_GROUP \
  --name $DATABASE \
  --query "length([?contains(name, 'AllowAll')])" -o tsv)

if [ "$FIREWALL_RULES" -eq 0 ]; then
  echo -e "${GREEN}✓${NC} Database Firewall: Secure (no AllowAll rules)"
else
  echo -e "${RED}✗${NC} Database Firewall: INSECURE (AllowAll rule present)"
fi

echo ""
echo "5. Alert Status Details:"
az monitor metrics alert list \
  --resource-group $RESOURCE_GROUP \
  --query "[].{Alert:name,Enabled:enabled,Severity:severity,HasActions:length(actions)}" \
  --output table

echo ""
echo "6. Database Firewall Rules:"
az postgres flexible-server firewall-rule list \
  --resource-group $RESOURCE_GROUP \
  --name $DATABASE \
  --output table

echo ""
echo "=================================================="
echo "Verification Complete"
echo "=================================================="
echo ""
echo "Quick Links:"
echo "- Application Insights: https://portal.azure.com/#@1cad08ec-88ce-4fad-861f-73474b7eb2d7/resource/subscriptions/417b3ad6-5fc1-47a3-917d-21cf4e3eddfc/resourceGroups/$RESOURCE_GROUP/providers/microsoft.insights/components/$APP_INSIGHTS/overview"
echo "- Alerts: https://portal.azure.com/#@1cad08ec-88ce-4fad-861f-73474b7eb2d7/resource/subscriptions/417b3ad6-5fc1-47a3-917d-21cf4e3eddfc/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Insights/metricAlerts"
echo ""
