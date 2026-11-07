# Prescripto AI 2.0 — Testing & Debugging Dossier

**Document ID:** `DOC-10-TEST`  
**Classification:** Academic Engineering Dossier  
**Canonical Spec Reference:** [backend/tests/](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/backend/tests/), [docs/TEST_REPORT.md](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/docs/TEST_REPORT.md)  
**Date of Extraction:** November 4, 2026  

---

## 1. Testing Infrastructure & Methodology

### 1.1. Test Harness Architecture
* **Testing Framework:** `pytest` (v9.1.1) with `pytest-asyncio` and `anyio`.
* **Execution Setup:** Configured via [backend/tests/conftest.py](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/backend/tests/conftest.py).
* **Dual Persistence Strategy:**
  1. **SQLite In-Memory Mode (Hermetic Unit Testing):** Default when `TEST_DATABASE_URL` is unset. Fast, isolated, zero-external-dependency execution.
  2. **PostgreSQL Savepoint Mode (Integration & Concurrency):** When `TEST_DATABASE_URL` is provided, pytest runs `alembic upgrade head` and uses SQLAlchemy's `join_transaction_mode="create_savepoint"`. This allows tests to issue real SQL `COMMIT` statements within worker transactions while rolling back outer savepoints between test functions to preserve test isolation.

---

## 2. Test Suite Categorization

```
backend/tests/
├── contract/             # Contract parity between OpenAPI schema and FastAPI routes
├── eval_set/             # Synthetic benchmark image dataset and ground-truth JSON
├── integration/          # Multi-component workflow and database integration suites
└── unit/                 # Pure domain, cryptographic, and mathematical rule suites
```

### 2.1. Suite Summary
* **Total Executed Automated Test Cases:** 197
* **Unit Tests:** 38 tests covering pure algorithms, uncertainty models, and cryptography.
* **Integration Tests:** 152 tests covering REST routes, worker concurrency, and S3 storage.
* **Contract Tests:** 7 tests verifying schema parity against `OPENAPI.yaml`.
* **PostgreSQL Concurrency Tests:** 6 tests evaluating simultaneous multi-worker claiming.

---

## 3. Verified Test Case Matrix

The following matrix documents real test cases executed in the Prescripto AI 2.0 codebase:

| Test ID | Module | Scenario Tested | Expected Result | Actual Result | Verification Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-SEC-01** | `auth.crypto` | Hash plaintext password and verify against hash | Matching password returns `True`; incorrect password returns `False` | Pass | VERIFIED IN TEST (`test_auth_crypto.py`) |
| **TC-SEC-02** | `auth.crypto` | Issue RS256 token and decode with public key | Valid payload returned with claims `sub`, `role`, `exp` | Pass | VERIFIED IN TEST (`test_auth_crypto.py`) |
| **TC-SEC-03** | `auth.crypto` | Decode expired RS256 JWT token | Raises `jwt.ExpiredSignatureError` | Pass | VERIFIED IN TEST (`test_auth_crypto.py`) |
| **TC-SEC-04** | `audit.logger` | Structlog event with unwhitelisted PHI keys | Strips unapproved keys, preserves `PERMITTED_LOG_KEYS`, records dropped count | Pass | VERIFIED IN TEST (`test_logger.py`) |
| **TC-SEC-05** | `storage.client` | Generate and verify HMAC presigned storage URL | Valid before expiration; returns `False` after expiration or tampering | Pass | VERIFIED IN TEST (`test_storage_client.py`) |
| **TC-SEC-06** | `storage.client` | Storage key containing path traversal `../` | Intercepted and raises `StorageObjectNotFoundException` | Pass | VERIFIED IN TEST (`test_storage_client.py`) |
| **TC-SAFE-01** | `domain.safety` | Same canonical drug prescribed twice on same document | Emits `DUPLICATE_MEDICATION` finding with `FindingStatus.POTENTIAL` | Pass | VERIFIED IN TEST (`test_clinical_safety_rules.py`) |
| **TC-SAFE-02** | `domain.safety` | Two distinct brands sharing active ingredient (*Dolo* + *Combiflam*) | Flags active ingredient overlap (*Paracetamol*) | Pass | VERIFIED IN TEST (`test_clinical_safety_rules.py`) |
| **TC-SAFE-03** | `domain.safety` | Unresolved medication line evaluated for duplicates | Emits `NOT_EVALUATED` finding with reason `UNRESOLVED_IDENTITY` | Pass | VERIFIED IN TEST (`test_clinical_safety_rules.py`) |
| **TC-SAFE-04** | `domain.safety` | Prescribed dose exceeds ceiling (Paracetamol 1500mg) | Emits `ADVERSE_EFFECT` finding requiring clinical review | Pass | VERIFIED IN TEST (`test_enhanced_safety.py`) |
| **TC-SAFE-05** | `domain.safety` | Patient with penicillin allergy prescribed Augmentin | Emits `ALLERGY_CONFLICT` finding flagging contraindication | Pass | VERIFIED IN TEST (`test_enhanced_safety.py`) |
| **TC-UNC-01** | `domain.uncertainty`| Raw confidence score $0.45$ assigned to extracted field | Mapped to `FieldState.UNREADABLE` | Pass | VERIFIED IN TEST (`test_domain_uncertainty.py`) |
| **TC-UNC-02** | `domain.uncertainty`| Unreadable field passed to downstream safety rule | Field is masked and excluded from safety conclusion | Pass | VERIFIED IN TEST (`test_domain_uncertainty.py`) |
| **TC-ING-01** | `api.prescriptions`| Upload image without `Idempotency-Key` header | Returns HTTP `400 Bad Request` (`MISSING_IDEMPOTENCY_KEY`) | Pass | VERIFIED IN TEST (`test_prescriptions_api.py`) |
| **TC-ING-02** | `api.prescriptions`| Replay identical upload with same idempotency key | Returns HTTP `202 Accepted` with existing IDs (0 duplicate jobs) | Pass | VERIFIED IN TEST (`test_prescriptions_api.py`) |
| **TC-ING-03** | `api.prescriptions`| Replay same key with different file payload | Returns HTTP `409 Conflict` (`IDEMPOTENCY_CONFLICT`) | Pass | VERIFIED IN TEST (`test_prescriptions_api.py`) |
| **TC-WRK-01** | `worker.queue` | 2 concurrent workers query queued jobs via `SKIP LOCKED` | Both workers claim distinct jobs without deadlock or double claim | Pass | VERIFIED IN TEST (`test_postgres_concurrency.py`) |
| **TC-WRK-02** | `worker.fencing` | Worker attempts to commit stage after lease expiration | Raises `WorkerFencedError`; rolls back transaction safely | Pass | VERIFIED IN TEST (`test_worker_fencing.py`) |
| **TC-DEL-01** | `retention.worker` | Execute 4-phase DPDPA deletion on existing document | Purges DB rows, deletes S3 object, writes signed HMAC certificate | Pass | VERIFIED IN TEST (`test_deletion_lifecycle.py`) |
| **TC-REV-01** | `api.analyses` | Reviewer submits sign-off (`APPROVE` / `FLAG`) | Transitions analysis status to `REVIEWED_COMPLETE` | Pass | VERIFIED IN TEST (`test_doctor_review_workflow.py`) |
| **TC-REV-02** | `api.analyses` | Patient attempts to submit review sign-off | Rejected with HTTP `403 Forbidden` (`INSUFFICIENT_ROLE`) | Pass | VERIFIED IN TEST (`test_doctor_review_workflow.py`) |

---

## 4. Notable Bugs Discovered & Debugging Decisions

### Bug 1: PostgreSQL Missing `patients` Table Migration (`BUG-01`)
* **Symptom:** In test suite execution on PostgreSQL, 14 integration tests failed with `relation "patients" does not exist`.
* **Root Cause:** A new `Patient` domain entity had been declared in SQLAlchemy models, but no corresponding Alembic migration script had been generated.
* **Resolution:** Authored Alembic migration [0003_add_patients_table.py](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/backend/prescripto/db/migrations/versions/0003_add_patients_table.py) safely creating the table, adding foreign key constraints, and registering the `Role.PATIENT` enum.

### Bug 2: Python Dependency Conflicts in Docker Build (`BUG-02`)
* **Symptom:** Docker container build on Render failed during `pip install` with `ResolutionImpossible: google-genai depends on pydantic>=2.9.0 and httpx>=0.28.1`.
* **Root Cause:** `backend/requirements.txt` strictly pinned `httpx==0.27.0` and `pydantic==2.7.4`.
* **Resolution:** Upgraded `httpx` to `0.28.1` and loosened Pydantic constraints to `pydantic>=2.10.0,<3.0.0` in [backend/requirements.txt](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/backend/requirements.txt).

### Bug 3: Windows SQLite Path Invocation on Linux Container (`BUG-03`)
* **Symptom:** Render web service crashed during deployment startup with:
  `sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unable to open database file`.
* **Root Cause:** The developer's local `backend/.env` containing Windows path `sqlite:///c:/Users/pbhus/.../prescripto.db` had been pasted into the Render dashboard. The Linux container could not resolve drive letter `c:`.
* **Resolution:** Authored an automatic path sanitizer inside `normalize_database_url` in [backend/prescripto/config/settings.py](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/backend/prescripto/config/settings.py) that detects Windows paths inside Linux environments and rewrites them to `sqlite:///prescripto.db`.

### Bug 4: Vercel Frontend Relative API 404 Failure (`BUG-04`)
* **Symptom:** Doctor and patient login on Vercel returned error: `"PROBLEM: The page could not be found"`.
* **Root Cause:** In the frontend, `VITE_API_BASE_URL` defaulted to relative path `/api/v1`. On Vercel (static hosting), calling relative `/api/v1` hit Vercel's static router instead of the Render backend.
* **Resolution:** 
  1. Updated [web/src/api/client.ts](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/web/src/api/client.ts) to hardcode production fallback to `https://prescripto-2-0.onrender.com`.
  2. Created [web/vercel.json](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/web/vercel.json) adding rewrite rules `/* -> /index.html` for client-side routing.
  3. Added dynamic CORS regex `allow_origin_regex=r"https?://.*"` in FastAPI.

