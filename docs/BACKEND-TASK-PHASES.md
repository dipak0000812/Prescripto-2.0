# Prescripto AI 2.0 — Backend Implementation Tasks & Roadmap

**Branch:** `bhushan`  
**Backend Engineer:** Bhushan  
**Reference Specs:** PRD v1, System Architecture v1.1, PROJECT-SPEC v1.0, API-CONTRACT.md, DATABASE-DESIGN.md

---

## 📌 Implementation Philosophy & Rules
1. **Branch Hygiene:** All work commits to `bhushan`. Commits are atomic and structured: `feat(slice-X): <description>` or `test(slice-X): <description>`.
2. **Uncertainty Invariant:** Upstream uncertainty must never silently become downstream certainty.
3. **Strict Layering:** `prescripto/domain/` has zero external dependencies (no FastAPI, no SQLAlchemy, no Boto3).
4. **Zero PHI in Logs:** No prescription images, patient identifiers, or raw OCR lines in application logs.
5. **Contract Parity:** DB check constraints and Pydantic schemas must strictly match `PROJECT-SPEC.md` enums and `OPENAPI.yaml`.

---

## 🗺️ Phase Overview

```
Phase 1: Project Foundations & Infrastructure (Slice 0)
   ├── Directory Structure & Packaging
   ├── Docker Compose (PostgreSQL 16 + MinIO)
   ├── Alembic Database Migrations (with C-3 fix)
   ├── Structured Logging (Zero-PHI)
   └── FastAPI Skeleton & RS256 JWT Auth
        ↓
Phase 2: Storage & Prescription Ingestion API (Slice 1)
   ├── MinIO/S3 Storage Service & Presigned URLs
   ├── IngestPrescription Use Case
   ├── POST /api/v1/prescriptions (Idempotent 202)
   └── Document Listing & Retrieval Endpoints
        ↓
Phase 3: Fenced Job Queue & Worker Engine (Slice 2)
   ├── PostgreSQL FOR UPDATE SKIP LOCKED Poller
   ├── Monotonic Lease Tokens & Heartbeat
   ├── Atomic Generation Fencing & WorkerFencedError
   └── Worker Process & Pipeline Coordinator
        ↓
Phase 4: Medication Master & Safety Screening Engine (Slices 6 & 7)
   ├── CDSCO Medication Master Seed & FTS Indexes
   ├── Pure Domain Safety Engine (Deterministic Rules)
   ├── Duplicate Medication Check
   └── Capability-Gated Providers & NOT_EVALUATED Paths
        ↓
Phase 5: Report Assembly, Review Routing & Review API (Slice 8)
   ├── Uncertainty Propagation & Review Triggers
   ├── Status & Result Endpoints (GET /analyses/{id}/result)
   └── Human Reviewer Submission API (POST /analyses/{id}/review)
        ↓
Phase 6: DPDPA Verifiable Deletion & Audit (Slice 10)
   ├── DELETE /api/v1/prescriptions/{id} (Tombstone)
   ├── Deletion Worker (DB Cascade + S3 Purge)
   └── Separately Permissioned Retention Manifest Vault
        ↓
Phase 7: Hardening, Contract Parity & Failure Injection (Slice 12)
   ├── Worker Fencing & Race Condition Tests
   ├── OpenAPI Contract Validation Suite
   └── Failure Injection (Worker crash, DB disconnect)
```

---

## 📋 Detailed Phase Breakdown

### Phase 1: Project Foundations & Infrastructure (Slice 0)
- [ ] **Task 1.1: Project Directory Structure & Package Config**
  - Create directory structure:
    ```
    prescripto/
    ├── domain/
    │   ├── prescription/
    │   ├── analysis/
    │   ├── medication/
    │   ├── safety/
    │   ├── review/
    │   └── uncertainty/
    ├── application/
    │   ├── dtos/
    │   └── use_cases/
    ├── api/
    │   ├── v1/
    │   └── schemas/
    ├── pipeline/
    ├── ml/
    ├── knowledge/
    ├── storage/
    ├── db/
    │   └── migrations/
    ├── worker/
    ├── retention/
    ├── auth/
    ├── audit/
    └── config/
    tests/
    docker/
    scripts/
    ```
  - Create `pyproject.toml` and `requirements.txt` with locked versions.
  - Setup `.env.example` and Pydantic-based `prescripto/config/settings.py`.
- [ ] **Task 1.2: Containerization (Docker Compose)**
  - Create `docker-compose.yml` defining services:
    - `postgres`: PostgreSQL 16 with health check and initialization scripts.
    - `minio`: MinIO object storage with default bucket provisioning (`prescripto` and `prescripto-retention`).
    - `api`: FastAPI web server (`prescripto.api.main:app`).
    - `worker`: Analysis background worker (`prescripto.worker.main`).
    - `deletion_worker`: Deletion background worker (`prescripto.retention.worker`).
- [ ] **Task 1.3: Database Models & Initial Alembic Migration (Fixing C-3)**
  - Define SQLAlchemy 2.0 models in `prescripto/db/models/`.
  - Ensure `prescription_medications` includes `unit_*` and `instructions_*` fields (resolving PRD/Arch conflict C-3).
  - Include all database constraints:
    - Enum `CHECK` constraints on statuses.
    - `chk_not_evaluated_reason` on `risk_findings`.
    - Partial index `idx_analysis_jobs_claimable`.
    - GIN index on `medications(brand_name, generic_name)`.
  - Create Alembic migration `0001_initial_schema.py` with verified `upgrade()` and `downgrade()`.
- [ ] **Task 1.4: Structured Zero-PHI Logging System**
  - Implement custom logger in `prescripto/audit/logger.py`.
  - Whitelist filter that blocks prescription images, OCR text buffers, and patient names.
- [ ] **Task 1.5: FastAPI App Skeleton & Health Checks**
  - Setup `prescripto/api/main.py` with standard error response envelope (`{"error": {"code", "message", "request_id"}}`).
  - Add `GET /api/v1/health` and `GET /api/v1/health/ready` (validating PostgreSQL and MinIO ping).
- [ ] **Task 1.6: RS256 JWT Authentication & Blocklist**
  - Implement token issuance in `prescripto/auth/`.
  - Implement `POST /api/v1/auth/token` and `POST /api/v1/auth/refresh`.
  - Connect refresh token validation to `token_blocklist` with fail-closed behavior (`401 BLOCKLIST_UNAVAILABLE`).
  - Add RBAC security dependencies (`OPERATOR`, `REVIEWER`, `ADMIN`).

---

### Phase 2: Storage & Prescription Ingestion API (Slice 1)
- [ ] **Task 2.1: MinIO/S3 Storage Service**
  - Implement `prescripto/storage/client.py` using `boto3`.
  - Secure bucket initialization, deterministic object keys.
  - Implement 60-second presigned URL generation (never persisted or logged).
- [ ] **Task 2.2: Pure Domain Prescription Ingestion Models**
  - Implement `PrescriptionDocument`, `Analysis`, `DocumentStatus` in `prescripto/domain/`.
  - Zero framework imports, pure business logic.
- [ ] **Task 2.3: IngestPrescription Application Use Case**
  - Implement `prescripto/application/use_cases/ingest_prescription.py`.
  - Validate image format (JPEG, PNG, WEBP, PDF) and max size (20MB).
  - Compute SHA-256 file checksum.
  - Handle idempotency:
    - Matching `Idempotency-Key` + matching hash → return existing `202` payload.
    - Matching `Idempotency-Key` + different hash → raise `409 IDEMPOTENCY_KEY_CONFLICT`.
- [ ] **Task 2.4: Upload Endpoint (`POST /api/v1/prescriptions`)**
  - Accept `multipart/form-data` with `Idempotency-Key` header.
  - Atomic DB transaction: insert `prescription_documents`, `analyses`, and `analysis_jobs` (`PENDING`).
  - Return `202 Accepted` with `document_id` and `analysis_id` within < 3s.
- [ ] **Task 2.5: Document Retrieval Endpoints**
  - `GET /api/v1/prescriptions`: Paginated, caller-scoped.
  - `GET /api/v1/prescriptions/{id}`: Detailed metadata with ephemeral presigned `image_url`.

---

### Phase 3: Fenced Job Queue & Worker Engine (Slice 2)
- [ ] **Task 3.1: PostgreSQL Transactional Queue Poller**
  - Implement `prescripto/worker/queue.py`.
  - Claim query using `SELECT ... FOR UPDATE SKIP LOCKED` targeting `PENDING` and claimable `FAILED` rows.
  - Set `lease_owner`, increment `lease_token`, set `lease_expires_at = now() + 10m`.
- [ ] **Task 3.2: Worker Lease Heartbeat Mechanism**
  - Background task that periodically (every 30s) updates `lease_expires_at` and `heartbeat_at`.
- [ ] **Task 3.3: Atomic Generation Fencing & Stage Persistence**
  - Implement `commit_stage_result()` in `prescripto/worker/fence.py`.
  - Validate `lease_token`, `lease_owner`, and `lease_expires_at > now()` in the same transaction.
  - Guard upsert against `analysis_stages.lease_token <= :token`.
  - Raise `WorkerFencedError` on fence collision or expired lease.
- [ ] **Task 3.4: Worker Retry Lifecycle & Dead Letter Queue**
  - Retry backoff schedule: 5s → 30s → 2m.
  - On `retry_count >= 3`, transition job to `DEAD` and trigger operator alert.
- [ ] **Task 3.5: Worker Main Runner**
  - Process coordinator running pipeline stages with lease check gates.

---

### Phase 4: Medication Master & Safety Screening Engine (Slices 6 & 7)
- [ ] **Task 4.1: Medication Master Seeding & Candidate Search**
  - Script `scripts/seed_medications.py` to seed CDSCO approved formulations.
  - Exact and fuzzy search queries against `medications` table using PostgreSQL `tsvector` / trigrams.
  - Candidate generator returning `RESOLVED`, `AMBIGUOUS`, or `UNRESOLVED`.
- [ ] **Task 4.2: Pure Domain Safety Engine**
  - Implement `prescripto/domain/safety/` without any external I/O.
  - Define `SafetyCheckType` (`DUPLICATE_MEDICATION`, `EVIDENCE_LOOKUP`, `ADVERSE_EFFECT`).
  - Define `FindingStatus` (`CONFIRMED_BY_SOURCE`, `POTENTIAL`, `INSUFFICIENT_EVIDENCE`, `NOT_EVALUATED`, `REQUIRES_REVIEW`).
- [ ] **Task 4.3: Duplicate Medication Detector**
  - Deterministic check comparing active ingredients and therapeutic classes among resolved drugs.
  - Generate `RiskFinding` records with full provenance.
- [ ] **Task 4.4: Knowledge Providers & Capability Gates**
  - Abstract `KnowledgeProvider` base class.
  - Implement `OpenFDAProvider` (per-drug queries, no bulk batching to safeguard privacy).
  - Enforce `NOT_EVALUATED` guarantee with mandatory reason when provider cannot evaluate or times out.

---

### Phase 5: Report Assembly, Review Routing & Review API (Slice 8)
- [ ] **Task 5.1: Report Assembly Stage & Review Trigger Evaluation**
  - Aggregate all stage outputs, medications, and findings.
  - Evaluate review triggers:
    - Any field with `AMBIGUOUS` state
    - Any medication with `UNRESOLVED` status
    - Any risk finding with `REQUIRES_REVIEW` or `POTENTIAL`
  - Route analysis to `COMPLETED` or `REQUIRES_REVIEW`.
  - Ensure `coverage_disclaimer` is always populated.
- [ ] **Task 5.2: Analysis Status & Result Endpoints**
  - `GET /api/v1/analyses/{id}`: Poll status, stage progress, and timestamps.
  - `GET /api/v1/analyses/{id}/result`: Full structured report.
    - Return `404 ANALYSIS_NOT_READY` for incomplete/processing analyses.
    - Include `fields`, `states`, `findings`, and `not_evaluated[]`.
- [ ] **Task 5.3: Review Submission Endpoint (`POST /api/v1/analyses/{id}/review`)**
  - Check role permissions (`REVIEWER` or `ADMIN`).
  - Accept review decisions (approve, flag, escalate) and optional field corrections.
  - Record entry in `reviews` table and transition analysis to `REVIEWED_COMPLETE` or `REVIEWED_ESCALATED`.

---

### Phase 6: DPDPA 2023 Verifiable Deletion & Audit (Slice 10)
- [ ] **Task 6.1: Deletion Request Endpoint (`DELETE /api/v1/prescriptions/{id}`)**
  - Mark document as `DELETION_REQUESTED`.
  - Insert job into `deletion_jobs` (`REQUESTED`).
- [ ] **Task 6.2: Deletion Worker Process (`prescripto/retention/worker.py`)**
  - Execute multi-step erasure:
    1. `DB_TOMBSTONED`: Purge prescription-scoped rows (`analyses`, `medications`, `findings`) while preserving global `medications` master.
    2. `STORAGE_DELETING`: Purge original image and line crops from MinIO/S3.
    3. `VERIFYING`: Check DB and S3 confirm zero remaining records.
    4. `COMPLETE`: Generate signed deletion manifest.
- [ ] **Task 6.3: Immutable Deletion Manifest Vault**
  - Write deletion manifest to `prescripto-retention` bucket.
  - Create restore verification script `scripts/apply_deletion_manifests.py`.

---

### Phase 7: Hardening, Contract Parity & Failure Injection (Slice 12)
- [ ] **Task 7.1: Worker Fencing & Race Condition Test Suite**
  - Test two workers attempting to commit with different lease tokens.
  - Test lease expiry fence rejection.
- [ ] **Task 7.2: OpenAPI Contract Parity Tests**
  - Automated test verifying all endpoints and schemas match `OPENAPI.yaml`.
- [ ] **Task 7.3: Failure Mode & Recovery Tests**
  - Worker crash mid-pipeline and automatic recovery.
  - Database reconnect and MinIO transient outage handling.
