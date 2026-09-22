# SECURITY.md

Controls and posture. Attacker-perspective analysis is in THREAT-MODEL.md.

> **Claim discipline:** this describes a *security-conscious prototype architecture*. Nothing here has been penetration-tested or independently audited. Do not describe the system as "secure" in any report or demo.

## Authentication

JWT RS256. Access token 15 min, refresh token 7 days.

Refresh tokens are checked against a PostgreSQL denylist on every grant. **The check fails closed** — if the database is unreachable, refresh returns 401 rather than allowing the grant. An auth check that fails open is worse than no auth check, because it creates false confidence.

**Accepted limitation:** access tokens are stateless and unrevocable before expiry. A compromised token is valid for up to 15 minutes. Accepted at this TTL; revisit if TTL ever grows.

Private key: environment variable, never in image layers, never in the repo. Public key distributed for verification.

## Authorization

| Role | Permitted |
|---|---|
| `OPERATOR` | Upload, view own documents and analyses, request deletion of own |
| `REVIEWER` | View assigned analyses, submit review decisions. **No upload** |
| `ADMIN` | Above + user management + audit access |

Authorization is checked at the resource level, not just the route. A REVIEWER hitting an analysis they aren't assigned to gets denied even though the route permits reviewers.

**Unauthorized access returns 404, not 403**, wherever 403 would confirm a resource exists to someone enumerating UUIDs. See ERROR-CONTRACT.md.

## Object storage

Buckets fully private. No public URL is ever issued.

Flow: client requests image → API verifies auth + ownership → API issues presigned GET, **60-second TTL** → client fetches directly.

Presigned URLs are bearer capabilities: anyone holding one has access for its lifetime. Therefore they are never logged, never stored, never included in an audit record. The 60s TTL is what keeps a leaked URL from being a durable breach.

## Upload validation

Ordered — each step runs only if the prior passed:

1. **Magic bytes** determine type. Client-supplied `Content-Type` and file extension are advisory and ignored for decisions.
2. Size ≤ 20 MB, enforced at API and DB.
3. PDFs: reject on embedded JavaScript (`PDF_ACTIVE_CONTENT_REJECTED`).
4. Images decoded into numpy arrays before persistence — decoded as data, never executed.
5. Storage key is a server-generated UUID path. Client filenames never reach the filesystem — this is the whole path-traversal class, closed by construction.

## Transport and rest

TLS on every hop: client↔API, API↔storage, API↔PostgreSQL, worker↔openFDA. Object storage server-side encryption at rest. Database at-rest encryption is a deployment concern (volume/disk level) and must be verified per environment rather than assumed.

## Logging

Whitelist, not blacklist. A structlog processor drops any field not on the permitted list and increments a warning metric.

**Permitted:** `request_id`, `analysis_id`, `document_id`, `pipeline_stage`, `model_version_id`, `status`, `duration_ms`, `error_code`, `actor_id`.

**Never logged:** image bytes, OCR text, medication names, dosages, patient_ref, presigned URLs, tokens, stack traces in production responses.

A blacklist would require predicting every field name someone might add later. The whitelist fails safe when a developer adds a field nobody reviewed.

## Secrets

Pydantic `BaseSettings` from environment only. Not hardcoded, not baked into image layers, not in logs, not in the repo. `.env.example` lists names with empty values; `.env` is gitignored. CI scans for committed secrets (see CI-CD.md).

## Rate limiting

Per-user limits on `POST /auth/token` (brute-force) and `POST /prescriptions` (storage exhaustion). **Not yet specified numerically** — limits set from measured normal usage rather than invented now.

openFDA is called **one drug name per query**, never a query encoding the full medication list. A combined query would leak a patient's complete medication profile to a third party in a single request; individual lookups leak only that a drug was queried, by someone, at some time.

## Deletion

Deletion isn't complete when the DB row is gone. Multi-stage, verifiable, manifest-backed — see Arch §17. The manifest lives in a separately-permissioned vault the application can write to but not delete from. **A restore without manifest re-application resurrects deleted patient data**; that step is mandatory in the DR runbook, not advisory.

## Dependency and license hygiene

Every runtime dependency's license verified at its primary source. `pip-audit` in CI. Model weights carry `license` in `model_versions` as a required field — a model with unverified licensing cannot be registered, and an unregistered model cannot load.

## Known gaps (V1)

| Gap | Why accepted | Revisit when |
|---|---|---|
| No pen-test | Academic prototype, no budget | Before any real patient data |
| Access tokens unrevocable ≤15min | Statelessness tradeoff | TTL increases |
| No WAF / DDoS protection | Single-instance, low volume | Public exposure |
| No MFA | Small known user set | Multi-org deployment |
| At-rest DB encryption deployment-dependent | Varies by host | Per environment, verified not assumed |
| No malware scanning on uploads | Images decoded as arrays; PDFs JS-stripped | Broader file type support |