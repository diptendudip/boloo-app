# Boloo Web App - Quick Reference Guide

## 🚀 Quick Access

**Production URL**: https://orange-sand-00170940f.3.azurestaticapps.net
**Backend API**: https://boloo-backend-api.azurewebsites.net
**Resource Group**: boloo-production-rg
**Status**: ✅ OPERATIONAL

---

## 📋 Essential Commands

### Local Development
```bash
# Navigate to web directory
cd web/

# Install dependencies
npm install

# Start dev server
npm run dev
# → http://localhost:3000

# Build for production
npm run build

# Run linting
npm run lint

# Type checking
npx tsc --noEmit

# Preview production build
npx serve out/
```

### Azure CLI Commands
```bash
# Check deployment status
az staticwebapp show \
  --resource-group boloo-production-rg \
  --name boloo-web-admin

# List deployments
az staticwebapp deployment list \
  --resource-group boloo-production-rg \
  --name boloo-web-admin

# Get deployment token
az staticwebapp secrets list \
  --resource-group boloo-production-rg \
  --name boloo-web-admin \
  --query "properties.apiKey" -o tsv
```

### GitHub Actions
```bash
# Trigger manual deployment
# 1. Go to GitHub Actions tab
# 2. Select "Deploy Web to Azure Static Web Apps"
# 3. Click "Run workflow"
# 4. Select branch → Run
```

---

## 📁 Project Structure

```
web/
├── app/                    # Next.js App Router
│   ├── page.tsx           # Dashboard (/)
│   ├── cases/             # Cases page
│   ├── entities/          # Entities page
│   ├── taxonomies/        # Taxonomies page
│   ├── users/             # Users page
│   ├── monitoring/        # Monitoring page
│   ├── analytics/         # Analytics page
│   └── settings/          # Settings page
├── components/            # Reusable components
├── lib/                   # Utility functions
├── public/               # Static assets
├── .env.local            # Local environment variables
├── .env.production       # Production environment variables
├── next.config.js        # Next.js configuration
├── package.json          # Dependencies
├── tailwind.config.js    # Tailwind CSS config
└── tsconfig.json         # TypeScript config
```

---

## 🔧 Configuration Files

### Environment Variables

**`.env.local`** (Development)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8080
```

**`.env.production`** (Production)
```bash
NEXT_PUBLIC_API_URL=https://boloo-backend-api.azurewebsites.net
```

### Static Web App Config

**`staticwebapp.config.json`**
- Routing rules
- Fallback handling
- Global headers
- MIME types
- API runtime settings

### Next.js Config

**`next.config.js`**
- Static export enabled
- Security headers
- Image optimization disabled (for static)
- Compression enabled
- SWC minification

---

## 🔑 GitHub Secrets Required

```
AZURE_STATIC_WEB_APPS_API_TOKEN    # Azure deployment token
NEXT_PUBLIC_API_URL                 # Backend API URL
GITHUB_TOKEN                        # Auto-provided
SLACK_WEBHOOK_URL                   # Optional: notifications
WEB_APP_URL                         # Optional: for Lighthouse
```

---

## 🌐 Available Pages

| Route | Description | Key Features |
|-------|-------------|--------------|
| `/` | Dashboard | Overview, metrics, quick actions |
| `/cases` | Cases | List, create, edit, filter cases |
| `/entities` | Entities | Entity management, relationships |
| `/taxonomies` | Taxonomies | Category and tag management |
| `/users` | Users | User directory, roles, permissions |
| `/monitoring` | Monitoring | System health, logs, metrics |
| `/analytics` | Analytics | Reports, charts, insights |
| `/settings` | Settings | Profile, preferences, config |
| `/404` | Not Found | Custom 404 page |

---

## ⌨️ Keyboard Shortcuts

### Global
- `?` - Show help
- `/` - Focus search
- `Esc` - Close dialogs
- `Ctrl/Cmd + K` - Command palette

### Navigation
- `G + D` - Dashboard
- `G + C` - Cases
- `G + E` - Entities
- `G + U` - Users
- `G + M` - Monitoring
- `G + A` - Analytics

### Actions
- `N` - New item
- `E` - Edit selected
- `Del` - Delete selected
- `Ctrl/Cmd + S` - Save
- `Ctrl/Cmd + Enter` - Submit

---

## 🔍 Troubleshooting

### Build Issues

**Problem**: `npm install` fails
```bash
# Solution
rm -rf node_modules package-lock.json
npm install
```

**Problem**: TypeScript errors
```bash
# Solution
npx tsc --noEmit
# Fix errors in source files
```

**Problem**: Build fails
```bash
# Solution
npm run build
# Check error messages
# Verify all dependencies installed
```

### Deployment Issues

**Problem**: GitHub Actions fails
```bash
# Check workflow logs
# Verify GitHub Secrets set
# Ensure web/ changes committed
# Re-run workflow
```

**Problem**: Site shows 404
```bash
# Verify staticwebapp.config.json
# Check deployment logs in Azure
# Clear browser cache
# Verify correct URL
```

**Problem**: API calls fail
```bash
# Check NEXT_PUBLIC_API_URL
# Verify backend is running
# Check CORS settings
# Test API directly
```

### Runtime Issues

**Problem**: Blank page
```bash
# Check browser console
# Verify JavaScript enabled
# Clear cache and cookies
# Try incognito mode
```

**Problem**: Slow loading
```bash
# Check internet connection
# Verify CDN status
# Clear browser cache
# Test from different location
```

---

## 🛡️ Security Headers

Applied automatically on all responses:

- `Strict-Transport-Security` - Force HTTPS
- `X-Frame-Options` - Prevent clickjacking
- `X-Content-Type-Options` - Prevent MIME sniffing
- `X-XSS-Protection` - XSS protection
- `Referrer-Policy` - Control referrer
- `Permissions-Policy` - Disable unnecessary features
- `Cache-Control` - Long-term caching

---

## 📊 Performance Targets

| Metric | Target | Actual |
|--------|--------|--------|
| Lighthouse Score | >90 | ~95 |
| First Load JS | <200 KB | ~110 KB ✅ |
| Total Bundle | <2 MB | 1.2 MB ✅ |
| TTFB | <200ms | ~50ms ✅ |
| FCP | <1.5s | ~1s ✅ |
| TTI | <3.5s | ~2s ✅ |

---

## 🔄 Deployment Workflow

### Automatic Deployment

```mermaid
Push to main → GitHub Actions → Build → Deploy → Live
    ↓                  ↓           ↓        ↓       ↓
  Trigger          Quality     Export    Azure    URL
                   Checks      Static   Upload  Update
```

### Manual Deployment

1. Make changes in `web/` directory
2. Test locally: `npm run dev`
3. Build: `npm run build`
4. Verify build in `out/` directory
5. Commit and push to `main` branch
6. GitHub Actions auto-deploys
7. Verify at production URL

---

## 📦 Build Output

**Generated Files**
```
out/
├── index.html              # Homepage
├── 404.html               # Not found page
├── _next/                 # Next.js bundles
│   ├── static/           # Static assets
│   └── ...
├── analytics/            # Analytics page
├── cases/               # Cases page
├── entities/            # Entities page
├── monitoring/          # Monitoring page
├── settings/            # Settings page
├── taxonomies/          # Taxonomies page
└── users/               # Users page
```

**Build Stats**
- Total Size: ~1.2 MB
- Pages: 11 routes
- First Load JS: ~110 KB
- Shared JS: ~82 KB

---

## 🚨 Emergency Procedures

### Rollback Deployment

**Method 1: GitHub**
```bash
git revert HEAD
git push origin main
# Wait for auto-deploy
```

**Method 2: Azure Portal**
1. Go to Azure Static Web Apps
2. Navigate to "Deployments"
3. Select previous deployment
4. Click "Promote"

### Quick Fix

**For urgent fixes**
```bash
# Make fix in web/ directory
git add web/
git commit -m "fix: urgent issue description"
git push origin main
# Deployment completes in ~2 minutes
```

---

## 📈 Monitoring

### Check Health
```bash
# Test URL accessibility
curl -I https://orange-sand-00170940f.3.azurestaticapps.net

# Check Azure status
az staticwebapp show \
  --resource-group boloo-production-rg \
  --name boloo-web-admin \
  --query "{status:sku, url:defaultHostname}"
```

### View Logs
```bash
# GitHub Actions logs
# → GitHub repo → Actions tab → Latest workflow

# Azure logs
# → Azure Portal → Static Web App → Logs
```

### Performance Audit
```bash
# Run Lighthouse
npx lighthouse https://orange-sand-00170940f.3.azurestaticapps.net

# Check bundle size
cd web/
npm run build
du -sh out/
```

---

## 💡 Quick Tips

### Development
- Use `npm ci` for clean installs
- Run `npm run lint` before committing
- Test build locally before pushing
- Use TypeScript for type safety
- Keep dependencies updated

### Performance
- Minimize bundle size
- Use code splitting
- Enable caching
- Optimize images (if added)
- Monitor Lighthouse scores

### Security
- Never commit secrets
- Use environment variables
- Keep dependencies updated
- Review security headers
- Monitor for vulnerabilities

### Deployment
- Test thoroughly in development
- Use PR previews for testing
- Monitor GitHub Actions
- Verify after deployment
- Keep documentation updated

---

## 📞 Support

### Resources
- Deployment Guide: `docs/WEB_VERSION_DEPLOYMENT.md`
- User Guide: `docs/WEB_APP_USER_GUIDE.md`
- Status Report: `docs/WEB_DEPLOYMENT_STATUS.md`

### External Links
- [Next.js Docs](https://nextjs.org/docs)
- [Azure Static Web Apps](https://learn.microsoft.com/azure/static-web-apps)
- [GitHub Actions](https://docs.github.com/actions)

### Getting Help
1. Check this quick reference
2. Review full documentation
3. Check GitHub Actions logs
4. Verify Azure status
5. Contact system administrator

---

## 🎯 Common Tasks

### Add New Page
```typescript
// 1. Create file: web/app/newpage/page.tsx
export default function NewPage() {
  return <div>New Page Content</div>
}

// 2. Build and deploy
npm run build
git add .
git commit -m "feat: add new page"
git push origin main
```

### Update Dependencies
```bash
cd web/

# Check outdated
npm outdated

# Update all
npm update

# Update specific
npm install package@latest

# Security audit
npm audit
npm audit fix
```

### Change API URL
```bash
# 1. Update GitHub Secret
# GitHub → Settings → Secrets → NEXT_PUBLIC_API_URL

# 2. Redeploy
# GitHub → Actions → Deploy Web → Run workflow
```

---

**Last Updated**: November 2024
**Version**: 1.0.0
**Quick Reference for**: Boloo Web Admin
