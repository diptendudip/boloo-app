# Domain Setup Guide - Connecting GoDaddy to Azure

## Overview
This guide covers connecting your bultoo.com domain from GoDaddy to Azure App Service and setting up SSL certificates.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Azure Custom Domain Configuration](#azure-custom-domain-configuration)
3. [GoDaddy DNS Configuration](#godaddy-dns-configuration)
4. [SSL Certificate Setup](#ssl-certificate-setup)
5. [Subdomain Strategy](#subdomain-strategy)
6. [Verification and Testing](#verification-and-testing)

---

## Prerequisites

- Domain registered at GoDaddy: `bultoo.com`
- Azure App Service deployed: `bultoo-api.azurewebsites.net`
- Azure CLI installed and logged in
- Access to GoDaddy account

---

## Azure Custom Domain Configuration

### 1. Get Azure App Service IP Address

```bash
# Get default hostname
az webapp show \
  --resource-group bultoo-rg \
  --name bultoo-api \
  --query defaultHostName -o tsv
# Output: bultoo-api.azurewebsites.net

# Get outbound IP addresses
az webapp show \
  --resource-group bultoo-rg \
  --name bultoo-api \
  --query outboundIpAddresses -o tsv

# Get possible inbound IP addresses
az webapp show \
  --resource-group bultoo-rg \
  --name bultoo-api \
  --query possibleInboundIpAddresses -o tsv
```

### 2. Get Domain Verification ID

```bash
# Get custom domain verification ID
az webapp show \
  --resource-group bultoo-rg \
  --name bultoo-api \
  --query customDomainVerificationId -o tsv
# Save this value - you'll need it for DNS verification
```

**Example output**: `A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6`

---

## GoDaddy DNS Configuration

### Option A: Using Azure App Service Directly (Recommended for Backend)

#### Step 1: Login to GoDaddy
1. Go to [https://dnsmanagement.godaddy.com](https://dnsmanagement.godaddy.com)
2. Select `bultoo.com`
3. Click "DNS" or "Manage DNS"

#### Step 2: Add DNS Records for API Subdomain

Add the following DNS records:

**For api.bultoo.com (Backend API):**

| Type | Name | Value | TTL |
|------|------|-------|-----|
| CNAME | api | bultoo-api.azurewebsites.net | 600 |
| TXT | asuid.api | `YOUR_VERIFICATION_ID` | 600 |

Replace `YOUR_VERIFICATION_ID` with the value from step 2 above.

#### Step 3: Screenshots of GoDaddy Configuration

**DNS Management Page:**
```
Domain: bultoo.com

DNS Records:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Type     Name        Value                           TTL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
A        @           Parked                          600
CNAME    api         bultoo-api.azurewebsites.net   600
TXT      asuid.api   A1B2C3D4E5F6G7H8...            600
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Option B: Using Root Domain (www.bultoo.com and bultoo.com)

**For root domain and www:**

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | @ | `AZURE_APP_IP_ADDRESS` | 600 |
| CNAME | www | bultoo-api.azurewebsites.net | 600 |
| TXT | asuid | `YOUR_VERIFICATION_ID` | 600 |
| TXT | asuid.www | `YOUR_VERIFICATION_ID` | 600 |

**Note**: Replace `AZURE_APP_IP_ADDRESS` with the IP from Step 1.

---

## Azure Custom Domain Addition

### 1. Add Custom Domain for API (api.bultoo.com)

```bash
# Wait 5-10 minutes after DNS changes for propagation

# Add custom domain
az webapp config hostname add \
  --resource-group bultoo-rg \
  --webapp-name bultoo-api \
  --hostname api.bultoo.com

# Verify domain was added
az webapp config hostname list \
  --resource-group bultoo-rg \
  --webapp-name bultoo-api
```

### 2. Add Root Domain (Optional)

```bash
# Add www subdomain
az webapp config hostname add \
  --resource-group bultoo-rg \
  --webapp-name bultoo-api \
  --hostname www.bultoo.com

# Add apex domain
az webapp config hostname add \
  --resource-group bultoo-rg \
  --webapp-name bultoo-api \
  --hostname bultoo.com
```

---

## SSL Certificate Setup

### Option 1: Free Managed Certificate (Recommended)

```bash
# Create free managed certificate for api.bultoo.com
az webapp config ssl create \
  --resource-group bultoo-rg \
  --name bultoo-api \
  --hostname api.bultoo.com

# Bind the certificate
az webapp config ssl bind \
  --resource-group bultoo-rg \
  --name bultoo-api \
  --certificate-thumbprint auto \
  --ssl-type SNI \
  --hostname api.bultoo.com

# Verify HTTPS
curl -I https://api.bultoo.com/health
```

### Option 2: Let's Encrypt Certificate (Alternative)

If you prefer Let's Encrypt or need certificates for multiple domains:

```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot

# Generate certificate (requires port 80 access)
sudo certbot certonly --manual --preferred-challenges dns -d api.bultoo.com

# Certbot will provide a TXT record to add to GoDaddy
# Add this record in GoDaddy DNS:
# Type: TXT
# Name: _acme-challenge.api
# Value: (provided by certbot)

# Upload certificate to Azure
az webapp config ssl upload \
  --resource-group bultoo-rg \
  --name bultoo-api \
  --certificate-file /etc/letsencrypt/live/api.bultoo.com/fullchain.pem \
  --certificate-password ""

# Get certificate thumbprint
THUMBPRINT=$(az webapp config ssl list \
  --resource-group bultoo-rg \
  --query "[?subjectName=='api.bultoo.com'].thumbprint" -o tsv)

# Bind certificate
az webapp config ssl bind \
  --resource-group bultoo-rg \
  --name bultoo-api \
  --certificate-thumbprint $THUMBPRINT \
  --ssl-type SNI \
  --hostname api.bultoo.com
```

### 3. Enable HTTPS Only

```bash
# Redirect all HTTP traffic to HTTPS
az webapp update \
  --resource-group bultoo-rg \
  --name bultoo-api \
  --https-only true
```

---

## Subdomain Strategy

### Recommended Architecture

```
bultoo.com (or www.bultoo.com)
├─ Marketing website / Landing page
│  └─ Could be static site on Azure Static Web Apps
│
api.bultoo.com
├─ FastAPI backend
│  └─ Azure App Service
│
cdn.bultoo.com (optional)
├─ Azure CDN for media/static assets
│  └─ Points to Azure Blob Storage
│
admin.bultoo.com (future)
└─ Admin dashboard
   └─ React/Next.js on Azure Static Web Apps
```

### DNS Configuration for Full Setup

```bash
# Complete DNS records in GoDaddy
```

**Recommended GoDaddy DNS Records:**

| Type | Name | Value | TTL | Purpose |
|------|------|-------|-----|---------|
| A | @ | `AZURE_STATIC_IP` | 600 | Root domain |
| CNAME | www | bultoo.com | 600 | WWW redirect |
| CNAME | api | bultoo-api.azurewebsites.net | 600 | Backend API |
| CNAME | cdn | bultoo.azureedge.net | 600 | CDN endpoint |
| TXT | asuid | `VERIFICATION_ID` | 600 | Domain verification |
| TXT | asuid.api | `VERIFICATION_ID` | 600 | API verification |
| TXT | asuid.www | `VERIFICATION_ID` | 600 | WWW verification |

---

## Verification and Testing

### 1. DNS Propagation Check

```bash
# Check DNS propagation (may take 24-48 hours globally)
nslookup api.bultoo.com

# Or use online tools:
# https://www.whatsmydns.net/#CNAME/api.bultoo.com
```

### 2. Test Domain Connectivity

```bash
# Test HTTP (should redirect to HTTPS)
curl -I http://api.bultoo.com/health

# Test HTTPS
curl -I https://api.bultoo.com/health

# Expected response:
# HTTP/2 200
# content-type: application/json
# ...
```

### 3. SSL Certificate Validation

```bash
# Check SSL certificate details
openssl s_client -connect api.bultoo.com:443 -servername api.bultoo.com

# Verify certificate chain
curl -vI https://api.bultoo.com 2>&1 | grep -A 10 "SSL certificate"
```

### 4. Verify All Endpoints

```bash
# API health check
curl https://api.bultoo.com/health

# API docs
curl https://api.bultoo.com/docs

# Test CORS
curl -H "Origin: https://bultoo.com" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     https://api.bultoo.com/api/v1/users
```

---

## Update Application Configuration

### 1. Update CORS Settings

```bash
# Update allowed origins to include custom domain
az webapp config appsettings set \
  --resource-group bultoo-rg \
  --name bultoo-api \
  --settings \
    CORS_ORIGINS="https://bultoo.com,https://www.bultoo.com,https://api.bultoo.com"
```

### 2. Update Mobile App Configuration

Update your React Native app's API configuration:

```javascript
// config/api.js or constants.js
export const API_CONFIG = {
  // Before deployment
  // baseURL: 'http://localhost:8000',

  // After domain setup
  baseURL: 'https://api.bultoo.com',

  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
};
```

---

## Domain Redirect Configuration

### Redirect www to non-www (or vice versa)

If you want www.bultoo.com to redirect to bultoo.com:

```bash
# This is typically handled at the web server level
# For Azure App Service, create a web.config file
```

**web.config** (for IIS-based redirects):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <system.webServer>
    <rewrite>
      <rules>
        <rule name="Redirect to non-www" stopProcessing="true">
          <match url="(.*)" />
          <conditions>
            <add input="{HTTP_HOST}" pattern="^www\.bultoo\.com$" />
          </conditions>
          <action type="Redirect" url="https://bultoo.com/{R:1}" redirectType="Permanent" />
        </rule>
      </rules>
    </rewrite>
  </system.webServer>
</configuration>
```

For FastAPI/Python apps, handle redirects in code:

```python
# main.py
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse

app = FastAPI()

@app.middleware("http")
async def redirect_www(request: Request, call_next):
    if request.url.hostname == "www.bultoo.com":
        url = str(request.url).replace("www.bultoo.com", "bultoo.com")
        return RedirectResponse(url=url, status_code=301)
    return await call_next(request)
```

---

## Troubleshooting

### Common Issues

**1. DNS Not Resolving**
```bash
# Check if DNS has propagated
dig api.bultoo.com

# Check from multiple locations
# Use: https://dnschecker.org

# Clear local DNS cache (if testing locally)
sudo dnsmasq -k  # Linux
sudo killall -HUP mDNSResponder  # macOS
ipconfig /flushdns  # Windows
```

**2. SSL Certificate Errors**
```bash
# Check certificate status
az webapp config ssl list \
  --resource-group bultoo-rg

# If certificate creation failed, try manual creation
az webapp config ssl create \
  --resource-group bultoo-rg \
  --name bultoo-api \
  --hostname api.bultoo.com
```

**3. Domain Verification Failed**
```bash
# Verify TXT record is correct
nslookup -type=TXT asuid.api.bultoo.com

# Get verification ID again
az webapp show \
  --resource-group bultoo-rg \
  --name bultoo-api \
  --query customDomainVerificationId -o tsv

# Wait 10-15 minutes and retry
```

**4. 404 Not Found After Domain Setup**
```bash
# Check hostname bindings
az webapp config hostname list \
  --resource-group bultoo-rg \
  --webapp-name bultoo-api

# Restart app service
az webapp restart \
  --resource-group bultoo-rg \
  --name bultoo-api
```

---

## CDN Custom Domain (Optional)

If you're using Azure CDN for static assets:

### 1. Create CNAME in GoDaddy

| Type | Name | Value | TTL |
|------|------|-------|-----|
| CNAME | cdn | bultoo.azureedge.net | 600 |

### 2. Add Custom Domain to CDN

```bash
# Add custom domain to CDN endpoint
az cdn custom-domain create \
  --resource-group bultoo-rg \
  --profile-name bultoo-cdn \
  --endpoint-name bultoo \
  --name cdn-bultoo \
  --hostname cdn.bultoo.com

# Enable HTTPS on CDN
az cdn custom-domain enable-https \
  --resource-group bultoo-rg \
  --profile-name bultoo-cdn \
  --endpoint-name bultoo \
  --name cdn-bultoo
```

---

## Monitoring Domain Health

```bash
# Check domain SSL expiry
echo | openssl s_client -servername api.bultoo.com -connect api.bultoo.com:443 2>/dev/null | openssl x509 -noout -dates

# Set up Azure Monitor alert for SSL expiry
az monitor metrics alert create \
  --name ssl-expiry-alert \
  --resource-group bultoo-rg \
  --scopes /subscriptions/SUBSCRIPTION_ID/resourceGroups/bultoo-rg/providers/Microsoft.Web/sites/bultoo-api \
  --condition "avg HttpResponseTime > 3000" \
  --description "Alert when response time exceeds 3 seconds"
```

---

## Cost Implications

- **Custom Domain**: Free (included with App Service)
- **Managed SSL Certificate**: Free (included with App Service)
- **DNS Management**: Varies by GoDaddy plan (typically included)
- **Custom Domain for CDN**: Free
- **CDN HTTPS**: Free (managed certificate)

---

## Next Steps

1. ✅ Verify DNS propagation (24-48 hours)
2. ✅ Test SSL certificate
3. ✅ Update mobile app configuration
4. ✅ Configure environment variables
5. ✅ Set up monitoring and alerts
6. 📱 Generate APK for testing (see APK_BUILD_GUIDE.md)
7. 🚀 Set up CI/CD pipeline

---

## Useful Links

- [Azure Custom Domain Documentation](https://docs.microsoft.com/azure/app-service/app-service-web-tutorial-custom-domain)
- [GoDaddy DNS Management](https://www.godaddy.com/help/manage-dns-zone-files-680)
- [DNS Propagation Checker](https://www.whatsmydns.net)
- [SSL Certificate Checker](https://www.sslshopper.com/ssl-checker.html)
