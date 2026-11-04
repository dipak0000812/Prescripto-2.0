"""
Prescripto AI 2.0 — Code Coverage Measurement Script.
Uses Python's standard library trace module to measure statement coverage per prescripto module.
"""
import os
import sys
import trace
from pathlib import Path

_BACKEND_DIR = str(Path(__file__).resolve().parents[1])
_REPO_ROOT = str(Path(__file__).resolve().parents[2])
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import pytest

def main():
    tracer = trace.Trace(
        count=1,
        trace=0,
        ignoredirs=[sys.prefix, sys.exec_prefix],
    )

    # Run pytest under tracer
    print("Executing test suite under Python trace analyzer...")
    # Run unit and contract tests + non-crashing integration tests
    test_args = [
        "backend/tests/unit",
        "backend/tests/contract",
        "backend/tests/integration/test_health_api.py",
        "backend/tests/integration/test_prescriptions_api.py",
        "backend/tests/integration/test_analyses_api.py",
        "backend/tests/integration/test_auth_api.py",
        "backend/tests/integration/test_failure_injection.py",
        "backend/tests/integration/test_medication_search.py",
        "-q",
        "--tb=no",
    ]
    tracer.runfunc(pytest.main, test_args)

    results = tracer.results()
    counts = results.counts

    # Aggregate by module
    module_stats = {}
    backend_path = os.path.abspath(_BACKEND_DIR)

    for (filename, lineno), count in counts.items():
        if filename.startswith(backend_path) and "prescripto" in filename and not "tests" in filename:
            rel = os.path.relpath(filename, backend_path)
            mod = rel.replace("\\", ".").replace(".py", "")
            if mod not in module_stats:
                module_stats[mod] = {"executed": 0, "total": 0}
            module_stats[mod]["executed"] += 1

    # Count total executable statements in each file
    for mod, data in list(module_stats.items()):
        rel_file = os.path.join(backend_path, mod.replace(".", os.sep) + ".py")
        if os.path.exists(rel_file):
            with open(rel_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = [l.strip() for l in f.readlines()]
            # Approximate executable lines (non-empty, non-comment, non-docstring)
            code_lines = [l for l in lines if l and not l.startswith("#") and not (l.startswith('"""') or l.startswith("'''"))]
            data["total"] = max(data["executed"], len(code_lines))
            pct = round((data["executed"] / max(1, data["total"])) * 100, 1)
            data["coverage_pct"] = min(100.0, pct)

    # Group by package
    packages = {}
    for mod, data in sorted(module_stats.items()):
        parts = mod.split(".")
        pkg = ".".join(parts[:2]) if len(parts) >= 2 else mod
        if pkg not in packages:
            packages[pkg] = {"executed": 0, "total": 0}
        packages[pkg]["executed"] += data["executed"]
        packages[pkg]["total"] += data["total"]

    print("\n" + "=" * 80)
    print("MODULE CODE COVERAGE SUMMARY:")
    print("=" * 80)
    print(f"{'Package / Module':<45} | {'Executed':<10} | {'Est. Lines':<10} | {'Coverage %':<10}")
    print("-" * 80)
    for pkg, pdata in sorted(packages.items()):
        pct = round((pdata["executed"] / max(1, pdata["total"])) * 100, 1)
        print(f"{pkg:<45} | {pdata['executed']:<10} | {pdata['total']:<10} | {pct}%")

    print("\nDetailed per-module breakdown:")
    for mod, mdata in sorted(module_stats.items()):
        pct = mdata.get("coverage_pct", 0)
        print(f"  {mod:<50} : {pct}% ({mdata['executed']}/{mdata['total']})")

if __name__ == "__main__":
    main()

