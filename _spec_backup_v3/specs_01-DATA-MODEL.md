# Data Model

## SQLite Schema (v1)

### ERD

```
┌─────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   users     │      │      tasks       │      │ approval_reqs   │
├─────────────┤      ├──────────────────┤      ├─────────────────┤
│ id (PK)     │◄────┤ user_id (FK)     │◄────┤ task_id (FK)    │
│ email       │      │ id (PK)          │      │ id (PK)         │
│ name        │      │ task_type        │      │ proposal (JSON) │
│ role        │      │ domain           │      │ risk_level      │
│ created_at  │      │ status           │      │ reason          │
└─────────────┘      │ priority         │      │ precedents(JSON)│
                     │ input_data (JSON)│      │ decision        │
                     │ plan (JSON)      │      │ modified_by     │
                     │ result (JSON)    │      │ feedback        │
                     │ confidence       │      │ created_at      │
                     │ trace_id         │      │ decided_at      │
                     │ created_at       │      └─────────────────┘
                     │ completed_at     │
                     │ feedback_id (FK) │◄────┐
                     └────────┬─────────┘     │
                              │               │
                              ▼               │
                     ┌──────────────────┐     │
                     │   feedback       │     │
                     ├──────────────────┤     │
                     │ id (PK)          │─────┘
                     │ task_id (FK)     │
                     │ score (1-5)      │
                     │ notes            │
                     │ corrections(JSON)│
                     │ tags (JSON)      │
                     │ created_at       │
                     └────────┬─────────┘
                              │
                              ▼
                     ┌──────────────────┐
                     │ learning_events  │
                     ├──────────────────┤
                     │ id (PK)          │
                     │ task_id (FK)     │
                     │ event_type       │
                     │ before_state     │
                     │ after_state      │
                     │ rule_extracted   │
                     │ applied          │
                     │ created_at       │
                     └──────────────────┘

┌──────────────────┐      ┌──────────────────┐
│ skill_defs       │      │ audit_log        │
├──────────────────┤      ├──────────────────┤
│ id (PK)          │      │ id (PK)          │
│ skill_name       │      │ ts               │
│ domain           │      │ trace_id         │
│ task_types (JSON)│      │ actor            │
│ trigger (JSON)   │      │ action           │
│ steps (JSON)     │      │ result           │
│ confidence       │      │ confidence       │
│ version          │      │ approver         │
│ success_rate     │      │ metadata (JSON)  │
│ created_from     │      └──────────────────┘
│ updated_at       │
└──────────────────┘
```

## DDL

```sql
-- users
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('admin', 'approver', 'user')),
    password_hash TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);

-- tasks
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    task_type TEXT NOT NULL,
    domain TEXT,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'running', 'waiting_approval',
                          'completed', 'failed', 'cancelled')),
    priority INTEGER DEFAULT 3 CHECK (priority BETWEEN 1 AND 5),
    input_data JSON NOT NULL,
    plan JSON,
    result JSON,
    confidence REAL CHECK (confidence BETWEEN 0 AND 1),
    trace_id TEXT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    feedback_id TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (feedback_id) REFERENCES feedback(id)
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
    precedents JSON,
    decision TEXT DEFAULT 'pending'
        CHECK (decision IN ('pending', 'approved', 'rejected', 'modified')),
    modified_by TEXT,
    modified_args JSON,
    feedback TEXT,
    approver_id TEXT,
    decided_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id),
    FOREIGN KEY (approver_id) REFERENCES users(id)
);

CREATE INDEX idx_approvals_task ON approval_requests(task_id);
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
        'mistake_correction', 'approval_learned', 'skill_created',
        'skill_promoted', 'skill_demoted', 'rule_added'
    )),
    before_state JSON,
    after_state JSON,
    rule_extracted TEXT,
    applied BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id),
    FOREIGN KEY (feedback_id) REFERENCES feedback(id)
);

CREATE INDEX idx_learning_task ON learning_events(task_id);
CREATE INDEX idx_learning_type ON learning_events(event_type, created_at);

-- skill_definitions
CREATE TABLE skill_definitions (
    id TEXT PRIMARY KEY,
    skill_name TEXT NOT NULL,
    domain TEXT,
    task_types JSON NOT NULL,
    trigger JSON,
    steps JSON NOT NULL,
    confidence REAL DEFAULT 0.7,
    version INTEGER DEFAULT 1,
    success_rate REAL DEFAULT 0.0,
    usage_count INTEGER DEFAULT 0,
    created_from TEXT CHECK (created_from IN ('manual', 'learned')),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (skill_name, version)
);

CREATE INDEX idx_skills_domain ON skill_definitions(domain);
CREATE INDEX idx_skills_success ON skill_definitions(success_rate DESC);

-- audit_log (append-only, không UPDATE/DELETE)
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    trace_id TEXT,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    result TEXT,
    confidence REAL,
    approver TEXT,
    metadata JSON
);

CREATE INDEX idx_audit_ts ON audit_log(ts DESC);
CREATE INDEX idx_audit_trace ON audit_log(trace_id);

-- Trigger ngăn UPDATE/DELETE trên audit_log
CREATE TRIGGER audit_log_no_update
BEFORE UPDATE ON audit_log
BEGIN
    SELECT RAISE(ABORT, 'audit_log is append-only');
END;

CREATE TRIGGER audit_log_no_delete
BEFORE DELETE ON audit_log
BEGIN
    SELECT RAISE(ABORT, 'audit_log is append-only');
END;
```

## ChromaDB Collections

### episodic_memory
- **ID format:** `{user_id}:{task_id}:{step_id}`
- **Embedding:** nomic-embed-text v1.5 (768 dim)
- **Metadata:**
  ```json
  {
    "user_id": "uuid",
    "task_id": "uuid",
    "task_type": "data_processing",
    "domain": "sales",
    "input_summary": "Query orders > $1000 last month",
    "result_summary": "Found 23 orders, total $45k",
    "success": true,
    "duration_ms": 2100,
    "date": "2026-07-19",
    "tools_used": ["query_db"],
    "confidence": 0.85
  }
  ```
- **Document:** Concatenated text của input + plan + result, max 2000 chars

### semantic_memory
- **ID format:** `{topic_hash}`
- **Metadata:**
  ```json
  {
    "topic": "VIP customer response time",
    "rule": "VIP customers must be responded within 2h",
    "evidence_count": 15,
    "confidence": 0.92,
    "last_validated": "2026-07-15"
  }
  ```
- **Document:** Rule text + examples

### procedural_memory
- **ID format:** `{skill_id}:v{version}`
- **Metadata:**
  ```json
  {
    "skill_id": "uuid",
    "skill_name": "handle_complaint",
    "domain": "customer_support",
    "success_rate": 0.88,
    "usage_count": 142,
    "trigger_pattern": "khách hàng phàn nàn|khiếu nại|refund"
  }
  ```
- **Document:** Skill name + steps summary

### approval_history
- **ID format:** `{approval_id}`
- **Metadata:**
  ```json
  {
    "task_id": "uuid",
    "task_type": "data_processing",
    "domain": "sales",
    "tool_name": "send_email",
    "risk_level": "high",
    "decision": "approved",
    "modified": false,
    "user_id": "uuid",
    "approver_id": "uuid"
  }
  ```
- **Document:** Reason + decision + feedback (text)

## Migration strategy

Dùng Alembic:

```bash
# Tạo migration mới
alembic revision --autogenerate -m "add audit_log"

# Apply
alembic upgrade head

# Rollback
alembic downgrade -1
```

Migrations nằm trong `core/common/migrations/`.

## Index strategy

- **Hot indexes:** `(user_id, status)`, `(created_at DESC)`, `(trace_id)`
- **Composite cho query phổ biến:** `(domain, task_type, status)`
- **Full-text search:** dùng FTS5 cho tasks.input_data nếu cần
- **Vector indexes:** ChromaDB tự quản lý (HNSW default)

## Backup strategy

- **Hot backup:** `sqlite3 .backup` mỗi 6h
- **Cold backup:** snapshot thư mục `data/` mỗi ngày
- **Retention:** 7 daily, 4 weekly, 12 monthly
- **Encrypt:** at-rest với age hoặc gpg
- **Offsite:** upload lên S3/MinIO sau khi encrypt
