"""Eval harness: chạy test, so sánh model, generate report."""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import typer
import yaml
from rich.console import Console
from rich.table import Table

from core.common.logging import get_logger

app = typer.Typer()
console = Console()
logger = get_logger(__name__)


def load_dataset(domain: str) -> list[dict[str, Any]]:
    """Load eval cases for a domain."""
    path = Path(f"eval/datasets/{domain}.yaml")
    if not path.exists():
        return []
    with open(path) as f:
        data = yaml.safe_load(f)
    return data.get("cases", [])


async def run_case(case: dict[str, Any], orchestrator: Any) -> dict[str, Any]:
    """Run a single eval case."""
    from core.common.types import TaskInput

    start = time.time()
    result = {"id": case["id"], "passed": True, "issues": []}

    try:
        task_input = TaskInput(
            input=case["input"],
            user_id="eval_user",
            domain=case.get("domain"),
        )
        task = await orchestrator.process_task(task_input)
        duration = time.time() - start
        result["duration_sec"] = duration

        # Check timeout
        if "timeout_sec" in case and duration > case["timeout_sec"]:
            result["passed"] = False
            result["issues"].append(f"timeout: {duration:.1f}s > {case['timeout_sec']}s")

        # Check task type
        if "expected" in case:
            expected = case["expected"]
            if "task_type" in expected and task.task_type != expected["task_type"]:
                result["passed"] = False
                result["issues"].append(f"wrong_task_type: {task.task_type} != {expected['task_type']}")

            # Check should_contain
            if "should_contain" in expected and task.result:
                output = json.dumps(task.result)
                for phrase in expected["should_contain"]:
                    if phrase not in output:
                        result["passed"] = False
                        result["issues"].append(f"missing: {phrase}")

            # Check should_not_contain
            if "should_not_contain" in expected and task.result:
                output = json.dumps(task.result)
                for phrase in expected["should_not_contain"]:
                    if phrase in output:
                        result["passed"] = False
                        result["issues"].append(f"forbidden: {phrase}")

    except Exception as e:
        result["passed"] = False
        result["issues"].append(f"exception: {e}")
        logger.exception("eval.case_failed", case_id=case["id"])

    return result


async def run_domain(domain: str, orchestrator: Any) -> dict[str, Any]:
    """Run all cases in a domain."""
    cases = load_dataset(domain)
    if not cases:
        return {"domain": domain, "total": 0, "passed": 0, "failed": 0, "results": []}

    console.print(f"[bold cyan]Running {len(cases)} cases for {domain}...[/bold cyan]")
    results = []
    for case in cases:
        result = await run_case(case, orchestrator)
        results.append(result)
        status = "✓" if result["passed"] else "✗"
        console.print(f"  {status} {case['id']}: {', '.join(result['issues']) or 'OK'}")

    passed = sum(1 for r in results if r["passed"])
    return {
        "domain": domain,
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "results": results,
    }


@app.command()
def run(
    domain: str = typer.Option("all", help="Domain or 'all'"),
    ci: bool = typer.Option(False, help="CI mode"),
    fail_on_regression: bool = typer.Option(True, help="Exit 1 on regression"),
) -> None:
    """Run eval suite."""
    import asyncio
    from api.deps import get_orchestrator

    orchestrator = get_orchestrator()
    domains = ["customer_support", "sales_ops", "hr_admin"] if domain == "all" else [domain]
    all_results = []
    for d in domains:
        result = asyncio.run(run_domain(d, orchestrator))
        all_results.append(result)

    # Summary
    console.print("\n[bold]=== Summary ===[/bold]")
    table = Table()
    table.add_column("Domain")
    table.add_column("Total")
    table.add_column("Passed")
    table.add_column("Failed")
    table.add_column("Pass rate")
    for r in all_results:
        total = r["total"]
        if total == 0:
            continue
        rate = f"{r['passed']/total*100:.1f}%"
        table.add_row(r["domain"], str(total), str(r["passed"]), str(r["failed"]), rate)
    console.print(table)

    # Save report
    report_dir = Path("eval/reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    report_path = report_dir / f"eval_{ts}.json"
    with open(report_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    console.print(f"\n[green]Report saved to {report_path}[/green]")


if __name__ == "__main__":
    app()
