# DATA-SPECIFICATION.md

Data contracts, versioning, and reproducibility. Dataset inventory is in DATASET-CATALOG.md.

## Input contract

| Property | Constraint | Enforced |
|---|---|---|
| Format | JPEG, PNG, TIFF, single-page PDF | Magic bytes, not extension or client MIME |
| Size | ≤ 20 MB | API + `CHECK (file_size_bytes <= 20971520)` |
| Pages | 1 (PDF: page 1 only) | Ingestion |
| Resolution | No hard minimum; low DPI → `QUALITY_TOO_LOW` → review | Quality check |
| Content | English / Hindi-English mixed | Best-effort; non-Latin script accuracy unmeasured |

## Version identifiers

Five independently versioned things. An analysis result is only reproducible if all five are pinned.

| Thing | Identifier | Where |
|---|---|---|
| Pipeline code | semver `pipeline_version` | `analyses.pipeline_version` |
| Model | `model_versions.id` + `checkpoint_sha256` | `analyses.model_snapshot_id` |
| Calibration | `calibration_snapshots.id` | FK from model_versions |
| Knowledge source | `knowledge_snapshots.id` + `source_version` | FK per `risk_findings` row |
| Dataset | `dataset_version` string in eval reports | EVALUATION-PLAN.md |

**`"latest"` is banned in production code paths.** Not discouraged — banned, and checked in CI. A result that can't name the exact artifacts that produced it isn't reproducible, and an irreproducible clinical finding can't be defended when it's questioned.

## Reproducibility contract

Given `analysis_id`, these are recoverable: model + checkpoint hash, calibration curve, knowledge snapshot per finding, pipeline version, every stage's output JSON, exact timestamps. Re-running with the same pins should produce identical structured output — the pipeline has no stochastic stage in V1 (LLM off, all extraction rule-based).

That property disappears the moment the LLM layer is enabled. Note it as a V1.x design constraint now, not a surprise later.

## Annotation schema (Tier B)

```
prescription_id, image_path, capture_type (SCANNED|PHOTOGRAPHED),
script_type (HANDWRITTEN|PRINTED|MIXED), language (EN|HI_EN|OTHER),
prescriber_id (pseudonymous — enables author-level splitting),
transcription: full-page verbatim text
line_items[]:
  line_index, and for each of the 8 fields: {value, state, annotator_note}
  states: CLEAR | AMBIGUOUS | UNREADABLE | NOT_PRESENT
  ground_truth_medication_id  (canonical Master ID, nullable)
adjudication: {annotator_a, annotator_b, adjudicator, disagreement_count}
```

`prescriber_id` is not optional metadata — without it, author-level splitting is impossible and the benchmark inflates.

## De-identification

Removed before ingestion: patient name, address, phone, ID numbers, prescriber name and registration number, clinic identifiers, any visible date that could re-identify in combination.

Retained: medication content, dosage, clinical instructions — the signal.

Method: manual redaction with visual verification. Automated redaction is **not** trusted for Tier B. Verification is a second pair of eyes, not the redactor's own.

## Data classification

| Class | Applies to | Handling |
|---|---|---|
| `SENSITIVE_PERSONAL_DATA` | Prescription images, extracted text, patient_ref | Encrypted at rest, caller-scoped, never logged |
| `OPERATIONAL` | IDs, statuses, durations, error codes | Loggable |
| `PUBLIC_KNOWLEDGE` | Medication Master, knowledge snapshots | Freely queryable within the app |

Governing framework: **DPDPA 2023 + DPDPA Rules 2025**. Not HIPAA — applying a US framework to an Indian academic system is legally sloppy, not conservative.

## Storage layout

```
prescriptions/{document_id}/original.{ext}
prescriptions/{document_id}/analyses/{analysis_id}/regions/{i}.png
models/{model_name}/{model_version}/
audit-archive/{yyyy}/{mm}/{dd}/
retention/deletion-manifest/{document_id}.json   ← separately permissioned vault
```

Deterministic keys make storage writes idempotent under retry. The retention vault is IAM-isolated from the application tenant — the application can write a manifest but cannot delete one, which is the point.

## Retention

| Data | Default | Configurable |
|---|---|---|
| Prescription documents | 30 days (research) | Per environment |
| Region crops | Same as parent | Purgeable earlier if storage-bound |
| Analysis records | Same as parent | |
| Audit events | Never deleted; 90 days hot + cold archive | |
| Medication Master, knowledge snapshots | Permanent | Never deleted |

"No retention policy" is not a valid deployment state. A default must be set at deploy time.