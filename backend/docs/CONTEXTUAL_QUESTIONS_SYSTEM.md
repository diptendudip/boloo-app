# Dynamic Context-Aware Question System

## Overview

The dynamic context-aware question system solves the scalability problem of handling thousands of different problem types with varying information requirements. Instead of asking the same fixed set of questions for all grievances, the system intelligently adapts questions based on the specific problem type.

## Problem Statement

**User Feedback:**
> "there will be thousands such use cases with numerous permutation and combination how to make sure its relevant and contextual."

**Challenge:**
- Fixed field systems don't scale to diverse problem types
- Water supply issues need different information than corruption cases
- Road problems require different context than health emergencies
- Asking irrelevant questions frustrates rural users

## Solution Architecture

### Two-Tier Field System

#### 1. Universal Required Fields (Apply to ALL)
```python
UNIVERSAL_REQUIRED_FIELDS = {
    "issue_description": "What is the problem?",
    "location": "Where is it happening?"
}
```

These 2 fields are ALWAYS required regardless of problem type. They provide the minimum information government needs to act: **WHAT** and **WHERE**.

#### 2. Contextual Fields (Dynamically Selected)
```python
CONTEXTUAL_FIELDS = {
    # Water/Electricity
    "service_duration": {
        "applies_to": ["water", "electricity", "drainage"],
        "prompt_hi": "यह समस्या कब से हो रही है?"
    },

    # Road/Infrastructure
    "road_landmark": {
        "applies_to": ["road", "bridge", "infrastructure"],
        "prompt_hi": "कौन सी सड़क या लैंडमार्क?"
    },

    # Health/Medical
    "health_affected_count": {
        "applies_to": ["health", "medical", "disease"],
        "prompt_hi": "कितने लोग बीमार हैं?"
    },

    # Education/School
    "school_name": {
        "applies_to": ["education", "school"],
        "prompt_hi": "कौन से स्कूल की बात हो रही है?"
    },

    # Corruption/Bribery
    "office_name": {
        "applies_to": ["corruption", "bribery"],
        "prompt_hi": "कौन सा ऑफिस/विभाग?"
    },

    # General (applies to all)
    "affected_scope": {
        "applies_to": ["all"],
        "prompt_hi": "कितने लोग प्रभावित हैं?"
    }
}
```

## How It Works

### Flow Diagram

```
User Reports Issue
    ↓
Extract Issue Description & Location (Universal Fields)
    ↓
AI Detects Problem Type (e.g., "water", "all")
    ↓
Select Contextual Fields for Problem Type
    ↓
Build Dynamic Field Schema (Universal + Contextual)
    ↓
Ask Contextual Questions Based on Problem Type
    ↓
Complete Grievance
```

### Example: Water Supply Problem

**Turn 1:**
- User: "हमारे गाँव रायपुर में पानी नहीं आ रहा है"
- AI Extracts:
  - issue_description = "पानी नहीं आ रहा"
  - location = "रायपुर"
- AI Detects: problem_types = ["water", "all"]
- AI Selects Contextual Fields:
  - service_duration (applies to "water")
  - service_frequency (applies to "water")
  - affected_scope (applies to "all")
- AI Asks: "यह समस्या कब से हो रही है?"

**Turn 2:**
- User: "15 दिन से"
- AI Extracts: service_duration = "15 दिन"
- AI Asks: "दिन में कितने घंटे पानी मिलती है?"

**Turn 3:**
- User: "नहीं पता"
- AI Accepts: service_frequency = "unknown"
- AI Asks: "यह समस्या सिर्फ आपको है या और लोगों को भी?"

### Example: Road Damage Problem

**Turn 1:**
- User: "दुर्ग में मुख्य सड़क पर गड्ढे हैं"
- AI Detects: problem_types = ["road", "all"]
- AI Selects Different Contextual Fields:
  - road_landmark (applies to "road")
  - damage_severity (applies to "road")
  - affected_scope (applies to "all")
- AI Asks: "कौन सी सड़क या नजदीक का लैंडमार्क बताएं।"

**Notice:** Water-specific fields (service_duration, service_frequency) are NOT asked for road problems!

## Implementation

### 1. Problem Type Detection
Uses Azure OpenAI to classify issue description into categories:

```python
def _detect_problem_type(self, issue_description: str) -> List[str]:
    """
    Analyze grievance and identify problem categories.

    Categories:
    - water, electricity, drainage, sewage
    - road, bridge, infrastructure
    - health, medical, disease
    - education, school
    - corruption, bribery, harassment
    - all (always included)
    """
```

### 2. Contextual Field Selection
Filters fields based on detected problem types:

```python
def _select_contextual_fields(self, problem_types: List[str]) -> Dict:
    """
    Select fields where 'applies_to' matches detected problem types.
    """
    selected_fields = {}
    for field_name, field_config in CONTEXTUAL_FIELDS.items():
        applies_to = field_config.get("applies_to", [])
        if any(problem_type in applies_to for problem_type in problem_types):
            selected_fields[field_name] = field_config
    return selected_fields
```

### 3. Dynamic Schema Building
Combines universal and contextual fields:

```python
def _build_dynamic_field_schema(self, extracted_data: Dict) -> Dict:
    """
    Start with 2 universal fields.
    If issue_description exists, detect problem type and add contextual fields.
    """
    schema = dict(UNIVERSAL_REQUIRED_FIELDS)

    if extracted_data and extracted_data.get("issue_description"):
        problem_types = self._detect_problem_type(extracted_data["issue_description"])
        contextual = self._select_contextual_fields(problem_types)
        schema.update(contextual)

    return schema
```

## Benefits

### 1. Scalability
- Can handle thousands of problem types
- Easy to add new categories and fields
- No need to modify core logic for new problem types

### 2. Relevance
- Only asks questions relevant to the specific problem
- Reduces user frustration from irrelevant questions
- Faster conversation completion

### 3. Flexibility
- Fields can apply to multiple problem types
- "all" category for universal questions
- Easy to adjust field mappings

### 4. Maintainability
- Centralized field definitions
- Clear separation of universal vs contextual
- Simple to add new problem categories

## Adding New Problem Types

### Example: Adding "Animal Problem" Category

1. **Add to problem type detection categories:**
```python
# In _detect_problem_type() prompt
"""
- animal: Stray animals, animal attacks, cattle issues
"""
```

2. **Add contextual fields:**
```python
CONTEXTUAL_FIELDS = {
    # ... existing fields ...

    "animal_type": {
        "name_hi": "कौन सा जानवर",
        "applies_to": ["animal"],
        "prompt_hi": "कौन सा जानवर है?"
    },
    "animal_count": {
        "name_hi": "कितने जानवर",
        "applies_to": ["animal"],
        "prompt_hi": "कितने जानवर हैं?"
    }
}
```

3. **Done!** The system will automatically:
   - Detect animal problems
   - Select animal-specific fields
   - Ask relevant questions

## Testing

Comprehensive test suite validates:
- Problem type detection accuracy
- Contextual field selection logic
- Dynamic schema building
- End-to-end conversation flows

Run tests:
```bash
cd backend
python3 -m pytest tests/test_contextual_completeness.py -v
```

Test results:
- ✅ 18 tests covering all problem types
- ✅ Water, electricity, road, health, education, corruption scenarios
- ✅ Dynamic field selection
- ✅ End-to-end conversation flows

## Files Modified

1. `app/services/completeness_analyzer.py`
   - Added UNIVERSAL_REQUIRED_FIELDS
   - Added CONTEXTUAL_FIELDS
   - Implemented _detect_problem_type()
   - Implemented _select_contextual_fields()
   - Implemented _build_dynamic_field_schema()
   - Updated _build_analysis_prompt() to use dynamic schema

2. `tests/test_contextual_completeness.py`
   - Comprehensive test suite for all problem types

## Performance

- **Problem Type Detection:** ~1-2 seconds (Azure OpenAI GPT-4o-mini)
- **Field Selection:** <1ms (local filtering)
- **Schema Building:** <1ms (dictionary operations)
- **Total Overhead:** ~1-2 seconds per conversation (only once when issue_description is provided)

## Future Enhancements

1. **Caching:** Cache problem type classifications for similar issues
2. **Learning:** Train model on historical data to improve classification
3. **Hybrid Approach:** Combine AI classification with keyword matching for speed
4. **User Feedback:** Allow users to correct problem type if misclassified
5. **Multi-category:** Handle issues that span multiple categories (e.g., school building damage)

## Conclusion

The dynamic context-aware question system provides a scalable, maintainable solution for handling diverse problem types in rural India grievance reporting. By intelligently adapting questions based on problem context, it reduces user frustration while collecting the most relevant information for government action.

**Key Achievement:** System now handles thousands of use cases with "permutation and combination" through AI-driven contextual field selection instead of fixed field schemas.
