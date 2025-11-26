#!/bin/bash
# Test with real CGNet problem: Hand pump broken for 1 year
# Problem #2 from the PDF

set -e

BASE_URL="http://localhost:8000"
USER_ID="11111111-1111-1111-1111-111111111111"

echo "🧪 Testing Real CGNet Problem: Broken Hand Pump"
echo "=============================================="
echo ""

# Start conversation
echo "1️⃣ Starting conversation..."
START_RESPONSE=$(curl -s -X POST "${BASE_URL}/v1/chat/start?user_id=${USER_ID}&language=hi")
CONV_ID=$(echo $START_RESPONSE | jq -r '.conversation_id')
GREETING=$(echo $START_RESPONSE | jq -r '.greeting_hi')

echo "✅ Conversation ID: $CONV_ID"
echo "   Greeting: $GREETING"
echo ""

# Turn 1: Describe the problem with location
echo "2️⃣ Turn 1: User describes problem..."
TURN1=$(curl -s -X POST "${BASE_URL}/v1/chat/turn" \
  -F "conversation_id=${CONV_ID}" \
  -F "user_id=${USER_ID}" \
  -F "text_message=हमारे वाड़ में एक हैंडपंप लगा है, पानी नहीं निकलता, नोगोई कटरापारा ओडगी")

AI1=$(echo $TURN1 | jq -r '.ai_response_hi')
COLLECTED1=$(echo $TURN1 | jq -r '.collected_fields | join(", ")')
SCORE1=$(echo $TURN1 | jq -r '.completeness_score')

echo "AI Response: $AI1"
echo "Collected: [$COLLECTED1]"
echo "Score: $SCORE1"
echo ""

# Turn 2: When started
echo "3️⃣ Turn 2: User says when it started..."
TURN2=$(curl -s -X POST "${BASE_URL}/v1/chat/turn" \
  -F "conversation_id=${CONV_ID}" \
  -F "user_id=${USER_ID}" \
  -F "text_message=1 साल से खराब है")

AI2=$(echo $TURN2 | jq -r '.ai_response_hi')
COLLECTED2=$(echo $TURN2 | jq -r '.collected_fields | join(", ")')
SCORE2=$(echo $TURN2 | jq -r '.completeness_score')

echo "AI Response: $AI2"
echo "Collected: [$COLLECTED2]"
echo "Score: $SCORE2"
echo ""

# Check for empathy
if [[ "$AI2" == *"साल"* ]] || [[ "$AI2" == *"1 साल"* ]]; then
    echo "✅ EMPATHY CHECK: AI acknowledged '1 साल से'"
else
    echo "⚠️  NO EMPATHY: AI didn't acknowledge user input"
fi
echo ""

# Turn 3: Affected people
echo "4️⃣ Turn 3: How many affected..."
TURN3=$(curl -s -X POST "${BASE_URL}/v1/chat/turn" \
  -F "conversation_id=${CONV_ID}" \
  -F "user_id=${USER_ID}" \
  -F "text_message=35 मकान हैं, सभी को परेशानी है")

AI3=$(echo $TURN3 | jq -r '.ai_response_hi')
COLLECTED3=$(echo $TURN3 | jq -r '.collected_fields | join(", ")')
SCORE3=$(echo $TURN3 | jq -r '.completeness_score')

echo "AI Response: $AI3"
echo "Collected: [$COLLECTED3]"
echo "Score: $SCORE3"
echo ""

# Check for empathy
if [[ "$AI3" == *"35"* ]] || [[ "$AI3" == *"मकान"* ]]; then
    echo "✅ EMPATHY CHECK: AI acknowledged '35 मकान'"
else
    echo "⚠️  NO EMPATHY: AI didn't acknowledge user input"
fi
echo ""

# Turn 4: Previous action
echo "5️⃣ Turn 4: Previous action taken..."
TURN4=$(curl -s -X POST "${BASE_URL}/v1/chat/turn" \
  -F "conversation_id=${CONV_ID}" \
  -F "user_id=${USER_ID}" \
  -F "text_message=सरपंच को बोले हैं, लेकिन ध्यान नहीं देते")

AI4=$(echo $TURN4 | jq -r '.ai_response_hi')
COLLECTED4=$(echo $TURN4 | jq -r '.collected_fields | join(", ")')
SCORE4=$(echo $TURN4 | jq -r '.completeness_score')
COMPLETE4=$(echo $TURN4 | jq -r '.is_complete')

echo "AI Response: $AI4"
echo "Collected: [$COLLECTED4]"
echo "Score: $SCORE4"
echo "Complete: $COMPLETE4"
echo ""

echo "🎉 Test complete!"
echo "================="
