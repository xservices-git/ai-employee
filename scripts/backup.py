"""Backup script - SQLite snapshot + ChromaDB snapshot.

Cron: every 6h.
Usage: python scripts/backup.py [--keep N]
"""
from __future__ import annotations
import argparse
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.config import SETTINGS


def backup_sqlite(dest: Path) -> Path:
    """Copy SQLite file via sqlite3 backup API (safe, online)."""
    import sqlite3
    src = SETTINGS.data_dir / "sqlite" / "ai_employee.db"
    if not src.exists():
        raise FileNotFoundError(f"SQLite not found: {src}")
    dest.mkdir(parents=True, exist_ok=True)
    target = dest / f"sqlite_{int(time.time())}.db"
    src_conn = sqlite3.connect(str(src))
    dst_conn = sqlite3.connect(str(target))
    with dst_conn:
        src_conn.backup(dst_conn)
    dst_conn.close()
    src_conn.close()
    return target


def backup_chromadb(dest: Path) -> Path | None:
    """Copy ChromaDB directory if exists."""
    chroma_dir = SETTINGS.data_dir / "chromadb"
    if not chroma_dir.exists():
        return None
    dest.mkdir(parents=True, exist_ok=True)
    target = dest / f"chromadb_{int(time.time())}"
    shutil.copytree(chroma_dir, target)
    return target


def prune_old(dest: Path, keep: int) -> int:
    """Keep only N newest backups per type. Returns deleted count."""
    deleted = 0
    for prefix in ("sqlite_", "chromadb_"):
        items = sorted(dest.glob(f"{prefix}*"), key=lambda p: p.stat().st_mtime, reverse=True)
        for old in items[keep:]:
            try:
                if old.is_dir():
                    shutil.rmtree(old)
                else:
                    old.unlink()
                deleted += 1
            except OSError:
                pass
    return deleted


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--keep", type=int, default=4, help="Keep N newest per type (default 4 = 24h at 6h cadence)")
    parser.add_argument("--dest", type=str, default=None, help="Backup root (default: data_dir/backups)")
    args = parser.parse_args()

    dest = Path(args.dest) if args.dest else (SETTINGS.data_dir / "backups")
    dest.mkdir(parents=True, exist_ok=True)

    print(f"[backup] dest={dest}")
    try:
        sqlite_target = backup_sqlite(dest)
        size_mb = sqlite_target.stat().st_size / 1024 / 1024
        print(f"[backup] sqlite OK: {sqlite_target.name} ({size_mb:.2f} MB)")
    except Exception as e:
        print(f"[backup] sqlite FAIL: {e}")
        return 1

    try:
        chroma_target = backup_chromadb(dest)
        if chroma_target:
            print(f"[backup] chromadb OK: {chroma_target.name}")
        else:
            print(f"[backup] chromadb: skipped (not found)")
    except Exception as e:
        print(f"[backup] chromadb FAIL: {e}")

    deleted = prune_old(dest, args.keep)
    print(f"[backup] pruned {deleted} old backups, keep={args.keep}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
