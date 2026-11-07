# Prescripto AI 2.0 — Production Deployment Guide

This document describes how to deploy Prescripto AI 2.0 to production using **Render** (managed services) with **PostgreSQL**, **S3**, and **Docker**.

---

## Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Frontend      │     │    Backend API   │     │   Background    │
│   (Static Site) │────▶│   (Web Service)  │────▶│   Workers       │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                              │        │
                              ▼        ▼
                        ┌──────────────────┐     ┌─────────────────┐
                        │   PostgreSQL     │     │      S3         │
                        │   (Managed)      │     │   (AWS/MinIO)   │
                        └──────────────────┘     └─────────────────┘
```

---

## Prerequisites

1. **Render Account** with Blueprint access
2. **AWS Account** for S3 buckets (or MinIO for self-hosted)
3. **Google Cloud Project** with Gemini API enabled
4. **Domain** configured (optional, for custom domains)

---

## Quick Start: Render Blueprint

### 1. Prepare Secrets

Before deploying, generate the following secrets:

```bash
# 1. Generate JWT Keys
cd backend
python scripts/generate_keys.py
# Output: JWT_PRIVATE_KEY and JWT_PUBLIC_KEY

# 2. Generate VAPID Keys for Push Notifications
python scripts/generate_vapid_keys.py
# Output: VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY

# 3. Get Gemini API Key
# Go to Google AI Studio > Get API Key
```

### 2. Create S3 Buckets

Create the following buckets in AWS S3 (or configure MinIO):

| Bucket Name | Purpose |
|-------------|---------|
| `prescripto-prod` | Main prescription image storage |
| `prescripto-retention-prod` | DPDPA deletion manifests & audit exports |

Configure bucket policies for private access only.

### 3. Deploy via Render Blueprint

1. Go to **Render Dashboard** → **Blueprints** → **New Blueprint Instance**
2. Connect your GitHub repository
3. Select the `render.yaml` file in the repo root
4. Fill in all **sync: false** environment variables:
   - `POSTGRES_PASSWORD` (auto-generated)
   - `JWT_PRIVATE_KEY` (from step 1)
   - `JWT_PUBLIC_KEY` (from step 1)
   - `VAPID_PRIVATE_KEY` (from step 1)
   - `VAPID_PUBLIC_KEY` (from step 1)
   - `GEMINI_API_KEY` (from Google AI Studio)
   - `S3_ACCESS_KEY` / `S3_SECRET_KEY` (AWS credentials)
   - `OPENFDA_API_KEY` (optional, for drug safety data)

5. Click **Apply** — Render will provision all services automatically

---

## Manual Deployment (Docker Compose)

If not using Render, deploy with the production compose file:

```bash
# 1. Create .env files from templates
cp backend/.env.prod backend/.env
cp web/.env.prod web/.env

# 2. Fill in all required values in both .env files

# 3. Start services
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 4. Run migrations (first deploy only)
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec api alembic upgrade head

# 5. Seed medications
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec api python scripts/seed_medications.py
```

---

## Service Configuration Details

### Backend API (`prescripto-api`)

| Setting | Value |
|---------|-------|
| Runtime | Docker (gunicorn + UvicornWorker) |
| Workers | 4 |
| Port | 8000 |
| Health Check | `/health` |
| Timeout | 120s |

**Key Environment Variables:**
```env
ENVIRONMENT=production
DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/db
CORS_ORIGINS=https://prescripto.ai,https://www.prescripto.ai
GEMINI_API_KEY=your-key
JWT_PRIVATE_KEY=...
JWT_PUBLIC_KEY=...
RECOGNITION_PROVIDER=gemini
ML_RUNTIME_MODE=rapidocr
```

### Background Worker (`prescripto-worker`)

Processes prescription analysis jobs from the PostgreSQL queue.

```env
WORKER_ID=prod-worker-1
WORKER_LEASE_SECONDS=600
WORKER_MAX_RETRIES=3
ML_RUNTIME_MODE=rapidocr
```

### Deletion Worker (`prescripto-deletion-worker`)

Handles DPDPA-compliant data deletion with manifest verification.

```env
RETENTION_DAYS=90
```

### Frontend (`prescripto-frontend`)

| Setting | Value |
|---------|-------|
| Type | Static Site (Nginx) |
| Build | `npm run build` (Vite) |
| Publish Path | `dist/` |
| SPA Fallback | Rewrite all routes to `index.html` |

**Nginx Configuration** handles:
- API proxy to `/api/`
- WebSocket proxy to `/api/v1/notifications/ws`
- Security headers (CSP, HSTS, X-Frame-Options)
- Gzip compression
- Static asset caching

---

## Post-Deployment Verification

### 1. Health Checks

```bash
# API Health
curl https://prescripto-2-0.onrender.com/health
# Expected: {"status": "healthy", "database": "connected", "storage": "connected"}

# Database Health
curl https://prescripto-2-0.onrender.com/health/db

# Readiness
curl https://prescripto-2-0.onrender.com/health/ready
```

### 2. Authentication Flow

1. Navigate to `https://prescripto-2-0.onrender.com/login`
2. Test Patient OTP flow (requires SMS provider in production)
3. Test Doctor login with seeded credentials

### 3. End-to-End Test

1. Upload a prescription image
2. Wait for analysis to complete (check `/review-queue`)
3. Verify safety findings and medication extraction
4. Test clinical sign-off workflow

---

## Security Checklist

- [ ] All `sync: false` secrets configured in Render
- [ ] JWT keys are unique per environment
- [ ] VAPID keys generated for push notifications
- [ ] S3 buckets have private ACL + bucket policies
- [ ] CORS origins restricted to production domains only
- [ ] Rate limiting enabled on auth endpoints (TODO)
- [ ] CSP headers configured in Nginx
- [ ] HSTS enabled via Nginx
- [ ] Database SSL enforced (Render default)
- [ ] Audit logging enabled (`prescripto.audit.logger`)

---

## Monitoring & Observability

### Render Built-in Metrics
- CPU / Memory usage per service
- Request latency (p50, p95, p99)
- Error rates
- Deployment history

### Application Logs
```bash
# View API logs
render logs prescripto-api --tail 100

# View Worker logs
render logs prescripto-worker --tail 100
```

### Custom Metrics (TODO)
- Prometheus metrics endpoint at `/metrics`
- Grafana dashboards for:
  - Prescription volume trends
  - Safety finding rates
  - Review queue depth
  - Worker throughput

---

## Backup & Disaster Recovery

### Database
- Render PostgreSQL: **Daily automated backups** (7-day retention)
- Point-in-time recovery: Available via Render dashboard
- Manual backup: `pg_dump` via Render shell

### S3 Storage
- Versioning enabled on all buckets
- Cross-region replication (recommended)
- Lifecycle policy: Move to Glacier after 90 days

### Audit Trail
- `audit_events` table retains all security events
- DPDPA deletion manifests in `retention_vault_bucket`
- Immutable: Append-only, never deleted

---

## Scaling Considerations

| Component | Current | Scale Trigger | Action |
|-----------|---------|---------------|--------|
| API Workers | 4 | CPU > 70% sustained | Increase gunicorn workers |
| PostgreSQL | Starter | Connections > 80% | Upgrade plan |
| Worker | 1 | Queue depth > 50 | Add worker instances |
| S3 | Standard | Cost optimization | Intelligent Tiering |

---

## Troubleshooting

### Common Issues

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `401 Unauthorized` on login | JWT keys mismatch | Regenerate keys, ensure same in .env |
| `503 Storage unavailable` | MinIO/S3 unreachable | Check S3_ENDPOINT, credentials |
| Analysis stuck in `PROCESSING` | Worker crashed | Check worker logs, restart |
| WebSocket connection failed | Nginx proxy config | Verify `/api/v1/notifications/ws` proxy |
| CORS errors | Origin not allowed | Add domain to `CORS_ORIGINS` |

### Debug Commands

```bash
# View service logs
render logs <service-name> --tail 100

# Execute commands in container
render exec <service-name> -- python -c "import sys; print(sys.path)"

# Database shell
render exec prescripto-api -- psql $DATABASE_URL

# Check migration status
render exec prescripto-api -- alembic current
```

---

## Rollback Procedure

1. **Render Dashboard** → Service → **Deploys** → Select previous deploy → **Rollback**
2. For database migrations: `alembic downgrade -1` (if backward compatible)
3. For static site: Re-deploy previous build artifact

---

## Support & Escalation

| Severity | Response Time | Contact |
|----------|---------------|---------|
| P0 (Production Down) | 15 min | On-call engineer |
| P1 (Major Feature Broken) | 1 hour | Team lead |
| P2 (Minor Issue) | 4 hours | Developer |
| P3 (Enhancement) | Next sprint | Product team |

---

## Appendix: Required GitHub Secrets

For CI/CD pipeline (`.github/workflows/ci.yml`):

| Secret | Description |
|--------|-------------|
| `JWT_PRIVATE_KEY` | Production JWT private key |
| `JWT_PUBLIC_KEY` | Production JWT public key |
| `GEMINI_API_KEY` | Google Gemini Vision API key |
| `RENDER_DEPLOY_HOOK_URL` | Render deploy hook for auto-deploy |
| `S3_ACCESS_KEY` | AWS access key for S3 |
| `S3_SECRET_KEY` | AWS secret key for S3 |

---

*Last updated: 2026-11-06 | Version: 2.0.0*