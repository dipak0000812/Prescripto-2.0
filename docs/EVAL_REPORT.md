# Prescripto AI 2.0 — Evaluation Report

Generated at: 2026-10-30 12:15:29 UTC

## 1. Executive Summary: Gemini vs RapidOCR Comparison

| Metric | Google Gemini | Local RapidOCR |
| :--- | :--- | :--- |
| **Evaluated Images** | 10 | 10 |
| **Total Expected Medicines** | 29 | 29 |
| **Exact Name Match Rate** | **100.0%** (29/29) | 51.7% (15/29) |
| **Fuzzy Name Match Rate** | **100.0%** (29/29) | 75.9% (22/29) |
| **Strength Accuracy** | **100.0%** (29/29) | 72.4% (21/29) |
| **Frequency Accuracy** | **100.0%** (29/29) | 58.6% (17/29) |
| **Duration Accuracy** | **100.0%** (29/29) | 75.9% (22/29) |
| **Medicines Missed** | **0** | 7 |
| **Hallucinated Medicines** | **0** | 1 |
| **Uncertain/Degraded Items Flagged** | 0 | 33 |
| **Average Latency** | 8.93s | **1.99s** |
| **Fallbacks Occurred** | 8 | 0 |

## 2. Real vs Synthetic Breakdown

### Provider: `gemini`

| Subset | Images | GT Meds | Exact Match | Fuzzy Match | Strength Acc | Missed | Hallucinated | Avg Latency |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Real Images | 0 | 0 | 0.0% | 0.0% | 0.0% | 0 | 0 | 0.00s |
| Synthetic Images | 10 | 29 | 100.0% | 100.0% | 100.0% | 0 | 0 | 8.93s |

### Provider: `rapidocr`

| Subset | Images | GT Meds | Exact Match | Fuzzy Match | Strength Acc | Missed | Hallucinated | Avg Latency |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Real Images | 0 | 0 | 0.0% | 0.0% | 0.0% | 0 | 0 | 0.00s |
| Synthetic Images | 10 | 29 | 51.7% | 75.9% | 72.4% | 7 | 1 | 1.99s |

## 3. Worst 3 Failures (Expected vs Extracted)

### Failure #1: `synthetic_02_blur.png` (Provider: `rapidocr`)

- **Model/Engine Used**: `rapidocr`
- **Missed**: 3 | **Hallucinated**: 0 | **Latency**: 0.39s

**Expected Medications (Ground Truth):**

| Drug Name | Strength | Frequency | Duration |
| :--- | :--- | :--- | :--- |
| Azithromycin | 500mg | once daily | 3 days |
| Pantoprazole | 40mg | once daily | 14 days |
| Levocetirizine | 5mg | at bedtime | 5 days |

**Extracted Medications:**

*No medications extracted.*

---

### Failure #2: `synthetic_08_pediatric_blur.png` (Provider: `rapidocr`)

- **Model/Engine Used**: `rapidocr`
- **Missed**: 2 | **Hallucinated**: 0 | **Latency**: 0.34s

**Expected Medications (Ground Truth):**

| Drug Name | Strength | Frequency | Duration |
| :--- | :--- | :--- | :--- |
| Augmentin | 375mg | three times daily | 5 days |
| Paracetamol | 250mg | as needed for fever | 3 days |

**Extracted Medications:**

*No medications extracted.*

---

### Failure #3: `synthetic_03_rot_pos.png` (Provider: `rapidocr`)

- **Model/Engine Used**: `rapidocr`
- **Missed**: 1 | **Hallucinated**: 1 | **Latency**: 2.24s

**Expected Medications (Ground Truth):**

| Drug Name | Strength | Frequency | Duration |
| :--- | :--- | :--- | :--- |
| Metformin | 500mg | twice daily | 30 days |
| Glimepiride | 1mg | once daily | 30 days |
| Atorvastatin | 20mg | once daily at night | 30 days |

**Extracted Medications:**

| Extracted Name | Strength | Frequency | Duration | Raw Text |
| :--- | :--- | :--- | :--- | :--- |
| Mefomin | 500mg |  |  | `1. Mefomin 500mg tablet- 1 tab twice dailywith meals bor30 days` |
| Glimepitide mg tablet1 tabonce dailybefore breakfast for30 days |  |  |  | `2.Glimepitide mg tablet1 tabonce dailybefore breakfast for30 days` |
| Atorvastatin | 20mg |  | for 30 days | `3. Atorvastatin 20mg tablet- 1 tabonce dailyat night for 30 days` |

---
