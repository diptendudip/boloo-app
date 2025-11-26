# Domain Configuration Guide

## Overview

This guide covers the complete setup of custom domains for the Boloo application, including DNS configuration, Azure custom domain setup, and SSL certificate management.

## Table of Contents

1. [Domain Architecture](#domain-architecture)
2. [DNS Configuration](#dns-configuration)
3. [Azure Custom Domain Setup](#azure-custom-domain-setup)
4. [SSL Certificate Configuration](#ssl-certificate-configuration)
5. [Domain Registrar Instructions](#domain-registrar-instructions)
6. [Verification and Testing](#verification-and-testing)
7. [Troubleshooting](#troubleshooting)

---

## Domain Architecture

### Primary Domain Structure

```
bultoo.com (root domain)
├── api.bultoo.com          → Backend API (Azure App Service)
├── admin.bultoo.com        → Web Admin Portal (Azure Static Web App)
├── www.bultoo.com          → Marketing/Landing Page (Optional)
└── cdn.bultoo.com          → CDN/Static Assets (Optional)
```

### Mobile App Configuration
- **Android**: `https://api.bultoo.com`
- **iOS**: `https://api.bultoo.com`

---

## DNS Configuration

### Required DNS Records

#### 1. Backend API (api.bultoo.com)

**Option A: CNAME Record (Recommended)**
```
Type:    CNAME
Name:    api
Value:   boloo-backend-api.azurewebsites.net
TTL:     3600
```

**Option B: A Record**
```
Type:    A
Name:    api
Value:   <Azure App Service IP>
TTL:     3600
```

#### 2. Admin Portal (admin.bultoo.com)

```
Type:    CNAME
Name:    admin
Value:   <static-web-app-name>.azurestaticapps.net
TTL:     3600
```

#### 3. Domain Verification (TXT Record)

```
Type:    TXT
Name:    asuid.api
Value:   <Azure verification code>
TTL:     3600
```

#### 4. Root Domain (Optional)

```
Type:    A
Name:    @
Value:   <Azure Static Web App IP>
TTL:     3600
```

### DNS Propagation

- **Expected Time**: 5 minutes to 48 hours
- **Typical Time**: 1-4 hours
- **Check Status**: Use `dig` or `nslookup` commands

---

## Azure Custom Domain Setup

### Prerequisites

1. **Azure Subscription**: Active subscription with appropriate permissions
2. **Domain Ownership**: Registered domain (bultoo.com)
3. **Azure CLI**: Installed and configured

### Step 1: Backend API Domain Setup

#### Using Azure Portal

1. Navigate to App Service → **boloo-backend-api**
2. Select **Custom domains** from left menu
3. Click **+ Add custom domain**
4. Enter domain: `api.bultoo.com`
5. Select **CNAME** validation type
6. Copy the verification TXT record
7. Add TXT record to DNS:
   ```
   Name: asuid.api
   Value: <verification-code>
   ```
8. Wait for DNS propagation (check with `nslookup`)
9. Click **Validate** in Azure Portal
10. Click **Add** to complete setup

#### Using Azure CLI

```bash
# Get verification code
az webapp show \
  --name boloo-backend-api \
  --resource-group boloo-rg \
  --query customDomainVerificationId \
  --output tsv

# Add custom domain
az webapp config hostname add \
  --webapp-name boloo-backend-api \
  --resource-group boloo-rg \
  --hostname api.bultoo.com

# Verify domain
az webapp config hostname list \
  --webapp-name boloo-backend-api \
  --resource-group boloo-rg
```

### Step 2: Admin Portal Domain Setup

#### For Azure Static Web Apps

```bash
# Add custom domain
az staticwebapp hostname set \
  --name boloo-admin-portal \
  --resource-group boloo-rg \
  --hostname admin.bultoo.com

# Verify setup
az staticwebapp hostname show \
  --name boloo-admin-portal \
  --resource-group boloo-rg \
  --hostname admin.bultoo.com
```

#### DNS Configuration for Static Web Apps

Add CNAME record:
```
Type:    CNAME
Name:    admin
Value:   <static-web-app-default-hostname>
TTL:     3600
```

### Step 3: Domain Binding Verification

```bash
# Test DNS resolution
nslookup api.bultoo.com
nslookup admin.bultoo.com

# Test HTTP response
curl -I https://api.bultoo.com/health
curl -I https://admin.bultoo.com
```

---

## SSL Certificate Configuration

### Azure Managed SSL Certificates (Free)

#### Enable for App Service

1. **Prerequisites**:
   - Custom domain added and verified
   - App Service plan: Basic (B1) or higher
   - Domain properly configured in DNS

2. **Enable Managed Certificate**:

```bash
# Create managed certificate
az webapp config ssl create \
  --name boloo-backend-api \
  --resource-group boloo-rg \
  --hostname api.bultoo.com

# Bind certificate
az webapp config ssl bind \
  --name boloo-backend-api \
  --resource-group boloo-rg \
  --certificate-thumbprint <thumbprint> \
  --ssl-type SNI
```

3. **Portal Method**:
   - Navigate to App Service → **TLS/SSL settings**
   - Select **Private Key Certificates (.pfx)**
   - Click **+ Create App Service Managed Certificate**
   - Select custom domain: `api.bultoo.com`
   - Click **Create**
   - Navigate to **Bindings** tab
   - Click **+ Add TLS/SSL Binding**
   - Select domain and certificate
   - Choose **SNI SSL**

#### Enable for Static Web Apps

Azure Static Web Apps automatically provision SSL certificates for custom domains:

1. Add custom domain (as shown in Step 2)
2. Certificate is auto-provisioned within 24 hours
3. Verify SSL:
   ```bash
   curl -vI https://admin.bultoo.com 2>&1 | grep -i ssl
   ```

### SSL Certificate Auto-Renewal

- **Azure Managed Certificates**: Auto-renewed 45 days before expiration
- **No action required**: Azure handles renewal automatically
- **Monitoring**: Set up alerts for certificate expiration

### Force HTTPS Redirect

#### App Service Configuration

```bash
# Enable HTTPS only
az webapp update \
  --name boloo-backend-api \
  --resource-group boloo-rg \
  --https-only true
```

#### Verify HTTPS Enforcement

```bash
# Should redirect to HTTPS
curl -I http://api.bultoo.com

# Should return 200 OK
curl -I https://api.bultoo.com
```

---

## Domain Registrar Instructions

### GoDaddy

1. **Login**: Go to GoDaddy.com → My Products
2. **DNS Management**: Select domain → DNS Management
3. **Add Records**:

   **CNAME for API**:
   ```
   Type:     CNAME
   Name:     api
   Value:    boloo-backend-api.azurewebsites.net
   TTL:      1 Hour
   ```

   **CNAME for Admin**:
   ```
   Type:     CNAME
   Name:     admin
   Value:    <static-web-app-hostname>
   TTL:      1 Hour
   ```

   **TXT Verification**:
   ```
   Type:     TXT
   Name:     asuid.api
   Value:    <azure-verification-code>
   TTL:      1 Hour
   ```

4. **Save**: Click "Save" for each record
5. **Wait**: Propagation typically takes 10-30 minutes

### Namecheap

1. **Login**: Namecheap.com → Domain List
2. **Manage**: Click "Manage" next to domain
3. **Advanced DNS**: Select "Advanced DNS" tab
4. **Add Records**:

   ```
   Host:    api
   Type:    CNAME Record
   Value:   boloo-backend-api.azurewebsites.net
   TTL:     Automatic
   ```

   ```
   Host:    admin
   Type:    CNAME Record
   Value:   <static-web-app-hostname>
   TTL:     Automatic
   ```

   ```
   Host:    asuid.api
   Type:    TXT Record
   Value:   <azure-verification-code>
   TTL:     Automatic
   ```

5. **Save**: Click green checkmark for each record

### Google Domains

1. **Login**: domains.google.com
2. **Select Domain**: Click on bultoo.com
3. **DNS**: Navigate to DNS section
4. **Custom Records**:

   ```
   Name:    api
   Type:    CNAME
   TTL:     3600
   Data:    boloo-backend-api.azurewebsites.net
   ```

   ```
   Name:    admin
   Type:    CNAME
   TTL:     3600
   Data:    <static-web-app-hostname>
   ```

   ```
   Name:    asuid.api
   Type:    TXT
   TTL:     3600
   Data:    <azure-verification-code>
   ```

5. **Add**: Click "Add" for each record

### Cloudflare

1. **Login**: cloudflare.com → Select domain
2. **DNS**: Click "DNS" tab
3. **Add Record**:

   ```
   Type:      CNAME
   Name:      api
   Target:    boloo-backend-api.azurewebsites.net
   Proxy:     DNS only (gray cloud)
   TTL:       Auto
   ```

   ```
   Type:      CNAME
   Name:      admin
   Target:    <static-web-app-hostname>
   Proxy:     DNS only (gray cloud)
   TTL:       Auto
   ```

   **Important**: Disable Cloudflare proxy (gray cloud) for Azure verification

4. **SSL/TLS Settings**:
   - Set SSL/TLS encryption mode to "Full" or "Full (strict)"
   - Enable "Always Use HTTPS"

---

## Verification and Testing

### DNS Verification

#### Check DNS Propagation

```bash
# Check CNAME records
dig api.bultoo.com CNAME +short
dig admin.bultoo.com CNAME +short

# Check from different DNS servers
nslookup api.bultoo.com 8.8.8.8
nslookup api.bultoo.com 1.1.1.1

# Online tools
# - https://dnschecker.org
# - https://www.whatsmydns.net
```

#### Verify TXT Records

```bash
dig asuid.api.bultoo.com TXT +short
```

### SSL Certificate Verification

```bash
# Check SSL certificate
openssl s_client -connect api.bultoo.com:443 -servername api.bultoo.com

# Check certificate expiration
echo | openssl s_client -servername api.bultoo.com -connect api.bultoo.com:443 2>/dev/null | openssl x509 -noout -dates

# Online SSL checker
# - https://www.ssllabs.com/ssltest/
```

### Application Testing

```bash
# Test API health endpoint
curl https://api.bultoo.com/health

# Test admin portal
curl -I https://admin.bultoo.com

# Test HTTPS redirect
curl -I http://api.bultoo.com
# Should return 301 or 308 redirect

# Test from mobile app configuration
curl -H "User-Agent: BolooMobileApp/1.0" https://api.bultoo.com/api/v1/status
```

### Performance Testing

```bash
# Test response time
time curl -I https://api.bultoo.com/health

# Test from different locations
# Use https://tools.pingdom.com
# Use https://www.webpagetest.org
```

---

## Troubleshooting

### Common Issues

#### 1. DNS Not Resolving

**Symptoms**:
- Domain doesn't resolve
- "Server not found" errors

**Solutions**:
```bash
# Clear local DNS cache (macOS)
sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder

# Clear local DNS cache (Windows)
ipconfig /flushdns

# Clear local DNS cache (Linux)
sudo systemd-resolve --flush-caches

# Check DNS propagation status
dig api.bultoo.com +trace
```

#### 2. SSL Certificate Issues

**Symptoms**:
- Certificate warnings
- "Not secure" messages
- Certificate mismatch errors

**Solutions**:
```bash
# Verify certificate matches domain
openssl s_client -connect api.bultoo.com:443 -servername api.bultoo.com | openssl x509 -noout -text | grep DNS

# Check certificate chain
curl -vI https://api.bultoo.com 2>&1 | grep -i certificate

# Force certificate refresh in Azure
az webapp config ssl create \
  --name boloo-backend-api \
  --resource-group boloo-rg \
  --hostname api.bultoo.com
```

#### 3. Domain Verification Failed

**Symptoms**:
- Azure cannot verify domain ownership
- Verification pending for > 24 hours

**Solutions**:
1. Verify TXT record is correctly added:
   ```bash
   dig asuid.api.bultoo.com TXT +short
   ```
2. Wait for DNS propagation (up to 48 hours)
3. Remove and re-add custom domain in Azure
4. Check for conflicting DNS records

#### 4. 404 Not Found After Domain Setup

**Symptoms**:
- Domain resolves but returns 404
- App works on azurewebsites.net but not custom domain

**Solutions**:
1. Verify app is running:
   ```bash
   curl https://boloo-backend-api.azurewebsites.net/health
   ```
2. Check hostname bindings:
   ```bash
   az webapp config hostname list \
     --webapp-name boloo-backend-api \
     --resource-group boloo-rg
   ```
3. Restart app service:
   ```bash
   az webapp restart \
     --name boloo-backend-api \
     --resource-group boloo-rg
   ```

#### 5. Slow DNS Resolution

**Solutions**:
1. Reduce TTL during initial setup (300 seconds)
2. Use CNAME instead of A records
3. Consider using Azure Traffic Manager for geo-routing
4. Enable CDN for static content

### Support Resources

- **Azure Support**: https://portal.azure.com → Support + troubleshooting
- **DNS Checker**: https://dnschecker.org
- **SSL Checker**: https://www.ssllabs.com/ssltest/
- **Azure Documentation**: https://docs.microsoft.com/azure/app-service/app-service-web-tutorial-custom-domain

---

## Best Practices

### Security

1. **Always enforce HTTPS**: Never serve content over HTTP
2. **Use SNI SSL**: More cost-effective and scalable
3. **Enable HSTS**: Add HTTP Strict Transport Security headers
4. **Monitor certificates**: Set up expiration alerts
5. **Use CAA records**: Control which CAs can issue certificates

### Performance

1. **Use CDN**: For static assets (admin portal, images)
2. **Enable caching**: Configure appropriate cache headers
3. **Minimize DNS lookups**: Use fewer subdomains
4. **Optimize TTL**: Balance between flexibility and performance
5. **Geographic distribution**: Use Azure Traffic Manager if needed

### Maintenance

1. **Document changes**: Keep DNS record inventory
2. **Test before production**: Use staging domains
3. **Monitor uptime**: Set up availability tests
4. **Regular audits**: Review DNS and SSL configurations
5. **Backup configurations**: Export DNS records

### Cost Optimization

1. **Use managed certificates**: Free with App Service Basic+
2. **Consolidate domains**: Minimize custom domain count
3. **Review unused domains**: Remove stale configurations
4. **Monitor bandwidth**: Track domain-specific traffic

---

## Migration Checklist

### Pre-Migration

- [ ] Purchase/register domain (bultoo.com)
- [ ] Verify domain ownership
- [ ] Document current DNS records
- [ ] Plan subdomain structure
- [ ] Review App Service plan tier (Basic or higher)

### During Migration

- [ ] Add DNS records (low TTL initially)
- [ ] Configure Azure custom domains
- [ ] Enable SSL certificates
- [ ] Test HTTPS enforcement
- [ ] Verify mobile app connectivity
- [ ] Test admin portal access

### Post-Migration

- [ ] Monitor application logs
- [ ] Verify SSL certificate validity
- [ ] Increase DNS TTL to normal values
- [ ] Update documentation
- [ ] Configure monitoring alerts
- [ ] Remove old domain references

---

## Next Steps

1. Review [Cloud Architecture](./CLOUD_ARCHITECTURE.md) for infrastructure overview
2. Check [Production Deployment Checklist](./PRODUCTION_DEPLOYMENT_CHECKLIST.md) for launch readiness
3. Configure [Environment Setup](./ENVIRONMENT_SETUP.md) for proper environment management

