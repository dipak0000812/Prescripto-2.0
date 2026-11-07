# Prescripto AI 2.0 — Project Structure & Source Code Map Dossier

**Document ID:** `DOC-12-STRUCT`  
**Classification:** Academic Engineering Dossier  
**Canonical Spec Reference:** Workspace File System Hierarchy  
**Date of Extraction:** November 4, 2026  

---

## 1. Top-Level Repository Organization

```
Prescripto-2.0/
├── .github/                      # GitHub workflows and Copilot configurations
│   └── workflows/
│       └── ci.yml                # Automated CI pipeline for linting and test runs
├── backend/                      # Complete FastAPI modular monolith backend
├── docs/                         # Formal architectural, clinical, and evaluation specifications
├── ml/                           # ML research scripts, PaddleOCR adapter, and OCR benchmarks
├── project-documentation/        # Academic semester project technical extraction dossier
├── research/                     # Evaluation protocol, RxHandBD dataset scripts
├── web/                          # React 19 + TypeScript + Vite + TailwindCSS frontend
├── .dockerignore                 # Docker build ignore filters
├── .env.example                  # Reference environment template
├── .gitignore                    # Git version control ignore rules
├── docker-compose.yml            # Multi-service local orchestration
├── Dockerfile                    # Root multi-stage Docker build specification
├── OPENAPI.yaml                  # Canonical machine-readable REST API contract
├── README.md                     # High-level product summary and documentation index
├── render.yaml                   # Infrastructure-as-code specification for Render cloud
└── vercel.json                   # Root SPA client-side rewrite rules for Vercel
```

---

## 2. Backend Subsystem Map (`backend/`)

```
backend/
├── alembic.ini                   # Alembic database migration environment configuration
├── pyproject.toml                # Build system metadata and pytest configuration
├── requirements.txt              # Pinned Python package dependencies
├── prescripto/                   # Core application source package
│   ├── api/                      # Presentation layer: FastAPI HTTP delivery
│   │   ├── main.py               # ASGI application entrypoint, middleware, SPA fallback
│   │   └── v1/
│   │       ├── routers/          # Modular API routers
│   │       │   ├── analyses.py   # Status, extraction results, clinician review, inline edits
│   │       │   ├── auth.py       # OAuth2 token, doctor login, patient OTP, refresh, /me
│   │       │   ├── health.py     # System health, PostgreSQL probe (/health/db), readiness
│   │       │   ├── patients.py   # Patient search, registration, medical timeline
│   │       │   └── prescriptions.py # Ingestion, listings, details, retention deletion
│   │       └── schemas/          # Pydantic request/response validation schemas
│   ├── application/              # Application orchestration layer
│   │   ├── dtos/                 # Data transfer objects crossing layer boundaries
│   │   ├── services/
│   │   │   ├── llm_explainer.py  # Plain-language patient explanation service
│   │   │   └── medication_search.py # Trigram fuzzy search against CDSCO Master
│   │   └── use_cases/            # Pure business use cases (IngestPrescription, SubmitReview)
│   ├── audit/
│   │   └── logger.py             # Zero-PHI structured logging with strict whitelist filter
│   ├── auth/                     # Authentication & cryptographic security
│   │   ├── crypto.py             # Bcrypt hashing, RS256 JWT encoding, public key decoding
│   │   ├── dependencies.py       # FastAPI auth guards (get_current_user, require_role)
│   │   ├── exceptions.py         # Domain authentication exceptions
│   │   └── service.py            # User credential verification, sliding-window OTP rate limit
│   ├── config/
│   │   └── settings.py           # Pydantic BaseSettings, database URL sanitization, RSA auto-heal
│   ├── db/                       # Relational database persistence
│   │   ├── base.py               # SQLAlchemy DeclarativeBase and utc_now helper
│   │   ├── session.py            # Engine creation, connection pooling, get_db dependency
│   │   ├── models/               # SQLAlchemy ORM entity models
│   │   │   ├── analysis.py       # Analysis, AnalysisJob, AnalysisStage
│   │   │   ├── audit.py          # AuditEvent immutable trail
│   │   │   ├── document.py       # PrescriptionDocument
│   │   │   ├── enums.py          # FieldState, Role, FindingStatus, SafetyCheckType
│   │   │   ├── idempotency.py    # IdempotencyRecord
│   │   │   ├── medication.py     # Medication (Master), PrescriptionMedication, Candidate
│   │   │   ├── patient.py        # Patient demographic and allergy history
│   │   │   ├── registry.py       # ModelVersion, CalibrationSnapshot
│   │   │   ├── retention.py      # DeletionJob, TokenBlocklist
│   │   │   ├── review.py         # Review sign-off decisions and notes
│   │   │   ├── safety.py         # RiskFinding
│   │   │   └── users.py          # User accounts and credentials
│   │   └── migrations/           # Alembic versioned migrations
│   │       ├── env.py            # Migration runtime environment
│   │       └── versions/
│   │           ├── 0001_initial_schema.py      # Core tables and enum types
│   │           ├── 0002_idempotency_records.py # Upload idempotency table
│   │           └── 0003_add_patients_table.py  # Patient table and Patient role enum
│   ├── domain/                   # Pure business domain layer (Zero external dependencies)
│   │   ├── analysis/             # Analysis aggregate roots and state transitions
│   │   ├── medication/           # CanonicalMedication and normalization models
│   │   ├── prescription/         # Prescription entity boundaries
│   │   ├── recognition/          # Recognized token structures
│   │   ├── review/               # Review trigger evaluation rules
│   │   ├── safety/               # Deterministic clinical safety screening engines
│   │   │   ├── allergy.py        # Patient allergen contraindication cross-referencer
│   │   │   ├── dosage.py         # Single-dose threshold ceiling evaluator
│   │   │   ├── duplicate.py      # Canonical duplicate and active ingredient overlap
│   │   │   └── models.py         # DomainRiskFinding, SafetyCheckType, FindingStatus
│   │   └── uncertainty/          # 4-State FieldState uncertainty propagation models
│   ├── knowledge/
│   │   └── providers.py          # Pharmacological knowledge provider interfaces (CDSCO)
│   ├── ml/                       # Machine learning adapters and runtimes
│   │   ├── extraction.py         # Rule-based entity parsing & form boilerplate stripper
│   │   ├── rapid_runtime.py      # Offline RapidOCR CPU execution runtime
│   │   ├── recognition_providers.py # Provider factory (Gemini Vision / RapidOCR fallback)
│   │   └── runtime.py            # MockModelRuntime and RemoteMLClient
│   ├── pipeline/
│   │   └── engine.py             # 8-Stage sequential pipeline stage handlers
│   ├── retention/
│   │   └── worker.py             # DPDPA 2023 verifiable deletion engine & cryptographic shredder
│   ├── storage/
│   │   ├── client.py             # Boto3 S3/MinIO client, HMAC presigned signer, path sanitizer
│   │   └── exceptions.py         # StorageObjectNotFoundException, StorageException
│   └── worker/                   # Asynchronous queue worker subsystem
│       ├── coordinator.py        # PipelineCoordinator orchestrating stage transitions
│       ├── heartbeat.py          # HeartbeatManager daemon thread renewing leases
│       ├── main.py               # WorkerRunner entrypoint and signal handling
│       └── queue.py              # QueuePoller (FOR UPDATE SKIP LOCKED)
├── scripts/                      # Operational and database seeding scripts
│   ├── create_user.py            # Seeds primary system administrator account
│   ├── generate_keys.py          # Generates 2048-bit RSA PEM keypair
│   ├── seed_medications.py       # Seeds 107 master medications into the database
│   └── seed_users.py             # Seeds demo doctor, reviewer, and operator accounts
└── tests/                        # Automated testing suite (197 test cases)
    ├── conftest.py               # Pytest harness, in-memory SQLite and PostgreSQL savepoints
    ├── contract/                 # OpenAPI parity tests
    ├── eval_set/                 # 10 synthetic prescription images and ground truth JSON
    ├── integration/              # API, database, and pipeline integration tests
    └── unit/                     # Pure domain, cryptographic, and safety tests
```

---

## 3. Frontend Subsystem Map (`web/`)

```
web/
├── package.json                  # Frontend dependencies (React 19, Vite 8, Tailwind 4)
├── tsconfig.json                 # TypeScript compiler configuration
├── vite.config.ts                # Vite bundler, Tailwind plugin, and proxy configuration
├── vercel.json                   # Client-side routing rewrites (/* -> /index.html)
├── index.html                    # Single-page application entrypoint
├── public/                       # Static public assets (favicon.svg, logo.svg, icons.svg)
└── src/
    ├── App.tsx                   # Main React component, router configuration, route guards
    ├── index.css                 # Global CSS and Tailwind design tokens
    ├── main.tsx                  # React application DOM root mounter
    ├── api/                      # Typed API clients and HTTP communication
    │   ├── analyses.ts           # Analysis polling and clinical review API calls
    │   ├── auth.ts               # Login, OTP dispatch, token refresh API calls
    │   ├── client.ts             # Axios instance, Bearer token injection, X-Request-ID, fallback URL
    │   ├── health.ts             # Health diagnostic API calls
    │   ├── patients.ts           # Patient search and history API calls
    │   └── prescriptions.ts      # Prescription upload and listing API calls
    ├── components/               # Reusable UI components
    │   ├── Badges.tsx            # Confidence badges (CLEAR, AMBIGUOUS, UNREADABLE)
    │   ├── CoverageDisclaimerCard.tsx # Explicit clinical coverage disclaimer
    │   ├── DeleteConfirmModal.tsx # DPDPA deletion confirmation modal
    │   ├── EditMedicineModal.tsx # Clinician inline medication correction modal
    │   ├── ErrorBoundary.tsx     # React component error boundary
    │   ├── LanguageSwitcher.tsx  # Multilingual dropdown (EN, HI, GU, MR)
    │   ├── Layout.tsx            # Navigation header, user profile, brand banner
    │   ├── MedicineHeroCard.tsx  # Patient-friendly medication timing card
    │   ├── PrescriptionImageModal.tsx # Fullscreen scan inspection viewer
    │   ├── StageProgressBar.tsx  # 8-stage visual pipeline execution tracker
    │   └── ui/                   # Primitive design system components
    │       ├── AlertBanner.tsx   # Alert warning banners
    │       ├── Button.tsx        # Accessible styled buttons
    │       ├── Card.tsx          # Card container wrappers
    │       ├── EmptyState.tsx    # Empty queue / list illustrations
    │       ├── HelpTooltip.tsx   # Clinical guidance tooltips
    │       ├── Input.tsx         # Accessible form inputs
    │       ├── LoadingState.tsx  # Skeleton loaders and animated spinners
    │       ├── StatusChip.tsx    # Status pills (COMPLETED, REQUIRES_REVIEW)
    │       └── Toast.tsx         # Ephemeral notification toasts
    ├── context/                  # React global state providers
    │   ├── AuthContext.tsx       # Authentication state, login/logout, active user
    │   └── LanguageContext.tsx   # Multilingual localization provider (EN, HI, GU, MR)
    ├── pages/                    # Route page views
    │   ├── AnalysisDetailPage.tsx # Dual-pane clinician review workspace
    │   ├── HelpPage.tsx          # Clinical safety guide and FAQs
    │   ├── HomePage.tsx          # Landing page and portal navigation
    │   ├── LoginPage.tsx         # Staff credential & patient mobile OTP login
    │   ├── PatientPortalPage.tsx # Patient medication schedule with voice audio
    │   ├── PatientSearchPage.tsx # Clinician patient search directory
    │   ├── PatientTimelinePage.tsx # Chronological patient prescription history
    │   ├── PrescriptionsListPage.tsx # Ingested prescriptions table
    │   ├── ReviewQueuePage.tsx   # Clinician review queue
    │   ├── SystemHealthPage.tsx  # Real-time health diagnostic dashboard
    │   └── UploadPrescriptionPage.tsx # Ingestion portal with file drag-and-drop
    └── types/
        └── api.ts                # TypeScript interfaces matching backend OpenAPI DTOs
```

