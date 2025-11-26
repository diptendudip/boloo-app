#!/bin/bash
# Test with Problem #4 from PDF: Old age pension not received
# Tests empathy engine with social welfare issue (71 years old person)

set -e

BASE_URL="http://localhost:8000"
USER_ID="11111111-1111-1111-1111-111111111111"

echo "🧪 Testing CGNet Problem #4: Old Age Pension Issue"
echo "=================================================="
echo ""

# Start conversation
echo "1️⃣ Starting conversation..."
START_RESPONSE=$(curl -s -X POST "${BASE_URL}/v1/chat/start?user_id=${USER_ID}&language=hi")
CONV_ID=$(echo $START_RESPONSE | jq -r '.conversation_id')
echo "✅ Conversation ID: $CONV_ID"
echo ""

# Turn 1: Problem description with location
echo "2️⃣ Turn 1: Describe pension problem..."
TURN1=$(curl -s -X POST "${BASE_URL}/v1/chat/turn" \
  -F "conversation_id=${CONV_ID}" \
  -F "user_id=${USER_ID}" \
  -F "text_message=वृद्धावस्था पेंशन नहीं मिल रहा है, नवाधकी गांव प्रतापपुर")

AI1=$(echo $TURN1 | jq -r '.ai_response_hi')
COLLECTED1=$(echo $TURN1 | jq -r '.collected_fields | join(", ")')
SCORE1=$(echo $TURN1 | jq -r '.completeness_score')
echo "AI: $AI1"
echo "Collected: [$COLLECTED1]"
echo "Score: $SCORE1"
echo ""

# Turn 2: When started
echo "3️⃣ Turn 2: When problem started..."
TURN2=$(curl -s -X POST "${BASE_URL}/v1/chat/turn" \
  -F "conversation_id=${CONV_ID}" \
  -F "user_id=${USER_ID}" \
  -F "text_message=6 महीने से आवेदन किया था")

AI2=$(echo $TURN2 | jq -r '.ai_response_hi')
COLLECTED2=$(echo $TURN2 | jq -r '.collected_fields | join(", ")')
SCORE2=$(echo $TURN2 | jq -r '.completeness_score')
echo "AI: $AI2"
echo "Collected: [$COLLECTED2]"
echo "Score: $SCORE2"
echo ""

# Check empathy
if [[ "$AI2" == *"6 महीने"* ]] || [[ "$AI2" == *"महीने"* ]]; then
    echo "✅ EMPATHY: Acknowledged '6 महीने से'"
else
    echo "⚠️  NO EMPATHY"
fi
echo ""

# Turn 3: Personal details (age)
echo "4️⃣ Turn 3: Age and affected people..."
TURN3=$(curl -s -X POST "${BASE_URL}/v1/chat/turn" \
  -F "conversation_id=${CONV_ID}" \
  -F "user_id=${USER_ID}" \
  -F "text_message=मेरी उम्र 71 साल है")

AI3=$(echo $TURN3 | jq -r '.ai_response_hi')
COLLECTED3=$(echo $TURN3 | jq -r '.collected_fields | join(", ")')
SCORE3=$(echo $TURN3 | jq -r '.completeness_score')
echo "AI: $AI3"
echo "Collected: [$COLLECTED3]"
echo "Score: $SCORE3"
echo ""

# Check empathy for age
if [[ "$AI3" == *"71"* ]] || [[ "$AI3" == *"साल"* ]]; then
    echo "✅ EMPATHY: Acknowledged age '71 साल'"
else
    echo "⚠️  NO EMPATHY"
fi
echo ""

# Turn 4: Previous action
echo "5️⃣ Turn 4: Previous action taken..."
TURN4=$(curl -s -X POST "${BASE_URL}/v1/chat/turn" \
  -F "conversation_id=${CONV_ID}" \
  -F "user_id=${USER_ID}" \
  -F "text_message=सचिव को बताया था लेकिन कोई जवाब नहीं")

AI4=$(echo $TURN4 | jq -r '.ai_response_hi')
COLLECTED4=$(echo $TURN4 | jq -r '.collected_fields | join(", ")')
COMPLETE4=$(echo $TURN4 | jq -r '.is_complete')
echo "AI: $AI4"
echo "Collected: [$COLLECTED4]"
echo "Complete: $COMPLETE4"
echo ""

# Check entity extraction
if [[ "$AI4" == *"सचिव"* ]]; then
    echo "✅ ENTITY EXTRACTION: Correctly extracted 'सचिव'"
else
    echo "⚠️  Entity extraction may need check"
fi

echo ""
echo "🎉 Test complete! Testing with social welfare problem."
echo "======================================================="
