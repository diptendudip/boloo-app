"""
Journalist-style narrative summary generator using Azure OpenAI.

Converts structured grievance data into natural, professional Hindi and English
narratives, similar to how a journalist would report civic issues.
"""

import logging
import json
from typing import Dict, Any
from openai import AzureOpenAI, APIError, APIConnectionError

from app.config import settings

logger = logging.getLogger(__name__)


class JournalistSummaryError(Exception):
    """Base exception for journalist summary errors"""
    pass


def generate_journalist_summary(extracted_data: dict) -> str:
    """
    Generate a professional journalist-style narrative summary in Hindi using Azure OpenAI.

    Args:
        extracted_data: Dict with keys: issue_description, location,
                       when_started, affected_people, previous_action

    Returns:
        Natural, professional Hindi narrative paragraph

    Example:
        "गांव वार्ड नंबर 20, पंचायत नोगांई कटरापारा में पिछले 6 महीने से पानी आपूर्ति
        की समस्या है। इस समस्या से करीब 50 परिवार प्रभावित हैं। ग्रामीणों ने सरपंच
        को इस बारे में सूचित किया था, लेकिन अभी तक कोई कार्रवाई नहीं हुई है।"
    """
    # Extract all data (safely handle None values)
    location = str(extracted_data.get('location') or '').strip()
    issue = str(extracted_data.get('issue_description') or '').strip()
    when_started = str(extracted_data.get('when_started') or '').strip()
    affected_count = str(extracted_data.get('affected_people') or '').strip()
    previous_action = str(extracted_data.get('previous_action') or '').strip()

    # Fallback to template if no data
    if not issue and not location:
        logger.warning("Insufficient data for journalist summary, using fallback")
        return "आपकी शिकायत दर्ज की जा रही है। कृपया सभी जानकारी प्रदान करें।"

    # Use Azure OpenAI for professional narrative generation
    try:
        if not settings.AZURE_OPENAI_ENDPOINT or not settings.AZURE_OPENAI_API_KEY:
            logger.warning("Azure OpenAI not configured, using template fallback")
            return _generate_template_summary_hindi(extracted_data)

        client = AzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION
        )

        # Build prompt for journalist summary
        prompt = f"""आप एक पत्रकार हैं जो नागरिक शिकायतों की रिपोर्ट करते हैं।

निम्नलिखित जानकारी को एक पेशेवर, पत्रकारिता शैली की हिंदी रिपोर्ट में बदलें:

स्थान: {location if location else 'नहीं बताया गया'}
समस्या का विवरण: {issue if issue else 'नहीं बताया गया'}
कब से: {when_started if when_started else 'नहीं बताया गया'}
प्रभावित लोग: {affected_count if affected_count else 'नहीं बताया गया'}
पहले की गई कार्रवाई: {previous_action if previous_action else 'नहीं की गई'}

निर्देश:
1. एक प्राकृतिक, पेशेवर पैराग्राफ लिखें (2-4 वाक्य)
2. समाचार रिपोर्ट की तरह तथ्यात्मक और स्पष्ट रहें
3. केवल हिंदी में लिखें - कोई अंग्रेजी शब्द नहीं
4. स्थान + समय + समस्या + प्रभाव + कार्रवाई का प्रवाह बनाएं
5. यदि कोई जानकारी नहीं है तो उसे छोड़ दें, न कि "नहीं बताया गया" लिखें

केवल पैराग्राफ लौटाएं, कोई शीर्षक या अतिरिक्त जानकारी नहीं।"""

        response = client.chat.completions.create(
            model=settings.AZURE_OPENAI_DEPLOYMENT_NAME or "gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "आप एक पेशेवर हिंदी पत्रकार हैं जो नागरिक शिकायतों की रिपोर्ट करते हैं। केवल स्पष्ट, तथ्यात्मक हिंदी में लिखें।"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.5,  # Lower temperature for more factual, consistent output
            max_tokens=300
        )

        narrative = response.choices[0].message.content.strip()
        logger.info(f"✅ Generated journalist summary (Hindi): {narrative[:100]}...")

        return narrative

    except (APIConnectionError, APIError) as e:
        logger.error(f"❌ Azure OpenAI error in journalist summary: {e}")
        return _generate_template_summary_hindi(extracted_data)

    except Exception as e:
        logger.error(f"❌ Unexpected error in journalist summary: {e}", exc_info=True)
        return _generate_template_summary_hindi(extracted_data)


def generate_journalist_summary_english(extracted_data: dict) -> str:
    """
    Generate a professional journalist-style narrative summary in English using Azure OpenAI.

    Args:
        extracted_data: Dict with keys: issue_description, location,
                       when_started, affected_people, previous_action

    Returns:
        Natural, professional English narrative paragraph
    """
    # Extract all data (safely handle None values)
    location = str(extracted_data.get('location') or '').strip()
    issue = str(extracted_data.get('issue_description') or '').strip()
    when_started = str(extracted_data.get('when_started') or '').strip()
    affected_count = str(extracted_data.get('affected_people') or '').strip()
    previous_action = str(extracted_data.get('previous_action') or '').strip()

    # Fallback if no data
    if not issue and not location:
        logger.warning("Insufficient data for English journalist summary, using fallback")
        return "Your complaint is being registered. Please provide all information."

    # Use Azure OpenAI for professional narrative generation
    try:
        if not settings.AZURE_OPENAI_ENDPOINT or not settings.AZURE_OPENAI_API_KEY:
            logger.warning("Azure OpenAI not configured, using template fallback")
            return _generate_template_summary_english(extracted_data)

        client = AzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION
        )

        # Build prompt for journalist summary
        prompt = f"""You are a journalist reporting on citizen grievances.

Convert the following information into a professional, journalistic English report:

Location: {location if location else 'Not specified'}
Issue Description: {issue if issue else 'Not specified'}
Duration: {when_started if when_started else 'Not specified'}
Affected People: {affected_count if affected_count else 'Not specified'}
Previous Action: {previous_action if previous_action else 'None'}

Instructions:
1. Write a natural, professional paragraph (2-4 sentences)
2. Be factual and clear like a news report
3. Follow the flow: location + timeline + issue + impact + action
4. Skip any information that is not available, don't write "Not specified"

Return only the paragraph, no title or extra information."""

        response = client.chat.completions.create(
            model=settings.AZURE_OPENAI_DEPLOYMENT_NAME or "gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional English journalist reporting on citizen grievances. Write clear, factual English only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.5,
            max_tokens=300
        )

        narrative = response.choices[0].message.content.strip()
        logger.info(f"✅ Generated journalist summary (English): {narrative[:100]}...")

        return narrative

    except (APIConnectionError, APIError) as e:
        logger.error(f"❌ Azure OpenAI error in English journalist summary: {e}")
        return _generate_template_summary_english(extracted_data)

    except Exception as e:
        logger.error(f"❌ Unexpected error in English journalist summary: {e}", exc_info=True)
        return _generate_template_summary_english(extracted_data)


def _generate_template_summary_hindi(extracted_data: dict) -> str:
    """
    Fallback template-based summary generator in Hindi.
    Used when Azure OpenAI is unavailable.
    """
    # Safely handle None values
    location = str(extracted_data.get('location') or '').strip()
    issue = str(extracted_data.get('issue_description') or '').strip()
    when_started = str(extracted_data.get('when_started') or '').strip()
    affected_count = str(extracted_data.get('affected_people') or '').strip()
    previous_action = str(extracted_data.get('previous_action') or '').strip()

    # Build narrative paragraph
    paragraphs = []

    # Opening sentence: Location + Time + Problem
    if location and when_started and issue:
        opening = f"{location} में {when_started} से {issue}।"
        paragraphs.append(opening)
    elif location and issue:
        opening = f"{location} में {issue}।"
        paragraphs.append(opening)
    elif issue:
        paragraphs.append(f"{issue}।")

    # Impact sentence: Affected people
    if affected_count:
        # Handle different formats: "300", "300 लोग", "300 मकान"
        if any(word in affected_count for word in ['लोग', 'परिवार', 'मकान', 'घर']):
            impact = f"इससे {affected_count} प्रभावित हैं।"
        else:
            impact = f"इससे करीब {affected_count} लोग प्रभावित हैं।"
        paragraphs.append(impact)

    # Action sentence: Previous action taken
    if previous_action:
        # Clean up entity name
        entity = previous_action.strip()
        entity = entity.replace(' को बताया', '').replace(' से बताया', '')
        entity = entity.replace(' को', '').replace(' से', '')
        entity = entity.replace(' बताया था', '').replace(' बताया', '')
        entity = entity.strip()

        # Check for negative responses
        negative_responses = [
            'no', 'नहीं', 'nahi', 'नही', 'कोई नहीं', 'none',
            'किसी को नहीं', 'nobody', 'कोई भी नहीं'
        ]

        entity_lower = entity.lower()
        is_negative = any(neg in entity_lower for neg in negative_responses)

        if not is_negative and entity and len(entity) > 2:
            action = f"इस मामले में ग्रामीणों ने {entity} को सूचित किया था, लेकिन अभी तक कोई कार्रवाई नहीं हुई है।"
            paragraphs.append(action)
        elif is_negative:
            paragraphs.append("इस मामले के बारे में किसी अधिकारी को सूचित नहीं किया गया है।")

    # Join all paragraphs
    narrative = " ".join(paragraphs)

    # Fallback if no data
    if not narrative.strip():
        return "आपकी शिकायत दर्ज की जा रही है। कृपया सभी जानकारी प्रदान करें।"

    return narrative.strip()


def _generate_template_summary_english(extracted_data: dict) -> str:
    """
    Fallback template-based summary generator in English.
    Used when Azure OpenAI is unavailable.
    """
    # Safely handle None values
    location = str(extracted_data.get('location') or '').strip()
    issue = str(extracted_data.get('issue_description') or '').strip()
    when_started = str(extracted_data.get('when_started') or '').strip()
    affected_count = str(extracted_data.get('affected_people') or '').strip()
    previous_action = str(extracted_data.get('previous_action') or '').strip()

    paragraphs = []

    # Opening sentence
    if location and when_started and issue:
        opening = f"In {location}, {issue} for the past {when_started}."
        paragraphs.append(opening)
    elif location and issue:
        opening = f"In {location}, {issue}."
        paragraphs.append(opening)
    elif issue:
        paragraphs.append(f"{issue}.")

    # Impact sentence
    if affected_count:
        impact = f"This issue affects approximately {affected_count} people."
        paragraphs.append(impact)

    # Action sentence
    if previous_action:
        entity = previous_action.replace(' ko', '').replace(' se', '').strip()

        negative_responses = [
            'no', 'नहीं', 'nahi', 'नही', 'कोई नहीं', 'none',
            'किसी को नहीं', 'nobody', 'कोई भी नहीं'
        ]

        entity_lower = entity.lower()
        is_negative = any(neg in entity_lower for neg in negative_responses)

        if not is_negative and entity and len(entity) > 2:
            action = f"Villagers have informed {entity} about this matter, but no action has been taken yet."
            paragraphs.append(action)
        elif is_negative:
            paragraphs.append("No official has been contacted about this issue yet.")

    narrative = " ".join(paragraphs)

    if not narrative.strip():
        return "Your complaint is being registered. Please provide all information."

    return narrative.strip()
