#!/usr/bin/env python3
"""Backup cron job.

Runs every 6h. Wraps scripts/backup.py and sends Telegram alert on failure.

Usage:
    python cron/backup_cron.py                  # run with defaults
    python cron/backup_cron.py --keep 8         # keep 8 newest (48h at 6h cadence)
    python cron/backup_cron.py --alert-on-ok    # also alert on success
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import monitoring

def run_backup(keep: int) -> tuple[int, str]:
    """Run backup.py subprocess. Returns (exit_code, output)."""
    script = ROOT / "scripts" / "backup.py"
    proc = subprocess.run(
        [sys.executable, str(script), "--keep", str(keep)],
        capture_output=True,
        text=True,
        timeout=300,
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, output

def main() -> int:
    parser = argparse.ArgumentParser(description="Backup cron job")
    parser.add_argument("--keep", type=int, default=4, help="Backups to keep (default 4 = 24h at 6h)")
    parser.add_argument("--alert-on-ok", action="store_true", help="Alert on success too")
    args = parser.parse_args()

    start = time.monotonic()
    print(f"[backup_cron] start keep={args.keep}")

    code, output = run_backup(args.keep)
    duration = round(time.monotonic() - start, 2)

    if code == 0:
        monitoring.update_metric("backup_last_ok", time.time())
        msg = f"Backup OK in {duration}s\n{output.strip()[-500:]}"
        print(msg)
        if args.alert_on_ok:
            monitoring.send_alert(msg, level="success")
    else:
        msg = f"Backup FAILED ({code}) in {duration}s\n{output.strip()[-500:]}"
        print(msg, file=sys.stderr)
        monitoring.send_alert(msg, level="error")

    return code

if __name__ == "__main__":
    sys.exit(main())
