# MSG91 OTP Quick Start Guide

## 🚀 5-Minute Setup

### Step 1: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

Add to your `.env` file:

```bash
# MSG91 Configuration (Development - leave empty to use mock)
MSG91_API_KEY=
MSG91_SENDER_ID=BOLOOO
MSG91_TEMPLATE_ID=
MSG91_ROUTE=4
MSG91_OTP_EXPIRY_MINUTES=5
```

**For Development:** Leave `MSG91_API_KEY` empty to use mock OTP (OTP will be returned in API response).

**For Production:** Get credentials from [https://msg91.com/](https://msg91.com/)

### Step 3: Test the API

#### Request OTP

```bash
curl -X POST http://localhost:8000/auth/otp/request \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+919876543210"}'
```

**Response (Dev Mode):**
```json
{
  "success": true,
  "message": "OTP sent to +919876543210",
  "phone_number": "+919876543210",
  "expires_in_minutes": 5,
  "otp_for_testing": "123456"
}
```

#### Verify OTP

```bash
curl -X POST http://localhost:8000/auth/otp/verify \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919876543210",
    "otp_code": "123456"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "phone": "+919876543210",
    "role": "citizen"
  }
}
```

#### Resend OTP

```bash
# Resend via SMS
curl -X POST http://localhost:8000/auth/otp/resend \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919876543210",
    "retry_type": "text"
  }'

# Resend via Voice Call
curl -X POST http://localhost:8000/auth/otp/resend \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919876543210",
    "retry_type": "voice"
  }'
```

## 📱 Phone Number Formats

All formats are accepted and normalized:

| Input | Normalized |
|-------|------------|
| `+919876543210` | `+919876543210` |
| `919876543210` | `+919876543210` |
| `9876543210` | `+919876543210` |

## 🔒 Security Features

### Rate Limiting

- **OTP Request:** 3 requests per 15 minutes per phone
- **OTP Request:** 10 requests per hour per IP
- **OTP Verify:** 5 attempts per minute per IP
- **OTP Resend:** 2 resends per 10 minutes per phone

### OTP Expiry

- Default: 5 minutes
- Configurable via `MSG91_OTP_EXPIRY_MINUTES`

### One-Time Use

- Each OTP can only be used once
- Expired OTPs are rejected

## 🧪 Running Tests

```bash
cd backend
pytest tests/test_msg91_auth.py -v
```

**Test Coverage:**
- ✅ OTP request with valid/invalid phone numbers
- ✅ OTP verification (success/failure cases)
- ✅ OTP expiry handling
- ✅ OTP reuse prevention
- ✅ Phone number normalization
- ✅ Rate limiting
- ✅ Complete authentication flow

## 🔧 Troubleshooting

### "Invalid phone number format"

**Solution:** Use Indian mobile numbers only (starts with 6, 7, 8, or 9)

```bash
# ✅ Correct
+919876543210
919876543210
9876543210

# ❌ Wrong
+1234567890  # Not Indian
+915876543210  # Starts with 5
```

### "Invalid or expired OTP"

**Possible causes:**
1. OTP expired (>5 minutes old)
2. Wrong OTP code
3. OTP already used

**Solution:** Request a new OTP

### "Too many OTP requests"

**Solution:** Wait for rate limit cooldown (15 minutes)

## 📊 Production Setup

### 1. Get MSG91 Account

1. Sign up at [https://msg91.com/](https://msg91.com/)
2. Complete KYC verification
3. Get Auth Key from dashboard

### 2. Configure Sender ID

1. Submit Sender ID for approval (6 chars max: `BOLOOO`)
2. Wait 24-48 hours for approval

### 3. Create DLT Template

**Template:**
```
Your Boloo verification code is {#var#}. Valid for {#var#} minutes. Do not share.
```

Get Template ID after approval.

### 4. Update Production Environment

```bash
MSG91_API_KEY=your-actual-auth-key
MSG91_SENDER_ID=BOLOOO
MSG91_TEMPLATE_ID=your-template-id
MSG91_ROUTE=4
MSG91_OTP_EXPIRY_MINUTES=5
```

### 5. Deploy and Monitor

- Check MSG91 dashboard for delivery reports
- Monitor logs for errors
- Set up balance alerts

## 📈 Cost Estimation

**MSG91 Pricing:**
- Free Tier: ₹0.20/SMS
- Standard: ₹0.15/SMS
- Premium: ₹0.10/SMS

**Example:**
- 1,000 users × 2 OTPs = 2,000 SMS
- 2,000 × ₹0.15 = **₹300/month** (~$3.6/month)

## 🎯 API Endpoints Summary

| Endpoint | Method | Purpose | Rate Limit |
|----------|--------|---------|------------|
| `/auth/otp/request` | POST | Request OTP | 3/15min per phone |
| `/auth/otp/verify` | POST | Verify OTP | 5/min per IP |
| `/auth/otp/resend` | POST | Resend OTP | 2/10min per phone |
| `/auth/profile` | PUT | Update profile | No limit |

## 📚 Related Documentation

- [Complete Integration Guide](MSG91_INTEGRATION.md)
- [MSG91 API Docs](https://docs.msg91.com/)
- [Boloo Backend README](../README.md)

## 💡 Tips

1. **Development:** Leave `MSG91_API_KEY` empty to use mock OTP
2. **Testing:** Use `otp_for_testing` from response in dev mode
3. **Production:** Never expose OTP in logs or responses
4. **Monitoring:** Check MSG91 balance regularly
5. **Fallback:** Implement voice OTP for better deliverability

## ✅ Checklist

Before going live:

- [ ] MSG91 account verified
- [ ] Sender ID approved
- [ ] DLT template approved
- [ ] Environment variables configured
- [ ] Tests passing
- [ ] Rate limiting enabled
- [ ] Error monitoring setup
- [ ] Load testing completed

---

**Need Help?** Check the [troubleshooting section](#-troubleshooting) or open an issue on GitHub.
