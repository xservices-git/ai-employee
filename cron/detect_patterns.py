#!/usr/bin/env python3
"""Pattern detection cron job.

Runs weekly (or on-demand) to:
1. Scan feedback + failed tasks for patterns
2. Propose new rules to HUMAN GATE
3. Auto-disable rules failing > 50% with 20+ samples

Usage:
    python cron/detect_patterns.py              # run full detection
    python cron/detect_patterns.py --dry-run    # preview only, no DB writes
    python cron/detect_patterns.py --auto-disable-only  # only run auto-disable pass
"""
import argparse
import json
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError

# allow imports from project root
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.config import SETTINGS  # noqa: E402
from core.pattern_detector import run_pattern_detection  # noqa: E402


def call_api(path: str, method: str = "GET", payload: dict | None = None) -> dict:
    """Call internal API. Used when server is running."""
    base = f"http://127.0.0.1:{SETTINGS.port}"
    url = f"{base}{path}"
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except URLError as exc:
        raise RuntimeError(f"API call failed: {exc}") from exc


def run_detection(dry_run: bool, auto_disable_only: bool) -> dict:
    """Run pattern detection via API or direct call."""
    if auto_disable_only:
        # auto-disable handled inline when record_rule_outcome is called.
        # No separate cron pass needed.
        return {"auto_disabled": 0, "note": "auto-disable handled inline in record_rule_outcome"}

    if dry_run:
        # run detector without writing to DB
        result = run_pattern_detection(lookback_days=30, min_occurrences=3, dry_run=True)
        result["dry_run"] = True
        return result

    # normal: call API
    result = call_api("/v1/rules/detect", method="POST", payload={"lookback_days": 30})
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Pattern detection cron job")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, no DB writes")
    parser.add_argument("--auto-disable-only", action="store_true", help="Only run auto-disable pass")
    args = parser.parse_args()

    start = time.monotonic()
    print(f"[detect_patterns] start (dry_run={args.dry_run} auto_disable_only={args.auto_disable_only})")

    try:
        result = run_detection(args.dry_run, args.auto_disable_only)
        duration = time.monotonic() - start
        print(f"[detect_patterns] done in {duration:.1f}s")
        print(json.dumps(result, indent=2, default=str))
        return 0
    except Exception as exc:
        print(f"[detect_patterns] FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
