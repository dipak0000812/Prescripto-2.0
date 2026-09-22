# DATASET-CATALOG.md

**Rule: no dataset enters the pipeline until its license is verified against the primary source.** Reputation, model-family name, and "it's on HuggingFace" are not license verification.

## Tier assignment (PRD §12.4)

- **Tier A** — public/research. Pretraining, baseline comparison, vocabulary. **Never** the selection benchmark.
- **Tier B** — our own, legally obtained, de-identified, expert-adjudicated. The **only** data that selects models or sets thresholds.
- **Tier C** — synthetic/augmented. Robustness training only. Never reported as equivalent to real clinical data.

## Tier A — OCR / prescription images

| Dataset | Size | License | Status | Use | Limitations |
|---|---|---|---|---|---|
| **MedOCR-Vision** | 2,462 docs (~1,000 handwritten prescriptions, 426 lab reports, 1,000 invoices, 36 OMR) | MIT | ✅ Verified | Pretraining, baseline | General medical-document OCR, **not confirmed India-specific**, not confirmed per-field structured. Do not cite as Indian ground truth |
| **RxHandBD** (Mendeley) | ~5,578 handwritten word crops, 80/20 split | Check card | ⚠️ Verify | Vocabulary, word-level baseline | **Word crops, not full pages** — doesn't match our page→detect→crop input shape. Bangladesh-sourced |
| **Bangladesh curated prescriptions** (Mendeley) | 200 full prescription images, Bangla/English/mixed, YOLO medicine-region boxes | Check card | ⚠️ Verify | Detection stage baseline | Closest public match to our actual input shape. Requires de-identification inspection before use |
| **HF Indian medicine names** | ~69K normalized names | Check card | ⚠️ Verify | **Fuzzy candidate dictionary only** | Not clinical truth. Never a source of canonical identity |

⚠️ = license and de-identification audit outstanding. These are candidates, not approved.

## Knowledge sources (runtime)

| Source | License | Mode | V1 role | Constraint |
|---|---|---|---|---|
| **RxNorm** | Free, public API, no key | `PUBLIC_DOMAIN` | Optional CUI enrichment | **US-centric — NLM states it contains few if any non-US drugs.** Never the sole identity authority (ADR-07) |
| **openFDA** | Public API, free; optional key raises limit to 120K/day | `PUBLIC_DOMAIN` | `EVIDENCE_LOOKUP`, `ADVERSE_EFFECT` | openFDA's own disclaimer: not for clinical decision-making, results unvalidated. Labeling evidence only. No structured DDI endpoint |
| **SIDER 4.1** | CC BY-NC-SA 4.0 | `RESEARCH_ONLY` | Adverse-effect evidence | **Excluded from commercial builds** (ADR-14). Keyed to STITCH/PubChem IDs — needs a mapping step |
| **CDSCO regulatory lists** | Public Indian government data | Verify | Medication Master seed, `VERIFIED_AUTHORITY` | Format inconsistency across releases; parsing effort underestimated at own risk |
| **DrugBank** | Free academic tier = **non-clinical research/education only** | — | ❌ **Not used at runtime** | Our use case is clinical-decision-support-themed; the academic tier does not clearly cover it. Reference only unless explicitly cleared |
| **MIMIC-IV** | PhysioNet credentialed, CITI training + per-person DUA | — | ❌ **Not a dependency** | Contains no prescription images. Wrong data type. Per-person credentialing × 4 for zero pipeline benefit |
| **MedQuAD** | Public, NIH-sourced | — | ❌ Not used in V1 | Was for LLM grounding; LLM is off (ADR-09) |

## Tier B — the benchmark that actually matters

| | |
|---|---|
| Target | 200–500 prescriptions |
| Status | **Does not exist. This is the project's critical path.** |
| Sourcing | Legally obtained with documented consent; de-identified before ingestion |
| Annotation | Two annotators + adjudication; medication-critical fields signed off by a pharmacist or equivalently qualified reviewer |
| Labels | Two levels — raw transcription, and all 8 structured fields with `CLEAR`/`AMBIGUOUS`/`UNREADABLE`/`NOT_PRESENT` |
| Splits | Same prescription never crosses splits. Near-duplicates don't cross. Handwriting-author separation where achievable. Synthetic variants stay with their source |

`UNREADABLE` is a valid, useful label. A confident wrong guess recorded as ground truth is worse than an honest "couldn't read it" — it silently poisons every metric computed against it.

**Why author-level splitting matters:** random image-level splits on handwriting data put the same handwriting in train and test. Results look strong and collapse under independent evaluation. This is the single easiest way to produce a benchmark that lies.

## Tier C — synthetic

Layout variation, handwriting-style augmentation, blur, rotation, illumination, JPEG compression, camera distortion. Robustness training only. Every eval report states synthetic proportion explicitly.

## Pre-use checklist

- [ ] License read at the primary source, not a summary
- [ ] Commercial vs non-commercial recorded as `license_mode`
- [ ] Redistribution terms checked before any derived artifact is published
- [ ] De-identification verified by inspection, not assumed
- [ ] `knowledge_snapshots` row created with `source_version` + `record_count`
- [ ] Recorded in REFERENCES.md with access date

## Open items

1. RxHandBD, Bangladesh set, HF 69K list — license + de-identification audits outstanding
2. CDSCO reuse terms for a derived Medication Master — **needs legal review**, not an engineering judgment call
3. No legally-obtainable Indian DDI dataset identified. This is why DDI is deferred, and the honest reason the product makes no interaction claim in V1