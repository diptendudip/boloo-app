"""
Hindi/Hinglish Response Detection Utility

Detects common Hindi and Hinglish responses to enable better conversation flow.
Fixes Bug #4: System ignoring "Haa", "Kar dijiye" responses.
"""

from typing import Dict, Optional
import re


class HindiResponseDetector:
    """Detects and categorizes Hindi/Hinglish responses"""

    # Affirmative responses
    # Note: Using lookahead/lookbehind for better Hindi Unicode matching
    AFFIRMATIVE_PATTERNS = [
        r'(?:^|\s)(haa+|han|हाँ|हां|हा|yes|yess|yeah|ok|okay|theek|ठीक|sahi|सही)(?:\s|$|[।,.!?])',
        r'(?:^|\s)(bilkul|बिल्कुल|zaroor|ज़रूर|jarur|जरूर)(?:\s|$|[।,.!?])',
        r'\b(kar\s+dijiye|कर\s+दीजिए|kar\s+do|कर\s+दो)\b',
        r'(?:^|\s)(achha|अच्छा|thik\s+hai|ठीक\s+है)(?:\s|$|[।,.!?])'
    ]

    # Negative responses
    NEGATIVE_PATTERNS = [
        r'(?:^|\s)(nahi+|nahin|नहीं|no|nope|na|ना)(?:\s|$|[।,.!?])',
        r'\b(nahi\s+pata|नहीं\s+पता|maloom\s+nahi|मालूम\s+नहीं)\b',
        r'\b(dont\s+know|don\'t\s+know|pata\s+nahi|पता\s+नहीं)\b',
        r'\b(nahi\s+hai|नहीं\s+है|mat\s+pucho|मत\s+पूछो)\b'
    ]

    # Proceed/Submit responses
    PROCEED_PATTERNS = [
        r'\b(kar\s+dijiye|कर\s+दीजिए|kar\s+do|कर\s+दो)\b',
        r'\b(submit\s+kar\s+do|सबमिट\s+कर\s+दो)\b',
        r'\b(jama\s+kar\s+do|जमा\s+कर\s+दो|report\s+jama|रिपोर्ट\s+जमा)\b',
        r'\b(theek\s+hai|ठीक\s+है|bas|बस|hogaya|हो\s+गया)\b',
        r'\b(aur\s+nahi|और\s+नहीं|bas\s+itna|बस\s+इतना)\b'
    ]

    # Frustration responses (user is annoyed)
    FRUSTRATION_PATTERNS = [
        r'\b(mazak|मज़ाक|mazaak|मजाक)\b.*\b(kar|कर)\b',  # "mazak kar rahe hain"
        r'\b(phir\s+se|फिर\s+से).*\b(same|वही|question|सवाल)\b',  # "phir se same question"
        r'\b(kitni\s+baar|कितनी\s+बार)\b',  # "kitni baar puchhenge"
        r'\b(bore|बोर|थक|thak|परेशान|pareshan)\b',
        r'\b(samajh|समझ).*\b(nahi|नहीं).*\b(aa\s+raha|आ\s+रहा)\b'  # "samajh nahi aa raha"
    ]

    # Skip/Continue responses
    SKIP_PATTERNS = [
        r'\b(skip\s+kar\s+do|स्किप\s+करो|chhodo|छोड़ो)\b',
        r'\b(aage\s+badho|आगे\s+बढ़ो|next|अगला)\b',
        r'\b(pata\s+nahi|पता\s+नहीं).*\b(aage|आगे)\b'
    ]

    # Question patterns (user asking questions instead of answering)
    QUESTION_PATTERNS = [
        r'[?।]\s*$',  # Ends with question mark or Hindi sentence end
        r'\b(kya|क्या|kaun|कौन|kab|कब|kahan|कहाँ|kaise|कैसे|kyun|क्यों)\b',  # Question words (? optional)
        # "should" questions - includes typo variants: चाइए, चाहीए, चाहिये, chahiye, chaiye
        r'\b(chahiye|चाहिए|चाइए|चाहीए|चाहिये|chaiye|hona\s+chahiye|होना\s+चाहिए|honi\s+chahiye|होनी\s+चाहिए)\s*[?।]?\s*$',
        # Opinion request patterns - "what do you think", "you tell me"
        r'\b(आप(को)?\s*क्या\s*लगता\s*(है)?|आप\s*बताइए|what\s*do\s*you\s*think|aap\s*kya\s*lagta|aapko\s*kya\s*lagta)\b',
        r'\b(lagta\s+hai|लगता\s+है)',  # "do you think" (? optional)
    ]

    def __init__(self):
        """Initialize the detector with compiled regex patterns"""
        self.affirmative_regex = [re.compile(p, re.IGNORECASE | re.UNICODE) for p in self.AFFIRMATIVE_PATTERNS]
        self.negative_regex = [re.compile(p, re.IGNORECASE | re.UNICODE) for p in self.NEGATIVE_PATTERNS]
        self.proceed_regex = [re.compile(p, re.IGNORECASE | re.UNICODE) for p in self.PROCEED_PATTERNS]
        self.frustration_regex = [re.compile(p, re.IGNORECASE | re.UNICODE) for p in self.FRUSTRATION_PATTERNS]
        self.skip_regex = [re.compile(p, re.IGNORECASE | re.UNICODE) for p in self.SKIP_PATTERNS]
        self.question_regex = [re.compile(p, re.IGNORECASE | re.UNICODE) for p in self.QUESTION_PATTERNS]

    def detect(self, text: str) -> Dict[str, any]:
        """
        Detect the type and sentiment of a Hindi/Hinglish response.

        Args:
            text: User's message text

        Returns:
            Dict with detection results:
            {
                "type": "affirmative" | "negative" | "proceed" | "frustration" | "skip" | "question" | "neutral",
                "confidence": 0.0-1.0,
                "matched_pattern": str,
                "should_stop_asking": bool  # True if system should stop asking questions
            }
        """
        if not text or not text.strip():
            return self._neutral_response()

        text = text.strip()

        # Check for QUESTION FIRST (user asking instead of answering)
        # BUG FIX #8: Detect when user responds with a question
        for pattern in self.question_regex:
            if pattern.search(text):
                return {
                    "type": "question",
                    "confidence": 0.9,
                    "matched_pattern": pattern.pattern,
                    "should_stop_asking": False,  # Don't stop, but recognize it's a question
                    "message": "User asked a question instead of answering"
                }

        # Check frustration SECOND (high priority)
        for pattern in self.frustration_regex:
            if pattern.search(text):
                return {
                    "type": "frustration",
                    "confidence": 0.95,
                    "matched_pattern": pattern.pattern,
                    "should_stop_asking": True,  # Stop immediately!
                    "message": "User is frustrated - stop asking questions"
                }

        # Check proceed/submit intent
        for pattern in self.proceed_regex:
            if pattern.search(text):
                return {
                    "type": "proceed",
                    "confidence": 0.9,
                    "matched_pattern": pattern.pattern,
                    "should_stop_asking": True,  # User wants to proceed
                    "message": "User wants to proceed/submit"
                }

        # Check skip intent
        for pattern in self.skip_regex:
            if pattern.search(text):
                return {
                    "type": "skip",
                    "confidence": 0.85,
                    "matched_pattern": pattern.pattern,
                    "should_stop_asking": False,
                    "message": "User wants to skip this question"
                }

        # Check affirmative
        for pattern in self.affirmative_regex:
            if pattern.search(text):
                return {
                    "type": "affirmative",
                    "confidence": 0.8,
                    "matched_pattern": pattern.pattern,
                    "should_stop_asking": False,
                    "message": "User agreed/confirmed"
                }

        # Check negative
        for pattern in self.negative_regex:
            if pattern.search(text):
                # If response is ONLY "nahi pata" / "don't know", should move on
                only_dont_know = len(text.split()) <= 3 and any(p in text.lower() for p in ["pata nahi", "nahi pata", "maloom nahi", "don't know"])
                return {
                    "type": "negative",
                    "confidence": 0.8,
                    "matched_pattern": pattern.pattern,
                    "should_stop_asking": only_dont_know,  # If just "don't know", move on
                    "message": "User said no/don't know"
                }

        return self._neutral_response()

    def _neutral_response(self) -> Dict[str, any]:
        """Return neutral response when no pattern matches"""
        return {
            "type": "neutral",
            "confidence": 0.0,
            "matched_pattern": None,
            "should_stop_asking": False,
            "message": "No special response detected"
        }

    def is_short_response(self, text: str, max_words: int = 3) -> bool:
        """Check if response is very short (likely just Haa/Nahi/etc)"""
        if not text:
            return True
        return len(text.split()) <= max_words


# Singleton instance
_detector = None

def get_hindi_response_detector() -> HindiResponseDetector:
    """Get or create singleton detector instance"""
    global _detector
    if _detector is None:
        _detector = HindiResponseDetector()
    return _detector
