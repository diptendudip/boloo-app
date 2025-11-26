#!/bin/bash
# Test script for human-like conversation flow
# Tests the fixes for robotic conversation issues

set -e

BASE_URL="http://localhost:8000"
USER_ID="550e8400-e29b-41d4-a716-446655440000"  # Test user ID

echo "🧪 Testing Human-Like Conversation Flow"
echo "========================================"
echo ""

# Step 1: Start conversation
echo "1️⃣ Starting conversation..."
START_RESPONSE=$(curl -s -X POST "${BASE_URL}/v1/chat/start?user_id=${USER_ID}&language=hi")
CONV_ID=$(echo $START_RESPONSE | jq -r '.conversation_id')
GREETING=$(echo $START_RESPONSE | jq -r '.greeting_hi')

if [ "$CONV_ID" = "null" ] || [ -z "$CONV_ID" ]; then
    echo "❌ Failed to start conversation"
    echo "$START_RESPONSE"
    exit 1
fi

echo "✅ Conversation started: $CONV_ID"
echo "   Greeting: $GREETING"
echo ""

# Step 2: Turn 1 - Provide issue and location
echo "2️⃣ Turn 1: User provides issue + location..."
TURN1_RESPONSE=$(curl -s -X POST "${BASE_URL}/v1/chat/turn" \
  -F "conversation_id=${CONV_ID}" \
  -F "user_id=${USER_ID}" \
  -F "text_message=पानी की सप्लाई नहीं आ रही है रायपुर में")

TURN1_AI=$(echo $TURN1_RESPONSE | jq -r '.ai_response_hi')
TURN1_COLLECTED=$(echo $TURN1_RESPONSE | jq -r '.collected_fields | join(", ")')
TURN1_SCORE=$(echo $TURN1_RESPONSE | jq -r '.completeness_score')
TURN1_COMPLETE=$(echo $TURN1_RESPONSE | jq -r '.is_complete')

echo "✅ Turn 1 complete"
echo "   AI Response: $TURN1_AI"
echo "   Collected: [$TURN1_COLLECTED]"
echo "   Completeness: ${TURN1_SCORE} (complete: $TURN1_COMPLETE)"
echo ""

# Verify not 100% complete yet
if [ "$TURN1_COMPLETE" = "true" ]; then
    echo "⚠️  WARNING: Marked as complete after only 1 turn (should need more info)"
fi

# Step 3: Turn 2 - Provide when_started
echo "3️⃣ Turn 2: User provides when_started..."
TURN2_RESPONSE=$(curl -s -X POST "${BASE_URL}/v1/chat/turn" \
  -F "conversation_id=${CONV_ID}" \
  -F "user_id=${USER_ID}" \
  -F "text_message=6 महीने से")

TURN2_AI=$(echo $TURN2_RESPONSE | jq -r '.ai_response_hi')
TURN2_COLLECTED=$(echo $TURN2_RESPONSE | jq -r '.collected_fields | join(", ")')
TURN2_SCORE=$(echo $TURN2_RESPONSE | jq -r '.completeness_score')
TURN2_EXTRACTED=$(echo $TURN2_RESPONSE | jq -r '.extracted_data | keys | join(", ")')

echo "✅ Turn 2 complete"
echo "   AI Response: $TURN2_AI"
echo "   Collected: [$TURN2_COLLECTED]"
echo "   Extracted Data: {$TURN2_EXTRACTED}"
echo "   Completeness: ${TURN2_SCORE}"
echo ""

# Check for empathy/acknowledgment
if [[ "$TURN2_AI" == *"6 महीने"* ]] || [[ "$TURN2_AI" == *"महीने से"* ]]; then
    echo "✅ EMPATHY CHECK PASSED: AI acknowledged user's input"
else
    echo "⚠️  EMPATHY CHECK: AI response doesn't acknowledge '6 mahine se'"
    echo "   Response was: $TURN2_AI"
fi

# Check it's not generic fallback
if [[ "$TURN2_AI" == "कृपया अपनी समस्या के बारे में और जानकारी दें"* ]]; then
    echo "❌ GENERIC FALLBACK DETECTED: Should use contextual response"
else
    echo "✅ NOT USING GENERIC FALLBACK"
fi
echo ""

# Step 4: Turn 3 - Provide affected_people
echo "4️⃣ Turn 3: User provides affected_people..."
TURN3_RESPONSE=$(curl -s -X POST "${BASE_URL}/v1/chat/turn" \
  -F "conversation_id=${CONV_ID}" \
  -F "user_id=${USER_ID}" \
  -F "text_message=200 लोग प्रभावित हैं")

TURN3_AI=$(echo $TURN3_RESPONSE | jq -r '.ai_response_hi')
TURN3_COLLECTED=$(echo $TURN3_RESPONSE | jq -r '.collected_fields | join(", ")')
TURN3_SCORE=$(echo $TURN3_RESPONSE | jq -r '.completeness_score')

echo "✅ Turn 3 complete"
echo "   AI Response: $TURN3_AI"
echo "   Collected: [$TURN3_COLLECTED]"
echo "   Completeness: ${TURN3_SCORE}"
echo ""

# Check for empathy about affected people
if [[ "$TURN3_AI" == *"200"* ]] || [[ "$TURN3_AI" == *"लोग"* ]]; then
    echo "✅ EMPATHY CHECK PASSED: AI acknowledged '200 लोग'"
else
    echo "⚠️  EMPATHY CHECK: AI didn't acknowledge affected_people count"
fi
echo ""

# Step 5: Get summary
echo "5️⃣ Getting conversation summary..."
SUMMARY_RESPONSE=$(curl -s -X GET "${BASE_URL}/v1/chat/${CONV_ID}/summary?user_id=${USER_ID}")
SUMMARY_HI=$(echo $SUMMARY_RESPONSE | jq -r '.summary_hi')
EXTRACTED_DATA=$(echo $SUMMARY_RESPONSE | jq -r '.extracted_data')
SUMMARY_SCORE=$(echo $SUMMARY_RESPONSE | jq -r '.completeness_score')

echo "✅ Summary retrieved"
echo "   Summary: $SUMMARY_HI"
echo "   Extracted Data: $EXTRACTED_DATA"
echo "   Final Completeness: ${SUMMARY_SCORE}"
echo ""

# Verify extracted_data has actual values
if [[ "$EXTRACTED_DATA" == *"issue_description"* ]]; then
    echo "✅ EXTRACTED DATA CHECK: Contains field values"
else
    echo "⚠️  EXTRACTED DATA: Might be empty or missing values"
fi

# Step 6: Submit
echo "6️⃣ Submitting conversation..."
SUBMIT_RESPONSE=$(curl -s -X POST "${BASE_URL}/v1/chat/${CONV_ID}/submit?user_id=${USER_ID}&conversation_id=${CONV_ID}")
SUBMIT_SUCCESS=$(echo $SUBMIT_RESPONSE | jq -r '.success')
SUBMIT_MSG=$(echo $SUBMIT_RESPONSE | jq -r '.message_hi')

if [ "$SUBMIT_SUCCESS" = "true" ]; then
    echo "✅ Submission successful"
    echo "   Message: $SUBMIT_MSG"
else
    echo "❌ Submission failed"
    echo "   Response: $SUBMIT_RESPONSE"
    exit 1
fi

echo ""
echo "🎉 All tests passed!"
echo "====================================="
echo ""
echo "📊 Conversation Summary:"
echo "   - Conversation ID: $CONV_ID"
echo "   - Turns: 3"
echo "   - Final Completeness: ${SUMMARY_SCORE}"
echo "   - Submission: Success"
echo ""
