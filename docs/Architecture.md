# Prescripto AI 2.0 — System Architecture & ADRs (LOCKED v1.1)

**Status:** LOCKED Architecture Baseline (v1.1)  
**Last updated:** 2026-09-11  
**Source of truth:** PRD v1 → this document  
**Lock Review v1.1 Applied:**
1. Atomic lease validation on stage commits (`lease_token`, `lease_owner`, `lease_expires_at > now()`).
2. Expired lease commit prohibition (expired leases cannot commit even if token is current).
3. Complete database-idempotence for side-effecting stages (deterministic `risk_findings` unique constraint & line item keys).
4. Deletion scope correction (preserves global canonical `medications` master & `knowledge_snapshots`; deletes only prescription-scoped records).
5. Exact parity between `risk_findings.check_type` SQL check constraints and domain `SafetyCheckType` enum (DDI & dosage-range deferred).
6. Explicit `max_retries` lifecycle semantics (1 initial execution + 3 retries -> `DEAD`).
7. Separately permissioned, durable retention vault for deletion manifests.
8. Harmonized terminology: "qualified/authorized human reviewer".

---

## 1. Architecture Principles

* **P1 — Correctness over complexity:** Simpler and provably correct beats impressive with hidden distributed failure modes.
* **P2 — Uncertainty propagates; it never rounds up:** Structurally enforced at the type and schema level. Downstream stages cannot elevate ambiguous inputs to confirmed findings.
* **P3 — Safety engine is LLM-independent:** The safety engine operates on deterministic domain rules and licensed evidence. Disabling the LLM leaves the core product fully functional.
* **P4 — Capability-aware coverage limits:** `NOT_EVALUATED != SAFE` across data model, API, and UI. Missing data or unsupported checks must never produce a clean bill of health.
* **P5 — Fenced idempotency over false exactly-once claims:** Job queue guarantees at-least-once dispatch with generation fencing tokens and idempotent stage commits for effectively-once persistence.
* **P6 — Measure before you scale:** No infrastructure component is introduced without a measured production trigger. Every architectural decision specifies a measurable reversal threshold.

---

## 2. Requirements & Regulatory Constraints

### PRD v1 Non-Negotiables
1. **Asynchronous processing:** Upload returns `202 Accepted` immediately with `document_id` and `analysis_id`.
2. **Human-in-the-loop decision support:** No finding or extraction is clinically actionable without qualified/authorized human review. Output is decision-support only.
3. **Structured uncertainty:** `FieldState` (`CLEAR`, `AMBIGUOUS`, `UNREADABLE`, `NOT_PRESENT`) propagates through extraction, normalization, and safety screening.
4. **LLM isolation:** LLM is strictly an optional commentary layer, completely disabled in V1 (`LLM_ENABLED=false`). Core structured report is the complete product.
5. **Full provenance:** Every finding, normalized medication, and knowledge record carries source name, version, timestamp, and confidence score.
6. **Controlled review routing:** Unresolved medications or ambiguous critical fields route to `REQUIRES_REVIEW` instead of forcing false normalization.
7. **Verifiable deletion:** Deletion is eventually complete across database, object storage, and backups (via an external deletion manifest stored in a separately permissioned retention vault).
8. **Preservation of global knowledge:** Deletion purges prescription-scoped data only. The global canonical `medications` master and `knowledge_snapshots` are immutable and never deleted.
9. **Zero PHI in operational logs:** Prescription images, raw OCR buffers, patient names, and medication names are stripped by logging processors.

### Regulatory Baseline: DPDPA 2023 & DPDPA Rules 2025
Prescripto is designed for compliance with the applicable provisions of the **Digital Personal Data Protection Act, 2023 (DPDPA 2023)** and the **Digital Personal Data Protection Rules, 2025 (notified November 2025)**, subject to deployment context and formal legal/security review. The architecture enforces data minimization, purpose limitation, caller-scoped access control, consent/retention tracking, and verifiable erasure workflows.

---

## 3. Workload Assumptions (V1 Baseline)

> [!NOTE]
> All figures below are engineering planning assumptions, not measured production metrics. Operational thresholds will be calibrated against Tier-B benchmarks and production telemetry.

| Dimension | Initial Assumption | Basis / Planning Target |
|---|---|---|
| Upload rate | 10–50 prescriptions / day | Single-clinic / initial pilot volume |
| Prescription image size | 2–8 MB (max 20 MB) | Mobile camera / flatbed scanner capture |
| Lines per prescription | 5–20 lines | Indian outpatient prescription variance |
| Line inference latency | 200–800 ms / line (CPU) | TrOCR / PP-OCR inference profile |
| Total analysis duration | 30–180 seconds | End-to-end pipeline execution |
| Storage per analysis | 5–15 MB | Original image + normalized region crops |
| Database rows per analysis | 50–200 rows | Document, stages, meds, candidates, findings, audit |

---

## 4. System Context & Component Architecture

```
                       PRESCRIPTO AI 2.0
                                │
                      React / Vite (SPA)
                                │
                           HTTPS / TLS
                                │
                   FastAPI Modular Monolith
                                │
        ┌───────────────────────┴───────────────────────┐
        │                                               │
   PostgreSQL 16+                              MinIO / S3 Storage
   ├── Domain Data (Medications, Analyses)     ├── Original Prescriptions
   ├── Job Queue + Fencing Leases              ├── Bounding Box Region Crops
   ├── Knowledge Snapshots & Master            └── Separately Permissioned Retention
   ├── Token Blocklist                             Vault (Audit & Deletion Manifests)
   └── Append-Only Audit Log
        │
   SELECT FOR UPDATE SKIP LOCKED
        │
   Fenced Analysis Worker (Python)
        ├── 1. Quality Gate & Ingestion
        ├── 2. Text Detection (DBNet / PP-OCRv6)
        ├── 3. Line Crops -> Recognition (TrOCR / PP-OCRv6 Candidate)
        ├── 4. Structured Field Extraction & Uncertainty Propagation
        ├── 5. Medication Master Normalization (CDSCO / RxNorm / Aliases)
        ├── 6. Capability-Aware Safety Engine (Duplicate Check / Evidence Lookup)
        └── 7. Fenced Stage Commit (Atomic Lease Validation Guarded)
```

### Omitted Distributed Infrastructure (Locked V1 Exclusions)
* **No Redis / Celery:** PostgreSQL `FOR UPDATE SKIP LOCKED` with leases and fencing tokens provides transactional queueing without dual-datastore sync issues.
* **No Kafka / Streaming:** Single-worker asynchronous processing satisfies all V1 throughput requirements.
* **No Kubernetes / Microservices:** Single container image running modular processes in Docker Compose minimizes operational failure modes.
* **No Vector Database:** PostgreSQL relational JOINs and Full-Text Search (`tsvector`) provide deterministic evidence lookup.

---

## 5. Container & Process Architecture

A single Docker image packages the entire codebase, deployed into distinct runtime processes:

```
Process 1: api              uvicorn prescripto.api.main:app --host 0.0.0.0 --port 8000
Process 2: worker           python -m prescripto.worker.main
Process 3: deletion_worker  python -m prescripto.retention.worker
```

* **API Process:** Handles authentication, upload ingestion, review management, and status polling. Target latency: `< 100ms` overhead.
* **Worker Process:** Executes the long-running analysis pipeline (30–180s) using CPU/GPU ML runtimes. Crashes are isolated from API availability.
* **Deletion Worker Process:** Executes asynchronous, multi-stage data erasure workflows and manifest verification.

---

## 6. Layered Architecture & Module Separation

To prevent API schemas from contaminating domain business logic, Prescripto enforces a strict four-layer separation:

```
[ Domain Entities & Value Objects ]  (Pure business logic, immutable models, zero I/O)
                 ↓
      [ Application DTOs ]           (Use-case orchestration data contracts)
                 ↓
     [ API Pydantic Schemas ]        (Serialization, validation, request/response format)
                 ↓
         [ OpenAPI Spec ]            (Canonical external contract generated from FastAPI)
```

```
prescripto/
├── domain/               # Pure business logic — ZERO external I/O or framework imports
│   ├── prescription/     # Prescription aggregate, LineItem, DocumentMetadata
│   ├── analysis/         # Analysis aggregate, StageResult, ExecutionToken
│   ├── medication/       # MedicationMaster, CanonicalMedication, BrandAlias
│   ├── safety/           # CheckDefinition, ProviderCapability, Evidence, Finding
│   ├── review/           # ReviewSession, ReviewDecision, ReviewAudit
│   └── uncertainty/      # FieldState, ExtractedField[T]
├── application/          # Application services & DTOs
│   ├── dtos/             # Internal transfer models
│   └── use_cases/        # ProcessPrescription, ExecuteStage, TombstoneDocument
├── api/                  # FastAPI routers, Pydantic request/response schemas, dependencies
│   ├── v1/               # Versioned route handlers
│   └── schemas/          # API-specific Pydantic schemas (separate from domain)
├── pipeline/             # Pipeline stage implementations & execution coordinator
├── ml/                   # ModelRuntime interface, adapters (PP-OCR, TrOCR), calibration
├── knowledge/            # Capability-aware KnowledgeProvider implementations
├── storage/              # S3/MinIO client, presigned URL generator, deletion manifest client
├── db/                   # SQLAlchemy models, Alembic migrations, session management
├── worker/               # Queue poller, lease heartbeat, stage fence manager
├── retention/            # DeletionJob runner, storage purger, manifest re-applier
├── auth/                 # JWT RS256 issuance/verification, RBAC, blocklist verification
├── audit/                # Typed audit event emitters & S3 export writer
└── config/               # Pydantic BaseSettings, environment validation
```

### Strict Boundary Rules
1. `domain/` has zero external dependencies (no SQLAlchemy, no FastAPI, no Boto3, no PyTorch).
2. `api/schemas/` models are distinct from `domain/` entities. Any changes to API contracts are reflected via explicit DTO mapping.
3. `pipeline/` orchestrates domain models and calls `ml/`, `knowledge/`, and `storage/`.
4. `worker/` manages job leases and database transactions, delegating business rules to `domain/`.

---

## 7. Analysis Pipeline & Fencing Execution Model

### At-Least-Once Execution with Fenced Idempotent Commits
PostgreSQL `FOR UPDATE SKIP LOCKED` handles job claiming. To guarantee safety during network partitions, slow workers, or worker crashes:
1. When Worker A claims a job, it acquires a monotonic **`lease_token`** (e.g., `101`) and sets `lease_expires_at = now() + 10 minutes`.
2. Worker A sends a heartbeat every 30 seconds, bumping `lease_expires_at` and `heartbeat_at`.
3. If Worker A hangs or dies, its lease expires (`lease_expires_at < now()`).
4. Worker B claims the expired job, increments the generation, and receives `lease_token = 102`.
5. **Atomic Lease Validation:** Every stage persistence operation validates `analysis_jobs.lease_token`, `analysis_jobs.lease_owner`, and `analysis_jobs.lease_expires_at > now()` within the **exact same transaction**.
6. **Expired Lease Rejection:** If Worker A's lease expires, even if no other worker has claimed the job yet or incremented the token, Worker A is forbidden from committing (`lease_expires_at > now()` check fails).
7. If Worker A attempts to write stage outputs with `lease_token = 101` after Worker B claims the job (`lease_token = 102`), the write is rejected with `0 rows affected`, raising `WorkerFencedError`.

```python
# Stage execution with atomic lease validation and generation fencing
def commit_stage_result(
    db: Session,
    analysis_id: UUID,
    stage_name: str,
    lease_token: int,
    lease_owner: str,
    output: dict
):
    with db.begin():
        # Validate that the worker holds the currently valid, non-expired lease
        lease_check = db.execute(
            text("""
                SELECT id FROM analysis_jobs
                WHERE analysis_id = :aid
                  AND lease_token = :token
                  AND lease_owner = :owner
                  AND lease_expires_at > now()
                  AND status = 'RUNNING'
                FOR SHARE
            """),
            {"aid": analysis_id, "token": lease_token, "owner": lease_owner}
        ).fetchone()

        if not lease_check:
            raise WorkerFencedError(
                f"Worker '{lease_owner}' with token {lease_token} has been fenced or lease has expired."
            )

        # Upsert stage output guarded by generation token
        result = db.execute(
            text("""
                INSERT INTO analysis_stages (analysis_id, stage_name, lease_token, status, output_json, completed_at)
                VALUES (:aid, :stage, :token, 'COMPLETED', :output, now())
                ON CONFLICT (analysis_id, stage_name) DO UPDATE
                SET status = 'COMPLETED',
                    lease_token = EXCLUDED.lease_token,
                    output_json = EXCLUDED.output_json,
                    completed_at = now()
                WHERE analysis_stages.lease_token <= :token
            """),
            {"aid": analysis_id, "stage": stage_name, "token": lease_token, "output": json.dumps(output)}
        )
        if result.rowcount == 0:
            raise WorkerFencedError(f"Stage commit rejected: newer stage generation already committed.")
```

### Side-Effecting Stage Database Idempotency
Every pipeline stage writing to the database is completely idempotent to ensure that duplicate job dispatch or re-runs cannot duplicate rows:
* `prescription_medications`: Enforces `UNIQUE (analysis_id, line_index)`. Re-execution updates existing line items.
* `medication_candidates`: Enforces `UNIQUE (prescription_med_id, matching_strategy, source_vocabulary)`.
* `risk_findings`: Enforces `UNIQUE (analysis_id, check_type, source_name, finding_key)`.
* Object storage: Deterministic keys (`prescriptions/{document_id}/analyses/{analysis_id}/...`) ensure that storage PUTs overwrite in place without creating orphaned files.

### Pipeline Stages & Failure Modes

| Stage | Input | Output | Failure / Error Mode | Idempotent |
|---|---|---|---|---|
| `INGESTION` | Storage key | Loaded image buffer & metadata | `FORMAT_UNSUPPORTED`, `FILE_CORRUPTED` | Yes |
| `QUALITY_CHECK` | Image buffer | Quality metrics (blur, contrast, DPI) | `QUALITY_TOO_LOW` -> routes to review | Yes |
| `TEXT_DETECTION` | Image buffer | Ordered bounding box coordinates | `DETECTION_FAILED` -> routes to review | Yes |
| `OCR_RECOGNITION` | Line crops | Raw text + model-native confidence | `OCR_FAILED` -> field marked `UNREADABLE` | Yes |
| `STRUCTURED_EXTRACTION` | OCR lines | `ExtractedField` line items with `FieldState` | `EXTRACTION_FAILED` | Yes |
| `MEDICATION_NORMALIZATION` | `ExtractedField` names | Resolved `MedicationMaster` reference / `UNRESOLVED` | `UNRESOLVED` (valid state, not exception) | Yes |
| `SAFETY_SCREENING` | Resolved medications | Capability-evaluated `RiskFinding` items | Provider timeout -> `NOT_EVALUATED` | Yes |
| `REPORT_ASSEMBLY` | All stage artifacts | Consolidated analysis record | DB constraint failure | Yes |

*Note: `UNREADABLE` fields are structurally excluded prior to Medication Normalization. `UNRESOLVED` or `AMBIGUOUS` entities are excluded prior to Safety Screening.*

---

## 8. State Machines

### 1. Analysis State Machine
```
QUEUED ──> PROCESSING ──┬──> COMPLETED         (all required fields CLEAR, 0 review triggers)
                        ├──> REQUIRES_REVIEW   (>= 1 review trigger: AMBIGUOUS, UNRESOLVED, etc.)
                        └──> FAILED            (unrecoverable pipeline or system error)

REQUIRES_REVIEW ──> REVIEWING ──┬──> REVIEWED_COMPLETE   (reviewer approved/corrected all items)
                                └──> REVIEWED_ESCALATED  (reviewer escalated to senior clinical lead)
```
* **`COMPLETED`:** Pipeline finished successfully with zero mandatory review conditions. *Output is decision-support only; never clinically actionable without qualified/authorized human reviewer review.*
* **`REQUIRES_REVIEW`:** Pipeline finished successfully, but triggered mandatory review routing rules.
* **Invalid Transitions:** `COMPLETED -> REVIEWING` (state change prohibited; voluntary audit inspection does not alter state), `FAILED -> COMPLETED` (prohibited; requires new analysis submission).

### 2. AnalysisJob State Machine & Retry Semantics
```
PENDING ──> CLAIMED ──> RUNNING ──> SUCCEEDED
   ▲           │           │
   │           │ (crash)   │ (lease expired / unhandled error)
   │           ▼           ▼
   └── [retry_count < max_retries] (Backoff: 5s -> 30s -> 2m)
               │
               ▼ [retry_count >= max_retries]
              DEAD (terminal, operator alert generated)
```

#### `max_retries` Lifecycle Semantics
* `max_retries = 3` defines the maximum allowed retry attempts following an initial execution failure or lease expiration.
* **Attempt 1 (Initial Execution):** `retry_count = 0`. If worker fails/crashes, status reset to `PENDING`, `retry_count = 1`, `backoff_until = now() + 5s`.
* **Attempt 2 (Retry 1):** `retry_count = 1`. If worker fails/crashes, status reset to `PENDING`, `retry_count = 2`, `backoff_until = now() + 30s`.
* **Attempt 3 (Retry 2):** `retry_count = 2`. If worker fails/crashes, status reset to `PENDING`, `retry_count = 3`, `backoff_until = now() + 2m`.
* **Terminal Failure (After Retry 3):** `retry_count = 3`. Upon the 4th failure (`retry_count >= max_retries`), status transitions directly to `DEAD`, lease is revoked, and a high-severity alert is dispatched to operators.

### 3. DeletionJob State Machine
```
REQUESTED ──> DB_TOMBSTONED ──> STORAGE_DELETING ──> VERIFYING ──> COMPLETE
     │                                                     │
     └─────────────────> PARTIAL_FAILURE <─────────────────┘
                                │ (exponential backoff retry)
                                ▼
```

---

## 9. Data Architecture & PostgreSQL Schema

```sql
-- Core Extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. Document Management
CREATE TABLE prescription_documents (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    uploader_id    UUID NOT NULL REFERENCES users(id),
    patient_ref    TEXT,                         -- De-identified external reference only
    storage_key    TEXT,                         -- NULL until upload verified
    file_hash_sha256 TEXT NOT NULL,
    mime_type      TEXT NOT NULL CHECK (mime_type IN ('image/jpeg', 'image/png', 'image/tiff', 'application/pdf')),
    file_size_bytes BIGINT NOT NULL CHECK (file_size_bytes > 0 AND file_size_bytes <= 20971520),
    status         TEXT NOT NULL DEFAULT 'UPLOAD_PENDING'
                   CHECK (status IN ('UPLOAD_PENDING', 'UPLOADED', 'DELETION_REQUESTED', 'DELETION_IN_PROGRESS', 'DELETED')),
    uploaded_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at     TIMESTAMPTZ
);

-- 2. Analysis Aggregate
CREATE TABLE analyses (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id      UUID NOT NULL REFERENCES prescription_documents(id),
    status           TEXT NOT NULL DEFAULT 'QUEUED'
                     CHECK (status IN ('QUEUED', 'PROCESSING', 'COMPLETED', 'REQUIRES_REVIEW',
                                       'REVIEWING', 'REVIEWED_COMPLETE', 'REVIEWED_ESCALATED', 'FAILED')),
    pipeline_version TEXT NOT NULL,
    model_snapshot_id UUID NOT NULL REFERENCES model_versions(id),
    review_required  BOOLEAN NOT NULL DEFAULT false,
    review_reasons   TEXT[] DEFAULT '{}',
    error_detail     TEXT,
    started_at       TIMESTAMPTZ,
    completed_at     TIMESTAMPTZ,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 3. Job Queue with Leases, Fencing Tokens, and Exponential Backoff
CREATE TABLE analysis_jobs (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id        UUID NOT NULL REFERENCES analyses(id),
    status             TEXT NOT NULL DEFAULT 'PENDING'
                       CHECK (status IN ('PENDING', 'CLAIMED', 'RUNNING', 'SUCCEEDED', 'FAILED', 'DEAD', 'CANCELLED')),
    lease_owner        TEXT,                     -- Worker process identifier
    lease_token        BIGINT NOT NULL DEFAULT 0,-- Monotonic generation fencing token
    lease_expires_at   TIMESTAMPTZ,
    heartbeat_at       TIMESTAMPTZ,
    retry_count        INT NOT NULL DEFAULT 0,
    max_retries        INT NOT NULL DEFAULT 3,   -- Initial attempt + 3 retries (total 4 attempts)
    backoff_until      TIMESTAMPTZ,
    last_error         TEXT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_analysis_jobs_claimable ON analysis_jobs (status, backoff_until, created_at)
    WHERE status IN ('PENDING', 'FAILED');

-- 4. Fenced Pipeline Stages
CREATE TABLE analysis_stages (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id  UUID NOT NULL REFERENCES analyses(id),
    stage_name   TEXT NOT NULL,
    lease_token  BIGINT NOT NULL DEFAULT 0,      -- Generation token of committing worker
    status       TEXT NOT NULL DEFAULT 'RUNNING'
                 CHECK (status IN ('RUNNING', 'COMPLETED', 'FAILED', 'SKIPPED')),
    output_json  JSONB,
    error_code   TEXT,
    started_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    UNIQUE (analysis_id, stage_name)
);

-- 5. Canonical Medication Master with Full Provenance (IMMUTABLE GLOBAL KNOWLEDGE)
-- Note: This table is NEVER deleted by user or prescription deletion workflows.
CREATE TABLE medications (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_name           TEXT NOT NULL,
    generic_name         TEXT NOT NULL,
    active_ingredients   TEXT[] NOT NULL,
    strength             TEXT,
    dosage_form          TEXT,
    route                TEXT,
    rxnorm_cui           TEXT,                   -- Nullable for India-specific formulations
    source_class         TEXT NOT NULL           -- 'CDSCO_REGULATORY', 'RXNORM', 'MANUFACTURER_VERIFIED', 'RESEARCH_VOCABULARY', 'MANUAL_EXPERT'
                         CHECK (source_class IN ('CDSCO_REGULATORY', 'RXNORM', 'MANUFACTURER_VERIFIED', 'RESEARCH_VOCABULARY', 'MANUAL_EXPERT')),
    source_version       TEXT NOT NULL,
    verification_status  TEXT NOT NULL DEFAULT 'UNVERIFIED'
                         CHECK (verification_status IN ('VERIFIED_AUTHORITY', 'PROVISIONAL', 'EXPERT_CONFIRMED', 'UNVERIFIED')),
    provenance_metadata  JSONB NOT NULL DEFAULT '{}',
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (brand_name, generic_name, strength, dosage_form, route)
);
CREATE INDEX idx_medications_search ON medications USING gin (to_tsvector('english', brand_name || ' ' || generic_name));

-- 6. Structured Extraction Line Items (Prescription-Scoped)
CREATE TABLE prescription_medications (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id          UUID NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
    line_index           INT NOT NULL,
    name_raw             TEXT,
    name_state           TEXT NOT NULL CHECK (name_state IN ('CLEAR', 'AMBIGUOUS', 'UNREADABLE', 'NOT_PRESENT')),
    name_confidence      REAL,
    strength_raw         TEXT,
    strength_state       TEXT NOT NULL CHECK (strength_state IN ('CLEAR', 'AMBIGUOUS', 'UNREADABLE', 'NOT_PRESENT')),
    strength_confidence  REAL,
    dose_raw             TEXT,
    dose_state           TEXT NOT NULL CHECK (dose_state IN ('CLEAR', 'AMBIGUOUS', 'UNREADABLE', 'NOT_PRESENT')),
    dose_confidence      REAL,
    frequency_raw        TEXT,
    frequency_state      TEXT NOT NULL CHECK (frequency_state IN ('CLEAR', 'AMBIGUOUS', 'UNREADABLE', 'NOT_PRESENT')),
    frequency_confidence REAL,
    route_raw            TEXT,
    route_state          TEXT NOT NULL CHECK (route_state IN ('CLEAR', 'AMBIGUOUS', 'UNREADABLE', 'NOT_PRESENT')),
    route_confidence     REAL,
    duration_raw         TEXT,
    duration_state       TEXT NOT NULL CHECK (duration_state IN ('CLEAR', 'AMBIGUOUS', 'UNREADABLE', 'NOT_PRESENT')),
    duration_confidence  REAL,
    UNIQUE (analysis_id, line_index)             -- Idempotency key for extraction stage
);

-- 7. Candidate Normalization Matches (Prescription-Scoped)
CREATE TABLE medication_candidates (
    id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prescription_med_id    UUID NOT NULL REFERENCES prescription_medications(id) ON DELETE CASCADE,
    analysis_id            UUID NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
    extracted_text         TEXT NOT NULL,
    matching_strategy      TEXT NOT NULL,        -- 'EXACT', 'FUZZY_LEVENSHTEIN', 'PHONETIC_DOUBLE_METAPHONE', 'ALIAS_LOOKUP'
    candidate_score        REAL NOT NULL,
    source_vocabulary      TEXT NOT NULL,
    resolved_medication_id UUID REFERENCES medications(id),
    resolution_status      TEXT NOT NULL CHECK (resolution_status IN ('RESOLVED', 'UNRESOLVED', 'AMBIGUOUS')),
    UNIQUE (prescription_med_id, matching_strategy, source_vocabulary)
);

-- 8. Capability-Aware Safety Findings (Prescription-Scoped)
-- V1 Executable check types: 'DUPLICATE_MEDICATION', 'EVIDENCE_LOOKUP', 'ADVERSE_EFFECT'
-- DDI ('KNOWN_INTERACTION') and 'DOSAGE_RANGE' are deferred in V1.
CREATE TABLE risk_findings (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id           UUID NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
    check_type            TEXT NOT NULL CHECK (check_type IN ('DUPLICATE_MEDICATION', 'EVIDENCE_LOOKUP', 'ADVERSE_EFFECT')),
    finding_key           TEXT NOT NULL,          -- Deterministic idempotency hash/key (e.g., md5(med_ids + source))
    finding_status        TEXT NOT NULL
                          CHECK (finding_status IN ('CONFIRMED_BY_SOURCE', 'POTENTIAL', 'INSUFFICIENT_EVIDENCE', 'NOT_EVALUATED', 'REQUIRES_REVIEW')),
    medication_ids        UUID[] NOT NULL DEFAULT '{}',
    evidence_text         TEXT,
    source_name           TEXT NOT NULL,
    source_version        TEXT NOT NULL,
    knowledge_snapshot_id UUID REFERENCES knowledge_snapshots(id),
    confidence_score      REAL,
    check_timestamp       TIMESTAMPTZ NOT NULL DEFAULT now(),
    not_evaluated_reason  TEXT,
    CONSTRAINT chk_not_evaluated_reason
        CHECK (finding_status != 'NOT_EVALUATED' OR not_evaluated_reason IS NOT NULL),
    UNIQUE (analysis_id, check_type, source_name, finding_key) -- Idempotency key for safety stage
);

-- 9. Machine Learning Model Registry & Calibration Snapshots
CREATE TABLE model_versions (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name              TEXT NOT NULL,
    model_version           TEXT NOT NULL,
    checkpoint_sha256       TEXT NOT NULL,
    artifact_storage_key    TEXT NOT NULL,
    framework               TEXT NOT NULL,
    license                 TEXT NOT NULL,
    registered_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (model_name, model_version)
);

CREATE TABLE calibration_snapshots (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_version_id        UUID NOT NULL REFERENCES model_versions(id),
    calibration_dataset_ver TEXT NOT NULL,
    review_threshold        REAL NOT NULL,
    calibration_curve_data  JSONB NOT NULL,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 10. Knowledge Source Snapshots (IMMUTABLE GLOBAL KNOWLEDGE)
CREATE TABLE knowledge_snapshots (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_name    TEXT NOT NULL,
    source_version TEXT NOT NULL,
    license_mode   TEXT NOT NULL CHECK (license_mode IN ('COMMERCIAL_PERMISSIVE', 'RESEARCH_ONLY', 'PUBLIC_DOMAIN')),
    snapshot_date  TIMESTAMPTZ NOT NULL,
    record_count   INT NOT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 11. Clinical Reviews (Prescription-Scoped)
CREATE TABLE reviews (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id  UUID NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
    reviewer_id  UUID NOT NULL REFERENCES users(id),
    status       TEXT NOT NULL DEFAULT 'PENDING_ASSIGNMENT'
                 CHECK (status IN ('PENDING_ASSIGNMENT', 'ASSIGNED', 'IN_PROGRESS', 'SUBMITTED', 'ESCALATED')),
    corrections  JSONB,
    notes        TEXT,
    submitted_at TIMESTAMPTZ,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 12. Deletion Jobs & Token Denylist
CREATE TABLE deletion_jobs (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id      UUID NOT NULL REFERENCES prescription_documents(id),
    status           TEXT NOT NULL DEFAULT 'REQUESTED'
                     CHECK (status IN ('REQUESTED', 'DB_TOMBSTONED', 'STORAGE_DELETING', 'VERIFYING', 'COMPLETE', 'PARTIAL_FAILURE')),
    manifest_written BOOLEAN NOT NULL DEFAULT false,
    retry_count      INT NOT NULL DEFAULT 0,
    error_detail     TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE token_blocklist (
    jti         TEXT PRIMARY KEY,
    user_id     UUID NOT NULL REFERENCES users(id),
    expires_at  TIMESTAMPTZ NOT NULL,
    revoked_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_token_blocklist_expiry ON token_blocklist (expires_at);

-- 13. Append-Only Audit Schema
CREATE SCHEMA IF NOT EXISTS audit;
CREATE TABLE audit.events (
    id            BIGSERIAL PRIMARY KEY,
    event_type    TEXT NOT NULL,
    actor_id      UUID,
    resource_type TEXT NOT NULL,
    resource_id   UUID NOT NULL,
    occurred_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    metadata      JSONB NOT NULL DEFAULT '{}'
);
```

---

## 10. Job System & Concurrency Control

### Job Claim Query (FOR UPDATE SKIP LOCKED + Lease Generation)
```sql
BEGIN;
SELECT id, analysis_id, lease_token, retry_count
FROM analysis_jobs
WHERE status = 'PENDING'
  AND (backoff_until IS NULL OR backoff_until <= now())
ORDER BY created_at ASC
LIMIT 1
FOR UPDATE SKIP LOCKED;

-- Worker generates new lease token: old_token + 1
UPDATE analysis_jobs
SET status = 'RUNNING',
    lease_owner = :worker_id,
    lease_token = lease_token + 1,
    lease_expires_at = now() + INTERVAL '10 minutes',
    heartbeat_at = now(),
    updated_at = now()
WHERE id = :job_id;
COMMIT;
```

### Expired-Job Recovery & Exponential Backoff
A scheduled sweeper query (or claim pre-pass) detects abandoned jobs where `status IN ('CLAIMED', 'RUNNING') AND lease_expires_at < now()`:

```sql
UPDATE analysis_jobs
SET status = CASE WHEN retry_count + 1 >= max_retries THEN 'DEAD' ELSE 'PENDING' END,
    retry_count = retry_count + 1,
    backoff_until = now() + (
        CASE
            WHEN retry_count = 0 THEN INTERVAL '5 seconds'
            WHEN retry_count = 1 THEN INTERVAL '30 seconds'
            ELSE INTERVAL '2 minutes'
        END
    ),
    lease_owner = NULL,
    lease_expires_at = NULL,
    last_error = 'Lease expired due to worker timeout or crash',
    updated_at = now()
WHERE status IN ('CLAIMED', 'RUNNING')
  AND lease_expires_at < now();
```

---

## 11. ML Architecture & OCR Pipeline

```
Raw Image
   │
[ Text Detection: PP-OCRv6 / DBNet ]
   │
Line Bounding Boxes & Rotated Rectangles
   │
[ Precise Line-Crop Extraction ] (Never send full page to TrOCR)
   │
[ Recognition: TrOCR-Handwritten / PP-OCRv6 Candidates ]
   │
Raw Text Tokens + Model-Native Confidence
   │
[ Temperature Scaling / Calibration Snapshot ]
   │
Calibrated Confidence Score [0.0, 1.0]
```

### Abstract Model Runtime Interface
```python
class ModelRuntime(ABC):
    @abstractmethod
    def load(self, checkpoint_path: str) -> None: ...

    @abstractmethod
    def detect_regions(self, image: np.ndarray) -> list[BoundingBox]: ...

    @abstractmethod
    def recognize_line(self, crop: np.ndarray) -> RawRecognitionResult: ...

    @property
    @abstractmethod
    def model_version_id(self) -> UUID: ...

@dataclass(frozen=True)
class CalibratedInferenceResult:
    text: str
    raw_score: float
    calibrated_confidence: float
    field_state: FieldState
    model_version_id: UUID
    latency_ms: int
```

### Dataset Classification
* **MedOCR-Vision (2,462 samples):** MIT licensed (1,000 handwritten prescriptions, 36 OMR, 426 lab reports, 1,000 invoices). Classified as **Tier A research/training candidate**, *NOT Tier B ground truth*.
* **Bangladesh Prescription Dataset (200 images):** Classified as **Candidate dataset only**. Requires license verification, annotation audit, de-identification inspection, and domain assessment before catalog entry.
* **Tier B Ground Truth Benchmark (200–500 prescriptions):** Legally obtained, de-identified, dual-annotated with expert qualified/authorized human reviewer adjudication. Evaluates CER, WER, field extraction accuracy, and critical error rates with 95% confidence intervals.

### Model Winner Selection Strategy
The architecture **locks the Detection -> Line-Crop -> Recognition pipeline**, but **does not hardcode a model winner**. The winning model (`PP-OCRv6`, `TrOCR-base-handwritten`, `TrOCR-large-handwritten`, or domain fine-tuned checkpoint) is determined strictly by measured performance on the Tier B benchmark.

---

## 12. Uncertainty Propagation Model

```python
class FieldState(str, Enum):
    CLEAR       = "CLEAR"        # High confidence, above calibrated threshold
    AMBIGUOUS   = "AMBIGUOUS"    # Low confidence or conflicting candidates -> routes to review
    UNREADABLE  = "UNREADABLE"   # Illegible text -> structurally excluded from downstream stages
    NOT_PRESENT = "NOT_PRESENT"  # Field absent from document

@dataclass(frozen=True)
class ExtractedField(Generic[T]):
    value: Optional[T]
    state: FieldState
    confidence: float
    raw_text: str

    def propagate(self) -> "ExtractedField[T]":
        if self.state == FieldState.UNREADABLE:
            raise UncertaintyPropagationError("UNREADABLE field must not reach normalization or safety stages.")
        if self.state != FieldState.CLEAR:
            return ExtractedField(self.value, FieldState.AMBIGUOUS, self.confidence, self.raw_text)
        return self
```

### Type-Safe Invariants
1. `UNREADABLE` fields trigger an immediate domain error if passed to Normalization or Safety screening.
2. If any input field is `AMBIGUOUS`, the resulting clinical finding cannot exceed `POTENTIAL` or `REQUIRES_REVIEW` (never `CONFIRMED_BY_SOURCE`).
3. Mypy `--strict` type-checking is enforced across all domain packages.

---

## 13. Medication Master & Normalization Architecture

RxNorm is primarily US-focused; therefore, Prescripto implements an internal **Medication Master** backed by regulatory data, verified aliases, and RxNorm mapping where available.

```
Extracted Line Item Text
          │
[ Candidate Generation (Exact, Levenshtein, Double Metaphone) ]
          │
[ Internal Medication Master ] ─── CDSCO Regulatory Data (Approved FDCs, New Drugs)
          │                    ─── Verified Indian Brand/Generic Aliases
          │                    ─── Expert Curated Formulations
          │
[ RxNorm CUI Mapping ] (Optional enrichment; nullable for Indian-only drugs)
          │
Resolved Entity OR UNRESOLVED (triggers review routing, never forced guess)
```

* **Candidate Vocabulary (e.g., 69K dataset):** Used strictly as an OCR post-processing / fuzzy candidate dictionary. **Not treated as clinical truth.**
* **Medication Master Provenance:** Every canonical entry records `source_class`, `source_version`, `verification_status`, and `provenance_metadata`.

---

## 14. Capability-Aware Safety Engine

Safety providers are modeled around explicit clinical capabilities. A provider cannot answer a check it does not support.

```
[ CheckDefinition ] ──> [ ProviderCapability ] ──> [ Evidence Lookup ] ──> [ RiskFinding ]
```

```python
class SafetyCheckType(str, Enum):
    DUPLICATE_MEDICATION = "DUPLICATE_MEDICATION"
    EVIDENCE_LOOKUP      = "EVIDENCE_LOOKUP"
    ADVERSE_EFFECT       = "ADVERSE_EFFECT"
    # Note: KNOWN_INTERACTION (comprehensive DDI) and DOSAGE_RANGE are deferred in V1

class ProviderCapability(str, Enum):
    CAN_CHECK_DUPLICATES  = "CAN_CHECK_DUPLICATES"
    CAN_LOOKUP_EVIDENCE   = "CAN_LOOKUP_EVIDENCE"
    CAN_CHECK_ADVERSE_ADV = "CAN_CHECK_ADVERSE_ADV"

class SafetyProvider(ABC):
    @property
    @abstractmethod
    def provider_id(self) -> str: ...

    @property
    @abstractmethod
    def capabilities(self) -> set[ProviderCapability]: ...

    @abstractmethod
    def evaluate(self, check: SafetyCheckType, meds: list[CanonicalMedication]) -> FindingResult: ...
```

### V1 Safety Check Scope
1. **`DUPLICATE_MEDICATION`:** Evaluated locally against the Canonical Medication Master. Fully supported.
2. **`EVIDENCE_LOOKUP` / `ADVERSE_EFFECT`:** Lookups against openFDA or local references where verified.
3. **Comprehensive Drug-Drug Interaction (`KNOWN_INTERACTION`):** **Deferred in V1.** Prescripto V1 does not claim comprehensive DDI coverage due to the absence of an authoritative, commercially licensed Indian DDI dataset.
4. **`DOSAGE_RANGE`:** **Deferred in V1.** Not supported until a verified, licensed dosage reference dataset is integrated.
5. **SIDER 4.1 Exclusion:** SIDER is licensed under CC BY-NC-SA 4.0. **SIDER is strictly research-only (`LICENSE_MODE=RESEARCH_ONLY`) and completely excluded from production/commercial builds.**

If a provider lacks capability or times out, it produces `finding_status = NOT_EVALUATED` with an explicit `not_evaluated_reason` (never a false `SAFE` or `NO_INTERACTION`).

---

## 15. LLM Architecture (V1 Locked OFF)

* **V1 Decision:** **`LLM_ENABLED = false`**. The structured JSON report is the complete product. Eliminating LLM inference in V1 removes latency, non-determinism, and patient data exposure risks.
* **Future V1.x / V2 Architecture (Optional Commentary Layer):**
  * **Input Boundary:** Frozen `ExplanationContext` containing non-PHI UUIDs, sanitized medication names, pre-computed findings, and mandatory coverage disclaimers.
  * **Untrusted Data Invariant:** OCR text is treated as untrusted data, never instructions. Prompt injection sanitizers strip instruction tokens (`system:`, `IGNORE PREVIOUS`, `###`).
  * **Zero Authority:** The LLM cannot create findings, alter medication identities, change confidence scores, or issue safety clearances.
  * **Output Validation:** Rigid JSON schema validation (`additionalProperties: false`), finding UUID cross-checking, and clinical clearance phrase rejection.

---

## 16. API Architecture & Security

### External API Contract
FastAPI automatically generates `/openapi.json`. The frontend client is strictly generated from this schema.

| Method | Endpoint | Description | Response Status |
|---|---|---|---|
| `POST` | `/api/v1/auth/token` | Obtain JWT access + refresh tokens | `200 OK` |
| `POST` | `/api/v1/auth/refresh` | Refresh access token (checks blocklist) | `200 OK` |
| `POST` | `/api/v1/prescriptions` | Upload prescription image | `202 Accepted` |
| `GET` | `/api/v1/prescriptions` | List user prescriptions (paginated) | `200 OK` |
| `GET` | `/api/v1/analyses/{id}` | Get processing status & stage progress | `200 OK` |
| `GET` | `/api/v1/analyses/{id}/result` | Full structured result (completed states only) | `200 OK` |
| `POST` | `/api/v1/analyses/{id}/review` | Submit reviewer decisions | `200 OK` |
| `DELETE` | `/api/v1/prescriptions/{id}` | Request deletion of document & derived data | `202 Accepted` |
| `GET` | `/api/v1/health` | Service health & storage/DB liveness | `200 OK` |

### Security Controls
1. **Authentication:** JWT RS256. Access token TTL: 15 minutes. Refresh token TTL: 7 days. Token revocation denylist in PostgreSQL.
2. **Role-Based Access Control (RBAC):**
   * `OPERATOR`: Ingest prescriptions, view owned prescriptions and analyses.
   * `REVIEWER`: View assigned analyses, submit review corrections.
   * `ADMIN`: Manage users, view system metrics, inspect append-only audit events.
3. **Application-Mediated Storage:** Buckets are completely private. Clients access images via time-limited presigned GET URLs (**TTL: 60 seconds**). Presigned URLs are bearer capabilities and are never logged or stored.
4. **Upload Validation:** Strict MIME magic-byte validation (JPEG, PNG, TIFF, PDF), 20 MB size limit, server-side generated UUID file paths, PDF JavaScript stripping, and image array decoding before disk persistence.

---

## 17. Privacy, Data Lifecycle & Separately Permissioned Retention Vault

```
DELETE /api/v1/prescriptions/{id}
   │
[ 1. Permission & Active Analysis Concurrency Check ]
   │
[ 2. DB Tombstone: status = 'DELETION_IN_PROGRESS', deleted_at = now() ]
   │
[ 3. Storage Deletion: Purge original & region crops under prescriptions/{id}/ ]
   │
[ 4. Cascade DB Erasure: Anonymize/delete rows in analyses, stages, medications ]
   │    (NOTE: Global canonical `medications` master is PRESERVED)
   │
[ 5. Write Manifest: s3://retention-vault/deletion-manifest/{doc_id}.json ]
   │    (Stored in separately permissioned, durable retention vault)
   │
[ 6. Verification Pass & Audit Event Emission ]
```

> [!IMPORTANT]
> **Preservation of Global Knowledge Master:** Deletion cascades strictly purge prescription-scoped records (`prescription_documents`, `analyses`, `analysis_stages`, `prescription_medications`, `medication_candidates`, `risk_findings`, `reviews`). The global canonical `medications` master and `knowledge_snapshots` tables are NEVER deleted.

### Backup Restoration & Retention Vault Guarantee
PostgreSQL database backups are retained for disaster recovery. Restoring an immutable database backup will inadvertently restore previously deleted patient records. To prevent zombie data:
1. Every successful deletion writes an immutable marker to a **separately permissioned and durable retention storage vault** (e.g., `s3://prescripto-retention-manifests/retention/deletion-manifest/{document_id}.json`) isolated by IAM access policies from regular application read/write tenants.
2. The disaster recovery runbook mandates executing the **Manifest Re-Application Script** immediately following any database restore:
   * Queries all IDs in the isolated retention vault.
   * Re-applies tombstones and purges any restored relational rows or storage objects.

---

## 18. Audit Durability & Observability

* **Logical Audit:** Append-only PostgreSQL table `audit.events` recording `event_type`, `actor_id`, `resource_id`, and non-PHI metadata.
* **Durable Export:** Hourly scheduled worker exports signed, encrypted JSONL audit logs to cold object storage (`audit-archive/{year}/{month}/{day}/`).
* **Structured Logging:** `structlog` with automated field filtering. Prescription images, extracted names, OCR text, and PHI are stripped before log writing.
* **Prometheus Metrics:** Queue depth, stage latencies, worker heartbeats, calibration triggers, and deletion outcomes.

---

## 19. Architecture Decision Records (ADRs)

### ADR-01: Modular Monolith Architecture
* **Decision:** Single deployable codebase with strictly separated domain modules.
* **Rationale:** Eliminates distributed network serialization, partial network partitions, and dual-phase commits at V1 scale.
* **Reversal Trigger:** Specific ML or API module requires independent autoscaling due to sustained, measured compute divergence.

### ADR-02: PostgreSQL as Primary Datastore & Knowledge Store
* **Decision:** PostgreSQL 16+ for relational entities, job queues, medication master, and audit logs.
* **Rationale:** Relational integrity, transactional DDL, CHECK constraints, FK cascading, JSONB indexing, and Full-Text Search.
* **Reversal Trigger:** Sustained write throughput exceeds 10,000 writes/sec or graph traversal queries become a measured bottleneck.

### ADR-03: S3-Compatible Object Storage
* **Decision:** MinIO for local development; AWS S3 (or S3-compliant store) for production using `boto3`.
* **Rationale:** Decouples binary prescription storage from the relational database; enables deterministic keys and short-lived presigned URLs.

### ADR-04: PostgreSQL Job Queue with Fencing Tokens & Atomic Lease Validation
* **Decision:** PostgreSQL `FOR UPDATE SKIP LOCKED` with monotonic generation fencing tokens, lease heartbeats, and atomic validation on stage commits.
* **Rationale:** Provides transactional job claiming with at-least-once execution and fenced, idempotent stage commits without introducing Redis or Celery.
* **Reversal Trigger:** Sustained lock contention wait time exceeds 100ms under load, or queue depth exceeds 100 with SLA violations.

### ADR-05: Domain DTO Layering & OpenAPI Contract
* **Decision:** Four-tier data boundary (`Domain Entities -> Application DTOs -> API Schemas -> OpenAPI`).
* **Rationale:** Prevents API schema changes from inadvertently breaking domain business logic or vice-versa.

### ADR-06: OCR Pipeline Abstraction & Benchmark-Driven Selection
* **Decision:** Two-stage detection and line-crop recognition pipeline. Model winner selected via Tier B benchmark.
* **Rationale:** Line-crop extraction prevents model hallucination. Benchmarking prevents premature lock-in to an unverified OCR checkpoint.

### ADR-07: Internal Medication Master with Multi-Source Provenance
* **Decision:** Build an internal canonical Medication Master combining CDSCO regulatory lists, verified aliases, and RxNorm CUI mapping.
* **Rationale:** RxNorm lacks comprehensive Indian brand formulations. Provenance tracking ensures every entry has a verifiable source class.

### ADR-08: Capability-Aware Safety Engine (No V1 DDI Promise)
* **Decision:** Safety checks are executed only against providers with explicit capabilities. Comprehensive DDI and dosage-range checks are deferred in V1.
* **Rationale:** Avoids false clinical clearance. `NOT_EVALUATED` is returned whenever evidence or capability is absent.

### ADR-09: LLM Disabled in V1 Production
* **Decision:** Set `LLM_ENABLED = false` for V1.
* **Rationale:** The structured extraction report is the product. Disabling LLM eliminates non-deterministic hallucination, latency, and DPA privacy risks.

### ADR-10: Verifiable Deletion with Separately Permissioned Manifest Vault
* **Decision:** Multi-stage asynchronous deletion with an external deletion manifest stored in a separately permissioned retention vault.
* **Rationale:** Guarantees that disaster-recovery database restores will not reinstate previously deleted patient records while strictly preserving global canonical medication masters.

### ADR-11: Full-Text Search Before Vector Database
* **Decision:** Use PostgreSQL `tsvector` and GIN indexing for knowledge and medication lookups.
* **Rationale:** Relational keyword matching is deterministic and sufficient. Vector DB deferred until large unstructured corpora require semantic recall.

### ADR-12: Application-Mediated Object Access
* **Decision:** Presigned GET URLs with a 60-second TTL.
* **Rationale:** Enforces strict authorization without proxying multi-megabyte image payloads through API workers.

### ADR-13: JWT Authentication with PostgreSQL Denylist
* **Decision:** RS256 signed JWTs with a 15-minute access TTL and a PostgreSQL-backed token blocklist for refresh grants.
* **Rationale:** Stateless API verification with revocation control during token refresh. Reversal trigger: Enterprise multi-tenant SSO -> OAuth2/OIDC.

### ADR-14: SIDER Commercial Exclusion (Research-Only)
* **Decision:** SIDER 4.1 is restricted to research environments (`LICENSE_MODE=RESEARCH_ONLY`) and completely excluded from commercial builds.
* **Rationale:** CC BY-NC-SA 4.0 license prohibits commercial usage.

### ADR-15: Expired-Job Exponential Backoff Recovery & Retry Semantics
* **Decision:** Expired job leases automatically reset to `PENDING` with exponential backoff (~5s, ~30s, ~2m) up to `max_retries` (total 4 attempts) before transitioning to `DEAD`.
* **Rationale:** Prevents worker crash loops from thrashing database resources or stalling the queue.

---

## 20. Deferred Architecture & Reversal Triggers

| Component / Feature | Status | Pre-Condition / Reversal Trigger to Introduce |
|---|---|---|
| **Redis / Celery** | DEFERRED | Measured PostgreSQL lock wait > 100ms sustained across multiple workers |
| **Comprehensive DDI Engine** | DEFERRED | Authoritative, commercially licensed Indian DDI dataset acquired |
| **Dosage-Range Checking** | DEFERRED | Verified, licensed pediatric/adult dosage reference database integrated |
| **Vector Database (pgvector / Qdrant)** | DEFERRED | Large unstructured clinical evidence corpus added where FTS recall is measurably insufficient |
| **LLM Explanation Generation** | DEFERRED (OFF) | Business requirement + DPA signed + prompt injection benchmark passed |
| **Kafka / Event Streaming** | DEFERRED | Multiple independent consumer systems requiring divergent processing SLAs |
| **Kubernetes** | DEFERRED | Multi-node horizontal scaling required across distributed infrastructure |
| **OAuth2 / OIDC / SSO** | DEFERRED | Multi-tenant enterprise hospital/clinic SSO requirements |

---

## 21. Research & Experiment Roadmap

The architecture is fully locked. The following research experiments operate within the locked architectural interfaces:

1. **Experiment 1 — OCR Recognition Model Winner:** Benchmark `PP-OCRv6`, `TrOCR-base-handwritten`, `TrOCR-large-handwritten`, and fine-tuned checkpoints on the Tier B ground truth dataset (CER, WER, field accuracy, 95% CIs).
2. **Experiment 2 — Normalization Matching Strategy:** Compare exact string matching, Levenshtein distance, Double Metaphone phonetic matching, and alias lookup accuracy on Indian brand names.
3. **Experiment 3 — Confidence Calibration & Review Thresholds:** Determine optimal review routing cutoffs on the calibrated Tier B reliability curves.
4. **Experiment 4 — VLM Verification Feasibility:** Evaluate whether a Vision-Language Model (`PaddleOCR-VL` or `Qwen2.5-VL`) materially improves low-confidence review routing without unacceptable latency.
5. **Experiment 5 — Licensed Safety Sources:** Identify and evaluate authoritative, commercially licensed Indian drug interaction and dosage reference datasets.

---

## 22. References

* **PostgreSQL 18 Explicit Locking & SKIP LOCKED:** https://www.postgresql.org/docs/current/explicit-locking.html
* **Digital Personal Data Protection Act, 2023 & Rules 2025 (India):** Ministry of Electronics and Information Technology (MeitY).
* **NLM RxNorm Documentation & Scope:** https://www.nlm.nih.gov/research/umls/rxnorm/docs/
* **openFDA API Disclaimer & Terms:** https://open.fda.gov/apis/disclaimer/
* **SIDER 4.1 Side Effect Resource (EMBL):** http://sideeffects.embl.de/
* **FastAPI Framework & OpenAPI Specification:** https://fastapi.tiangolo.com/
* **Prescripto PRD v1:** [prd_v1.md](file:///c:/Users/HP/OneDrive/Desktop/Prescripto-2.0/docs/prd_v1.md)
