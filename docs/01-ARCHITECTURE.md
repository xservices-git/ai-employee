# Architecture

## 1 orchestrator + 3 tang memory + MCP tools

```
┌──────────────────────────────────────────────────────────────────┐
│  TANG 0: NGUOI DUNG                                              │
│  Chat / Dashboard / Approval Center                              │
└────────────────────────────────┬─────────────────────────────────┘
                                 │ REST + WebSocket
┌────────────────────────────────▼─────────────────────────────────┐
│  TANG 1: WEB UI (Next.js 15)                                     │
│  Chat / Task Dashboard / Approval Queue / Trace Viewer           │
└────────────────────────────────┬─────────────────────────────────┘
                                 │ REST (OpenAPI)
┌────────────────────────────────▼─────────────────────────────────┐
│  TANG 2: ORCHESTRATOR (Python 3.12 + FastAPI)                    │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  STATE MACHINE (1 process, 5 buoc)                          │ │
│  │  classify -> plan -> execute -> review -> store             │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  + Confidence Scoring (5 chi so)                                 │
│  + 3 lop Safety (input/plan/output filter)                       │
│  + Approval Workflow (high/critical risk)                        │
└────────────────────────────────┬─────────────────────────────────┘
                                 │ MCP JSON-RPC
         ┌───────────────────────┼───────────────────────┐
┌────────▼─────────┐  ┌─────────▼──────────┐  ┌────────▼─────────┐
│ TANG 3A: MODEL   │  │ TANG 3B: MEMORY    │  │ TANG 3C: TOOLS  │
│ Ollama local     │  │ ChromaDB + SQLite  │  │ MCP servers     │
│ 4B: classify,    │  │ episodic + semantic│  │ data, comms,    │
│     plan, exec   │  │ + procedural (YAML)│  │ file, sched,    │
│ 8B: review       │  │                    │  │ web-research    │
└──────────────────┘  └────────────────────┘  └──────────────────┘
```

## State machine (5 buoc, 1 process)

Thay vi 5 agents rieng (overhead), dung 1 orchestrator voi 5 buoc lien tiep:

```python
async def run_task(task: Task) -> Task:
    # Buoc 1: Classify (4B, 500ms)
    task.task_type = await classify(task.input)
    task.domain = detect_domain(task.input)

    # Buoc 2: Plan (8B, 1-2s)
    plan = await plan(task, memory_context)
    task.confidence = calculate_confidence(plan)

    # Buoc 3: Approval gate (neu confidence < 0.7 hoac risk >= high)
    if needs_approval(task):
        task = await wait_for_approval(task)

    # Buoc 4: Execute (4B, 2-10s)
    result = await execute(plan)

    # Buoc 5: Review (8B, 1-2s)
    review = await review(result)
    if review.score < 0.5:
        result = await retry_with_feedback(result, review.issues)

    # Async: Store memory (khong block)
    asyncio.create_task(store_episode(task, result, review))

    return task
```

**Ly do 1 orchestrator thay vi 5 agents:**
- 5 agents = 5 process + message bus + 5x memory load = CHAM va PHUC TAP
- 1 orchestrator = 1 process, de debug, de test, nhanh hon
- Neu can scale: spawn nhieu orchestrator cho nhieu task (khong phai 5 agents/instance)

## Confidence scoring (5 chi so)

```
confidence = familiarity x 0.30
           + clarity      x 0.20
           + risk_score   x 0.25
           + similarity   x 0.15
           + simplicity   x 0.10
```

Chi tiet xem `specs/02-CONFIDENCE.md`.

## Safety (3 lop)

### Layer 1: Input filter
- Prompt injection detection (regex + heuristic)
- PII detection + mask
- Rate limit (100 req/h/user)

### Layer 2: Plan validator
- Action whitelist
- Risk-class matching (tool risk vs confidence)
- Resource limit (token, time, cost)

### Layer 3: Output filter
- PII leak detection
- Hallucination scoring (Critic)
- Format validation

Chi tiet xem `specs/03-SAFETY.md`.

## Memory 3 tang

### Tang 1: Episodic (SQLite)
- Moi task = 1 row trong `tasks` table
- Metadata: task_type, domain, user_id, confidence, success
- Query: filter theo user, task_type, success rate

### Tang 2: Semantic (ChromaDB)
- Embedding cua input + output + feedback
- Collection: `episodic_memory`, `semantic_memory`
- Query: cosine similarity, top-k

### Tang 3: Procedural (YAML)
- File `domain_configs/{domain}/rules.yaml`
- Moi rule: trigger_keywords, action, example, success_rate, sample_size
- HUMAN tao + HUMAN approve rule moi (KHONG auto-promote)

## Learning loop (HUMAN GATE)

```
Task chay -> Outcome (success/fail)
    |
    v
Feedback thu thap (auto implicit + user explicit)
    |
    v
Weekly cron: pattern detection
    |
    v
AI propose rules moi (status=PENDING)
    |
    v
HUMAN review qua UI
    |
    v
HUMAN approve -> rule active
    |
    v
Shadow mode 1 tuan
    |
    v
HUMAN promote len main
```

**Quan trong:** AI KHONG BAO GIO tu promote rule production. Moi rule can:
- 1 PR voi description + example
- Human test tren 5 cases
- Human approve

**Toc do thuc te:** 5-10 rules moi / thang (khong phai tu dong hoan toan).

## Observability

### Trace (OpenTelemetry-compatible)
- Moi task co `trace_id`
- Span cho moi buoc: classify, plan, execute, review, store
- Luu vao `traces` table, dashboard xem lai

### Metrics (Prometheus)
- `tasks_total{task_type, status}` counter
- `task_duration_seconds` histogram
- `confidence_score` histogram
- `approval_required_total` counter

Chi tiet xem `specs/04-OBSERVABILITY.md`.

## Tech stack (toi gian)

### Backend
- **Python 3.12** + FastAPI + uvicorn
- **SQLite** (1M records du, backup don gian)
- **ChromaDB** (local, persistent, khong can server)
- **Ollama** (4B + 8B + nomic-embed)
- **httpx** (async HTTP)
- **structlog** (JSON log)
- **pytest** + ruff + mypy

### Frontend
- **Next.js 15** + TypeScript + Tailwind 4
- **shadcn/ui** + zustand + tanstack-query

### Container
- **Docker Compose** (KHONG K8s, KHONG Helm)
- Volumes: `./data:/data` (SQLite + ChromaDB + Ollama)

### KHONG dung
- LangChain (black box, version hell)
- LlamaIndex (tuong tu)
- Pinecone, Weaviate (ChromaDB du)
- Redis (chua can)
- Kubernetes (qua nang cho SME)
- MongoDB (SQLite du)
- OpenAI API (vendor lock-in)
