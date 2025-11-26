# MSG91 Setup Guide - SMS Authentication for India

**MSG91 is perfect for Indian SMS!** Much better than Twilio for India.

---

## 🔐 Step 1: Get MSG91 API Credentials

### **Log In to MSG91:**

**Dashboard:** https://control.msg91.com/signin/

Once logged in, follow these steps:

---

### **Step 2: Get Your Auth Key (API Key)**

1. **Go to:** https://control.msg91.com/app/settings/api-keys
   - Or click **"API Keys"** in left sidebar under Settings

2. **You'll see your API Keys:**
   - **Auth Key**: `xxxxxxxxxxxxxxxxxxxxxxxx` (main API key)
   - Copy this value!

3. **If you don't see any key:**
   - Click **"Create New API Key"**
   - Give it a name (e.g., "Boloo MVP")
   - Copy the key shown

---

### **Step 3: Get Your Sender ID**

**Sender ID** is what appears as the sender name in SMS (e.g., "BOLOO" or "BULTOO")

1. **Go to:** https://control.msg91.com/app/senderId
   - Or click **"Sender IDs"** in left sidebar

2. **Check if you have an approved Sender ID:**
   - Status should be **"Approved"**
   - Copy the Sender ID (e.g., `BOLOO`, `BULTOO`, etc.)

3. **If you don't have one:**
   - Click **"Create New Sender ID"**
   - Enter: `BOLOO` or `BULTOO` (6 characters max)
   - Select **"Transactional"** (for OTP)
   - Submit for approval (takes 1-2 days)
   - **For testing:** Use default sender ID like `MSGIND`

---

### **Step 4: Get Template ID (for OTP)**

MSG91 requires pre-approved templates for OTP:

1. **Go to:** https://control.msg91.com/app/sms/template
   - Or click **"SMS Templates"** in left sidebar

2. **Check for OTP template:**
   - Look for template with text like: `Your OTP is ##OTP##. Valid for 10 minutes.`
   - Copy the **Template ID**

3. **If you don't have one:**
   - Click **"Create New Template"**
   - **Template Type:** Transactional
   - **Message:**
     ```
     Your Boloo verification code is ##OTP##. Valid for 10 minutes. Do not share with anyone.
     ```
   - Replace `##OTP##` with variable placeholder
   - Submit for approval
   - **For testing:** Use a default approved template

---

## 📝 **Credentials Needed:**

Once you have them, provide these 3 values:

```
MSG91_AUTH_KEY=xxxxxxxxxxxxxxxxxxxxxxxx
MSG91_SENDER_ID=BOLOO (or BULTOO or MSGIND)
MSG91_TEMPLATE_ID=xxxxxxxxxxxxxxxxxxxxxxxx (optional for testing)
```

---

## 💰 **MSG91 Costs (Much Better for India!)**

| Service | Cost |
|---------|------|
| OTP SMS (India) | ₹0.15-0.25 per SMS |
| Sender ID | Free |
| **1,000 OTPs/month** | **₹150-250** 💰 |

**Compare with Twilio:**
- Twilio: ₹0.50-1.50 per SMS = ₹500-1,500/month
- MSG91: ₹0.15-0.25 per SMS = ₹150-250/month
- **Save 70-80%!** 🎉

---

## 🔧 **Quick Links:**

- **Login:** https://control.msg91.com/signin/
- **API Keys:** https://control.msg91.com/app/settings/api-keys
- **Sender IDs:** https://control.msg91.com/app/senderId
- **Templates:** https://control.msg91.com/app/sms/template
- **Documentation:** https://docs.msg91.com/

---

## ✅ **After You Provide Credentials:**

I'll:
1. ✅ Update backend code to use MSG91
2. ✅ Configure credentials on Azure
3. ✅ Test SMS sending
4. ✅ Deploy to production

---

## 📱 **MSG91 Features (Better than Twilio for India):**

✅ **Indian company** - Better India support
✅ **Cheaper** - 70-80% cheaper than Twilio
✅ **Faster delivery** - Optimized for Indian carriers
✅ **No phone number needed** - Uses Sender ID
✅ **Pre-approved templates** - Compliant with TRAI regulations
✅ **Better delivery rates** - 98%+ in India

---

## 🚀 **Quick Start:**

1. **Log in:** https://control.msg91.com/signin/
2. **Get Auth Key** from API Keys section
3. **Get Sender ID** from Sender IDs section (use MSGIND for testing)
4. **Copy Template ID** if you have approved OTP template

**Then paste here:**
```
AUTH_KEY: xxxxx
SENDER_ID: BOLOO (or MSGIND)
TEMPLATE_ID: xxxxx (optional)
```

I'll configure everything!

---

## 🔒 **Security:**

- Auth Key is like a password - keep it secret
- Never commit to GitHub (already protected by .gitignore)
- Stored securely in Azure App Settings
- Can be rotated anytime from MSG91 dashboard

---

**Ready?** Log in to MSG91 and grab those credentials! 🚀

**Note:** If you don't have approved Sender ID/Template yet, we can start with default ones for testing and apply for approval later.
