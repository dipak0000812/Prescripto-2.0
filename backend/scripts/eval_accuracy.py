"""
Accuracy Evaluation Script for Prescripto 2.0.
Evaluates recognition providers (Gemini Vision vs Local RapidOCR) against an evaluation dataset.
Compares extracted entities to ground truth, reports detailed per-image and aggregate metrics,
and writes docs/EVAL_REPORT.md.
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# Ensure project root and backend are on PYTHONPATH
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
PROJECT_ROOT = os.path.abspath(os.path.join(BACKEND_DIR, ".."))
for p in [BACKEND_DIR, PROJECT_ROOT]:
    if p not in sys.path:
        sys.path.insert(0, p)

from prescripto.config.settings import settings
from prescripto.ml.recognition_providers import (
    GeminiVisionProvider,
    LocalRapidOCRProvider,
    DocumentRecognitionResult,
)


def normalize_text(text: Optional[str]) -> str:
    if not text:
        return ""
    cleaned = text.lower().strip()
    cleaned = re.sub(r"[^\w\s\.]", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def fuzzy_match_ratio(a: str, b: str) -> float:
    na = normalize_text(a)
    nb = normalize_text(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    if na in nb or nb in na:
        return 0.95
    return difflib.SequenceMatcher(None, na, nb).ratio()


def attribute_matches(expected: Optional[str], extracted: Optional[str]) -> bool:
    if not expected:
        return True
    if not extracted:
        return False
    ne = normalize_text(expected)
    nx = normalize_text(extracted)
    if ne == nx or ne in nx or nx in ne:
        return True
    tokens_e = set(ne.split())
    tokens_x = set(nx.split())
    if tokens_e.issubset(tokens_x) or tokens_x.issubset(tokens_e):
        return True
    return difflib.SequenceMatcher(None, ne, nx).ratio() >= 0.75


@dataclass
class EvalImageResult:
    image_name: str
    is_synthetic: bool
    provider_name: str
    provider_used: str
    model_used: Optional[str]
    fallback_occurred: bool
    fallback_reason: Optional[str]
    latency_sec: float
    ground_truth_meds: List[Dict[str, Any]]
    extracted_meds: List[Dict[str, Any]]
    exact_name_matches: int = 0
    fuzzy_name_matches: int = 0
    strength_correct: int = 0
    frequency_correct: int = 0
    duration_correct: int = 0
    medicines_missed: int = 0
    medicines_hallucinated: int = 0
    uncertain_items_count: int = 0
    unmatched_expected: List[Dict[str, Any]] = field(default_factory=list)
    unmatched_extracted: List[Dict[str, Any]] = field(default_factory=list)
    matched_pairs: List[Tuple[Dict[str, Any], Dict[str, Any]]] = field(default_factory=list)


def evaluate_image(
    image_name: str,
    is_synthetic: bool,
    provider_name: str,
    rec_result: DocumentRecognitionResult,
    gt_meds: List[Dict[str, Any]],
    latency: float,
) -> EvalImageResult:
    ext_meds: List[Dict[str, Any]] = []
    for m in rec_result.medications:
        ext_meds.append({
            "name": m.name or "",
            "strength": m.strength or "",
            "frequency": m.frequency or "",
            "duration": m.duration or "",
            "original_text": m.original_text or "",
        })

    eval_res = EvalImageResult(
        image_name=image_name,
        is_synthetic=is_synthetic,
        provider_name=provider_name,
        provider_used=getattr(rec_result, "provider_used", provider_name),
        model_used=getattr(rec_result, "model_used", None),
        fallback_occurred=getattr(rec_result, "fallback_occurred", False),
        fallback_reason=getattr(rec_result, "fallback_reason", None),
        latency_sec=latency,
        ground_truth_meds=gt_meds,
        extracted_meds=ext_meds,
        uncertain_items_count=len(rec_result.uncertain_items),
    )

    remaining_ext = list(ext_meds)
    matched_pairs: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []

    for expected in gt_meds:
        best_match = None
        best_score = 0.0
        best_idx = -1

        for idx, candidate in enumerate(remaining_ext):
            score = fuzzy_match_ratio(expected.get("name", ""), candidate.get("name", ""))
            # Also check if drug name is inside original text
            if expected.get("name", "").lower() in candidate.get("original_text", "").lower():
                score = max(score, 0.9)
            if score > best_score and score >= 0.6:
                best_score = score
                best_match = candidate
                best_idx = idx

        if best_match is not None:
            matched_pairs.append((expected, best_match))
            remaining_ext.pop(best_idx)

            # Exact name match
            if normalize_text(expected.get("name")) == normalize_text(best_match.get("name")):
                eval_res.exact_name_matches += 1
                eval_res.fuzzy_name_matches += 1
            else:
                eval_res.fuzzy_name_matches += 1

            # Strength check
            if attribute_matches(expected.get("strength"), best_match.get("strength") or best_match.get("original_text")):
                eval_res.strength_correct += 1

            # Frequency check
            if attribute_matches(expected.get("frequency"), best_match.get("frequency") or best_match.get("original_text")):
                eval_res.frequency_correct += 1

            # Duration check
            if attribute_matches(expected.get("duration"), best_match.get("duration") or best_match.get("original_text")):
                eval_res.duration_correct += 1
        else:
            eval_res.unmatched_expected.append(expected)

    eval_res.medicines_missed = len(eval_res.unmatched_expected)
    eval_res.medicines_hallucinated = len(remaining_ext)
    eval_res.unmatched_extracted = remaining_ext
    eval_res.matched_pairs = matched_pairs
    return eval_res


@dataclass
class AggregateMetrics:
    total_images: int = 0
    total_gt_meds: int = 0
    total_ext_meds: int = 0
    exact_name_matches: int = 0
    fuzzy_name_matches: int = 0
    strength_correct: int = 0
    frequency_correct: int = 0
    duration_correct: int = 0
    medicines_missed: int = 0
    medicines_hallucinated: int = 0
    total_uncertain_items: int = 0
    total_latency_sec: float = 0.0
    fallback_count: int = 0

    @property
    def exact_name_acc(self) -> float:
        return (self.exact_name_matches / self.total_gt_meds * 100) if self.total_gt_meds else 0.0

    @property
    def fuzzy_name_acc(self) -> float:
        return (self.fuzzy_name_matches / self.total_gt_meds * 100) if self.total_gt_meds else 0.0

    @property
    def strength_acc(self) -> float:
        return (self.strength_correct / self.total_gt_meds * 100) if self.total_gt_meds else 0.0

    @property
    def frequency_acc(self) -> float:
        return (self.frequency_correct / self.total_gt_meds * 100) if self.total_gt_meds else 0.0

    @property
    def duration_acc(self) -> float:
        return (self.duration_correct / self.total_gt_meds * 100) if self.total_gt_meds else 0.0

    @property
    def avg_latency(self) -> float:
        return (self.total_latency_sec / self.total_images) if self.total_images else 0.0


def compute_aggregate(results: List[EvalImageResult]) -> AggregateMetrics:
    m = AggregateMetrics()
    m.total_images = len(results)
    for r in results:
        m.total_gt_meds += len(r.ground_truth_meds)
        m.total_ext_meds += len(r.extracted_meds)
        m.exact_name_matches += r.exact_name_matches
        m.fuzzy_name_matches += r.fuzzy_name_matches
        m.strength_correct += r.strength_correct
        m.frequency_correct += r.frequency_correct
        m.duration_correct += r.duration_correct
        m.medicines_missed += r.medicines_missed
        m.medicines_hallucinated += r.medicines_hallucinated
        m.total_uncertain_items += r.uncertain_items_count
        m.total_latency_sec += r.latency_sec
        if r.fallback_occurred:
            m.fallback_count += 1
    return m


def run_evaluation(
    eval_dir: str,
    report_path: str,
    providers_to_test: List[str],
) -> Dict[str, Any]:
    gt_path = os.path.join(eval_dir, "ground_truth.json")
    if not os.path.exists(gt_path):
        raise FileNotFoundError(f"ground_truth.json not found in {eval_dir}")

    with open(gt_path, "r") as f:
        ground_truth = json.load(f)

    all_files = os.listdir(eval_dir)
    images_to_eval = []
    skipped_images = []

    for fn in sorted(all_files):
        if fn == "ground_truth.json":
            continue
        if fn.lower().endswith((".png", ".jpg", ".jpeg", ".tiff")):
            if fn in ground_truth:
                images_to_eval.append(fn)
            else:
                skipped_images.append(fn)
                print(f"[!] Image '{fn}' has no ground truth entry: marked as 'needs ground truth' (skipped).")

    print(f"\n[*] Total images in eval set with ground truth: {len(images_to_eval)}")

    results_by_provider: Dict[str, List[EvalImageResult]] = {p: [] for p in providers_to_test}

    # Initialize providers
    providers_map = {}
    if "gemini" in providers_to_test:
        providers_map["gemini"] = GeminiVisionProvider(
            model_name=settings.GEMINI_MODEL,
            fallback_model=settings.GEMINI_FALLBACK_MODEL,
        )
    if "rapidocr" in providers_to_test:
        providers_map["rapidocr"] = LocalRapidOCRProvider()

    for provider_name in providers_to_test:
        prov = providers_map[provider_name]
        print(f"\n{'='*60}\nEvaluating Provider: {provider_name.upper()}\n{'='*60}")

        for img_fn in images_to_eval:
            img_path = os.path.join(eval_dir, img_fn)
            with open(img_path, "rb") as f:
                img_bytes = f.read()

            mime = "image/jpeg" if img_fn.lower().endswith((".jpg", ".jpeg")) else "image/png"
            is_synthetic = bool(ground_truth[img_fn].get("synthetic", False))
            gt_meds = ground_truth[img_fn].get("medicines", [])

            t0 = time.perf_counter()
            try:
                rec_result = prov.recognize_document(img_bytes, mime_type=mime)
            except Exception as e:
                print(f"  [ERROR] {img_fn}: Failed with {type(e).__name__}: {e}")
                # Fallback to an empty recognition result
                rec_result = DocumentRecognitionResult(
                    provider_used=provider_name,
                    model_used="failed",
                    fallback_occurred=False,
                    fallback_reason=str(e),
                )
            latency = time.perf_counter() - t0

            eval_res = evaluate_image(
                image_name=img_fn,
                is_synthetic=is_synthetic,
                provider_name=provider_name,
                rec_result=rec_result,
                gt_meds=gt_meds,
                latency=latency,
            )
            results_by_provider[provider_name].append(eval_res)

            print(
                f"  [{provider_name}] {img_fn}: {eval_res.exact_name_matches}/{len(gt_meds)} exact names, "
                f"{eval_res.fuzzy_name_matches}/{len(gt_meds)} fuzzy names, "
                f"{eval_res.medicines_missed} missed, {eval_res.medicines_hallucinated} hallucinated "
                f"({latency:.2f}s)"
            )

    # Compute worst failures
    all_eval_results: List[Tuple[float, EvalImageResult]] = []
    for prov, rlist in results_by_provider.items():
        for r in rlist:
            # Error penalty score
            penalty = (r.medicines_missed * 3) + (r.medicines_hallucinated * 2) + (
                len(r.ground_truth_meds) - r.exact_name_matches
            )
            all_eval_results.append((penalty, r))

    all_eval_results.sort(key=lambda x: x[0], reverse=True)
    worst_3 = [item[1] for item in all_eval_results[:3]]

    # Generate Markdown Report
    report_md = generate_markdown_report(results_by_provider, worst_3, skipped_images)

    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_md)
    print(f"\n[+] Saved Markdown evaluation report to {report_path}")

    return {
        "results_by_provider": results_by_provider,
        "worst_3": worst_3,
        "skipped_images": skipped_images,
    }


def generate_markdown_report(
    results_by_provider: Dict[str, List[EvalImageResult]],
    worst_3: List[EvalImageResult],
    skipped_images: List[str],
) -> str:
    md = []
    md.append("# Prescripto AI 2.0 — Evaluation Report\n")
    md.append(f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n")
    md.append("## 1. Executive Summary: Gemini vs RapidOCR Comparison\n")

    md.append("| Metric | Google Gemini | Local RapidOCR |")
    md.append("| :--- | :--- | :--- |")

    g_results = results_by_provider.get("gemini", [])
    r_results = results_by_provider.get("rapidocr", [])
    g_agg = compute_aggregate(g_results)
    r_agg = compute_aggregate(r_results)

    md.append(f"| **Evaluated Images** | {g_agg.total_images} | {r_agg.total_images} |")
    md.append(f"| **Total Expected Medicines** | {g_agg.total_gt_meds} | {r_agg.total_gt_meds} |")
    md.append(f"| **Exact Name Match Rate** | **{g_agg.exact_name_acc:.1f}%** ({g_agg.exact_name_matches}/{g_agg.total_gt_meds}) | {r_agg.exact_name_acc:.1f}% ({r_agg.exact_name_matches}/{r_agg.total_gt_meds}) |")
    md.append(f"| **Fuzzy Name Match Rate** | **{g_agg.fuzzy_name_acc:.1f}%** ({g_agg.fuzzy_name_matches}/{g_agg.total_gt_meds}) | {r_agg.fuzzy_name_acc:.1f}% ({r_agg.fuzzy_name_matches}/{r_agg.total_gt_meds}) |")
    md.append(f"| **Strength Accuracy** | **{g_agg.strength_acc:.1f}%** ({g_agg.strength_correct}/{g_agg.total_gt_meds}) | {r_agg.strength_acc:.1f}% ({r_agg.strength_correct}/{r_agg.total_gt_meds}) |")
    md.append(f"| **Frequency Accuracy** | **{g_agg.frequency_acc:.1f}%** ({g_agg.frequency_correct}/{g_agg.total_gt_meds}) | {r_agg.frequency_acc:.1f}% ({r_agg.frequency_correct}/{r_agg.total_gt_meds}) |")
    md.append(f"| **Duration Accuracy** | **{g_agg.duration_acc:.1f}%** ({g_agg.duration_correct}/{g_agg.total_gt_meds}) | {r_agg.duration_acc:.1f}% ({r_agg.duration_correct}/{r_agg.total_gt_meds}) |")
    md.append(f"| **Medicines Missed** | **{g_agg.medicines_missed}** | {r_agg.medicines_missed} |")
    md.append(f"| **Hallucinated Medicines** | **{g_agg.medicines_hallucinated}** | {r_agg.medicines_hallucinated} |")
    md.append(f"| **Uncertain/Degraded Items Flagged** | {g_agg.total_uncertain_items} | {r_agg.total_uncertain_items} |")
    md.append(f"| **Average Latency** | {g_agg.avg_latency:.2f}s | **{r_agg.avg_latency:.2f}s** |")
    md.append(f"| **Fallbacks Occurred** | {g_agg.fallback_count} | 0 |\n")

    # Real vs Synthetic breakdowns
    md.append("## 2. Real vs Synthetic Breakdown\n")

    for prov_name, rlist in results_by_provider.items():
        real_list = [r for r in rlist if not r.is_synthetic]
        synth_list = [r for r in rlist if r.is_synthetic]
        real_agg = compute_aggregate(real_list)
        synth_agg = compute_aggregate(synth_list)

        md.append(f"### Provider: `{prov_name}`\n")
        md.append("| Subset | Images | GT Meds | Exact Match | Fuzzy Match | Strength Acc | Missed | Hallucinated | Avg Latency |")
        md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
        md.append(
            f"| Real Images | {real_agg.total_images} | {real_agg.total_gt_meds} | "
            f"{real_agg.exact_name_acc:.1f}% | {real_agg.fuzzy_name_acc:.1f}% | {real_agg.strength_acc:.1f}% | "
            f"{real_agg.medicines_missed} | {real_agg.medicines_hallucinated} | {real_agg.avg_latency:.2f}s |"
        )
        md.append(
            f"| Synthetic Images | {synth_agg.total_images} | {synth_agg.total_gt_meds} | "
            f"{synth_agg.exact_name_acc:.1f}% | {synth_agg.fuzzy_name_acc:.1f}% | {synth_agg.strength_acc:.1f}% | "
            f"{synth_agg.medicines_missed} | {synth_agg.medicines_hallucinated} | {synth_agg.avg_latency:.2f}s |\n"
        )

    # Worst 3 Failures Section
    md.append("## 3. Worst 3 Failures (Expected vs Extracted)\n")
    for idx, failure in enumerate(worst_3, 1):
        md.append(f"### Failure #{idx}: `{failure.image_name}` (Provider: `{failure.provider_name}`)\n")
        md.append(f"- **Model/Engine Used**: `{failure.model_used or failure.provider_used}`")
        md.append(f"- **Missed**: {failure.medicines_missed} | **Hallucinated**: {failure.medicines_hallucinated} | **Latency**: {failure.latency_sec:.2f}s")
        if failure.fallback_occurred:
            md.append(f"- **Fallback**: {failure.fallback_reason}")

        md.append("\n**Expected Medications (Ground Truth):**\n")
        md.append("| Drug Name | Strength | Frequency | Duration |")
        md.append("| :--- | :--- | :--- | :--- |")
        for m in failure.ground_truth_meds:
            md.append(f"| {m.get('name')} | {m.get('strength')} | {m.get('frequency')} | {m.get('duration')} |")

        md.append("\n**Extracted Medications:**\n")
        if failure.extracted_meds:
            md.append("| Extracted Name | Strength | Frequency | Duration | Raw Text |")
            md.append("| :--- | :--- | :--- | :--- | :--- |")
            for m in failure.extracted_meds:
                md.append(f"| {m.get('name')} | {m.get('strength')} | {m.get('frequency')} | {m.get('duration')} | `{m.get('original_text')}` |")
        else:
            md.append("*No medications extracted.*")
        md.append("\n---\n")

    if skipped_images:
        md.append("## 4. Skipped Images (Missing Ground Truth)\n")
        for s in skipped_images:
            md.append(f"- `{s}`: needs ground truth\n")

    return "\n".join(md)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Prescription Recognition Accuracy")
    parser.add_argument(
        "--eval-dir",
        default=os.path.join(BACKEND_DIR, "tests", "eval_set"),
        help="Path to eval set directory containing images and ground_truth.json",
    )
    parser.add_argument(
        "--report-path",
        default=os.path.join(PROJECT_ROOT, "docs", "EVAL_REPORT.md"),
        help="Path where markdown evaluation report will be written",
    )
    parser.add_argument(
        "--providers",
        nargs="+",
        default=["gemini", "rapidocr"],
        help="Providers to evaluate (default: gemini rapidocr)",
    )

    args = parser.parse_args()
    run_evaluation(
        eval_dir=os.path.abspath(args.eval_dir),
        report_path=os.path.abspath(args.report_path),
        providers_to_test=args.providers,
    )

