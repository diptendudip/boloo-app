# GoDaddy DNS Setup for bultoo.com

## Complete Step-by-Step Instructions

### Step 1: Login to GoDaddy

1. Go to https://www.godaddy.com
2. Click "Sign In" (top right)
3. Enter your GoDaddy username and password
4. Click "Sign In"

### Step 2: Access DNS Management

1. After login, click your profile icon (top right)
2. Click "My Products"
3. Find "bultoo.com" in your domains list
4. Click the three dots (...) or "DNS" button next to bultoo.com
5. Click "Manage DNS"

### Step 3: Add CNAME Record for www.bultoo.com

1. Scroll down to the "Records" section
2. Click "Add" or "Add New Record" button
3. Fill in these exact values:

   ```
   Type: CNAME
   Name: www
   Value: lemon-coast-0f65c5710.3.azurestaticapps.net
   TTL: 1 Hour (or 3600 seconds)
   ```

4. Click "Save" or "Add Record"

### Step 4: Wait for DNS Propagation

- **Time needed**: 5-30 minutes (usually 5-10 minutes)
- **Check status**: Open https://dnschecker.org
  - Enter: www.bultoo.com
  - Type: CNAME
  - Click "Search"
  - Wait until it shows the Azure domain

### Step 5: Notify Me

After you complete Step 3 and save the CNAME record, tell me:
**"DNS record added"**

I will then:
1. Configure Azure to accept www.bultoo.com
2. Setup SSL certificate (automatic, free)
3. Test the deployment

---

## Alternative: Use apex domain (bultoo.com without www)

If you prefer **bultoo.com** instead of **www.bultoo.com**:

### Option A: If GoDaddy supports ALIAS/ANAME records

1. In DNS Management, click "Add"
2. Fill in:
   ```
   Type: ALIAS (or ANAME)
   Name: @ (or leave blank)
   Value: lemon-coast-0f65c5710.3.azurestaticapps.net
   TTL: 1 Hour
   ```
3. Save

### Option B: If GoDaddy only has A records (most common)

1. First, we need to get the IP address
2. Run this command (I'll help):
   ```bash
   nslookup lemon-coast-0f65c5710.3.azurestaticapps.net
   ```
3. Then add A record with that IP

---

## Which Should You Choose?

**Recommended: www.bultoo.com**
- ✅ Easier setup (just one CNAME record)
- ✅ Works immediately
- ✅ Standard practice for web apps
- ❌ Has "www" in URL

**Alternative: bultoo.com**
- ✅ Shorter, cleaner URL
- ✅ No "www"
- ❌ Slightly more complex setup
- ❌ May require IP address (which can change)

---

## Current Status

**Mobile Web App:**
- Working URL: https://lemon-coast-0f65c5710.3.azurestaticapps.net
- All features functional:
  - 35 states in dropdown ✅
  - 33 districts for Chhattisgarh ✅
  - Blocks and panchayats working ✅
  - Cases and chat functional ✅

**What Happens After DNS Setup:**
- Your domain → Mobile web app
- Same features, new URL
- Free SSL certificate added automatically
- Ready to share with friends

---

## Need Help?

**Take a screenshot of:**
1. Your GoDaddy DNS Management page (after adding the record)
2. Any error messages

And share it with me!
