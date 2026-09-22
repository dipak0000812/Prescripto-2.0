# DOMAIN-MODEL.md

Conceptual layer over the DDL in `SYSTEM-ARCHITECTURE.md` v1.1 §9. DDL is canonical; this explains boundaries and invariants the DDL enforces but doesn't narrate.

## Entity relationships

```
User ──uploads──> PrescriptionDocument ──1:N──> Analysis
                                                  ├──1:N──> AnalysisStage
                                                  ├──1:1──> AnalysisJob
                                                  ├──1:N──> PrescriptionMedication ──1:N──> MedicationCandidate ──0:1──> Medication
                                                  ├──1:N──> RiskFinding ──0:1──> KnowledgeSnapshot
                                                  └──1:N──> Review (reviewer: User)

ModelVersion ──1:N──> CalibrationSnapshot
PrescriptionDocument ──1:N──> DeletionJob
* ──> audit.events (polymorphic: resource_type + resource_id)
```

## Two data classes — the deletion boundary

| Class | Tables | Deletion behavior |
|---|---|---|
| **Prescription-scoped** | prescription_documents, analyses, analysis_stages, analysis_jobs, prescription_medications, medication_candidates, risk_findings, reviews | Purged on deletion request |
| **Global knowledge (immutable)** | medications, knowledge_snapshots, model_versions, calibration_snapshots | **Never deleted.** Shared across all users; deleting one user's data must not degrade the Medication Master |

This split is the reason `medication_candidates.resolved_medication_id` has no `ON DELETE CASCADE` toward `medications` — the arrow points from disposable to permanent, never the reverse.

## Aggregates

| Root | Owns | Module |
|---|---|---|
| `PrescriptionDocument` | file metadata, lifecycle | `domain/prescription` |
| `Analysis` | stages, job, line items, candidates, findings | `domain/analysis` |
| `Medication` | canonical identity + provenance | `domain/medication` |
| `Review` | reviewer decisions | `domain/review` |

`AnalysisStage`, `PrescriptionMedication`, `MedicationCandidate`, `RiskFinding` are **not** independent aggregates — mutated only through the owning `Analysis`.

## Entity notes

**PrescriptionDocument** — `storage_key` NULL until the object write verifies. The one load-bearing NULL in the model: it means "upload in flight," not "missing data." Orphan `UPLOAD_PENDING` rows are swept after 30 min.

**Analysis** — unit of both execution and review. `model_snapshot_id` is `NOT NULL`: an analysis cannot exist without a pinned model version.

**AnalysisStage** — `UNIQUE(analysis_id, stage_name)` plus `lease_token` is the fence. The unique constraint *is* the invariant "a stage commits at most one generation," not merely an index.

**AnalysisJob** — one per Analysis, not per stage. `lease_token` monotonic; `lease_expires_at > now()` validated inside the same transaction as every stage commit. Four total attempts (1 + 3 retries) before `DEAD`.

**PrescriptionMedication** — one row per medication line. Eight independently-stateful field groups (see PROJECT-SPEC §4 — DDL currently has six; open defect). `UNIQUE(analysis_id, line_index)` is the extraction stage's idempotency key.

**MedicationCandidate** — one scored attempt per (strategy, vocabulary) pair. Multiple candidates per line is normal; `AMBIGUOUS` means several scored comparably, which is a distinct failure from `UNRESOLVED` (nothing scored above threshold).

**Medication** — Medication Master. Keyed `UNIQUE(brand_name, generic_name, strength, dosage_form, route)`. `verification_status` distinguishes `VERIFIED_AUTHORITY` (CDSCO-sourced) from `PROVISIONAL` (research vocabulary) — a finding's trustworthiness inherits from this, so it is never defaulted silently.

**RiskFinding** — `UNIQUE(analysis_id, check_type, source_name, finding_key)` makes safety screening idempotent under re-execution. `finding_key` is a deterministic hash of the medication IDs + source, so a re-run produces the identical key rather than a duplicate row.

**KnowledgeSnapshot** — versioned pointer, not the data. `license_mode` gates runtime availability: `RESEARCH_ONLY` sources (SIDER) are excluded from commercial builds by configuration, enforced at provider registration.

**Review** — immutable post-submission. Corrections are new rows.

**DeletionJob** — `manifest_written` boolean is the durability gate: deletion is not `COMPLETE` until the manifest lands in the separately-permissioned retention vault, because a DB-only deletion is undone by any backup restore.

## Invariants: where each is actually enforced

| Invariant | Domain | DB | Notes |
|---|---|---|---|
| Stage commits at most once per generation | fence check | `UNIQUE(analysis_id, stage_name)` + lease validation | Both required |
| NOT_EVALUATED has a reason | constructor | `CHECK` | |
| UNREADABLE never reaches normalization | `ExtractedField.propagate()` raises | — | **Domain-only.** Pipeline ordering, not schema |
| AMBIGUOUS input cannot yield CONFIRMED_BY_SOURCE | safety engine rule | — | **Domain-only.** Candidate for a trigger post-V1 |
| Duplicate safety findings impossible | deterministic finding_key | `UNIQUE(analysis_id, check_type, source_name, finding_key)` | |
| Analysis immutable after REVIEWED_* | transition table | — | **Domain-only** |

The three domain-only rows are the model's soft spots — application discipline, not the database, is holding them. Worth a trigger once the schema settles; flagged rather than added as an unvalidated constraint now.