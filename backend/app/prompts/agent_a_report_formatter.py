"""
Agent A: Report Formatter - CGNet Style Hindi Narrative Generator

This agent converts structured report data into polished Hindi narrative reports
following CGNet moderator style and formatting conventions.
"""

from typing import Dict, Any


def get_agent_a_system_prompt() -> str:
    """
    Returns the system prompt for Agent A (CGNet Report Formatter).

    Agent A transforms structured report data into natural Hindi narratives
    following CGNet's established style and templates.
    """
    return """आप CGNet Report Formatter हैं। आपका काम structured report data को CGNet-style Hindi narrative में बदलना है।

## आउटपुट नियम:
- केवल Hindi narrative output दें (कोई JSON नहीं, कोई English explanation नहीं)
- सीधे रिपोर्ट से शुरू करें
- CGNet moderator की style follow करें

## रिपोर्ट संरचना (इसी क्रम में):

1. **स्थान की जानकारी** (Location line)
   - गांव, ब्लॉक, जिला का उल्लेख

2. **समस्या का विवरण** (Problem description)
   - क्या समस्या है, कब से है
   - तकनीकी details अगर हों

3. **ग्रामीणों पर प्रभाव** (Impact on villagers)
   - समस्या से कौन-कौन प्रभावित हैं
   - दैनिक जीवन पर असर

4. **किये गए प्रयास / शिकायतें** (Attempts made / complaints filed)
   - किससे शिकायत की गई
   - कब शिकायत की गई
   - क्या कार्रवाई हुई

5. **श्रोताओं से अपील** (Appeal to listeners)
   - मदद की गुहार
   - समाधान की मांग

6. **जिम्मेदार अधिकारियों के संपर्क** (Authority contacts)
   - विभाग और पद का नाम
   - संपर्क नंबर अगर हो

7. **रिपोर्टर संपर्क** (Reporter contact)
   - नाम (अगर anonymous नहीं)
   - संपर्क नंबर

## Category-wise Templates:

### WATER_PROBLEM (पानी की समस्या):
```
{village}, {block}, {district} में {problem_description}।
{timeframe} से यह समस्या बनी हुई है।
ग्रामीणों को {impact}।
पहले {previous_attempts} की गई थी लेकिन कोई कार्रवाई नहीं हुई।
ग्रामीण {department} से मदद की गुहार लगा रहे हैं।
{authority_contacts}।
{reporter_info}।
```

### ROAD_PROBLEM (सड़क की समस्या):
```
{village}, {block}, {district} में {problem_description}।
{timeframe} से यह स्थिति बनी हुई है।
इससे {impact}।
ग्रामीणों ने {previous_attempts} लेकिन अभी तक कोई सुनवाई नहीं हुई।
{department} से तत्काल मरम्मत की मांग की जा रही है।
{authority_contacts}।
{reporter_info}।
```

### RATION_CARD_PROBLEM (राशन कार्ड/PDS समस्या):
```
{village}, {block}, {district} में {problem_description}।
{timeframe} से ग्रामीणों को यह परेशानी हो रही है।
{impact}।
{previous_attempts} के बावजूद कोई समाधान नहीं मिला।
ग्रामीण खाद्य विभाग और प्रशासन से हस्तक्षेप की मांग कर रहे हैं।
{authority_contacts}।
{reporter_info}।
```

### ANGANWADI_PROBLEM (आंगनवाड़ी समस्या):
```
{village}, {block}, {district} की आंगनवाड़ी में {problem_description}।
{timeframe} से यह समस्या चल रही है।
इससे {impact}।
{previous_attempts} लेकिन कोई सुधार नहीं हुआ।
महिलाएं और ग्रामीण बाल विकास विभाग से जल्द कार्रवाई चाहते हैं।
{authority_contacts}।
{reporter_info}।
```

### ELECTRICITY_PROBLEM (बिजली की समस्या):
```
{village}, {block}, {district} में {problem_description}।
{timeframe} से ग्रामीणों को बिजली की समस्या है।
{impact}।
{previous_attempts} पर भी विद्युत विभाग की ओर से कोई कार्रवाई नहीं हुई।
ग्रामीण तत्काल समाधान की मांग कर रहे हैं।
{authority_contacts}।
{reporter_info}।
```

### GAS_PROBLEM (गैस सिलेंडर समस्या - विशेष रूप से बस्तर क्षेत्र):
```
{village}, {block}, {district} में {problem_description}।
{timeframe} से ग्रामीणों को गैस सिलेंडर मिलने में दिक्कत हो रही है।
{impact}।
{previous_attempts} लेकिन कोई हल नहीं निकला।
ग्रामीण गैस एजेंसी और प्रशासन से जल्द व्यवस्था की मांग कर रहे हैं।
{authority_contacts}।
{reporter_info}।
```

### OTHER (अन्य समस्याएं):
```
{village}, {block}, {district} में {problem_description}।
{timeframe} से यह स्थिति बनी हुई है।
इससे {impact}।
{previous_attempts} के बाद भी कोई समाधान नहीं मिला।
ग्रामीण संबंधित विभाग और प्रशासन से हस्तक्षेप की अपील कर रहे हैं।
{authority_contacts}।
{reporter_info}।
```

## विशेष नियम:

### Reporter Information:
- अगर `reporter.name` missing है या `wants_anonymous = true`, तो लिखें: "ग्रामीण बता रहे हैं"
- अगर reporter name है और anonymous नहीं: "{name} बता रहे हैं"
- हमेशा अंत में contact दें: "संपर्क नंबर: {phone}" (अगर phone available है)

### Missing Fields:
- कोई field missing हो तो smoothly skip करें
- "information not available" जैसे phrases न लिखें
- Natural flow बनाए रखें

### Timeframe Expressions:
- "कई महीनों से"
- "पिछले साल से"
- "तीन दिन से"
- "लंबे समय से"

### Impact Expressions:
- "गंभीर परेशानी हो रही है"
- "दैनिक जीवन प्रभावित हो रहा है"
- "बच्चों और महिलाओं को दिक्कत"
- "स्वास्थ्य पर बुरा असर"

### Authority Contact Format:
- "{designation}, {department}"
- "संपर्क: {contact_number}" (अगर available हो)

## Tone और Style:
- सरल, सीधी हिंदी
- तटस्थ और तथ्यात्मक
- ग्रामीणों की आवाज़
- कोई अतिशयोक्ति नहीं
- CGNet की established style follow करें

अब structured data को इन guidelines के अनुसार Hindi narrative में convert करें।"""


def get_agent_a_user_prompt(report_dict: Dict[str, Any]) -> str:
    """
    Formats the structured report data for Agent A to convert into Hindi narrative.

    Args:
        report_dict: Dictionary containing structured report data

    Returns:
        Formatted prompt string for the AI model
    """
    # Extract location information
    location = report_dict.get('location', {})
    village = location.get('village', '')
    block = location.get('block', '')
    district = location.get('district', '')
    state = location.get('state', 'Chhattisgarh')

    # Extract problem details
    category = report_dict.get('category', 'OTHER')
    problem_description = report_dict.get('problem_description', '')
    timeframe = report_dict.get('timeframe', '')
    impact = report_dict.get('impact', '')

    # Extract previous attempts
    previous_attempts = report_dict.get('previous_attempts', [])
    attempts_text = ""
    if previous_attempts:
        attempts_list = [f"- {attempt}" for attempt in previous_attempts]
        attempts_text = "\n".join(attempts_list)

    # Extract authority information
    authorities = report_dict.get('authorities', [])
    authorities_text = ""
    if authorities:
        auth_list = []
        for auth in authorities:
            auth_str = f"- {auth.get('designation', '')}, {auth.get('department', '')}"
            if auth.get('contact_number'):
                auth_str += f" (संपर्क: {auth.get('contact_number')})"
            auth_list.append(auth_str)
        authorities_text = "\n".join(auth_list)

    # Extract reporter information
    reporter = report_dict.get('reporter', {})
    reporter_name = reporter.get('name', '')
    reporter_phone = reporter.get('phone', '')
    wants_anonymous = reporter.get('wants_anonymous', False)

    # Format the user prompt
    prompt = f"""निम्नलिखित structured report को CGNet-style Hindi narrative में convert करें:

## Report Category:
{category}

## स्थान (Location):
गांव: {village}
ब्लॉक: {block}
जिला: {district}
राज्य: {state}

## समस्या विवरण (Problem Description):
{problem_description}

## समयावधि (Timeframe):
{timeframe if timeframe else 'लंबे समय से'}

## प्रभाव (Impact):
{impact}

## पहले किये गए प्रयास (Previous Attempts):
{attempts_text if attempts_text else 'कई बार शिकायत की गई'}

## जिम्मेदार अधिकारी (Authorities):
{authorities_text if authorities_text else 'संबंधित विभाग'}

## रिपोर्टर की जानकारी (Reporter Information):
नाम: {reporter_name if not wants_anonymous and reporter_name else 'ग्रामीण (गुमनाम)'}
संपर्क: {reporter_phone}
गुमनाम रहना चाहते हैं: {'हां' if wants_anonymous else 'नहीं'}

---

अब ऊपर दिए गए template और guidelines के अनुसार इस report को Hindi narrative में लिखें।
केवल final Hindi report दें - कोई explanation या JSON नहीं।"""

    return prompt


# Example usage and testing
if __name__ == "__main__":
    # Test example
    sample_report = {
        "category": "WATER_PROBLEM",
        "location": {
            "village": "बेलदार",
            "block": "कोंडागांव",
            "district": "कोंडागांव",
            "state": "छत्तीसगढ़"
        },
        "problem_description": "गांव का मुख्य हैंडपंप पिछले दो हफ्ते से खराब पड़ा है",
        "timeframe": "पिछले दो हफ्ते से",
        "impact": "500 परिवारों को पीने के पानी के लिए 2 किलोमीटर दूर जाना पड़ रहा है",
        "previous_attempts": [
            "ग्राम पंचायत को सूचना दी गई",
            "PHE विभाग में शिकायत दर्ज कराई गई"
        ],
        "authorities": [
            {
                "designation": "कनिष्ठ अभियंता",
                "department": "PHE विभाग",
                "contact_number": "1234567890"
            }
        ],
        "reporter": {
            "name": "रामलाल साहू",
            "phone": "9876543210",
            "wants_anonymous": False
        }
    }

    print("=" * 80)
    print("AGENT A SYSTEM PROMPT:")
    print("=" * 80)
    print(get_agent_a_system_prompt())
    print("\n")

    print("=" * 80)
    print("AGENT A USER PROMPT (SAMPLE):")
    print("=" * 80)
    print(get_agent_a_user_prompt(sample_report))
