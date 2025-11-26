# Twilio Setup Guide - SMS Authentication

## 🔐 Step 1: Sign In to Twilio

**Twilio Console:** https://console.twilio.com

### If You Already Have an Account:

1. **Go to:** https://console.twilio.com/login
2. **Enter your credentials** (email/password or phone number)
3. **Click "Log in"**

### If You Need to Create Account:

1. **Go to:** https://www.twilio.com/try-twilio
2. **Fill in:**
   - First Name
   - Last Name
   - Email
   - Password
3. **Verify your email**
4. **Verify your phone number** (they'll send you a code)

---

## 📱 Step 2: Get Your Credentials

Once logged in to Twilio Console:

### **A. Account SID & Auth Token**

1. Go to **Dashboard** (https://console.twilio.com)
2. Look for **"Account Info"** section on the right
3. You'll see:
   - **Account SID:** `ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`
   - **Auth Token:** Click "View" to reveal

   Copy both of these!

### **B. Get a Phone Number**

**For India SMS:**

1. Go to **Phone Numbers** → **Buy a Number**
2. **Select Country:** India (+91)
3. **Capabilities:** Check ☑ SMS
4. **Search** for available numbers
5. **Buy** a number (costs ~$1-2/month)

**Important:** Twilio India numbers can send SMS to Indian mobile numbers!

---

## 💰 Twilio Costs for India

| Service | Cost |
|---------|------|
| Phone Number | ~₹80-150/month |
| SMS (India) | ₹0.50-1.50 per message |
| **Estimated for 1,000 OTPs/month** | **₹650-1,650/month** |

**Your Budget:** ₹13,000+ remaining after Azure costs ✅

---

## 🔧 Step 3: Configure in Boloo Backend

Once you have the credentials, I'll configure them on Azure:

### **Credentials Needed:**

```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+91XXXXXXXXXX
```

### **How to Provide Them:**

**Option 1: Tell me here** (I'll configure on Azure securely)

**Option 2: Add to backend/.env locally** (for testing)
```bash
cd "/Users/diptendu/boloo app/boloo-app/backend"
echo "TWILIO_ACCOUNT_SID=ACxxxx..." >> .env
echo "TWILIO_AUTH_TOKEN=xxxx..." >> .env
echo "TWILIO_PHONE_NUMBER=+91xxxx..." >> .env
```

**Option 3: Configure directly on Azure**
```bash
az webapp config appsettings set \
  --name boloo-backend-app \
  --resource-group cgnet-mvp-rg \
  --settings \
    TWILIO_ACCOUNT_SID="ACxxxx..." \
    TWILIO_AUTH_TOKEN="xxxx..." \
    TWILIO_PHONE_NUMBER="+91xxxx..."
```

---

## 📝 Step 4: Update Backend Code (If Needed)

Check if backend is already configured for Twilio:

**File:** `backend/app/routers/auth.py`

Should have SMS sending logic. If using email OTP currently, we need to switch to Twilio SMS.

---

## ✅ Step 5: Test SMS OTP

Once configured:

```bash
# Test sending OTP
curl -X POST https://boloo-backend-app.azurewebsites.net/api/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+91XXXXXXXXXX"}'

# Should receive SMS with 6-digit code

# Verify OTP
curl -X POST https://boloo-backend-app.azurewebsites.net/api/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+91XXXXXXXXXX", "otp_code": "123456"}'
```

---

## 🚨 Troubleshooting

### **Error: "Unverified number"**
- In Twilio trial account, you can only send to verified numbers
- **Solution:** Either:
  1. Add test numbers to "Verified Caller IDs" in Twilio console
  2. Upgrade to paid account ($20 credit)

### **Error: "Twilio credentials invalid"**
- Check Account SID and Auth Token are correct
- Make sure no extra spaces
- Restart Azure app: `az webapp restart --name boloo-backend-app --resource-group cgnet-mvp-rg`

### **SMS not received**
- Check phone number format: `+91XXXXXXXXXX` (with +91 prefix)
- Verify number is Indian mobile (Twilio India numbers work for India)
- Check Twilio logs: https://console.twilio.com/monitor/logs/sms

---

## 📊 Twilio Dashboard Features

**Monitor Usage:** https://console.twilio.com/monitor/logs/sms
- See all SMS sent
- Check delivery status
- View costs

**Set Budget Alerts:**
1. Go to **Billing** → **Alerts**
2. Set alert at ₹1,000/month
3. Enter email: diptendudip@gmail.com

---

## 🔐 Security Best Practices

1. **Never commit credentials** to GitHub (already protected by .gitignore)
2. **Use Azure App Settings** for production credentials
3. **Rotate Auth Token** periodically (every 90 days)
4. **Enable IP whitelisting** in Twilio (optional)
5. **Monitor usage** to detect abuse

---

## 📱 Alternative: Use Existing Twilio Account

If you mentioned Twilio is "already logged in", check:

1. **Browser:** Look for saved credentials in browser password manager
2. **VSCode:** Check if credentials in any .env files:
   ```bash
   grep -r "TWILIO" "/Users/diptendu/boloo app/boloo-app" --include="*.env*"
   ```
3. **Twilio CLI:** If installed, run `twilio profiles:list`

---

## ✅ Quick Start Checklist

- [ ] Sign in to Twilio Console
- [ ] Copy Account SID
- [ ] Copy Auth Token
- [ ] Buy India phone number (+91)
- [ ] Provide credentials to Claude
- [ ] Test OTP sending
- [ ] Set budget alert in Twilio

---

**Need help?** Just provide me with:
1. Account SID
2. Auth Token
3. Phone Number

And I'll configure everything on Azure!

**Generated:** November 20, 2025
