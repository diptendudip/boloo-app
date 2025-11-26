#!/bin/bash
# Test with Problem #5 from PDF: Electricity connection issues
# More complex scenario to test empathy engine

set -e

BASE_URL="http://localhost:8000"
USER_ID="22222222-2222-2222-2222-222222222222"

echo "🧪 Testing CGNet Problem #5: Electricity Connection"
echo "===================================================="
echo ""

# Start conversation
echo "1️⃣ Starting conversation..."
START_RESPONSE=$(curl -s -X POST "${BASE_URL}/v1/chat/start?user_id=${USER_ID}&language=hi")
CONV_ID=$(echo $START_RESPONSE | jq -r '.conversation_id')
echo "✅ Conversation ID: $CONV_ID"
echo ""

# Turn 1: Problem description
echo "2️⃣ Turn 1: Describe electricity problem..."
TURN1=$(curl -s -X POST "${BASE_URL}/v1/chat/turn" \
  -F "conversation_id=${CONV_ID}" \
  -F "user_id=${USER_ID}" \
  -F "text_message=बिजली का कनेक्शन नहीं मिल रहा, कुसुमकेरा गांव में")

AI1=$(echo $TURN1 | jq -r '.ai_response_hi')
COLLECTED1=$(echo $TURN1 | jq -r '.collected_fields | join(", ")')
echo "AI: $AI1"
echo "Collected: [$COLLECTED1]"
echo ""

# Turn 2: Duration
echo "3️⃣ Turn 2: When it started..."
TURN2=$(curl -s -X POST "${BASE_URL}/v1/chat/turn" \
  -F "conversation_id=${CONV_ID}" \
  -F "user_id=${USER_ID}" \
  -F "text_message=3 महीने से आवेदन किया है")

AI2=$(echo $TURN2 | jq -r '.ai_response_hi')
COLLECTED2=$(echo $TURN2 | jq -r '.collected_fields | join(", ")')
echo "AI: $AI2"
echo "Collected: [$COLLECTED2]"
echo ""

# Check empathy
if [[ "$AI2" == *"3 महीने"* ]] || [[ "$AI2" == *"महीने"* ]]; then
    echo "✅ EMPATHY: Acknowledged duration '3 महीने से'"
else
    echo "⚠️  NO EMPATHY"
fi
echo ""

# Turn 3: Affected count
echo "4️⃣ Turn 3: How many affected..."
TURN3=$(curl -s -X POST "${BASE_URL}/v1/chat/turn" \
  -F "conversation_id=${CONV_ID}" \
  -F "user_id=${USER_ID}" \
  -F "text_message=10 घर हैं जो प्रभावित हैं")

AI3=$(echo $TURN3 | jq -r '.ai_response_hi')
COLLECTED3=$(echo $TURN3 | jq -r '.collected_fields | join(", ")')
echo "AI: $AI3"
echo "Collected: [$COLLECTED3]"
echo ""

# Turn 4: Previous action
echo "5️⃣ Turn 4: Previous action..."
TURN4=$(curl -s -X POST "${BASE_URL}/v1/chat/turn" \
  -F "conversation_id=${CONV_ID}" \
  -F "user_id=${USER_ID}" \
  -F "text_message=बिजली विभाग से शिकायत की थी लेकिन कोई जवाब नहीं")

AI4=$(echo $TURN4 | jq -r '.ai_response_hi')
COLLECTED4=$(echo $TURN4 | jq -r '.collected_fields | join(", ")')
COMPLETE4=$(echo $TURN4 | jq -r '.is_complete')
echo "AI: $AI4"
echo "Collected: [$COLLECTED4]"
echo "Complete: $COMPLETE4"
echo ""

# Check entity extraction quality
if [[ "$AI4" == *"बिजली विभाग"* ]]; then
    echo "✅ ENTITY EXTRACTION: Correctly extracted 'बिजली विभाग'"
else
    echo "⚠️  Entity extraction may need improvement"
fi

echo ""
echo "🎉 Test complete!"
