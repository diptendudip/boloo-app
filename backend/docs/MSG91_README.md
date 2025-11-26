# MSG91 SMS OTP Authentication - README

## 📋 Quick Overview

Production-ready MSG91 SMS OTP authentication system for the Boloo backend. Supports Indian mobile numbers with comprehensive security, rate limiting, and error handling.

## 🎯 What Was Implemented

### Core Features
✅ MSG91 SMS OTP sending
✅ OTP verification with JWT tokens
✅ OTP resend with voice fallback
✅ Phone number validation (Indian mobiles)
✅ Rate limiting (3/15min per phone)
✅ Security logging and audit trail
✅ Development mode for testing
✅ Comprehensive error handling

### API Endpoints
1. `POST /auth/otp/request` - Request OTP
2. `POST /auth/otp/verify` - Verify OTP and get JWT
3. `POST /auth/otp/resend` - Resend OTP (SMS/Voice)

## 🚀 Getting Started

### Development Mode (No MSG91 Account Needed)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Leave MSG91_API_KEY empty in .env (uses mock)
MSG91_API_KEY=

# 3. Start server
uvicorn app.main:app --reload

# 4. Test with curl
curl -X POST http://localhost:8000/auth/otp/request \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+919876543210"}'

# Response includes OTP in dev mode:
# {"otp_for_testing": "123456", ...}
```

### Production Mode (Requires MSG91 Account)

```bash
# 1. Sign up at https://msg91.com/
# 2. Get Auth Key, Sender ID, Template ID
# 3. Configure .env:

MSG91_API_KEY=your-auth-key
MSG91_SENDER_ID=BOLOOO
MSG91_TEMPLATE_ID=your-template-id
MSG91_ROUTE=4
MSG91_OTP_EXPIRY_MINUTES=5

# 4. Deploy and test
```

## 📁 Files Created/Modified

### New Files
- `/app/services/msg91_service.py` - MSG91 service (replaced)
- `/tests/test_msg91_auth.py` - Test suite (18+ tests)
- `/docs/MSG91_INTEGRATION.md` - Complete guide
- `/docs/MSG91_QUICKSTART.md` - Quick start
- `/docs/MSG91_IMPLEMENTATION_SUMMARY.md` - Summary
- `/docs/MSG91_README.md` - This file

### Modified Files
- `/app/config.py` - Added MSG91 settings
- `/app/routers/auth.py` - Integrated MSG91 + added resend endpoint
- `/requirements.txt` - Added phonenumbers library
- `/.env.example` - Added MSG91 configuration template

## 🔧 Configuration

### Environment Variables

```bash
# MSG91 Configuration
MSG91_API_KEY=              # Required for production
MSG91_SENDER_ID=BOLOOO      # 6 chars max (default: BOLOOO)
MSG91_TEMPLATE_ID=          # DLT template ID
MSG91_ROUTE=4               # 4 = Transactional (default)
MSG91_OTP_EXPIRY_MINUTES=5  # OTP validity (default: 5)
```

### Phone Number Formats

All formats accepted:
- `+919876543210` ✅
- `919876543210` ✅
- `9876543210` ✅

Validation:
- Must be 10 digits after removing country code
- Must start with 6, 7, 8, or 9 (Indian mobile)

## 🧪 Testing

### Run Test Suite
```bash
pytest tests/test_msg91_auth.py -v
```

### Manual Testing
```bash
# Request OTP
curl -X POST http://localhost:8000/auth/otp/request \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+919876543210"}'

# Verify OTP
curl -X POST http://localhost:8000/auth/otp/verify \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+919876543210", "otp_code": "123456"}'

# Resend OTP (voice)
curl -X POST http://localhost:8000/auth/otp/resend \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+919876543210", "retry_type": "voice"}'
```

## 🔒 Security

### Rate Limits
- **OTP Request:** 3 per 15 minutes per phone
- **OTP Request:** 10 per hour per IP
- **OTP Verify:** 5 per minute per IP
- **OTP Resend:** 2 per 10 minutes per phone

### Security Features
- 6-digit random OTP
- 5-minute expiry
- One-time use enforcement
- Phone number validation
- IP and User-Agent logging
- Production/development mode separation

## 📊 Cost Estimation

### MSG91 Pricing
- Free Tier: ₹0.20/SMS
- Standard: ₹0.15/SMS
- Premium: ₹0.10/SMS

### Monthly Estimate
- 1,000 users × 2 OTPs = 2,000 SMS
- 2,000 × ₹0.15 = **₹300/month** (~$3.6/month)

Very affordable for India-focused apps!

## 🐛 Troubleshooting

### "Invalid phone number format"
✅ Use Indian mobile numbers only (+919876543210)

### "Invalid or expired OTP"
✅ Request new OTP (5-minute expiry)

### "Too many OTP requests"
✅ Wait 15 minutes for rate limit reset

### OTP not received (Production)
1. Check MSG91 dashboard for delivery status
2. Verify Sender ID is approved
3. Verify DLT template is approved
4. Check MSG91 balance

## 📚 Documentation

1. **[MSG91_QUICKSTART.md](MSG91_QUICKSTART.md)** - 5-minute setup guide
2. **[MSG91_INTEGRATION.md](MSG91_INTEGRATION.md)** - Complete integration guide
3. **[MSG91_IMPLEMENTATION_SUMMARY.md](MSG91_IMPLEMENTATION_SUMMARY.md)** - Technical summary
4. **[MSG91_README.md](MSG91_README.md)** - This file

## 🎯 Production Checklist

Before deploying:

- [ ] MSG91 account created
- [ ] KYC verification completed
- [ ] Sender ID approved (BOLOOO)
- [ ] DLT template created and approved
- [ ] Environment variables set
- [ ] Tests passing
- [ ] Rate limiting enabled
- [ ] Error monitoring configured
- [ ] Load testing completed
- [ ] Balance alerts set up

## 🔗 Useful Links

- **MSG91 Website:** https://msg91.com/
- **MSG91 API Docs:** https://docs.msg91.com/
- **MSG91 Support:** https://msg91.com/help
- **Boloo Backend:** [GitHub Repository]

## 💡 Pro Tips

1. **Development:** Leave `MSG91_API_KEY` empty for mock OTP
2. **Testing:** Use `otp_for_testing` from dev mode response
3. **Production:** Monitor MSG91 balance regularly
4. **Fallback:** Use voice OTP for better deliverability
5. **Security:** Never log OTP codes in production

## ✅ Status

**Implementation:** ✅ Complete
**Testing:** ✅ 18+ test cases
**Documentation:** ✅ Complete
**Production Ready:** ✅ Yes (after MSG91 setup)

---

**Need Help?** Check the [Troubleshooting](#-troubleshooting) section or refer to the complete [Integration Guide](MSG91_INTEGRATION.md).

**Last Updated:** November 24, 2024
**Version:** 1.0.0
