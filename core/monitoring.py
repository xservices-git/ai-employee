"""Monitoring: metrics collection + alert callbacks.

- Prometheus-style /metrics endpoint (plain text, no lib)
- Telegram alert sender (via env TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID)
"""
from __future__ import annotations
import os
import time
from typing import Optional
from core import db

# --- Metrics ---

_metrics_lock = __import__("threading").Lock()
_metrics: dict[str, float] = {
    "tasks_total": 0,
    "tasks_completed": 0,
    "tasks_failed": 0,
    "tasks_pending": 0,
    "rules_pending": 0,
    "rules_auto_disabled": 0,
    "backup_last_ok": 0,
    "uptime_seconds": 0,
}
_start_time = time.time()


def _get_startup() -> float:
    return _start_time


def update_metric(name: str, value: float) -> None:
    with _metrics_lock:
        _metrics[name] = value


def inc_metric(name: str, delta: float = 1) -> None:
    with _metrics_lock:
        _metrics[name] = _metrics.get(name, 0) + delta


def get_metrics() -> dict[str, float]:
    """Return snapshot of current metrics."""
    with _metrics_lock:
        m = dict(_metrics)
    m["uptime_seconds"] = round(time.time() - _get_startup())
    # query DB counts
    try:
        conn = db.get_db()
        m["tasks_total"] = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        m["tasks_completed"] = conn.execute("SELECT COUNT(*) FROM tasks WHERE status='completed'").fetchone()[0]
        m["tasks_failed"] = conn.execute("SELECT COUNT(*) FROM tasks WHERE status='failed'").fetchone()[0]
        m["tasks_pending"] = conn.execute("SELECT COUNT(*) FROM tasks WHERE status='pending'").fetchone()[0]
        m["rules_pending"] = conn.execute("SELECT COUNT(*) FROM proposed_rules WHERE status='pending'").fetchone()[0]
        m["rules_auto_disabled"] = conn.execute("SELECT COUNT(*) FROM proposed_rules WHERE status='auto_disabled'").fetchone()[0]
    except Exception:
        pass
    return m


def format_prometheus(prefix: str = "ai_employee") -> str:
    """Format as prometheus text format (no external lib)."""
    m = get_metrics()
    lines = []
    for key, val in m.items():
        safe_key = key.replace(" ", "_")
        lines.append(f"# HELP {prefix}_{safe_key} Auto-generated metric")
        lines.append(f"# TYPE {prefix}_{safe_key} gauge")
        lines.append(f"{prefix}_{safe_key} {val}")
    return "\n".join(lines) + "\n"


# --- Telegram alerts ---

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


def send_alert(message: str, level: str = "warn") -> bool:
    """Send alert via Telegram. Returns True if sent."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    import urllib.request
    import urllib.parse
    emoji = {"info": "\u2139\ufe0f", "warn": "\u26a0\ufe0f", "error": "\u274c", "success": "\u2705"}
    text = f"{emoji.get(level, '')} *{level.upper()}* ai-employee\\\n{message}"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
    }).encode()
    try:
        urllib.request.urlopen(url, data=data, timeout=10)
        return True
    except Exception:
        return False
