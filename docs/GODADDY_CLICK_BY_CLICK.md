# GoDaddy DNS Setup - Click-by-Click Guide

## Looking at Your Current Screen

I can see your GoDaddy DNS Management page. Here's exactly what to do:

---

## ✅ STEP 1: Find the www CNAME Record

Look at your DNS Records table. You'll see:

**Row 4** (has a red box around it in your screenshot):
- Type: **CNAME**
- Name: **www**
- Data: **bultoo.com.** ← This needs to change!
- TTL: 1 Hour

---

## ✅ STEP 2: Click the Edit Button

On Row 4 (the www CNAME record):

1. **Look at the far right** of that row
2. You'll see a small **pencil icon** (Edit button)
3. **Click the pencil icon**

---

## ✅ STEP 3: Edit the Record

A popup/form will appear. You'll see fields like:

```
Type: CNAME
Name: www
Points to: bultoo.com.    ← CHANGE THIS!
TTL: 1 Hour
```

**CHANGE THIS:**
1. **Clear** the "Points to" or "Data" field (delete "bultoo.com.")
2. **Type** this exact value:
   ```
   lemon-coast-0f65c5710.3.azurestaticapps.net
   ```
3. Make sure there are **NO EXTRA SPACES** at the end
4. **DO NOT add a dot** at the end
5. Leave TTL as "1 Hour"

---

## ✅ STEP 4: Save

1. Look for a **"Save"** button at the bottom of the popup
2. **Click "Save"**
3. You might see a confirmation message

---

## ✅ STEP 5: Verify the Change

After saving, look at your DNS Records table again.

**Row 4 should now show:**
- Type: CNAME
- Name: www
- Data: **lemon-coast-0f65c5710.3.azurestaticapps.net** ✅
- TTL: 1 Hour

---

## ✅ STEP 6: Tell Me You're Done

Once you see the change saved, reply with:

**"DNS record updated"**

I will then:
1. Configure Azure to accept www.bultoo.com
2. Setup free SSL certificate
3. Test the deployment

---

## ⏱️ How Long Does It Take?

- **You edit the record**: 2 minutes
- **DNS propagation**: 5-10 minutes
- **Azure configuration**: 2 minutes (I'll do this)
- **Total time**: ~15 minutes

Then **www.bultoo.com** will show your Boloo app!

---

## 📸 Screenshot

If you get stuck, take a screenshot and share it. I'll guide you through exactly where to click!

---

## Current App URLs (Both Work Now)

- ✅ **Azure URL**: https://lemon-coast-0f65c5710.3.azurestaticapps.net
- ⏳ **Your Domain** (after DNS setup): https://www.bultoo.com

Same app, two URLs!
