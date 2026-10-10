# RESEARCH PROTOCOL SPECIFICATION (PRE-REGISTRATION)
## Prescripto AI 2.0: Evaluating Conventional OCR Metrics vs. Medication-Critical Transcription Correctness

- **Document Version:** 1.0.0 (FROZEN PRE-REGISTRATION)
- **Protocol Status:** LOCKED & PRE-REGISTERED (Prior to Dataset Finalization and Experimentation)
- **Primary Domain:** Machine Perception & Healthcare Informatics (Medical Document Transcription)
- **Scope Boundary:** Machine-transcription correctness of handwritten prescription medication fields. This protocol evaluates transcription fidelity that could alter medication meaning; it explicitly does **not** evaluate clinical appropriateness, diagnostic correctness, or pharmacological prescribing justification.

---

## 1. Research Questions & Hypotheses

### 1.1 Primary Research Question ($RQ_1$)
> **Does standard character error rate (CER) and word error rate (WER) adequately capture medication-critical errors in handwritten prescription OCR?**

- **Hypothesis $H_1$:** Standard string-edit distance metrics (CER / WER) do not adequately represent medication-critical transcription correctness in handwritten prescriptions.
- **Falsifiable Outcomes:**
  - **Result A (Supports $H_1$):** Weak or discordant correlation between CER/WER and Medication-Critical Error Rate (MCER) (e.g., low CER cases with catastrophic 10× dosage shifts or high CER cases driven by non-critical cosmetic characters; Spearman $\rho < 0.60$ or high discordance rate $> 15\%$).
  - **Result B (Falsifies / Does Not Support $H_1$):** Strong, uniform monotonic correlation between CER/WER and critical error occurrence ($\rho \ge 0.85$, near-zero discordance), indicating conventional OCR metrics are sufficient surrogates for critical safety.
  - **Result C (Nuanced Evidence):** Overall correlation exists for general text, but systematically breaks down for specific high-risk numerical/acronym error classes (e.g., dosage numbers, frequency codes, units).

### 1.2 Secondary Research Question ($RQ_2$)
> **Under matched review-workload budgets, does a medication-aware uncertainty review allocation policy detect significantly more critical transcription errors than a conventional generic confidence threshold policy?**

- **Hypothesis $H_2$:** At equal human verification budget (matched percentage of lines routed to human review), uncertainty allocation conditioned on field criticality (dosage, drug name, frequency) achieves higher sensitivity to medication-critical errors than uniform model-confidence thresholding.
- **Falsifiable Outcomes:**
  - **Supports $H_2$:** Medication-aware review policy captures statistically significantly higher proportion of critical errors ($\Delta \text{Sensitivity} > 0$, $p < 0.05$) across fixed review budget fractions (e.g., 5%, 10%, 20%, 30%).
  - **Falsifies $H_2$:** Generic confidence ranking yields equivalent or superior critical error capture under identical review budgets.

---

## 2. Evaluation Boundary & Critical Fields

The evaluation boundary is strictly limited to transcription fidelity of recognized prescription text against expert-adjudicated ground truth.

```
Uploaded Image
      ↓
OCR Model (Perception)
      ↓
Recognized Text Spans
      ↓
[EVALUATION BOUNDARY]
  1. Drug Identity (Brand / Generic name)
  2. Strength (Concentration, e.g., 500 mg, 625 mg)
  3. Dose (Quantity, e.g., 1 tablet, 2 puffs)
  4. Unit (Dosage form, e.g., tab, cap, ml, mg)
  5. Frequency (Administration schedule, e.g., BD, TDS, QDS, PRN, once daily)
  6. Route (Administration pathway, e.g., Oral, IV, Topical, Inhalation)
  7. Duration (Treatment period, e.g., 5 days, 2 weeks)
```

---

## 3. Medication-Critical Error Taxonomy

Transcription errors are mapped into a standardized, discrete severity taxonomy:

| Class | Category | Severity | Definition & Clinical Risk Mechanism | Example Reference $\rightarrow$ Hypothesis |
|---|---|---|---|---|
| **C1** | **Dosage Magnitude Shift** | **CRITICAL** | Change in numerical multiplier $\ge 2\times$, decimal point omission/insertion, or magnitude order shift. | Ref: `0.5 mg` $\rightarrow$ Hyp: `5 mg` (10× overdose); Ref: `50 mg` $\rightarrow$ Hyp: `500 mg` |
| **C2** | **Look-Alike / Sound-Alike (LASA) Drug Substitution** | **CRITICAL** | Transcription error converting target drug name into a different valid drug entity or unrecognizable entity. | Ref: `Celebrex` $\rightarrow$ Hyp: `Celexa`; Ref: `Prednisone` $\rightarrow$ Hyp: `Prednisolone` |
| **C3** | **Frequency / Schedule Distortion** | **CRITICAL** | Alteration of dosage intervals or timing abbreviations that changes cumulative daily dose. | Ref: `OD` (once daily) $\rightarrow$ Hyp: `QDS` (four times daily); Ref: `PRN` $\rightarrow$ Hyp: `BD` |
| **C4** | **Unit of Measure Confusion** | **CRITICAL** | Substitution or omission of units altering administered drug mass or volume. | Ref: `5.0 mg` $\rightarrow$ Hyp: `5.0 ml` or `5.0 g` |
| **C5** | **Route Inversion** | **CRITICAL** | Misrecognition of administration pathway altering bioavailability or toxicity. | Ref: `Topical` $\rightarrow$ Hyp: `Oral`; Ref: `IV` $\rightarrow$ Hyp: `IM` |
| **NC1** | **Minor Cosmetic Typo** | **NON-CRITICAL** | Typographical error in brand suffix or non-critical word not altering active entity or dose. | Ref: `Augmentin-Duo` $\rightarrow$ Hyp: `Augmentin Duo` (punctuation missing) |
| **NC2** | **Incidental / Instruction Spelling** | **NON-CRITICAL** | Misspelling in ancillary instructions (food intake, casing, spacing) without clinical shift. | Ref: `after food` $\rightarrow$ Hyp: `after food.` or `After Food` |
| **NC3** | **Whitespace / Layout Variations** | **NON-CRITICAL** | Extra spaces, line breaks, or punctuation that do not alter token semantic boundaries. | Ref: `1 tab BD` $\rightarrow$ Hyp: `1  tab  BD` |

---

## 4. Primary & Secondary Endpoints

### 4.1 Conventional String-Level Metrics
1. **Character Error Rate (CER):**
   $$\text{CER} = \frac{S_c + D_c + I_c}{N_c} = \frac{\text{LevenshteinDistance}(R_c, H_c)}{|R_c|}$$
   Computed strictly where $N_c$ is reference character length (standard formulation; not divided by $\max(|R|, |H|)$).
2. **Word Error Rate (WER):**
   $$\text{WER} = \frac{S_w + D_w + I_w}{N_w}$$
   Computed across whitespace-delimited tokens against reference length $N_w$.
3. **Exact Line Match Rate (ELMR):** Binary match indicator per line ($\mathbb{I}[R = H]$).

### 4.2 Medication-Critical Metrics
1. **Medication-Critical Error Rate (MCER):**
   $$\text{MCER} = \frac{\text{Total Critical Errors } (C1 + C2 + C3 + C4 + C5)}{\text{Total Evaluated Prescription Lines}}$$
2. **Critical Field Error Rate (CFER) per Field:**
   $$\text{CFER}_f = \frac{\sum_{i=1}^M \mathbb{I}[\text{Field } f \text{ has Critical Error in Line } i]}{M_f}$$
   Reported independently for Identity, Strength, Dose, Unit, Frequency, Route, Duration.
3. **Metric Discordance Index (MDI):**
   Fraction of lines where conventional metric indicates near-perfect transcription ($\text{CER} \le 5\%$) but $\ge 1$ critical error ($C1\text{--}C5$) is present, and vice-versa ($\text{CER} > 20\%$ but zero critical errors).

### 4.3 Review Routing Endpoints (for $H_2$)
1. **Critical Error Recall at Budget $B$ ($\text{Rec}_C@B$):** Proportion of all critical errors in the test cohort contained in the top $B\%$ highest-uncertainty lines routed for human review.
2. **Relative Risk Reduction ($\text{RRR}@B$):** Unreviewed critical error rate under policy vs. random or generic confidence baseline.

---

## 5. Dataset Architecture & Writer-Disjoint Partitioning Strategy

### 5.1 Cohort Architecture
- **Target Size:** 200–500 unique prescription images.
- **Unit of Independence:** **Writer / Prescriber Key** (Pseudonymous identifier).
- **Rule:** Prescriptions from the same writer/clinic must NEVER cross dataset splits. Lines from the same prescription or doctor are strictly clustered.

### 5.2 Three-Way Partitioning
1. **Development Set (60%):** Model hyperparameter exploration, temperature scaling calibration fitting, span parsing heuristics.
2. **Validation / Tuning Set (20%):** Review threshold tuning, calibration parameter validation.
3. **Independent Lockbox Evaluation Set (20%):** **Strictly frozen**. Evaluated exactly once. No tuning, threshold modification, or re-fitting permitted after opening the lockbox.

---

## 6. Ground Truth & Annotation Protocol

1. **De-identification:** All Direct Patient Identifiers (Names, Phone Numbers, Aadhaar/SSN, Addresses) redacted prior to research entry.
2. **Double-Blind Annotation:** Two independent annotators transcribe each sample using standardized JSON schemas.
3. **Adjudication:** Discrepancies between Annotator 1 and Annotator 2 resolved by a qualified pharmacist/physician domain expert.
4. **Structured Schema:**
   ```json
   {
     "sample_id": "RX-2026-001",
     "writer_id": "WRITER-A-04",
     "line_index": 0,
     "raw_text": "Augmentin 625 Duo 1 tab BD 5 days",
     "fields": {
       "identity": "Augmentin 625 Duo",
       "strength": "625 mg",
       "dose": "1",
       "unit": "tablet",
       "frequency": "BD",
       "route": "oral",
       "duration": "5 days"
     },
     "adjudicated_canonical_id": "AMOX-CLAV-625",
     "critical_annotation_flags": []
   }
   ```

---

## 7. Baseline Systems Under Evaluation

All systems evaluated on identical image crops and ground-truth pairings:
1. **PP-OCRv6 Baseline:** Lightweight mobile/edge architecture (active deployment model in `ml/app`).
2. **TrOCR (Handwritten Base):** Transformer-based encoder-decoder vision-to-text sequence model.
3. **Calibrated Variant:** Model outputs rescaled via post-hoc Temperature Scaling on the Development split.

---

## 8. Statistical Analysis Plan (SAP)

1. **Clustered Bootstrap Resampling:** 95% Confidence Intervals calculated by cluster-bootstrap resampling at the **Writer level** (1,000 iterations), accounting for within-writer handwriting correlation.
2. **Correlation Analysis:**
   - Spearman rank correlation ($\rho$) and Kendall rank correlation ($\tau$) between sample CER and sample Critical Error Count.
   - Stratified analysis by field type (numerical dose vs. alphabetical drug name).
3. **Hypothesis Testing for $H_2$:**
   - Paired McNemar's test and bootstrap difference of proportions for $\text{Rec}_C@B$ across matched budgets ($B \in \{5\%, 10\%, 20\%, 30\%\}$).
   - Significance threshold: $\alpha = 0.05$ (two-tailed).

---

## 9. Protocol Lock & Governance Statement

This document represents the immutable pre-registration of the Prescripto AI 2.0 evaluation protocol.
Any post-hoc modifications to metrics, taxonomy, thresholds, or splits must be reported transparently as *exploratory post-hoc analyses*, distinct from this *pre-registered confirmatory protocol*.
