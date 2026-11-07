# 20. Project Execution, Local Setup, and Operational Runbook — Prescripto AI 2.0

**Document Reference:** `DOC-20-RUNBOOK`  
**Classification:** Operational Runbook & Execution Manual  
**Repository Reference:** `https://github.com/dipak0000812/Prescripto-2.0` (Branch `main`)  
**Deployment Backend:** `https://prescripto-2-0.onrender.com`  
**Date:** November 5, 2026  

---

## 1. Quick Access and Service Topology

| Subsystem | URL / Port | Technology | Purpose |
| :--- | :--- | :--- | :--- |
| **Frontend Dev Server** | `http://localhost:5173/` | React 18, Vite, Tailwind | Hot-reloading clinician and patient web portal with live API proxying. |
| **Backend API Gateway** | `http://localhost:8001/` | FastAPI, Uvicorn, Python 3.12 | Core REST API gateway, authentication, and root SPA static file host. |
| **Interactive API Documentation** | `http://localhost:8001/docs` | Swagger UI / OpenAPI 3.0 | Interactive testing harness for all 21 REST endpoints. |
| **Alternative API Documentation** | `http://localhost:8001/redoc` | ReDoc | Human-readable API specifications and schema models. |
| **System Diagnostics** | `http://localhost:8001/health` | FastAPI Health Router | Database pool, storage, and worker heartbeat checks. |
| **Database Pool Diagnostics** | `http://localhost:8001/health/db` | SQLAlchemy 2.0 | PostgreSQL / SQLite active connection pool metrics. |
| **Live Cloud Backend** | `https://prescripto-2-0.onrender.com` | Render Docker PaaS | Publicly accessible production backend instance. |

> **Port Allocation Notice**: Port `8001` is utilized locally for the FastAPI backend because Windows Hyper-V / Docker dynamically reserves port `8000`. The Vite development configuration (`web/vite.config.ts`) automatically proxies `/api` requests to `http://127.0.0.1:8001`.

---

## 2. Pre-Seeded Demonstration Accounts

The local database (`prescripto.db`) and cloud production databases are pre-populated with authenticated test roles:

### 2.1 Clinician / Reviewer Portal
- **Login URL**: `http://localhost:5173/login` (or `http://localhost:8001/login`)
- **Email Address**: `doctor.sharma@prescripto.local`
- **Username**: `doctor_sharma` *(or administrative user: `admin`)*
- **Password**: `DoctorPass123!` *(or `AdminPass123!`)*
- **Assigned Role**: `REVIEWER` (Grants access to dual-pane prescription review, bounding boxes, safety flags, and clinical sign-off).
- **One-Click Feature**: Use the **"Click to Autofill"** button directly on the login card.

### 2.2 Patient Mobile Voice Portal
- **Login URL**: `http://localhost:5173/patient-portal` (or toggle on login page)
- **Mobile Number**: Any valid 10-digit mobile number (e.g., `9876543210`)
- **Demo Verification OTP**: `123456`
- **Supported Languages**: English, Hindi (हिन्दी), Gujarati (ગુજરાતી), Marathi (मराठी) with client-side Web Speech API audio narration.

---

## 3. Step-by-Step Local Startup Instructions

### Prerequisites
- Python 3.11 or 3.12 installed on host machine.
- Node.js v20+ or v22+ and npm 10+.
- Microsoft Windows, macOS, or Linux.

### Terminal 1: Launch Backend API Gateway
```powershell
# Navigate to project root
cd c:\Users\pbhus\Desktop\Priscption-project\Prescripto-2.0

# Activate virtual environment and set Python module path
$env:PYTHONPATH="backend"

# Start Uvicorn ASGI server on port 8001
.\.venv\Scripts\python.exe -m uvicorn prescripto.api.main:app --host 127.0.0.1 --port 8001
```

### Terminal 2: Launch Frontend Development Server
```powershell
# Navigate to web application directory
cd c:\Users\pbhus\Desktop\Priscption-project\Prescripto-2.0\web

# Start Vite server with host exposure
npx vite --host 127.0.0.1 --port 5173
```

---

## 4. Automated Verification and Test Execution

The system maintains 197 automated test cases verifying all modules. To re-run the verification suites locally:

```powershell
$env:PYTHONPATH="backend"

# Execute Phase 1: Unit & Domain Logic Suite (68 tests)
.\.venv\Scripts\python.exe backend/scripts/run_phase1_api_suite.py

# Execute Phase 2: Database Schema & Migration Suite (24 tests)
.\.venv\Scripts\python.exe backend/scripts/run_phase2_database_suite.py

# Execute Phase 3: Integration & Pipeline Worker Suite (45 tests)
.\.venv\Scripts\python.exe backend/scripts/run_phase3_security_suite.py

# Execute Phase 4: Security, RBAC & DPDPA Deletion Suite (42 tests)
.\.venv\Scripts\python.exe backend/scripts/run_phase4_e2e_suite.py

# Execute Phase 5: Performance Benchmarks (18 tests)
.\.venv\Scripts\python.exe backend/scripts/run_phase5_performance_suite.py
```

---

## 5. Live Cloud Deployment Synchronization

- **GitHub Repository**: `https://github.com/dipak0000812/Prescripto-2.0` (Branch `main`)
- **Render Auto-Deployment**: Render tracks `main` branch commits automatically.
- **Vercel Web App**: Connects to Render backend via `DEFAULT_API_BASE = 'https://prescripto-2-0.onrender.com'` configured in `web/src/api/client.ts`.

