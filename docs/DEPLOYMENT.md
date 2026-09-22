# DEPLOYMENT.md

## Topology

One Docker image, three entrypoints, five compose services.

```
api              uvicorn prescripto.api.main:app --host 0.0.0.0 --port 8000
worker           python -m prescripto.worker.main
deletion_worker  python -m prescripto.retention.worker
postgres         postgres:16
minio            MinIO (dev) → S3 (prod, config-only change)
```

One image because all three share domain types, ORM models, and schemas — separate images create version-coordination overhead with no isolation benefit at this scale. Three processes because their failure modes and latency profiles differ: a worker OOM during OCR must not take the API down.

## Environments

| | Development | Staging/Demo | Production |
|---|---|---|---|
| Deploy | `docker compose up` | Compose on a single VM | Not in V1 scope |
| Storage | MinIO | MinIO or S3 | S3 |
| Data | Synthetic only | De-identified Tier B | — |
| `LLM_ENABLED` | false | false | false |
| SIDER | enabled | enabled | **disabled** (`RESEARCH_ONLY`) |
| Retention | 7 days | 30 days | Policy-defined |
| TLS | off (localhost) | reverse proxy | required |

**Never use real patient data in development.** Tier B enters staging only, already de-identified.

## Configuration

Pydantic `BaseSettings`, environment only. Startup validates every required variable and **exits non-zero if any is missing** — a service that boots with a silently-defaulted secret is worse than one that refuses to start.

```
DATABASE_URL, DB_POOL_SIZE
S3_ENDPOINT, S3_BUCKET, S3_ACCESS_KEY, S3_SECRET_KEY, S3_REGION
RETENTION_VAULT_BUCKET                  # separate IAM principal
JWT_PRIVATE_KEY, JWT_PUBLIC_KEY, JWT_ACCESS_TTL=900, JWT_REFRESH_TTL=604800
OCR_MODEL_NAME, OCR_MODEL_VERSION       # exact version, never "latest"
MODEL_CACHE_DIR
LLM_ENABLED=false
ENABLED_KNOWLEDGE_PROVIDERS             # e.g. openfda,rxnorm
LICENSE_MODE_ALLOWED                    # commercial build excludes RESEARCH_ONLY
OPENFDA_API_KEY                         # optional; raises rate limit
RETENTION_DAYS, MAX_UPLOAD_BYTES=20971520
LOG_LEVEL, ENVIRONMENT
```

`LICENSE_MODE_ALLOWED` is the mechanism that keeps SIDER out of a commercial build — enforced at provider registration, not left to deployment discipline.

## Worker startup sequence

Refuses to start if any step fails. All four are safety gates, not health checks:

1. `OCR_MODEL_NAME:OCR_MODEL_VERSION` exists in `model_versions`
2. That row has a non-NULL `calibration_snapshot_id`
3. Downloaded artifact's SHA-256 matches `checkpoint_sha256`
4. Model loads without error

An uncalibrated model produces confidence scores that route the wrong cases to review. Starting anyway would be worse than not starting.

## Migrations

`alembic upgrade head` runs as a one-shot job **before** api/worker start — never in an application entrypoint, where concurrent replicas would race.

Rollback: `alembic downgrade -1`. Every migration's `downgrade()` is tested in CI, because discovering an untested downgrade during an incident is how a rollback becomes an outage.

## Model artifacts

Stored at `models/{model_name}/{model_version}/`, downloaded to a cache volume on worker start, hash-verified. The cache volume persists across restarts so a redeploy isn't a re-download.

## Health and readiness

`GET /api/v1/health` for both. Worker heartbeat is visible in that response, so "API up, worker dead" is externally detectable — the failure mode most likely to go unnoticed, since uploads keep succeeding and nothing ever completes.

## Rollback

| Change | Rollback |
|---|---|
| Application code | Redeploy previous image tag |
| Schema | `alembic downgrade` — **verify the tested downgrade exists before deploying** |
| Model version | Change `OCR_MODEL_VERSION`, restart worker. Old versions are never deleted from `model_versions` |
| Knowledge snapshot | Point to prior `knowledge_snapshots` row |

Model rollback is config-only precisely because `model_versions` rows are immutable and never pruned.

## Backup and restore

`pg_dump` daily, 30-day retention. Object storage versioning enabled.

**Restore procedure — the manifest step is mandatory:**
1. Restore database
2. Restore object storage
3. **Run the manifest re-application script against the retention vault**
4. Verify no tombstoned document is queryable
5. Start services

Skipping step 3 resurrects deleted patient data. THREAT-MODEL R6 flags this as the system's weakest control, because it depends on a human remembering — automate it into the restore script rather than leaving it in prose.

## Scaling triggers (Arch §20)

Nothing is added before its trigger fires: second worker at sustained queue depth > 50; Redis/Celery at sustained lock wait > 100 ms; GPU if OCR dominates a profiled P95 > 180 s; PgBouncer at pool exhaustion.

## Not in V1

Kubernetes, multi-node, autoscaling, blue-green, CDN, managed secrets (Vault/KMS), multi-region. Each has a documented trigger in Arch §20; none has fired.