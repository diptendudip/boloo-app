#!/bin/bash
# Quick Setup Script for Azure OpenAI Integration
# Run this script after you have created your Azure OpenAI resource

set -e  # Exit on error

echo "🚀 Boloo Azure OpenAI Setup Script"
echo "=================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to prompt for input
prompt_input() {
    local prompt="$1"
    local var_name="$2"
    local default="$3"

    if [ -n "$default" ]; then
        read -p "$prompt [$default]: " input
        input="${input:-$default}"
    else
        read -p "$prompt: " input
    fi

    eval "$var_name='$input'"
}

echo -e "${YELLOW}Step 1: Install OpenAI SDK${NC}"
echo "=================================="
pip3 install openai
echo -e "${GREEN}✓ OpenAI SDK installed${NC}"
echo ""

echo -e "${YELLOW}Step 2: Configure Azure OpenAI${NC}"
echo "=================================="
echo "You need the following from Azure Portal:"
echo "1. Go to https://portal.azure.com"
echo "2. Navigate to your Azure OpenAI resource"
echo "3. Click 'Keys and Endpoint' in the left sidebar"
echo ""

# Get Azure OpenAI configuration from user
prompt_input "Enter your Azure OpenAI Endpoint (e.g., https://boloo-openai.openai.azure.com/)" ENDPOINT ""
prompt_input "Enter your Azure OpenAI API Key" API_KEY ""
prompt_input "Enter your deployment name" DEPLOYMENT "gpt-35-turbo"
prompt_input "Enter API version" API_VERSION "2024-02-15-preview"

# Validate inputs
if [ -z "$ENDPOINT" ] || [ -z "$API_KEY" ]; then
    echo -e "${RED}Error: Endpoint and API Key are required!${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 3: Update .env file${NC}"
echo "=================================="

# Backup existing .env if it exists
if [ -f ".env" ]; then
    cp .env .env.backup
    echo -e "${GREEN}✓ Backed up existing .env to .env.backup${NC}"
fi

# Check if Azure OpenAI variables already exist in .env
if grep -q "AZURE_OPENAI_ENDPOINT" .env 2>/dev/null; then
    echo -e "${YELLOW}Azure OpenAI variables already exist in .env${NC}"
    echo "Updating existing values..."

    # Update existing values
    sed -i.bak "s|AZURE_OPENAI_ENDPOINT=.*|AZURE_OPENAI_ENDPOINT=$ENDPOINT|g" .env
    sed -i.bak "s|AZURE_OPENAI_API_KEY=.*|AZURE_OPENAI_API_KEY=$API_KEY|g" .env
    sed -i.bak "s|AZURE_OPENAI_DEPLOYMENT_NAME=.*|AZURE_OPENAI_DEPLOYMENT_NAME=$DEPLOYMENT|g" .env
    sed -i.bak "s|AZURE_OPENAI_API_VERSION=.*|AZURE_OPENAI_API_VERSION=$API_VERSION|g" .env
    rm .env.bak
else
    echo "Adding new Azure OpenAI configuration..."

    # Add new configuration
    cat >> .env << EOF

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=$ENDPOINT
AZURE_OPENAI_API_KEY=$API_KEY
AZURE_OPENAI_DEPLOYMENT_NAME=$DEPLOYMENT
AZURE_OPENAI_API_VERSION=$API_VERSION
AZURE_OPENAI_TEMPERATURE=0.7
EOF
fi

echo -e "${GREEN}✓ .env file updated${NC}"
echo ""

echo -e "${YELLOW}Step 4: Test Azure OpenAI Connection${NC}"
echo "=================================="

# Test Azure OpenAI connection
python3 << EOF
import os
from openai import AzureOpenAI

try:
    client = AzureOpenAI(
        api_key="$API_KEY",
        api_version="$API_VERSION",
        azure_endpoint="$ENDPOINT"
    )

    response = client.chat.completions.create(
        model="$DEPLOYMENT",
        messages=[
            {"role": "user", "content": "Say hello in Hindi"}
        ],
        max_tokens=50
    )

    print("\n${GREEN}✓ Azure OpenAI connection successful!${NC}")
    print(f"\nTest response: {response.choices[0].message.content}\n")

except Exception as e:
    print(f"\n${RED}✗ Error connecting to Azure OpenAI: {e}${NC}\n")
    exit(1)
EOF

echo ""
echo -e "${YELLOW}Step 5: Next Steps${NC}"
echo "=================================="
echo "1. ✓ OpenAI SDK installed"
echo "2. ✓ .env file configured"
echo "3. ✓ Azure OpenAI connection tested"
echo ""
echo "Next, you need to:"
echo "1. Update app/config.py (see docs/azure-openai-setup.md Step 4)"
echo "2. Update app/services/conversation_service.py (see docs/azure-openai-setup.md Step 6)"
echo "3. Restart the backend server"
echo ""
echo -e "${GREEN}Setup complete! 🎉${NC}"
echo ""
echo "📚 Full documentation: backend/docs/azure-openai-setup.md"
echo ""
