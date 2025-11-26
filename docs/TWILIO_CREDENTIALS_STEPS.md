# Get Twilio API Credentials - Step by Step

You've provided your Twilio login credentials. Now let's get the API credentials needed for the backend.

## 🔐 Step-by-Step Instructions:

### **Step 1: Log In to Twilio**

1. **Go to:** https://login.twilio.com
2. **Enter:**
   - Username: `chaitlemaandi@gmail.com`
   - Password: `Dip@0106`
3. **Click "Log in"**

---

### **Step 2: Get Account SID and Auth Token**

Once you're logged in:

1. **You'll see the Dashboard** - Look at the **right sidebar**
2. **Find "Account Info" section** - It shows:
   - **Account SID**: `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - **Auth Token**: Click the "View" button to reveal

3. **Copy both values** - You'll need these!

---

### **Step 3: Get/Buy a Phone Number**

If you already have a number:
1. Go to **Phone Numbers** → **Manage** → **Active numbers**
2. Copy your number (format: `+91XXXXXXXXXX`)

If you need to buy one:
1. Go to **Phone Numbers** → **Buy a number**
2. Select **Country: India**
3. Check **☑ SMS** capability
4. Click **Search**
5. **Buy** a number (~₹80-150/month)

---

### **Step 4: Provide These 3 Values**

Once you have them, just paste here:

```
Account SID: ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Auth Token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Phone Number: +91XXXXXXXXXX
```

Then I'll configure them on Azure!

---

## 📱 Quick Access Links:

- **Dashboard (Account SID/Token):** https://console.twilio.com
- **Phone Numbers:** https://console.twilio.com/phone-numbers/active
- **Buy a Number:** https://console.twilio.com/phone-numbers/search

---

## 🔒 Security Note:

Your login credentials (`chaitlemaandi@gmail.com` / `Dip@0106`) are for accessing Twilio console only.

The **API credentials** (Account SID, Auth Token) are what the backend uses to send SMS.

Both are kept secure:
- Login creds: Only you use them
- API creds: Stored in Azure App Settings (never in code)

---

**Ready?** Log in and copy those 3 values! 🚀
