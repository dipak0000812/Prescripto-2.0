# Prescripto AI 2.0 — Project Identity & Background Dossier

**Document ID:** `DOC-01-ID`  
**Classification:** Academic Engineering Dossier  
**Canonical Spec Reference:** [docs/PRD_V1.md](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/docs/PRD_V1.md), [docs/PROJECT-SPEC.md](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/docs/PROJECT-SPEC.md)  
**Date of Extraction:** November 4, 2026  

> [!IMPORTANT]
> **CRITICAL PROJECT STATUS NOTE (OBSOLETE PPT NOTICE)**:  
> Earlier presentations and preliminary roadmap documents (e.g. `docs/ROADMAP_TO_100.md`) described an early development stage where backend integration, database models, OCR configuration, worker queues, and safety screening were listed as pending work. **That status is obsolete.** Subsequent development cycles fully implemented, integrated, tested, and deployed all of those subsystems. Refer to [`19_DEVELOPMENT_COMPLETION_AND_STATUS_CORRECTION.md`](file:///c:/Users/pbhus/Desktop/Priscption-project/Prescripto-2.0/project-documentation/19_DEVELOPMENT_COMPLETION_AND_STATUS_CORRECTION.md) for the detailed audit proving 100% completion across backend, database, ML perception, workers, safety rules, and cloud deployment.  

---

## 1. Project Nomenclature and Definition

* **Official Project Name:** Prescripto AI 2.0
* **Formal Project Title:** Prescription Document Intelligence & Medication-Safety Decision Support System
* **Short Description:** A clinical decision-support and document intelligence platform that ingests handwritten medical prescription images, extracts structured medication regimens using multi-tier vision and OCR pipelines, normalizes drug identities against verified national formularies, performs deterministic safety boundary evaluations, and enforces human-in-the-loop review before clinical action.
* **Academic Discipline / Application Domain:** Health Informatics, Medical Document Analysis, Optical Character Recognition (OCR), Computer Vision, Clinical Decision Support Systems (CDSS), Software Engineering for High-Stakes Environments.

---

## 2. Motivation and Problem Context

### The Real-World Clinical Problem
Handwritten medical prescriptions remain the dominant medium of prescription order communication in outpatient healthcare across developing and developed nations, especially across India's decentralized outpatient dispensaries. 

Cursive medical handwriting, ambiguous abbreviations (e.g., Latin sig codes such as *OD*, *BD*, *TDS*, *QID*, *HS*, *SOS*), look-alike sound-alike (LASA) drug nomenclature, and rushed physician documentation cause severe medication errors:
1. **Misinterpreted Dosages & Strengths**: Misreading `50mg` as `500mg` or confusion between micrograms (`mcg`) and milligrams (`mg`).
2. **Duplicate Therapy Overlap**: Prescribing multiple branded drugs that contain identical active pharmaceutical ingredients (e.g., prescribing *Dolo 650* alongside *Combiflam*, both containing Paracetamol, leading to acetaminophen-induced hepatotoxicity).
3. **Allergy Contraindications**: Administering penicillin-class antibiotics (e.g., *Augmentin*, *Amoxicillin*) to patients with documented penicillin allergies.
4. **The "False Confidence" Machine Learning Hazard**: Modern off-the-shelf generative AI and OCR systems tend to hallucinate plausible-sounding drug names when encountering illegible text. In healthcare, an AI that quietly guesses a drug is exponentially more dangerous than an AI that declares text unreadable.

### Why Prescripto AI 2.0 Was Developed
Prescripto AI 2.0 was designed to replace blind optical transcription with **uncertainty-aware clinical decision support**. It enforces a strict separation between machine perception (statistical pattern recognition) and clinical validation (deterministic drug databases and mandatory human sign-off).

---

## 3. Target Stakeholders and User Personas

| Stakeholder Role | System Role | Primary Needs & Responsibilities | Interaction Surfaces |
| :--- | :--- | :--- | :--- |
| **Qualified Reviewer (Doctor / Pharmacist)** | `Role.REVIEWER` | Inspect flagged safety warnings, verify ambiguous handwriting against original scans, edit extractions, and sign off. | Clinical Review Queue (`/review-queue`), Dual-Pane Analysis Workspace (`/analyses/{id}`) |
| **Clinic Operator / Staff** | `Role.OPERATOR` | Digitize paper prescriptions, upload mobile camera captures, tag patient IDs, verify upload integrity. | Ingestion Portal (`/upload`), Prescriptions List (`/prescriptions`) |
| **System Administrator** | `Role.ADMIN` | Oversee system health diagnostics, audit logs, DPDPA 2023 verifiable deletion requests, user management. | System Health Dashboard (`/health`), Patient Directory (`/patients`), Deletion Worker |
| **Patient** | `Role.PATIENT` | Understand medication dosage schedules, food instructions (before/after meal), listen to spoken instructions in regional languages. | Patient Portal (`/patient-portal`), Mobile OTP Login (`/login`) |

---

## 4. Primary Use Cases

### UC-1: Prescription Upload and Integrity Verification
* **Actor:** Clinic Operator or Patient.
* **Precondition:** Authenticated user with valid session token.
* **Flow:** User selects a JPEG, PNG, or TIFF image. The client validates file size ($\le 20\text{ MB}$) and MIME type, calculates SHA-256 hash, generates an idempotent UUIDv4 token, and submits to `POST /api/v1/prescriptions`.
* **Outcome:** File is stored in S3/MinIO, a database record is created in PostgreSQL, an asynchronous analysis job is enqueued, and HTTP 202 is returned with the analysis tracking URL.

### UC-2: 8-Stage Asynchronous Pipeline Execution
* **Actor:** Fenced Worker Engine (`WorkerRunner`).
* **Flow:** Worker claims the next queued job using `SELECT ... FOR UPDATE SKIP LOCKED`, acquires a 10-minute lease with monotonic fencing token, and executes 8 sequential stages:
  1. Ingestion verification (SHA-256 match)
  2. Quality gate (Laplacian blur variance and brightness check)
  3. Text detection
  4. OCR recognition
  5. 8-field clinical entity extraction
  6. Medication normalization against CDSCO formulary
  7. Deterministic safety screening (duplicates, allergies, dosage ceilings)
  8. Report assembly and review trigger evaluation.
* **Outcome:** Status transitions to `REQUIRES_REVIEW` if any ambiguity or safety trigger is found, or `COMPLETED`.

### UC-3: Clinician Dual-Pane Verification and Review Sign-Off
* **Actor:** Qualified Medical Reviewer (`doctor.sharma@prescripto.local`).
* **Flow:** Clinician opens `/analyses/{id}`. The left pane renders the original high-resolution prescription scan with zoom/pan capabilities via a 60-second HMAC signed storage URL. The right pane renders editable medication cards showing field confidence states (`CLEAR`, `AMBIGUOUS`, `UNREADABLE`, `NOT_PRESENT`) and safety alert cards (`DUPLICATE_MEDICATION`, `ADVERSE_EFFECT`). The clinician can adjust drug names, correct strengths, and record an audit-logged action: `APPROVE`, `FLAG`, or `ESCALATE`.
* **Outcome:** System transitions the record to `REVIEWED_COMPLETE`. All decisions are persisted with reviewer timestamp and reason codes.

### UC-4: Multilingual Patient Medication Schedule & Spoken Guidance
* **Actor:** Patient via mobile phone.
* **Flow:** Patient logs in with phone number and OTP. The patient portal presents structured "Medicine Hero Cards" color-coded by daily schedule (Morning, Afternoon, Night, SOS) with dietary chips (Before Food / After Food). The patient can select their language (**English, Hindi, Gujarati, Marathi**) and click the speaker icon to hear the regimen read aloud via the Web Speech API.
* **Outcome:** High comprehension and adherence for non-English literate and elderly patients.

---

## 5. Objectives vs. Implemented Reality

To maintain strict academic integrity, this matrix separates original design intentions from verifiable implementations in the current repository:

```
┌──────────────────────────────────────────────────────────┬─────────────────────────────┬────────────────────────────────────────────────────────────┐
│ Objective Description                                    │ Documented Target           │ Actual Implemented State in Codebase                       │
├──────────────────────────────────────────────────────────┼─────────────────────────────┼────────────────────────────────────────────────────────────┤
│ 8-Field Prescription Parsing                             │ Extract 8 clinical fields   │ ✅ VERIFIED: name, strength, dose, unit, route,            │
│                                                          │ with confidence states      │    frequency, duration, instructions extracted in Stage 5. │
├──────────────────────────────────────────────────────────┼─────────────────────────────┼────────────────────────────────────────────────────────────┤
│ Formulary Normalization Database                         │ 15,000+ CDSCO Master drugs  │ ⚠️ PARTIAL: 107 commonly prescribed Indian drugs seeded in  │
│                                                          │                             │    PostgreSQL; full 15,000 scraping blocked by CDSCO license│
├──────────────────────────────────────────────────────────┼─────────────────────────────┼────────────────────────────────────────────────────────────┤
│ Duplicate Medication Detection                           │ Deterministic rule engine   │ ✅ VERIFIED: Flags duplicate canonical products and         │
│                                                          │                             │    overlapping active ingredients (e.g. Paracetamol).      │
├──────────────────────────────────────────────────────────┼─────────────────────────────┼────────────────────────────────────────────────────────────┤
│ Dosage Upper-Bound Check                                 │ Flag single-dose overdoses  │ ✅ VERIFIED: Checks mg thresholds across 17 drug classes    │
│                                                          │                             │    (e.g., Paracetamol > 1000mg, Azithromycin > 500mg).     │
├──────────────────────────────────────────────────────────┼─────────────────────────────┼────────────────────────────────────────────────────────────┤
│ Patient Allergy Contraindication                         │ Cross-reference allergies   │ ✅ VERIFIED: Regex-based cross-referencing across 11        │
│                                                          │                             │    allergen families (Penicillin, Sulfa, NSAIDs, etc.).   │
├──────────────────────────────────────────────────────────┼─────────────────────────────┼────────────────────────────────────────────────────────────┤
│ Drug-Drug Interaction (DDI) Network                      │ Complete pairwise DDI grid  │ 🔲 PLANNED / OUT OF SCOPE: Excluded from V1 due to legal    │
│                                                          │                             │    licensing restrictions on commercial Indian DDI data.   │
├──────────────────────────────────────────────────────────┼─────────────────────────────┼────────────────────────────────────────────────────────────┤
│ Multilingual Spoken Guidance                             │ Support Indian vernaculars  │ ✅ VERIFIED: Full UI translations and Web Speech synthesis  │
│                                                          │                             │    in English, Hindi, Gujarati, and Marathi.               │
├──────────────────────────────────────────────────────────┼─────────────────────────────┼────────────────────────────────────────────────────────────┤
│ Zero-PHI Structured Audit Logging                        │ No PHI in system logs       │ ✅ VERIFIED: Strict structlog whitelist filter drops        │
│                                                          │                             │    unapproved keys before writing to console/streams.      │
├──────────────────────────────────────────────────────────┼─────────────────────────────┼────────────────────────────────────────────────────────────┤
│ DPDPA 2023 Cryptographic Shredding                       │ 4-phase verifiable deletion │ ✅ VERIFIED: Deletion worker purges DB records & S3 objects,│
│                                                          │                             │    writing signed HMAC manifests to retention vault.       │
└──────────────────────────────────────────────────────────┴─────────────────────────────┴────────────────────────────────────────────────────────────┘
```

