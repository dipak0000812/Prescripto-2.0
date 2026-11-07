# Prescripto AI 2.0 — Complete Technical Stack Inventory

**Document ID:** `DOC-03-STACK`  
**Classification:** Academic Engineering Dossier  
**Canonical Spec Reference:** [backend/requirements.txt](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/backend/requirements.txt), [web/package.json](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/web/package.json), [docker-compose.yml](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/docker-compose.yml)  
**Date of Extraction:** November 4, 2026  

---

## 1. Backend Core & Application Framework

| Component | Library / Binary | Version in Repo | Exact Purpose | File References |
| :--- | :--- | :--- | :--- | :--- |
| **Language Runtime** | Python | `3.11` / `3.12` | Core backend execution runtime | [Dockerfile](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/Dockerfile), [.github/workflows/ci.yml](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/.github/workflows/ci.yml) |
| **API Framework** | FastAPI | `0.115.0` | Asynchronous REST API routing, request validation, OpenAPI auto-generation | [backend/prescripto/api/main.py](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/backend/prescripto/api/main.py) |
| **ASGI Engine** | Starlette / Uvicorn | Uvicorn `0.32.0`, Starlette `0.38.6` | HTTP server execution, reverse-proxy header propagation (`--proxy-headers`) | [backend/prescripto/api/main.py](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/backend/prescripto/api/main.py) |
| **Data Validation** | Pydantic v2 | `>=2.10.0, <3.0.0` | Strict schema serialization, input validation, custom field validators | [backend/prescripto/api/v1/schemas/](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/backend/prescripto/api/v1/schemas/) |
| **Settings Management**| Pydantic Settings | `2.6.0` | Multi-source environment loading (`.env`, `backend/.env`, system env vars) | [backend/prescripto/config/settings.py](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/backend/prescripto/config/settings.py) |
| **Structured Logging** | Structlog | `24.4.0` | High-performance JSON logging with custom Zero-PHI whitelist processors | [backend/prescripto/audit/logger.py](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/backend/prescripto/audit/logger.py) |
| **HTTP Client** | HTTPX | `0.28.1` | Asynchronous HTTP requests, TestClient execution, integration test harness | [backend/requirements.txt](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/backend/requirements.txt) |

---

## 2. Relational Database & Persistence Layer

| Component | Library / Binary | Version in Repo | Exact Purpose | File References |
| :--- | :--- | :--- | :--- | :--- |
| **Database Engine** | PostgreSQL | `16-alpine` | Relational storage, ACID transactions, `FOR UPDATE SKIP LOCKED` worker queue | [docker-compose.yml](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/docker-compose.yml), [render.yaml](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/render.yaml) |
| **Lightweight Engine** | SQLite3 | Native Python 3.11 | Hermetic unit test execution and isolated developer environment | [backend/prescripto/db/session.py](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/backend/prescripto/db/session.py) |
| **ORM Framework** | SQLAlchemy | `2.0.35` | Object-Relational Mapping, connection pooling, database session management | [backend/prescripto/db/session.py](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/backend/prescripto/db/session.py) |
| **Schema Migrations** | Alembic | `1.20.0` | Versioned schema migration scripts (`0001`, `0002`, `0003`) | [backend/prescripto/db/migrations/](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/backend/prescripto/db/migrations/) |
| **Postgres Driver** | Psycopg2-binary | `2.9.10` | Low-level C-based PostgreSQL database adapter | [backend/requirements.txt](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/backend/requirements.txt) |

---

## 3. Machine Learning, Computer Vision & Perception

| Component | Library / SDK | Version in Repo | Exact Purpose | File References |
| :--- | :--- | :--- | :--- | :--- |
| **Primary Vision SDK**| Google GenAI SDK | `2.14.0` | Cloud multimodal vision extraction using `gemini-3.5-flash` and `gemini-3.1-flash-lite` | [backend/prescripto/ml/recognition_providers.py](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/backend/prescripto/ml/recognition_providers.py) |
| **Local OCR Runtime** | RapidOCR (ONNX) | `rapidocr-onnxruntime` | Offline CPU-based handwriting/printed OCR fallback when Gemini is unavailable | [backend/prescripto/ml/rapid_runtime.py](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/backend/prescripto/ml/rapid_runtime.py) |
| **Image Processing** | Pillow (PIL) | `10.4.0` | Image decoding, resizing, thumbnail generation, color-space conversion | [backend/prescripto/pipeline/engine.py](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/backend/prescripto/pipeline/engine.py) |
| **Computer Vision** | OpenCV Headless | `4.10.0.84` | Laplacian blur variance calculation, contrast and exposure threshold gates | [ml/ocr/quality_check.py](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/ml/ocr/quality_check.py) |
| **Detection Backbone**| PaddleOCR DBNet++ | Configured in `ml/` | Bounding box text detection candidate fine-tuned on prescription margins | [ml/ocr/PP-OCRv6_small_rxhandbd.yml](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/ml/ocr/PP-OCRv6_small_rxhandbd.yml) |

---

## 4. Security, Cryptography & Object Storage

| Component | Library / Protocol | Version in Repo | Exact Purpose | File References |
| :--- | :--- | :--- | :--- | :--- |
| **JWT Tokens** | PyJWT | `2.9.0` | Asymmetric RS256 token encoding and decoding with expiration checks | [backend/prescripto/auth/crypto.py](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/backend/prescripto/auth/crypto.py) |
| **Cryptographic Lib** | Cryptography | `43.0.3` | 2048-bit RSA keypair generation, PKCS8 serialization, and verification | [backend/prescripto/config/settings.py](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/backend/prescripto/config/settings.py) |
| **Password Hashing** | Bcrypt | `4.2.0` | Salted SHA-256 bcrypt hashing for clinician and administrator credentials | [backend/prescripto/auth/crypto.py](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/backend/prescripto/auth/crypto.py) |
| **Object Store SDK** | Boto3 / Botocore | `1.35.40` | S3-compatible object storage communication, bucket lifecycle, presigned URLs | [backend/prescripto/storage/client.py](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/backend/prescripto/storage/client.py) |
| **Signed URL Auth** | HMAC-SHA256 | Native Python `hmac` | Ephemeral 60-second presigned URLs for local storage streaming | [backend/prescripto/storage/client.py](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/backend/prescripto/storage/client.py) |

---

## 5. Frontend UI & Client Technology

| Component | Technology | Version in Repo | Exact Purpose | File References |
| :--- | :--- | :--- | :--- | :--- |
| **UI Framework** | React | `^19.3.0` | Declarative component hierarchy, virtual DOM, reactivity | [web/package.json](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/web/package.json) |
| **Language** | TypeScript | `~6.0.2` | Compile-time type safety, interface contracts matching backend DTOs | [web/tsconfig.json](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/web/tsconfig.json) |
| **Build & Bundler** | Vite | `^8.3.0` | Instant HMR development server, optimized rollup asset chunking | [web/vite.config.ts](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/web/vite.config.ts) |
| **Styling Engine** | Tailwind CSS v4 | `^4.3.3` | Utility-first responsive design, humanized clinical light color tokens | [web/src/index.css](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/web/src/index.css) |
| **Client Router** | React Router DOM | `^7.18.4` | Single-page application routing, route guards (`RequireRole`), SPA fallback | [web/src/App.tsx](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/web/src/App.tsx) |
| **HTTP Interceptor**| Axios | `^1.20.0` | Global token injection, auto-refresh queue on 401, UUID `X-Request-ID` generation | [web/src/api/client.ts](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/web/src/api/client.ts) |
| **Iconography** | Lucide React | `^1.52.0` | Medical iconography (pills, stethoscopes, warnings, shields, arrows) | [web/src/components/](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/web/src/components/) |
| **Voice Synthesis** | Web Speech API | Native Browser | High-clarity spoken audio readouts for patients in 4 Indian languages | [web/src/pages/PatientPortalPage.tsx](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/web/src/pages/PatientPortalPage.tsx) |

---

## 6. Infrastructure, Containerization & CI/CD

| Platform / Tool | Role in Project | Configuration File | Verified Behavior |
| :--- | :--- | :--- | :--- |
| **Docker Multi-Stage** | Compiles React Vite into static dist and bundles with Python runtime | [Dockerfile](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/Dockerfile) | Validated on Debian 12 slim |
| **Docker Compose** | Local orchestration: `api`, `worker`, `postgres`, `minio`, `createbuckets` | [docker-compose.yml](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/docker-compose.yml) | Verified with ports 8000, 5435, 9000, 9001 |
| **Render Cloud** | Backend API hosting, managed PostgreSQL, auto-deploy from `main` | [render.yaml](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/render.yaml) | Verified at `prescripto-2-0.onrender.com` |
| **Vercel** | Frontend static site deployment with SPA routing rewrites | [vercel.json](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/vercel.json), [web/vercel.json](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/web/vercel.json) | Verified client-side URL routing |
| **GitHub Actions** | Automated CI pipeline: dependency installation, linting, and pytest suites | [.github/workflows/ci.yml](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/.github/workflows/ci.yml) | Runs on push to `main` |

