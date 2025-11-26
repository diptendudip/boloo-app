#!/bin/bash
# Check existing Azure OpenAI resources
# This script helps you find your existing Azure OpenAI resources

echo "🔍 Checking for Azure OpenAI Resources"
echo "======================================"
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "⚠️  Azure CLI is not installed"
    echo ""
    echo "To install Azure CLI:"
    echo "  macOS: brew install azure-cli"
    echo "  Linux: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash"
    echo "  Windows: Download from https://aka.ms/installazurecliwindows"
    echo ""
    exit 1
fi

echo "✓ Azure CLI is installed"
echo ""

# Check if logged in
if ! az account show &> /dev/null; then
    echo "⚠️  Not logged into Azure"
    echo ""
    echo "Please run: az login"
    echo ""
    exit 1
fi

echo "✓ Logged into Azure"
echo ""

# Get current subscription
SUBSCRIPTION=$(az account show --query name -o tsv)
echo "Current subscription: $SUBSCRIPTION"
echo ""

# List Azure OpenAI resources
echo "Searching for Azure OpenAI resources..."
echo ""

RESOURCES=$(az cognitiveservices account list --query "[?kind=='OpenAI']" -o json)

if [ "$RESOURCES" = "[]" ]; then
    echo "❌ No Azure OpenAI resources found"
    echo ""
    echo "To create a new Azure OpenAI resource:"
    echo "1. Go to https://portal.azure.com"
    echo "2. Click 'Create a resource'"
    echo "3. Search for 'Azure OpenAI'"
    echo "4. Click 'Create'"
    echo ""
    echo "OR run this command:"
    echo ""
    echo "az cognitiveservices account create \\"
    echo "  --name boloo-openai \\"
    echo "  --resource-group boloo-ai-resources \\"
    echo "  --kind OpenAI \\"
    echo "  --sku S0 \\"
    echo "  --location eastus"
    echo ""
else
    echo "✓ Found Azure OpenAI resources:"
    echo ""

    # Parse and display resources
    echo "$RESOURCES" | python3 -c "
import sys, json
resources = json.load(sys.stdin)
for i, res in enumerate(resources, 1):
    print(f'{i}. Resource Name: {res[\"name\"]}')
    print(f'   Location: {res[\"location\"]}')
    print(f'   Resource Group: {res[\"resourceGroup\"]}')
    print(f'   Endpoint: {res[\"properties\"][\"endpoint\"]}')
    print()
"

    echo ""
    echo "To get API keys for a resource, run:"
    echo ""
    echo "az cognitiveservices account keys list \\"
    echo "  --name <resource-name> \\"
    echo "  --resource-group <resource-group>"
    echo ""

    echo "To list deployments, run:"
    echo ""
    echo "az cognitiveservices account deployment list \\"
    echo "  --name <resource-name> \\"
    echo "  --resource-group <resource-group>"
    echo ""
fi

echo "======================================"
echo "For more information, see: backend/docs/azure-openai-setup.md"
echo ""
