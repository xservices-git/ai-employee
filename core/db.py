"""SQLite - tap 1 file, stdlib thuan, khong can ORM.

Tang 1: Episodic memory - luu task history.
"""
from __future__ import annotations
import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .config import SETTINGS


_lock = threading.Lock()
_conn: Optional[sqlite3.Connection] = None


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    password_hash TEXT,
    api_token TEXT UNIQUE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT 'local',
    task_type TEXT NOT NULL,
    domain TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    priority INTEGER DEFAULT 3,
    input_data TEXT NOT NULL,
    plan TEXT,
    result TEXT,
    confidence REAL,
    trace_id TEXT,
    error_message TEXT,
    created_at TEXT NOT NULL,
    completed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_user_type ON tasks(user_id, task_type);

CREATE TABLE IF NOT EXISTS feedback (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    score INTEGER NOT NULL,
    notes TEXT,
    corrections TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_feedback_task ON feedback(task_id);

CREATE TABLE IF NOT EXISTS approval_requests (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    proposal TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    reason TEXT,
    decision TEXT NOT NULL DEFAULT 'pending',
    modified_args TEXT,
    feedback TEXT,
    approver_id TEXT,
    decided_at TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_approvals_status ON approval_requests(decision, created_at);

CREATE TABLE IF NOT EXISTS learning_events (
    id TEXT PRIMARY KEY,
    task_id TEXT,
    feedback_id TEXT,
    event_type TEXT NOT NULL,
    before_state TEXT,
    after_state TEXT,
    rule_extracted TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS traces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trace_id TEXT NOT NULL,
    span_id TEXT NOT NULL,
    parent_span_id TEXT,
    name TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT,
    duration_ms REAL,
    attributes TEXT,
    status TEXT,
    UNIQUE(trace_id, span_id)
);
CREATE INDEX IF NOT EXISTS idx_traces_trace ON traces(trace_id);

CREATE TABLE IF NOT EXISTS skill_metadata (
    id TEXT PRIMARY KEY,
    skill_name TEXT NOT NULL UNIQUE,
    domain TEXT,
    success_count INTEGER DEFAULT 0,
    fail_count INTEGER DEFAULT 0,
    sample_size INTEGER DEFAULT 0,
    success_rate REAL DEFAULT 0.0,
    status TEXT DEFAULT 'active',
    last_used_at TEXT
);

CREATE TABLE IF NOT EXISTS proposed_rules (
    id TEXT PRIMARY KEY,
    rule_text TEXT NOT NULL,
    condition_pattern TEXT,
    action_type TEXT,
    domain TEXT,
    source_event_id TEXT,
    evidence_count INTEGER DEFAULT 1,
    success_count INTEGER DEFAULT 0,
    fail_count INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending',
    proposed_by TEXT NOT NULL DEFAULT 'pattern_detector',
    reviewer_id TEXT,
    review_notes TEXT,
    created_at TEXT NOT NULL,
    reviewed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_rules_status ON proposed_rules(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_rules_domain ON proposed_rules(domain, status);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    trace_id TEXT,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    result TEXT,
    confidence REAL,
    metadata TEXT
);
CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_log(actor, ts DESC);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action, ts DESC);
CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit_log
BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END;
CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit_log
BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END;
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _migrate(conn: sqlite3.Connection) -> None:
    """Idempotent ALTER TABLE migrations for existing DBs."""
    cols = {row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()}
    if "password_hash" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
    if "api_token" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN api_token TEXT")

def get_db() -> sqlite3.Connection:
    """Singleton connection, thread-safe init."""
    global _conn
    if _conn is None:
        with _lock:
            if _conn is None:
                db_path = SETTINGS.data_dir / "sqlite" / "ai_employee.db"
                _conn = sqlite3.connect(str(db_path), check_same_thread=False)
                _conn.row_factory = sqlite3.Row
                _conn.executescript(SCHEMA)
                # migrations
                _migrate(_conn)
                _conn.commit()
    return _conn



def create_user(email: str, name: str, password: str, role: str = "user") -> Optional[dict]:
    """Create user with hash password. Returns user dict or None if email exists."""
    from core.auth import hash_password
    uid = str(uuid.uuid4())
    pw_hash = hash_password(password)
    try:
        cur = get_db().execute(
            "INSERT INTO users (id, email, name, role, password_hash) VALUES (?, ?, ?, ?, ?)",
            (uid, email, name, role, pw_hash),
        )
        get_db().commit()
        return get_user(uid)
    except sqlite3.IntegrityError:
        return None

def get_user(user_id: str) -> Optional[dict]:
    """Get user by ID."""
    row = get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if row:
        return dict(row)
    return None

def get_user_by_email(email: str) -> Optional[dict]:
    """Get user by email."""
    row = get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if row:
        return dict(row)
    return None

def authenticate_user(email: str, password: str) -> Optional[dict]:
    """Verify password, return user dict or None."""
    from core.auth import verify_password
    user = get_user_by_email(email)
    if user and user.get("password_hash") and verify_password(password, user["password_hash"]):
        return user
    return None

def list_users(limit: int = 50) -> list:
    """List all users."""
    rows = get_db().execute(
        "SELECT id, email, name, role, created_at FROM users ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]
def reset_db() -> None:
    """Xoa toan bo - chi dung cho test."""
    global _conn
    if _conn is not None:
        _conn.close()
        _conn = None
    db_path = SETTINGS.data_dir / "sqlite" / "ai_employee.db"
    if db_path.exists():
        db_path.unlink()


# ============ Task CRUD ============

def create_task(
    task_type: str,
    input_data: dict,
    user_id: str = "local",
    domain: Optional[str] = None,
    priority: int = 3,
) -> dict:
    task_id = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())
    now = _now()
    db = get_db()
    db.execute(
        """INSERT INTO tasks (id, user_id, task_type, domain, status, priority,
                             input_data, trace_id, created_at)
           VALUES (?, ?, ?, ?, 'pending', ?, ?, ?, ?)""",
        (task_id, user_id, task_type, domain, priority,
         json.dumps(input_data, ensure_ascii=False), trace_id, now),
    )
    db.commit()
    return {
        "id": task_id,
        "user_id": user_id,
        "task_type": task_type,
        "domain": domain,
        "status": "pending",
        "priority": priority,
        "input_data": input_data,
        "trace_id": trace_id,
        "created_at": now,
    }


def update_task(
    task_id: str,
    *,
    status: Optional[str] = None,
    plan: Optional[dict] = None,
    result: Optional[dict] = None,
    confidence: Optional[float] = None,
    error_message: Optional[str] = None,
) -> None:
    sets = []
    vals = []
    if status is not None:
        sets.append("status = ?")
        vals.append(status)
        if status in ("completed", "failed", "cancelled"):
            sets.append("completed_at = ?")
            vals.append(_now())
    if plan is not None:
        sets.append("plan = ?")
        vals.append(json.dumps(plan, ensure_ascii=False))
    if result is not None:
        sets.append("result = ?")
        vals.append(json.dumps(result, ensure_ascii=False))
    if confidence is not None:
        sets.append("confidence = ?")
        vals.append(confidence)
    if error_message is not None:
        sets.append("error_message = ?")
        vals.append(error_message)
    if not sets:
        return
    vals.append(task_id)
    db = get_db()
    db.execute(f"UPDATE tasks SET {', '.join(sets)} WHERE id = ?", vals)
    db.commit()


def get_task(task_id: str) -> Optional[dict]:
    db = get_db()
    row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not row:
        return None
    return _row_to_task(row)


def list_tasks(
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict], int]:
    db = get_db()
    where = []
    vals = []
    if status:
        where.append("status = ?")
        vals.append(status)
    if task_type:
        where.append("task_type = ?")
        vals.append(task_type)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    rows = db.execute(
        f"SELECT * FROM tasks {where_sql} ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (*vals, limit, offset),
    ).fetchall()
    total = db.execute(f"SELECT COUNT(*) AS n FROM tasks {where_sql}", vals).fetchone()["n"]
    return [_row_to_task(r) for r in rows], total


def _row_to_task(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "task_type": row["task_type"],
        "domain": row["domain"],
        "status": row["status"],
        "priority": row["priority"],
        "input_data": json.loads(row["input_data"]) if row["input_data"] else {},
        "plan": json.loads(row["plan"]) if row["plan"] else None,
        "result": json.loads(row["result"]) if row["result"] else None,
        "confidence": row["confidence"],
        "trace_id": row["trace_id"],
        "error_message": row["error_message"],
        "created_at": row["created_at"],
        "completed_at": row["completed_at"],
    }


# ============ Feedback ============

def create_feedback(
    task_id: str,
    score: int,
    notes: Optional[str] = None,
    corrections: Optional[dict] = None,
) -> dict:
    fb_id = str(uuid.uuid4())
    now = _now()
    db = get_db()
    db.execute(
        """INSERT INTO feedback (id, task_id, score, notes, corrections, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (fb_id, task_id, score, notes,
         json.dumps(corrections, ensure_ascii=False) if corrections else None, now),
    )
    db.commit()
    return {"id": fb_id, "task_id": task_id, "score": score, "notes": notes}


def list_feedback(task_id: str) -> list[dict]:
    db = get_db()
    rows = db.execute(
        "SELECT * FROM feedback WHERE task_id = ? ORDER BY created_at", (task_id,),
    ).fetchall()
    return [dict(r) for r in rows]


# ============ Approval ============

def create_approval(
    task_id: str,
    proposal: dict,
    risk_level: str,
    reason: Optional[str] = None,
) -> dict:
    ap_id = str(uuid.uuid4())
    now = _now()
    db = get_db()
    db.execute(
        """INSERT INTO approval_requests
           (id, task_id, proposal, risk_level, reason, decision, created_at)
           VALUES (?, ?, ?, ?, ?, 'pending', ?)""",
        (ap_id, task_id, json.dumps(proposal, ensure_ascii=False),
         risk_level, reason, now),
    )
    db.commit()
    return {"id": ap_id, "task_id": task_id, "proposal": proposal,
            "risk_level": risk_level, "reason": reason, "decision": "pending"}


def decide_approval(
    approval_id: str,
    decision: str,
    feedback: Optional[str] = None,
    approver_id: str = "local",
) -> Optional[dict]:
    if decision not in ("approved", "rejected", "modified"):
        raise ValueError(f"Invalid decision: {decision}")
    db = get_db()
    db.execute(
        """UPDATE approval_requests
           SET decision = ?, feedback = ?, approver_id = ?, decided_at = ?
           WHERE id = ? AND decision = 'pending'""",
        (decision, feedback, approver_id, _now(), approval_id),
    )
    db.commit()
    return get_approval(approval_id)


def get_approval(approval_id: str) -> Optional[dict]:
    db = get_db()
    row = db.execute(
        "SELECT * FROM approval_requests WHERE id = ?", (approval_id,),
    ).fetchone()
    if not row:
        return None
    return {
        "id": row["id"],
        "task_id": row["task_id"],
        "proposal": json.loads(row["proposal"]) if row["proposal"] else {},
        "risk_level": row["risk_level"],
        "reason": row["reason"],
        "decision": row["decision"],
        "feedback": row["feedback"],
        "approver_id": row["approver_id"],
        "decided_at": row["decided_at"],
        "created_at": row["created_at"],
    }


def list_pending_approvals() -> list[dict]:
    db = get_db()
    rows = db.execute(
        "SELECT * FROM approval_requests WHERE decision = 'pending' "
        "ORDER BY created_at DESC"
    ).fetchall()
    out = []
    for r in rows:
        out.append({
            "id": r["id"],
            "task_id": r["task_id"],
            "proposal": json.loads(r["proposal"]) if r["proposal"] else {},
            "risk_level": r["risk_level"],
            "reason": r["reason"],
            "decision": r["decision"],
            "created_at": r["created_at"],
        })
    return out


# ============ Trace ============

def record_span(
    trace_id: str,
    span_id: str,
    name: str,
    parent_span_id: Optional[str],
    start_time: str,
    end_time: Optional[str],
    duration_ms: Optional[float],
    attributes: Optional[dict],
    status: str,
) -> None:
    db = get_db()
    db.execute(
        """INSERT OR REPLACE INTO traces
           (trace_id, span_id, parent_span_id, name, start_time, end_time,
            duration_ms, attributes, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (trace_id, span_id, parent_span_id, name, start_time, end_time,
         duration_ms,
         json.dumps(attributes, ensure_ascii=False) if attributes else None,
         status),
    )
    db.commit()


def list_traces(trace_id: str) -> list[dict]:
    db = get_db()
    rows = db.execute(
        "SELECT * FROM traces WHERE trace_id = ? ORDER BY start_time", (trace_id,),
    ).fetchall()
    out = []
    for r in rows:
        out.append({
            "trace_id": r["trace_id"],
            "span_id": r["span_id"],
            "parent_span_id": r["parent_span_id"],
            "name": r["name"],
            "start_time": r["start_time"],
            "end_time": r["end_time"],
            "duration_ms": r["duration_ms"],
            "attributes": json.loads(r["attributes"]) if r["attributes"] else None,
            "status": r["status"],
        })
    return out


# ============ Skill metadata ============

def upsert_skill(
    skill_name: str,
    domain: Optional[str] = None,
    success: bool = True,
) -> None:
    db = get_db()
    row = db.execute(
        "SELECT * FROM skill_metadata WHERE skill_name = ?", (skill_name,),
    ).fetchone()
    if row is None:
        db.execute(
            """INSERT INTO skill_metadata
               (id, skill_name, domain, success_count, fail_count, sample_size,
                success_rate, status, last_used_at)
               VALUES (?, ?, ?, ?, ?, 1, ?, 'active', ?)""",
            (str(uuid.uuid4()), skill_name, domain,
             1 if success else 0, 0 if success else 1,
             1.0 if success else 0.0, _now()),
        )
    else:
        new_succ = row["success_count"] + (1 if success else 0)
        new_fail = row["fail_count"] + (0 if success else 1)
        sample = new_succ + new_fail
        rate = new_succ / sample if sample else 0.0
        new_status = "disabled" if (sample >= 20 and rate < 0.5) else row["status"]
        db.execute(
            """UPDATE skill_metadata
               SET success_count = ?, fail_count = ?, sample_size = ?,
                   success_rate = ?, status = ?, last_used_at = ?
               WHERE skill_name = ?""",
            (new_succ, new_fail, sample, rate, new_status, _now(), skill_name),
        )
    db.commit()

# ============ Proposed rules (HUMAN GATE) ============

def create_proposed_rule(
    rule_text: str,
    condition_pattern: Optional[str] = None,
    action_type: Optional[str] = None,
    domain: Optional[str] = None,
    source_event_id: Optional[str] = None,
    proposed_by: str = "pattern_detector",
) -> dict:
    rule_id = str(uuid.uuid4())
    now = _now()
    db = get_db()
    db.execute(
        """INSERT INTO proposed_rules
           (id, rule_text, condition_pattern, action_type, domain, source_event_id,
            evidence_count, status, proposed_by, created_at)
           VALUES (?, ?, ?, ?, ?, ?, 1, 'pending', ?, ?)""",
        (rule_id, rule_text, condition_pattern, action_type, domain,
         source_event_id, proposed_by, now),
    )
    db.commit()
    return {
        "id": rule_id,
        "rule_text": rule_text,
        "condition_pattern": condition_pattern,
        "action_type": action_type,
        "domain": domain,
        "source_event_id": source_event_id,
        "evidence_count": 1,
        "status": "pending",
        "proposed_by": proposed_by,
        "created_at": now,
    }

def list_proposed_rules(
    status: Optional[str] = None,
    domain: Optional[str] = None,
    limit: int = 50,
) -> list[dict]:
    db = get_db()
    where, vals = [], []
    if status:
        where.append("status = ?")
        vals.append(status)
    if domain:
        where.append("domain = ?")
        vals.append(domain)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    rows = db.execute(
        f"""SELECT * FROM proposed_rules {where_sql}
            ORDER BY created_at DESC LIMIT ?""",
        (*vals, limit),
    ).fetchall()
    return [dict(r) for r in rows]

def get_proposed_rule(rule_id: str) -> Optional[dict]:
    db = get_db()
    row = db.execute(
        "SELECT * FROM proposed_rules WHERE id = ?", (rule_id,),
    ).fetchone()
    return dict(row) if row else None

def decide_proposed_rule(
    rule_id: str,
    decision: str,
    reviewer_id: str = "local",
    review_notes: Optional[str] = None,
) -> Optional[dict]:
    """Approve / reject rule. Decision: approved | rejected."""
    if decision not in ("approved", "rejected"):
        raise ValueError(f"Invalid decision: {decision}")
    db = get_db()
    db.execute(
        """UPDATE proposed_rules
           SET status = ?, reviewer_id = ?, review_notes = ?, reviewed_at = ?
           WHERE id = ? AND status = 'pending'""",
        (decision, reviewer_id, review_notes, _now(), rule_id),
    )
    db.commit()
    return get_proposed_rule(rule_id)

def record_rule_outcome(rule_id: str, success: bool) -> None:
    """Sau khi rule duoc apply, ghi outcome de auto-disable neu fail > 50%."""
    db = get_db()
    row = db.execute(
        "SELECT * FROM proposed_rules WHERE id = ?", (rule_id,),
    ).fetchone()
    if not row:
        return
    new_succ = row["success_count"] + (1 if success else 0)
    new_fail = row["fail_count"] + (0 if success else 1)
    sample = new_succ + new_fail
    rate = new_succ / sample if sample else 0.0
    new_status = row["status"]
    if row["status"] == "approved" and sample >= 20 and rate < 0.5:
        new_status = "auto_disabled"
    db.execute(
        """UPDATE proposed_rules
           SET success_count = ?, fail_count = ?, evidence_count = ?
           WHERE id = ?""",
        (new_succ, new_fail, sample, rule_id),
    )
    if new_status != row["status"]:
        db.execute("UPDATE proposed_rules SET status = ? WHERE id = ?", (new_status, rule_id))
    db.commit()

# ============ Learning events ============

def create_learning_event(
    event_type: str,
    task_id: Optional[str] = None,
    feedback_id: Optional[str] = None,
    before_state: Optional[dict] = None,
    after_state: Optional[dict] = None,
    rule_extracted: Optional[str] = None,
) -> dict:
    ev_id = str(uuid.uuid4())
    now = _now()
    db = get_db()
    db.execute(
        """INSERT INTO learning_events
           (id, task_id, feedback_id, event_type, before_state, after_state,
            rule_extracted, status, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)""",
        (ev_id, task_id, feedback_id, event_type,
         json.dumps(before_state, ensure_ascii=False) if before_state else None,
         json.dumps(after_state, ensure_ascii=False) if after_state else None,
         rule_extracted, now),
    )
    db.commit()
    return {"id": ev_id, "event_type": event_type, "status": "pending"}

def list_learning_events(
    event_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
) -> list[dict]:
    db = get_db()
    where, vals = [], []
    if event_type:
        where.append("event_type = ?")
        vals.append(event_type)
    if status:
        where.append("status = ?")
        vals.append(status)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    rows = db.execute(
        f"""SELECT * FROM learning_events {where_sql}
            ORDER BY created_at DESC LIMIT ?""",
        (*vals, limit),
    ).fetchall()
    out = []
    for r in rows:
        out.append({
            "id": r["id"],
            "task_id": r["task_id"],
            "feedback_id": r["feedback_id"],
            "event_type": r["event_type"],
            "before_state": json.loads(r["before_state"]) if r["before_state"] else None,
            "after_state": json.loads(r["after_state"]) if r["after_state"] else None,
            "rule_extracted": r["rule_extracted"],
            "status": r["status"],
            "created_at": r["created_at"],
        })
    return out


# ============ Audit log ============

def log_action(actor: str, action: str, result: str = "ok", trace_id: Optional[str] = None,
               confidence: Optional[float] = None, metadata: Optional[dict] = None) -> int:
    """Append-only audit log entry. Returns row id."""
    db = get_db()
    cur = db.execute(
        "INSERT INTO audit_log (trace_id, actor, action, result, confidence, metadata) VALUES (?, ?, ?, ?, ?, ?)",
        (trace_id, actor, action, result, confidence,
         json.dumps(metadata, ensure_ascii=False) if metadata else None),
    )
    db.commit()
    return cur.lastrowid

def list_audit_log(actor: Optional[str] = None, action: Optional[str] = None,
                   limit: int = 100) -> list[dict]:
    """Get audit log entries, newest first."""
    db = get_db()
    where, vals = [], []
    if actor:
        where.append("actor = ?")
        vals.append(actor)
    if action:
        where.append("action = ?")
        vals.append(action)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    rows = db.execute(
        f"SELECT * FROM audit_log {where_sql} ORDER BY ts DESC LIMIT ?",
        (*vals, limit),
    ).fetchall()
    out = []
    for r in rows:
        row = dict(r)
        if row.get("metadata"):
            try:
                row["metadata"] = json.loads(row["metadata"])
            except (json.JSONDecodeError, TypeError):
                pass
        out.append(row)
    return out
