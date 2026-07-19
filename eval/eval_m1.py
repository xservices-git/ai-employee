"""Eval harness - 30 cases cho 3 task types (M1 DoD).

Moi case: input text + expected (task_type, must_contain, status).
Chay orchestrator, so sanh output, tinh pass rate.
"""
from __future__ import annotations
import asyncio
import sys
import time
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import db, memory, orchestrator


EVAL_CASES = [
    # ===== 10 cases: data_processing =====
    {
        "input": "Kiem tra don hang #12345 cho khach Nguyen Van A",
        "expected": {"task_type": "data_processing", "domain": "customer_support",
                     "must_contain": []},
    },
    {
        "input": "Lay danh sach khach hang vip",
        "expected": {"task_type": "data_processing", "must_contain": []},
    },
    {
        "input": "Truy van invoice thang 7",
        "expected": {"task_type": "data_processing", "domain": "sales_ops", "must_contain": []},
    },
    {
        "input": "Tim order cua khach so dien thoai 0901234567",
        "expected": {"task_type": "data_processing", "must_contain": []},
    },
    {
        "input": "Lookup ticket support #789",
        "expected": {"task_type": "data_processing", "domain": "customer_support", "must_contain": []},
    },
    {
        "input": "Cho xem doanh thu hom nay",
        "expected": {"task_type": "data_processing", "must_contain": []},
    },
    {
        "input": "Lay thong tin khach hang ID 42",
        "expected": {"task_type": "data_processing", "must_contain": []},
    },
    {
        "input": "Truy van bang products theo SKU",
        "expected": {"task_type": "data_processing", "must_contain": []},
    },
    {
        "input": "Check order status cua shop 187",
        "expected": {"task_type": "data_processing", "must_contain": []},
    },
    {
        "input": "Query database lay danh sach hoa don",
        "expected": {"task_type": "data_processing", "must_contain": []},
    },

    # ===== 10 cases: content_generation =====
    {
        "input": "Viet email chao khach hang moi dang ky",
        "expected": {"task_type": "content_generation", "must_contain": []},
    },
    {
        "input": "Soan thao bao cao doanh thu thang 7",
        "expected": {"task_type": "content_generation", "must_contain": []},
    },
    {
        "input": "Viet bai viet gioi thieu san pham moi",
        "expected": {"task_type": "content_generation", "must_contain": []},
    },
    {
        "input": "Draft email follow up cho lead ABC",
        "expected": {"task_type": "content_generation", "must_contain": []},
    },
    {
        "input": "Soan thong bao nghi le 2/9",
        "expected": {"task_type": "content_generation", "must_contain": []},
    },
    {
        "input": "Content cho trang chu website",
        "expected": {"task_type": "content_generation", "must_contain": []},
    },
    {
        "input": "Tao template reply ticket support",
        "expected": {"task_type": "content_generation", "must_contain": []},
    },
    {
        "input": "Viet noi dung cho newsletter thang 8",
        "expected": {"task_type": "content_generation", "must_contain": []},
    },
    {
        "input": "Soan email confirm don hang",
        "expected": {"task_type": "content_generation", "must_contain": []},
    },
    {
        "input": "Draft bao cao tong ket quy 3",
        "expected": {"task_type": "content_generation", "must_contain": []},
    },

    # ===== 10 cases: research_summarization =====
    {
        "input": "Tom tat bai bao ve AI va tu dong hoa",
        "expected": {"task_type": "research_summarization", "must_contain": []},
    },
    {
        "input": "Search web ve ChatGPT ban moi nhat",
        "expected": {"task_type": "research_summarization", "must_contain": []},
    },
    {
        "input": "Tim kiem thong tin ve TikTok Shop 2026",
        "expected": {"task_type": "research_summarization", "must_contain": []},
    },
    {
        "input": "Nghien cuu ve PostgreSQL vs MariaDB",
        "expected": {"task_type": "research_summarization", "must_contain": []},
    },
    {
        "input": "Wiki ve machine learning co ban",
        "expected": {"task_type": "research_summarization", "must_contain": []},
    },
    {
        "input": "Summary tai lieu ban hang TikTok",
        "expected": {"task_type": "research_summarization", "must_contain": []},
    },
    {
        "input": "Research ve best practices REST API",
        "expected": {"task_type": "research_summarization", "must_contain": []},
    },
    {
        "input": "Tim thong tin ve Giai phap affiliate 2026",
        "expected": {"task_type": "research_summarization", "must_contain": []},
    },
    {
        "input": "Tom tat PDF huong dan su dung Ollama",
        "expected": {"task_type": "research_summarization", "must_contain": []},
    },
    {
        "input": "Search docs cua FastAPI",
        "expected": {"task_type": "research_summarization", "must_contain": []},
    },
]


async def run_case(case: dict, idx: int) -> dict:
    """Chay 1 case, tra ve ket qua."""
    task = db.create_task(
        task_type="pending",
        input_data={"text": case["input"]},
    )
    t0 = time.time()
    try:
        result = await orchestrator.run(task["id"])
    except Exception as e:
        return {"idx": idx, "input": case["input"][:50], "passed": False,
                "error": str(e), "duration_ms": int((time.time() - t0) * 1000)}

    expected = case["expected"]
    actual_type = (result.get("plan", {}) or {}).get("classification", {}).get("task_type")
    issues = []
    if expected["task_type"] != actual_type:
        issues.append(f"task_type: expected={expected['task_type']} actual={actual_type}")
    if expected.get("domain"):
        actual_domain = (result.get("plan", {}) or {}).get("classification", {}).get("domain")
        if expected["domain"] != actual_domain:
            issues.append(f"domain: expected={expected['domain']} actual={actual_domain}")
    if expected.get("must_contain"):
        text = str(result.get("result", {}))
        for kw in expected["must_contain"]:
            if kw.lower() not in text.lower():
                issues.append(f"missing: {kw}")

    return {
        "idx": idx,
        "input": case["input"][:50],
        "expected_type": expected["task_type"],
        "actual_type": actual_type,
        "status": result.get("status"),
        "passed": not issues,
        "issues": issues,
        "duration_ms": int((time.time() - t0) * 1000),
    }


async def run_all() -> dict:
    db.reset_db()
    db.get_db()
    t0 = time.time()
    results = []
    for i, case in enumerate(EVAL_CASES):
        r = await run_case(case, i)
        results.append(r)
        status = "PASS" if r["passed"] else "FAIL"
        print(f"[{i+1:2d}/{len(EVAL_CASES)}] {status} {r['input'][:40]:<40} "
              f"-> {r.get('actual_type', '?')} ({r['duration_ms']}ms)")
        if not r["passed"]:
            for issue in r.get("issues", []):
                print(f"      ! {issue}")

    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    total_ms = int((time.time() - t0) * 1000)
    print(f"\n=== EVAL RESULT: {passed}/{total} pass ({passed/total*100:.1f}%) in {total_ms}ms ===")
    return {
        "passed": passed,
        "total": total,
        "pass_rate": passed / total,
        "duration_ms": total_ms,
        "results": results,
    }


if __name__ == "__main__":
    asyncio.run(run_all())
