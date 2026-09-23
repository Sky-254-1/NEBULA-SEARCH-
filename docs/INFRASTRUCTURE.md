# Nebula Search Infrastructure

## Cloud Architecture (AWS)

### Terraform Infrastructure (`infra/terraform/`)
- **VPC**: Isolated network with public/private subnets across 2 AZs
- **NAT Gateway**: Secure outbound internet access for private resources
- **RDS PostgreSQL 16.1**: Managed database with automated backups
- **ElastiCache Redis 7.1**: Clustered cache with automatic failover
- **S3 Buckets**: Uploads and exports storage with versioning
- **Application Load Balancer**: HTTPS termination with WAF integration
- **ECS Fargate**: Serverless container orchestration (2 tasks, 512MB/1GB)
- **CloudFront CDN**: Global content delivery with DDoS protection
- **WAF**: Rate limiting + AWS managed rule sets
- **SSM Parameter Store**: Secure secrets management (JWT, encryption keys)

### Kubernetes (`infra/kubernetes/`)
- **Deployment**: 3 replicas with security contexts (non-root, read-only filesystem)
- **Service**: ClusterIP for internal routing
- **HPA**: Autoscaling from 3 to 20 pods based on CPU/memory
- **Prometheus**: Metrics collection and monitoring
- **Secrets**: Encrypted Kubernetes secrets for sensitive data

## CI/CD Pipeline (`.github/workflows/deploy.yml`)

1. **Test**: Backend (pytest) + Frontend (vitest) + lint
2. **Security Scan**: Trivy vulnerability scanner
3. **Build & Push**: Docker image to ECR
4. **Terraform**: Infrastructure provisioning
5. **Kubernetes Deploy**: Rolling update with health checks
6. **Notify**: Slack notification on completion

## Security Hardening (100% Target)

### Application Layer
- **InputValidationMiddleware**: SQL injection + XSS detection
- **AdvancedRateLimitMiddleware**: Per-IP and per-user rate limiting
- **AuditLoggingMiddleware**: Security event logging to database
- **CSRFProtectionMiddleware**: Token-based CSRF defense
- **SecurityHeadersMiddleware**: HSTS, CSP, X-Frame-Options, Permissions-Policy
- **IPWhitelistMiddleware**: Admin IP restriction

### Infrastructure Layer
- **WAF**: Rate limiting + managed rule sets
- **Security Groups**: Network-level access control
- **Private Subnets**: Backend isolation from internet
- **NAT Gateway**: Controlled outbound access
- **SSM Parameter Store**: Encrypted secrets
- **EBS Encryption**: At-rest encryption for RDS
- **CloudTrail**: AWS API audit logging

### Kubernetes Security
- **Security Contexts**: Non-root, dropped capabilities, read-only filesystem
- **Resource Limits**: CPU/memory constraints
- **Health Probes**: Liveness and readiness checks
- **RBAC**: Kubernetes role-based access control

## Observability

- **Prometheus**: Metrics collection (requests, duration, cache hits)
- **OpenTelemetry**: Distributed tracing
- **Sentry**: Error tracking
- **Structured Logging**: JSON format in production
- **Audit Logs**: 90-day retention for security events
- **Health Checks**: `/health`, `/health/live`, `/health/ready`, `/health/detailed`