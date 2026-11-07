# DEPLOYMENT.md

## Topology

One Docker image, three entrypoints, five compose services.

```
api              uvicorn prescripto.api.main:app --host 0.0.0.0 --port 8000
worker           python -m prescripto.worker.main
deletion_worker  python -m prescripto.retention.worker   # code exists; not yet in compose
postgres         postgres:16
minio            MinIO (dev) → S3 (prod, config-only change)
ml-service       disabled (compose profile `ml-service`; do not set ML_RUNTIME_MODE=remote)
```

One image because all three share domain types, ORM models, and schemas — separate images create version-coordination overhead with no isolation benefit at this scale. Three processes because their failure modes and latency profiles differ: a worker OOM during OCR must not take the API down.

## Environments

| | Development | Staging/Demo | Production |
|---|---|---|---|
| Deploy | `docker compose up` | Compose on a single VM | Deploy API/worker and frontend with a managed secret store |
| Storage | MinIO | MinIO or S3 | S3 |
| Data | Synthetic only | De-identified Tier B | Only with documented privacy/legal approval |
| `RECOGNITION_PROVIDER` | `gemini` (RapidOCR on quota/auth/timeout only) | `gemini` | `gemini` |
| `LLM_ENABLED` | false | false | false unless separately approved |
| SIDER | enabled | enabled | **disabled** (`RESEARCH_ONLY`) |
| Retention | 7 days | 30 days | Policy-defined |
| TLS | off (localhost) | reverse proxy | required |

**Never use real patient data in development.** Tier B enters staging only, already de-identified.

## Configuration

Pydantic `BaseSettings`, environment only. Startup validates every required variable and **exits non-zero if any is missing** — a service that boots with a silently-defaulted secret is worse than one that refuses to start.

```
DATABASE_URL (host: localhost:5435; inside Docker: postgres:5432), DB_POOL_SIZE
S3_ENDPOINT, S3_BUCKET, S3_ACCESS_KEY, S3_SECRET_KEY, S3_REGION
RETENTION_VAULT_BUCKET                  # separate IAM principal
JWT_PRIVATE_KEY, JWT_PUBLIC_KEY, JWT_ACCESS_TTL=900, JWT_REFRESH_TTL=604800
OCR_MODEL_NAME, OCR_MODEL_VERSION       # exact version, never "latest"
MODEL_CACHE_DIR
RECOGNITION_PROVIDER=gemini            # default; RapidOCR only after Gemini quota/auth/timeout
GEMINI_API_KEY                         # backend secret; never expose to frontend; missing key logs one error at startup
GEMINI_MODEL=gemini-3.5-flash          # primary Gemini model name
GEMINI_FALLBACK_MODEL=gemini-3.1-flash-lite # fallback Gemini model before RapidOCR
LLM_ENABLED=false                      # optional Gemini commentary layer, separate from recognition
ENABLED_KNOWLEDGE_PROVIDERS             # e.g. openfda,rxnorm
LICENSE_MODE_ALLOWED                    # commercial build excludes RESEARCH_ONLY
OPENFDA_API_KEY                         # optional; raises rate limit
RETENTION_DAYS, MAX_UPLOAD_BYTES=20971520
LOG_LEVEL, ENVIRONMENT
```

`LICENSE_MODE_ALLOWED` is the mechanism that keeps SIDER out of a commercial build — enforced at provider registration, not left to deployment discipline.

Copy `backend/.env.example` to `backend/.env` for host runs. That file uses `DATABASE_URL=...@localhost:5435/...` because Compose publishes Postgres on host port 5435. Compose services override `DATABASE_URL` to `postgres:5432` on the internal network — do not put the `postgres` hostname in a host `.env`. CORS defaults include `http://localhost:5173` and `http://localhost:3000`.

For Gemini recognition, set `RECOGNITION_PROVIDER=gemini` (the default), `GEMINI_API_KEY`, `GEMINI_MODEL=gemini-3.5-flash`, and `GEMINI_FALLBACK_MODEL=gemini-3.1-flash-lite` on both the API and worker. `docker-compose.yml` reads `backend/.env` and sets `GEMINI_MODEL=gemini-3.5-flash` with `GEMINI_FALLBACK_MODEL=gemini-3.1-flash-lite`. Never use a frontend `VITE_` variable for the key. If `GEMINI_API_KEY` is empty at process startup, the API and worker log one error and do not print the key. RapidOCR is used only when Gemini returns quota, auth, or timeout failures — not as a paid-provider switch, and not when the key is missing. The `ml-service` container is not started (`docker compose --profile ml-service up` only); leave `ML_RUNTIME_MODE` as `rapidocr` and do not set `remote`.

Google's Gemini API pricing page lists currently available access and limits. Free-tier quotas vary by project, model, and region and can change. A 429/quota response falls back to local RapidOCR; the job is not retried against a paid Gemini tier. Google states free-tier content may be used to improve its products; see Gemini API terms. Do not send identifiable prescriptions or other PHI without explicit organizational privacy/legal approval. Keep `LLM_ENABLED=false` unless the separate commentary feature is approved; it uses the same `gemini-3.5-flash` model.

The selected model name and free-tier eligibility are time-sensitive; recheck current official model availability, quota, regional support, and data-use terms immediately before deployment. `GEMINI_API_KEY` is a backend secret only and must not appear in client bundles, logs, or committed files.

## Worker startup sequence

**Specified startup sequence** — the following gates are architecturally required; the schema exists but startup enforcement is not yet wired in `worker/main.py`:

1. `OCR_MODEL_NAME:OCR_MODEL_VERSION` exists in `model_versions`
2. That row has a linked `calibration_snapshots` row
3. Downloaded artifact's SHA-256 matches `checkpoint_sha256`
4. Model loads without error

Until these gates are wired, the worker boots without validating model/calibration registration. `ML_RUNTIME_MODE=remote` / `RemoteMLClient` remains disabled.

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


## Medicine Reminders Engine & Web Push (VAPID)

Prescripto 2.0 includes an automated medicine reminder scheduler and standard Web Push notification engine.

### Configuration & Keys
1. **Generate VAPID Keypair**:
   ```bash
   python backend/scripts/generate_vapid_keys.py
   ```
   This generates an uncompressed P-256 keypair formatted for Web Push.
2. **Environment Variables**:
   - `VAPID_PUBLIC_KEY`: Base64URL-encoded public key shared with the browser.
   - `VAPID_PRIVATE_KEY`: Secret private key for signing push headers.
   - `VAPID_CLAIMS_SUB`: Subject contact (e.g. `mailto:support@prescripto.local`).

### Architecture & Worker Scheduler
- **Worker Dispatch Loop**:
  The background worker process (`prescripto.worker.main:WorkerRunner`) runs a scheduled dispatch loop (`dispatch_reminders_if_due(interval_seconds=30.0)`).
- **Execution Flow**:
  1. Queries all due doses (`status IN ('PENDING', 'SNOOZED')` and `due_at <= now_utc`).
  2. For users with registered push subscriptions (`push_subscriptions` table), securely encrypts the payload and delivers it via `pywebpush`.
  3. Events older than 2 hours without patient response are transitioned to `MISSED`.
  4. Snoozed events automatically create a new dose event scheduled 10 minutes later.
- **Calendar (.ics) Integration**:
  Provides RFC 5545 iCalendar feeds (`GET /api/v1/reminders/plans/{id}/calendar.ics`) with embedded alarms (`VALARM`) for offline Google Calendar, Apple Calendar, and Outlook sync.
- **PWA Service Worker**:
  - `web/public/sw.js` handles push events and background notifications with interactive action buttons (`Taken`, `Snooze 10m`, `Skip`).
  - `web/public/manifest.json` enables Add-to-Home-Screen PWA support (mandatory for Web Push on iOS 16.4+).
