"""
Conversational prompts and empathy templates for human-like AI responses.

This module provides contextual acknowledgments and empathetic responses
to make the conversation feel more natural and less robotic.
"""

import random
import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def clean_extracted_value(field: str, value: Any) -> str:
    """
    Clean and normalize extracted values to prevent duplicate particles
    and improve natural language flow.

    Args:
        field: Field name (e.g., "when_started", "previous_action")
        value: Raw extracted value

    Returns:
        Cleaned value suitable for template insertion
    """
    if not value:
        return ""

    text = str(value).strip()

    if field == "when_started":
        # Remove trailing postpositions: से, है, हैं, खराब है, etc.
        text = re.sub(r'\s+(से|है|हैं|खराब\s+है|चल\s+रहा\s+है)$', '', text)

    elif field == "previous_action":
        # Extract just the entity name from phrases like "सरपंच को बोले हैं"
        # Common patterns: "X को बोले", "X से संपर्क किया", "X को शिकायत की"
        entity_match = re.search(r'^([^,]+?)\s*(को|से)', text)
        if entity_match:
            text = entity_match.group(1).strip()
        else:
            # If no pattern match, take first significant phrase before comma
            text = text.split(',')[0].strip()
            # Remove trailing verbs
            text = re.sub(r'\s+(बोले|बताया|शिकायत|संपर्क|किया|की|है|हैं)$', '', text)

    elif field == "affected_people":
        # Remove trailing text after numbers/counts
        # Keep patterns like "35 मकान", "50 लोग", but remove extra phrases
        text = re.sub(r'\s*,.*$', '', text)  # Remove everything after comma
        text = re.sub(r'\s+(को|से|की|है|हैं)\s+.*$', '', text)  # Remove clauses

    return text.strip()


# Empathy templates for acknowledging user's input before asking next question
# NOTE: Reporter personal details (name, phone, address) are auto-populated from user profile
# and should NOT be asked in conversation, so they don't have templates here.
#
# RURAL CONTEXT: Keep responses simple, empathetic, and action-oriented
EMPATHY_TEMPLATES = {
    "location": [
        "{location} में यह समस्या है। समझ गया। ",
        "ठीक है, {location} का मामला है। ",
        "{location} - यह नोट कर लिया। ",
        "समझा, {location} की बात हो रही है। "
    ],
    "issue_description": [
        "समझा, आपकी समस्या है कि {issue}। ",
        "{issue} - यह गंभीर है। ",
        "ठीक है, {issue} की शिकायत दर्ज हो रही है। ",
        "आपकी परेशानी समझ में आ गई: {issue}। "
    ],
    "affected_scope": [
        "समझ गया। यह समस्या {scope} को प्रभावित कर रही है। ",
        "ठीक है, {scope} परेशान हैं। ",
        "{scope} - यह नोट हो गया। ",
        "समझा, {scope} की बात है। "
    ],
    # Generic empathy for "don't know" responses
    "unknown": [
        "कोई बात नहीं। ",
        "ठीक है। ",
        "समझ गया। ",
        "चलिए आगे बढ़ते हैं। "
    ]
}


# Next question templates that flow naturally after acknowledgment
# NOTE: Reporter personal details (name, phone, address) are auto-populated from user profile
# and should NOT be asked in conversation, so they don't have templates here.
# RURAL CONTEXT: Simple, direct questions. Accept "don't know" and move on.
NATURAL_QUESTION_TEMPLATES = {
    "location": [
        "यह समस्या कहाँ हो रही है? गाँव या क्षेत्र का नाम बताएं।",
        "कौन सी जगह की बात हो रही है?",
        "यह किस गाँव/इलाके में है?"
    ],
    "issue_description": [
        "कृपया अपनी समस्या के बारे में बताएं।",
        "आपकी क्या परेशानी है?",
        "क्या समस्या है?"
    ],
    "affected_scope": [
        "क्या यह समस्या सिर्फ आपको है या पूरे गाँव/क्षेत्र को?",
        "कितने लोग इससे परेशान हैं?",
        "यह समस्या कितने लोगों को हो रही है?"
    ]
}


def build_contextual_response(
    last_collected_field: Optional[str],
    last_collected_value: Any,
    next_missing_field: str,
    next_field_prompt_hi: str
) -> str:
    """
    Build a contextual AI response that:
    1. Acknowledges what the user just provided (empathy)
    2. Asks for the next missing field (natural question)

    Args:
        last_collected_field: The field that was just collected (e.g., "when_started")
        last_collected_value: The value provided by user (e.g., "6 महीने से")
        next_missing_field: The next field to ask for (e.g., "affected_people")
        next_field_prompt_hi: Default prompt for the next field

    Returns:
        Contextual response in Hindi with acknowledgment + question
    """
    response = ""

    # Part 1: Acknowledge what user just said (empathy)
    if last_collected_field and last_collected_value:
        templates = EMPATHY_TEMPLATES.get(last_collected_field, [])
        if templates:
            template = random.choice(templates)

            # Clean the value before formatting
            cleaned_value = clean_extracted_value(last_collected_field, last_collected_value)

            # Only add empathy if we have a valid cleaned value
            # Skip if value is None, empty, or literal "null"/"None" string
            if cleaned_value and cleaned_value.lower() not in ["null", "none", ""]:
                # Format the acknowledgment based on field type
                if last_collected_field == "when_started":
                    response += template.format(duration=cleaned_value)
                elif last_collected_field == "affected_people":
                    response += template.format(count=cleaned_value)
                elif last_collected_field == "previous_action":
                    response += template.format(entity=cleaned_value)
                elif last_collected_field == "location":
                    response += template.format(location=cleaned_value)
                elif last_collected_field == "issue_description":
                    # Truncate long descriptions
                    issue_summary = cleaned_value[:50]
                    response += template.format(issue=issue_summary)

    # Part 2: Ask for next missing field (natural question)
    # ⚠️ CRITICAL FIX: DON'T ask for the field we just acknowledged!
    # If last_collected_field == next_missing_field, it means we just collected it
    # but the system hasn't re-evaluated yet. Skip asking the same question.
    logger.info(f"[ConvPrompts] DEBUG: last_collected='{last_collected_field}', next_missing='{next_missing_field}'")
    if last_collected_field and last_collected_field == next_missing_field:
        # We just collected this field - don't ask for it again!
        # Just return the acknowledgment without a follow-up question
        logger.info(f"[ConvPrompts] ✅ SKIPPING repetitive question for field: {last_collected_field}")
        return response.strip() if response else "बहुत अच्छा!"

    # Ask for the NEXT missing field (only if it's different from what we just collected)
    natural_questions = NATURAL_QUESTION_TEMPLATES.get(next_missing_field, [])
    if natural_questions:
        response += random.choice(natural_questions)
    else:
        # Fallback to default prompt
        response += next_field_prompt_hi

    return response.strip()


def build_acknowledgment_only(field: str, value: Any) -> str:
    """
    Build standalone acknowledgment without asking next question.
    Useful for intermediate responses.

    Args:
        field: Field name (e.g., "when_started")
        value: Field value

    Returns:
        Acknowledgment text in Hindi
    """
    templates = EMPATHY_TEMPLATES.get(field, [])
    if not templates:
        return "समझा।"

    template = random.choice(templates)

    # Clean the value before formatting
    cleaned_value = clean_extracted_value(field, value)

    # Only build acknowledgment if we have a valid cleaned value
    # Skip if value is None, empty, or literal "null"/"None" string
    if not cleaned_value or cleaned_value.lower() in ["null", "none", ""]:
        return "समझा।"

    if field == "when_started":
        return template.format(duration=cleaned_value).strip()
    elif field == "affected_people":
        return template.format(count=cleaned_value).strip()
    elif field == "previous_action":
        return template.format(entity=cleaned_value).strip()
    elif field == "location":
        return template.format(location=cleaned_value).strip()
    elif field == "issue_description":
        issue_summary = cleaned_value[:50]
        return template.format(issue=issue_summary).strip()

    return "समझा।"


def get_natural_question(field: str, default_prompt: str = "") -> str:
    """
    Get a natural-sounding question for a specific field.

    Args:
        field: Field name
        default_prompt: Fallback prompt if no natural template exists

    Returns:
        Natural question in Hindi
    """
    templates = NATURAL_QUESTION_TEMPLATES.get(field, [])
    if templates:
        return random.choice(templates)
    return default_prompt if default_prompt else "कृपया और जानकारी दें।"
