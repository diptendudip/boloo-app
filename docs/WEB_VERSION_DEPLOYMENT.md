# Boloo Web Version Deployment Guide

## Overview

The Boloo web application is deployed on **Azure Static Web Apps**, providing a high-performance, globally distributed admin interface for the Boloo platform. This guide covers deployment, configuration, and usage of the web version.

## Current Deployment Status

### Azure Resources
- **Resource Group**: `boloo-production-rg`
- **Static Web App**: `boloo-web-admin`
- **SKU**: Free Tier
- **Location**: East US 2
- **Live URL**: https://orange-sand-00170940f.3.azurestaticapps.net
- **Backend API**: https://boloo-backend-api.azurewebsites.net

### Technology Stack
- **Framework**: Next.js 14.0.4
- **Runtime**: Node.js 18
- **Build Mode**: Static Export (SSG)
- **UI Library**: React 18.2.0
- **Styling**: Tailwind CSS 3.3.6
- **Charts**: Recharts 2.10.3
- **HTTP Client**: Axios 1.6.2 + SWR 2.2.4

## Web App Features

### Available Pages
1. **Dashboard** (`/`) - Main overview with analytics
2. **Cases** (`/cases`) - Case management interface
3. **Entities** (`/entities`) - Entity tracking and management
4. **Taxonomies** (`/taxonomies`) - Taxonomy configuration
5. **Users** (`/users`) - User management
6. **Monitoring** (`/monitoring`) - System monitoring and health
7. **Analytics** (`/analytics`) - Advanced analytics and reporting
8. **Settings** (`/settings`) - Application settings

### Build Statistics
- **Total Routes**: 11 pages
- **Bundle Size**: ~110 KB first load JS
- **Optimization**: Static generation, tree-shaking, minification
- **Performance**: Fully optimized for CDN delivery

## Local Development

### Prerequisites
```bash
# Required
- Node.js 18.x or higher
- npm 9.x or higher

# Optional
- Git (for version control)
- Azure CLI (for deployment)
```

### Setup Instructions

1. **Navigate to Web Directory**
   ```bash
   cd web/
   ```

2. **Install Dependencies**
   ```bash
   npm install
   # or
   npm ci  # for clean install
   ```

3. **Configure Environment Variables**
   ```bash
   # Copy example environment file
   cp .env.example .env.local

   # Edit .env.local with your settings
   NEXT_PUBLIC_API_URL=https://boloo-backend-api.azurewebsites.net
   ```

4. **Run Development Server**
   ```bash
   npm run dev
   ```
   - Access at: http://localhost:3000
   - Hot reload enabled
   - Fast refresh for React components

5. **Run Linting**
   ```bash
   npm run lint
   ```

6. **Type Checking**
   ```bash
   npx tsc --noEmit
   ```

## Production Build

### Build Process

1. **Create Production Build**
   ```bash
   cd web/
   npm run build
   ```

2. **Build Output**
   - Output directory: `web/out/`
   - Static HTML, CSS, JS files
   - Optimized assets with compression
   - Source maps (excluded in production)

3. **Verify Build**
   ```bash
   # Check build size
   du -sh out/

   # List generated pages
   ls -la out/
   ```

4. **Local Preview**
   ```bash
   npm run start
   # Note: For static export, use a static server
   npx serve out/
   ```

## Azure Deployment

### Automatic Deployment (GitHub Actions)

The web app deploys automatically via GitHub Actions when changes are pushed to the `main` branch.

#### Workflow File
`.github/workflows/deploy-web.yml`

#### Trigger Conditions
- Push to `main` branch with changes in `web/` directory
- Pull request to `main` branch with changes in `web/` directory
- Manual workflow dispatch

#### Deployment Steps
1. Checkout code
2. Setup Node.js 18
3. Install dependencies (`npm ci`)
4. Run linting (continues on error)
5. Run type checking (continues on error)
6. Run tests (continues on error)
7. Create production environment file
8. Build Next.js application
9. Optimize assets (remove source maps, create gzip)
10. Deploy to Azure Static Web Apps
11. Add custom headers and routing config
12. Upload deployment artifacts
13. Run Lighthouse performance audit

### Manual Deployment

#### Using Azure CLI

1. **Install Azure CLI**
   ```bash
   # macOS
   brew install azure-cli

   # Windows
   winget install Microsoft.AzureCLI
   ```

2. **Login to Azure**
   ```bash
   az login
   ```

3. **Get Deployment Token**
   ```bash
   az staticwebapp secrets list \
     --resource-group boloo-production-rg \
     --name boloo-web-admin \
     --query "properties.apiKey" -o tsv
   ```

4. **Deploy Using SWA CLI**
   ```bash
   # Install SWA CLI
   npm install -g @azure/static-web-apps-cli

   # Deploy
   swa deploy \
     --app-location web/out \
     --deployment-token <YOUR_DEPLOYMENT_TOKEN>
   ```

#### Using GitHub Actions Manual Trigger

1. Go to GitHub repository
2. Navigate to Actions tab
3. Select "Deploy Web to Azure Static Web Apps"
4. Click "Run workflow"
5. Select branch and click "Run workflow"

## Configuration

### Environment Variables

#### Required Variables (GitHub Secrets)
```bash
AZURE_STATIC_WEB_APPS_API_TOKEN  # Azure deployment token
NEXT_PUBLIC_API_URL               # Backend API URL
```

#### Optional Variables
```bash
SLACK_WEBHOOK_URL                 # For deployment notifications
WEB_APP_URL                       # For Lighthouse audits
```

### Static Web App Configuration

File: `web/staticwebapp.config.json`

```json
{
  "routes": [
    {
      "route": "/*",
      "allowedRoles": ["anonymous"]
    }
  ],
  "navigationFallback": {
    "rewrite": "/404.html",
    "exclude": ["/_next/*", "/static/*", "/*.{css,scss,js,png,gif,ico,jpg,svg}"]
  },
  "responseOverrides": {
    "404": {
      "rewrite": "/404.html",
      "statusCode": 404
    }
  },
  "globalHeaders": {
    "cache-control": "public, max-age=31536000, immutable"
  }
}
```

### Next.js Configuration

File: `web/next.config.js`

Key settings:
- **Output**: Static export for Azure Static Web Apps
- **Images**: Unoptimized for static hosting
- **Trailing Slashes**: Enabled for better CDN caching
- **Minification**: SWC minifier for faster builds
- **Compression**: Enabled
- **Security Headers**: HSTS, XSS protection, content type options

## Web vs Mobile Comparison

### Web Version Features
- Full admin interface
- Desktop-optimized layouts
- Advanced analytics and reporting
- Multi-tab navigation
- Keyboard shortcuts support
- Large screen optimization
- No installation required
- Instant updates

### Mobile Version Features
- Native iOS app
- Touch-optimized interface
- Offline capabilities
- Push notifications
- Camera integration
- Biometric authentication
- App Store distribution
- Native performance

### Feature Parity

| Feature | Web | Mobile |
|---------|-----|--------|
| Dashboard | ✅ | ✅ |
| Case Management | ✅ | ✅ |
| Entity Tracking | ✅ | ✅ |
| User Management | ✅ | ✅ |
| Analytics | ✅ | Limited |
| Settings | ✅ | ✅ |
| Monitoring | ✅ | ❌ |
| Taxonomies | ✅ | ❌ |
| Offline Mode | ❌ | ✅ |
| Push Notifications | ❌ | ✅ |

## Performance Optimization

### Build Optimizations
- **Static Generation**: All pages pre-rendered at build time
- **Tree Shaking**: Unused code eliminated
- **Code Splitting**: Automatic chunk splitting
- **Minification**: SWC-based minification
- **Compression**: Gzip compression for text assets
- **Image Optimization**: Disabled for static export (use CDN)

### Runtime Optimizations
- **CDN Delivery**: Global edge distribution
- **Cache Headers**: Long-term caching (1 year)
- **HTTP/2**: Enabled by default
- **Brotli Compression**: Automatic on Azure
- **Resource Hints**: DNS prefetch enabled

### Performance Metrics (Target)
- **Lighthouse Score**: >90
- **First Contentful Paint**: <1.5s
- **Time to Interactive**: <3.5s
- **Total Bundle Size**: <500KB
- **Initial Load**: <2s

## Monitoring and Analytics

### Azure Static Web Apps Analytics
```bash
# View deployment history
az staticwebapp show \
  --resource-group boloo-production-rg \
  --name boloo-web-admin

# View deployment logs
az staticwebapp deployment list \
  --resource-group boloo-production-rg \
  --name boloo-web-admin
```

### GitHub Actions Metrics
- Build time tracking
- Bundle size monitoring
- Lighthouse performance audits
- Deployment success rate

## Troubleshooting

### Build Failures

**Issue**: Build fails with dependency errors
```bash
# Solution: Clean install
cd web/
rm -rf node_modules package-lock.json
npm install
```

**Issue**: TypeScript errors
```bash
# Solution: Check types
npx tsc --noEmit
# Fix errors in source files
```

### Deployment Issues

**Issue**: Deployment token expired
```bash
# Solution: Regenerate token
az staticwebapp secrets renew \
  --resource-group boloo-production-rg \
  --name boloo-web-admin
```

**Issue**: 404 errors on refresh
- Verify `staticwebapp.config.json` has correct fallback
- Check `navigationFallback.rewrite` points to `/404.html`

### Runtime Issues

**Issue**: API connection fails
- Verify `NEXT_PUBLIC_API_URL` in environment variables
- Check CORS settings on backend API
- Verify backend API is running

**Issue**: Blank page after deployment
- Check browser console for errors
- Verify all assets loaded correctly
- Check network tab for failed requests

## Security

### Implemented Security Features
- **HSTS**: Strict Transport Security enabled
- **XSS Protection**: X-XSS-Protection header
- **Content Type Options**: nosniff enabled
- **Frame Options**: SAMEORIGIN to prevent clickjacking
- **Referrer Policy**: origin-when-cross-origin
- **Permissions Policy**: Camera, microphone, geolocation disabled

### Security Best Practices
1. Never commit secrets to repository
2. Use GitHub Secrets for sensitive data
3. Rotate deployment tokens regularly
4. Enable Azure AD authentication (future)
5. Implement rate limiting on API
6. Use HTTPS only (enforced by Azure)

## Custom Domain Setup (Optional)

### Add Custom Domain

1. **Configure DNS**
   ```bash
   # Add CNAME record
   CNAME: www.yourapp.com -> orange-sand-00170940f.3.azurestaticapps.net
   ```

2. **Add to Azure**
   ```bash
   az staticwebapp hostname set \
     --resource-group boloo-production-rg \
     --name boloo-web-admin \
     --hostname www.yourapp.com
   ```

3. **Verify SSL Certificate**
   - Azure automatically provisions SSL certificate
   - Validation takes 5-10 minutes

## Rollback Procedures

### Rollback to Previous Deployment

1. **Using Azure Portal**
   - Navigate to Static Web App
   - Go to "Deployments" section
   - Select previous deployment
   - Click "Promote"

2. **Using Git**
   ```bash
   # Revert to previous commit
   git revert HEAD
   git push origin main

   # Or rollback to specific commit
   git reset --hard <commit-hash>
   git push -f origin main
   ```

## Maintenance

### Regular Tasks
- Update dependencies monthly
- Review Lighthouse audits weekly
- Monitor bundle size growth
- Check deployment logs
- Review security headers
- Update Node.js version annually

### Dependency Updates
```bash
cd web/

# Check outdated packages
npm outdated

# Update all packages
npm update

# Update specific package
npm install package-name@latest

# Audit security vulnerabilities
npm audit
npm audit fix
```

## Cost Management

### Azure Static Web Apps Free Tier Limits
- **Bandwidth**: 100 GB/month
- **API Requests**: No limit
- **Custom Domains**: 2 domains
- **Staging Environments**: Unlimited
- **Build Minutes**: 50 minutes/month

### Cost Optimization
- Static export reduces compute costs
- CDN caching reduces bandwidth
- Free tier sufficient for most use cases
- Monitor usage in Azure portal

## Support and Resources

### Documentation
- Next.js: https://nextjs.org/docs
- Azure Static Web Apps: https://learn.microsoft.com/azure/static-web-apps
- React: https://react.dev

### Internal Resources
- Backend API Docs: `docs/BACKEND_DEPLOYMENT.md`
- Mobile Deployment: `docs/MOBILE_DEPLOYMENT.md`
- GitHub Workflows: `.github/workflows/`

### Getting Help
1. Check troubleshooting section above
2. Review deployment logs in GitHub Actions
3. Check Azure Static Web Apps logs
4. Contact DevOps team

## Appendix

### Useful Commands

```bash
# Check Azure resource status
az staticwebapp show \
  --resource-group boloo-production-rg \
  --name boloo-web-admin \
  --query "{name:name, defaultHostname:defaultHostname, location:location}"

# List all deployments
az staticwebapp deployment list \
  --resource-group boloo-production-rg \
  --name boloo-web-admin

# View app configuration
az staticwebapp appsettings list \
  --resource-group boloo-production-rg \
  --name boloo-web-admin

# Build locally
cd web/ && npm run build

# Preview build
npx serve out/

# Deploy manually
swa deploy --app-location web/out
```

### Environment Files

**`.env.local`** (Development)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8080
```

**`.env.production`** (Production)
```bash
NEXT_PUBLIC_API_URL=https://boloo-backend-api.azurewebsites.net
```

### GitHub Secrets Required
```
AZURE_STATIC_WEB_APPS_API_TOKEN
NEXT_PUBLIC_API_URL
GITHUB_TOKEN (automatic)
SLACK_WEBHOOK_URL (optional)
WEB_APP_URL (optional)
```

---

**Last Updated**: November 2024
**Version**: 1.0.0
**Maintained By**: Boloo DevOps Team
