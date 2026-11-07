# 17. Evidence and Technical Accuracy Register — Prescripto AI 2.0

This register audits every significant technical claim, architectural mechanism, security protocol, database structure, and deployment behavior across the Prescripto AI 2.0 project.

---

## 1. Evidence Classification Standards

Every claim in this register is classified using the following strict taxonomy:

| Classification Code | Description |
| :--- | :--- |
| **`VERIFIED IN SOURCE CODE`** | Confirmed by direct inspection of active source code in `backend/` or `web/`. |
| **`VERIFIED IN CONFIGURATION`** | Confirmed in configuration files (`alembic.ini`, `settings.py`, `package.json`, `Dockerfile`). |
| **`VERIFIED THROUGH EXECUTION OR TEST`** | Confirmed by executing automated test suites, scripts, or runtime commands. |
| **`VERIFIED IN DEPLOYMENT`** | Confirmed via live HTTP probe against Render backend or Vercel frontend. |
| **`DOCUMENTED BUT NOT INDEPENDENTLY VERIFIED`** | Present in specification documents (`docs/`) but lacking active code implementation. |
| **`HISTORICAL DEVELOPMENT INFORMATION`** | Recovered from Git commit history, pull request records, or prior conversation context. |
| **`PLANNED FEATURE`** | Identified in architectural roadmaps for future iterations; not currently implemented. |
| **`UNKNOWN / NEEDS CONFIRMATION`** | Institutional, academic, or personal details that cannot be determined from the repository. |

---

## 2. Comprehensive Technical Claim Audit Matrix

| Claim ID | System Area | Specific Claim / Feature | Evidence Classification | Supporting File Path / Class / Function / Output | Notes & Discrepancies |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **CLM-001** | Image Quality | Pre-flight blur detection uses OpenCV Laplacian variance with threshold $\ge 100.0$. | `VERIFIED IN SOURCE CODE` | `backend/prescripto/domain/rules/image_quality.py` (`assess_image_quality`, `cv2.Laplacian`) | Verified: returns `IMAGE_TOO_BLURRY` if variance $< 100.0$. |
| **CLM-002** | Image Quality | Pre-flight exposure detection flags mean pixel intensity $< 40$ or $> 220$. | `VERIFIED IN SOURCE CODE` | `backend/prescripto/domain/rules/image_quality.py` | Verified: returns `IMAGE_UNDEREXPOSED` or `IMAGE_OVEREXPOSED`. |
| **CLM-003** | AI Perception | Primary handwriting OCR uses Gemini 3.5 Flash; secondary uses Gemini 3.1 Flash-Lite. | `VERIFIED IN SOURCE CODE` | `backend/prescripto/ml/recognition_providers.py` (`GeminiFlash35Provider`, `GeminiFlash31LiteProvider`) | Verified: calls `google-genai` SDK with structured Pydantic response schema. |
| **CLM-004** | AI Perception | Local offline fallback uses RapidOCR ONNX runtime on CPU. | `VERIFIED IN SOURCE CODE` | `backend/prescripto/ml/rapid_runtime.py` (`RapidOCRRuntime`) | Verified: instantiated if cloud API keys are absent or rate-limited. |
| **CLM-005** | Uncertainty Model | System implements a 4-state field-level confidence taxonomy (`CLEAR`, `AMBIGUOUS`, `UNREADABLE`, `NOT_PRESENT`). | `VERIFIED IN SOURCE CODE` | `backend/prescripto/domain/entities/uncertainty.py` (`FieldConfidenceState`) | Verified: prevents silent hallucination; no numerical averaging. |
| **CLM-006** | Safety Engine | Duplicate active ingredient detection checks for therapeutic redundancy across brand names. | `VERIFIED IN SOURCE CODE` | `backend/prescripto/domain/rules/duplicate_therapy.py` (`DuplicateTherapyRule`) | Verified: tested with *Augmentin* + *Amoxicillin* duplicate detection. |
| **CLM-007** | Safety Engine | Maximum daily dosage calculation detects single-dose and cumulative daily overflows. | `VERIFIED IN SOURCE CODE` | `backend/prescripto/domain/rules/dosage_safety.py` (`DosageCeilingRule`) | Verified: computes `strength * frequency` vs. `max_daily_dose_mg`. |
| **CLM-008** | Safety Engine | Allergy cross-matching flags medications contra-indicated by patient allergy history. | `VERIFIED IN SOURCE CODE` | `backend/prescripto/domain/rules/allergy_cross_match.py` (`AllergyContraindicationRule`) | Verified: checks active ingredients against `patient_allergies` table. |
| **CLM-009** | Worker Concurrency | Distributed worker queue uses PostgreSQL row locks (`FOR UPDATE SKIP LOCKED`). | `VERIFIED IN SOURCE CODE` | `backend/prescripto/worker/queue.py` (`fetch_next_job`) | Verified: enables multi-worker scaling without Redis/Celery. |
| **CLM-010** | Worker Concurrency | Distributed worker implements generation fencing tokens to prevent split-brain processing. | `VERIFIED IN SOURCE CODE` | `backend/prescripto/worker/fence.py` (`GenerationFencingCoordinator`, `WorkerFencedError`) | Verified: leases abort if generation token is incremented by another worker. |
| **CLM-011** | Security / Auth | Doctor and staff authentication uses RS256 asymmetric cryptographic signatures with 2048-bit RSA keys. | `VERIFIED IN SOURCE CODE` | `backend/prescripto/config/settings.py` (`ensure_jwt_keys`), `backend/prescripto/application/services/auth.py` | Verified: auto-generates valid RSA keypair if not configured in environment. |
| **CLM-012** | Security / Auth | Password hashing uses bcrypt with salted work factor. | `VERIFIED IN SOURCE CODE` | `backend/prescripto/application/services/auth.py` (`passlib.context.CryptContext`, `schemes=["bcrypt"]`) | Verified: secure password derivation. |
| **CLM-013** | Security / Auth | System enforces 4-tier RBAC (`doctor`, `reviewer`, `patient`, `admin`). | `VERIFIED IN SOURCE CODE` | `backend/prescripto/domain/entities/user.py` (`UserRole`), `backend/prescripto/api/v1/routers/auth.py` | Verified: role guards on all critical endpoints. |
| **CLM-014** | Privacy / DPDPA | System provides verifiable hard-deletion complying with DPDPA 2023. | `VERIFIED IN SOURCE CODE` | `backend/prescripto/application/use_cases/delete_prescription.py` | Verified: deletes storage binary, scrubs database record, and writes audit record. |
| **CLM-015** | Observability | Zero-PHI Structlog filter sanitizes patient names, phone numbers, and images from log output. | `VERIFIED IN SOURCE CODE` | `backend/prescripto/config/logging.py` (`sanitize_phi_filter`) | Verified: intercepts logs before console/file output. |
| **CLM-016** | Database Design | PostgreSQL schema contains 16 relational tables with Alembic migrations `0001` through `0003`. | `VERIFIED IN SOURCE CODE` | `backend/prescripto/db/models/`, `backend/prescripto/db/migrations/versions/` | Verified: complete foreign key cascading, unique constraints, indices. |
| **CLM-017** | Clinical Formulary | Active formulary is seeded with 107 verified medications. | `VERIFIED IN SOURCE CODE` | `backend/scripts/seed_medications.py` | Verified: exactly 107 drug rows inserted during initial seed. |
| **CLM-018** | Frontend UX | Clinician dual-pane interface features side-by-side zoom/pan document viewer and extraction editor. | `VERIFIED IN SOURCE CODE` | `web/src/pages/DoctorReview.tsx` | Verified: React 18 SPA with Tailwind styling. |
| **CLM-019** | Frontend UX | Patient portal supports 4 regional languages (English, Hindi, Marathi, Gujarati) with voice narration. | `VERIFIED IN SOURCE CODE` | `web/src/pages/PatientPortal.tsx` | Verified: integrates `window.speechSynthesis` for audio playback. |
| **CLM-020** | Automated Tests | Repository contains 197 automated test cases across unit, database, integration, and security phases. | `VERIFIED THROUGH EXECUTION OR TEST` | `backend/scripts/run_phase1_api_suite.py` through `run_phase5_performance_suite.py` | Verified: 197 tests executed and passed during Phase 1–5 test suite run. |
| **CLM-021** | Deployment | Backend is deployed on Render as a Docker service (`https://prescripto-2-0.onrender.com`). | `VERIFIED IN DEPLOYMENT` | HTTP GET `https://prescripto-2-0.onrender.com/` returns 200 OK | Verified live in Render production environment. |
| **CLM-022** | Deployment | Health check endpoints exist at `/health` and `/health/db`. | `VERIFIED IN DEPLOYMENT` | HTTP GET `https://prescripto-2-0.onrender.com/health` returns status `healthy` | Verified: reports PostgreSQL connection pool status and API version. |
| **CLM-023** | Deployment | Frontend client automatically falls back to `https://prescripto-2-0.onrender.com` if VITE env is unset. | `VERIFIED IN SOURCE CODE` | `web/src/api/client.ts` (`DEFAULT_API_BASE`) | Commit `1bc8e6c`: prevents Vercel 404 proxy misconfigurations. |
| **CLM-024** | Integration | HL7 FHIR v4.0.1 direct export to hospital EHRs. | `PLANNED FEATURE` | `project-documentation/14_LIMITATIONS_AND_FUTURE_SCOPE.md` | Not implemented in active codebase; documented as Phase 3 future scope. |
| **CLM-025** | Clinical Formulary | Full 15,000+ national drug formulary with `pg_trgm` fuzzy matching. | `PLANNED FEATURE` | `project-documentation/14_LIMITATIONS_AND_FUTURE_SCOPE.md` | Currently restricted to 107 seeded medications. |
| **CLM-026** | Academic Metadata | College name, supervisor name, student roll numbers, and submission date. | `UNKNOWN / NEEDS CONFIRMATION` | N/A | Requires human project team / supervisor confirmation. |
| **CLM-027** | Development Status | Backend API and router integration is 100% complete and deployed (previously listed as "pending" in early PPT). | `VERIFIED IN SOURCE CODE` | `backend/prescripto/api/main.py`, routers in `backend/prescripto/api/v1/routers/` | Contradicts outdated PPT; verified active in repo and on Render. |
| **CLM-028** | Development Status | Database schema and Alembic migrations are 100% complete (previously listed as "to be finalized" in early PPT). | `VERIFIED IN SOURCE CODE` | `backend/prescripto/db/models/`, `backend/prescripto/db/migrations/versions/` | 16 tables, 3 migrations, tested in `run_phase2_database_suite.py`. |
| **CLM-029** | Development Status | Multimodal vision & OCR perception pipeline is 100% complete (previously listed as "being configured" in early PPT). | `VERIFIED IN SOURCE CODE` | `backend/prescripto/ml/recognition_providers.py`, `rapid_runtime.py` | Tri-tier Gemini 3.5 / 3.1-Lite / RapidOCR operational. |
| **CLM-030** | Development Status | Asynchronous pipeline workers with fencing tokens are 100% complete (previously listed as "unintegrated" in early PPT). | `VERIFIED IN SOURCE CODE` | `backend/prescripto/worker/queue.py`, `fence.py`, `main.py` | Row locks + monotonic fencing fully implemented. |
| **CLM-031** | Development Status | Deterministic clinical safety engine is 100% complete (previously listed as "to be designed" in early PPT). | `VERIFIED IN SOURCE CODE` | `backend/prescripto/domain/rules/` | Duplicate active ingredients, daily dosage ceilings, and allergy matching. |
| **CLM-032** | Development Status | React frontend with clinician dual-pane and patient voice portal is 100% complete (previously listed as "0%" in early PPT). | `VERIFIED IN SOURCE CODE` | `web/src/pages/DoctorReview.tsx`, `PatientPortal.tsx`, `UploadPrescription.tsx` | Complete React 18 SPA deployed on Vercel. |

---

## 3. Discrepancy and Reconciliation Report

During the comprehensive repository audit, four discrepancies between early documentation / presentations and implemented code were identified and reconciled:

1. **Development Completion vs. Outdated Presentation (PPT)**:
   - *Documentation Discrepancy*: The preliminary presentation slides (PPT) and early gap analysis documents (such as `docs/ROADMAP_TO_100.md`) reflected an initial architectural baseline where backend integration, database integration, OCR experimentation, pipeline workers, and safety screening were listed as remaining work.
   - *Implemented Reality*: Subsequent engineering cycles fully completed, tested, integrated, and deployed all of these modules. The backend has 21 API endpoints, the database contains 16 relational tables with Alembic migrations, the ML engine has a tri-tier perception fallback, the worker queue is fully operational with row locks and fencing tokens, the safety engine enforces 3 deterministic checks, the frontend has dedicated doctor review and patient multilingual voice portals, and 197 automated test cases pass.
   - *Resolution*: Canonical reconciliation provided in [`19_DEVELOPMENT_COMPLETION_AND_STATUS_CORRECTION.md`](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/project-documentation/19_DEVELOPMENT_COMPLETION_AND_STATUS_CORRECTION.md). The academic report must reflect the completed implementation, not the outdated preliminary presentation.

2. **Database Engine: SQLite vs. PostgreSQL 16**:
   - *Documentation Discrepancy*: Early task phase notes in `docs/` mentioned local SQLite file persistence (`sqlite:///prescripto.db`).
   - *Implemented Reality*: The production codebase is architected for PostgreSQL 16, utilizing PostgreSQL-specific concurrency constructs (`FOR UPDATE SKIP LOCKED`). When deployed on Render or running locally with PostgreSQL, full row locking is enforced. An automatic path sanitizer was added in `settings.py` (commit `56678f4`) to gracefully handle fallback SQLite paths.
   - *Resolution*: Documented accurately as a PostgreSQL-first architecture with dev/test SQLite compatibility.

3. **Perception Engine: Pure Tesseract vs. Multimodal Gemini + RapidOCR Fallback**:
   - *Documentation Discrepancy*: Early draft architectural diagrams listed "Tesseract OCR" as the primary perception engine.
   - *Implemented Reality*: Inspection of `backend/prescripto/ml/` revealed zero Tesseract dependencies. The actual system implements a tri-tier architecture using Google Gemini 3.5 Flash as primary, Gemini 3.1 Flash-Lite as secondary, and RapidOCR ONNX as tertiary offline fallback.
   - *Resolution*: All architectural documentation and literature reviews reflect the actual Gemini/RapidOCR implementation.

4. **Patient Mobile Authentication: Live SMS Gateway vs. Mock OTP**:
   - *Documentation Discrepancy*: Some functional requirement specifications implied real-time SMS delivery of OTPs to Indian mobile numbers.
   - *Implemented Reality*: Inspection of `backend/prescripto/api/v1/routers/auth.py` confirmed that OTP generation currently operates with a mock SMS handler accepting fixed OTP `123456` in testing environments.
   - *Resolution*: Accurately documented in `14_LIMITATIONS_AND_FUTURE_SCOPE.md` as an architectural limitation requiring telecom gateway integration for production.

