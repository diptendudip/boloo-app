# Conversation Memory Fix - AI Repeating Questions

**Date**: 2025-11-12
**Status**: Fix Identified, Implementation Needed
**Priority**: CRITICAL

## Problem

The AI repeatedly asks the same questions even though the user has already provided answers. Example:
- User says "Che mahine se" (6 months)
- AI asks again "कब से यह समस्या है?" (When did this problem start?)

## Root Causes

### 1. Azure OpenAI Not Following Instructions
- System prompt explicitly says "NEVER REPEAT QUESTIONS"
- But GPT-4o-mini sometimes ignores this
- Temperature is 0.7 (too high for structured tasks)

### 2. Weak Duplicate Detection
- Only checks LAST turn (line 332-345 in chat.py)
- Should check ENTIRE conversation history
- Should check if field is in `collected_data`

### 3. Missing Fields Include Already-Collected Data
- `completeness_analyzer` might return fields we already have
- Need to filter `missing_fields` before passing to AI

## Solutions

### Fix 1: Strengthen Duplicate Question Detection (CRITICAL)

In `/backend/app/routers/chat.py` around line 332:

```python
# OLD CODE (only checks last turn):
if conversation.turns:
    last_turn = conversation.turns[-1]
    if last_turn.ai_question_asked and last_turn.ai_question_asked.strip() == ai_response_hi.strip():
        logger.warning(f"[Chat] Duplicate question detected...")

# NEW CODE (check ALL turns + collected_data):
# Check for duplicate questions across ENTIRE history
asked_questions = {turn.ai_question_asked.strip().lower() for turn in conversation.turns if turn.ai_question_asked}

if ai_response_hi.strip().lower() in asked_questions:
    logger.warning(f"[Chat] 🚫 DUPLICATE QUESTION DETECTED: '{ai_response_hi[:50]}...'")
    logger.warning(f"[Chat] This question was already asked in a previous turn.")

    # Skip to NEXT missing field
    if not completeness_result["is_complete"] and len(completeness_result["missing_fields"]) > 1:
        # Find first field NOT in collected_data
        for missing_field in completeness_result["missing_fields"]:
            field_name = missing_field.get("field")
            if field_name and field_name not in completeness_result["extracted_data"]:
                ai_response_hi = missing_field.get("prompt_hi", "कृपया और जानकारी दें")
                ai_response_en = missing_field.get("prompt_en", "Please provide more information")
                logger.info(f"[Chat] ✅ Switched to next field: {field_name}")
                break
        else:
            # All fields collected, ask for summary
            ai_response_hi = "धन्यवाद! क्या मैं आपको सारांश दिखाऊं?"
            ai_response_en = "Thank you! Should I show you the summary?"
    else:
        ai_response_hi = "क्या आप कुछ और जोड़ना चाहेंगे?"
        ai_response_en = "Would you like to add anything else?"
```

### Fix 2: Filter Missing Fields to Exclude Collected Data

In `/backend/app/routers/chat.py` around line 306:

```python
# BEFORE passing to Azure OpenAI, filter out already-collected fields
actually_missing_fields = [
    field for field in completeness_result["missing_fields"]
    if field.get("field") not in completeness_result["extracted_data"]
]

logger.info(f"[Chat] Filtered missing fields: {[f.get('field') for f in actually_missing_fields]}")

ai_result = ai_service.generate_conversation_response(
    user_message=user_message,
    conversation_history=history,
    missing_fields=actually_missing_fields,  # Use filtered list
    collected_data=completeness_result["extracted_data"],
    is_complete=completeness_result["is_complete"] or len(actually_missing_fields) == 0
)
```

### Fix 3: Lower AI Temperature for Consistency

In `/backend/app/config.py`:

```python
# Change from 0.7 to 0.3 for more deterministic responses
AZURE_OPENAI_TEMPERATURE: float = Field(default=0.3, env="AZURE_OPENAI_TEMPERATURE")
```

### Fix 4: Enhance System Prompt

In `/backend/app/services/azure_openai_service.py` around line 455:

```python
user_prompt = f"""बातचीत का संदर्भ:
{conversation_context}

उपयोगकर्ता का नवीनतम संदेश: "{user_message}"

पहले से एकत्रित जानकारी: {collected_summary}

🚨 CRITICAL: These fields are ALREADY COLLECTED - DO NOT ask about them again:
{', '.join(collected_data.keys())}

ONLY ask about these missing fields:
अगली आवश्यक जानकारी: {next_field_name}
सुझाया गया प्रश्न: {next_field_prompt}

कृपया एक प्राकृतिक, सहानुभूतिपूर्ण प्रतिक्रिया लिखें जो:
1. उपयोगकर्ता के संदेश को स्वीकार करती है
2. सहानुभूति दिखाती है
3. केवल ऊपर दी गई अगली जानकारी पूछती है (पहले से एकत्रित जानकारी के बारे में नहीं!)

महत्वपूर्ण: रोबोटिक न हों! जैसे आप किसी दोस्त से बात कर रहे हों वैसे लिखें।"""
```

## Implementation Priority

1. **Fix 1** (Duplicate Detection) - IMPLEMENT IMMEDIATELY - Most Critical
2. **Fix 2** (Filter Missing Fields) - IMPLEMENT IMMEDIATELY - Prevents root cause
3. **Fix 3** (Lower Temperature) - Easy change, big impact
4. **Fix 4** (Enhanced Prompt) - Additional safety layer

## Testing

After implementing:
1. Create new conversation with water problem
2. Provide location in first message
3. Verify AI doesn't ask for location again
4. Check logs for "DUPLICATE QUESTION DETECTED"
5. Verify "Filtered missing fields" excludes collected data

## Files to Modify

1. `/backend/app/routers/chat.py` (lines 306-308, 332-346)
2. `/backend/app/services/azure_openai_service.py` (line 455)
3. `/backend/app/config.py` (AZURE_OPENAI_TEMPERATURE)

## Expected Outcome

- AI should NEVER ask same question twice
- Collected data should persist across turns
- User should only be asked for MISSING information
- Much better UX - no frustration from repeated questions
