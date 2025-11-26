"""
Prompts for intent classification and triage using Claude API.

Handles code-mixed language (Hindi + English + Chhattisgarhi) and provides
context-aware classification for Chhattisgarh citizen reporting.
"""

from typing import Dict, Optional, Any


# Issue taxonomy for grievance classification
# Based on common civic issues in Chhattisgarh
ISSUE_TAXONOMY = [
    # Water & Sanitation
    "water_supply",
    "water_quality",
    "sewage_drainage",
    "garbage_collection",

    # Infrastructure
    "road_repair",
    "road_maintenance",
    "street_lights",
    "public_transport",

    # Environment
    "tree_cutting",
    "noise_pollution",
    "air_pollution",

    # Civic Services
    "electricity_supply",
    "illegal_construction",
    "encroachment",

    # Government Services
    "ration_card",
    "pension",
    "health_services",
    "education",
    "building_permit",
    "property_tax",

    # Law & Order
    "corruption",
    "police_complaint",

    # Other
    "other"
]


# Chhattisgarh-specific context
CHHATTISGARH_CONTEXT = """
REGIONAL CONTEXT - CHHATTISGARH:
- Major cities: Raipur, Bilaspur, Durg, Bhilai, Korba, Rajnandgaon
- Common languages: Hindi, Chhattisgarhi, English (code-mixed)
- Typical grievances: Water supply (monsoon dependent), electricity (industrial load),
  road conditions (rural connectivity), forest rights, tribal welfare
- Common Chhattisgarhi phrases:
  * "पानी नइ आवत" = Water is not coming
  * "बत्ती नइ जलत" = Electricity is not working
  * "सड़क टूटे हे" = Road is broken
  * "कचरा पड़े हे" = Garbage is lying
"""


# Example classifications for few-shot learning
CLASSIFICATION_EXAMPLES = """
EXAMPLES OF INTENT CLASSIFICATION:

Example 1 - GRIEVANCE (High Confidence):
Transcript: "हमारे मोहल्ले में 15 दिन से पानी नहीं आ रहा है। Raipur sector 5 में रहते हैं।
50 घर प्रभावित हैं। PHED में दो बार complaint की है।"
(Water hasn't come to our locality for 15 days. We live in Raipur sector 5.
50 houses affected. Complained to PHED twice.)

Classification:
{
  "intent": "grievance",
  "confidence": 0.95,
  "reasoning": "Clear civic issue (water supply) affecting multiple households, specific location,
               prior complaint attempts mentioned - strong grievance indicators",
  "suggested_issue_type": "water_supply"
}

Example 2 - COMMUNITY (High Confidence):
Transcript: "हम लोग इंदिरा नगर में cleanliness drive organize करना चाहते हैं।
Next Sunday को 30 volunteers आएंगे। Social media पर promote कर रहे हैं।"
(We want to organize a cleanliness drive in Indira Nagar.
30 volunteers will come next Sunday. Promoting on social media.)

Classification:
{
  "intent": "community",
  "confidence": 0.92,
  "reasoning": "Community organizing activity with volunteers, planned event, promotional efforts -
               clear community action indicators",
  "suggested_issue_type": null
}

Example 3 - PERSONAL (High Confidence):
Transcript: "मुझे याद रखना है कि कल शाम को ward councillor से electricity bill के बारे में बात करनी है।"
(I need to remember to talk to ward councillor tomorrow evening about electricity bill.)

Classification:
{
  "intent": "personal",
  "confidence": 0.88,
  "reasoning": "Personal reminder/note format, individual action item, not reporting an issue -
               personal note indicators",
  "suggested_issue_type": null
}

Example 4 - UNCERTAIN (Low Confidence):
Transcript: "यहाँ बहुत problem है।"
(There's a lot of problem here.)

Classification:
{
  "intent": "uncertain",
  "confidence": 0.35,
  "reasoning": "Too vague - no specific issue type, location, or context to determine intent.
               Could be grievance, community concern, or personal note.",
  "suggested_issue_type": null
}

Example 5 - GRIEVANCE with Chhattisgarhi (High Confidence):
Transcript: "सड़क टूटे हे भाई। Bilaspur के पास वाला road। बरसात में बहुत खराब हो जाथे।
गाड़ी भी नइ चल सकत।"
(Road is broken, brother. Road near Bilaspur. Gets very bad in monsoon.
Vehicle can't even move.)

Classification:
{
  "intent": "grievance",
  "confidence": 0.93,
  "reasoning": "Infrastructure issue (broken road) with location, seasonal impact described,
               affects transportation - grievance about road condition",
  "suggested_issue_type": "road_repair"
}
"""


def get_intent_classification_prompt(
    transcript: str,
    location_hint: Optional[str] = None,
    user_context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate prompt for intent classification.

    Args:
        transcript: The conversation transcript to classify
        location_hint: Optional location context
        user_context: Optional user history/context

    Returns:
        Formatted prompt string for Claude API
    """

    user_context_str = ""
    if user_context:
        user_context_str = f"\nUSER CONTEXT:\n{_format_user_context(user_context)}\n"

    location_str = ""
    if location_hint:
        location_str = f"\nLOCATION HINT: {location_hint}\n"

    prompt = f"""You are an expert at classifying citizen reports in India, specifically for Chhattisgarh state.
You understand code-mixed language (Hindi, English, Chhattisgarhi) and can determine the intent of conversations.

{CHHATTISGARH_CONTEXT}

YOUR TASK:
Analyze the following transcript and classify the speaker's intent into one of these categories:

1. **grievance**: A civic complaint or problem report that needs government/authority attention
   - Indicators: Infrastructure issues, service failures, public problems, complaints
   - Examples: Water supply, road damage, garbage, electricity, corruption

2. **community**: A community organizing or collective action initiative
   - Indicators: Event planning, volunteer coordination, group activities, campaigns
   - Examples: Cleanliness drives, awareness campaigns, community meetings

3. **personal**: A personal note, reminder, or individual action item
   - Indicators: Personal reminders, to-do items, individual tasks
   - Examples: "Remember to call X", "Need to check Y", personal notes

4. **uncertain**: Unable to determine intent with confidence
   - Use this when: Too vague, insufficient information, ambiguous context

{CLASSIFICATION_EXAMPLES}

ISSUE TAXONOMY (for grievances only):
Match the issue to ONE of these categories:
{', '.join(ISSUE_TAXONOMY)}
{location_str}{user_context_str}
TRANSCRIPT TO CLASSIFY:
```
{transcript}
```

CLASSIFICATION RULES:
1. Consider code-mixed language patterns (Hindi-English-Chhattisgarhi)
2. Look for key indicators: problem description vs. event planning vs. personal reminder
3. Assess specificity: specific location/issue = higher confidence
4. For grievances: Match to closest taxonomy category
5. If too vague or ambiguous: Use "uncertain" with low confidence
6. Confidence thresholds:
   - High (≥0.7): Clear indicators, specific details
   - Medium (0.5-0.7): Some indicators, moderate clarity
   - Low (<0.5): Vague, ambiguous, or insufficient information

RESPONSE FORMAT (JSON only):
{{
  "intent": "grievance|community|personal|uncertain",
  "confidence": 0.85,
  "reasoning": "Brief explanation of classification decision (2-3 sentences)",
  "suggested_issue_type": "taxonomy_category or null"
}}

IMPORTANT:
- Return ONLY valid JSON, no additional text
- Be conservative with confidence scores
- For grievances, ALWAYS provide suggested_issue_type
- Consider regional context and language patterns
- If uncertain, say so with low confidence
"""

    return prompt


def _format_user_context(context: Dict[str, Any]) -> str:
    """Format user context for prompt inclusion."""
    parts = []

    if "previous_cases" in context:
        prev = context["previous_cases"]
        parts.append(f"Previous cases: {prev}")

    if "preferred_language" in context:
        parts.append(f"Preferred language: {context['preferred_language']}")

    if "location_history" in context:
        parts.append(f"Common locations: {context['location_history']}")

    return "\n".join(parts) if parts else "No prior context available"


def get_follow_up_prompt_for_uncertain(transcript: str) -> str:
    """
    Generate prompt to ask clarifying questions for uncertain classifications.

    Args:
        transcript: The original transcript

    Returns:
        Formatted prompt for generating follow-up questions
    """
    return f"""The following transcript was too vague to classify confidently:

TRANSCRIPT:
```
{transcript}
```

Generate 2-3 clarifying questions in Hindi/English code-mix to help determine the intent.
The questions should help identify whether this is:
- A grievance/complaint about a civic issue
- A community organizing initiative
- A personal note/reminder

Questions should be:
- Conversational and friendly
- In code-mixed Hindi-English (like the examples)
- Specific to the context of what was said

Return as JSON array:
{{
  "questions": [
    "क्या आप किसी समस्या की शिकायत करना चाहते हैं? (Do you want to report a problem?)",
    "यह किसी community event के बारे में है? (Is this about a community event?)"
  ]
}}
"""
