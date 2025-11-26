#!/bin/bash

# Test script for stateful conversation flow
# This tests that the AI merges data across turns and doesn't repeat questions

USER_ID="65b0e2b7-3f50-4f92-8d7f-864ff2ca8c8d"
BASE_URL="http://localhost:8000"

echo "========================================="
echo "Testing Stateful Conversation Flow"
echo "========================================="
echo ""

# Step 1: Start conversation
echo "Step 1: Starting conversation..."
START_RESPONSE=$(curl -s -X POST "${BASE_URL}/v1/chat/start?user_id=${USER_ID}&language=hi")
CONV_ID=$(echo "$START_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['conversation_id'])")

echo "Conversation ID: $CONV_ID"
echo "Greeting: $(echo "$START_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['greeting_hi'][:100])")"
echo ""

# Step 2: Turn 1 - Send partial info (location + issue)
echo "Step 2: Turn 1 - Sending location and issue..."
echo "User says: 'पानी नहीं आ रहा रायपुर में'"

TURN1_FILE="/tmp/turn1_data.txt"
cat > "$TURN1_FILE" << EOF
--boundary123
Content-Disposition: form-data; name="conversation_id"

${CONV_ID}
--boundary123
Content-Disposition: form-data; name="user_id"

${USER_ID}
--boundary123
Content-Disposition: form-data; name="text_message"

पानी नहीं आ रहा रायपुर में
--boundary123
Content-Disposition: form-data; name="language"

hi-IN
--boundary123--
EOF

TURN1_RESPONSE=$(curl -s -X POST "${BASE_URL}/v1/chat/turn" \
  -H "Content-Type: multipart/form-data; boundary=boundary123" \
  --data-binary "@${TURN1_FILE}")

echo "AI Response: $(echo "$TURN1_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['ai_response_hi'][:200])")"
echo "Completeness: $(echo "$TURN1_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['completeness_score'])")"
echo "Collected fields: $(echo "$TURN1_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['collected_fields'])")"
echo ""

# Wait a bit for processing
sleep 2

# Step 3: Turn 2 - Send when_started info
echo "Step 3: Turn 2 - Sending when_started..."
echo "User says: '3 दिन से यह समस्या है'"

TURN2_FILE="/tmp/turn2_data.txt"
cat > "$TURN2_FILE" << EOF
--boundary123
Content-Disposition: form-data; name="conversation_id"

${CONV_ID}
--boundary123
Content-Disposition: form-data; name="user_id"

${USER_ID}
--boundary123
Content-Disposition: form-data; name="text_message"

3 दिन से यह समस्या है
--boundary123
Content-Disposition: form-data; name="language"

hi-IN
--boundary123--
EOF

TURN2_RESPONSE=$(curl -s -X POST "${BASE_URL}/v1/chat/turn" \
  -H "Content-Type: multipart/form-data; boundary=boundary123" \
  --data-binary "@${TURN2_FILE}")

echo "AI Response: $(echo "$TURN2_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['ai_response_hi'][:200])")"
echo "Completeness: $(echo "$TURN2_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['completeness_score'])")"
echo "Collected fields: $(echo "$TURN2_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['collected_fields'])")"
echo "Missing fields: $(echo "$TURN2_RESPONSE" | python3 -c "import sys, json; print([f['field'] for f in json.load(sys.stdin)['missing_fields']])")"
echo ""

# Step 4: Check backend logs for stateful merging
echo "Step 4: Checking backend logs for stateful behavior..."
echo "Looking for 'Accumulated data' and 'Merged collected fields' in logs..."
tail -30 /tmp/boloo-backend.log | grep -E "Accumulated data|Merged collected fields|Updated extracted_data" | head -10

echo ""
echo "========================================="
echo "Test Complete!"
echo "========================================="
echo ""
echo "EXPECTED BEHAVIOR:"
echo "- Turn 1 should collect: location, issue_description"
echo "- Turn 1 should ask about: when_started"
echo "- Turn 2 should collect: ALL THREE (location + issue_description + when_started)"
echo "- Turn 2 should NOT ask about location or issue again"
echo "- Turn 2 should ask about: affected_people or previous_action"
echo ""

# Cleanup
rm -f "$TURN1_FILE" "$TURN2_FILE"
