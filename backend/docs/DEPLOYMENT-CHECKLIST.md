# Deployment Checklist

Use this checklist before deploying to production.

## Pre-Deployment

### Code Quality
- [ ] All tests passing locally
- [ ] No linting errors
- [ ] Code reviewed and approved
- [ ] Documentation updated
- [ ] CHANGELOG.md updated

### Configuration
- [ ] Environment variables configured in `.env.production`
- [ ] Database migrations tested
- [ ] Secrets stored in Azure Key Vault
- [ ] CORS origins configured correctly
- [ ] Rate limiting configured

### Security
- [ ] JWT secret key rotated
- [ ] API keys secured
- [ ] Database credentials secured
- [ ] SSL/TLS certificates valid
- [ ] Security headers configured

### Infrastructure
- [ ] Azure resources provisioned
- [ ] Database backup configured
- [ ] Monitoring enabled
- [ ] Log retention configured
- [ ] Health check endpoint working

## Deployment

### Build & Push
- [ ] Docker image builds successfully
- [ ] Image pushed to GHCR
- [ ] Image tagged correctly
- [ ] Previous image backed up

### Deploy
- [ ] Azure credentials valid
- [ ] App Service configuration updated
- [ ] Environment variables set
- [ ] Container image deployed
- [ ] App Service restarted

### Validation
- [ ] Health check passes
- [ ] Smoke tests pass
- [ ] API documentation accessible
- [ ] Response times acceptable
- [ ] Error rates normal

## Post-Deployment

### Monitoring
- [ ] Application logs reviewed
- [ ] Error tracking active
- [ ] Performance metrics normal
- [ ] Database connections healthy
- [ ] API endpoints responding

### Testing
- [ ] Critical user flows tested
- [ ] Integration tests passing
- [ ] Load testing (if applicable)
- [ ] Security scan completed

### Communication
- [ ] Team notified of deployment
- [ ] Release notes published
- [ ] Stakeholders informed
- [ ] Support team briefed

### Backup Plan
- [ ] Rollback procedure ready
- [ ] Previous version tagged
- [ ] Rollback tested (if needed)
- [ ] Incident response plan reviewed

## Rollback Criteria

Rollback if any of these occur:
- [ ] Health check fails for > 5 minutes
- [ ] Error rate > 5%
- [ ] Response time > 3 seconds
- [ ] Database connection failures
- [ ] Critical feature broken

## Rollback Procedure

If rollback needed:

1. Execute rollback script:
   ```bash
   ./scripts/rollback-deployment.sh previous
   ```

2. Verify health:
   ```bash
   curl https://boloo-backend-api.azurewebsites.net/health
   ```

3. Test deployment:
   ```bash
   ./scripts/test-deployment.sh
   ```

4. Notify team and investigate root cause

## Sign-off

Deployment completed by: ________________
Date: ________________
Time: ________________

Verified by: ________________
Date: ________________

Notes:
_______________________________________
_______________________________________
_______________________________________
