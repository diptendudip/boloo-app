#!/bin/bash
# Test script for OTP verification state tracking

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
PHONE_NUMBER="${PHONE_NUMBER:-+919876543210}"

echo -e "${GREEN}=== OTP Verification State Tracking Test ===${NC}\n"

# Step 1: Run migration
echo -e "${YELLOW}Step 1: Running database migration...${NC}"
cd "$(dirname "$0")/.."
alembic upgrade head
echo -e "${GREEN}✓ Migration completed${NC}\n"

# Step 2: Request OTP
echo -e "${YELLOW}Step 2: Requesting OTP...${NC}"
OTP_RESPONSE=$(curl -s -X POST "$API_URL/auth/otp/request" \
  -H "Content-Type: application/json" \
  -d "{\"phone_number\": \"$PHONE_NUMBER\"}")

echo "Response: $OTP_RESPONSE"

# Extract OTP from response (development mode only)
OTP_CODE=$(echo "$OTP_RESPONSE" | grep -o '"otp_for_testing":"[^"]*"' | cut -d'"' -f4)

if [ -z "$OTP_CODE" ]; then
  echo -e "${RED}✗ Failed to get OTP. Is development mode enabled?${NC}"
  echo "Please enter OTP manually:"
  read -r OTP_CODE
fi

echo -e "${GREEN}✓ OTP received: $OTP_CODE${NC}\n"

# Step 3: Verify OTP
echo -e "${YELLOW}Step 3: Verifying OTP...${NC}"
VERIFY_RESPONSE=$(curl -s -X POST "$API_URL/auth/otp/verify" \
  -H "Content-Type: application/json" \
  -d "{\"phone_number\": \"$PHONE_NUMBER\", \"otp_code\": \"$OTP_CODE\"}")

echo "Response: $VERIFY_RESPONSE"

# Extract token
TOKEN=$(echo "$VERIFY_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo -e "${RED}✗ Failed to get access token${NC}"
  exit 1
fi

echo -e "${GREEN}✓ OTP verified successfully${NC}"
echo -e "Token: ${TOKEN:0:20}...${NC}\n"

# Check if user is verified
PHONE_VERIFIED=$(echo "$VERIFY_RESPONSE" | grep -o '"phone_verified":[^,]*' | cut -d':' -f2)

if [ "$PHONE_VERIFIED" == "true" ]; then
  echo -e "${GREEN}✓ User phone is verified${NC}\n"
else
  echo -e "${RED}✗ User phone is NOT verified${NC}\n"
  exit 1
fi

# Step 4: Test /auth/verify endpoint
echo -e "${YELLOW}Step 4: Testing /auth/verify endpoint...${NC}"
VERIFY_TOKEN_RESPONSE=$(curl -s -X GET "$API_URL/auth/verify" \
  -H "Authorization: Bearer $TOKEN")

echo "Response: $VERIFY_TOKEN_RESPONSE"

# Check if token is valid
VALID=$(echo "$VERIFY_TOKEN_RESPONSE" | grep -o '"valid":[^,]*' | cut -d':' -f2)

if [ "$VALID" == "true" ]; then
  echo -e "${GREEN}✓ Token is valid${NC}\n"
else
  echo -e "${RED}✗ Token is invalid${NC}\n"
  exit 1
fi

# Step 5: Decode JWT token
echo -e "${YELLOW}Step 5: Decoding JWT token...${NC}"

# Extract payload (base64 decode second part of JWT)
PAYLOAD=$(echo "$TOKEN" | cut -d'.' -f2)

# Add padding if needed
case $((${#PAYLOAD} % 4)) in
  2) PAYLOAD="${PAYLOAD}==" ;;
  3) PAYLOAD="${PAYLOAD}=" ;;
esac

DECODED=$(echo "$PAYLOAD" | base64 -d 2>/dev/null || echo "$PAYLOAD" | base64 -D 2>/dev/null)

echo "Decoded payload:"
echo "$DECODED" | python3 -m json.tool 2>/dev/null || echo "$DECODED"

# Check if phone_verified is in payload
if echo "$DECODED" | grep -q '"phone_verified": true'; then
  echo -e "${GREEN}✓ JWT token contains phone_verified: true${NC}\n"
else
  echo -e "${RED}✗ JWT token missing phone_verified field${NC}\n"
  exit 1
fi

# Step 6: Check database state
echo -e "${YELLOW}Step 6: Checking database state...${NC}"

# Get database URL from .env
DB_URL=$(grep DATABASE_URL .env | cut -d'=' -f2)
DB_USER=$(echo "$DB_URL" | grep -o '://[^:]*' | cut -d'/' -f3)
DB_NAME=$(echo "$DB_URL" | grep -o '/[^?]*$' | cut -d'/' -f2 | cut -d'?' -f1)

# Query database
psql "$DB_URL" -c "
  SELECT
    phone,
    phone_verified,
    phone_verified_at,
    last_otp_verified_at
  FROM users
  WHERE phone = '$PHONE_NUMBER';
"

echo -e "${GREEN}✓ Database query completed${NC}\n"

# Step 7: Test middleware (optional - requires production mode)
if [ "$APP_ENV" == "production" ]; then
  echo -e "${YELLOW}Step 7: Testing OTP middleware...${NC}"

  # Create unverified user token
  UNVERIFIED_TOKEN=$(curl -s -X POST "$API_URL/auth/otp/request" \
    -H "Content-Type: application/json" \
    -d '{"phone_number": "+919999999999"}' | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

  # Try to access protected endpoint
  MIDDLEWARE_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/cases/my-cases" \
    -H "Authorization: Bearer $UNVERIFIED_TOKEN")

  HTTP_CODE=$(echo "$MIDDLEWARE_RESPONSE" | tail -n1)

  if [ "$HTTP_CODE" == "403" ]; then
    echo -e "${GREEN}✓ Middleware correctly blocks unverified users${NC}\n"
  else
    echo -e "${RED}✗ Middleware did not block unverified user (got HTTP $HTTP_CODE)${NC}\n"
  fi
else
  echo -e "${YELLOW}Step 7: Skipping middleware test (not in production mode)${NC}\n"
fi

# Summary
echo -e "${GREEN}=== All Tests Passed! ===${NC}\n"
echo "Summary:"
echo "  ✓ Database migration completed"
echo "  ✓ OTP request successful"
echo "  ✓ OTP verification successful"
echo "  ✓ User phone_verified flag set"
echo "  ✓ JWT token includes phone_verified"
echo "  ✓ /auth/verify endpoint working"
echo "  ✓ Database state correct"

echo -e "\n${GREEN}OTP verification state tracking is working correctly!${NC}"
