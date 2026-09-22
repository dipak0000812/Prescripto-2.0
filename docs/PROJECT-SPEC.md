# PROJECT-SPEC.md — Canonical Source of Truth

**Version:** 1.0 · **Aligned to:** PRD v1 + System Architecture v1.1 (LOCKED)
**Rule:** where any document conflicts with this file, this file wins until explicitly updated.

---

## 1. Conflict Register (PRD v1 ↔ Architecture v1.1)

Architecture v1.1 postdates PRD v1 and supersedes it on these three points. PRD v1 must be amended; until it is, **this register is authoritative**.

| # | PRD v1 says | Arch v1.1 says | Resolution | PRD sections to amend |
|---|---|---|---|---|
| C-1 | LLM explanation is in MVP scope; §8.6 FR-REP-01..05 define its behavior | `LLM_ENABLED = false` in V1; structured report is the complete product (ADR-09) | **v1.1 wins.** LLM deferred to V1.x. FR-REP-01/04/05 still apply to the *structured* report. FR-REP-02/03 become V1.x requirements. | §8.6, §12.7, §22.1, §23, §28 |
| C-2 | §22.2 lists "selected evidence-backed interaction checks" as *Supported* | `KNOWN_INTERACTION` (DDI) **deferred entirely** in V1; check types limited to `DUPLICATE_MEDICATION`, `EVIDENCE_LOOKUP`, `ADVERSE_EFFECT` (ADR-08) | **v1.1 wins.** V1 makes no interaction-detection claim of any kind. | §8.5 FR-SAFE-07, §22.2 |
| C-3 | §8.3 FR-OCR-06 and §12.1 require `unit` and `instructions` as independently stated+scored fields | `prescription_medications` DDL has only 6 field groups — `unit` and `instructions` absent | **PRD wins.** Without a `unit` column, "critical unit error" (mg→mcg, §12.1) is unmeasurable. Schema must add both. See §4 below. | Arch §9 DDL — **open defect, not yet fixed in v1.1** |

> [!WARNING]
> **C-3 is an open schema defect.** v1.1 locked without it. Two of the four critical-error metrics the PRD mandates (`critical unit error`, and instruction-level extraction) cannot be computed against the current DDL. Fix before the first Alembic migration is written — retrofitting columns after Tier B annotation begins means re-annotating.

---

## 2. Terminology (canonical — no synonyms permitted)

| Term | Meaning | Never call it |
|---|---|---|
| **PrescriptionDocument** | The uploaded file + metadata. Immutable after ingestion. | prescription, scan, image record |
| **Analysis** | One pipeline execution over one document. | run, job, processing |
| **AnalysisJob** | Queue row driving one Analysis. | task, worker job |
| **AnalysisStage** | One pipeline step's committed result. | step, phase |
| **PrescriptionMedication** | One extracted medication *line* from a document. | medication, drug, line |
| **MedicationCandidate** | One scored normalization attempt for a line. | match, suggestion |
| **Medication** | Canonical entity in the global Medication Master. Never deleted. | drug, canonical drug, master drug |
| **RiskFinding** | One safety-check result. | risk, alert, warning, flag |
| **KnowledgeSnapshot** | Versioned pointer to a knowledge source's state. | source, dataset |
| **Reviewer** | "qualified/authorized human reviewer" — full phrase in user-facing text | doctor, pharmacist, clinician (in code/UI copy) |

**Field naming:** `snake_case` everywhere — DB, API, DTOs. `medication_name` never `medicineName`/`drugName`/`name`.

---

## 3. Canonical Enums

```
FieldState:        CLEAR | AMBIGUOUS | UNREADABLE | NOT_PRESENT
ResolutionStatus:  RESOLVED | UNRESOLVED | AMBIGUOUS
FindingStatus:     CONFIRMED_BY_SOURCE | POTENTIAL | INSUFFICIENT_EVIDENCE | NOT_EVALUATED | REQUIRES_REVIEW
SafetyCheckType:   DUPLICATE_MEDICATION | EVIDENCE_LOOKUP | ADVERSE_EFFECT
                   (KNOWN_INTERACTION, DOSAGE_RANGE — deferred, must not appear in V1 code)
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

## 4. Canonical Structured Fields (8, not 6)

Every `PrescriptionMedication` carries these eight field groups, each with `_raw`, `_state`, `_confidence`:

`name`, `strength`, `dose`, `unit`, `frequency`, `route`, `duration`, `instructions`

Arch v1.1 DDL currently omits `unit` and `instructions` (conflict C-1 above). Required DDL addition:

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

## 5. Confidence Semantics (what each number means)

| Layer | Value | Meaning | Comparable across models? |
|---|---|---|---|
| Model-native | `raw_score` | Beam-search score (TrOCR) or CTC probability (PP-OCR) | **No** |
| Calibrated | `calibrated_confidence` | P(field correct), from that model version's calibration snapshot | Yes, within a model version |
| Field | `FieldState` | Calibrated confidence bucketed against the version's `review_threshold` | Yes |
| Finding | `confidence_score` | Evidence strength from the source — **not** a model probability | No — never averaged with OCR confidence |

**Prohibited:** any single "overall analysis confidence" score (PRD §17.1). Review routing is triggered by *rules over states*, never by an averaged scalar.

---

## 6. Versioned Identifiers

Every `Analysis` pins: `pipeline_version` (semver of pipeline code), `model_snapshot_id` → `model_versions.id`, `knowledge_snapshot_id` per finding. No `"latest"` string is permitted in any production code path. Re-running with a new version creates a new `Analysis`, never an update.

---

## 7. Non-Functional Requirements (consolidated)

| ID | Requirement | Status |
|---|---|---|
| NFR-01 | Upload P95 ≤ 3s | Target — unmeasured |
| NFR-02 | Analysis 30–180s | Planning assumption — unmeasured |
| NFR-03 | Single instance, single worker | V1 constraint |
| NFR-04 | No PHI in operational logs | Invariant |
| NFR-05 | mypy `--strict` across `domain/` | CI gate |
| NFR-06 | Every endpoint conforms to `/openapi.json` | CI gate |

---

## 8. Document Map

| Doc | Authority over |
|---|---|
| `PROJECT-SPEC.md` (this) | Terminology, enums, conflicts, confidence semantics |
| `PRD.md` | Product behavior, requirements, acceptance criteria |
| `SYSTEM-ARCHITECTURE.md` v1.1 | Components, DDL, ADRs, execution model |
| `API-CONTRACT.md` + `openapi.yaml` | API surface |
| `ERROR-CONTRACT.md` | Error codes |
| `ML-*.md`, `DATASET-CATALOG.md`, `EVALUATION-PLAN.md` | ML pipeline, models, data, metrics |
| `SECURITY.md`, `THREAT-MODEL.md` | Security posture |
| `TEST-STRATEGY.md`, `OBSERVABILITY.md`, `DEPLOYMENT.md`, `CI-CD.md` | Operations |
| `IMPLEMENTATION-PLAN.md` | Build order |