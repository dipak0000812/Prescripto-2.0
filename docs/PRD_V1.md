# Prescripto AI 2.0 — Product Requirements Document v1

**Owner:** Dipak Dhangar  
**Status:** PRD v1 — For engineering implementation  
**Last updated:** 2026-09-10  
**Derived from:** Engineering Specification (Pre-PRD Foundation, verified)

---

## Table of Contents

1. [Product Definition](#1-product-definition)
2. [Problem Statement](#2-problem-statement)
3. [Goals](#3-goals)
4. [Non-Goals](#4-non-goals)
5. [Users and Personas](#5-users-and-personas)
6. [User Journeys](#6-user-journeys)
7. [Core Workflows](#7-core-workflows)
8. [Functional Requirements](#8-functional-requirements)
9. [Non-Functional Requirements](#9-non-functional-requirements)
10. [Safety Requirements](#10-safety-requirements)
11. [Privacy and Security Requirements](#11-privacy-and-security-requirements)
12. [AI/ML Product Requirements](#12-aiml-product-requirements)
13. [Human Review Workflow](#13-human-review-workflow)
14. [Analysis Lifecycle](#14-analysis-lifecycle)
15. [Prescription Lifecycle](#15-prescription-lifecycle)
16. [Error and Failure Behavior](#16-error-and-failure-behavior)
17. [Confidence and Uncertainty Behavior](#17-confidence-and-uncertainty-behavior)
18. [Evidence and Provenance Requirements](#18-evidence-and-provenance-requirements)
19. [Audit Requirements](#19-audit-requirements)
20. [Data Retention and Deletion](#20-data-retention-and-deletion)
21. [API and Product Boundaries](#21-api-and-product-boundaries)
22. [MVP Scope](#22-mvp-scope)
23. [Explicitly Deferred Scope](#23-explicitly-deferred-scope)
24. [Acceptance Criteria](#24-acceptance-criteria)
25. [Measurable Success Criteria](#25-measurable-success-criteria)
26. [Engineering Constraints](#26-engineering-constraints)
27. [Open Decisions](#27-open-decisions)
28. [PRD Lock Status](#28-prd-lock-status)

---

## 1. Product Definition

Prescripto AI 2.0 is a **prescription document intelligence and medication-safety decision-support system**.

Given a photograph or scan of a paper prescription, Prescripto:
1. Extracts the medication list and associated structured fields (drug name, strength, dose, unit, frequency, route, duration, instructions).
2. Resolves extracted medication candidates against a canonical medication knowledge base.
3. Screens the resolved medication set against available safety-knowledge sources.
4. Presents a structured report — flagged findings, confidence levels, evidence, and a plain-language explanation — to a qualified human reviewer.

Prescripto does not diagnose. It does not prescribe. It does not claim comprehensive interaction coverage. It does not act autonomously. **Every analysis produces decision-support output, but no finding is actionable until reviewed by a qualified human.**

> [!IMPORTANT]
> The core design invariant: **upstream uncertainty must never silently become downstream clinical certainty.**  
> If OCR is uncertain → extraction is uncertain. If extraction is uncertain → normalization is uncertain. If normalization is uncertain → safety analysis inherits that uncertainty. Nothing rounds up to confident. Ever.

---

## 2. Problem Statement

Paper prescriptions — handwritten and printed — contain medication-critical information that is error-prone to read and transcribe manually at scale. Illegible handwriting, non-standardized abbreviations, brand-name/generic ambiguity, and inconsistent dosage notation all create opportunities for misinterpretation.

Current decision-support tools in this space are either:
- Too narrowly scoped (US-market, English-only, print-only)
- Too opaque (no provenance, no uncertainty — just a result)
- Too permissive (hallucinated identities, uncited findings)

For an Indian academic research context:
- Labeled Indian prescription data is limited but not absent.
- Indian medication brand/generic vocabularies exist but lack clinical authority.
- Comprehensive DDI databases are not reproducible from freely available sources.

Prescripto's response to this is not to claim coverage it doesn't have. It claims **coverage-aware** analysis, states its evidence sources, and routes uncertain findings to human review.

---

## 3. Goals

**G1 — Safe extraction:** Extract medication-critical fields from prescription images with measurable confidence, and make that confidence visible at every output surface.

**G2 — Honest normalization:** Resolve extracted medication candidates against a canonical entity table. When resolution fails or is uncertain, route to review — never force a best-guess.

**G3 — Evidence-backed safety screening:** Screen the resolved medication set against available knowledge sources. Report what was found, what source confirmed it, and what was not evaluated.

**G4 — Coverage-honest reporting:** Never conflate "not found in our sources" with "does not exist." Every report must make the system's knowledge limits explicit.

**G5 — Human-in-the-loop by design:** The product is decision support, not decision-making. Every finding goes to a qualified reviewer. The system routes; humans decide.

**G6 — Reproducibility:** Every analysis is reproducible — model versions, knowledge snapshots, rules, and timestamp are recorded with every result.

**G7 — Data minimization:** The system retains only what is necessary, for only as long as configured, with full deletion across all storage layers.

---

## 4. Non-Goals

**NG1 — Autonomous diagnosis.** Prescripto does not determine what condition a patient has or should be treated for.

**NG2 — Autonomous prescribing.** Prescripto does not generate prescriptions.

**NG3 — Treatment recommendation.** Prescripto does not suggest alternatives to what is written on the prescription.

**NG4 — Comprehensive DDI coverage.** Prescripto explicitly does not claim to know about all drug-drug interactions. V1 covers interactions available from its licensed sources only.

**NG5 — Clinical validation.** Prescripto is an academic research prototype. It is not a cleared medical device and must not be represented as one.

**NG6 — EHR integration.** No integration with electronic health records in V1.

**NG7 — Real-time processing.** Analysis is asynchronous. Real-time interactive analysis is not a V1 requirement.

**NG8 — Mobile native app.** Web client only in V1.

**NG9 — Multi-language UI.** English UI only in V1. Hindi-English prescription content is in scope for OCR; UI language is not.

---

## 5. Users and Personas

### 5.1 Primary User — Pharmacist / Clinical Reviewer

**Who:** A pharmacist or equivalently qualified clinical professional responsible for reviewing flagged prescriptions.

**Goal:** Quickly understand what the system extracted, what was flagged, what evidence supports each flag, and what confidence level was assigned — so they can make an informed review decision.

**Key needs:**
- See the original prescription image alongside extracted fields.
- Understand which fields have low confidence and why.
- See exactly which source confirmed each safety finding.
- Approve, reject, or escalate each finding independently.
- Know that the report will not lie about what it doesn't know.

**What they must never see:** A finding marked confident that the system was actually uncertain about. A "no interaction found" result presented as "safe."

### 5.2 Secondary User — Research Operator / Admin

**Who:** The researcher or operator managing the system.

**Goal:** Upload prescription documents (or bulk-load a dataset), track analysis status, manage reviewers, configure the system, and access audit records.

**Key needs:**
- Document upload and management.
- Analysis status dashboard.
- Reviewer assignment.
- Audit log access.
- Environment configuration (retention, model selection).

### 5.3 Out of Scope for V1

- Patients (no patient-facing interface).
- Prescribing physicians (no physician-facing interface).
- Payers, insurers.

---

## 6. User Journeys

### 6.1 Prescription Upload and Analysis (Operator)

1. Operator logs in.
2. Operator uploads a prescription document (image or PDF).
3. System accepts the document, records metadata, returns an `analysis_id` and `202 Accepted`.
4. Operator sees the analysis in a "Pending" state on the dashboard.
5. Analysis completes (or fails). Status updates to `COMPLETED`, `FAILED`, or `REQUIRES_REVIEW`.
6. Operator assigns the result to a reviewer if the status requires human review.

### 6.2 Structured Review (Clinical Reviewer)

1. Reviewer is notified of or navigates to a result awaiting review.
2. Reviewer sees:
   - Original prescription image.
   - Extracted fields per medication line (name, strength, dose, unit, frequency, route, duration).
   - Confidence indicator per field (`CLEAR` / `AMBIGUOUS` / `UNREADABLE` / `NOT_PRESENT`).
   - Safety findings, each with: finding status, evidence, source, confidence.
   - Plain-language explanation (if generated and valid).
   - Explicit statement of what was NOT evaluated.
3. Reviewer approves, flags, or escalates each finding.
4. Reviewer submits review decision.
5. System records the decision with reviewer identity and timestamp.

### 6.3 Analysis Failure (Either User)

1. Analysis fails at any pipeline stage.
2. System records the failure stage, error code, and model version.
3. Status becomes `FAILED`.
4. Operator sees the failure on the dashboard.
5. Operator can resubmit if appropriate.
6. No partial or uncertain result is presented as a completed analysis.

---

## 7. Core Workflows

### 7.1 Document Ingestion

```
Upload request
  → document format validation (accepted: JPEG, PNG, TIFF, PDF single-page)
  → file stored in object storage
  → PrescriptionDocument record created (status: UPLOADED)
  → Analysis job enqueued (status: QUEUED)
  → 202 Accepted + analysis_id returned
```

### 7.2 Analysis Pipeline

```
Job dequeued
  → PrescriptionDocument retrieved from object storage
  → Quality check (resolution, orientation, legibility score)
    → if unprocessable: FAILED(QUALITY_UNPROCESSABLE)
  → Orientation correction (if needed)
  → Text region detection
  → Per-region OCR / HTR
    → confidence score per region
  → Candidate text assembled
  → Prescription parser
    → structured fields extracted per medication line
    → field-level confidence assigned
    → field-level state: CLEAR | AMBIGUOUS | UNREADABLE | NOT_PRESENT
  → Confidence gate
    → below threshold: route to VLM verification (low-confidence regions only)
    → at or above threshold: proceed
  → Medication normalization
    → candidate generation from extracted names
    → lookup against canonical medication table
    → if unrecognized: state = UNRESOLVED, route to human review
    → if resolved: canonical Medication entity linked
  → Safety screening
    → screen resolved medications against available knowledge sources
    → each finding: status, evidence, source, source version, timestamp
    → record which medications were NOT evaluated and why
  → LLM explanation generation (optional, schema-constrained)
    → if generation fails validation: discard, use structured result only
  → Report assembled
  → Analysis status: COMPLETED | REQUIRES_REVIEW
```

### 7.3 Human Review

```
Analysis in REQUIRES_REVIEW or COMPLETED
  → Reviewer assigned (manually in V1)
  → Reviewer opens review interface
  → Reviewer sees: image, extracted fields, findings, explanation
  → Reviewer acts per finding: APPROVED | FLAGGED | ESCALATED
  → Review submitted
  → Review record created (reviewer, timestamp, decision per finding)
  → Analysis status: REVIEWED
```

---

## 8. Functional Requirements

### 8.1 Document Management

**FR-DOC-01:** The system must accept prescription document uploads in JPEG, PNG, TIFF, and single-page PDF formats.  
**FR-DOC-02:** Original documents must be stored in object storage and must not be modified after ingestion.  
**FR-DOC-03:** The system must record document metadata: upload timestamp, uploader identity, file hash, format, and storage reference.  
**FR-DOC-04:** The system must associate each document with a patient record where provided, or flag it as unlinked.  
**FR-DOC-05:** The system must allow documents to be deleted, with deletion propagated to object storage, derived artifacts, and database records.

### 8.2 Analysis

**FR-ANA-01:** Analysis must be asynchronous. Upload must return a response before analysis begins.  
**FR-ANA-02:** The system must expose an analysis status endpoint callable by the client to track progress.  
**FR-ANA-03:** Every analysis must record: model versions used, knowledge snapshot identifiers, analysis timestamp, pipeline stages executed, stage-level status.  
**FR-ANA-04:** Every analysis must be uniquely identified by an `analysis_id`.  
**FR-ANA-05:** The system must support resubmission of a failed analysis (new analysis job, preserving original document).

### 8.3 OCR and Field Extraction

**FR-OCR-01:** The system must perform text region detection before character recognition.  
**FR-OCR-02:** Handwriting recognition must operate on cropped line regions, not full document images.  
**FR-OCR-03:** The system must produce a confidence score for each recognized text region.  
**FR-OCR-04:** The system must route low-confidence regions to secondary verification before proceeding.  
**FR-OCR-05:** The extraction output must assign each field one of four states: `CLEAR`, `AMBIGUOUS`, `UNREADABLE`, `NOT_PRESENT`. No field may be coerced from `UNREADABLE` to a guessed value without explicit review routing.  
**FR-OCR-06:** Per-medication-line structured fields must include: medication name, strength, dose, unit, frequency, route, duration, instructions. Each field carries its own state and confidence.

### 8.4 Medication Normalization

**FR-NORM-01:** Extracted medication names must be matched against the canonical medication table using a documented matching strategy.  
**FR-NORM-02:** A medication that cannot be confidently resolved must be marked `UNRESOLVED` and must trigger human review routing — not a forced best-guess normalization.  
**FR-NORM-03:** Resolved medications must link to a canonical `Medication` entity containing: internal_id, normalized_name, generic_name, active_ingredients, strength, dosage_form, route, rxnorm_cui (nullable), external_identifiers, provenance.  
**FR-NORM-04:** The system must record the matching strategy, candidate score, and the source vocabulary used for each normalization result.  
**FR-NORM-05:** RxNorm CUI must be nullable — Indian-only medications may have no RxNorm mapping.

### 8.5 Safety Screening

**FR-SAFE-01:** Safety screening must operate on resolved `Medication` entities, not raw OCR text.  
**FR-SAFE-02:** Each finding must carry a `FindingStatus`: `CONFIRMED_BY_SOURCE`, `POTENTIAL`, `INSUFFICIENT_EVIDENCE`, `NOT_EVALUATED`, or `REQUIRES_REVIEW`.  
**FR-SAFE-03:** Every finding must record: which source(s) confirmed or evaluated it, the source version, the timestamp of the check, the medication identities involved, the confidence level, and the rule or model version applied.  
**FR-SAFE-04:** The system must explicitly record which medication pairs or individual medications were NOT screened, and the reason (e.g., `UNRESOLVED_IDENTITY`, `SOURCE_NOT_COVERING`).  
**FR-SAFE-05:** `NOT_EVALUATED` and `NO_KNOWN_INTERACTION_IN_DATABASE` must be distinct states from `NO_INTERACTION_EXISTS`. They must never be presented to the user as equivalent.  
**FR-SAFE-06:** The safety engine must function completely and produce a structured result when the LLM explanation layer is disabled.  
**FR-SAFE-07:** Supported checks in V1: medication identity confirmation, duplicate medication detection, selected evidence-backed interaction checks (per available licensed sources). See §22 for explicit scope boundary.

### 8.6 Explanation and Report

**FR-REP-01:** The system must produce a structured report for every completed analysis regardless of whether LLM explanation succeeds.  
**FR-REP-02:** If LLM explanation generation is attempted and the output fails schema validation, the explanation is discarded and the structured report stands alone. The report does not degrade to an error state.  
**FR-REP-03:** Explanations must be generated only from verified structured findings + retrieved evidence. The LLM must not introduce new clinical claims.  
**FR-REP-04:** The report must clearly state the system's knowledge limits: which sources were queried, which medications were not evaluated, and what coverage gaps exist.  
**FR-REP-05:** The report must not use language that implies comprehensive safety clearance.

### 8.7 Human Review

**FR-REV-01:** Every analysis result must support human review before any finding is treated as actionable.  
**FR-REV-02:** Reviewers must be able to approve, flag, or escalate each finding independently.  
**FR-REV-03:** All review decisions must be recorded with reviewer identity, timestamp, and action taken.  
**FR-REV-04:** A reviewed analysis must preserve both the original system findings and the reviewer's decisions as separate records. Review decisions do not overwrite system output.  
**FR-REV-05:** In V1, reviewer assignment is manual.

---

## 9. Non-Functional Requirements

### 9.1 Performance

**NFR-PERF-01:** Document upload response time must be ≤ 3 seconds at P95 under expected concurrent load (exact threshold set after load baseline is measured).  
**NFR-PERF-02:** Analysis completion time for a single-page prescription must be measured and reported as a baseline before any SLA is committed. Async design means total wall-clock time is decoupled from the upload response.  
**NFR-PERF-03:** The system must remain responsive (upload, status polling) during concurrent analysis workloads.

### 9.2 Reliability

**NFR-REL-01:** A failed analysis must not corrupt the document record or any other analysis.  
**NFR-REL-02:** Pipeline failures must be idempotent with respect to retry — a resubmitted job must not double-record findings.  
**NFR-REL-03:** The system must survive worker restart without losing in-progress analysis state beyond the current pipeline stage.

### 9.3 Scalability

**NFR-SCALE-01:** V1 targets a single-instance deployment with a single worker process. Horizontal scaling is not a V1 requirement and must not drive architectural decisions.

### 9.4 Observability

**NFR-OBS-01:** The system must log per-stage: `request_id`, `analysis_id`, `pipeline_stage`, `model_version`, `status`, `duration_ms`, `error_code`. No patient data in operational logs.  
**NFR-OBS-02:** Errors must be surfaced with sufficient context to diagnose without exposing prescription content.  
**NFR-OBS-03:** Audit records (see §19) are a separate, distinct data structure from application logs.

### 9.5 Testability

**NFR-TEST-01:** The analysis pipeline must be testable stage-by-stage in isolation.  
**NFR-TEST-02:** The safety engine must be testable without the LLM. LLM calls must be mockable.  
**NFR-TEST-03:** All API contracts must be tested against the canonical OpenAPI schema.  
**NFR-TEST-04:** The normalization and safety-screening layers must have deterministic test paths (fixed model versions, fixed knowledge snapshots).

---

## 10. Safety Requirements

> [!CAUTION]
> These requirements may not be weakened, bypassed, or deferred without explicit product and safety review. They are invariants, not preferences.

**SR-01 — No silent certainty escalation:** A field or finding cannot be marked `CONFIRMED` or `CLEAR` if the upstream stage that produced it was in an uncertain state. Uncertainty propagates forward. It never gets rounded up.

**SR-02 — No autonomous clinical output:** The system must not produce any output that functions as a diagnosis, prescription, or treatment recommendation. This applies to the LLM explanation layer specifically.

**SR-03 — No hallucinated medication identity:** The system must not resolve a medication to a canonical entity it is not confidently matched to. Forced best-guess normalization is prohibited.

**SR-04 — No false safety clearance:** The system must not present the absence of a finding as evidence of safety. Explicitly:
- `NO_KNOWN_INTERACTION_IN_DATABASE` ≠ `NO_INTERACTION_EXISTS`.
- `NOT_EVALUATED` ≠ `SAFE`.
- These distinctions must appear in the data model, the API response, the UI, and any generated explanation text.

**SR-05 — Safety engine LLM independence:** The safety engine must produce a complete, valid structured result with the LLM disabled. Any architecture where disabling the LLM breaks safety output fails this requirement.

**SR-06 — Finding provenance is mandatory:** A safety finding with no source, no evidence reference, or no confidence level is invalid and must not be surfaced to a reviewer.

**SR-07 — Unrecognized medication triggers review:** An `UNRESOLVED` medication identity must route the analysis to human review. It must not be silently dropped from the screened medication set.

**SR-08 — No finding is actionable without human review:** Every analysis produces decision-support output. No finding is actionable until reviewed by a qualified human reviewer. The product surface must make this explicit. No "auto-approve" path exists in V1.

**SR-09 — Version lock on analysis:** Every analysis records the exact versions of models, rules, and knowledge snapshots used to produce it. Retroactively reprocessing with a different version creates a new analysis record, not an in-place update.

---

## 11. Privacy and Security Requirements

### 11.1 Data Classification

Prescription documents and their extracted contents are classified as `SENSITIVE_PERSONAL_DATA`. Within that class, health-related content (medication names, doses, clinical instructions) is treated at a stricter sub-level. This classification is internal and independent of any specific jurisdiction's legal framework.

> [!NOTE]
> This system is designed for an Indian academic research context. The applicable legal framework is India's Digital Personal Data Protection Act (DPDPA 2023), not HIPAA. HIPAA-specific language must not be used in technical or product documentation. Where international deployment is considered in future, the applicable framework is reassessed.

### 11.2 Access Control

**SEC-01:** Prescription documents and analysis results must only be accessible to authenticated, authorized users with an explicit access grant.  
**SEC-02:** Object storage access must be mediated through the application layer. Direct public URLs to prescription documents must not be issued.  
**SEC-03:** Reviewer and operator roles must have separate permission sets. An operator role does not grant clinical review permissions by default.  
**SEC-04:** Authentication must be session-based or token-based with expiry. Session fixation and CSRF must be mitigated.

### 11.3 Data at Rest and in Transit

**SEC-05:** Prescription documents in object storage must be encrypted at rest.  
**SEC-06:** All traffic between client, API, worker, and storage must be encrypted in transit (TLS).  
**SEC-07:** Database columns containing sensitive health content must be considered for application-level encryption where column-level access control is insufficient.

### 11.4 Logging Constraints

**SEC-08:** Application logs must never contain: prescription image data, raw OCR text, patient names, phone numbers, addresses, or medication lists. Log fields are restricted to: `request_id`, `analysis_id`, `pipeline_stage`, `model_version`, `status`, `duration_ms`, `error_code`.  
**SEC-09:** Audit records (§19) are not application logs. Audit records do contain actor identity, action, and resource identifier — but not clinical content.

### 11.5 Third-Party Services

**SEC-10:** Prescription content must not be transmitted to external third-party APIs (including LLM APIs) without explicit data-processing agreements in place and documented in the system's data flow record.  
**SEC-11:** In the research prototype, if a cloud LLM API is used, the data processing agreement and permissible data categories must be verified before any prescription text is sent.

---

## 12. AI/ML Product Requirements

### 12.1 What the system must measure (not just OCR accuracy)

The product distinguishes the following independent correctness axes. Each must be measured and reported separately:

| Axis | Description |
|---|---|
| Transcription correctness | CER, WER, exact match on raw OCR output |
| Medication name correctness | Extracted name matches ground-truth name |
| Medication identity correctness | Resolved canonical entity matches ground-truth drug |
| Strength correctness | Extracted strength value and unit match ground truth |
| Dose correctness | Extracted dose matches ground truth |
| Unit correctness | Extracted unit matches ground truth (mg, mcg, ml, etc.) |
| Frequency correctness | Extracted frequency matches ground truth (OD, BD, TDS, QID, etc.) |
| Duration correctness | Extracted duration matches ground truth |
| Route correctness | Extracted route matches ground truth |
| Normalization correctness | Normalization result matches ground-truth canonical entity |
| Safety finding correctness | Finding matches ground-truth (for cases with known reference findings) |
| Human review routing correctness | System routes to review when it should; does not over-route or under-route |
| Explanation groundedness | Explanation claims are traceable to verified structured findings |

**Critical medication errors** receive higher priority than generic CER/WER:
- **Critical medication identity error:** Prediction resolves to a clinically different drug.
- **Critical dose error:** Prediction materially changes the prescribed dose.
- **Critical unit error:** e.g., mg → mcg (clinically consequential unit swap).
- **Critical frequency error:** e.g., OD → QID (materially different administration).

Criticality is assessed per-medication against a clinical reference, not against a universal numeric multiplier.

### 12.2 Model selection is an implementation decision

The PRD does not mandate a specific OCR model, HTR model, normalization strategy, or LLM. These are implementation candidates benchmarked against the Tier B evaluation set. The PRD mandates the **requirements** the chosen models must satisfy:

- The primary HTR component must be benchmarked on our Tier B evaluation data, not only on its own model-card test set.
- Model selection is documented in the architecture decision record, not in this PRD.
- No model version is used in production without being recorded in the `ModelVersion` table.

### 12.3 Confidence thresholds

Confidence thresholds (for routing to VLM verification, for routing to human review) are not fixed in this PRD. They are:
- Defined as configurable parameters per environment.
- Set after baseline measurement on Tier B data.
- Approved by the designated product/safety reviewer.
- Locked in the architecture decision record before V1 release.

The PRD requires that thresholds exist, are configurable, are documented, and are not hardcoded to arbitrary defaults.

### 12.4 Data tiers and their permitted uses

| Tier | Source | Permitted use |
|---|---|---|
| Tier A | Public/research (MedOCR-Vision, RxHandBD, HF 69K Indian medicine names, others passing license check) | Pretraining, baseline comparison, vocabulary coverage. **Not** ground-truth benchmark. |
| Tier B | Our own legally obtained, de-identified, expert-reviewed prescriptions (target: 200–500 documents) | Ground-truth benchmark. The only dataset that determines model selection and threshold setting. |
| Tier C | Synthetic/augmented (layout variation, handwriting style, image degradation) | Robustness training only. **Never** presented as equivalent to real clinical data in any eval report. |

Tier B requirements:
- Documents must be legally obtained and de-identified before entering the system.
- Expert annotation: two annotators + adjudication. Medication-critical fields require pharmacist or equivalently qualified sign-off.
- Field states: `CLEAR`, `AMBIGUOUS`, `UNREADABLE`, `NOT_PRESENT`. `UNREADABLE` is a valid label. Forced guesses are not.
- Split discipline: same prescription never crosses train/val/test splits. Handwriting-style separation where achievable. Synthetic variants in same split as source.

### 12.5 Eval reporting requirements

Every benchmark report must include:
- Number of prescriptions evaluated.
- Number of medication mentions evaluated.
- Distribution of handwriting types (handwritten / printed / mixed).
- Distribution of prescription languages (English / Hindi-English / other).
- Number of distinct prescribers/handwriting styles.
- Drug vocabulary coverage (fraction of target vocabulary present).
- Difficulty distribution.
- 95% confidence intervals on all accuracy numbers.

A result of "96.4%" without a confidence interval and dataset description is not an acceptable eval result.

### 12.6 ML deployment discipline

V1 uses manual deployment:
```
experiment → evaluation on Tier B → manual review → model promotion
```

No automated model deployment until:
- Regression gates are defined based on measured baseline variance (not pre-guessed).
- The gates cover: critical medication error rate, medication accuracy, dosage accuracy.
- Gate values are approved through product/safety review.

### 12.7 Explanation layer constraints

The LLM explanation layer:
- Receives: verified structured finding + retrieved evidence + structured context.
- Must produce: schema-constrained output.
- Must not: introduce new clinical claims, medications, interactions, or warnings not present in the verified structured input.
- Failure: if the generated explanation fails validation, it is discarded. The report falls back to the structured finding. This is a graceful degradation, not an error state.

---

## 13. Human Review Workflow

### 13.1 Review routing

An analysis is routed to human review when any of the following conditions hold:
- Any extracted medication field is in state `AMBIGUOUS` or `UNREADABLE`.
- Any medication candidate is `UNRESOLVED` after normalization.
- Any safety finding carries status `POTENTIAL`, `INSUFFICIENT_EVIDENCE`, or `REQUIRES_REVIEW`.
- Overall analysis confidence falls below the configured review threshold.
- The system encounters an error in any pipeline stage (partial result + failure reason).

An analysis not meeting any of these conditions reaches `COMPLETED` state. Its findings are still not actionable until reviewed — but review is not system-mandated. An operator or reviewer may open any completed analysis for voluntary review; the finding actionability rule applies regardless.

### 13.2 Review interface requirements

The review interface must show, per analysis:
1. Original prescription image (full resolution, zoom-capable).
2. Per-medication-line extracted fields with field state and confidence.
3. Per-finding: status, evidence text, source name, source version, check timestamp, medication identities involved, confidence, rule/model version.
4. An explicit list of medications and medication pairs that were NOT evaluated, with reasons.
5. A clear statement that the system's knowledge coverage is limited and that absence of a finding does not confirm safety.
6. LLM explanation (if available and valid), visually distinguished from verified structured findings.

### 13.3 Review actions

Per finding:
- `APPROVED`: Reviewer confirms the finding as stated.
- `FLAGGED`: Reviewer disputes the finding or needs further investigation.
- `ESCALATED`: Reviewer escalates to a senior reviewer or external authority.

Per analysis:
- `REVIEWED_COMPLETE`: All findings actioned.
- `REVIEWED_ESCALATED`: One or more findings escalated; analysis under further review.

### 13.4 Review record requirements

Every review must record:
- Reviewer identity (user ID).
- Timestamp of each action.
- Action taken per finding.
- Any free-text notes the reviewer adds.
- The analysis version reviewed (model/knowledge snapshot).

Review records are immutable after submission. Corrections create a new review record referencing the original.

---

## 14. Analysis Lifecycle

```
QUEUED
  → PROCESSING
    → FAILED                (terminal — reason recorded per stage)
    → COMPLETED             (pipeline finished; no mandatory review conditions met)
    → REQUIRES_REVIEW       (pipeline finished; ≥1 mandatory review condition met)
      → REVIEWING           (reviewer assigned, actively reviewing)
        → REVIEWED_COMPLETE
        → REVIEWED_ESCALATED
```

**State semantics:**
- `COMPLETED` — the pipeline finished successfully and no mandatory routing condition was triggered. Findings are available for inspection but are **not actionable** without review. `COMPLETED` does not mean clinically approved or safe.
- `REQUIRES_REVIEW` — the pipeline finished and at least one mandatory routing condition was met (see §13.1). A reviewer must be assigned before findings may be acted upon.
- `REVIEWING` — a reviewer is actively working the analysis. Only `REQUIRES_REVIEW` analyses enter `REVIEWING` as a mandatory step. `COMPLETED` analyses that a reviewer opens voluntarily do not change state; they are read with review-actionability still applying.
- `REVIEWED_COMPLETE` — all mandatory findings have been actioned by a reviewer.
- `REVIEWED_ESCALATED` — one or more findings have been escalated; analysis under further review.

State transitions:
- `QUEUED → PROCESSING`: Worker dequeues the job.
- `PROCESSING → FAILED`: Any unrecoverable pipeline error.
- `PROCESSING → COMPLETED`: Pipeline finished, no mandatory routing conditions met.
- `PROCESSING → REQUIRES_REVIEW`: Pipeline finished, ≥1 mandatory routing condition met.
- `REQUIRES_REVIEW → REVIEWING`: Reviewer assigned (mandatory path).
- `REVIEWING → REVIEWED_COMPLETE / REVIEWED_ESCALATED`: Reviewer submits.

Each transition is recorded with timestamp and triggering actor (worker or user ID).

Invalid transitions must be rejected. An analysis in `FAILED` state cannot transition to `COMPLETED` — it must be resubmitted as a new analysis. `COMPLETED` does not transition to `REVIEWING` in the state machine; voluntary review of a `COMPLETED` analysis is a read operation recorded in the audit log, not a state change.

---

## 15. Prescription Lifecycle

```
UPLOADED
  → ANALYSIS_QUEUED
  → ANALYSIS_IN_PROGRESS
  → ANALYSIS_FAILED
  → ANALYSIS_COMPLETE
    → REVIEW_PENDING
    → REVIEW_IN_PROGRESS
    → REVIEW_COMPLETE
```

A prescription document may have multiple analyses (e.g., after resubmission following a failure, or after model update). Each analysis is a separate record. The prescription document record itself is immutable once ingested.

---

## 16. Error and Failure Behavior

### 16.1 Document-level failures

| Condition | Behavior |
|---|---|
| Document format not supported | Reject at upload. Return 400 with reason. No record created. |
| Document unprocessable (resolution too low, completely illegible) | Analysis moves to `FAILED(QUALITY_UNPROCESSABLE)`. Reason recorded. |
| Document upload storage failure | Return 500. No analysis record created. |

### 16.2 Pipeline-stage failures

Each pipeline stage records its own status. A failure at any stage terminates the analysis and records:
- Which stage failed.
- Error code.
- Model/component version at the time of failure.
- Whether retry is appropriate.

Partial results from earlier stages are preserved in the record but must not be surfaced as a complete analysis result.

### 16.3 Normalization failure

An extracted medication that cannot be resolved → marked `UNRESOLVED`. Does not fail the analysis. Does route to human review.

### 16.4 Safety screening failure

A safety screening component failure (source unavailable, timeout) → affected findings marked `NOT_EVALUATED(SOURCE_UNAVAILABLE)`. The analysis proceeds with a degraded but honest result. The reviewer sees which checks did not run.

### 16.5 LLM explanation failure

Explanation generation fails or produces invalid output → structured finding is used without explanation. Not an error state. Reviewer sees structured finding only.

### 16.6 Worker failure mid-analysis

Analysis job must be recoverable. If a worker dies mid-analysis:
- Job returns to queue after configurable timeout.
- Retry count recorded.
- After max retries, status becomes `FAILED(WORKER_TIMEOUT)`.

---

## 17. Confidence and Uncertainty Behavior

### 17.1 Confidence is per-field, not per-analysis

The system does not produce a single "overall confidence" score as a substitute for field-level confidence. Each extracted field carries its own confidence and state.

A prescription with 5 `CLEAR` fields and 1 `AMBIGUOUS` field is not "96.4% confident." It has 5 fields at one state and 1 field at another. These are reported separately.

### 17.2 Confidence propagation rules

| Upstream state | Downstream behavior |
|---|---|
| Field state `CLEAR` | Field may proceed normally. |
| Field state `AMBIGUOUS` | Downstream stages inherit uncertainty. Finding cannot be `CONFIRMED`. |
| Field state `UNREADABLE` | Field is excluded from structured extraction. Downstream is notified. |
| Field state `NOT_PRESENT` | Field is absent. Not treated as zero or default. |
| Medication state `UNRESOLVED` | Cannot be screened. Routed to review. |
| OCR confidence below threshold | Routed to secondary verification before proceeding. |

### 17.3 User-visible uncertainty

The UI must not flatten uncertainty into a pass/fail indicator. Reviewers must see field states and confidence levels, not a single summary grade.

---

## 18. Evidence and Provenance Requirements

### 18.1 Per-finding provenance record

Every safety finding must carry:

```
finding_id
analysis_id
finding_status          (CONFIRMED_BY_SOURCE | POTENTIAL | INSUFFICIENT_EVIDENCE | NOT_EVALUATED | REQUIRES_REVIEW)
medication_ids[]        (canonical internal IDs involved)
evidence_text           (verbatim or structured excerpt from source)
source_name             (e.g., "openFDA", "SIDER 4.1")
source_version          (specific version or snapshot identifier)
knowledge_snapshot_id   (foreign key to KnowledgeSnapshot record)
rule_id                 (if rule-based, the specific rule applied)
model_version_id        (if ML-based, the model version used)
confidence_score        (numeric, if applicable)
check_timestamp         (when the source was queried)
not_evaluated_reason    (nullable — reason if NOT_EVALUATED)
```

A finding missing any required provenance field is invalid and must not be surfaced.

### 18.2 Medication normalization provenance

Each normalization result must record:

```
candidate_id
analysis_id
extracted_text
matching_strategy       (e.g., "fuzzy_string", "ontology_lookup")
candidate_score
source_vocabulary       (e.g., "canonical_table", "rxnorm", "indian_brand_list")
resolved_medication_id  (nullable — null if UNRESOLVED)
resolution_status       (RESOLVED | UNRESOLVED | AMBIGUOUS)
```

### 18.3 Analysis version record

Every analysis must reference:

```
analysis_id
model_versions[]        (name, version, checkpoint hash where applicable)
knowledge_snapshot_ids[](per-source snapshots used)
pipeline_version        (pipeline code version)
analysis_timestamp
```

This record is immutable after analysis completion.

---

## 19. Audit Requirements

### 19.1 Events to audit

| Event | Fields recorded |
|---|---|
| Document uploaded | actor_id, document_id, timestamp, file_hash |
| Analysis started | actor_id (worker), analysis_id, document_id, timestamp |
| Analysis completed | analysis_id, status, timestamp |
| Analysis failed | analysis_id, stage, error_code, timestamp |
| Review action | actor_id, analysis_id, finding_id, action, timestamp |
| Review submitted | actor_id, analysis_id, timestamp, overall_status |
| Document deleted | actor_id, document_id, timestamp, deletion_scope |
| User login | actor_id, timestamp, outcome |
| User permission change | actor_id, target_user_id, permission_change, timestamp |

### 19.2 Audit record integrity

- Audit records are append-only. No update or delete of audit records.
- Audit records are stored separately from application records. A database failure that corrupts the main tables must not corrupt the audit log.
- Audit records must not contain prescription image data, raw OCR text, or clinical content (medication names, doses). They reference IDs, not content.

---

## 20. Data Retention and Deletion

### 20.1 Retention policy

Retention periods are configurable per environment:
- Demo/research: short retention (configurable, e.g., 30 days).
- Production: policy-defined per applicable jurisdiction.

A default retention period must be set at deployment time. "No policy" is not a valid default.

### 20.2 Deletion scope

Deleting a prescription document must delete:
- Original document from object storage.
- Processed/derived images (orientation-corrected, region crops).
- Generated report artifacts.
- Database records: `PrescriptionDocument`, `PrescriptionMedication`, `MedicationCandidate`, `Analysis`, `RiskFinding`, `Evidence`.
- Cached representations, if any.
- Backup inclusion: deletion requests must be recorded so backup restoration does not inadvertently restore deleted records.

> [!WARNING]
> Deleting the database row while leaving the object-storage blob is not deletion. Deletion across PostgreSQL, object storage, derived artifacts, caches, and backup tracking cannot be made atomic across these boundaries — the requirement is **eventually complete and verifiable deletion**, not distributed atomicity.

The deletion workflow must follow this sequence:

```
Deletion requested
  → DB tombstone / soft-delete transaction (atomic within PostgreSQL)
  → Deletion job enqueued
    ├── Object storage: original document deleted
    ├── Object storage: derived artifacts (crops, processed images, reports) deleted
    ├── Cache: any cached representations invalidated
    └── Backup tracking: deletion marker written so backup restoration does not reinstate deleted records
  → Verification pass: confirm all layers cleared
  → Audit event written: deletion complete, scope confirmed
```

The deletion job must be idempotent — retrying after a partial failure must not produce duplicate deletions or leave inconsistent state. The system must expose a deletion status that confirms cross-layer completion, not just the DB transaction.

### 20.3 Audit records on deletion

Deletion events are recorded in the audit log. The audit record itself is not deleted.

### 20.4 Patient records

Patient records that have no associated prescription documents may be deleted. Patient records with associated documents follow the prescription document retention policy.

---

## 21. API and Product Boundaries

### 21.1 API style

RESTful, versioned (`/api/v1/`). OpenAPI 3.x spec is canonical. All clients (web, worker, internal) derive their contracts from the OpenAPI spec. No client maintains a shadow schema.

### 21.2 Key endpoints (behavioral contract)

| Endpoint | Method | Behavior |
|---|---|---|
| `/api/v1/prescriptions` | POST | Accept document upload. Return 202 + `{analysis_id, prescription_id}`. |
| `/api/v1/analyses/{id}` | GET | Return current analysis status and stage. |
| `/api/v1/analyses/{id}/result` | GET | Return full analysis result (only if COMPLETED or REQUIRES_REVIEW). |
| `/api/v1/analyses/{id}/review` | POST | Submit reviewer decisions. |
| `/api/v1/prescriptions/{id}` | DELETE | Delete document and all derived data. |
| `/api/v1/health` | GET | System health check. |

### 21.3 Response contract for analysis results

The analysis result response must include:
- `analysis_id`, `status`, `analysis_timestamp`
- `model_versions[]`
- `knowledge_snapshots[]`
- Per medication line: extracted fields with `state` and `confidence` per field.
- Per finding: all provenance fields from §18.1.
- `not_evaluated[]`: list of medications/pairs not evaluated, with reason.
- `coverage_disclaimer`: explicit text stating that absence of findings is not safety confirmation.
- `explanation` (nullable): LLM explanation if generated and validated.

### 21.4 Error responses

All errors return structured JSON: `{error_code, message, request_id}`. No stack traces in production responses.

### 21.5 Async contract

Upload responds before analysis starts. Status polling is the expected client pattern. Webhook/subscription delivery is a deferred feature. The API must not block on analysis completion.

---

## 22. MVP Scope

### 22.1 In scope

**Product:**
- Prescription document upload (JPEG, PNG, TIFF, PDF single-page).
- Analysis status dashboard.
- Structured-extraction review interface with field-level confidence.
- Safety report with per-finding provenance.
- Human review workflow (manual reviewer assignment).
- Document and analysis history.
- Document deletion with full propagation.

**AI/ML:**
- Document quality check and orientation correction.
- Text region detection.
- Handwriting and print OCR with per-region confidence.
- Low-confidence routing to secondary verification.
- Structured field extraction: medication name, strength, dose, unit, frequency, route, duration, instructions.
- Field-state assignment: `CLEAR`, `AMBIGUOUS`, `UNREADABLE`, `NOT_PRESENT`.
- Medication normalization against canonical medication table.
- Duplicate medication detection.
- Selected evidence-backed interaction and safety checks using: openFDA, SIDER (subject to CC BY-NC-SA license constraint on deployment context).
- Confidence scoring throughout.
- LLM explanation generation (schema-constrained, gracefully degradable).

**Engineering:**
- PostgreSQL.
- Object storage for documents and derived artifacts.
- FastAPI application.
- Async worker (PostgreSQL-backed job queue).
- OpenAPI 3.x specification (canonical schema).
- Authentication and role-based access control.
- Audit log.
- Operational logging (non-PHI).
- Docker deployment.
- Automated tests: unit + integration, covering pipeline stages, safety engine (LLM-off), API contracts.

### 22.2 Safety scope boundary

| Supported | Limited | Not supported |
|---|---|---|
| Medication identity resolution | Contraindication checks | Diagnosis |
| Duplicate medication detection | Allergy checks (no patient allergy record in V1) | Treatment recommendation |
| Selected evidence-backed interaction checks | Individualized dosing analysis | Autonomous prescribing |
| Structured dose/frequency/unit extraction | | Comprehensive DDI coverage |
| Ambiguity detection and review routing | | Comprehensive clinical validation |
| Coverage-honest reporting | | |

### 22.3 Not in scope for V1 (explicitly)

- EHR integration.
- Patient-facing or physician-facing interfaces.
- Real-time analysis.
- Multi-page PDF.
- Non-English UI.
- Webhook/push delivery.
- Automated model deployment.
- Vector database / semantic retrieval.
- Redis, Kafka, Kubernetes.
- Multiple microservices.
- Comprehensive DDI database (commercial-grade).
- DrugBank runtime use (pending licensing).
- MIMIC-IV dependency.

---

## 23. Explicitly Deferred Scope

| Feature | Deferral reason |
|---|---|
| Automated model deployment | Requires measured regression gates; gates require a measured baseline that doesn't exist yet. |
| Vector DB / semantic retrieval | Requires experiment demonstrating it outperforms BM25/Postgres FTS on our own data. |
| Redis / Celery job queue | Requires measured workload demonstrating need beyond Postgres-backed queue. |
| DrugBank integration | Requires explicit licensing clearance for our deployment type. |
| Comprehensive DDI coverage | Not achievable from freely available sources; commercial licensing required. |
| Allergy checking | Requires patient allergy records; no patient-data intake in V1. |
| Webhook delivery | API polling is sufficient for V1 scale. |
| Automated reviewer assignment | Manual in V1; workflow complexity not justified at V1 scale. |
| Multi-page PDF | Increases pipeline complexity; single-page is sufficient for MVP validation. |
| Dedicated NER stage (BioBERT/ClinicalBERT) | Requires experiment to demonstrate improvement over direct structured extraction; not justified before benchmark. |

---

## 24. Acceptance Criteria

### 24.1 Pipeline completeness

- AC-01: A valid prescription image completes the full pipeline from upload to structured result without manual intervention under normal conditions.
- AC-02: A low-quality or ambiguous image produces a `REQUIRES_REVIEW` result with documented reasons, not a fabricated result.
- AC-03: An unrecognized medication triggers review routing, not normalization to a guessed drug.

### 24.2 Safety invariants

- AC-04: Disabling the LLM does not break or degrade the safety engine's ability to produce structured findings.
- AC-05: A `NOT_EVALUATED` finding is never displayed as `NO_INTERACTION_EXISTS` in any UI, API response, or generated explanation.
- AC-06: A finding with missing provenance fields is never surfaced to the reviewer interface.
- AC-07: The critical medication error rate on the Tier B evaluation set is measured and reported with a 95% CI before V1 is released.

### 24.3 Data and provenance

- AC-08: Every completed analysis result includes `model_versions[]`, `knowledge_snapshots[]`, and `analysis_timestamp`.
- AC-09: Document deletion produces eventually complete, verifiable deletion: the DB tombstone is written atomically, the deletion job completes across object storage and derived artifacts, and the verification pass confirms cross-layer completion before the deletion audit event is written.
- AC-10: Audit records persist after document deletion. The deletion event itself is audited.

### 24.4 API contract

- AC-11: All API responses conform to the canonical OpenAPI spec.
- AC-12: The safety engine is testable without external LLM API calls (all LLM calls are mockable).

### 24.5 Review workflow

- AC-13: A reviewer can independently approve, flag, or escalate each finding.
- AC-14: Review records are immutable after submission; corrections produce a new record.
- AC-15: The reviewer interface shows which medications were NOT evaluated and why.

---

## 25. Measurable Success Criteria

> [!NOTE]
> Exact numeric thresholds below are marked as **[POST-BASELINE]** where they must be set after measuring actual system variance on the Tier B evaluation set. Writing a number before that measurement is a guess wearing a decimal point — we don't do that.

| Metric | Measurement method | Threshold |
|---|---|---|
| Critical medication identity error rate | Tier B eval, expert-adjudicated | **[POST-BASELINE]** — set after baseline measured |
| Critical dose error rate | Tier B eval | **[POST-BASELINE]** |
| Critical unit error rate | Tier B eval | **[POST-BASELINE]** |
| Critical frequency error rate | Tier B eval | **[POST-BASELINE]** |
| Medication name extraction accuracy | Tier B eval, field-level | **[POST-BASELINE]** |
| Medication identity normalization accuracy | Tier B eval | **[POST-BASELINE]** |
| Structured field accuracy (per field) | Tier B eval | **[POST-BASELINE]** |
| Human review routing precision | Fraction of review-routed cases that actually required review | **[POST-BASELINE]** |
| Human review routing recall | Fraction of cases requiring review that were correctly routed | **[POST-BASELINE]** |
| False safety clearance rate | Cases where `NOT_EVALUATED` was misclassified as `SAFE` | Must be 0. Not post-baseline — this is an absolute invariant. |
| Analysis pipeline completion rate | Fraction of valid uploads that reach `COMPLETED` or `REQUIRES_REVIEW` without `FAILED` | **[POST-BASELINE]** |
| Upload P95 response time | Measured under load | **[POST-BASELINE]** |

All reported metrics include 95% confidence intervals and the evaluation set descriptor from §12.5.

---

## 26. Engineering Constraints

**EC-01 — Canonical schema:** Frontend, backend, DB, and ML all derive their data contracts from one canonical schema. No silently drifting shadow definitions. The OpenAPI spec is canonical for the API surface; the database schema is canonical for persistence.

**EC-02 — Modular monolith:** V1 is a single deployable unit. No microservices. Internal module boundaries are enforced by code structure, not by network boundaries.

**EC-03 — PostgreSQL primary store:** No second database engine. All relational data — including the job queue — lives in PostgreSQL.

**EC-04 — Object storage for binaries:** Prescription documents and all derived artifacts live in object storage. PostgreSQL holds only metadata and references.

**EC-05 — FastAPI:** The application layer is FastAPI with an async ASGI server.

**EC-06 — Async analysis:** Analysis is always asynchronous. No synchronous analysis path.

**EC-07 — Docker:** The full system (API, worker, DB, storage) runs in Docker. Local development and deployment use the same container configuration.

**EC-08 — No vector DB, Kafka, Redis, Kubernetes for V1:** These are explicitly rejected for V1 unless a specific measured requirement arises. Any PR introducing these components without a documented measurement-backed justification is rejected.

**EC-09 — License verification:** Every runtime dependency (libraries, model weights, data sources) must have its license verified against the primary source before use. License assumptions from reputation or model family name are not accepted.

---

## 27. Open Decisions

These are unresolved and require experimental measurement or explicit agreement before the ML architecture is locked. They do not block V1 implementation work that is independent of them — but they block shipping V1 as a complete product.

| Decision | What's needed to resolve |
|---|---|
| OCR model selection | Benchmark on Tier B: TrOCR variants vs. PP-OCRv6 recognition head-to-head. |
| VLM verification value | Experiment: does the VLM verification step reduce critical medication errors measurably vs. latency/cost? |
| Confidence thresholds | Set after baseline measurement on Tier B evaluation data. |
| Medication vocabulary sources | Legal review of reusability of available Indian brand/generic sources for seeding canonical table. |
| DDI coverage extent | What can legally be obtained for an academic prototype? Exact gap from comprehensive coverage? |
| SIDER deployment eligibility | CC BY-NC-SA: confirm non-commercial deployment context is clear. |
| Compute / latency baseline | Measure pipeline latency and VRAM under expected load. Determines whether V1 load targets are achievable. |
| Dedicated NER stage | Experiment: BioBERT/ClinicalBERT NER vs. direct structured extraction from OCR/VLM. |
| MedOCR-Vision record count | Direct verification against dataset card (spec flags this as unverified). |
| Prescription-specific TrOCR CER | Verify model-card CER number against primary source (spec flags this as unverified). |
| Regression gate values | Set from measured baseline variance, not pre-guessed. Required before ML deployment automation. |

---

## 28. PRD Lock Status

### LOCKED
_Must not change without explicit architecture and product review._

- Clinical decision-support positioning — not diagnostic, not autonomous.
- Human review required for all findings before any finding is treated as actionable.
- OCR uncertainty must never silently become clinical certainty (SR-01).
- LLM is explanation layer only — not a safety authority (SR-05).
- `NO_KNOWN_INTERACTION_IN_DATABASE` ≠ `NO_INTERACTION_EXISTS` — enforced in data model, API, and UI (SR-04).
- Safety findings require full provenance — finding with missing provenance is invalid (SR-06).
- Unrecognized medication → review, not forced normalization (SR-07).
- Safety engine must function with LLM disabled (SR-05).
- Every analysis records model/rule/knowledge versions (SR-09).
- PostgreSQL as primary data store.
- Object storage for all binaries.
- Async analysis — upload returns before analysis starts.
- Modular monolith — no microservices for V1.
- OpenAPI spec is the canonical API contract.
- No automated ML deployment until regression gates are measured and approved.
- Confidence intervals required on all reported eval metrics.
- Tier B evaluation set required before V1 model selection is locked.

### CONSTRAINED
_Implementation may change; the invariant may not._

- Async job queue: currently PostgreSQL-backed. May move to Redis/Celery if measured workload demands it. Invariant: analysis must be async, retry-safe, and observable.
- OCR/HTR model: implementation candidate, not locked. Invariant: the chosen model must be benchmarked on Tier B data, version-recorded, and satisfy all confidence/provenance requirements.
- Normalization strategy: implementation candidate. Invariant: unresolved medications route to review, all normalization results carry provenance.
- LLM model and provider: implementation candidate. Invariant: explanation layer must be schema-constrained, gracefully degradable, and unable to create unverified findings.
- Confidence threshold values: configurable, post-baseline. Invariant: thresholds exist, are configurable, and are approved before release.
- Safety source selection: openFDA and SIDER approved as candidates. Additional sources may be added via provider interface. Invariant: every source's license must be verified before use; every finding from every source carries full provenance.

### OPEN
_Unresolved — requires experiment or research before architecture locks._

- OCR model selection.
- VLM verification value vs. cost.
- Confidence threshold values.
- Medication vocabulary sources (Indian brands/generics).
- DDI coverage scope from legally available sources.
- Compute and latency baseline.
- Dedicated NER stage justification.
- MedOCR-Vision dataset verified counts.
- Prescription-specific TrOCR CER verified number.

### DEFERRED
_Explicitly excluded from V1 scope._

- Automated model deployment.
- Vector database / semantic retrieval.
- Redis / Celery job queue.
- DrugBank runtime integration (pending licensing).
- Comprehensive DDI coverage.
- Allergy checking.
- Webhook delivery.
- Automated reviewer assignment.
- Multi-page PDF.
- Dedicated NER stage.
- EHR integration.
- Patient-facing / physician-facing interfaces.
- Kafka, Kubernetes, service mesh.
- Non-English UI.
- Mobile native app.

---

_End of PRD v1_

---

**Self-review checklist (completed before delivery):**

- [x] Can an engineering team implement V1 without guessing behavior? Yes — each workflow has defined states, transitions, and failure modes.
- [x] Are all user-visible states defined? Yes — analysis lifecycle, prescription lifecycle, field states, finding states, review states all defined.
- [x] Are failure states defined? Yes — §16 covers document, pipeline, normalization, safety, explanation, and worker failure modes.
- [x] Are safety boundaries explicit? Yes — §10 contains 9 non-negotiable safety requirements.
- [x] Are acceptance criteria testable? Yes — §24 criteria are observable behaviors, not qualitative assertions.
- [x] Are requirements measurable? Yes — §25 distinguishes absolute invariants from post-baseline thresholds.
- [x] Did we accidentally promise comprehensive clinical safety? No — §4, §6.2, §22.2, and every finding state make limits explicit.
- [x] Did we make an ML model a product requirement? No — models are implementation candidates. Requirements are behavioral.
- [x] Did we introduce unnecessary infrastructure? No — §22.3 and §23 explicitly exclude and defer premature complexity.
- [x] Are requirements contradictory? None found.
- [x] Are terms ambiguous? Key terms defined: field states, finding states, analysis states, review states, data tiers.
- [x] Are there hidden assumptions? LLM availability assumed at runtime but failure path is defined (graceful degradation to structured finding).
- [x] Did we distinguish "not detected" from "does not exist"? Yes — §8.5 FR-SAFE-05, §10 SR-04, §17, §21.3.
- [x] Did we preserve uncertainty throughout? Yes — §17 defines propagation rules; §8.3 FR-OCR-05 prohibits coercion from `UNREADABLE` to a guessed value.
