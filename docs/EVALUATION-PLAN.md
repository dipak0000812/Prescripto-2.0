# EVALUATION-PLAN.md

**Status:** Protocol locked; dataset, thresholds, and model promotion are blocked until Tier B is collected and adjudicated.

## Purpose and claims boundary

This protocol selects research-prototype OCR/extraction components. It does not establish clinical safety, regulatory clearance, or suitability for autonomous use. Tier A/public and synthetic data may support development and debugging but may not select a model, set a production threshold, or be reported as Indian prescription ground truth.

## Tier B governance and annotation

Target 200-500 legally obtained prescriptions is a collection target, not proof of statistical adequacy. Collection requires documented authority/consent and ethics review as applicable, de-identification before system ingestion, controlled access, retention/deletion terms, and a provenance record. A qualified legal/privacy owner must approve the data-use basis before collection begins.

Two annotators independently label each page; disagreements are adjudicated by a qualified medication-domain reviewer. Annotation includes:

- Page properties: capture type, language/script, print/handwriting/mixed, source organization, and a pseudonymous writer/prescriber grouping key maintained by the data custodian.
- Text regions and medication-line grouping, with bounding boxes and reading order.
- Verbatim transcription and character spans for each of the eight structured fields.
- Field value, one of the four canonical `FieldState` labels, and an uncertainty/adjudication note.
- Canonical medication identity only when adjudicated; otherwise explicitly unresolved.
- Error severity labels for identity, dose, unit, and frequency errors, defined by the qualified annotators before scoring.

Do not retain direct identifiers in the benchmark. The pseudonymous grouping key is sensitive linkage data: keep it separately access-controlled and do not expose it in model inputs or reports.

## Split and lockbox policy

Split by writer/prescriber and source organization, not by image. No patient, writer, source duplicate, near-duplicate, or augmented derivative may cross partitions. Use a development partition for model/rule selection and calibration; reserve an independent lockbox for final evaluation. If fine-tuning is authorized, create a separate training subset within development. Freeze the dataset manifest, annotations, code, model hashes, and thresholds before opening the lockbox. The lockbox is evaluated once for a release candidate; after any tuning based on its results, it is no longer a holdout and a new holdout is required.

If the available cohort cannot support meaningful grouped partitions or stable target-level calibration, report feasibility results only. Do not lower the standard, reuse the holdout, or claim a validated threshold to meet a schedule.

## Candidate comparisons

Compare, under the same preprocessing and line crops:

1. PP-OCRv6 recognition baseline.
2. TrOCR-base-handwritten line recognizer.
3. A prescription-fine-tuned recognizer only after exact checkpoint license, training-data rights, and reproducible artifact provenance are verified.
4. TrOCR-large only if measured hardware feasibility and latency/resource requirements are satisfied.

Benchmark detector and line grouping separately. PP-OCRv6 paper-level aggregate metrics are context only; they are not estimates of performance on this prescription cohort. No model is selected from model-card claims or aggregate benchmark scores.

## Metrics and reporting

Report denominators and 95% confidence intervals, stratified where sample counts permit, for:

- Detection/line grouping: region precision/recall, line recall, merged-line and split-line rates.
- Transcription: CER and WER, plus exact medication-line match.
- Extraction: exact match and normalized value accuracy for each of the eight fields; report `NOT_PRESENT` and `UNREADABLE` handling separately.
- Medication identity: precision among automatically resolved identities, candidate recall, unresolved/ambiguous rate, and wrong-canonical-identity rate.
- Safety rule: exact-duplicate candidate precision/recall against adjudicated repeated canonical product lines; do not score this as DDI detection.
- Review routing: critical-error sensitivity, false-review rate, and selective risk versus automation coverage.
- Calibration: reliability plots and Brier score/ECE only for explicitly defined target outcomes with adequate sample counts.
- Operations: cold/warm latency, peak memory, device/runtime, batch size, and failures per page/line.

Compute confidence intervals with resampling clustered at the independent writer/prescriber or source-group level; do not treat lines from one prescription as independent observations. Report subgroup counts and avoid publishing unstable subgroup point estimates as general performance.

## Calibration and threshold selection

Fit calibration using only development data, separated from model selection where feasible. Calibration target must match the decision being made (line transcription correctness, individual field correctness, or medication identity correctness). OCR token/beam/CTC scores cannot stand in for field correctness. Prefer a simple calibration method supported by the sample size; if bins are sparse or calibration is unstable, do not claim calibrated probabilities.

Select review thresholds on development data against an explicitly documented operating objective. The product/safety owner must define the maximum acceptable critical-error risk and review workload before threshold selection; this document does not invent clinical risk tolerances. Freeze thresholds before lockbox evaluation. A missing or inadequate calibration artifact blocks model startup for any mode that emits confidence-based `CLEAR` states.

## Promotion gate

A candidate can be promoted only when all of the following are recorded and approved:

- Tier B rights, de-identification, annotation, adjudication, and split manifest are complete.
- Exact model/checkpoint license and hash are verified.
- Lockbox report includes all required metrics, denominators, clustered confidence intervals, and subgroup limitations.
- Critical identity, dose, unit, and frequency error bounds satisfy pre-approved product/safety criteria; non-inferiority cannot be inferred from overlapping confidence intervals alone.
- Target-specific calibration is stable and the review workload is operationally feasible.
- Reviewer sign-off and model/pipeline/calibration registry entries are complete.

Until this gate passes, only a clearly labeled research/demo mode is allowed, with no claim that model confidence is calibrated for clinical correctness. If no candidate passes, keep automation disabled and continue human transcription/review; do not choose the least-bad candidate by default.
