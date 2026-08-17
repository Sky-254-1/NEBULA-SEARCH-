# Staging Environment

## Overview

Staging is a production-like environment used for testing changes before they go live. It mirrors production infrastructure but with smaller resource allocations.

## Access

- **URL**: https://staging.nebula-search.example.com
- **API Docs**: https://staging.nebula-search.example.com/docs
- **Health Check**: https://staging.nebula-search.example.com/health

## Deployment

Staging deploys automatically when code is pushed to the `develop` branch.

### Manual Deployment

```bash
# Trigger staging deployment
git push origin develop

# Or via GitHub CLI
gh workflow run staging.yml --ref develop
```

### Deployment Pipeline

1. Run tests (backend + frontend)
2. Build Docker image
3. Push to staging ECR
4. Deploy to staging Kubernetes namespace (`nebula-staging`)
5. Run smoke tests
6. Send Slack notification

## Configuration

Staging uses the same configuration as production but with:
- Smaller database instance (db.t3.micro)
- Single Redis node (no cluster)
- Lower resource limits
- Test data seeded automatically

### Environment Variables

Set in GitHub Secrets:
- `STAGING_ECR_REGISTRY` - ECR registry for staging images
- `STAGING_KUBE_CONFIG` - Kubernetes config for staging cluster
- `SLACK_WEBHOOK_URL` - Slack notifications

## Testing Checklist

Before deploying to production, verify:

- [ ] All tests pass in staging
- [ ] Smoke tests pass (health, docs endpoint)
- [ ] Manual testing of critical user flows:
  - [ ] User signup/login
  - [ ] Search functionality
  - [ ] Document upload
  - [ ] AI chat
  - [ ] Admin dashboard
- [ ] Performance is acceptable (< 2s response time)
- [ ] No errors in staging logs
- [ ] Database migrations ran successfully
- [ ] SSL certificate is valid

## Data

Staging uses synthetic test data that is reset weekly. Do not store production data in staging.

## Cleanup

Staging deployments are automatically cleaned up after 7 days to reduce costs.

## Troubleshooting

### View Logs

```bash
kubectl logs -n nebula-staging -l app=nebula-backend --tail=100 -f
kubectl logs -n nebula-staging -l app=nebula-frontend --tail=100 -f
```

### Restart Services

```bash
kubectl rollout restart deployment/nebula-backend -n nebula-staging
```

### Database Access

```bash
kubectl exec -n nebula-staging -it <postgres-pod> -- psql -U nebula -d nebula
```

### Reset to Production-like State

```bash
# Run seed script
kubectl exec -n nebula-staging <backend-pod> -- python -m app.database.seed