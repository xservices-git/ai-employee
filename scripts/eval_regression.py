"""Eval regression test - run 50 cases, compare with baseline.

Usage: python scripts/eval_regression.py [--baseline FILE] [--out FILE]
Exit 0 = pass, 1 = fail.
"""
from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import db, orchestrator
import asyncio


def run_eval() -> dict:
    """Run all eval cases. Returns {total, passed, failed, pass_rate, by_type}."""
    from tests.eval_cases import EVAL_CASES
    results = {"total": len(EVAL_CASES), "passed": 0, "failed": 0, "pass_rate": 0.0, "by_type": {}}
    for case in EVAL_CASES:
        task = db.create_task(
            task_type="pending",
            input_data={"text": case["input"]},
            user_id="eval",
            domain=case.get("domain"),
        )
        try:
            asyncio.run(orchestrator.run(task["id"]))
        except Exception as e:
            db.update_task(task["id"], status="failed", error_message=str(e)[:500])
        final = db.get_task(task["id"])
        ok = final["status"] == "completed" and final.get("result")
        if ok:
            results["passed"] += 1
        else:
            results["failed"] += 1
        t = case.get("task_type", "unknown")
        results["by_type"].setdefault(t, {"total": 0, "passed": 0})
        results["by_type"][t]["total"] += 1
        if ok:
            results["by_type"][t]["passed"] += 1
    results["pass_rate"] = round(results["passed"] / results["total"], 4) if results["total"] else 0.0
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=str, default=None, help="Baseline JSON file to compare")
    parser.add_argument("--out", type=str, default=None, help="Output JSON file")
    args = parser.parse_args()

    start = time.time()
    print(f"[eval] running {len(open('tests/eval_cases.py').read())} cases...")
    results = run_eval()
    elapsed = round(time.time() - start, 2)

    print(f"[eval] {results['passed']}/{results['total']} PASS ({results['pass_rate']*100:.1f}%) in {elapsed}s")
    for t, stats in results["by_type"].items():
        rate = round(stats["passed"] / stats["total"], 4) if stats["total"] else 0.0
        print(f"  - {t}: {stats['passed']}/{stats['total']} ({rate*100:.0f}%)")

    if args.out:
        Path(args.out).write_text(json.dumps({**results, "elapsed_seconds": elapsed}, indent=2))
        print(f"[eval] saved -> {args.out}")

    if args.baseline:
        base = json.loads(Path(args.baseline).read_text())
        base_rate = base.get("pass_rate", 0)
        if results["pass_rate"] < base_rate - 0.05:  # 5% drop = fail
            print(f"[eval] REGRESSION: {results['pass_rate']*100:.1f}% < baseline {base_rate*100:.1f}%")
            return 1
        print(f"[eval] OK: {results['pass_rate']*100:.1f}% >= baseline {base_rate*100:.1f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
