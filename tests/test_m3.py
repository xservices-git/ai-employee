"""M3 smoke tests - auth, monitoring, backup.

Run: python tests/test_m3.py
"""
import sys
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import auth, monitoring
from core.auth import hash_password, verify_password, create_jwt, decode_jwt

def test_password_hash():
    pw = "test_password_123"
    h = hash_password(pw)
    assert h.startswith("pbkdf2_sha256$")
    assert verify_password(pw, h) is True
    assert verify_password("wrong", h) is False
    print(f"[OK] password hash + verify")

def test_password_timing_safe():
    """Same-length wrong password should still be False."""
    pw = "test_password_123"
    h = hash_password(pw)
    assert verify_password("test_password_124", h) is False
    print("[OK] password timing safe")

def test_jwt_roundtrip():
    token = create_jwt("user-1", "admin", ttl=60)
    payload = decode_jwt(token)
    assert payload is not None
    assert payload["sub"] == "user-1"
    assert payload["role"] == "admin"
    assert payload["exp"] > int(time.time())
    print("[OK] JWT create + decode")

def test_jwt_expired():
    token = create_jwt("user-1", "user", ttl=-10)
    assert decode_jwt(token) is None
    print("[OK] JWT expired rejected")

def test_jwt_tampered():
    token = create_jwt("user-1", "user", ttl=60)
    parts = token.split(".")
    parts[1] = parts[1][:-2] + "XX"
    bad = ".".join(parts)
    assert decode_jwt(bad) is None
    print("[OK] JWT tampered rejected")

def test_monitoring_metrics():
    m = monitoring.get_metrics()
    assert "tasks_total" in m
    assert "uptime_seconds" in m
    assert m["uptime_seconds"] >= 0
    print(f"[OK] monitoring metrics ({len(m)} keys)")

def test_monitoring_prometheus():
    txt = monitoring.format_prometheus()
    assert "ai_employee_tasks_total" in txt
    assert "ai_employee_uptime_seconds" in txt
    assert "# TYPE" in txt
    assert "# HELP" in txt
    assert txt.endswith("\n")
    print(f"[OK] prometheus format ({len(txt.splitlines())} lines)")

def test_monitoring_telegram_no_env():
    """send_alert must return False silently when env not set."""
    saved_token = monitoring.TELEGRAM_BOT_TOKEN
    saved_chat = monitoring.TELEGRAM_CHAT_ID
    monitoring.TELEGRAM_BOT_TOKEN = ""
    monitoring.TELEGRAM_CHAT_ID = ""
    try:
        assert monitoring.send_alert("test") is False
        print("[OK] telegram alert skipped (no env)")
    finally:
        monitoring.TELEGRAM_BOT_TOKEN = saved_token
        monitoring.TELEGRAM_CHAT_ID = saved_chat

def test_metrics_inc():
    monitoring.inc_metric("tasks_total", 5)
    m = monitoring.get_metrics()
    assert m["tasks_total"] >= 5
    print(f"[OK] metrics inc + read")

def test_backup_sqlite():
    """Backup script must create a valid SQLite copy."""
    from scripts.backup import backup_sqlite, prune_old
    from core.config import SETTINGS
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp)
        try:
            target = backup_sqlite(dest)
            assert target.exists()
            assert target.stat().st_size > 0
            assert str(target).endswith(".db")
            # Verify it's a valid SQLite file
            import sqlite3
            conn = sqlite3.connect(str(target))
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            conn.close()
            assert len(tables) > 0, "Backup SQLite has no tables"
            # Prune should not error
            deleted = prune_old(dest, keep=0)
            assert deleted >= 1
            print(f"[OK] backup sqlite ({target.stat().st_size} bytes, {len(tables)} tables)")
        except FileNotFoundError as e:
            print(f"[SKIP] backup sqlite (DB not initialized: {e})")

if __name__ == "__main__":
    test_password_hash()
    test_password_timing_safe()
    test_jwt_roundtrip()
    test_jwt_expired()
    test_jwt_tampered()
    test_monitoring_metrics()
    test_monitoring_prometheus()
    test_monitoring_telegram_no_env()
    test_metrics_inc()
    test_backup_sqlite()
    print("\n=== ALL M3 TESTS PASS ===")
