# Data Model

## SQLite Schema (v1 - toi gian)

### ERD

```
users ----< tasks ----< feedback
              |
              +----< approval_requests
              |
              +----< learning_events

skill_definitions (YAML, khong luu DB - chi metadata trong DB)
audit_log (append-only)
```

## DDL

```sql
-- users (toi gian, M3 moi can auth)
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    password_hash TEXT NOT NULL,  -- pbkdf2_sha256$<salt_b64>$<hash_b64> (core/auth.py)
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('admin', 'approver', 'user')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);
CREATE INDEX idx_users_email ON users(email);

-- tasks (TAM CHINH)
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    task_type TEXT NOT NULL,
    domain TEXT,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'running', 'waiting_approval',
                          'completed', 'failed', 'cancelled')),
    priority INTEGER DEFAULT 3,
    input_data JSON NOT NULL,
    plan JSON,
    result JSON,
    confidence REAL,
    trace_id TEXT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE INDEX idx_tasks_user_status ON tasks(user_id, status);
CREATE INDEX idx_tasks_created ON tasks(created_at DESC);
CREATE INDEX idx_tasks_trace ON tasks(trace_id);

-- approval_requests
CREATE TABLE approval_requests (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    proposal JSON NOT NULL,
    risk_level TEXT NOT NULL CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    reason TEXT,
    decision TEXT DEFAULT 'pending'
        CHECK (decision IN ('pending', 'approved', 'rejected', 'modified')),
    modified_args JSON,
    feedback TEXT,
    approver_id TEXT,
    decided_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);
CREATE INDEX idx_approvals_status ON approval_requests(decision, created_at);

-- feedback
CREATE TABLE feedback (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    score INTEGER NOT NULL CHECK (score BETWEEN 1 AND 5),
    notes TEXT,
    corrections JSON,
    tags JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);
CREATE INDEX idx_feedback_task ON feedback(task_id);

-- learning_events
CREATE TABLE learning_events (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    feedback_id TEXT,
    event_type TEXT NOT NULL CHECK (event_type IN (
        'mistake_correction', 'approval_learned',
        'rule_proposed', 'rule_approved', 'rule_rejected'
    )),
    before_state JSON,
    after_state JSON,
    rule_extracted TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

-- traces (OpenTelemetry-compatible)
CREATE TABLE traces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trace_id TEXT NOT NULL,
    span_id TEXT NOT NULL,
    parent_span_id TEXT,
    name TEXT NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_ms REAL,
    attributes JSON,
    status TEXT,
    UNIQUE(trace_id, span_id)
);
CREATE INDEX idx_traces_trace ON traces(trace_id);

-- audit_log (append-only)
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    trace_id TEXT,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    result TEXT,
    confidence REAL,
    metadata JSON
);
-- Trigger: khong cho UPDATE/DELETE
CREATE TRIGGER audit_no_update BEFORE UPDATE ON audit_log
BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END;
CREATE TRIGGER audit_no_delete BEFORE DELETE ON audit_log
BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END;
```

## ChromaDB Collections

### Collection 1: episodic_memory
- Moi task thanh cong/fail = 1 chunk
- Metadata: `task_type`, `domain`, `user_id`, `success`, `confidence`, `date`
- Query: top-k cosine similarity

### Collection 2: semantic_memory
- Patterns rut ra tu nhieu episode
- Vi du: "User lam viec voi TikTok Shop, gap van de 12052093"
- Metadata: `domain`, `pattern_type`, `source_episodes`

### Collection 3: approval_history
- Moi approval decision (approve/reject)
- De predict risk cho task tuong lai

## Procedural Memory (YAML, KHONG luu DB)

Moi rule la 1 entry trong file YAML:

```yaml
# domain_configs/stuvia/rules.yaml
domain: stuvia
version: 1
rules:
  - id: stuvia_resolve_file
    description: "Resolve file URL cho Stuvia upload"
    trigger_keywords: ["stuvia", "upload pdf", "auto_gen"]
    condition: "gen_mode == 'auto_gen'"
    action: "pushTool/stuvia.py::_resolve_file()"
    example: |
      Input: gen_mode=auto_gen, product_id=123
      Action: Dung Demo File (pdf_url), khong phai local_file_url
    source: manual
    created_at: 2026-07-19
    success_count: 47
    fail_count: 3
    success_rate: 0.94
    sample_size: 50
    status: active  # active | shadow | disabled
```

**Status:**
- `active`: dang dung trong production
- `shadow`: log nhung khong apply (test truoc khi active)
- `disabled`: fail nhieu, can review

**Metadata trong DB** (de query nhanh):

```sql
-- skill_metadata (chua stats, khong chua noi dung rule)
CREATE TABLE skill_metadata (
    id TEXT PRIMARY KEY,
    skill_name TEXT NOT NULL,
    domain TEXT,
    success_rate REAL,
    sample_size INTEGER,
    status TEXT,
    last_used_at TIMESTAMP,
    UNIQUE(skill_name)
);
```

Noi dung rule giu trong YAML file (de diff, review, human edit).

## Migration (Alembic)

Moi thay doi schema dung Alembic:

```bash
# Tao migration
alembic revision --autogenerate -m "add skill_metadata table"

# Apply
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Bo sung tu spec cu

**Loai bo (khong can thuc te):**
- A2A message bus (1 orchestrator, khong can protocol)
- Planner/Executor/Critic rieng (gop vao 1 state machine)
- Memory Curator agent (gop vao store_episode)
- Supervisor agent (gop vao approval gate)

**Giu lai:**
- users, tasks, feedback, approval_requests, audit_log
- learning_events (co them rule_proposed status)
- traces table (cho observability)
