"""Tang 2: Semantic memory - keyword-based similarity (M1).

M2 se thay bang embedding that (Ollama nomic-embed).
Hien tai dung token overlap (Jaccard) - du de test flow.
"""
from __future__ import annotations
import json
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from . import db as dbm
from .config import SETTINGS


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _tokenize(text: str) -> set[str]:
    """Lowercase + split tu tieng Viet/Anh, loai bo stop words don gian."""
    text = (text or "").lower()
    tokens = re.findall(r"[a-z0-9_áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ]+", text)
    stop = {"the", "a", "an", "is", "are", "was", "be", "been", "of", "to", "in",
            "on", "at", "for", "with", "by", "this", "that", "it", "la", "co",
            "cac", "va", "la", "mot", "cho", "nhu", "nhung", "khi", "toi"}
    return {t for t in tokens if t and t not in stop and len(t) > 1}


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def store_episode(
    task_id: str,
    task_type: str,
    domain: Optional[str],
    input_text: str,
    output_text: str,
    success: bool,
    confidence: Optional[float] = None,
) -> str:
    """Luu 1 episode vao memory (M2 se embed that)."""
    ep_id = str(uuid.uuid4())
    conn = dbm.get_db()
    conn.execute(
        """CREATE TABLE IF NOT EXISTS memory_episodes (
            id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL,
            task_type TEXT NOT NULL,
            domain TEXT,
            input_text TEXT NOT NULL,
            output_text TEXT,
            success INTEGER NOT NULL,
            confidence REAL,
            tokens TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""",
    )
    conn.execute(
        """INSERT INTO memory_episodes
           (id, task_id, task_type, domain, input_text, output_text,
            success, confidence, tokens, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (ep_id, task_id, task_type, domain, input_text, output_text,
         1 if success else 0, confidence,
         json.dumps(sorted(_tokenize(input_text + " " + output_text))),
         _now()),
    )
    conn.commit()
    return ep_id


def search_similar(
    query: str,
    task_type: Optional[str] = None,
    top_k: int = 5,
) -> list[dict]:
    """Top-k episodes giong query (Jaccard token overlap)."""
    conn = dbm.get_db()
    # Ensure table exists (M2 se di chuyen sang ChromaDB).
    conn.execute(
        """CREATE TABLE IF NOT EXISTS memory_episodes (
            id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL,
            task_type TEXT NOT NULL,
            domain TEXT,
            input_text TEXT NOT NULL,
            output_text TEXT,
            success INTEGER NOT NULL,
            confidence REAL,
            tokens TEXT NOT NULL,
            created_at TEXT NOT NULL
        )"""
    )
    conn.commit()
    if task_type:
        rows = conn.execute(
            "SELECT * FROM memory_episodes WHERE task_type = ? ORDER BY created_at DESC LIMIT 200",
            (task_type,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM memory_episodes ORDER BY created_at DESC LIMIT 200",
        ).fetchall()

    q_tokens = _tokenize(query)
    scored = []
    for r in rows:
        ep_tokens = set(json.loads(r["tokens"]))
        score = _jaccard(q_tokens, ep_tokens)
        scored.append((score, r))
    scored.sort(key=lambda x: x[0], reverse=True)
    out = []
    for score, r in scored[:top_k]:
        out.append({
            "id": r["id"],
            "task_id": r["task_id"],
            "task_type": r["task_type"],
            "domain": r["domain"],
            "input_text": r["input_text"],
            "output_text": r["output_text"],
            "success": bool(r["success"]),
            "confidence": r["confidence"],
            "score": round(score, 3),
        })
    return out


def calculate_familiarity(task_type: str, domain: Optional[str]) -> float:
    """So 0-1: quen thuoc voi task_type+domain nay."""
    conn = dbm.get_db()
    conn.execute(
        """CREATE TABLE IF NOT EXISTS memory_episodes (
            id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL,
            task_type TEXT NOT NULL,
            domain TEXT,
            input_text TEXT NOT NULL,
            output_text TEXT,
            success INTEGER NOT NULL,
            confidence REAL,
            tokens TEXT NOT NULL,
            created_at TEXT NOT NULL
        )"""
    )
    conn.commit()
    if domain:
        row = conn.execute(
            """SELECT COUNT(*) AS n,
                      SUM(success) AS ok
               FROM memory_episodes
               WHERE task_type = ? AND (domain = ? OR domain IS NULL)""",
            (task_type, domain),
        ).fetchone()
    else:
        row = conn.execute(
            """SELECT COUNT(*) AS n, SUM(success) AS ok
               FROM memory_episodes WHERE task_type = ?""",
            (task_type,),
        ).fetchone()
    n = row["n"] or 0
    ok = row["ok"] or 0
    if n == 0:
        return 0.3
    success_rate = ok / n
    exp = min(1.0, n / 10)
    return round(success_rate * exp, 3)
