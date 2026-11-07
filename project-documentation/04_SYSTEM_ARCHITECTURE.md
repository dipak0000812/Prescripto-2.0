# Prescripto AI 2.0 — System Architecture Dossier

**Document ID:** `DOC-04-ARCH`  
**Classification:** Academic Engineering Dossier  
**Canonical Spec Reference:** [docs/Architecture.md](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/docs/Architecture.md), [docs/PROJECT-SPEC.md](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/docs/PROJECT-SPEC.md)  
**Date of Extraction:** November 4, 2026  

---

## 1. Architectural Philosophy and Style

Prescripto AI 2.0 is engineered as a **Hexagonal / Clean Architecture (Modular Monolith)** coupled to an **Asynchronous Fenced Worker Subsystem**:

```
┌────────────────────────────────────────────────────────────────────────┐
│                          PRESENTATION LAYER                            │
│  React 19 SPA (Vercel)  /  FastAPI RESTful Web Endpoints (Render)      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Calls Use Cases
┌───────────────────────────────────▼────────────────────────────────────┐
│                          APPLICATION LAYER                             │
│  Use Cases (IngestPrescription, SubmitReview, RequestDeletion, etc.)   │
│  Application Services (MedicationSearchService, LLMExplainerService)   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Orchestrates
┌───────────────────────────────────▼────────────────────────────────────┐
│                            DOMAIN LAYER                                │
│  Pure Domain Logic (Zero External Framework Dependencies):             │
│  - 4-State Field Uncertainty Model (CLEAR, AMBIGUOUS, UNREADABLE, etc.)│
│  - Deterministic Safety Engines (Duplicates, Allergies, Dosages)       │
│  - Review Trigger Rule Evaluators                                      │
└───────────────────────────────────▲────────────────────────────────────┘
                                    │ Implements Ports
┌───────────────────────────────────┴────────────────────────────────────┐
│                        INFRASTRUCTURE LAYER                            │
│  - Database: SQLAlchemy ORM, Alembic Migrations, PostgreSQL 16 Engine │
│  - Queue: PostgreSQL FOR UPDATE SKIP LOCKED with Fencing Tokens        │
│  - Object Store: S3/MinIO Boto3 Client with HMAC-SHA256 Signing       │
│  - Perception: Gemini Vision SDK, Local RapidOCR ONNX Runtime          │
│  - Audit: Zero-PHI Structlog Filter with Whitelist Enforcement         │
└────────────────────────────────────────────────────────────────────────┘
```

### Architectural Guarantees
1. **Separation of Concerns**: The Domain layer (`backend/prescripto/domain/`) has zero dependencies on FastAPI, SQLAlchemy, or Boto3. It can be compiled and verified completely in isolation.
2. **Deterministic Safety Decoupling**: Probabilistic vision models (Gemini / PaddleOCR) are strictly confined to perception. No neural model makes final decisions on drug-drug interactions, duplicate therapies, or dosage violations.
3. **Audit Immutability**: Once an analysis is finalized by a clinician sign-off (`REVIEWED_COMPLETE`), the database locks the record against any subsequent programmatic modification.

---

## 2. End-to-End System Component Architecture

```mermaid
flowchart TD
    subgraph Client Tier
        Browser[Clinician / Patient Web Browser]
        VercelEdge[Vercel CDN Edge Network]
        Browser -->|Fetches Static Assets| VercelEdge
    end

    subgraph API Gateway & Presentation Tier
        RenderLB[Render Cloud Reverse Proxy]
        FastAPIApp[FastAPI Modular Monolith :8000]
        CORS[CORS Middleware: allow_origin_regex]
        Audit[Zero-PHI Structlog Middleware]
        
        Browser -->|HTTPS REST API Calls| RenderLB
        RenderLB -->|Proxy Headers: X-Forwarded-Proto| FastAPIApp
        FastAPIApp --> CORS
        FastAPIApp --> Audit
    end

    subgraph Data & Storage Tier
        Postgres[(PostgreSQL 16 Managed DB)]
        S3Store[(MinIO / AWS S3 Object Store)]
    end

    subgraph Asynchronous Worker Tier
        WorkerEngine[Fenced Background Worker Engine]
        Heartbeat[Heartbeat Thread: Lease Renewer]
        StageEngine[8-Stage Sequential Pipeline Engine]
        
        WorkerEngine -->|Claim Job: FOR UPDATE SKIP LOCKED| Postgres
        WorkerEngine --> Heartbeat
        WorkerEngine --> StageEngine
    end

    subgraph Perception & AI Services
        GeminiCloud[Google Gemini Vision API: 3.5-Flash / 3.1-Flash-Lite]
        LocalRapid[Local RapidOCR ONNX Runtime on CPU]
    end

    FastAPIApp -->|Persists Document & Job| Postgres
    FastAPIApp -->|Streams Image Bytes| S3Store
    StageEngine -->|Stage 1: Fetch Scan| S3Store
    StageEngine -->|Stage 3: Vision Perception| GeminiCloud
    GeminiCloud -.->|On Quota / Timeout Failover| LocalRapid
    StageEngine -->|Stage 6-8: Persist Results| Postgres
```

---

## 3. Asynchronous Execution & Generation Fencing Model

To prevent duplicate job processing and race conditions without adding Redis or Celery overhead, Prescripto AI 2.0 leverages PostgreSQL's native row-level concurrency primitives:

```mermaid
sequenceDiagram
    autonumber
    participant W1 as Worker Node 1
    participant DB as PostgreSQL (analysis_jobs)
    participant W2 as Worker Node 2
    participant HB as Heartbeat Thread

    Note over DB: Job 101 status = QUEUED

    W1->>DB: SELECT * FROM analysis_jobs WHERE status='QUEUED'<br/>ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1
    DB-->>W1: Grants Row Lock on Job 101
    W1->>DB: UPDATE analysis_jobs SET status='RUNNING', worker_id='worker-1',<br/>lease_token='lease-v1', heartbeat_at=NOW(), expires_at=NOW() + 10m
    W1->>HB: Launch Heartbeat Thread (interval: 30s)

    Note over W1: Worker 1 executes Stage 1 - 4

    W2->>DB: SELECT * FROM analysis_jobs WHERE status='QUEUED'<br/>FOR UPDATE SKIP LOCKED LIMIT 1
    Note over W2: Skips Job 101 (Locked by Worker 1)
    DB-->>W2: Returns 0 rows (No available jobs)

    loop Every 30 Seconds
        HB->>DB: UPDATE analysis_jobs SET heartbeat_at=NOW(),<br/>expires_at=NOW() + 10m WHERE id=101 AND lease_token='lease-v1'
        DB-->>HB: Lease Successfully Renewed
    end

    W1->>DB: Commit Stage 8 & Mark Analysis Status = REQUIRES_REVIEW
    W1->>HB: Stop Heartbeat Thread
    W1->>DB: UPDATE analysis_jobs SET status='COMPLETED'
```

### The Worker Fencing Guarantee (`WorkerFencedError`)
If Worker 1 experiences a long GC pause or network partition exceeding `lease_seconds` (10 minutes), Worker 2 can reclaim the job. When Worker 1 recovers and attempts to commit its next stage result, the query validates:
```sql
UPDATE analysis_jobs 
SET heartbeat_at = NOW() 
WHERE id = :job_id AND lease_token = :my_token;
```
If `rowcount == 0`, Worker 1 raises `WorkerFencedError`, immediately rolls back its transaction, and ceases execution, guaranteeing that stale workers never corrupt pipeline state.

---

## 4. Uncertainty Propagation Architecture

The pipeline enforces an explicit mathematical contract across all 8 stages:

```mermaid
stateDiagram-v2
    [*] --> Ingested
    Ingested --> QualityChecked
    
    QualityChecked --> ClearField: Image Sharp (Var > 100) & Conf >= 0.85
    QualityChecked --> AmbiguousField: Image Borderline or Conf 0.50..0.84
    QualityChecked --> UnreadableField: Image Blurry (Var < 100) or Conf < 0.50

    state ClearField {
        [*] --> HighConfidenceExtraction
        HighConfidenceExtraction --> ExactFormularyMatch: Matches 1 Verified CDSCO Item
        ExactFormularyMatch --> ResolvedMedication: ResolutionStatus = RESOLVED
    }

    state AmbiguousField {
        [*] --> LowConfidenceExtraction
        LowConfidenceExtraction --> AmbiguousMatch: Matches Multiple Candidates
        AmbiguousMatch --> RequiresReview: ResolutionStatus = AMBIGUOUS
    }

    state UnreadableField {
        [*] --> MaskedStroke
        MaskedStroke --> ExcludedFromSafetyRules: Value = Masked
        ExcludedFromSafetyRules --> RequiresReview: ResolutionStatus = UNRESOLVED
    }

    ResolvedMedication --> SafetyScreening
    SafetyScreening --> ReportAssembled
    RequiresReview --> ReportAssembled
    
    ReportAssembled --> ClinicianSignOff: Status = REQUIRES_REVIEW
    ClinicianSignOff --> Approved: Clinician Confirms / Overrides
    Approved --> [*]
```

---

## 5. Deployment Topology

The production architecture utilizes a resilient multi-cloud split topology:

```
┌───────────────────────────────────────┐
│         VERCEL EDGE NETWORK           │
│  - Static SPA Web Hosting             │
│  - Global CDN & Brotli Compression    │
│  - Rewrites: /* -> /index.html        │
│  - Inlined VITE_API_BASE_URL          │
└──────────────────┬────────────────────┘
                   │ HTTPS API Traffic
┌──────────────────▼────────────────────┐
│      RENDER CLOUD (Oregon, US)        │
│                                       │
│  [Web Service: prescripto-2-0]        │
│  - Docker Multi-Stage Container       │
│  - Uvicorn ASGI on Port 10000         │
│  - Background Worker Daemon Thread    │
│                                       │
│  [Managed Relational Database]        │
│  - PostgreSQL 16 Server               │
│  - SSL Mode: Required                 │
│  - Connection Pool Timeout: 30s       │
└──────────────────┬────────────────────┘
                   │
┌──────────────────▼────────────────────┐
│        EXTERNAL AI PROVIDERS          │
│  - Google Gemini 3.5 Flash API        │
│  - Google Gemini 3.1 Flash Lite API   │
└───────────────────────────────────────┘
```

