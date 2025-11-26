# Making Boloo Chat Human-Like: Complete Guide

## Problem Analysis

**Current Implementation (conversation_service.py)**:
- Mock-based slot extraction (lines 237-278)
- Hardcoded questions in if-elif chains
- No actual Claude API usage for conversation
- Form-filling pattern: "Give me field 1, now give me field 2..."

**Result**: Feels like filling a government form, not chatting.

---

## Solution: Natural Conversational AI

### Architecture Changes

```
OLD:
User → Hardcoded Question → Extract Slot → Next Hardcoded Question

NEW:
User → Claude with Full Context → Natural Response → Background Slot Extraction
```

### Key Principles

1. **Let users speak freely** - Don't force specific answers
2. **Claude maintains conversation** - Not your code
3. **Extract slots in background** - Don't ask for slots explicitly
4. **Use conversation history** - Claude remembers context
5. **Show empathy first** - Acknowledge feelings before asking questions

---

## Implementation

### Step 1: Replace Mock with Real Claude API

**File**: `app/services/conversation_service.py`

```python
from anthropic import Anthropic
import json

class ConversationService:
    def __init__(self, use_mock: bool = False):
        """Now uses real Claude API"""
        self.use_mock = use_mock
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-3-5-sonnet-20241022"

    def process_turn(
        self,
        state: ConversationState,
        user_transcript: str
    ) -> Tuple[str, ConversationState]:
        """Process conversation turn with Claude"""

        # Build conversation history for Claude
        messages = self._build_conversation_history(state)

        # Add user's latest message
        messages.append({
            "role": "user",
            "content": user_transcript
        })

        # Get system prompt based on intent
        system_prompt = self._get_conversational_system_prompt(state.intent)

        # Call Claude with full context
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            temperature=0.7,  # Higher for natural conversation
            system=system_prompt,
            messages=messages
        )

        agent_response = response.content[0].text

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

    def _build_conversation_history(self, state: ConversationState) -> List[Dict]:
        """Convert state.turns to Claude message format"""
        messages = []
        for turn in state.turns:
            messages.append({
                "role": "user" if turn.speaker == "user" else "assistant",
                "content": turn.text_hindi
            })
        return messages

    def _get_conversational_system_prompt(self, intent: IntentType) -> str:
        """Get natural conversation prompt"""

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

        # Use Claude to extract structured data from conversation
        extraction_prompt = f"""From this Hindi conversation, extract information:

Conversation so far:
{self._format_turns_for_extraction(state.turns)}

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

        response = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            temperature=0.1,
            messages=[{"role": "user", "content": extraction_prompt}]
        )

        try:
            extracted = json.loads(response.content[0].text)
            # Update slots silently
            for key, value in extracted.items():
                if value and value != "null":
                    setattr(state.slots, key, value)
        except:
            pass  # Silent failure, don't break conversation
```

### Step 2: Stream Responses for Real-Time Feel

```python
def process_turn_streaming(
    self,
    state: ConversationState,
    user_transcript: str
):
    """Stream responses like Claude Chat"""

    messages = self._build_conversation_history(state)
    messages.append({
        "role": "user",
        "content": user_transcript
    })

    system_prompt = self._get_conversational_system_prompt(state.intent)

    # Use streaming
    with self.client.messages.stream(
        model=self.model,
        max_tokens=1024,
        temperature=0.7,
        system=system_prompt,
        messages=messages
    ) as stream:
        full_response = ""
        for text in stream.text_stream:
            full_response += text
            yield text  # Stream to frontend

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
```

### Step 3: Update Chat Endpoint to Stream

**File**: `app/routers/chat.py` (new file)

```python
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import json

router = APIRouter()

@router.post("/v1/chat/stream")
async def chat_stream(
    message: str,
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Stream chat responses like Claude Chat"""

    # Get conversation state from database
    state = get_conversation_state(db, conversation_id, current_user.id)

    # Stream response
    async def generate():
        service = get_conversation_service()
        for chunk in service.process_turn_streaming(state, message):
            # Send as SSE format
            yield f"data: {json.dumps({'text': chunk})}\n\n"

        # Send completion marker
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
```

### Step 4: Frontend Changes (Mobile)

**Update mobile to use streaming**:

```typescript
// src/services/api.ts
export const streamChatMessage = async (
  message: string,
  conversationId: string,
  onChunk: (text: string) => void
) => {
  const response = await fetch(`${API_URL}/v1/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${await getAuthToken()}`
    },
    body: JSON.stringify({ message, conversation_id: conversationId })
  });

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        if (data.text) {
          onChunk(data.text);
        }
      }
    }
  }
};
```

---

## Comparison: Before vs After

### Before (Current - Form-like):
```
Bot: गांव का नाम बताइए।
User: रायपुर
Bot: यह समस्या कब से है?
User: 6 महीने से
Bot: कितने लोग प्रभावित हैं?
User: 200
```
**Feels like**: Filling a government form

### After (Natural Conversation):
```
User: हमारे गांव में 6 महीने से पानी नहीं आ रहा है
Bot: 6 महीने से! यह तो बहुत लंबा समय है। समझ सकता हूँ कितनी परेशानी होती होगी।
     कौन से गांव की बात हो रही है?
User: रायपुर में
Bot: समझ गया, रायपुर। और बताइए, गांव में कितने लोगों को यह समस्या है?
User: पूरे गांव को, करीब 200 लोग
Bot: ओह, पूरे 200 लोग! यह तो बहुत गंभीर है। क्या आपने इस बारे में
     सरपंच या किसी अधिकारी से बात की थी?
```
**Feels like**: Talking to a caring friend

---

## Key Changes Summary

1. ✅ **Use Claude's Messages API** with full conversation history
2. ✅ **Natural system prompts** that set tone, not rigid instructions
3. ✅ **Extract slots in background** - don't ask for them directly
4. ✅ **Higher temperature** (0.7 instead of 0.2) for natural responses
5. ✅ **Stream responses** for real-time feel like Claude Chat
6. ✅ **Empathy templates** in system prompt, not hardcoded
7. ✅ **Let Claude drive** the conversation, not your if-elif chains

---

## Next Steps

1. Add ANTHROPIC_API_KEY to your .env file
2. Replace conversation_service.py with the new implementation
3. Add streaming endpoint to chat router
4. Update mobile frontend to use streaming
5. Test with real users - adjust system prompts based on feedback

The magic is in the **system prompt** - that's where you define personality!
