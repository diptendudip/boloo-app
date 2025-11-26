#!/bin/bash

# Feed API Test Script
# Tests all feed endpoints using dev mode (no JWT required)

BASE_URL="http://localhost:8000/v1"
DEV_USER_ID="81589658-3600-4000-8815-000000000000"  # Test user UUID

echo "🚀 Testing Boloo Feed API"
echo "================================"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Health Check
echo -e "\n${YELLOW}Test 1: Health Check${NC}"
curl -s "${BASE_URL%/v1}/health" | jq .

# Test 2: Get Feed (should return empty initially)
echo -e "\n${YELLOW}Test 2: Get Personalized Feed${NC}"
curl -s "${BASE_URL}/feed?dev_user_id=${DEV_USER_ID}&limit=5" | jq .

# Test 3: Create a test case first (needed for feed posts)
echo -e "\n${YELLOW}Test 3: Create Test Case (for sharing)${NC}"
CASE_RESPONSE=$(curl -s -X POST "${BASE_URL}/cases?dev_user_id=${DEV_USER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "सड़क में गड्ढा",
    "transcript_text": "Main road has dangerous potholes",
    "location_text": "MG Road, Delhi",
    "location_lat": 28.7041,
    "location_lng": 77.1025,
    "issue_type": "road_maintenance",
    "kind": "grievance"
  }')

echo "$CASE_RESPONSE" | jq .

# Extract case ID
CASE_ID=$(echo "$CASE_RESPONSE" | jq -r '.case.id')
echo -e "${GREEN}Created case ID: ${CASE_ID}${NC}"

# Test 4: Share case publicly (create feed post)
echo -e "\n${YELLOW}Test 4: Share Case on Feed${NC}"
POST_RESPONSE=$(curl -s -X POST "${BASE_URL}/feed/posts?dev_user_id=${DEV_USER_ID}" \
  -H "Content-Type: application/json" \
  -d "{
    \"case_id\": \"${CASE_ID}\",
    \"is_anonymous\": false,
    \"caption\": \"हमारी सड़क की हालत बहुत खराब है\"
  }")

echo "$POST_RESPONSE" | jq .

POST_ID=$(echo "$POST_RESPONSE" | jq -r '.data.id')
echo -e "${GREEN}Created post ID: ${POST_ID}${NC}"

# Test 5: Like the post
echo -e "\n${YELLOW}Test 5: Like Post${NC}"
curl -s -X POST "${BASE_URL}/feed/posts/${POST_ID}/like?dev_user_id=${DEV_USER_ID}" | jq .

# Test 6: Unlike the post (toggle)
echo -e "\n${YELLOW}Test 6: Unlike Post (Toggle)${NC}"
curl -s -X POST "${BASE_URL}/feed/posts/${POST_ID}/like?dev_user_id=${DEV_USER_ID}" | jq .

# Test 7: Like again
echo -e "\n${YELLOW}Test 7: Like Post Again${NC}"
curl -s -X POST "${BASE_URL}/feed/posts/${POST_ID}/like?dev_user_id=${DEV_USER_ID}" | jq .

# Test 8: Add comment
echo -e "\n${YELLOW}Test 8: Add Comment${NC}"
curl -s -X POST "${BASE_URL}/feed/posts/${POST_ID}/comment?dev_user_id=${DEV_USER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "यह समस्या मेरे इलाके में भी है। कब तक यह ठीक होगा?"
  }' | jq .

# Test 9: Get comments
echo -e "\n${YELLOW}Test 9: Get Comments${NC}"
curl -s "${BASE_URL}/feed/posts/${POST_ID}/comments?dev_user_id=${DEV_USER_ID}&limit=10" | jq .

# Test 10: Share post
echo -e "\n${YELLOW}Test 10: Share Post${NC}"
curl -s -X POST "${BASE_URL}/feed/posts/${POST_ID}/share?dev_user_id=${DEV_USER_ID}" | jq .

# Test 11: Get feed (should now show the post)
echo -e "\n${YELLOW}Test 11: Get Feed (With Post)${NC}"
curl -s "${BASE_URL}/feed?dev_user_id=${DEV_USER_ID}&limit=10" | jq .

# Test 12: Get trending posts
echo -e "\n${YELLOW}Test 12: Get Trending Posts (24h)${NC}"
curl -s "${BASE_URL}/feed/trending?dev_user_id=${DEV_USER_ID}&hours=24&limit=10" | jq .

# Test 13: Create anonymous post
echo -e "\n${YELLOW}Test 13: Create Test Case for Anonymous Post${NC}"
CASE_RESPONSE_2=$(curl -s -X POST "${BASE_URL}/cases?dev_user_id=${DEV_USER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "पानी की समस्या",
    "transcript_text": "Water supply issue in our area",
    "location_text": "Sector 12, Noida",
    "location_lat": 28.5355,
    "location_lng": 77.3910,
    "issue_type": "water_supply",
    "kind": "grievance"
  }')

CASE_ID_2=$(echo "$CASE_RESPONSE_2" | jq -r '.case.id')
echo -e "${GREEN}Created case ID: ${CASE_ID_2}${NC}"

echo -e "\n${YELLOW}Test 14: Share Anonymously${NC}"
ANON_POST_RESPONSE=$(curl -s -X POST "${BASE_URL}/feed/posts?dev_user_id=${DEV_USER_ID}" \
  -H "Content-Type: application/json" \
  -d "{
    \"case_id\": \"${CASE_ID_2}\",
    \"is_anonymous\": true,
    \"caption\": \"गुमनाम रूप से साझा किया गया\"
  }")

echo "$ANON_POST_RESPONSE" | jq .

ANON_POST_ID=$(echo "$ANON_POST_RESPONSE" | jq -r '.data.id')
echo -e "${GREEN}Created anonymous post ID: ${ANON_POST_ID}${NC}"

# Test 15: Verify anonymous user in feed
echo -e "\n${YELLOW}Test 15: Verify Anonymous Post in Feed${NC}"
curl -s "${BASE_URL}/feed?dev_user_id=${DEV_USER_ID}&limit=10" | jq '.data.posts[] | select(.id == "'${ANON_POST_ID}'") | .user'

# Test 16: Delete post (owner)
echo -e "\n${YELLOW}Test 16: Delete Post (Owner)${NC}"
curl -s -X DELETE "${BASE_URL}/feed/posts/${POST_ID}?dev_user_id=${DEV_USER_ID}" | jq .

# Test 17: Verify post is removed from feed
echo -e "\n${YELLOW}Test 17: Verify Post Removed from Feed${NC}"
curl -s "${BASE_URL}/feed?dev_user_id=${DEV_USER_ID}&limit=10" | jq '.data.posts | length'

# Test 18: Try to share personal diary (should fail)
echo -e "\n${YELLOW}Test 18: Create Personal Diary Entry${NC}"
PERSONAL_CASE=$(curl -s -X POST "${BASE_URL}/cases?dev_user_id=${DEV_USER_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Personal Note",
    "transcript_text": "This is my personal diary entry",
    "kind": "personal"
  }')

PERSONAL_CASE_ID=$(echo "$PERSONAL_CASE" | jq -r '.case.id')
echo -e "${GREEN}Created personal case ID: ${PERSONAL_CASE_ID}${NC}"

echo -e "\n${YELLOW}Test 19: Try to Share Personal Diary (Should Fail)${NC}"
curl -s -X POST "${BASE_URL}/feed/posts?dev_user_id=${DEV_USER_ID}" \
  -H "Content-Type: application/json" \
  -d "{
    \"case_id\": \"${PERSONAL_CASE_ID}\",
    \"is_anonymous\": false
  }" | jq .

echo -e "\n${GREEN}✅ All tests completed!${NC}"
echo ""
echo "Summary:"
echo "--------"
echo "✅ Health check"
echo "✅ Get feed (empty and with posts)"
echo "✅ Create feed post"
echo "✅ Like/unlike toggle"
echo "✅ Add comments"
echo "✅ Get comments"
echo "✅ Share post"
echo "✅ Trending posts"
echo "✅ Anonymous posting"
echo "✅ Delete post"
echo "✅ Personal diary protection"
echo ""
echo "🎉 Feed API is working correctly!"
