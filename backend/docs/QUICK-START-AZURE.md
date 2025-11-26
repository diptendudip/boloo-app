# Azure OpenAI Quick Start Guide

## ✅ Your Current Setup

**What you already have:**
- ✅ Azure CLI installed (`/usr/local/bin/az`)
- ✅ OpenAI SDK installed (version 1.10.0)
- ✅ Backend is currently using mock responses (NO API charges)

**What you need:**
- Azure OpenAI resource in Azure Portal
- API key and endpoint from Azure

---

## 🚀 Quick Start (3 Steps)

### Option 1: Already Have Azure OpenAI Resource?

If you already have an Azure OpenAI resource created:

```bash
cd "/Users/diptendu/boloo app/boloo-app/backend"

# Check your existing Azure resources
./scripts/check-azure-resources.sh

# Configure the backend with your credentials
./scripts/setup-azure-openai.sh
```

The script will ask you for:
1. Azure OpenAI Endpoint (e.g., `https://your-resource.openai.azure.com/`)
2. API Key (from Azure Portal)
3. Deployment name (e.g., `gpt-35-turbo`)

### Option 2: Need to Create Azure OpenAI Resource?

**Step 1: Request Azure OpenAI Access** (if you haven't)
1. Go to: https://aka.ms/oai/access
2. Fill out the form
3. Wait 1-2 business days for approval

**Step 2: Create Azure OpenAI Resource**

```bash
# Login to Azure
az login

# Create resource group
az group create --name boloo-ai-resources --location eastus

# Create Azure OpenAI resource
az cognitiveservices account create \
  --name boloo-openai \
  --resource-group boloo-ai-resources \
  --kind OpenAI \
  --sku S0 \
  --location eastus

# Get your endpoint
az cognitiveservices account show \
  --name boloo-openai \
  --resource-group boloo-ai-resources \
  --query properties.endpoint

# Get your API key
az cognitiveservices account keys list \
  --name boloo-openai \
  --resource-group boloo-ai-resources \
  --query key1
```

**Step 3: Deploy GPT-3.5 Turbo Model**

```bash
# Deploy the model
az cognitiveservices account deployment create \
  --name boloo-openai \
  --resource-group boloo-ai-resources \
  --deployment-name gpt-35-turbo \
  --model-name gpt-35-turbo \
  --model-version "0613" \
  --model-format OpenAI \
  --sku-capacity 120 \
  --sku-name "Standard"
```

**Step 4: Configure Backend**

```bash
cd "/Users/diptendu/boloo app/boloo-app/backend"

# Run the setup script
./scripts/setup-azure-openai.sh
```

---

## 📋 What the Setup Script Does

The `setup-azure-openai.sh` script will:

1. ✅ Install OpenAI SDK (already installed!)
2. ✅ Update your `.env` file with Azure OpenAI credentials
3. ✅ Test the connection to Azure OpenAI
4. ✅ Verify everything works

**It will NOT**:
- ❌ Update `config.py` (you need to do this manually)
- ❌ Update `conversation_service.py` (you need to do this manually)

---

## 🔧 Manual Configuration (After Running Script)

### 1. Update `app/config.py`

Replace the Anthropic configuration with Azure OpenAI:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Azure OpenAI Configuration
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_DEPLOYMENT_NAME: str = "gpt-35-turbo"
    AZURE_OPENAI_API_VERSION: str = "2024-02-15-preview"
    AZURE_OPENAI_TEMPERATURE: float = 0.7

    # ... rest of your config

    class Config:
        env_file = ".env"

settings = Settings()
```

### 2. Update `app/services/conversation_service.py`

**Full replacement code is in**: `docs/azure-openai-setup.md` (Step 6)

**Key changes:**
```python
from openai import AzureOpenAI  # Change this line

# In __init__:
self.client = AzureOpenAI(
    api_key=settings.AZURE_OPENAI_API_KEY,
    api_version=settings.AZURE_OPENAI_API_VERSION,
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
)
self.deployment_name = settings.AZURE_OPENAI_DEPLOYMENT_NAME

# In API calls, use:
model=self.deployment_name  # Instead of model name
```

### 3. Restart Backend

```bash
cd "/Users/diptendu/boloo app/boloo-app/backend"

# Kill existing backend
lsof -ti:8000 | xargs kill -9

# Start fresh
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🧪 Testing

### Test 1: Quick Connection Test

```bash
cd "/Users/diptendu/boloo app/boloo-app/backend"

python3 -c "
from openai import AzureOpenAI
import os

client = AzureOpenAI(
    api_key=os.getenv('AZURE_OPENAI_API_KEY'),
    api_version=os.getenv('AZURE_OPENAI_API_VERSION'),
    azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT')
)

response = client.chat.completions.create(
    model=os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-35-turbo'),
    messages=[{'role': 'user', 'content': 'Say hello in Hindi'}]
)

print(response.choices[0].message.content)
"
```

**Expected output**: Should see a Hindi greeting like "नमस्ते! कैसे हैं आप?"

### Test 2: Test via API

```bash
# Make sure backend is running, then:
curl -X POST http://localhost:8000/v1/cases/triage \
  -H "Content-Type: application/json" \
  -d '{
    "transcript_text": "हमारे गांव में पानी नहीं आ रहा",
    "location_hint": "Raipur"
  }'
```

**Expected output**: Should see intent classification (grievance/community/personal)

---

## 💰 Cost Estimation

**GPT-3.5 Turbo Pricing:**
- $0.50 per 1M input tokens
- $1.50 per 1M output tokens

**Typical Boloo Conversation:**
- Input: ~2,000 tokens → $0.001
- Output: ~500 tokens → $0.00075
- **Total: ~$0.0018 per conversation**

**Monthly Cost Estimates:**
- 100 conversations/month: $0.18
- 1,000 conversations/month: $1.80
- 10,000 conversations/month: $18.00

---

## 🆘 Troubleshooting

### "Resource not found"
**Cause**: Deployment name doesn't match
**Fix**: Check deployment name in Azure Portal or run:
```bash
az cognitiveservices account deployment list \
  --name boloo-openai \
  --resource-group boloo-ai-resources
```

### "Access denied" or "Not authorized"
**Cause**: Haven't been approved for Azure OpenAI
**Fix**: Apply at https://aka.ms/oai/access

### "InvalidEndpoint"
**Cause**: Wrong endpoint format
**Fix**: Endpoint should be: `https://{resource-name}.openai.azure.com/`

### "openai.APIError: The API deployment for this resource does not exist"
**Cause**: Model not deployed
**Fix**: Deploy model in Azure OpenAI Studio or via CLI (see Step 3 above)

---

## 📚 Full Documentation

- **Complete setup guide**: `docs/azure-openai-setup.md`
- **OpenAI vs Claude comparison**: `docs/openai-migration-guide.md`
- **Conversational AI upgrade**: `docs/conversational-ai-upgrade.md`

---

## 🎯 Summary: What You Need to Do

1. **Check if you have Azure OpenAI access**: https://aka.ms/oai/access
2. **Create/find your Azure OpenAI resource** (via Portal or CLI)
3. **Run setup script**: `./scripts/setup-azure-openai.sh`
4. **Update config.py** (see section above)
5. **Update conversation_service.py** (see docs/azure-openai-setup.md)
6. **Restart backend**
7. **Test** (see Testing section above)

---

## ✨ Benefits of Azure OpenAI

- ✅ Same pricing as OpenAI API
- ✅ Better enterprise security and compliance
- ✅ Regional data residency
- ✅ 99.9% SLA guarantee
- ✅ Integration with Azure ecosystem
- ✅ Use Azure credits if you have them

**Ready to get started?** Run: `./scripts/check-azure-resources.sh`
