# Prescripto AI 2.0 — Senior Engineering Read-Only Audit Report

**Audit Date:** 2026-10-29  
**Auditor Role:** Senior Systems & Security Engineer  
**Mode:** Strictly Read-Only (No source code modified)  
**Target Architecture:** React 19 / Vite SPA, FastAPI Modular Monolith (`/api/v1`), PostgreSQL Queue + Worker, MinIO Object Storage, Google Gemini 3.8 Flash + RapidOCR ONNX fallback, Clinical Decision Support Engine.

---

## 1. Executive Summary

- **Overall System Health:** **78%**  
  The core architecture, distributed PostgreSQL worker fencing, MinIO ingestion, RapidOCR ONNX fallback, safety screening rules, and React 19 frontend are implemented and largely functional.
- **Can it run end-to-end today:** **YES**  
  Verified live via real database, MinIO object storage, RapidOCR ONNX inference, and pipeline execution on `sample_prescription.png`.
- **Top 5 Critical Blockers:**
  1. **Runtime NameError in Clinical Summary:** `backend/prescripto/api/v1/routers/analyses.py:144,150` crashes with `NameError: name 'HTTPException' is not defined` on 404/auth failure.
  2. **Runtime AttributeError in Patient Timeline:** `backend/prescripto/api/v1/routers/patients.py:266,269` queries non-existent `Review.action` and `Review.reviewed_at` attributes, crashing the patient history page.
  3. **Critical IDOR & Data Leak in Patient Endpoints:** `backend/prescripto/api/v1/routers/patients.py:94,158` has no role or ownership check; any patient logged in via OTP can view or search all other patients' full medical history.
  4. **Fragile Gemini Fallback Exception Handling:** `backend/prescripto/pipeline/engine.py:150` catches only Quota, Auth, and Timeout errors, causing model unavailable or malformed JSON responses to crash the worker job instead of falling back.
  5. **Docs vs. Code Architectural Split:** `docs/Architecture.md` (ADR-06, ADR-09, ADR-14) explicitly mandates local-only OCR with zero external LLM calls, whereas the code defaults to cloud-based Google Gemini 3.8 Flash Vision.

---

## 2. What Runs vs. What Doesn't

### Execution Commands & Live Results

| Target Component | Exact Command Executed | Result | Details / Output / Error Message |
|---|---|---|---|
| **Frontend Build** | `npm --prefix web run build` | **PASS** | `tsc && vite build` passed cleanly in 1.16s. Generated `dist/assets/index-Bc8R3Sso.js` (526 kB). Warning: bundle chunk size exceeds 500 kB. |
| **Backend Test Suite** | `.venv\Scripts\python.exe -m pytest backend/tests` | **PASS** | `174 passed, 6 skipped, 3 warnings in 41.82s`. 6 concurrency tests skipped because PostgreSQL URL was not configured in `TEST_DATABASE_URL` during hermetic run. |
| **ML Test Suite** | `.venv\Scripts\python.exe -m pytest ml/tests` | **PASS** | `20 passed, 4 warnings in 1.05s`. Tests OCR preprocessing and span extraction. |
| **Backend Type Checker** | `.venv\Scripts\mypy.exe backend/prescripto` | **FAIL** | Exit code 1. `Found 46 errors in 17 files`. Caught runtime bugs: missing `HTTPException` in `analyses.py`, invalid `Review` fields in `patients.py`, and type mismatches in `openfda.py` and `duplicate.py`. |
| **Container Engine** | `docker ps` | **FAIL** | `failed to connect to docker API: The system cannot find the file specified`. Docker Desktop Linux engine was not running on the host. |
| **PostgreSQL Database** | Direct TCP via `psycopg2` (`localhost:5435`) | **PASS** | Host port 5435 active. Connected successfully. Verified `medications` table contains 117 seeded records. |
| **MinIO Storage** | Direct S3 via `boto3` (`localhost:9000`) | **PASS** | Host port 9000 active. Connected successfully. Default bucket `prescripto` ensured and operational. |
| **API Web Server** | `http://localhost:8000/api/v1/health` | **BLOCKED** | Refused connection on port 8000 (server not started as background daemon). Successfully imported `prescripto.api.main:app` in Python. |
| **End-to-End Pipeline** | `.venv\Scripts\python.exe backend/scripts/run_demo_pipeline.py` | **PASS** | Real execution on `sample_prescription.png`: image stored in MinIO -> document `85ebd020...` created -> job `0ad261ef...` queued -> claimed by `demo-runner-01` -> all 8 canonical pipeline stages executed with RapidOCR ONNX -> extracted Amoxicillin (500mg), Paracetamol (650mg), Cetirizine (10mg) -> normalized against Medication Master (1.0 exact match) -> status `REQUIRES_REVIEW` set -> `Worker Success: True`. |

---

## 3. Feature Status Matrix

| Feature | Status | Concrete Evidence (File & Line / Command) |
|---|---|---|
| **Login / Auth (Token, Doctor, OTP)** | **WORKING** | `backend/prescripto/api/v1/routers/auth.py:25-103`. Verified by `test_auth_api.py` and `test_otp_and_doctor_auth.py`. Issues valid RS256 JWT access and refresh token pairs; blocks revoked refresh tokens in DB. |
| **Image Upload + Validation + Storage** | **WORKING** | `backend/prescripto/application/use_cases/ingest_prescription.py:39-90`. Validates JPEG/PNG/TIFF magic bytes, rejects active PDFs, enforces 20MB limit, stores in MinIO with SHA-256 deduplication. |
| **Job Queue + Worker Processing** | **WORKING** | `backend/prescripto/worker/queue.py:88-164`. Implements PostgreSQL `FOR UPDATE SKIP LOCKED` claiming, fencing tokens, lease heartbeats, and exponential recovery. Proven live by `run_demo_pipeline.py`. |
| **Image Quality Check** | **WORKING** | `backend/prescripto/pipeline/engine.py:80-120`. Inspects dimensions (<400px), blank contrast (<5), Laplacian blur threshold (100.0), and brightness exposure (20-255). Triggers `review_required=True` on failure. |
| **Recognition (Gemini & RapidOCR)** | **PARTIAL** | `backend/prescripto/ml/recognition_providers.py:432-700`. Gemini Vision and RapidOCR ONNX both implemented, but fallback in `engine.py:150` ignores model unavailable / malformed JSON errors, failing the job. |
| **Structured Extraction + Schema Validation** | **WORKING** | `backend/prescripto/pipeline/engine.py:239-335`. Separates genuine medication orders from hospital boilerplate, vitals, symptoms, and diagnoses. Correctly extracted 3 drugs in demo test. |
| **Medication Master Normalization** | **PARTIAL** | `backend/prescripto/pipeline/engine.py:355-430`. Normalizes via `MedicationSearchService` with exact and fuzzy matching, but `backend/scripts/seed_medications.py:11` hardcodes SQLite (`prescripto.db`) rather than PostgreSQL. |
| **Duplicate / Safety Checks** | **WORKING** | `backend/prescripto/pipeline/engine.py:435-528`. Executes exact duplicate checks (`duplicate.py`), patient allergen contraindications (`allergy.py`), and dosage ceiling evaluations (`dosage.py`), persisting `RiskFinding` rows. |
| **Review Page (Image, Edit, Confirm)** | **WORKING** | `web/src/pages/AnalysisDetailPage.tsx:72-120,705-765`. Displays presigned prescription image via modal/card, provides inline modal to correct medication lines via `PATCH /analyses/{id}/medications`, and submits review decisions. |
| **Clinical Summary Endpoint + UI Label** | **BROKEN** | `backend/prescripto/api/v1/routers/analyses.py:144,150`. Crashes with `NameError: name 'HTTPException' is not defined` when analysis is not found or operator is unauthorized. UI label implemented in `AnalysisDetailPage.tsx:710`. |
| **History / List Pages** | **PARTIAL** | `web/src/pages/PrescriptionsListPage.tsx` lists caller prescriptions cleanly. However, `backend/prescripto/api/v1/routers/patients.py:266,269` crashes on `rv.action` and `rv.reviewed_at`, breaking the Patient Timeline page. |
| **Error Handling (Quota, Key, Model, Image)** | **PARTIAL** | Image errors caught at upload (`ingest_prescription.py:84`). Gemini Quota, Key, and Timeout caught in `engine.py:150`. However, bad Gemini model name or invalid JSON payload raises uncaught exceptions that fail the worker job. |
| **Frontend UI/UX Quality** | **8 / 10** | Professional, accessible light theme with medical palette. Features multilingual support (EN, HI, GU, MR) and text-to-speech voice playback (`LanguageContext.tsx:9`). Hampered by 526 kB JS bundle and unhandled 500 error cascades. |

---

## 4. Integration Mismatches

### 4.1. Frontend API Calls vs. Backend Routes & Contracts

The backend registers 19 endpoints on FastAPI `app`, but the canonical `OPENAPI.yaml` and `docs/API-CONTRACT.md` only document 8 endpoints. The following 11 endpoints exist in code and frontend, but have no contract specification:

| Route Path | Method | Frontend Caller | Contract Status | Mismatch Notes |
|---|---|---|---|---|
| `/api/v1/auth/doctor/login` | `POST` | `web/src/api/auth.ts:49` | Missing from `OPENAPI.yaml` | Implemented in backend, absent from spec |
| `/api/v1/auth/send-otp` | `POST` | `web/src/api/auth.ts:24` | Missing from `OPENAPI.yaml` | Implemented in backend, absent from spec |
| `/api/v1/auth/verify-otp` | `POST` | `web/src/api/auth.ts:36` | Missing from `OPENAPI.yaml` | Implemented in backend, absent from spec |
| `/api/v1/auth/me` | `GET` | `web/src/api/auth.ts:57` | Missing from `OPENAPI.yaml` | Implemented in backend, absent from spec |
| `/api/v1/analyses/{id}/clinical-summary` | `GET` | `web/src/api/analyses.ts:72` | Missing from `OPENAPI.yaml` | Crashes with `NameError` on 404/forbidden |
| `/api/v1/analyses/{id}/medications` | `PATCH` | `web/src/api/analyses.ts:88` | Missing from `OPENAPI.yaml` | Implemented in backend, absent from spec |
| `/api/v1/patients` | `POST` | `web/src/api/patients.ts:92` | Missing from `OPENAPI.yaml` | Implemented in backend, absent from spec |
| `/api/v1/patients/search` | `GET` | `web/src/api/patients.ts:80` | Missing from `OPENAPI.yaml` | Critical IDOR auth gap |
| `/api/v1/patients/{patient_identifier}` | `GET` | `web/src/api/patients.ts:87` | Missing from `OPENAPI.yaml` | Crashes on `Review.action` / `Review.reviewed_at` |
| `/api/v1/storage/{key:path}` | `GET` | Direct browser `<img>` | Missing from `OPENAPI.yaml` | Unauthenticated public route in `main.py:178` |

### 4.2. Configuration & Environment Consistency

- **Gemini Model Name:** Pinned consistently to `gemini-3.8-flash` across `backend/prescripto/config/settings.py:67`, `docker-compose.yml:83,128`, and `backend/.env.example:47`.
- **Database Port Discrepancy:**
  - `docker-compose.yml:14`: publishes PostgreSQL on host port `5435:5432`.
  - `backend/prescripto/config/settings.py:25` & `backend/.env.example:13`: correctly defaults to port `5435`.
  - `backend/alembic.ini:45`: hardcodes `sqlalchemy.url = ...:5432/...`. Running `alembic upgrade head` on the host without `DATABASE_URL` fails.
- **Settings Missing from `backend/.env.example`:**
  The following 6 fields exist in `backend/prescripto/config/settings.py` but are omitted from `backend/.env.example`:
  `OCR_DEVICE`, `WORKER_HEARTBEAT_SECONDS`, `WORKER_ID`, `WORKER_LEASE_SECONDS`, `WORKER_MAX_RETRIES`, `WORKER_POLL_INTERVAL`.
- **Frontend Environment:**
  `web/` contains no `.env.example` file. Default fallback in `web/src/api/client.ts:4` relies on `import.meta.env.VITE_API_BASE_URL || '/api/v1'` proxied by Vite (`web/vite.config.ts:12`).

### 4.3. Dead or Duplicate Code Paths

1. **Dead `ml-service` Microservice:**
   The entire `ml/` standalone microservice (`ml/app/main.py`, `ml/Dockerfile`, PaddleOCR runtime) is disabled in `docker-compose.yml:98` (`profiles: ["ml-service"]`). `backend/prescripto/config/settings.py:56` marks `ML_RUNTIME_MODE=remote` as unused. `RemoteMLClient` in `backend/prescripto/ml/runtime.py:133` is dead code.
2. **Duplicated Regex Extraction Code:**
   `ml/app/extraction/spans.py` and `backend/prescripto/ml/extraction.py` contain duplicate regex patterns and parsing logic for boilerplate, vitals, and dates.
3. **Double Gemini Billing Calls:**
   Prescription processing calls Gemini Vision multimodal inference during text recognition (`backend/prescripto/pipeline/engine.py:149`). When a user visits the review page, `web/src/pages/AnalysisDetailPage.tsx:110` calls `GET /analyses/{id}/clinical-summary`, triggering a *second* Gemini call (`backend/prescripto/application/services/llm_explainer.py:92`) without server-side caching.

---

## 5. Accuracy & AI Findings

### 5.1. Gemini Vision Configuration & Prompts

- **Model:** `gemini-3.8-flash` (`backend/prescripto/config/settings.py:67`)
- **Temperature:** `0` (`backend/prescripto/ml/recognition_providers.py:503`)
- **Payload Input:** Raw image bytes are sent directly as a multimodal binary part (`recognition_providers.py:509`: `contents=[prompt, types.Part.from_bytes(data=image_bytes, mime_type=mime_type)]`). No prior OCR text is sent to Gemini.
- **Response Schema:** Structured JSON strictly bound via Pydantic model `GeminiPrescriptionOutput` (`recognition_providers.py:418-430`) with `response_mime_type="application/json"`.
- **System Instruction / Prompt:**
  ```text
  Transcribe this prescription image into the requested JSON schema. Keep each text span in its correct category. Only list medicines or treatments as medicines when an explicit medicine order is visible; never put dates, IDs, hospital or clinician names, symptoms, diagnoses, vitals, or general advice in medications. A medicine's original_text must quote its visible order, including any legible sig text. Do not infer or complete handwriting. Copy uncertain text verbatim into uncertain_items. Only include a name, strength, dose, route, frequency, duration, or instruction if that value is explicitly legible in the image. Never invent a diagnosis, advice, or dosing. This output is unverified and requires human review.
  ```

### 5.2. Failure & Invalid JSON Handling

- If Gemini raises `RecognitionQuotaError`, `RecognitionAuthenticationError`, or `RecognitionTimeoutError`, `backend/prescripto/pipeline/engine.py:150` catches the exception and falls back to `LocalRapidOCRProvider`.
- **Vulnerability:** If Gemini fails with `RecognitionModelUnavailableError`, `RecognitionMalformedResponseError` (e.g. schema mismatch or truncated JSON), or generic `RecognitionError`, the exception is **not** caught by `engine.py:150`. The exception propagates up and causes the worker job to permanently transition to `FAILED` or `DEAD`.

### 5.3. Uncertainty & Illegibility Flagging

- In Gemini mode: Prompt instructs the model to copy uncertain text into `uncertain_items`.
- In Local RapidOCR mode: `classify_text_line` (`recognition_providers.py:220-230`) flags text lacking vowels, containing symbols, or unclassifiable as `DocumentFieldType.UNCERTAIN_UNREADABLE`.
- In Pipeline Assembly: `handle_report_assembly` (`engine.py:588`) inspects `FieldState.AMBIGUOUS` or unreadable fields; any presence sets `analysis.review_required = True` and records `review_reasons`.
- In UI: `web/src/pages/AnalysisDetailPage.tsx:375-412` displays an amber alert banner and an interactive button: `Jump to Unclear Items (N)`.

### 5.4. Test Prescription Ground Truth vs. Extracted Results

Running `backend/scripts/run_demo_pipeline.py` against `sample_prescription.png`:

| Medication Line | Expected (Ground Truth in `sample_prescription.py`) | Extracted Text | Normalized Master Match | Match Score | Status |
|---|---|---|---|---|---|
| Line 1 | Amoxicillin 500mg capsule (Sig: 1 cap three times daily) | `Amoxicillin` (Strength: `500mg`) | `Amoxicillin` | `1.0` (EXACT) | **MATCH** |
| Line 2 | Paracetamol 650mg tablet (Sig: 1 tab as needed for fever) | `Paracetamol` (Strength: `650mg`) | `Paracetamol` | `1.0` (EXACT) | **MATCH** |
| Line 3 | Cetirizine 10mg tablet (Sig: 1 tab at bedtime for 5 days) | `Cetirizine` (Strength: `10mg`) | `Cetirizine` | `1.0` (EXACT) | **MATCH** |

*Note on LocalRapidOCR Fallback:* The `Sig:` instructions were categorized as `GENERAL_ADVICE` lines (`recognition_providers.py:177`) rather than linked to the medication object. When using Gemini Vision, the sig text is structured directly into `frequency` and `instructions`.

---

## 6. Risks & Quality

### 6.1. Security & Compliance Findings

- **Broken Object-Level Authorization (IDOR) on Patient History:**  
  `backend/prescripto/api/v1/routers/patients.py:155` (`get_patient_timeline`) requires authentication, but has **no role or tenant check**. Any patient authenticated via OTP can enter any other patient's ID (`PAT-1001`) or phone number and download their entire historical clinical record, medications, and safety findings.
- **Unrestricted Patient Directory Search:**  
  `backend/prescripto/api/v1/routers/patients.py:90` (`search_patients`) requires `current_user: User = Depends(get_current_user)`, but does not enforce `require_role(Role.REVIEWER, Role.ADMIN)`. Any patient can query `/patients/search?q=` and dump the full patient registry.
- **Unauthenticated Storage Image Download:**  
  `backend/prescripto/api/main.py:178` mounts `GET /api/v1/storage/{key:path}` without authentication (`include_in_schema=False`). Any unauthenticated client knowing or guessing the storage key can download the original prescription image. In `storage/client.py:146`, local file paths are joined without verifying path boundary containment.
- **Missing Rate Limiting:**  
  No rate limiter exists on sensitive endpoints: `POST /api/v1/auth/send-otp` (SMS toll fraud / spam), `POST /api/v1/auth/verify-otp` (brute-forcing 6-digit OTPs), `POST /api/v1/auth/token` (credential stuffing), and `POST /api/v1/prescriptions` (storage exhaustion).
- **Patient Data in Logs:**  
  `backend/prescripto/audit/logger.py:12-60` implements a strict whitelist filter (`PERMITTED_LOG_KEYS`). Unlisted keys are stripped and logged as `_dropped_unwhitelisted_keys_count`. Live test logs confirmed no PHI was leaked in structured key-value pairs.

### 6.2. Test Coverage & Deficiencies

- **What exists:** 180 backend tests in `backend/tests` (174 passed, 6 skipped) covering auth crypto, domain uncertainty models, queue fencing tokens, worker heartbeats, and storage client abstraction. ML service has 20 unit tests in `ml/tests`.
- **What is missing:**
  - Zero automated end-to-end frontend tests (no Cypress or Playwright test suites in `web/`).
  - No integration tests verifying patient timeline serialization with real `Review` records.
  - Concurrency test suite (`test_postgres_concurrency.py`) is skipped on SQLite environments.

### 6.3. Top Technical Debt Items

1. **46 Mypy Errors in Backend:** `mypy backend/prescripto` fails with 46 typing issues, notably missing stubs, invalid dictionary types in `openfda.py`, and type mismatches in domain safety classes.
2. **Dual Database Seeding Architecture:** `seed_users.py` and `seed_patients.py` seed PostgreSQL via SQLAlchemy `SessionLocal`, but `seed_medications.py:11` seeds SQLite `prescripto.db` via raw `sqlite3`.
3. **Dead `ml/` Microservice:** Maintaining a separate `ml/` Docker container and codebase that is disabled in Docker Compose adds maintenance overhead.
4. **Large Frontend Bundle:** Vite reports `dist/assets/index-Bc8R3Sso.js` at 526 kB; needs manual route-level code splitting via `React.lazy()`.

---

## 7. Docs-vs-Code Differences

| Area | Documentation Specification (`docs/*`) | Codebase Reality |
|---|---|---|
| **Recognition Architecture** | `docs/Architecture.md` (ADR-06) specifies an offline, local line-crop OCR model (TrOCR / PP-OCR) with benchmark-driven selection. | Primary recognizer is cloud-hosted **Google Gemini 3.8 Flash Vision** (`RECOGNITION_PROVIDER=gemini`). Local RapidOCR ONNX is used only as fallback. |
| **LLM Usage in Production** | `docs/Architecture.md` (ADR-09) explicitly sets `LLM_ENABLED = false` for V1 to eliminate hallucination and privacy risks. | Gemini Vision is active for document transcription, and `LLMExplainerService` (`llm_explainer.py`) is integrated for clinical summaries. |
| **Safety Engine Scope** | `docs/Architecture.md` (ADR-08) defers DDI and dosage-range checks in V1, restricting checks to exact duplicate candidates. | Code implements active dosage threshold checks (`dosage.py`) and patient allergen cross-referencing (`allergy.py`) in `handle_safety_screening`. |
| **External Third-Party APIs** | `docs/Architecture.md` (ADR-14) states no external safety providers will be called at runtime to avoid disclosing patient data. | Raw prescription images are transmitted to Google Cloud (Gemini API) during processing. |
| **API Contract & Schema** | `docs/API-CONTRACT.md` and `OPENAPI.yaml` list exactly 8 endpoints, stating: *"No endpoint exists without a row here."* | Backend registers 19 endpoints, adding doctor login, OTP flows, patient search, medical history timelines, and medication editing. |
| **Frontend Implementation Status** | `docs/ROADMAP_TO_100.md` lists Frontend at 25% with no dedicated consumer or clinician UI. | `web/` contains a completed React 19 SPA with 10 functional pages, review queue, modal image viewer, and multilingual speech assistance. |
| **Database Migration Port** | `docs/DEPLOYMENT.md` specifies Compose maps Postgres to `localhost:5435`. | `backend/alembic.ini:45` hardcodes `localhost:5432`, causing manual host migrations to fail without manual env overrides. |

---

## 8. Prioritized Next Actions

### P0: Critical (Blocks MVP / Immediate Safety & Crash Fixes)

1. **Import `HTTPException` in Analyses Router**
   - **Files:** `backend/prescripto/api/v1/routers/analyses.py:10,144,150`
   - **Effort:** **S** (5 minutes)
   - **Action:** Add `HTTPException` to `from fastapi import APIRouter, Depends, status, HTTPException`. Resolves 500 crashes on missing analyses.
2. **Fix `Review` Attributes in Patient Timeline Router**
   - **Files:** `backend/prescripto/api/v1/routers/patients.py:266,269`
   - **Effort:** **S** (15 minutes)
   - **Action:** Change `rv.action` to `rv.status` and `rv.reviewed_at` to `rv.submitted_at` or `rv.created_at` to match `Review` model (`models/review.py`).
3. **Fix IDOR & Enforce Role Guards on Patient Endpoints**
   - **Files:** `backend/prescripto/api/v1/routers/patients.py:94,158`
   - **Effort:** **S** (30 minutes)
   - **Action:** Restrict `search_patients` to `require_role(Role.REVIEWER, Role.ADMIN)`. In `get_patient_timeline`, verify that `current_user.role in (Role.REVIEWER, Role.ADMIN)` OR `current_user.id == patient.user_id`.
4. **Widen Gemini Fallback Exception Handling in Pipeline**
   - **Files:** `backend/prescripto/pipeline/engine.py:150`
   - **Effort:** **S** (20 minutes)
   - **Action:** Catch `RecognitionModelUnavailableError`, `RecognitionMalformedResponseError`, and generic `RecognitionError` so any Gemini failure triggers local RapidOCR fallback instead of failing the job.
5. **Secure Local Storage Endpoint**
   - **Files:** `backend/prescripto/api/main.py:178`, `backend/prescripto/storage/client.py:146`
   - **Effort:** **S** (30 minutes)
   - **Action:** Add `current_user = Depends(get_current_user)` to `/api/v1/storage/{key:path}` and validate that `local_path.resolve()` remains inside `_local_dir`.

---

### P1: Needed for Launch / Production Readiness

1. **Add Rate Limiting Middleware**
   - **Files:** `backend/prescripto/api/main.py`, `backend/pyproject.toml`
   - **Effort:** **M** (2–3 hours)
   - **Action:** Integrate `slowapi` or custom Redis rate limiter for `/auth/send-otp` (5/min), `/auth/verify-otp` (10/min), and `/prescriptions` (20/min).
2. **Unify Medication Master Seeding on PostgreSQL**
   - **Files:** `backend/scripts/seed_medications.py:11`
   - **Effort:** **S** (30 minutes)
   - **Action:** Refactor `seed_medications.py` to use SQLAlchemy `SessionLocal` so it seeds the active PostgreSQL instance rather than local `prescripto.db`.
3. **Align `OPENAPI.yaml` and `docs/API-CONTRACT.md`**
   - **Files:** `OPENAPI.yaml`, `backend/OPENAPI.yaml`, `docs/API-CONTRACT.md`
   - **Effort:** **M** (2 hours)
   - **Action:** Add the 11 missing endpoints and schemas (`/auth/doctor/login`, OTP endpoints, patient timeline, clinical summary, medication update) to the official contract.
4. **Fix Alembic Default Port**
   - **Files:** `backend/alembic.ini:45`
   - **Effort:** **S** (5 minutes)
   - **Action:** Update default `sqlalchemy.url` port from `5432` to `5435` or inject via `os.getenv("DATABASE_URL")`.
5. **Implement Code Splitting in Frontend**
   - **Files:** `web/src/App.tsx`, `web/vite.config.ts`
   - **Effort:** **S** (45 minutes)
   - **Action:** Use `React.lazy()` for route pages (`AnalysisDetailPage`, `PatientTimelinePage`, `SystemHealthPage`) to reduce bundle chunk size below 500 kB.
6. **Resolve 46 Backend Mypy Errors**
   - **Files:** `backend/prescripto/knowledge/openfda.py`, `prescripto/domain/safety/duplicate.py`, `prescripto/storage/client.py`
   - **Effort:** **M** (2–3 hours)
   - **Action:** Fix type annotations to achieve 100% clean type-checking.

---

### P2: Technical Debt & Post-Launch Improvements

1. **Decommission Dead Standalone `ml/` Microservice**
   - **Files:** `ml/`, `docker-compose.yml:97-114`, `backend/prescripto/ml/runtime.py:133`
   - **Effort:** **M** (2 hours)
   - **Action:** Either remove the orphaned `ml/` service and `RemoteMLClient` or move the active RapidOCR/PaddleOCR inference into it if microservice decoupling is desired.
2. **Server-Side Clinical Summary Caching**
   - **Files:** `backend/prescripto/api/v1/routers/analyses.py`, `prescripto/db/models/analysis.py`
   - **Effort:** **S** (1 hour)
   - **Action:** Persist the generated clinical summary in a JSON column on `Analysis` to prevent redundant Gemini LLM API calls on repeated page loads.
3. **Automated Frontend End-to-End Tests**
   - **Files:** `web/tests/e2e/review-flow.spec.ts`
   - **Effort:** **L** (1–2 days)
   - **Action:** Add Playwright test suite testing login -> prescription upload -> review queue -> doctor approval.

---

## 9. Top 3 Questions You Need to Decide

1. **Architectural Direction: Cloud Gemini Vision vs. Local-Only OCR**
   - *Context:* `docs/Architecture.md` (ADR-06, ADR-09, ADR-14) explicitly prohibits sending patient prescription data to external LLMs and mandates local OCR. However, the codebase now relies on Google Gemini 3.8 Flash Vision for superior handwriting accuracy, treating local RapidOCR as a fallback.
   - *Decision Needed:* Do you approve updating the architectural specifications to endorse cloud-first Gemini Vision (with DPDPA/HIPAA data processing addendums), or must we enforce strict local-first OCR as specified in ADR-09?
2. **Access Control Policy for the Patient Directory**
   - *Context:* The new Patient Portal allows patients to log in via phone OTP, but the backend `/patients/search` and `/patients/{id}` routes currently permit any authenticated user to view any patient's records.
   - *Decision Needed:* Should patient accounts be strictly quarantined to viewing only their own profile and prescriptions, reserving patient search and cross-patient lookup exclusively for `REVIEWER` and `ADMIN` doctor roles?
3. **Disposition of the Dead `ml/` Microservice Directory**
   - *Context:* The repository contains an entire standalone FastAPI microservice in `ml/` (port 8001) that is disabled in Docker Compose, while the backend runs RapidOCR in-process.
   - *Decision Needed:* Should the `ml/` directory and `RemoteMLClient` code be archived and deleted to clean up technical debt, or is there an intent to revive it as a dedicated GPU inference service?


