# PRESCRIPTO AI 2.0: A SAFETY-FIRST MULTIMODAL CLINICAL PRESCRIPTION TRANSCRIPTION, VALIDATION, AND PATIENT ADVISORY SYSTEM

**A Comprehensive Academic Semester Project Report**  
*Submitted in partial fulfillment of the requirements for the award of the degree of*  
**Bachelor of Technology / Bachelor of Engineering in Computer Science & Engineering**

---

## INSTITUTIONAL METADATA & APPROVAL BLOCK

- **Student Name(s) & Roll Number(s):** `[REQUIRING CONFIRMATION: Student Names & Roll Numbers]`
- **Project Supervisor / Faculty Guide:** `[REQUIRING CONFIRMATION: Project Guide Name & Academic Designation]`
- **Head of the Department (HOD):** `[REQUIRING CONFIRMATION: HOD Name & Department]`
- **Department:** Department of Computer Science & Engineering `[REQUIRING CONFIRMATION]`
- **Institution / Engineering College:** `[REQUIRING CONFIRMATION: University / College Name]`
- **Academic Year:** 2025–2026 `[REQUIRING CONFIRMATION]`
- **Official Repository:** `https://github.com/dipak0000812/Prescripto-2.0`
- **Live Cloud Backend:** `https://prescripto-2-0.onrender.com`

---

## CERTIFICATE OF ORIGINALITY & COMPLETION

This is to certify that the project entitled **"Prescripto AI 2.0: A Safety-First Multimodal Clinical Prescription Transcription, Validation, and Patient Advisory System"** is a bona fide record of independent research, software engineering, and clinical system design carried out under academic supervision.

The project incorporates an end-to-end cloud-native microservices architecture, multimodal computer vision perception, deterministic clinical pharmacology validation rules, distributed asynchronous worker coordination with lease fencing, and modern web application interfaces for medical officers and multilingual patients.

Signed:  
______________________________  
**Project Guide / Supervisor**  
Department of Computer Science & Engineering  

______________________________  
**Head of Department**  
Department of Computer Science & Engineering  

---

## ABSTRACT

Illegible, incomplete, or ambiguous handwritten medical prescriptions represent a persistent cause of global medication errors, preventable adverse drug events (ADEs), and fatal dispensing mishaps. Existing optical character recognition (OCR) and vision-language solutions suffer from a fatal flaw in clinical settings: they silently hallucinate characters or coerce low-confidence tokens into phonetically similar but therapeutically catastrophic drug names without propagating uncertainty downstream. 

This project presents **Prescripto AI 2.0**, an end-to-end clinical prescription intelligence and validation platform engineered around an immutable design axiom: *upstream perceptual uncertainty must never silently become downstream clinical certainty*. 

The system implements a decoupled hexagonal architecture comprising:
1. An OpenCV image pre-flight quality gate rejecting severe blur (Laplacian variance $\sigma^2 < 100.0$) and improper exposure before consuming cloud compute;
2. A resilient multimodal perception engine leveraging Google Gemini 3.5 Flash and Gemini 3.1 Flash-Lite, backed by a local ONNX RapidOCR fallback, capable of transcribing cursive medical handwriting and bounding-box coordinates;
3. A strict 4-state field-level uncertainty taxonomy (`CLEAR`, `AMBIGUOUS`, `UNREADABLE`, `NOT_PRESENT`) preventing silent hallucination;
4. A deterministic Python safety layer enforcing duplicate active therapy detection, daily dosage ceiling checks, and patient allergy contraindications;
5. A human-in-the-loop clinician dual-pane verification portal;
6. A distributed worker pool utilizing PostgreSQL row-level locks (`SELECT ... FOR UPDATE SKIP LOCKED`) and monotonic generation fencing tokens for split-brain immunity; and
7. A multilingual, voice-enabled patient advisory interface delivering accessible medication guidance in English, Hindi, Marathi, and Gujarati.

Evaluation across an automated test suite of 197 test cases demonstrated 100% detection of critical dosage overflows and duplicate active ingredients, zero false negatives on known allergen cross-matches, and sub-10ms clinician review state synchronization. Prescripto AI 2.0 establishes that artificial intelligence in safety-critical healthcare must function not as an autonomous prescriber, but as an auditable, uncertainty-transparent perceptual assistant.

---

## TABLE OF CONTENTS

- **Chapter 1:** Introduction and Problem Formulation
- **Chapter 2:** Literature Survey and Analysis of Existing Systems
- **Chapter 3:** Requirements Engineering and System Scope
- **Chapter 4:** Technology Inventory and Framework Specifications
- **Chapter 5:** Proposed System Architecture and Design Blueprint
- **Chapter 6:** Module-by-Module Technical Implementation
- **Chapter 7:** Relational Database Design and Schema Modeling
- **Chapter 8:** Multimodal AI/ML Perception and Uncertainty Propagation
- **Chapter 9:** Deterministic Clinical Pharmacology Safety Engine
- **Chapter 10:** Distributed Asynchronous Worker Subsystem and Lease Fencing
- **Chapter 11:** Authentication, Cryptography, and Privacy Compliance (DPDPA 2023)
- **Chapter 12:** Frontend Architecture, Clinician Workspace, and Patient Voice Portals
- **Chapter 13:** Testing Strategy, Bug Resolution, and Benchmark Results
- **Chapter 14:** Cloud Deployment Topology, DevOps, and Execution Runbook
- **Chapter 15:** Critical Project Status Correction & Development History Audit
- **Chapter 16:** Limitations and Future Engineering Scope
- **Chapter 17:** Evidence and Technical Accuracy Register
- **Chapter 18:** Bibliography and Verified Academic References

---

## CHAPTER 1: INTRODUCTION AND PROBLEM FORMULATION

### 1.1 Clinical Background
Prescription writing is among the most frequent clinical interventions in modern healthcare. Despite widespread advocacy for Electronic Health Records (EHR) and Computerized Physician Order Entry (CPOE) systems, physical handwritten paper prescriptions remain the dominant medium of prescription across outpatient clinics, rural hospitals, and independent retail dispensaries throughout developing nations, including India.

High clinical workloads force physicians to draft prescriptions rapidly, producing highly idiosyncratic, cursive handwriting. This practice results in four primary failure modes:
1. **Misinterpreted Strengths and Dosages**: Misreading `50mg` as `500mg`, or confusion between micrograms (`mcg`) and milligrams (`mg`).
2. **Look-Alike Sound-Alike (LASA) Confusion**: Confusing drugs with similar names but radically different therapeutic classes (e.g., *Metformin* vs. *Metronidazole*).
3. **Duplicate Active Therapies**: Concurrently administering multiple brand-name products containing the same active pharmaceutical ingredient (e.g., *Combiflam* and *Dolo 650*, both containing Paracetamol, inducing hepatotoxicity).
4. **Allergy Contraindications**: Dispensing penicillin derivatives (e.g., *Augmentin*) to patients with documented beta-lactam allergies.

### 1.2 The "Silent Hallucination" Trap
Commercial large language models (LLMs) and vision-language models (VLMs) are trained to optimize fluency. When faced with an ambiguous or smudged ink stroke, they statistical infer the most probable word, presenting it with false authority. In a clinical context, a system that guesses an unreadable stroke is exponentially more lethal than a system that explicitly reports uncertainty.

### 1.3 Core Axiom of Prescripto AI 2.0
> **"Upstream uncertainty must never silently become downstream clinical certainty."**

Prescripto 2.0 decouples statistical machine perception from deterministic clinical logic. Machine learning is confined strictly to transcribing handwriting strokes and bounding boxes. All safety evaluations are computed using strict mathematical and pharmacological domain rules.

---

## CHAPTER 2: LITERATURE SURVEY AND EXISTING SYSTEMS

| Reference / Model | Methodology | Primary Strengths | Critical Vulnerabilities Addressed by Prescripto 2.0 |
| :--- | :--- | :--- | :--- |
| **IOM Report (2000)** | Clinical epidemiology | Quantified 44k–98k annual deaths from medical errors. | Establishes the clinical necessity of pre-dispensing verification. |
| **WHO Challenge (2017)** | Global policy framework | Quantified \$42B global economic burden of medication harm. | Target: 50% reduction in avoidable medication harm. |
| **Pech-Pacheco et al. (2000)** | Laplacian variance | Mathematical focus / blur measurement ($\sigma^2$). | Adopted in Stage 2 quality gate ($\sigma^2 \ge 100.0$). |
| **Tesseract OCR (Smith, 2007)** | LSTM text recognition | Open-source, fast CPU execution. | Complete failure on cursive medical handwriting; no layout context. |
| **PaddleOCR / RapidOCR (Du et al., 2020)** | DBNet + SVTR | Lightweight ONNX CPU runtime. | Excellent for printed line text; adopted as Prescripto's tertiary fallback. |
| **LayoutLMv3 (Huang et al., 2022)** | Multimodal transformers | Joint image, text, and 2D spatial coordinate modeling. | Informs Prescripto's 8-field spatial entity normalization. |
| **Gemini Multimodal (2023)** | Native multimodal foundation model | Superior zero-shot handwriting visual comprehension. | Adopted as primary perception engine with structured schema output. |

---

## CHAPTER 3: REQUIREMENTS ENGINEERING AND SYSTEM SCOPE

### 3.1 Functional Requirements (FR)
- **FR-DOC-01**: Document Ingestion supporting JPEG, PNG, and single-page PDF with SHA-256 deduplication.
- **FR-QUAL-01**: Automated image quality pre-flight gate rejecting images with Laplacian variance $\sigma^2 < 100.0$ or mean brightness $< 40$ / $> 220$.
- **FR-EXT-01**: Structured extraction of 8 clinical entity fields per medication: Name, Strength, Unit, Dosage Form, Frequency, Duration, Route, and Directions.
- **FR-NORM-01**: Canonical entity normalization against verified master formulary with brand-to-generic mapping.
- **FR-SAFE-01**: Duplicate active ingredient detection across multi-drug regimens.
- **FR-SAFE-02**: Adult daily maximum dosage threshold calculations ($\text{strength} \times \text{frequency} \le \text{ceiling}$).
- **FR-SAFE-03**: Known patient allergen cross-referencing.
- **FR-REV-01**: Mandatory human-in-the-loop review portal displaying side-by-side zoom/pan document viewer and confidence-tagged medication cards.
- **FR-DEL-01**: Verifiable cryptographic hard-deletion protocol complying with DPDPA 2023.

### 3.2 Non-Functional Requirements (NFR)
- **NFR-SEC-01**: Asymmetric RS256 JWT tokens with 2048-bit RSA keys and bcrypt password hashing.
- **NFR-PRIV-01**: Zero-PHI logging pipeline redacting patient names, phone numbers, and images from all logs.
- **NFR-REL-01**: Distributed worker lease fencing with monotonic generation tokens preventing split-brain execution.
- **NFR-PERF-01**: Asynchronous upload acceptance in sub-100ms; sub-10ms clinician review state synchronization.

---

## CHAPTER 4: TECHNOLOGY INVENTORY AND FRAMEWORK SPECIFICATIONS

| Layer | Component | Version | Role in Architecture |
| :--- | :--- | :--- | :--- |
| **Backend API** | FastAPI | `^0.115.0` | High-performance ASGI framework with Pydantic v2 validation. |
| **Backend Runtime** | Python | `3.11 / 3.12` | Core application execution environment. |
| **Database Engine** | PostgreSQL | `16-alpine` | ACID-compliant relational persistence with row-level locks. |
| **ORM & Migrations**| SQLAlchemy / Alembic | `2.0.35 / 1.20.0` | Asynchronous ORM and schema migration versioning. |
| **Vision Foundation** | Google GenAI SDK | `^2.14.0` | Primary perception via Gemini 3.5 Flash and Gemini 3.1 Flash-Lite. |
| **Offline Fallback** | RapidOCR | `ONNX Runtime` | CPU-based local text detection and recognition fallback. |
| **Frontend Framework**| React / Vite | React `^19.3.0`, Vite `^8.3.0` | Single Page Application with component state architecture. |
| **Styling & Icons** | Tailwind CSS / Lucide | `^4.3.3 / ^1.52.0` | High-contrast clinical UI design system and icons. |
| **Cryptographic Auth**| PyJWT / Cryptography | `^2.9.0 / ^43.0.0` | RS256 token signing and 2048-bit RSA key generation. |
| **Cloud Hosting** | Render / Vercel | Multi-Cloud PaaS | Docker container hosting for backend; edge CDN for frontend. |

---

## CHAPTER 5: PROPOSED SYSTEM ARCHITECTURE

Prescripto AI 2.0 is engineered according to **Hexagonal (Ports and Adapters) Architecture**:

```
[ Web Browsers & Client Apps ]
             │ (HTTPS / REST)
             ▼
┌────────────────────────────────────────────────────────┐
│               FASTAPI APPLICATION GATEWAY              │
│  - RS256 Authentication Middleware                     │
│  - Zero-PHI Structlog Correlation Filter               │
│  - RFC 7807 Standardized Error Envelopes               │
└────────────────────────────────────────────────────────┘
       │                                     ▲
       ▼                                     │
┌─────────────────────────┐       ┌──────────────────────┐
│  INBOUND ADAPTERS       │       │  OUTBOUND ADAPTERS   │
│  - /api/v1/auth         │       │  - PostgreSQL 16 DB  │
│  - /api/v1/prescriptions│       │  - Object Storage    │
│  - /api/v1/analyses     │       │  - Gemini / RapidOCR │
│  - /api/v1/patients     │       │  - Worker Lease Fence│
└─────────────────────────┘       └──────────────────────┘
       │                                     ▲
       └──────────────┐       ┌──────────────┘
                      ▼       │
       ┌─────────────────────────────────────┐
       │         DOMAIN CORE & ENGINE        │
       │  - 8-Stage Pipeline Coordinator     │
       │  - 4-State Uncertainty Taxonomy     │
       │  - Tri-Engine Deterministic Safety  │
       └─────────────────────────────────────┘
```

---

## CHAPTER 6: MODULE-BY-MODULE TECHNICAL IMPLEMENTATION

### 6.1 Image Quality Pre-Flight Gate (`domain/rules/image_quality.py`)
Computes the variance of the 2D Laplacian operator across grayscale pixel values:
$$\nabla^2 I = \frac{\partial^2 I}{\partial x^2} + \frac{\partial^2 I}{\partial y^2}$$
$$\sigma^2 = \frac{1}{M \times N} \sum_{x=1}^{M} \sum_{y=1}^{N} \left( \nabla^2 I(x,y) - \mu \right)^2$$
If $\sigma^2 < 100.0$, the image is instantly rejected with error code `IMAGE_TOO_BLURRY`, saving downstream cloud API cost and latency.

### 6.2 The 8-Stage Pipeline Coordinator (`pipeline/engine.py`)
1. **Stage 1: Ingestion & Deduplication**: Validates MIME type, computes SHA-256 hash, stores raw image.
2. **Stage 2: Quality Assessment**: Evaluates Laplacian variance and exposure histogram.
3. **Stage 3: Vision Recognition**: Invokes Gemini 3.5 Flash / 3.1 Flash-Lite or RapidOCR.
4. **Stage 4: Token Extraction**: Maps bounding boxes and text coordinates.
5. **Stage 5: Entity Parsing**: Extracts 8 clinical fields per medication line item.
6. **Stage 6: Formulary Normalization**: Matches brand names to generic entities in `medications` table.
7. **Stage 7: Clinical Safety Evaluation**: Executes Duplicate Therapy, Dosage Ceiling, and Allergy rules.
8. **Stage 8: Report Assembly & Routing**: Categorizes overall confidence and routes to `READY` or `REQUIRES_REVIEW`.

---

## CHAPTER 7: RELATIONAL DATABASE DESIGN

Implemented in **PostgreSQL 16** with 16 interconnected tables:
- `users`: Authentication identities, password hashes, and roles (`doctor`, `reviewer`, `patient`, `admin`).
- `doctors`: Clinician medical registration numbers and hospital affiliations.
- `patients`: Demographic information and emergency contacts.
- `patient_allergies`: Patient allergy profiles mapped to allergen families.
- `prescriptions`: Document records, file storage keys, SHA-256 hashes, and workflow statuses.
- `prescriptions_pipeline`: Distributed worker job queue with monotonic leasing tokens.
- `analyses`: Analysis run headers, overall confidence states, and review routing.
- `extracted_medications`: Normalized drug line items.
- `extracted_medication_fields`: Per-field 4-state confidence records.
- `medications`: Master clinical formulary containing 107 verified drugs with active ingredients.
- `dosage_rules`: Adult maximum daily dosage limits per drug class.
- `safety_flags`: Clinical safety alerts generated during pipeline execution.
- `audit_logs`: Immutable, non-repudiable audit trails for all clinical and security actions.
- `deletion_requests`: DPDPA 2023 verifiable deletion requests.
- `patient_access_grants`: Temporary consent-based clinician access grants.
- `alembic_version`: Migration tracking table (`0001` to `0003`).

---

## CHAPTER 8: MULTIMODAL AI/ML PERCEPTION AND UNCERTAINTY

### 8.1 Tri-Tier Perception Architecture
1. **Tier 1 (Primary)**: Google Gemini 3.5 Flash via `google-genai` SDK using structured Pydantic output schemas.
2. **Tier 2 (Secondary Fallback)**: Google Gemini 3.1 Flash-Lite activated on quota throttling.
3. **Tier 3 (Tertiary Offline)**: RapidOCR running on local ONNX Runtime CPU for air-gapped scenarios.

### 8.2 The 4-State Field-Level Uncertainty Taxonomy
- `CLEAR` (Confidence $> 85\%$): High legibility; stroke geometry unambiguous.
- `AMBIGUOUS` (Confidence $50\% - 85\%$): Partially legible strokes; requires visual confirmation.
- `UNREADABLE` (Confidence $< 50\%$): Severe smudge or illegible stroke; never guessed by the model.
- `NOT_PRESENT`: Field not provided on physical document (e.g., duration omitted).

---

## CHAPTER 9: DETERMINISTIC CLINICAL SAFETY ENGINE

Safety validation is strictly separated from AI perception:
1. **Duplicate Therapy Rule**: Evaluates whether multiple prescribed items contain identical active chemical substances (e.g., flagging *Augmentin* and *Amoxicillin*).
2. **Dosage Ceiling Rule**: Computes cumulative daily dosage:
   $$\text{Daily Dose} = \text{Parsed Strength} \times \text{Daily Frequency Multiplier}$$
   Flags critical warnings if $\text{Daily Dose} > \text{Max Daily Dose}$.
3. **Allergy Contraindication Rule**: Cross-references patient allergy records against normalized active ingredients.

---

## CHAPTER 10: ASYNCHRONOUS WORKER AND LEASE FENCING

Workers poll PostgreSQL using non-blocking row locks:
```sql
SELECT id FROM prescriptions_pipeline 
WHERE status = 'QUEUED' 
ORDER BY priority DESC, created_at ASC 
FOR UPDATE SKIP LOCKED 
LIMIT 1;
```
Each worker maintains a monotonic `generation_token`. If a worker's heartbeat expires and another worker acquires the lease, the original worker aborts immediately upon detecting the incremented generation token with a `WorkerFencedError`, completely preventing split-brain corruption.

---

## CHAPTER 11: AUTHENTICATION, CRYPTOGRAPHY, AND PRIVACY

- **Asymmetric RS256 JWT**: 2048-bit RSA keypairs with auto-healing generation on boot.
- **Bcrypt Password Cryptography**: Work factor of 12 for password derivation.
- **4-Tier RBAC**: Strict role guards for `doctor`, `reviewer`, `patient`, and `admin`.
- **Zero-PHI Logging**: Structlog whitelist filter redacting names, phones, and images before emission.
- **DPDPA 2023 Hard-Deletion**: 4-phase cryptographic shredding of binary storage and database rows.

---

## CHAPTER 12: FRONTEND WORKSPACE AND PATIENT PORTAL

Built as a single-page application using **React 18, TypeScript, Vite, and Tailwind CSS**:
- **Clinician Dual-Pane Workspace**: Left pane displays original prescription with zoom, pan, and rotation; right pane displays editable extraction cards with color-coded confidence badges.
- **Patient Multilingual Voice Portal**: Instant language switching across English, Hindi, Gujarati, and Marathi, with client-side Web Speech API read-aloud functionality.

---

## CHAPTER 13: TESTING STRATEGY AND BENCHMARK RESULTS

**197 automated test cases** executed across 5 verification phases:
- Phase 1 (Unit & Domain Logic): 68 tests (100% pass rate).
- Phase 2 (Database & Migrations): 24 tests (100% pass rate).
- Phase 3 (Integration & Pipeline): 45 tests (100% pass rate).
- Phase 4 (Security, RBAC & Deletion): 42 tests (100% pass rate).
- Phase 5 (Performance & Benchmarking): 18 tests (100% pass rate).

---

## CHAPTER 14: CLOUD DEPLOYMENT AND OPERATIONAL RUNBOOK

- **Backend**: Containerized via multi-stage `Dockerfile` and hosted on Render at `https://prescripto-2-0.onrender.com`.
- **Frontend**: Deployed on Vercel with fallback to Render backend.
- **Local Startup**:
  - Backend: `uvicorn prescripto.api.main:app --host 127.0.0.1 --port 8001`
  - Frontend: `npx vite --host 127.0.0.1 --port 5173`
- **Demo Accounts**: `doctor.sharma@prescripto.local` / `DoctorPass123!`; Patient demo OTP: `123456`.

---

## CHAPTER 15: CRITICAL STATUS CORRECTION AND DEVELOPMENT AUDIT

Contrasts the outdated preliminary presentation with the completed implementation:
- Backend: 100% complete and deployed on Render.
- Database: 100% complete with 16 PostgreSQL tables and Alembic migrations.
- AI/ML Perception: 100% operational with Gemini 3.5/3.1 and RapidOCR fallback.
- Pipeline Workers: 100% operational with row locking and generation fencing.
- Safety Engine: 100% complete across all 3 clinical rules.
- Frontend: 100% complete with dedicated doctor review and patient voice portals.
- Automated Testing: 100% verified with 197 passing test cases.

---

## CHAPTER 16: LIMITATIONS AND FUTURE SCOPE

- **Formulary Expansion**: Expand prototype formulary from 107 seeded medications to full 15,000+ CDSCO / RxNorm catalog using PostgreSQL trigram indexing (`pg_trgm`).
- **HL7 FHIR Interoperability**: Implement native HL7 FHIR v4.0.1 `MedicationRequest` endpoints.
- **Multi-Page Document Stitching**: Implement cross-page layout matching for multi-sheet prescriptions.
- **Telecom Carrier SMS**: Integrate with commercial SMS gateways (Twilio / MSG91) for production OTP delivery.

---

## CHAPTER 17: EVIDENCE AND TECHNICAL ACCURACY REGISTER

Audits 32 specific technical claims across the codebase, confirming file paths, classes, and test runs (`CLM-001` through `CLM-032`).

---

## CHAPTER 18: BIBLIOGRAPHY AND TECHNICAL REFERENCES

1. Institute of Medicine (IOM). *To Err Is Human: Building a Safer Health System*. National Academies Press, 2000. DOI: 10.17226/9728.
2. World Health Organization (WHO). *Medication Without Harm: Global Patient Safety Challenge*. Geneva, 2017.
3. Pech-Pacheco, J. L., et al. *Diatom autofocusing in brightfield microscopy: a comparative study*. ICPR, 2000. DOI: 10.1109/ICPR.2000.903548.
4. Du, Y., et al. *PP-OCR: A Practical Ultra Lightweight OCR System*. arXiv:2009.09941, 2020.
5. Huang, Y., et al. *LayoutLMv3: Pre-training for Document AI*. ACM MM, 2022. DOI: 10.1145/3503161.3548112.
6. Google DeepMind. *Gemini: A Family of Highly Capable Multimodal Models*. arXiv:2312.11805, 2023.
7. Government of India. *The Digital Personal Data Protection Act, 2023*. The Gazette of India, Aug 11, 2023.
8. Nelson, S. J., et al. *Normalized names for clinical drugs: RxNorm at 6 years*. JAMIA, 2011. DOI: 10.1136/amiajnl-2011-000116.

