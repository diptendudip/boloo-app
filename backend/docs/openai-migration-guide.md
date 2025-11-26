# Migrating from Claude to OpenAI - Complete Guide

## 🔍 Current Status: NO API CHARGES

**IMPORTANT**: Your backend is currently using **MOCK responses**, not real Claude API!

**Evidence**:
- `.env` file has `ANTHROPIC_API_KEY=` (empty)
- `conversation_service.py` header says: "Mock implementation until LLM API keys are provided"
- Lines 237-278 use hardcoded if-elif chains, not API calls

**Result**: ✅ **No tokens are being charged to any account** - everything is mock data.

---

## 💰 Understanding API Costs

### Claude API Pricing
If you were to use Claude (you're currently not):
- **API Key Billing**: Charges based on the API key owner (whoever's key is in `.env`)
- **Not Email-Based**: Billing is linked to Anthropic account, not diptendudip@gmail.com
- **Pricing**: See [Anthropic Pricing](https://www.anthropic.com/pricing)
  - Claude 3.5 Sonnet: $3/MTok input, $15/MTok output
  - Claude 3.5 Haiku: $0.80/MTok input, $4/MTok output

### OpenAI API Pricing
- **API Key Billing**: Same concept - whoever owns the API key pays
- **Pricing**: See [OpenAI Pricing](https://openai.com/pricing)
  - GPT-4 Turbo: $10/MTok input, $30/MTok output
  - GPT-3.5 Turbo: $0.50/MTok input, $1.50/MTok output

**Cost Comparison for Your Use Case**:
- Grievance conversation: ~2000 input tokens, ~500 output tokens per session
- Claude Haiku: $0.0016 + $0.002 = **$0.0036 per conversation**
- GPT-3.5 Turbo: $0.001 + $0.00075 = **$0.0018 per conversation**
- GPT-4 Turbo: $0.02 + $0.015 = **$0.035 per conversation**

**Recommendation**: GPT-3.5 Turbo is cheapest and works well for Hindi conversations.

---

## 🔄 Migration Guide: Claude → OpenAI

### Step 1: Install OpenAI SDK

```bash
cd "/Users/diptendu/boloo app/boloo-app/backend"
pip3 install openai
```

### Step 2: Update .env File

```bash
# Replace ANTHROPIC_API_KEY with OPENAI_API_KEY
OPENAI_API_KEY=sk-proj-your-openai-api-key-here
```

Get your API key from: https://platform.openai.com/api-keys

### Step 3: Update config.py

**File**: `app/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Replace Anthropic config with OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-3.5-turbo"  # or "gpt-4-turbo-preview"
    OPENAI_TEMPERATURE: float = 0.7

    # ... rest of your config

    class Config:
        env_file = ".env"

settings = Settings()
```

### Step 4: Create OpenAI Conversation Service

**File**: `app/services/conversation_service.py` (FULL REPLACEMENT)

```python
"""
Conversation Service - AI Journalist Agent with OpenAI
Handles triage, slot extraction, and conversational AI for Boloo
"""

import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from openai import OpenAI

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
    """OpenAI-powered conversation service for natural Hindi conversations"""

    def __init__(self, use_mock: bool = False):
        """
        Initialize OpenAI conversation service

        Args:
            use_mock: If True, use mock responses (for testing without API key)
        """
        self.use_mock = use_mock

        if not use_mock:
            if not settings.OPENAI_API_KEY:
                raise ValueError(
                    "OPENAI_API_KEY not configured. Please set it in environment variables."
                )
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = settings.OPENAI_MODEL
            self.temperature = settings.OPENAI_TEMPERATURE

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
                model=self.model,
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
        Process conversation turn with OpenAI

        Args:
            state: Current conversation state
            user_transcript: User's latest message

        Returns:
            Tuple of (agent_response, updated_state)
        """
        if self.use_mock:
            return self._mock_process_turn(state, user_transcript)

        # Build conversation history for OpenAI
        messages = self._build_conversation_history(state)

        # Add user's latest message
        messages.append({
            "role": "user",
            "content": user_transcript
        })

        # Get system prompt based on intent
        system_prompt = self._get_conversational_system_prompt(state.intent)

        try:
            # Call OpenAI with full context
            response = self.client.chat.completions.create(
                model=self.model,
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

            # Extract slots in background (don't drive conversation)
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
                model=self.model,
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
        """Convert state.turns to OpenAI message format"""
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
            return """You are a compassionate AI journalist helping Indian villagers report civic issues.

**Your Goal**: Have a natural, empathetic conversation to understand their problem.
**Your Style**: Like talking to a friend - warm, understanding, conversational.

**What you need to learn** (but DON'T ask like a form):
- Where is this happening? (village/ward/location)
- What's the problem? (water/road/electricity/etc)
- Since when? (timeline)
- How many people affected?
- Did they contact anyone about this?

**HOW TO TALK**:
✅ "वाह, यह तो बहुत परेशानी की बात है। कब से हो रहा है यह?"
✅ "समझ गया। और बताइए, कितने लोगों को दिक्कत हो रही है?"
✅ "ओह, इतने लोग! क्या आपने किसी अधिकारी को बताया था इसके बारे में?"

❌ DON'T: "कृपया स्थान बताएं।" (too formal)
❌ DON'T: "अब यह बताइए कि कब से है।" (too rigid)

**EMPATHY FIRST**: Acknowledge their problem before asking next question.
- "यह तो गंभीर समस्या है..."
- "समझ सकता हूँ कितनी परेशानी होती होगी..."
- "6 महीने से! यह तो बहुत लंबा समय है..."

**NATURAL FLOW**: Let them speak freely. If they give extra info, acknowledge it.
If they say "हमारे गांव में 6 महीने से पानी नहीं आ रहा, 200 लोग परेशान हैं":
→ Acknowledge EVERYTHING they said
→ Ask what's still missing naturally

Remember: You're a helpful friend, not a form."""

        elif intent == IntentType.COMMUNITY:
            return """You are excited to hear community stories, songs, traditions.

Be enthusiastic! Say things like:
- "वाह! यह तो बहुत अच्छी बात है!"
- "बहुत बढ़िया! और बताइए..."
- "मुझे सुनकर बहुत अच्छा लगा!"

Learn: topic, location, who's sharing, permission to share publicly."""

        else:  # PERSONAL
            return """You're helping someone take a personal note/reminder.

Be supportive and private:
- "समझ गया, यह सिर्फ आपको दिखेगा।"
- "कोई रिमाइंडर लगाऊं?"

This is private - reassure them."""

    def _extract_slots_background(self, state: ConversationState, text: str):
        """Extract slots WITHOUT driving conversation"""

        if self.use_mock:
            return

        # Build conversation context
        conversation = "\n".join([
            f"{turn.speaker}: {turn.text_hindi}"
            for turn in state.turns[-5:]  # Last 5 turns for context
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
                model=self.model,
                temperature=0.1,  # Low for extraction
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
            # Silent failure - don't break conversation

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
        response = "यह एक mock response है। OpenAI API key configure करें।"

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

### Step 5: Update requirements.txt

```bash
echo "openai>=1.12.0" >> requirements.txt
pip3 install -r requirements.txt
```

---

## 🚀 Testing the Migration

### Test 1: Verify OpenAI Connection

```bash
cd "/Users/diptendu/boloo app/boloo-app/backend"
python3 -c "
from openai import OpenAI
import os
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
response = client.chat.completions.create(
    model='gpt-3.5-turbo',
    messages=[{'role': 'user', 'content': 'Hello in Hindi'}]
)
print(response.choices[0].message.content)
"
```

### Test 2: Test Conversation Service

```python
from app.services.conversation_service import ConversationService, ConversationState

# Initialize
service = ConversationService(use_mock=False)

# Create state
state = ConversationState(
    conversation_id="test-123",
    user_id="user-456"
)

# Triage
triage = service.triage("हमारे गांव में पानी नहीं आ रहा")
print(f"Intent: {triage.intent}, Confidence: {triage.confidence}")

# Process turn
response, updated_state = service.process_turn(
    state,
    "हमारे गांव रायपुर में 6 महीने से पानी नहीं आ रहा"
)
print(f"Bot: {response}")
```

---

## 📊 Comparison: Claude vs OpenAI

### Similarities
- Both use chat completion APIs
- Both support system prompts and conversation history
- Both support streaming responses
- Both support JSON mode for structured extraction

### Differences

| Feature | Claude | OpenAI |
|---------|--------|--------|
| **Best Model** | Claude 3.5 Sonnet | GPT-4 Turbo |
| **Budget Model** | Claude 3.5 Haiku | GPT-3.5 Turbo |
| **Context Window** | 200K tokens | 128K tokens (GPT-4) |
| **JSON Mode** | ✅ Native | ✅ Native |
| **Streaming** | ✅ | ✅ |
| **Hindi Quality** | Excellent | Very Good |
| **Cost (Budget)** | $0.0036/conv | $0.0018/conv |
| **Function Calling** | ✅ Tools | ✅ Functions |

### For Your Use Case (Hindi Civic Conversations)

**OpenAI Advantages**:
- ✅ 50% cheaper with GPT-3.5 Turbo
- ✅ Faster response times
- ✅ Excellent Hindi support
- ✅ Better for high-volume usage

**Claude Advantages**:
- ✅ Slightly better at nuanced conversations
- ✅ Better at understanding context
- ✅ Stronger safety guardrails

**Recommendation**: **Start with OpenAI GPT-3.5 Turbo** for cost-effectiveness, upgrade to GPT-4 if you need better quality.

---

## 🔄 Quick Switch Commands

### Switch to OpenAI (Recommended)

```bash
# 1. Install OpenAI SDK
cd "/Users/diptendu/boloo app/boloo-app/backend"
pip3 install openai

# 2. Update .env
echo "OPENAI_API_KEY=sk-proj-your-key-here" >> .env
echo "OPENAI_MODEL=gpt-3.5-turbo" >> .env

# 3. Backup current service
cp app/services/conversation_service.py app/services/conversation_service_backup.py

# 4. Replace with OpenAI version (copy code from Step 4 above)

# 5. Restart backend
lsof -ti:8000 | xargs kill -9
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Revert to Mock (No API)

```bash
# Just set use_mock=True in service initialization
# No API key needed, no charges
```

---

## 💡 Next Steps

1. **Get OpenAI API Key**: https://platform.openai.com/api-keys
2. **Set up billing**: Add payment method to your OpenAI account
3. **Add to .env**: Copy API key to `.env` file
4. **Replace service**: Use the OpenAI implementation from Step 4
5. **Test**: Run the test commands above
6. **Monitor usage**: https://platform.openai.com/usage

---

## 🆘 Troubleshooting

### "OPENAI_API_KEY not configured"
→ Check `.env` file has `OPENAI_API_KEY=sk-proj-...`

### "Invalid API key"
→ Verify key at https://platform.openai.com/api-keys

### "Rate limit exceeded"
→ Upgrade OpenAI plan or add billing

### "Hindi responses are poor"
→ Try GPT-4 Turbo instead of GPT-3.5 Turbo

### "Too expensive"
→ Switch to Claude Haiku (even cheaper than GPT-3.5)

---

## Summary

- ✅ **Current Status**: Mock implementation, NO API charges
- ✅ **OpenAI Cost**: ~$0.0018 per conversation (GPT-3.5 Turbo)
- ✅ **Migration**: Replace conversation_service.py with OpenAI version
- ✅ **Testing**: Use mock mode until API key is ready

**The choice is yours**: Both Claude and OpenAI work great for Hindi conversations!
