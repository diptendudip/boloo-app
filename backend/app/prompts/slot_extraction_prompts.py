"""
Slot Extraction Prompts for Claude API

Generates prompts for extracting structured data from voice transcripts
based on case type (grievance, community, personal).
"""

from typing import Dict, Any, Optional, List

# Issue taxonomy for grievance classification
ISSUE_TAXONOMY = {
    "water_supply": "Water supply",
    "roads": "Roads and infrastructure",
    "electricity": "Electricity",
    "garbage": "Garbage and sanitation",
    "health": "Healthcare services",
    "education": "Education",
    "corruption": "Corruption",
    "police": "Police and law enforcement",
    "nrega": "NREGA/MGNREGA employment",
    "pension": "Pension and welfare schemes",
    "ration": "PDS/Ration",
    "land": "Land disputes",
    "agriculture": "Agriculture support",
    "housing": "Housing schemes",
    "child_welfare": "Child welfare",
    "women_safety": "Women safety",
    "forest": "Forest and environment",
    "animal": "Animal welfare/husbandry",
    "disaster": "Disaster management",
    "transport": "Public transport",
    "other": "Other"
}


def generate_extraction_prompt(
    transcript_text: str,
    case_kind: str,
    location_hint: Optional[str] = None,
    existing_slots: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate prompt for slot extraction based on case type.

    Args:
        transcript_text: The voice transcript to extract from
        case_kind: Type of case (grievance|community|personal)
        location_hint: Optional location context
        existing_slots: Previously extracted slots for iterative extraction

    Returns:
        Formatted prompt string for Claude API
    """
    if case_kind == "grievance":
        return _grievance_extraction_prompt(transcript_text, location_hint, existing_slots)
    elif case_kind == "community":
        return _community_extraction_prompt(transcript_text, location_hint, existing_slots)
    elif case_kind == "personal":
        return _personal_extraction_prompt(transcript_text, location_hint, existing_slots)
    else:
        raise ValueError(f"Invalid case_kind: {case_kind}")


def _grievance_extraction_prompt(
    transcript: str,
    location_hint: Optional[str],
    existing_slots: Optional[Dict[str, Any]]
) -> str:
    """Generate extraction prompt for grievance cases"""

    existing_context = ""
    if existing_slots:
        existing_context = f"\n\nPreviously extracted information:\n{existing_slots}\n"

    location_context = ""
    if location_hint:
        location_context = f"\nLocation context: {location_hint}"

    taxonomy_list = "\n".join([f"- {k}: {v}" for k, v in ISSUE_TAXONOMY.items()])

    return f"""You are extracting structured information from a citizen's grievance report in India.

Transcript:
"{transcript}"{location_context}{existing_context}

Extract the following slots with confidence scores (0.0-1.0):

**Required Slots:**
1. **location_text**: Village/ward name, area, district, state (e.g., "Koramangala, Raipur, Chhattisgarh")
2. **issue_type**: Match to ONE of these categories:
{taxonomy_list}

3. **when_started**: When the problem began (e.g., "2 weeks ago", "15 दिन से", "yesterday")
4. **scope_affected**: How many people/households affected (e.g., "~50 households", "whole village")
5. **prior_contact**: Whom the citizen contacted before (e.g., "talked to sarpanch", "called district office")
6. **evidence**: Photos, videos, documents mentioned (e.g., "have photos", "will send video")
7. **contact_phone**: Phone number (extract from profile if mentioned)

**Confidence Scoring Rules:**
- 0.9-1.0: Explicitly mentioned with clear details
- 0.7-0.89: Clearly implied or mentioned indirectly
- 0.5-0.69: Somewhat mentioned but vague
- 0.0-0.49: Not mentioned or very uncertain

**Follow-up Questions:**
Generate 1-2 Hindi/English bilingual follow-up questions for missing slots (confidence < 0.7).

**Output Format (JSON):**
{{
  "slots": {{
    "location_text": {{"value": "Raipur, Chhattisgarh", "confidence": 0.85}},
    "issue_type": {{"value": "water_supply", "confidence": 0.95}},
    "when_started": {{"value": "2 weeks ago", "confidence": 0.9}},
    "scope_affected": {{"value": null, "confidence": 0.0}},
    "prior_contact": {{"value": "talked to sarpanch", "confidence": 0.7}},
    "evidence": {{"value": null, "confidence": 0.0}},
    "contact_phone": {{"value": null, "confidence": 0.0}}
  }},
  "follow_up_questions": [
    "कितने लोग/घर प्रभावित हैं? (How many people/households are affected?)"
  ]
}}

Extract as much as possible from the transcript. Use null for missing values."""


def _community_extraction_prompt(
    transcript: str,
    location_hint: Optional[str],
    existing_slots: Optional[Dict[str, Any]]
) -> str:
    """Generate extraction prompt for community story cases"""

    existing_context = ""
    if existing_slots:
        existing_context = f"\n\nPreviously extracted:\n{existing_slots}\n"

    location_context = ""
    if location_hint:
        location_context = f"\nLocation context: {location_hint}"

    return f"""You are extracting information from a community story/event submission.

Transcript:
"{transcript}"{location_context}{existing_context}

Extract these slots with confidence scores:

**Required Slots:**
1. **topic**: What is this about? (e.g., "traditional song", "herbal medicine", "village festival", "local news")
2. **where**: Location/village/area
3. **who**: Who is involved? (narrator, performers, elders, community members)
4. **rights_ok**: Does the narrator have consent/rights to share? (true/false)
5. **media**: Photos/videos mentioned
6. **contact_phone**: Phone number if mentioned

**Output Format (JSON):**
{{
  "slots": {{
    "topic": {{"value": "traditional song performance", "confidence": 0.9}},
    "where": {{"value": "Raipur village", "confidence": 0.85}},
    "who": {{"value": "local musicians", "confidence": 0.8}},
    "rights_ok": {{"value": true, "confidence": 0.7}},
    "media": {{"value": "have video", "confidence": 0.9}},
    "contact_phone": {{"value": null, "confidence": 0.0}}
  }},
  "follow_up_questions": [
    "क्या आपके पास शेयर करने की अनुमति है? (Do you have permission to share?)"
  ]
}}"""


def _personal_extraction_prompt(
    transcript: str,
    location_hint: Optional[str],
    existing_slots: Optional[Dict[str, Any]]
) -> str:
    """Generate extraction prompt for personal note cases"""

    existing_context = ""
    if existing_slots:
        existing_context = f"\n\nPreviously extracted:\n{existing_slots}\n"

    return f"""You are extracting information from a personal note/reminder.

Transcript:
"{transcript}"{existing_context}

Extract these slots:

**Required Slots:**
1. **short_title**: Brief title/summary (10-15 words max)
2. **note**: Full note content (transcript summary)
3. **reminder_when**: When to remind (e.g., "7 days", "next week", "1st June")
4. **convertible**: Could this become a grievance later? (true/false)
5. **contact_phone**: Phone if mentioned

**Output Format (JSON):**
{{
  "slots": {{
    "short_title": {{"value": "School admission forms", "confidence": 0.9}},
    "note": {{"value": "Need to submit forms by end of month", "confidence": 1.0}},
    "reminder_when": {{"value": "7 days", "confidence": 0.85}},
    "convertible": {{"value": true, "confidence": 0.6}},
    "contact_phone": {{"value": null, "confidence": 0.0}}
  }},
  "follow_up_questions": []
}}"""


def get_follow_up_question(slot_name: str, case_kind: str) -> str:
    """
    Generate a follow-up question for a missing slot.

    Args:
        slot_name: Name of the missing slot
        case_kind: Type of case

    Returns:
        Bilingual (Hindi + English) follow-up question
    """
    questions = {
        "grievance": {
            "location_text": "कहाँ है यह समस्या? गाँव/मोहल्ला बताएं। (Where is this problem? Please mention village/area.)",
            "issue_type": "यह किस प्रकार की समस्या है? (What type of problem is this?)",
            "when_started": "यह कब से है? (Since when has this been happening?)",
            "scope_affected": "कितने लोग/घर प्रभावित हैं? (How many people/households are affected?)",
            "prior_contact": "क्या आपने किसी से संपर्क किया? (Have you contacted anyone about this?)",
            "evidence": "क्या आपके पास फोटो/वीडियो है? (Do you have photos/videos?)",
            "contact_phone": "संपर्क नंबर बताएं। (Please provide contact number.)"
        },
        "community": {
            "topic": "यह किस बारे में है? (What is this about?)",
            "where": "यह कहाँ है? (Where is this?)",
            "who": "इसमें कौन शामिल है? (Who is involved in this?)",
            "rights_ok": "क्या आपके पास शेयर करने की अनुमति है? (Do you have permission to share?)",
            "media": "क्या आपके पास फोटो/वीडियो है? (Do you have photos/videos?)"
        },
        "personal": {
            "short_title": "इसे छोटे में कैसे बताएं? (How would you summarize this briefly?)",
            "reminder_when": "कब याद दिलाएं? (When should we remind you?)",
            "convertible": "क्या यह बाद में शिकायत बन सकता है? (Could this become a grievance later?)"
        }
    }

    return questions.get(case_kind, {}).get(slot_name, "कृपया और जानकारी दें। (Please provide more information.)")
