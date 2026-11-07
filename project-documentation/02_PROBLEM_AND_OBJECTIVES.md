# Prescripto AI 2.0 — Problem Analysis & Formal Requirements Dossier

**Document ID:** `DOC-02-REQ`  
**Classification:** Academic Engineering Dossier  
**Canonical Spec Reference:** [docs/REQUIREMENTS.md](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/docs/REQUIREMENTS.md), [docs/PROJECT-SPEC.md](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/docs/PROJECT-SPEC.md)  
**Date of Extraction:** November 4, 2026  

---

## 1. Comprehensive Problem Analysis

### 1.1. The Healthcare Challenge: Medical Prescription Errors
Preventable Adverse Drug Events (pADEs) represent a leading cause of accidental patient harm and avoidable hospitalization worldwide. According to landmark epidemiological studies by the **Institute of Medicine (IOM)** (*To Err Is Human: Building a Safer Health System*) and the **World Health Organization (WHO)** (*Medication Without Harm*), medication errors account for billions of dollars in healthcare expenses and tens of thousands of deaths annually.

In outpatient care across India and South Asia, medical orders remain heavily reliant on handwritten documents. Common error pathways include:
1. **Unchecked Slang and Sig Codes**: Physician shorthand such as `TDS` (ter die sumendum - 3 times daily) or `OD` (once daily) misread as `QID` (4 times daily) causing a 300% dosing error.
2. **Look-Alike Sound-Alike (LASA) Medications**: Phonetically or visually similar drug names being mixed up (e.g., *Celexa* vs. *Celebrex*, or *Metformin* for diabetes vs. *Metronidazole* for amoebiasis).
3. **Compounded Active Ingredient Duplication**: A patient consulting an orthopedic surgeon for back pain receives *Combiflam* (Ibuprofen 400mg + Paracetamol 325mg) and simultaneously receives *Dolo 650* (Paracetamol 650mg) from an internal medicine practitioner. Without active ingredient tracking, the patient consumes toxic cumulative acetaminophen doses.

### 1.2. The Failure Modes of Existing Digitization Solutions
Conventional optical character recognition (OCR) and commercial document processing tools fail in clinical environments due to three structural weaknesses:
* **The "Rounding Up" False Confidence Failure**: If a generic OCR engine cannot distinguish between `5mg` and `50mg`, it arbitrarily outputs one string without signaling doubt to the clinician.
* **Lack of Pharmacological Normalization**: Standard OCR extracts raw textual strings (e.g., `"Augmentn 625"`) without resolving them to active chemical molecules, salt strengths, or national regulatory formularies.
* **Absence of Strict Regulatory Privacy**: Cloud-based transcription frequently violates healthcare privacy mandates (such as HIPAA and India's **DPDPA 2023**) by transmitting unredacted patient images to third-party endpoints or storing patient health identifiers (PHI) in unencrypted plain-text operational log files.

---

## 2. Formal Functional Requirements (FR)

The system enforces six core functional requirement groups:

### 2.1. Document Ingestion & Storage (FR-DOC)
* **FR-DOC-01**: The system **SHALL** accept prescription image uploads in JPEG, PNG, and single-page TIFF formats.
* **FR-DOC-02**: The system **SHALL** validate that uploaded payloads do not exceed 20 MB (`MAX_UPLOAD_BYTES = 20971520`).
* **FR-DOC-03**: The system **SHALL** verify binary magic bytes upon upload to prevent polyglot file attacks.
* **FR-DOC-04**: The system **SHALL** compute and record the SHA-256 cryptographic hash of every uploaded file.
* **FR-DOC-05**: The system **SHALL** store images in an S3-compatible object store using deterministic keys structured as `prescriptions/{document_id}/original.{ext}`.
* **FR-DOC-06**: The system **SHALL** support client idempotency via an `Idempotency-Key` HTTP header. Replaying the same key with identical payload **MUST** return the existing analysis without creating duplicate pipeline jobs.

### 2.2. Image Preprocessing & Quality Verification (FR-QUAL)
* **FR-QUAL-01**: The system **SHALL** decode image dimensions and reject images smaller than $400 \times 400$ pixels.
* **FR-QUAL-02**: The system **SHALL** evaluate document sharpness using the Laplacian variance operator:
  $$\text{Var}(\nabla^2 I) < 100.0$$
  Images failing this threshold are flagged with `sharp_ok = False`.
* **FR-QUAL-03**: The system **SHALL** evaluate grayscale luminance distribution, flagging underexposed images ($< 20.0$ mean intensity) and overexposed images.

### 2.3. Clinical Entity & 8-Field Extraction (FR-EXT)
* **FR-EXT-01**: For every medication line, the system **SHALL** extract up to 8 discrete clinical fields:
  1. `name` (Brand or generic name)
  2. `strength` (e.g. 500mg, 10ml)
  3. `dose` (e.g. 1 tablet, 2 puffs)
  4. `unit` (e.g. Tablet, Capsule, Syrup)
  5. `route` (e.g. Oral, Topical, Inhalation)
  6. `frequency` (e.g. Once daily, TDS, SOS)
  7. `duration` (e.g. 5 days, 1 month)
  8. `instructions` (e.g. After food, At bedtime)
* **FR-EXT-02**: Every extracted field **SHALL** be assigned one of four discrete uncertainty states:
  * `CLEAR`: High calibrated confidence; model perception is unambiguous.
  * `AMBIGUOUS`: Moderate confidence or competing hypotheses detected; reviewer attention required.
  * `UNREADABLE`: Illegible stroke geometry; field value is masked and excluded from automated safety rules.
  * `NOT_PRESENT`: Field is absent from the document (explicitly distinguished from blank or null).

### 2.4. Medication Normalization (FR-NORM)
* **FR-NORM-01**: Extracted raw drug strings **SHALL** be matched against the CDSCO Medication Master repository using exact string matching and trigram fuzzy similarity.
* **FR-NORM-02**: If exactly one verified canonical product matches with 100% exact equality, the record **SHALL** be marked `ResolutionStatus.RESOLVED`.
* **FR-NORM-03**: If multiple plausible matches exist, the record **SHALL** be marked `ResolutionStatus.AMBIGUOUS`.
* **FR-NORM-04**: Under no circumstances **SHALL** the system automatically replace ambiguous text with a guessed medication without explicit human clinician sign-off.

### 2.5. Deterministic Clinical Safety Screening (FR-SAFE)
* **FR-SAFE-01 (Duplicate Product & Active Ingredient Check)**: The system **SHALL** flag instances where either the same canonical product ID or overlapping active ingredients appear across multiple lines on the same prescription.
* **FR-SAFE-02 (Dosage Upper-Bound Check)**: The system **SHALL** parse numeric milligram values and flag single-dose threshold exceedances across 17 therapeutic drug classes (e.g., Paracetamol $> 1000\text{ mg}$, Azithromycin $> 500\text{ mg}$, Ibuprofen $> 800\text{ mg}$).
* **FR-SAFE-03 (Patient Allergy Cross-Reference)**: If patient allergy records are tagged to the prescription, the system **SHALL** cross-reference prescribed molecules against 11 allergen drug families (Penicillins, Sulfonamides, NSAIDs, Cephalosporins, Macrolides, Fluoroquinolones, Statins, etc.).

### 2.6. Human-in-the-Loop Review & Verifiable Deletion (FR-REV & FR-DEL)
* **FR-REV-01**: An analysis **SHALL** transition to `REQUIRES_REVIEW` if any medication is `AMBIGUOUS` or `UNRESOLVED`, if any safety finding is emitted, or if image quality failed.
* **FR-REV-02**: Clinician sign-off decisions (`APPROVE`, `FLAG`, `ESCALATE`) **MUST** be recorded immutably with reviewer ID, timestamp, and optional clinical notes.
* **FR-DEL-01**: The system **SHALL** support verifiable deletion under DPDPA 2023, executing a 4-phase purge across relational records and S3 objects, producing an HMAC-SHA256 signed audit manifest.

---

## 3. Non-Functional Requirements (NFR)

* **NFR-PERF-01 (API Response Latency)**: Prescription submission (`POST /api/v1/prescriptions`) must return in $< 200\text{ ms}$ under standard load.
* **NFR-PERF-02 (Queue Concurrency)**: The job queue must support multiple parallel workers without race conditions, deadlocks, or duplicate job executions.
* **NFR-SEC-01 (Zero-PHI Logging)**: Operational logs must pass through a strict whitelist filter dropping patient names, phone numbers, and raw drug names before writing to disk or cloud logging aggregators.
* **NFR-SEC-02 (Asymmetric Token Security)**: All authentication tokens must be signed using 2048-bit RS256 asymmetric cryptography with a 15-minute access TTL and 7-day refresh TTL.
* **NFR-REL-01 (Perception Failover)**: The ML inference worker must seamlessly fall back from Gemini Vision to local RapidOCR upon quota depletion, network timeout, or authentication failure without aborting the job.

