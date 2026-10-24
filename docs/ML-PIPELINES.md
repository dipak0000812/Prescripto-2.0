# ML-PIPELINES.md

**Status:** V1 pipeline contract locked; model winner and thresholds remain evaluation-gated.
**Authority:** PROJECT-SPEC.md controls shared enums and product boundaries. This document defines stage inputs, outputs, and failure behavior.

## Pipeline contract

The pipeline preserves the original document and never replaces source content with corrected or normalized text. Every stage output is versioned, tied to its input, and committed idempotently. Raw OCR text, parsed fields, normalization candidates, and reviewer corrections remain distinct artifacts.

| Stage | Input | Output | Failure behavior |
|---|---|---|---|
| `INGESTION` | Uploaded bytes | Verified MIME, dimensions/page count, immutable storage reference, SHA-256 | Reject invalid/unsupported input; no analysis is queued |
| `QUALITY_CHECK` | Decoded page | Orientation-corrected working image, quality measurements, quality state | Low quality remains reviewable; never silently discard a page |
| `TEXT_DETECTION` | Working image | Text-region boxes, detector version, raw scores | Detection failure produces a failed stage and reviewable error; no fabricated empty transcription |
| `OCR_RECOGNITION` | Grouped line crops | Verbatim recognized text, crop coordinates, raw score, recognizer version | A missing/unreadable region is explicit; do not substitute a language-model guess |
| `STRUCTURED_EXTRACTION` | Verbatim OCR lines with geometry | Eight field values, raw spans, state, calibrated confidence when available | Parse failure is explicit; retain OCR text and route for review |
| `MEDICATION_NORMALIZATION` | Name field plus approved master/aliases | Ranked candidates, match method, vocabulary version, resolution status | Fuzzy-only candidate is review-only; unresolved stays unresolved |
| `SAFETY_SCREENING` | Resolved, verified canonical product IDs | Exact repeated-product candidates and per-check coverage records | Unsupported or ineligible check becomes `NOT_EVALUATED` with reason |
| `REPORT_ASSEMBLY` | All preceding artifacts | Structured result, review reasons, findings, coverage, source/version provenance | Incomplete required artifacts fail closed; partial output is not labeled complete |

## Image and text path

1. Validate format from file signatures, size, page count, and successful decoding. Enforce configurable decoded-pixel and dimension ceilings to prevent decompression/resource exhaustion; the numeric ceilings must be set and load-tested before implementation. Reject PDFs with active content; do not silently strip or rewrite the source.
2. Apply EXIF orientation and deterministic image normalization only to a derived working copy. Preserve the uploaded original unchanged. Record transform parameters and output hash.
3. Run text detection on the full working page. A detector box is not assumed to equal a medication line. Group boxes into line crops with a deterministic, versioned geometry rule; record source boxes and the grouping decision. Evaluate missed, merged, and split lines.
4. Recognize each line crop. TrOCR is single-line input; full-page use is invalid. Preserve exact decoded text and model-native score. Any optional candidate strings remain alternatives, never silent corrections.
5. Order regions by documented reading order while retaining coordinates. Multi-column ambiguity, overlapping regions, or uncertain grouping routes to review rather than merging unrelated medication lines.

## Structured extraction

The parser is deterministic and versioned. It may recognize explicit lexical forms for strength, dose, unit, frequency, route, duration, and instructions, but it must not infer omitted values or convert instructions into a recommendation. Every parsed value carries the OCR character span(s) that support it. Original text is retained verbatim.

`CLEAR`, `AMBIGUOUS`, `UNREADABLE`, and `NOT_PRESENT` are distinct:

- `CLEAR`: target-level calibrated correctness meets the approved threshold and no parser conflict exists.
- `AMBIGUOUS`: competing parses, uncertain OCR/grouping, conflicting evidence, or confidence below threshold.
- `UNREADABLE`: the source region cannot support a value; it is excluded from downstream identity/risk evaluation and appears in coverage.
- `NOT_PRESENT`: the field is absent; it remains absent and is never converted to zero, a default, or `AMBIGUOUS`.

State propagation is monotone: `CLEAR` may proceed; `AMBIGUOUS` remains uncertain; `UNREADABLE` cannot be consumed downstream; `NOT_PRESENT` remains absent. No downstream component may upgrade an uncertain state without a reviewer correction recorded separately.

## Normalization and V1 screening

- Match exact verified aliases first. Fuzzy/phonetic search may propose candidates for review only until Tier B evidence and a reviewed threshold support automatic resolution.
- A canonical product is eligible for the V1 duplicate rule only when its identity and master verification status are approved. Candidate-vocabulary entries are not canonical truth.
- The only V1 safety rule detects the same canonical product ID repeated on the same prescription. It emits a `POTENTIAL` finding for a reviewer; it does not assert a harmful interaction, duplicate ingredient across different formulations, or duplication against the patient's medication history.
- V1 makes no openFDA, SIDER, RxNorm, DDI, dosage-range, allergy, contraindication, or adverse-event causality query. Each unsupported/ineligible check is represented in `not_evaluated[]` with an explicit reason.

## Confidence and calibration boundary

Model-native scores are never interpreted as probabilities. Calibration is tied to the exact model artifact, pipeline/parser version, output target (for example line transcription versus medication-name field), and calibration dataset version. Calibrating line OCR does not calibrate a parsed dose or normalized medication identity. If a target lacks adequate calibration data, it cannot receive a confidence-based `CLEAR` state; route it to review. Numerical thresholds are not set in this document.

## Output contract

The completed result contains:

- One record per detected medication line, including all eight fields and their states.
- OCR text and supporting region/span references needed by the reviewer.
- Normalization status and candidates, with match provenance.
- Potential duplicate findings, with rule/version and involved canonical product IDs.
- Complete evaluated/not-evaluated coverage for each supported check and eligible subject.
- Pipeline/model/calibration/dataset versions and the mandatory coverage disclaimer.
- Review-required reasons, including stage errors and uncertain or unresolved fields.

No generated narrative or overall confidence is part of V1. The reviewer interface must not hide unreadable or not-evaluated items.

## Deferred stages

VLM verification, learned field extraction/NER, LLM explanations, external evidence retrieval, and additional clinical checks are not V1 stages. A proposal to add one requires a new decision record, privacy/license review, failure-mode analysis, and a Tier B experiment demonstrating measurable benefit on critical field/identity errors without increasing false certainty.
