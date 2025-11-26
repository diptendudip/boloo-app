# MSG91 SMS OTP Integration Guide

## Overview

This document describes the MSG91 SMS OTP authentication integration for the Boloo backend. MSG91 is a cloud communication platform optimized for India with competitive pricing and high deliverability.

## Features

- ✅ OTP generation and sending via MSG91 SMS API
- ✅ OTP verification with retry limits
- ✅ OTP resend with voice fallback
- ✅ Rate limiting and security
- ✅ Comprehensive error handling
- ✅ Phone number validation for Indian mobiles
- ✅ Development mode with OTP exposure for testing

## MSG91 Setup

### 1. Create MSG91 Account

1. Visit [https://msg91.com/](https://msg91.com/)
2. Sign up for a free account
3. Verify your email and phone number
4. Complete KYC verification (required for production)

### 2. Get API Credentials

1. Login to MSG91 dashboard
2. Go to **Settings** → **API Keys**
3. Copy your **Auth Key** (this is your `MSG91_API_KEY`)

### 3. Configure Sender ID

1. Go to **Settings** → **Sender IDs**
2. Submit a new Sender ID (max 6 characters)
   - Recommended: `BOLOOO` or `BOLOAP`
3. Wait for approval (usually 24-48 hours)

### 4. Create DLT Template

For regulatory compliance in India, you need a DLT (Distributed Ledger Technology) template:

1. Go to **Templates** → **Create Template**
2. Template type: **Transactional**
3. Template content:
   ```
   Your Boloo verification code is {#var#}. Valid for {#var#} minutes. Do not share with anyone.
   ```
4. Submit for approval
5. Copy the **Template ID** once approved

## Environment Configuration

Add these variables to your `.env` file:

```bash
# MSG91 SMS Configuration
MSG91_API_KEY=your-auth-key-from-msg91-dashboard
MSG91_SENDER_ID=BOLOOO
MSG91_TEMPLATE_ID=your-dlt-template-id
MSG91_ROUTE=4
MSG91_OTP_EXPIRY_MINUTES=5
```

### Configuration Parameters

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MSG91_API_KEY` | Auth key from MSG91 dashboard | - | Yes (Prod) |
| `MSG91_SENDER_ID` | Approved sender ID (6 chars max) | `BOLOOO` | Yes |
| `MSG91_TEMPLATE_ID` | DLT template ID for OTP | - | Yes (Prod) |
| `MSG91_ROUTE` | SMS route (4 = Transactional) | `4` | No |
| `MSG91_OTP_EXPIRY_MINUTES` | OTP validity in minutes | `5` | No |

## API Endpoints

### 1. Request OTP

```http
POST /auth/otp/request
Content-Type: application/json

{
  "phone_number": "+919876543210"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "OTP sent to +919876543210",
  "phone_number": "+919876543210",
  "expires_in_minutes": 5,
  "otp_for_testing": "123456"  // Only in development mode
}
```

**Response (Error - Invalid Phone):**
```json
{
  "detail": "Invalid phone number format: +1234567890. Expected format: +91XXXXXXXXXX"
}
```

**Response (Error - Rate Limit):**
```json
{
  "detail": "Too many OTP requests. Please try again later."
}
```

### 2. Verify OTP

```http
POST /auth/otp/verify
Content-Type: application/json

{
  "phone_number": "+919876543210",
  "otp_code": "123456"
}
```

**Response (Success):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "phone": "+919876543210",
    "email": "919876543210@boloo-users.local",
    "role": "citizen",
    "is_first_timer": true
  }
}
```

**Response (Error - Invalid OTP):**
```json
{
  "detail": "Invalid or expired OTP"
}
```

### 3. Resend OTP (Coming Soon)

```http
POST /auth/otp/resend
Content-Type: application/json

{
  "phone_number": "+919876543210",
  "retry_type": "voice"  // "text" or "voice"
}
```

## Phone Number Formats

The service accepts multiple phone number formats and normalizes them:

| Input Format | Normalized Output | Valid |
|--------------|-------------------|-------|
| `+919876543210` | `+919876543210` | ✅ |
| `919876543210` | `+919876543210` | ✅ |
| `9876543210` | `+919876543210` | ✅ |
| `+91 9876 543 210` | `+919876543210` | ✅ |
| `+1234567890` | - | ❌ (Not Indian) |
| `+915876543210` | - | ❌ (Starts with 5) |

**Valid Indian mobile numbers:**
- Must be 10 digits
- Must start with 6, 7, 8, or 9

## Error Handling

### Custom Exceptions

```python
from app.services.msg91_service import (
    MSG91Error,            # Base exception
    MSG91RateLimitError,   # Rate limit exceeded
    MSG91InvalidPhoneError # Invalid phone number
)
```

### HTTP Status Codes

| Status | Meaning | Example |
|--------|---------|---------|
| `200` | Success | OTP sent/verified |
| `400` | Bad Request | Invalid phone format |
| `401` | Unauthorized | Invalid/expired OTP |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Server Error | MSG91 API error |

## Rate Limiting

The service implements multiple rate limiting layers:

1. **Per Phone Number:** 3 requests per 15 minutes
2. **Per IP Address:** 10 requests per hour
3. **MSG91 API:** As per your MSG91 plan

Rate limits are enforced using `slowapi` middleware.

## Security Features

### 1. OTP Expiry
- Default: 5 minutes
- Configurable via `MSG91_OTP_EXPIRY_MINUTES`
- Expired OTPs are automatically rejected

### 2. One-Time Use
- OTPs are marked as used after successful verification
- Cannot reuse the same OTP

### 3. Security Logging
- All OTP requests logged with IP and User-Agent
- Failed verification attempts logged
- Suspicious activity tracked

### 4. Development vs Production

**Development Mode:**
- OTP exposed in API response for testing
- MSG91 API calls mocked if no API key
- Logs include OTP codes

**Production Mode:**
- OTP never exposed in response
- Real MSG91 API calls
- Secure logging without OTP codes

## Testing

### Unit Tests

Run the test suite:

```bash
cd backend
pytest tests/test_msg91_auth.py -v
```

### Manual Testing

1. Start the backend server:
   ```bash
   uvicorn app.main:app --reload
   ```

2. Request OTP:
   ```bash
   curl -X POST http://localhost:8000/auth/otp/request \
     -H "Content-Type: application/json" \
     -d '{"phone_number": "+919876543210"}'
   ```

3. Verify OTP (use the `otp_for_testing` from response):
   ```bash
   curl -X POST http://localhost:8000/auth/otp/verify \
     -H "Content-Type: application/json" \
     -d '{"phone_number": "+919876543210", "otp_code": "123456"}'
   ```

## Monitoring

### Check MSG91 Balance

```python
from app.services.msg91_service import msg91_service

balance = await msg91_service.check_balance()
print(f"Balance: ₹{balance['balance']}")
```

### Logs

All MSG91 operations are logged:

```python
# Success
INFO: MSG91 OTP sent successfully to +919876543210. Request ID: abc123

# Error
ERROR: MSG91 API error: HTTP 429 - Rate limit exceeded

# Warning
WARNING: Invalid phone number format: +1234567890
```

## Cost Estimation

MSG91 pricing (as of 2024):

| Plan | Price per SMS | Recommended For |
|------|---------------|-----------------|
| Free Tier | ₹0.20/SMS | Development/Testing |
| Standard | ₹0.15/SMS | Small apps |
| Premium | ₹0.10/SMS | Production apps |

**Monthly cost estimate for Boloo:**
- 1,000 users × 2 OTPs/user = 2,000 SMS
- 2,000 × ₹0.15 = **₹300/month** (~$3.6/month)

## Troubleshooting

### Issue: OTP not received

**Possible causes:**
1. Invalid phone number format
2. MSG91 API key not configured
3. Sender ID not approved
4. DLT template not approved
5. Insufficient balance

**Solution:**
- Check logs for error messages
- Verify phone number format
- Ensure MSG91 credentials are correct
- Check MSG91 dashboard for balance and approvals

### Issue: "Invalid or expired OTP"

**Possible causes:**
1. OTP expired (>5 minutes old)
2. OTP already used
3. Wrong OTP code entered
4. Database timing issues

**Solution:**
- Request a new OTP
- Verify system clock is correct
- Check database for OTP records

### Issue: Rate limit exceeded

**Possible causes:**
1. Too many requests from same phone/IP
2. MSG91 plan limit reached

**Solution:**
- Wait for rate limit cooldown
- Upgrade MSG91 plan if needed
- Contact support if issue persists

## Production Checklist

Before deploying to production:

- [ ] MSG91 account KYC verified
- [ ] Sender ID approved by MSG91
- [ ] DLT template approved
- [ ] Environment variables set in production
- [ ] Rate limiting configured
- [ ] Security logging enabled
- [ ] Error monitoring setup (Sentry)
- [ ] Load testing completed
- [ ] Backup OTP delivery method configured

## Support

- **MSG91 Support:** [https://msg91.com/help](https://msg91.com/help)
- **MSG91 API Docs:** [https://docs.msg91.com/](https://docs.msg91.com/)
- **Boloo Backend Issues:** [GitHub Issues](https://github.com/your-org/boloo/issues)

## License

This integration is part of the Boloo project and follows the same license terms.
