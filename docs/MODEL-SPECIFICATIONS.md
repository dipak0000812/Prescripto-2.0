# MODEL-SPECIFICATIONS.md

Per-model specs for every candidate. **No model is selected.** Selection is decided by Tier B benchmark (EVALUATION-PLAN.md), not by this document.

## Registry contract

Every model in production has a `model_versions` row and a linked `calibration_snapshots` row. Worker startup refuses to boot if either is missing, or if the artifact's SHA-256 doesn't match `checkpoint_sha256`. There is no "load whatever's on disk" path.

## Candidates

### PP-OCRv6 (detection) — `ppocr_det`
| | |
|---|---|
| Role | Text detection. **Locked** — no competing candidate |
| License | Apache 2.0 (verified) |
| Size | tiny 1.5M / small 7.7M / medium 34.5M, LCNetV4 backbone |
| Reported | 86.2% detection Hmean, medium tier, PaddleOCR in-house 15/16-category benchmark (arXiv 2606.13108) |
| Input | Full corrected page |
| Output | Rotated bounding boxes |
| Why locked | Detection is less accuracy-critical than recognition — a slightly loose box still crops the line. No measurable benefit to benchmarking alternatives against project time |

### PP-OCRv6 (recognition) — `ppocr_rec`
| | |
|---|---|
| Role | Recognition **baseline / floor**, and the printed-text path |
| License | Apache 2.0 |
| Reported | 83.2% weighted-avg recognition (medium tier, same benchmark). Handwritten-English substantially weaker than printed-English — the gap is large and consistent across tiers |
| Runs on | CPU acceptably |
| Verification note | The specific handwritten/printed English split figures quoted in earlier drafts (67.8% / 94.1%) are **UNVERIFIED** at medium tier — only the tiny-tier row was confirmable. Do not cite those two numbers in any report until pulled directly from Table 6 |
| Role in selection | This is the number everything else must beat on handwriting to justify its cost. Not a favorite — a floor |

### TrOCR base handwritten — `trocr_base`
| | |
|---|---|
| License | MIT (verified) |
| Pretrained on | IAM handwriting — English cursive, not prescriptions |
| Input | **Single text line only.** Full-page input is a defect |
| Confidence | Beam-search score — not comparable to CTC scores; calibration mandatory |
| Expected | 200–800 ms/line CPU (unmeasured — Colab pilot required) |

### TrOCR large handwritten — `trocr_large`
Same contract as base. Higher expected accuracy, materially higher latency and memory. **Free-tier feasibility is unverified** — must survive a Colab T4 session-limit pilot before it's a real candidate.

### Prescription-fine-tuned TrOCR — `trocr_rx`
| | |
|---|---|
| License | **Verify per model card — unconfirmed** |
| Claimed | Sub-2% CER on the author's own test set |
| Status | Model-card number on the author's data, not ours. Treated as a candidate like any other; the claim is a reason to test it, not to trust it |

### VLM verifier — `vlm` (DEFERRED)
| | |
|---|---|
| Candidates | PaddleOCR-VL-1.6 (0.9B), Qwen2.5-VL |
| License | **Qwen licensing varies by checkpoint** — some Apache 2.0, some Qwen Research License. Never write "Qwen is Apache 2.0" as a blanket claim. Verify the exact repo, every time |
| Status | D-04. Stage not in V1 pipeline |
| Concern | PP-OCRv6's own hallucination benchmark shows specialized OCR stays better grounded to the image than large VLMs. A hallucinated drug name is a safety incident, not a UX blemish |

### BioBERT / Bio_ClinicalBERT (DEFERRED)
| | |
|---|---|
| License | Apache 2.0 / open weights. Bio_ClinicalBERT weights are openly published despite MIMIC-III training — weights ≠ data access |
| Status | D-05. Ablation only, and not before OCR selection settles — no point tuning a downstream stage against a moving upstream |

### LLM (DISABLED IN V1)
`LLM_ENABLED = false`. ADR-09. No provider selected. Re-enabling requires a signed DPA and a passed prompt-injection benchmark.

## Calibration spec

Applies to every recognition model before promotion:

1. Collect `(raw_score, correct?)` pairs on the Tier B **validation** split — never test.
2. Fit isotonic regression by default. Platt scaling only if validation bins are too sparse for isotonic to be stable — **check bin counts first**; a 200–500 document Tier B set can easily be too thin for isotonic per-field.
3. Persist curve + `review_threshold` as a `calibration_snapshots` row against that exact `model_version_id`.
4. Re-fit on every checkpoint change. Calibration does not transfer across versions, including minor bumps.

## Promotion gate

- `calibration_snapshots` row exists (startup-enforced)
- Tier B report covers all three metric layers with 95% CIs
- Critical identity/dose/unit/frequency error rates not worse than incumbent, within CI overlap

"Better CER" alone is not a promotion reason. CER improvements that don't move critical-error rates are noise for this product.

## Hardware reality check

Free-tier only (Colab/Kaggle/HF). Before committing to any fine-tuning plan, run a **week-1 pilot**: time a small TrOCR fine-tune against Colab's session limits. If a full fine-tune doesn't fit inside a session, the plan is zero-shot benchmarking of pretrained checkpoints plus rule-based post-correction — decided by measurement, not optimism.