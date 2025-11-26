# Using Azure OpenAI (ChatGPT 3.5 Turbo) - Complete Setup Guide

## 🎯 Why Azure OpenAI?

**Advantages over OpenAI API**:
- ✅ Better enterprise security and compliance
- ✅ Use existing Azure credits
- ✅ Regional data residency (keep data in your region)
- ✅ Better SLA guarantees
- ✅ Integration with Azure ecosystem
- ✅ Same pricing as OpenAI API

**Same Models**: Azure OpenAI provides the exact same GPT-3.5 Turbo model, hosted on Azure infrastructure.

---

## 📋 Prerequisites

1. **Azure Account**: Sign up at https://azure.microsoft.com
2. **Azure OpenAI Service Access**: Request access at https://aka.ms/oai/access
   - Takes 1-2 business days for approval
   - Free to apply
3. **Azure Subscription**: Free tier available or pay-as-you-go

---

## 🚀 Step 1: Create Azure OpenAI Resource

### Via Azure Portal (GUI)

1. **Go to Azure Portal**: https://portal.azure.com
2. **Click "Create a resource"**
3. **Search for "Azure OpenAI"**
4. **Click "Create"**
5. **Fill in details**:
   - **Subscription**: Select your subscription
   - **Resource Group**: Create new → "boloo-ai-resources"
   - **Region**: Select closest to you (e.g., "East US", "West Europe", "Southeast Asia")
   - **Name**: "boloo-openai" (must be globally unique)
   - **Pricing Tier**: Standard S0
6. **Click "Review + Create"** → **"Create"**
7. **Wait 2-3 minutes** for deployment

### Via Azure CLI (Command Line)

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
```

---

## 🔑 Step 2: Get Your API Keys and Endpoint

### Via Azure Portal

1. **Navigate to your Azure OpenAI resource** ("boloo-openai")
2. **Click "Keys and Endpoint"** (left sidebar)
3. **Copy the following**:
   - **KEY 1** (your API key)
   - **Endpoint** (e.g., `https://boloo-openai.openai.azure.com/`)
   - **Region** (e.g., `eastus`)

### Via Azure CLI

```bash
# Get endpoint
az cognitiveservices account show \
  --name boloo-openai \
  --resource-group boloo-ai-resources \
  --query properties.endpoint \
  --output tsv

# Get API key
az cognitiveservices account keys list \
  --name boloo-openai \
  --resource-group boloo-ai-resources \
  --query key1 \
  --output tsv
```

**Example Output**:
```
Endpoint: https://boloo-openai.openai.azure.com/
API Key: 1234567890abcdef1234567890abcdef
Region: eastus
```

---

## 🤖 Step 3: Deploy GPT-3.5 Turbo Model

Azure requires you to explicitly deploy models before using them.

### Via Azure Portal

1. **Go to Azure OpenAI Studio**: https://oai.azure.com
2. **Select your resource** ("boloo-openai")
3. **Click "Deployments"** (left sidebar)
4. **Click "Create new deployment"**
5. **Fill in details**:
   - **Model**: Select "gpt-35-turbo" (GPT-3.5 Turbo)
   - **Model version**: "0613" or latest
   - **Deployment name**: "gpt-35-turbo" (you can name it anything)
   - **Content filter**: Default
6. **Click "Create"**
7. **Wait 30 seconds** for deployment

### Via Azure CLI

```bash
# List available models
az cognitiveservices account deployment list \
  --name boloo-openai \
  --resource-group boloo-ai-resources

# Deploy GPT-3.5 Turbo
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

**Important**: Note your **deployment name** (e.g., "gpt-35-turbo") - you'll need this!

---

## ⚙️ Step 4: Configure Backend

### Update .env File

Add these to `/Users/diptendu/boloo app/boloo-app/backend/.env`:

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://boloo-openai.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-35-turbo
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

**Replace**:
- `your-api-key-here` → Your actual API key from Step 2
- `boloo-openai` → Your resource name
- `gpt-35-turbo` → Your deployment name from Step 3

### Update config.py

**File**: `app/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Azure OpenAI Configuration
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_DEPLOYMENT_NAME: str = "gpt-35-turbo"
    AZURE_OPENAI_API_VERSION: str = "2024-02-15-preview"
    AZURE_OPENAI_TEMPERATURE: float = 0.7

    # Database and other configs...
    DATABASE_URL: str = "postgresql://..."

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## 💻 Step 5: Install Azure OpenAI SDK

```bash
cd "/Users/diptendu/boloo app/boloo-app/backend"
pip3 install openai
```

**Note**: The `openai` package supports both OpenAI API and Azure OpenAI - same SDK!

---

## 🔧 Step 6: Update Conversation Service

**File**: `app/services/conversation_service.py`

```python
"""
Conversation Service - AI Journalist Agent with Azure OpenAI
Handles triage, slot extraction, and conversational AI for Boloo
"""

import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from openai import AzureOpenAI

from app.config import settings
from app.services.conversation_prompts import (
    SYSTEM_PROMPT_TRIAGE,
    SYSTEM_PROMPT_GRIEVANCE,
    SYSTEM_PROMPT_COMMUNITY,
    SYSTEM_PROMPT_PERSONAL,
    TONE_EXAMPLES,
)


class IntentType(str, Enum):
    GRIEVANCE = "grievance"
    COMMUNITY = "community"
    PERSONAL = "personal"
    UNCERTAIN = "uncertain"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class TriageResult:
    """Result of initial triage classification"""
    intent: IntentType
    confidence: ConfidenceLevel
    location_hint: Optional[str] = None
    topic_hint: Optional[str] = None
    reasoning: Optional[str] = None


@dataclass
class ConversationSlots:
    """Slots extracted from conversation"""
    location_text: Optional[str] = None
    location_confidence: ConfidenceLevel = ConfidenceLevel.LOW
    issue_type: Optional[str] = None
    when_started: Optional[str] = None
    scope_affected: Optional[str] = None
    prior_contact: Optional[str] = None
    evidence_mentioned: bool = False
    topic: Optional[str] = None
    who_sharing: Optional[str] = None
    rights_consent: bool = False
    short_title: Optional[str] = None
    note_text: Optional[str] = None
    reminder_when: Optional[str] = None
    convertible_to_grievance: bool = False


@dataclass
class ConversationTurn:
    """Single turn in conversation"""
    speaker: str
    text_hindi: str
    text_english: Optional[str] = None
    timestamp: str = None
    confidence: Optional[float] = None


@dataclass
class ConversationState:
    """Complete conversation state"""
    conversation_id: str
    user_id: str
    intent: Optional[IntentType] = None
    intent_confidence: ConfidenceLevel = ConfidenceLevel.LOW
    slots: ConversationSlots = None
    turns: List[ConversationTurn] = None
    is_complete: bool = False
    formal_summary: Optional[str] = None

    def __post_init__(self):
        if self.slots is None:
            self.slots = ConversationSlots()
        if self.turns is None:
            self.turns = []


class ConversationService:
    """Azure OpenAI-powered conversation service for natural Hindi conversations"""

    def __init__(self, use_mock: bool = False):
        """
        Initialize Azure OpenAI conversation service

        Args:
            use_mock: If True, use mock responses (for testing without API key)
        """
        self.use_mock = use_mock

        if not use_mock:
            if not settings.AZURE_OPENAI_API_KEY or not settings.AZURE_OPENAI_ENDPOINT:
                raise ValueError(
                    "Azure OpenAI not configured. Please set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY."
                )

            # Initialize Azure OpenAI client
            self.client = AzureOpenAI(
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
            )
            self.deployment_name = settings.AZURE_OPENAI_DEPLOYMENT_NAME
            self.temperature = settings.AZURE_OPENAI_TEMPERATURE

    def triage(
        self,
        transcript: str,
        location_hint: Optional[str] = None
    ) -> TriageResult:
        """
        Classify user's intent (grievance, community story, or personal note)

        Args:
            transcript: User's spoken text in Hindi/English
            location_hint: Optional location context

        Returns:
            TriageResult with classification and confidence
        """
        if self.use_mock:
            return self._mock_triage(transcript)

        # Build triage prompt
        prompt = f"""User said: "{transcript}"
{f'Location hint: {location_hint}' if location_hint else ''}

Classify this as:
- "grievance": Civic complaint (water, road, electricity, etc.)
- "community": Cultural sharing (song, tradition, news)
- "personal": Private note/reminder

Return JSON:
{{
  "intent": "grievance|community|personal",
  "confidence": "high|medium|low",
  "reasoning": "brief explanation"
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,  # Azure uses deployment name, not model name
                temperature=0.3,  # Lower for classification
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT_TRIAGE},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            return TriageResult(
                intent=IntentType(result.get("intent", "uncertain")),
                confidence=ConfidenceLevel(result.get("confidence", "low")),
                reasoning=result.get("reasoning")
            )
        except Exception as e:
            print(f"Triage error: {e}")
            return TriageResult(
                intent=IntentType.UNCERTAIN,
                confidence=ConfidenceLevel.LOW,
                reasoning=f"Error: {str(e)}"
            )

    def process_turn(
        self,
        state: ConversationState,
        user_transcript: str
    ) -> Tuple[str, ConversationState]:
        """
        Process conversation turn with Azure OpenAI

        Args:
            state: Current conversation state
            user_transcript: User's latest message

        Returns:
            Tuple of (agent_response, updated_state)
        """
        if self.use_mock:
            return self._mock_process_turn(state, user_transcript)

        # Build conversation history
        messages = self._build_conversation_history(state)

        # Add user's latest message
        messages.append({
            "role": "user",
            "content": user_transcript
        })

        # Get system prompt based on intent
        system_prompt = self._get_conversational_system_prompt(state.intent)

        try:
            # Call Azure OpenAI with full context
            response = self.client.chat.completions.create(
                model=self.deployment_name,  # Azure deployment name
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    *messages
                ]
            )

            agent_response = response.choices[0].message.content

            # Update state
            state.turns.append(ConversationTurn(
                speaker="user",
                text_hindi=user_transcript
            ))
            state.turns.append(ConversationTurn(
                speaker="agent",
                text_hindi=agent_response
            ))

            # Extract slots in background
            self._extract_slots_background(state, user_transcript)

            return agent_response, state

        except Exception as e:
            print(f"Conversation error: {e}")
            return f"माफ़ करें, कुछ गड़बड़ हो गई। ({str(e)})", state

    def process_turn_streaming(
        self,
        state: ConversationState,
        user_transcript: str
    ):
        """
        Stream responses like ChatGPT for real-time feel

        Args:
            state: Current conversation state
            user_transcript: User's latest message

        Yields:
            Text chunks as they arrive
        """
        if self.use_mock:
            yield "Mock streaming not implemented"
            return

        messages = self._build_conversation_history(state)
        messages.append({
            "role": "user",
            "content": user_transcript
        })

        system_prompt = self._get_conversational_system_prompt(state.intent)

        try:
            stream = self.client.chat.completions.create(
                model=self.deployment_name,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    *messages
                ],
                stream=True
            )

            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    text = chunk.choices[0].delta.content
                    full_response += text
                    yield text

            # Update state after streaming completes
            state.turns.append(ConversationTurn(
                speaker="user",
                text_hindi=user_transcript
            ))
            state.turns.append(ConversationTurn(
                speaker="agent",
                text_hindi=full_response
            ))

            # Extract slots in background
            self._extract_slots_background(state, user_transcript)

        except Exception as e:
            yield f"Error: {str(e)}"

    def _build_conversation_history(self, state: ConversationState) -> List[Dict]:
        """Convert state.turns to message format"""
        messages = []
        for turn in state.turns:
            messages.append({
                "role": "user" if turn.speaker == "user" else "assistant",
                "content": turn.text_hindi
            })
        return messages

    def _get_conversational_system_prompt(self, intent: IntentType) -> str:
        """Get natural conversation prompt based on intent"""

        if intent == IntentType.GRIEVANCE:
            return SYSTEM_PROMPT_GRIEVANCE

        elif intent == IntentType.COMMUNITY:
            return SYSTEM_PROMPT_COMMUNITY

        else:  # PERSONAL
            return SYSTEM_PROMPT_PERSONAL

    def _extract_slots_background(self, state: ConversationState, text: str):
        """Extract slots WITHOUT driving conversation"""

        if self.use_mock:
            return

        # Build conversation context
        conversation = "\n".join([
            f"{turn.speaker}: {turn.text_hindi}"
            for turn in state.turns[-5:]
        ])

        extraction_prompt = f"""From this Hindi conversation, extract information:

Conversation:
{conversation}

Latest message: "{text}"

Extract in JSON:
{{
  "location_text": "village/area if mentioned",
  "issue_type": "water/road/electricity/etc if clear",
  "when_started": "timeline if mentioned",
  "scope_affected": "number of people if mentioned",
  "prior_contact": "who they contacted if mentioned"
}}

Return only JSON. Use null for not mentioned."""

        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": extraction_prompt}
                ],
                response_format={"type": "json_object"}
            )

            extracted = json.loads(response.choices[0].message.content)

            # Update slots silently
            for key, value in extracted.items():
                if value and value != "null":
                    setattr(state.slots, key, value)

        except Exception as e:
            print(f"Slot extraction error: {e}")

    def _mock_triage(self, transcript: str) -> TriageResult:
        """Mock triage for testing"""
        text_lower = transcript.lower()

        if any(word in text_lower for word in ["पानी", "सड़क", "बिजली", "water", "road"]):
            return TriageResult(
                intent=IntentType.GRIEVANCE,
                confidence=ConfidenceLevel.HIGH,
                reasoning="Keywords suggest civic issue"
            )
        elif any(word in text_lower for word in ["गीत", "परंपरा", "song", "tradition"]):
            return TriageResult(
                intent=IntentType.COMMUNITY,
                confidence=ConfidenceLevel.MEDIUM,
                reasoning="Keywords suggest community story"
            )
        else:
            return TriageResult(
                intent=IntentType.PERSONAL,
                confidence=ConfidenceLevel.LOW,
                reasoning="Default to personal note"
            )

    def _mock_process_turn(
        self,
        state: ConversationState,
        user_transcript: str
    ) -> Tuple[str, ConversationState]:
        """Mock conversation for testing"""
        response = "यह एक mock response है। Azure OpenAI configure करें।"

        state.turns.append(ConversationTurn(
            speaker="user",
            text_hindi=user_transcript
        ))
        state.turns.append(ConversationTurn(
            speaker="agent",
            text_hindi=response
        ))

        return response, state


# Singleton instance
_conversation_service: Optional[ConversationService] = None


def get_conversation_service(use_mock: bool = False) -> ConversationService:
    """Get or create conversation service singleton"""
    global _conversation_service
    if _conversation_service is None:
        _conversation_service = ConversationService(use_mock=use_mock)
    return _conversation_service
```

---

## ✅ Step 7: Test the Setup

### Test 1: Verify Azure OpenAI Connection

```bash
cd "/Users/diptendu/boloo app/boloo-app/backend"

python3 -c "
from openai import AzureOpenAI
import os

client = AzureOpenAI(
    api_key=os.getenv('AZURE_OPENAI_API_KEY'),
    api_version='2024-02-15-preview',
    azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT')
)

response = client.chat.completions.create(
    model='gpt-35-turbo',  # Your deployment name
    messages=[{'role': 'user', 'content': 'Say hello in Hindi'}]
)

print(response.choices[0].message.content)
"
```

**Expected Output**: Should see Hindi greeting like "नमस्ते! कैसे हैं आप?"

### Test 2: Test Conversation Service

```python
from app.services.conversation_service import ConversationService, ConversationState

# Initialize with Azure OpenAI
service = ConversationService(use_mock=False)

# Create conversation state
state = ConversationState(
    conversation_id="test-123",
    user_id="user-456"
)

# Test triage
triage = service.triage("हमारे गांव में पानी नहीं आ रहा")
print(f"Intent: {triage.intent}, Confidence: {triage.confidence}")

# Test conversation
response, updated_state = service.process_turn(
    state,
    "हमारे गांव रायपुर में 6 महीने से पानी नहीं आ रहा"
)
print(f"Bot: {response}")
```

### Test 3: Restart Backend

```bash
# Kill existing backend
lsof -ti:8000 | xargs kill -9

# Start backend
cd "/Users/diptendu/boloo app/boloo-app/backend"
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Check logs**: Should see "Azure OpenAI initialized successfully"

---

## 💰 Pricing

Azure OpenAI has the **same pricing** as OpenAI API:

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| GPT-3.5 Turbo | $0.50 | $1.50 |

**Example**: A typical grievance conversation:
- Input: ~2000 tokens → $0.001
- Output: ~500 tokens → $0.00075
- **Total**: ~$0.0018 per conversation

**Monthly estimate** (1000 conversations): ~$1.80/month

---

## 🔍 Monitoring Usage

### Via Azure Portal

1. **Go to your Azure OpenAI resource**
2. **Click "Metrics"** (left sidebar)
3. **View**:
   - Total tokens processed
   - Requests per minute
   - Error rates
   - Latency

### Via Azure CLI

```bash
az monitor metrics list \
  --resource "/subscriptions/{subscription-id}/resourceGroups/boloo-ai-resources/providers/Microsoft.CognitiveServices/accounts/boloo-openai" \
  --metric "TotalTokens" \
  --start-time "2024-01-01T00:00:00Z" \
  --end-time "2024-12-31T23:59:59Z"
```

---

## 🛡️ Security Best Practices

1. **Use Managed Identity** (for production):
   ```python
   from azure.identity import DefaultAzureCredential

   credential = DefaultAzureCredential()
   client = AzureOpenAI(
       azure_ad_token_provider=credential,
       api_version="2024-02-15-preview",
       azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
   )
   ```

2. **Rotate API Keys** regularly (every 90 days)
3. **Use Azure Key Vault** for storing secrets
4. **Enable Content Filters** in Azure OpenAI Studio

---

## 🆘 Troubleshooting

### "Resource not found"
→ Check deployment name matches: `AZURE_OPENAI_DEPLOYMENT_NAME=gpt-35-turbo`

### "Access denied"
→ Verify you've been approved for Azure OpenAI access

### "Rate limit exceeded"
→ Increase quota in Azure Portal → Quotas

### "Invalid endpoint"
→ Check endpoint format: `https://{resource-name}.openai.azure.com/`

### "Model not found"
→ Deploy the model in Azure OpenAI Studio first

---

## 📊 Azure vs OpenAI API Comparison

| Feature | Azure OpenAI | OpenAI API |
|---------|-------------|------------|
| **Pricing** | Same | Same |
| **Models** | Same (GPT-3.5, GPT-4) | Same |
| **Setup** | More steps (requires deployment) | Simpler |
| **Security** | Better (Azure AD, VNets) | Basic |
| **Compliance** | SOC 2, HIPAA, ISO | Basic |
| **Region** | Choose your region | US-based |
| **SLA** | 99.9% uptime guarantee | Best effort |

---

## 🎯 Quick Setup Commands

```bash
# 1. Install SDK
pip3 install openai

# 2. Set environment variables
cat >> "/Users/diptendu/boloo app/boloo-app/backend/.env" << EOF
AZURE_OPENAI_ENDPOINT=https://boloo-openai.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-35-turbo
AZURE_OPENAI_API_VERSION=2024-02-15-preview
EOF

# 3. Backup and replace conversation service
cp app/services/conversation_service.py app/services/conversation_service_backup.py
# (Copy the Azure OpenAI code from Step 6)

# 4. Restart backend
lsof -ti:8000 | xargs kill -9
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Summary

✅ **Azure OpenAI is perfect for your use case** - same pricing, better security, enterprise-grade!
✅ **Complete setup takes ~15 minutes** once you have Azure access
✅ **Same code patterns** as OpenAI API (just use `AzureOpenAI` instead of `OpenAI`)
✅ **Better for production** with SLA, compliance, and regional options

**Next**: Follow the steps above to set up Azure OpenAI!
