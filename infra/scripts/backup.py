#!/usr/bin/env python
"""Backup script: dump SQLite + tar ChromaDB."""

from __future__ import annotations

import os
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def backup_database(backup_dir: Path) -> Path:
    """Backup SQLite database."""
    backup_dir.mkdir(parents=True, exist_ok=True)
    db_path = Path("./data/ai-employee.db")
    if not db_path.exists():
        print(f"Database not found: {db_path}", file=sys.stderr)
        return None

    backup_path = backup_dir / "db.sqlite"
    # Use SQLite backup API
    source = sqlite3.connect(str(db_path))
    dest = sqlite3.connect(str(backup_path))
    source.backup(dest)
    dest.close()
    source.close()
    print(f"DB backed up to {backup_path}")
    return backup_path


def backup_chroma(backup_dir: Path) -> Path:
    """Tar ChromaDB directory."""
    chroma_path = Path("./data/chroma")
    if not chroma_path.exists():
        print(f"ChromaDB not found: {chroma_path}", file=sys.stderr)
        return None

    backup_path = backup_dir / "chroma.tar.gz"
    subprocess.run(
        ["tar", "czf", str(backup_path), "-C", str(chroma_path.parent), chroma_path.name],
        check=True,
    )
    print(f"ChromaDB backed up to {backup_path}")
    return backup_path


def cleanup_old_backups(base_dir: Path, keep: int = 7) -> None:
    """Keep only N most recent backups."""
    if not base_dir.exists():
        return
    backups = sorted([d for d in base_dir.iterdir() if d.is_dir()], key=lambda d: d.name)
    if len(backups) > keep:
        for old in backups[:-keep]:
            shutil.rmtree(old)
            print(f"Removed old backup: {old}")


def main():
    base_dir = Path(os.environ.get("BACKUP_DIR", "./backups"))
    ts = datetime.utcnow().strftime("%Y-%m-%d_%H-%M")
    backup_dir = base_dir / ts

    print(f"Starting backup to {backup_dir}")
    backup_database(backup_dir)
    backup_chroma(backup_dir)
    cleanup_old_backups(base_dir, keep=7)
    print("Backup complete")


if __name__ == "__main__":
    main()
