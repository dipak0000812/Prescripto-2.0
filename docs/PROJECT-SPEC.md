# PROJECT-SPEC.md — Canonical Source of Truth

**Version:** 1.1 · **Decision baseline:** 2026-10-02
**Rule:** where any document conflicts with this file, this file wins until explicitly updated.

---

## 1. Conflict Register (PRD v1 ↔ Architecture v1.1)

Architecture v1.1 postdates PRD v1 and supersedes it on these three points. PRD v1 must be amended; until it is, **this register is authoritative**.

| # | Conflict | Resolution | State |
|---|---|---|---|
| C-1 | PRD puts LLM explanations in V1; Architecture disables them | Structured report only; LLM remains out of V1 and no provider is selected | Resolved; PRD must conform |
| C-2 | PRD claims selected interaction checks; Architecture defers DDI | V1 makes no DDI, dosage, allergy, or adverse-event claim; only exact duplicate-product candidates are in scope | Resolved; PRD and safety contracts must conform |
| C-3 | PRD requires eight fields; Architecture DDL initially defined six | Eight field groups are required; DDL must include `unit` and `instructions` before migration 0001 | Resolved only when Architecture DDL is amended |
| C-4 | Docs name multiple canonical files that are absent from this workspace | Existing files listed in §10 are authoritative; absent implementation artifacts are gates, not implied complete docs | Resolved in this baseline |

## 2. Locked V1 Decision Baseline

These choices are locked for the academic research prototype. They do not establish clinical validity, regulatory clearance, or permission to process identifiable patient data.

| Area | Locked decision |
|---|---|
| Intended use | Offline/restricted research prototype for transcription, structured extraction, and qualified human review. No diagnosis, treatment, prescribing, or autonomous safety clearance. |
| V1 output | Structured extraction, field-level uncertainty, normalization candidates, and a coverage-complete review report. No generated explanation and no overall confidence score. |
| Safety checks | Exact same canonical product ID repeated within one uploaded prescription may produce a `POTENTIAL` duplicate candidate. It is not a patient medication-history check or a clinical interaction check. |
| External safety sources | No runtime openFDA, SIDER, RxNorm, or other external lookup in V1. This avoids unsupported Indian-market coverage, causal overclaiming, licensing ambiguity, and disclosure of medication names to third parties. |
| Unsupported checks | DDI, dosage range, allergy/contraindication, adverse-event causality, and broad evidence lookup are not evaluated in V1. The report must state this explicitly. |
| Human review | Every result is decision support. No output is actionable until a qualified/authorized reviewer reviews it. Unreadable, ambiguous, unresolved, failed, or unsupported items remain visible and cannot be silently omitted. |
| OCR pipeline | Decode and orient image → quality gate → text-region detection → deterministic line grouping/cropping → line recognition → rule-based field parsing with source spans → medication candidate generation → report. No VLM and no LLM in V1. |
| OCR model | PP-OCRv6 detector/recognizer and TrOCR-base-handwritten are benchmark candidates only. No production model winner is selected by reputation or paper-level aggregate scores. |
| Dataset/evaluation | Tier B is required for model promotion and calibrated `CLEAR` states. Group splits by prescriber/author and source organization; one untouched lockbox is evaluated once after model/rules/thresholds are frozen. |
| Identity normalization | Exact verified alias first; fuzzy matching may generate review candidates only. No automatic resolution from an unvalidated fuzzy score. RxNorm is optional metadata only and not an identity authority. |
| Data handling | No real or identifiable patient data until ethics approval, legal basis/consent, retention policy, access control, threat review, and deployment security review are documented. DPDPA compliance is not asserted by this specification. |

### Decisions deliberately not locked

The following are evidence or authority gates, not design indecision: recognition model and detector configuration (Tier B), numerical confidence/review thresholds (Tier B calibration), minimum sample size for any claimed error bound (statistical plan and observed class counts), CDSCO-derived data reuse (written legal clearance), real-data collection (ethics/legal approval), and any clinical deployment (regulatory/clinical review). If a gate is unmet, the corresponding capability stays disabled; a planning deadline does not waive it.

---

## 3. Terminology (canonical — no synonyms permitted)

| Term | Meaning | Never call it |
|---|---|---|
| **PrescriptionDocument** | The uploaded file + metadata. Immutable after ingestion. | prescription, scan, image record |
| **Analysis** | One pipeline execution over one document. | run, job, processing |
| **AnalysisJob** | Queue row driving one Analysis. | task, worker job |
| **AnalysisStage** | One pipeline step's committed result. | step, phase |
| **PrescriptionMedication** | One extracted medication *line* from a document. | medication, drug, line |
| **MedicationCandidate** | One scored normalization attempt for a line. | match, suggestion |
| **Medication** | Canonical entity in the global Medication Master. Never deleted. | drug, canonical drug, master drug |
| **RiskFinding** | A potential duplicate-product candidate emitted by the V1 deterministic rule. | risk, alert, warning, flag |
| **ScreeningCoverage** | Whether a requested check ran for a medication or scope, including an explicit reason when it did not. | not-evaluated finding |
| **KnowledgeSnapshot** | Versioned pointer to a knowledge source's state. | source, dataset |
| **Reviewer** | "qualified/authorized human reviewer" — full phrase in user-facing text | doctor, pharmacist, clinician (in code/UI copy) |

**Field naming:** `snake_case` everywhere — DB, API, DTOs. `medication_name` never `medicineName`/`drugName`/`name`.

---

## 4. Canonical Enums

```
FieldState:        CLEAR | AMBIGUOUS | UNREADABLE | NOT_PRESENT
ResolutionStatus:  RESOLVED | UNRESOLVED | AMBIGUOUS
FindingStatus:     POTENTIAL
SafetyCheckType:   DUPLICATE_MEDICATION
                   (EVIDENCE_LOOKUP, ADVERSE_EFFECT, KNOWN_INTERACTION, DOSAGE_RANGE — deferred; must not execute in V1)
CoverageStatus:    EVALUATED | NOT_EVALUATED
AnalysisStatus:    QUEUED | PROCESSING | COMPLETED | REQUIRES_REVIEW | REVIEWING
                   | REVIEWED_COMPLETE | REVIEWED_ESCALATED | FAILED
JobStatus:         PENDING | CLAIMED | RUNNING | SUCCEEDED | FAILED | DEAD | CANCELLED
StageStatus:       RUNNING | COMPLETED | FAILED | SKIPPED
DocumentStatus:    UPLOAD_PENDING | UPLOADED | DELETION_REQUESTED | DELETION_IN_PROGRESS | DELETED
DeletionStatus:    REQUESTED | DB_TOMBSTONED | STORAGE_DELETING | VERIFYING | COMPLETE | PARTIAL_FAILURE
ReviewStatus:      PENDING_ASSIGNMENT | ASSIGNED | IN_PROGRESS | SUBMITTED | ESCALATED
ReviewAction:      APPROVED | FLAGGED | ESCALATED
Role:              OPERATOR | REVIEWER | ADMIN
LicenseMode:       COMMERCIAL_PERMISSIVE | RESEARCH_ONLY | PUBLIC_DOMAIN
```

**Pipeline stage names** (exact strings, `analysis_stages.stage_name`):
`INGESTION`, `QUALITY_CHECK`, `TEXT_DETECTION`, `OCR_RECOGNITION`, `STRUCTURED_EXTRACTION`, `MEDICATION_NORMALIZATION`, `SAFETY_SCREENING`, `REPORT_ASSEMBLY`

> `VLM_VERIFICATION` and `EXPLANATION_GENERATION` are **not** V1 stage names. v1.1 dropped both from the pipeline table. Re-adding either requires a spec update first.

---

## 5. Canonical Structured Fields (8)

Every `PrescriptionMedication` carries these eight field groups, each with `_raw`, `_state`, `_confidence`:

`name`, `strength`, `dose`, `unit`, `frequency`, `route`, `duration`, `instructions`

The DDL must persist `unit` and `instructions` along with the original six groups before the first migration:

```sql
ALTER TABLE prescription_medications
  ADD COLUMN unit_raw TEXT,
  ADD COLUMN unit_state TEXT NOT NULL DEFAULT 'NOT_PRESENT'
      CHECK (unit_state IN ('CLEAR','AMBIGUOUS','UNREADABLE','NOT_PRESENT')),
  ADD COLUMN unit_confidence REAL,
  ADD COLUMN instructions_raw TEXT,
  ADD COLUMN instructions_state TEXT NOT NULL DEFAULT 'NOT_PRESENT'
      CHECK (instructions_state IN ('CLEAR','AMBIGUOUS','UNREADABLE','NOT_PRESENT')),
  ADD COLUMN instructions_confidence REAL;
```

---

## 6. Confidence Semantics (what each number means)

| Layer | Value | Meaning | Comparable across models? |
|---|---|---|---|
| Model-native | `raw_score` | Beam-search score (TrOCR) or CTC probability (PP-OCR) | **No** |
| Calibrated | `calibrated_confidence` | Estimated probability that the specific output target is correct, calibrated on end-to-end Tier B labels for that target | Only for the same target, dataset protocol, and model/pipeline version |
| Field | `FieldState` | Calibrated confidence bucketed against the version's `review_threshold` | Yes |
| Finding | `confidence_score` | Evidence strength from the source — **not** a model probability | No — never averaged with OCR confidence |

**Prohibited:** treating OCR-native score as field correctness, or producing a single "overall analysis confidence" score. Review routing is triggered by explicit state/rule conditions, never by an averaged scalar. If target-level calibration is unsupported by sample counts, the output cannot be `CLEAR` on model confidence alone.

---

## 7. Versioned Identifiers

Every `Analysis` pins: `pipeline_version` (semver of pipeline code), `model_snapshot_id` → `model_versions.id`, `knowledge_snapshot_id` per finding. No `"latest"` string is permitted in any production code path. Re-running with a new version creates a new `Analysis`, never an update.

---

## 8. Screening Coverage Contract

`RiskFinding` and `ScreeningCoverage` are separate concepts. A non-evaluation is not a finding and must not be encoded as an empty list or as a negative result. For every in-scope check and medication/scope, record `EVALUATED` or `NOT_EVALUATED`; the latter requires a reason. V1 coverage reasons include `UNRESOLVED_IDENTITY`, `AMBIGUOUS_IDENTITY`, `MASTER_ENTRY_UNVERIFIED`, and `CHECK_NOT_SUPPORTED`. The response includes both `findings[]` and `not_evaluated[]`; a finding may not imply that all checks ran.

## 9. Non-Functional Requirements (consolidated)

| ID | Requirement | Status |
|---|---|---|
| NFR-01 | Upload P95 ≤ 3s | Target — unmeasured |
| NFR-02 | Analysis 30–180s | Planning assumption — unmeasured |
| NFR-03 | Single instance, single worker | V1 constraint |
| NFR-04 | No PHI in operational logs | Invariant |
| NFR-05 | mypy `--strict` across `domain/` | CI gate |
| NFR-06 | Every endpoint conforms to `/openapi.json` | CI gate |

---

## 10. Document Map and Workspace Status

| Doc | Authority over |
|---|---|
| `PROJECT-SPEC.md` (this) | Terminology, enums, conflicts, confidence semantics |
| `PRD_V1.md` | Product behavior and requirements; must be amended to match this baseline |
| `Architecture.md` | Components, DDL, ADRs, execution model |
| `API-CONTRACT.md` | Behavioral API contract. Machine-readable OpenAPI is a pre-implementation deliverable; none exists in this workspace yet |
| `ERROR-CONTRACT.md` | Error codes |
| `ML-ARCHITECTURE.md`, `MODEL-SPECIFICATIONS.md`, `DATA-SPECIFICATION.md`, `DATASET-CATALOG.md` | ML pipeline, candidates, data, and evaluation contract |
| `SECURITY.md` | Security posture; threat model remains a pre-real-data gate |
| `OBSERVABILITY.md`, `DEPLOYMENT.md`, `CI-CD.md` | Operations targets; implementation has not started |
| `IMPLEMENTATION-PLAN.md` | Build order |

This workspace currently contains documentation only. Referenced but absent artifacts (including `ML-PIPELINES.md`, `EVALUATION-PLAN.md`, `THREAT-MODEL.md`, `TEST-STRATEGY.md`, and `openapi.yaml`) are not considered complete or authoritative until created and reviewed.