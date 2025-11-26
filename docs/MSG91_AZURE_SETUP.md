# MSG91 Production Setup Guide for Azure

## Overview

This guide explains how to configure MSG91 SMS OTP service for the Boloo backend running on Azure.

## Current Status

| Setting | Current Value | Required Action |
|---------|---------------|-----------------|
| `MSG91_API_KEY` | (empty) | Get from MSG91 dashboard |
| `MSG91_SENDER_ID` | BOLOOO | Submit for approval |
| `MSG91_TEMPLATE_ID` | (empty) | Create DLT template |
| `MSG91_ROUTE` | 4 (Transactional) | No change needed |
| `MSG91_OTP_EXPIRY_MINUTES` | 5 | No change needed |

## Demo Account (No MSG91 Required)

For testing purposes, a demo account bypasses MSG91:
- **Phone**: `9999999999` or `+919999999999`
- **OTP**: `123456`

This works without any MSG91 configuration.

## Steps to Enable Real OTP

### Step 1: Create MSG91 Account

1. Go to [https://msg91.com/](https://msg91.com/)
2. Sign up for a new account
3. Complete KYC verification (PAN, Aadhaar required)
4. Add credits (minimum ~₹500)

### Step 2: Get API Key (Authkey)

1. Login to MSG91 dashboard
2. Go to **Settings** → **API** → **Authkey**
3. Copy the authkey (it looks like: `123456AbCdEf789012...`)

### Step 3: Register Sender ID

1. Go to **Sender ID** section
2. Create new Sender ID: `BOLOOO` (6 characters max)
3. Select entity type: **Promotional** or **Transactional**
4. Wait for approval (24-48 hours)

### Step 4: Create DLT Template

**TRAI DLT Registration is MANDATORY for India**

1. Register on your telecom's DLT portal:
   - Jio: https://trueconnect.jio.com/
   - Airtel: https://www.airtel.in/business/commercial-communication
   - Vodafone-Idea: https://vilpower.in/
   - BSNL: https://www.ucc-bsnl.co.in/

2. Create OTP template with this exact format:
   ```
   Your Boloo verification code is {#var#}. Valid for {#var#} minutes. Do not share this code with anyone.
   ```

3. Wait for DLT approval (3-5 business days)

4. Get the **Template ID** (e.g., `1207161234567890123`)

### Step 5: Configure Azure App Settings

Run this command with your actual values:

```bash
az webapp config appsettings set \
  --resource-group boloo-production-rg \
  --name boloo-backend-api \
  --settings \
    MSG91_API_KEY="YOUR_ACTUAL_MSG91_AUTHKEY" \
    MSG91_SENDER_ID="BOLOOO" \
    MSG91_TEMPLATE_ID="YOUR_DLT_TEMPLATE_ID"
```

### Step 6: Restart Backend

```bash
az webapp restart --resource-group boloo-production-rg --name boloo-backend-api
```

### Step 7: Test Real OTP

```bash
# Request OTP (with a real Indian phone number)
curl -X POST https://boloo-backend-api.azurewebsites.net/v1/auth/otp/request \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+91YOUR_REAL_NUMBER"}'

# You should receive an SMS with OTP

# Verify OTP
curl -X POST https://boloo-backend-api.azurewebsites.net/v1/auth/otp/verify \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+91YOUR_REAL_NUMBER", "otp_code": "RECEIVED_OTP"}'
```

## Cost Estimation

| Plan | Cost per SMS | Monthly (1000 users × 2 OTPs) |
|------|-------------|-------------------------------|
| Free Tier | ₹0.20 | ₹400 (~$5) |
| Standard | ₹0.15 | ₹300 (~$3.6) |
| Premium | ₹0.10 | ₹200 (~$2.4) |

## Troubleshooting

### "Invalid API Key"
- Verify the authkey is correct
- Check if account has credits

### "Sender ID not approved"
- Wait for MSG91 approval
- Contact MSG91 support

### "Template not found"
- Ensure DLT template is approved
- Template ID must match exactly

### "SMS not delivered"
- Check MSG91 delivery reports
- Verify phone number format (+91XXXXXXXXXX)
- Check if number is DND registered

## Security Notes

1. **Never expose MSG91_API_KEY** in client-side code
2. **Rate limiting** is enabled (3 OTPs per 15 min per phone)
3. **Demo account works only for 9999999999**
4. **Production OTPs expire in 5 minutes**

## Alternative: Keep Demo Mode

If you don't need real SMS OTP immediately:

1. Keep `MSG91_API_KEY` empty
2. Demo account continues to work
3. All other phones will fail (expected behavior)
4. Enable MSG91 when ready for real users

---

## Quick Reference

### Azure CLI Commands

```bash
# View current settings
az webapp config appsettings list --resource-group boloo-production-rg --name boloo-backend-api --query "[?contains(name, 'MSG91')]" -o table

# Update settings
az webapp config appsettings set --resource-group boloo-production-rg --name boloo-backend-api --settings MSG91_API_KEY="your-key"

# Restart after changes
az webapp restart --resource-group boloo-production-rg --name boloo-backend-api
```

### Test Endpoints

```bash
# Health check
curl https://boloo-backend-api.azurewebsites.net/health

# Demo login
curl -X POST https://boloo-backend-api.azurewebsites.net/v1/auth/otp/request \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+919999999999"}'

curl -X POST https://boloo-backend-api.azurewebsites.net/v1/auth/otp/verify \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+919999999999", "otp_code": "123456"}'
```

---

*Last Updated: November 2024*
