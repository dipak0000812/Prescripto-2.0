# 14. Technical Limitations and Future Scope — Prescripto AI 2.0

This document records the genuine technical, clinical, architectural, and operational limitations of the Prescripto AI 2.0 system as verified in the repository (`https://github.com/dipak0000812/Prescripto-2.0`), alongside a realistic, evidence-backed engineering roadmap for future iterations.

---

## 1. Confirmed Technical and Architectural Limitations

Every limitation documented below is verified against source code, configuration files, and test suites.

### 1.1 Formulary Coverage and Lexical Scope
- **Current State**: The active clinical formulary seeded in `backend/scripts/seed_medications.py` contains exactly **107 distinct medications** (across antibiotics, analgesics, antihypertensives, antidiabetics, and antihistamines).
- **Limitation**: Real-world clinical practice encompasses over 15,000 approved drug formulations (under CDSCO in India or FDA in the US). Rare drugs, specialized oncology agents, biologics, pediatric elixirs, and niche topical formulations will result in `NOT_FOUND` during candidate matching.
- **Evidence**: `backend/scripts/seed_medications.py` lines 18–180; `backend/prescripto/domain/rules/medication_matching.py`.

### 1.2 Drug-Drug Interaction (DDI) Matrix Exclusion
- **Current State**: The safety engine implements three deterministic rules:
  1. *Duplicate Active Ingredient Detection* (`backend/prescripto/domain/rules/duplicate_therapy.py`)
  2. *Maximum Daily Dosage Thresholds* (`backend/prescripto/domain/rules/dosage_safety.py`)
  3. *Patient Known Allergy Contraindications* (`backend/prescripto/domain/rules/allergy_cross_match.py`)
- **Limitation**: Complex cross-class Drug-Drug Interactions (DDIs) (e.g., Warfarin + NSAID bleeding risks, ACE inhibitors + Potassium-sparing diuretics) are deliberately omitted from V1. This was an architectural decision driven by the lack of an open-access, clinically validated DDI knowledge graph with indemnity licensing.
- **Evidence**: `backend/prescripto/pipeline/engine.py` (only the 3 safety stages are executed).

### 1.3 Single-Page Document Scope
- **Current State**: The document ingestion pipeline (`POST /api/v1/prescriptions/upload`) ingests a single document payload per prescription record (`image/jpeg`, `image/png`, or single-page PDF).
- **Limitation**: Clinical encounters frequently generate multi-page documents (e.g., page 1: clinical diagnosis and advice; page 2: itemized Rx table; page 3: laboratory orders). Prescripto 2.0 does not currently implement multi-page image stitching, pagination correlation, or cross-page medication reconciliation.
- **Evidence**: `backend/prescripto/api/v1/routers/prescriptions.py`, `Prescription` database model (`image_hash` and `original_filename` assume 1:1 image mapping).

### 1.4 Multimodal Vision Latency and Rate Limit Dependency
- **Current State**: Primary handwriting perception relies on Google Gemini 3.5 Flash / 3.1 Flash-Lite via the `google-genai` SDK (`backend/prescripto/ml/recognition_providers.py`).
- **Limitation**:
  1. Network round-trip and LLM multimodal inference latency averages **2.1 to 3.8 seconds per prescription**, precluding sub-second real-time video stream scanning.
  2. Cloud API dependence introduces quota and throttling risks during peak emergency room triage surges.
  3. While a tertiary local fallback exists (`RapidOCR` with ONNX CPU runtime in `backend/prescripto/ml/rapid_runtime.py`), RapidOCR performs printed line text extraction and lacks handwriting multimodal layout intelligence.
- **Evidence**: `backend/prescripto/ml/runtime.py`, `backend/scripts/run_phase5_performance_suite.py`.

### 1.5 Patient Authentication via Demo OTP
- **Current State**: Doctor and staff authentication utilizes secure RS256 asymmetric JWTs and bcrypt passwords (`backend/prescripto/api/v1/routers/auth.py`). However, patient mobile OTP authentication currently defaults to a mock SMS handler accepting fixed OTP `123456` in testing and staging environments.
- **Limitation**: Production deployment requires integration with a licensed telecom SMS / WhatsApp Business API gateway (e.g., Twilio, MSG91, AWS SNS) to deliver one-time cryptographically random tokens to Indian (+91) phone numbers.
- **Evidence**: `backend/prescripto/api/v1/routers/auth.py` lines 112–148 (`verify_otp` endpoint logic).

### 1.6 Multilingual Speech Synthesis Delivery
- **Current State**: The patient portal (`web/src/pages/PatientPortal.tsx`) supports 4 regional languages (English, Hindi, Marathi, Gujarati). Explanations are translated via Gemini with simple readability prompts (`backend/prescripto/application/services/llm_explainer.py`).
- **Limitation**: Text-to-speech audio playback relies on the browser's native client-side Web Speech API (`window.speechSynthesis`). Voice quality, dialect fidelity, and pronunciation vary across end-user devices, operating systems, and browsers (e.g., iOS Safari vs. Android Chrome).
- **Evidence**: `web/src/pages/PatientPortal.tsx`, `backend/prescripto/application/services/llm_explainer.py`.

### 1.7 Healthcare Standards and EHR Interoperability
- **Current State**: Data exchange is governed by JSON REST APIs defined in OpenAPI v3.0 schemas (`backend/OPENAPI.yaml`).
- **Limitation**: The system does not natively ingest or export standard HL7 FHIR (Fast Healthcare Interoperability Resources) v4.0.1 resources (such as `MedicationRequest`, `Patient`, `DocumentReference`, `Bundle`) or DICOM imaging wrappers. Direct integration into enterprise hospital information systems (Epic Systems, Cerner, Allscripts) requires custom middleware.
- **Evidence**: `backend/prescripto/api/v1/routers/`, lack of `fhirclient` in `backend/requirements.txt`.

---

## 2. Realistic Future Engineering Scope

The following enhancements represent natural technical extensions that align with the existing architecture and database models:

```mermaid
flowchart TD
    subgraph Phase 1: Near-Term Enhancements
        F1["Formulary Scale-Up\n(15k+ CDSCO/RxNorm Drugs)"]
        F2["PostgreSQL pg_trgm\nFuzzy Search Indexing"]
        F3["SMS Gateway Integration\n(Twilio / MSG91)"]
    end

    subgraph Phase 2: Core ML & Pipeline Upgrades
        M1["Domain-Specific Handwriting Model\n(Fine-tuned on RxHandBD / IAM)"]
        M2["Multi-Page Stitching &\nDocument PDF Parsing"]
        M3["Open-Source DDI Graph Engine\n(DrugBank / NLM RxNav Adapter)"]
    end

    subgraph Phase 3: Clinical Interoperability & Edge
        E1["HL7 FHIR v4.0.1 Importer/Exporter\n(MedicationRequest Bundles)"]
        E2["Server-Side Neural TTS\n(Bhashini / Google Cloud TTS)"]
        E3["On-Premises Edge Vision Inference\n(Triton Inference Server / TensorRT)"]
    end

    Phase 1 --> Phase 2
    Phase 2 --> Phase 3
```

### 2.1 Near-Term Enhancements (Architecture & Infrastructure)
1. **Full National Formulary Integration**:
   - Ingest the official CDSCO (Central Drugs Standard Control Organisation) national list of essential medicines and the NLM RxNorm knowledge base.
   - Implement PostgreSQL trigram indices (`CREATE EXTENSION pg_trgm; CREATE INDEX idx_med_trgm ON medications USING GIN (name gin_trgm_ops);`) to maintain sub-10ms fuzzy text lookup across 100,000+ brand and generic variants.
2. **Production SMS & WhatsApp Notification Service**:
   - Replace the demo OTP engine with an asynchronous worker pipeline delivering time-based one-time passwords (TOTP) and prescription dispensing reminders over SMS/WhatsApp.
3. **Redis Caching Layer for Drug Metadata**:
   - Deploy a Redis 7.x caching cluster in front of PostgreSQL to cache verified drug monographs, dosage ranges, and active ingredient maps, reducing database read load during batch imports.

### 2.2 Medium-Term Enhancements (Vision & Perception)
1. **Fine-Tuning on Indian Medical Handwriting Datasets**:
   - Fine-tune open-weights vision backbones (e.g., Donut, Nougat, or TrOCR) on domain-specific medical handwriting corpora such as RxHandBD.
   - Containerize local inference via Triton Inference Server with NVIDIA TensorRT acceleration to achieve sub-second on-premises execution without cloud API egress.
2. **Multi-Page & Double-Sided PDF Stitching Engine**:
   - Enhance the image intake pipeline to accept multi-page TIFF and PDF documents.
   - Implement perceptual layout graph matching to track continuous prescription sections across physical page boundaries.
3. **Clinically Validated DDI Knowledge Graph**:
   - Partner with or license an open-access clinical pharmacology database (such as NLM RxNav or DrugBank academic tier) to introduce severity-stratified drug interaction warnings (Contraindicated, Major, Moderate, Minor).

### 2.3 Long-Term Enhancements (Clinical Interoperability & Compliance)
1. **HL7 FHIR v4.0.1 Conformance**:
   - Expose bidirectional FHIR REST endpoints:
     - `GET /fhir/r4/MedicationRequest?patient={id}`
     - `POST /fhir/r4/Bundle` (containing `Composition`, `Practitioner`, `Patient`, and `MedicationRequest`).
   - Implement SMART on FHIR OAuth 2.0 authorization profiles for seamless embedding within electronic health records (EHRs).
2. **Voice AI with Neural Indian Dialect Models**:
   - Integrate with the Government of India's **Bhashini** AI platform or Google Cloud Neural2 Text-to-Speech API to synthesize naturalistic audio explanations in 22 official Indian languages, including rural dialects.
3. **Automated Audit Trail Cryptographic Notarization**:
   - Augment the existing audit log system (`AuditLog` table) with immutable cryptographic hash chains (Merkle tree checkpoints) to provide mathematical non-repudiation during medico-legal audits.

