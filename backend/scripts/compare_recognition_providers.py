"""
Prescripto AI — Synthetic OCR classifier evaluation utility.

Evaluates only local classification of supplied synthetic text lines. It does not
measure Gemini or image-recognition accuracy.
Evaluates:
- Character Error Rate (CER)
- Word Error Rate (WER)
- Field-level extraction accuracy (10 document field types)
- Medication extraction Precision and Recall
- False Medication Entries count (e.g. dates/symptoms/vitals classified as medicines)
- Unsupported Dosing Instructions count (e.g. fabricated frequencies or 'as directed')
- Local classifier execution time (milliseconds)

Usage:
python backend/scripts/compare_recognition_providers.py [--output report.json]
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add backend directory to sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from prescripto.domain.recognition.models import DocumentFieldType, DocumentRecognitionResult
from prescripto.ml.recognition_providers import (
    LocalRapidOCRProvider,
)


@dataclass
class GroundTruthItem:
    text: str
    field_type: DocumentFieldType
    is_medication: bool
    expected_dose: Optional[str] = None
    expected_freq: Optional[str] = None


@dataclass
class SyntheticBenchmarkSample:
    sample_id: str
    title: str
    ground_truth_items: List[GroundTruthItem]
    simulated_ocr_raw_lines: List[str]


@dataclass
class ProviderEvaluationMetrics:
    provider_name: str
    sample_count: int = 0
    total_latency_ms: float = 0.0
    estimated_cost_usd: float = 0.0
    cer: float = 0.0
    wer: float = 0.0
    field_accuracy: float = 0.0
    medication_precision: float = 0.0
    medication_recall: float = 0.0
    false_medication_count: int = 0
    unsupported_dosing_count: int = 0
    raw_details: List[Dict[str, Any]] = field(default_factory=list)


def calculate_levenshtein_distance(s1: str, s2: str) -> int:
    """Standard dynamic programming Levenshtein distance."""
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,      # deletion
                dp[i][j - 1] + 1,      # insertion
                dp[i - 1][j - 1] + cost  # substitution
            )
    return dp[m][n]


def compute_cer(reference: str, hypothesis: str) -> float:
    """Character Error Rate: edit_distance(ref, hyp) / len(ref)."""
    ref = reference.strip()
    hyp = hypothesis.strip()
    if not ref:
        return 0.0 if not hyp else 1.0
    dist = calculate_levenshtein_distance(ref, hyp)
    return float(dist) / float(len(ref))


def compute_wer(reference: str, hypothesis: str) -> float:
    """Word Error Rate using token-level edit distance."""
    ref_words = reference.strip().split()
    hyp_words = hypothesis.strip().split()
    if not ref_words:
        return 0.0 if not hyp_words else 1.0
    m, n = len(ref_words), len(hyp_words)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if ref_words[i - 1].lower() == hyp_words[j - 1].lower() else 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)
    return float(dp[m][n]) / float(len(ref_words))


def get_standard_synthetic_benchmark() -> List[SyntheticBenchmarkSample]:
    """
    Synthetic text benchmark representing common clinical document categories:
    - Case 1: Complex handwritten prescription with symptoms, vitals, IV fluids, advice, dates.
    - Case 2: Outpatient prescription with hospital header, printed items, handwritten notes.
    """
    sample1 = SyntheticBenchmarkSample(
        sample_id="SYNTH-001",
        title="Synthetic handwritten emergency note example",
        ground_truth_items=[
            GroundTruthItem("Apex Hospital & Emergency Care", DocumentFieldType.HOSPITAL_DETAILS, False),
            GroundTruthItem("Date: 22/11/2022", DocumentFieldType.DATE, False),
            GroundTruthItem("Pt: Ramesh Kumar 52M", DocumentFieldType.PATIENT_DETAILS, False),
            GroundTruthItem("giddiness, restlessness", DocumentFieldType.SYMPTOMS_COMPLAINTS, False),
            GroundTruthItem("BP – 110/70", DocumentFieldType.VITAL_SIGNS, False),
            GroundTruthItem("Acute Dehydration", DocumentFieldType.DIAGNOSIS, False),
            GroundTruthItem("10% Dextrose (IV) stat.", DocumentFieldType.NON_MEDICATION_TREATMENT, False),
            GroundTruthItem("Tab Paracetamol 650mg SOS", DocumentFieldType.MEDICATION_ORDER, True, expected_dose="650mg", expected_freq="SOS"),
            GroundTruthItem("ORS 2 sachets in 1L water", DocumentFieldType.NON_MEDICATION_TREATMENT, False),
            GroundTruthItem("Adequate fluid intake", DocumentFieldType.GENERAL_ADVICE, False),
        ],
        simulated_ocr_raw_lines=[
            "Apex Hosp Care",
            "22112122",
            "Pt Ramesh 52M",
            "yuddbeu, yeublesny",
            "07011",
            "Acute Dehydr",
            "10% Dextrose",
            "Tab Paracetamol 650mg SOS",
            "RS2zache",
            "Adeauae Pluidtnbake",
        ],
    )

    sample2 = SyntheticBenchmarkSample(
        sample_id="SYNTH-002",
        title="Outpatient Cardiology Prescription",
        ground_truth_items=[
            GroundTruthItem("City Heart Care Clinic", DocumentFieldType.HOSPITAL_DETAILS, False),
            GroundTruthItem("2026-10-15", DocumentFieldType.DATE, False),
            GroundTruthItem("Mr. S. Rao, 61 Y / Male", DocumentFieldType.PATIENT_DETAILS, False),
            GroundTruthItem("Complaints: Chest heaviness on exertion", DocumentFieldType.SYMPTOMS_COMPLAINTS, False),
            GroundTruthItem("Pulse 78/min, BP 130/84 mmHg", DocumentFieldType.VITAL_SIGNS, False),
            GroundTruthItem("Hypertension Stage 1", DocumentFieldType.DIAGNOSIS, False),
            GroundTruthItem("Tab Telmisartan 40mg once daily in morning", DocumentFieldType.MEDICATION_ORDER, True, expected_dose="40mg", expected_freq="once daily"),
            GroundTruthItem("Tab Atorvastatin 10mg at bedtime", DocumentFieldType.MEDICATION_ORDER, True, expected_dose="10mg", expected_freq="at bedtime"),
            GroundTruthItem("Low salt diet and 30 min daily walking", DocumentFieldType.GENERAL_ADVICE, False),
        ],
        simulated_ocr_raw_lines=[
            "City Heart Care Clinic",
            "2026-10-15",
            "Mr S Rao 61 Y Male",
            "Chest heaviness on exertion",
            "Pulse 78 BP 130/84",
            "Hypertension",
            "Tab Telmisartan 40mg once daily morning",
            "Tab Atorvastatin 10mg bedtime",
            "Low salt diet and walking",
        ],
    )

    return [sample1, sample2]


def evaluate_recognition_output(
    sample: SyntheticBenchmarkSample,
    recognition_result: DocumentRecognitionResult,
    provider_name: str,
    latency_ms: float,
    estimated_cost: float,
) -> Dict[str, Any]:
    """Evaluates a DocumentRecognitionResult against GroundTruth."""
    gt_items = sample.ground_truth_items
    rec_items = recognition_result.items

    # 1. Full text concatenation CER & WER
    ref_full_text = " ".join([gt.text for gt in gt_items])
    hyp_full_text = " ".join([rec.interpreted_text or rec.original_text for rec in rec_items])
    sample_cer = compute_cer(ref_full_text, hyp_full_text)
    sample_wer = compute_wer(ref_full_text, hyp_full_text)

    # 2. Field classification accuracy
    matched_field_count = 0
    for gt in gt_items:
        # Find closest match in recognized items
        best_match = None
        best_dist = 999
        for rec in rec_items:
            dist = calculate_levenshtein_distance(gt.text.lower(), rec.original_text.lower())
            if dist < best_dist:
                best_dist = dist
                best_match = rec
        if best_match and best_match.field_type == gt.field_type:
            matched_field_count += 1
    field_acc = matched_field_count / max(len(gt_items), 1)

    # 3. Medication precision and recall
    gt_medications = [gt for gt in gt_items if gt.is_medication]
    rec_medications = [rec for rec in rec_items if rec.field_type == DocumentFieldType.MEDICATION_ORDER]

    true_positives = 0
    false_positives = 0
    for rec_m in rec_medications:
        # Check if matches any GT medication
        match_found = any(
            gt.is_medication and (gt.text.lower() in rec_m.original_text.lower() or rec_m.original_text.lower() in gt.text.lower() or calculate_levenshtein_distance(gt.text.lower(), rec_m.original_text.lower()) < 8)
            for gt in gt_items
        )
        if match_found:
            true_positives += 1
        else:
            false_positives += 1

    false_negatives = max(0, len(gt_medications) - true_positives)
    precision = true_positives / max((true_positives + false_positives), 1)
    recall = true_positives / max((true_positives + false_negatives), 1)

    # 4. Count of False Medication Entries
    # (Non-medication ground truth items that were classified as MEDICATION_ORDER)
    false_medication_count = 0
    for rec in rec_items:
        if rec.field_type == DocumentFieldType.MEDICATION_ORDER:
            # Check if this maps to a non-medication GT item
            for gt in gt_items:
                if not gt.is_medication and (
                    gt.text.lower() in rec.original_text.lower() or
                    rec.original_text.lower() in gt.text.lower() or
                    calculate_levenshtein_distance(gt.text.lower(), rec.original_text.lower()) < 8
                ):
                    false_medication_count += 1
                    break

    # 5. Unsupported Dosing Instructions count
    unsupported_dosing_count = 0
    for rec in rec_items:
        if rec.field_type == DocumentFieldType.MEDICATION_ORDER:
            lower_text = (rec.interpreted_text or rec.original_text).lower()
            if "as directed" in lower_text:
                # Check if ground truth specifically had "as directed"
                if not any("as directed" in gt.text.lower() for gt in gt_items):
                    unsupported_dosing_count += 1

    return {
        "sample_id": sample.sample_id,
        "sample_title": sample.title,
        "provider": provider_name,
        "latency_ms": latency_ms,
        "estimated_cost_usd": estimated_cost,
        "cer": round(sample_cer, 4),
        "wer": round(sample_wer, 4),
        "field_accuracy": round(field_acc, 4),
        "medication_precision": round(precision, 4),
        "medication_recall": round(recall, 4),
        "false_medication_count": false_medication_count,
        "unsupported_dosing_count": unsupported_dosing_count,
        "recognized_item_count": len(rec_items),
        "medication_item_count": len(rec_medications),
    }


def run_benchmark_comparison() -> Dict[str, Any]:
    """Runs the synthetic text-only classifier benchmark."""
    samples = get_standard_synthetic_benchmark()
    local_provider = LocalRapidOCRProvider()
    all_results = []

    for sample in samples:
        start_t = time.perf_counter()
        local_items = [
            local_provider.classify_text_line(line)
            for line in sample.simulated_ocr_raw_lines
        ]
        local_result = DocumentRecognitionResult(
            provider_used="rapidocr",
            items=local_items,
        )
        local_latency = (time.perf_counter() - start_t) * 1000.0
        all_results.append(evaluate_recognition_output(
            sample=sample,
            recognition_result=local_result,
            provider_name="Local classifier (synthetic text only)",
            latency_ms=local_latency,
            estimated_cost=0.0,
        ))

    return {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sample_count": len(samples),
        "benchmark_scope": "Synthetic OCR text classification only; no image or Gemini accuracy measurement.",
        "detailed_results": all_results,
    }

def print_comparison_table(report: Dict[str, Any]) -> None:
    """Prints synthetic classifier metrics without implying model accuracy."""
    print("\n" + "=" * 90)
    print("PRESCRIPTO AI — SYNTHETIC TEXT CLASSIFIER CHECK")
    print("=" * 90)
    print(f"Evaluated Samples: {report['sample_count']}")
    print(report["benchmark_scope"])
    print("-" * 90)
    print(
        f"{'Provider':<28} | {'CER':<6} | {'WER':<6} | {'Field Acc':<9} | {'Med Prec':<8} | {'Med Rec':<7} | {'False Meds':<10} | {'Latency':<8} | {'Cost/Req'}"
    )
    print("-" * 90)

    for res in report["detailed_results"]:
        prov = f"{res['provider']} ({res['sample_id']})"
        cer = f"{res['cer']:.2%}"
        wer = f"{res['wer']:.2%}"
        facc = f"{res['field_accuracy']:.2%}"
        prec = f"{res['medication_precision']:.2%}"
        rec = f"{res['medication_recall']:.2%}"
        fmed = f"{res['false_medication_count']}"
        lat = f"{res['latency_ms']:.0f}ms"
        cost = f"${res['estimated_cost_usd']:.4f}"
        print(
            f"{prov:<28} | {cer:<6} | {wer:<6} | {facc:<9} | {prec:<8} | {rec:<7} | {fmed:<10} | {lat:<8} | {cost}"
        )

    print("=" * 90)
    print("These figures describe only the hard-coded synthetic text examples, not recognition accuracy.")
    print("=" * 90 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the synthetic local OCR text classifier.")
    parser.add_argument("--output", type=str, default="", help="Path to write JSON benchmark report")
    args = parser.parse_args()

    report = run_benchmark_comparison()
    print_comparison_table(report)

    if args.output:
        out_p = Path(args.output)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"Benchmark results saved to {out_p.resolve()}")


if __name__ == "__main__":
    main()
