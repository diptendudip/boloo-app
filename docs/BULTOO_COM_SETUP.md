# Bultoo.com Domain Configuration

## Current Status
- Mobile Web App: https://lemon-coast-0f65c5710.3.azurestaticapps.net
- Target Domain: bultoo.com

## DNS Configuration Required

### Step 1: Configure DNS Records

Go to your domain registrar (where you bought bultoo.com) and add these DNS records:

#### Option A: Use www.bultoo.com (Recommended)
```
Type: CNAME
Name: www
Value: lemon-coast-0f65c5710.3.azurestaticapps.net
TTL: 3600
```

#### Option B: Use bultoo.com (root domain)
```
Type: TXT
Name: @ (or leave blank for apex/root domain)
Value: [VALIDATION_TOKEN - to be generated]
TTL: 3600

Type: ALIAS or ANAME (if supported) OR A record
Name: @ (or leave blank)
Value: lemon-coast-0f65c5710.3.azurestaticapps.net (or get IP address)
TTL: 3600
```

### Step 2: After DNS is configured

Run this command to add the custom domain:

```bash
# For www.bultoo.com
az staticwebapp hostname set \
  --name boloo-mobile-web \
  --resource-group boloo-production-rg \
  --hostname www.bultoo.com

# For bultoo.com (apex)
az staticwebapp hostname set \
  --name boloo-mobile-web \
  --resource-group boloo-production-rg \
  --hostname bultoo.com \
  --validation-method dns-txt-token
```

### Step 3: Verify

After DNS propagates (5-30 minutes):
- https://www.bultoo.com → Mobile web app
- OR https://bultoo.com → Mobile web app

## Quick Start (Recommended Path)

**Use www.bultoo.com** - it's simpler and works immediately:

1. Add CNAME record: www → lemon-coast-0f65c5710.3.azurestaticapps.net
2. Wait 5 minutes for DNS propagation
3. Run: `az staticwebapp hostname set --name boloo-mobile-web --resource-group boloo-production-rg --hostname www.bultoo.com`
4. Test: https://www.bultoo.com

## Alternative: Use Backend Domain

You already own boloo-backend-api.azurewebsites.net. You can:

1. Add custom domain to App Service
2. Serve mobile web from /mobile path
3. Use app.bultoo.com or similar

Which approach do you prefer?
