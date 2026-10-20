# Prescripto AI 2.0 — Live Demo Runbook & Lifecycle Guide

This runbook provides the exact terminal commands (from startup to teardown), cURL commands, and a complete architectural lifecycle showcase for live presentations and evaluators.

---

## 1. System Architecture Overview

Prescripto AI 2.0 operates as an asynchronous, distributed clinical decision-support pipeline:

```
[ Operator / Client ]
        │  1. POST /prescriptions (multipart image + Idempotency-Key)
        ▼
[ Backend API :8000 ] ─── 2. Write Object ───▶ [ MinIO S3 :9000 ]
        │
        ├── 3. Enqueue Job (QUEUED)
        ▼
[ PostgreSQL :5435 ]
        ▲
        │  4. Poll & Lease Job (Fencing Token)
[ Worker Container ]
        │
        ├── 5. POST /v1/ocr/recognize (HTTP) ──▶ [ ML Service :8001 (PP-OCRv6) ]
        ├── 6. Extract Spans & Normalize ─────▶ [ CDSCO Drug Knowledgebase ]
        ├── 7. Deterministic Safety Checks ───▶ [ Clinical Rules Engine ]
        │
        └── 8. Transition State (REQUIRES_REVIEW) ──▶ [ PostgreSQL :5435 ]
                                                                ▲
[ Clinical Reviewer ]                                           │
        │  9. POST /analyses/{id}/review (APPROVED)            │
        └───────────────────────────────────────────────────────┘
           10. Final State: REVIEWED_COMPLETE (Immutable Lock)
```

---

## 2. Fast Path: Complete 1-Command Rehearsal

If you need to verify the entire system in 10 seconds:

```bash
docker compose exec api python scripts/rehearse_demo.py
```

This script automatically logs in as `operator1`, uploads a prescription, polls the worker until `REQUIRES_REVIEW`, logs in as `reviewer1`, submits clinical approval decisions, and confirms the final status `REVIEWED_COMPLETE`.

---

## 3. Terminal Commands: Start to Finish

### Step 3.1: Start the Infrastructure Stack
Run from the repository root:

```bash
# Start all 6 distributed containers in detached mode
docker compose up -d

# Verify all containers are running and healthy
docker compose ps
```

*Expected Services:*
- `prescripto-api` (`http://localhost:8000`)
- `prescripto-ml` (`http://localhost:8001`)
- `prescripto-worker`
- `prescripto-deletion-worker`
- `prescripto-postgres` (port `5435`)
- `prescripto-minio` (S3: `9000`, Web Console: `9001`)

---

### Step 3.2: Verify Health Endpoints

```bash
# Check Backend Core Health (PostgreSQL, MinIO, Worker heartbeat)
curl -s http://localhost:8000/api/v1/health

# Check ML Inference Service Health (PaddleOCR PP-OCRv6)
curl -s http://localhost:8001/health
```

---

### Step 3.3: Database Migrations & Initial Seeding

```bash
# 1. Run Alembic Database Migrations
docker compose exec api alembic upgrade head

# 2. Seed Baseline CDSCO Medication Dictionary (12 essential drugs)
docker compose exec api python scripts/seed_medications.py

# 3. Create Demo Users with Bcrypt Passwords
# Operator (Uploads prescriptions)
docker compose exec api python scripts/create_user.py \
  --username operator1 \
  --email operator1@demo.local \
  --password Demo#12345 \
  --role OPERATOR

# Reviewer (Pharmacist / Clinician)
docker compose exec api python scripts/create_user.py \
  --username reviewer1 \
  --email reviewer1@demo.local \
  --password Demo#12345 \
  --role REVIEWER

# Administrator
docker compose exec api python scripts/create_user.py \
  --username admin1 \
  --email admin1@demo.local \
  --password Demo#12345 \
  --role ADMIN
```

---

## 4. End-to-End Demo Lifecycle (cURL Walkthrough)

### Phase 1: Authentication (Operator Login)

Request an RS256-signed JWT token as `operator1`:

```bash
# Linux / macOS / Git Bash
OPERATOR_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=operator1&password=Demo%2312345" | jq -r .access_token)

echo "Operator Token: $OPERATOR_TOKEN"
```

*PowerShell equivalent:*
```powershell
$tokenRes = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/token" -Method Post -Body "username=operator1&password=Demo%2312345" -ContentType "application/x-www-form-urlencoded"
$OPERATOR_TOKEN = $tokenRes.access_token
```

---

### Phase 2: Ingest Prescription Document

Upload a prescription image with an idempotent request header:

```bash
IDEMPOTENCY_KEY=$(uuidgen 2>/dev/null || python -c "import uuid; print(uuid.uuid4())")

UPLOAD_RES=$(curl -s -X POST http://localhost:8000/api/v1/prescriptions \
  -H "Authorization: Bearer $OPERATOR_TOKEN" \
  -H "Idempotency-Key: $IDEMPOTENCY_KEY" \
  -F "file=@sample_rx.png;type=image/png" \
  -F "patient_external_id=PAT-DEMO-01")

echo $UPLOAD_RES
```

*Response (HTTP 202 Accepted):*
```json
{
  "analysis_id": "33212319-ffca-4d3f-9413-540d3b36ef63",
  "prescription_id": "c3dc921a-6ed6-4f43-8839-ed6e4be3c2d8"
}
```

---

### Phase 3: Inspect Document Metadata & Ephemeral Image URL

Using the `prescription_id`:

```bash
curl -s -X GET http://localhost:8000/api/v1/prescriptions/c3dc921a-6ed6-4f43-8839-ed6e4be3c2d8 \
  -H "Authorization: Bearer $OPERATOR_TOKEN"
```

*Security note:* Returns an ephemeral, cryptographically pre-signed MinIO URL valid for 60 seconds only.

---

### Phase 4: Monitor Worker Pipeline Stages

Poll status using the `analysis_id`:

```bash
curl -s -X GET http://localhost:8000/api/v1/analyses/33212319-ffca-4d3f-9413-540d3b36ef63 \
  -H "Authorization: Bearer $OPERATOR_TOKEN"
```

*Response during/after processing:*
```json
{
  "analysis_id": "33212319-ffca-4d3f-9413-540d3b36ef63",
  "status": "REQUIRES_REVIEW",
  "stages": [
    { "stage_name": "INGESTION", "status": "COMPLETED" },
    { "stage_name": "QUALITY_CHECK", "status": "COMPLETED" },
    { "stage_name": "TEXT_DETECTION", "status": "COMPLETED" },
    { "stage_name": "OCR_RECOGNITION", "status": "COMPLETED" },
    { "stage_name": "STRUCTURED_EXTRACTION", "status": "COMPLETED" },
    { "stage_name": "MEDICATION_NORMALIZATION", "status": "COMPLETED" },
    { "stage_name": "SAFETY_SCREENING", "status": "COMPLETED" },
    { "stage_name": "REPORT_ASSEMBLY", "status": "COMPLETED" }
  ]
}
```

---

### Phase 5: Fetch Structured Clinical Analysis Report

```bash
curl -s -X GET http://localhost:8000/api/v1/analyses/33212319-ffca-4d3f-9413-540d3b36ef63/result \
  -H "Authorization: Bearer $OPERATOR_TOKEN"
```

*Key extracted outputs:*
- `medications`: Identifies drug name, strength, dosage, route, frequency, and instructions.
- `findings`: Lists safety risk alerts (e.g. `DUPLICATE_MEDICATION`, `AMBIGUOUS_IDENTITY`).
- `coverage_disclaimer`: Mandatory clinical assistive disclaimer.

---

### Phase 6: Human-in-the-Loop Clinical Review

#### Step 6.1: Obtain Reviewer JWT Token
```bash
REVIEWER_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=reviewer1&password=Demo%2312345" | jq -r .access_token)
```

#### Step 6.2: Submit Review Decisions
Pass the specific `finding_id` from Phase 5:

```bash
curl -s -X POST http://localhost:8000/api/v1/analyses/33212319-ffca-4d3f-9413-540d3b36ef63/review \
  -H "Authorization: Bearer $REVIEWER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "decisions": [
      {
        "finding_id": "4fda2f69-f6ec-4ee3-ab64-1c190d2eebfe",
        "action": "APPROVED",
        "notes": "Verified by clinical pharmacist during live evaluation."
      }
    ]
  }'
```

*Response (HTTP 201 Created):*
```json
{
  "review_id": "27060c72-8953-45d2-ad13-305d9774a93c",
  "analysis_id": "33212319-ffca-4d3f-9413-540d3b36ef63",
  "reviewer_id": "9fe2082a-d56f-43d2-b9f0-6c017e2d066b",
  "submitted_at": "2026-10-10T05:40:54Z",
  "overall_status": "REVIEWED_COMPLETE"
}
```

---

### Phase 7: State Immutability Verification (Security Gate)

Attempting to re-submit or alter an already finalized review:

```bash
curl -s -X POST http://localhost:8000/api/v1/analyses/33212319-ffca-4d3f-9413-540d3b36ef63/review \
  -H "Authorization: Bearer $REVIEWER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "decisions": [] }'
```

*Response (HTTP 409 Conflict):*
```json
{
  "error": {
    "code": "ANALYSIS_NOT_REVIEWABLE",
    "message": "Analysis 33212319-ffca-4d3f-9413-540d3b36ef63 is in status 'REVIEWED_COMPLETE' and cannot be reviewed"
  }
}
```
*Why this matters:* Validates clinical audit-trail immutability required under medical software standards.

---

## 5. Visual UI Showcase (Browser Guide)

| Interface | URL | Credentials | Demo Highlight |
| :--- | :--- | :--- | :--- |
| **Interactive Swagger API** | `http://localhost:8000/docs` | `operator1` / `Demo#12345`<br>`reviewer1` / `Demo#12345` | Real-time interactive testing of all ingestion, status, and review endpoints |
| **MinIO S3 Console** | `http://localhost:9001` | `minioadmin` / `minioadmin` | Show encrypted storage buckets (`prescripto` and `prescripto-retention`) |
| **Backend Health** | `http://localhost:8000/api/v1/health` | Public | Live health heartbeat |
| **ML Engine Health** | `http://localhost:8001/health` | Public | PP-OCRv6 status |

---

## 6. Teardown & Maintenance Commands

```bash
# View live logs of the worker as it processes jobs
docker compose logs -f worker

# View live logs of the ML service
docker compose logs -f ml-service

# Stop all containers safely without losing database data
docker compose stop

# Restart stopped containers
docker compose start

# Clean slate: Stop and wipe database/storage volumes
docker compose down -v
```
