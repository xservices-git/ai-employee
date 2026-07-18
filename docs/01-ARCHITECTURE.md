# Architecture

## 4 tầng + 5 agents

```
┌──────────────────────────────────────────────────────────────────┐
│  TẦNG 0: NGƯỜI DÙNG                                              │
│  Chat / Voice / Email / Dashboard / Approval Center              │
└────────────────────────────────┬─────────────────────────────────┘
                                 │ REST + WebSocket
┌────────────────────────────────▼─────────────────────────────────┐
│  TẦNG 1: GIAO DIỆN (Next.js - Open WebUI fork)                   │
│  Chat / Approval Queue / Task Dashboard / Trace Viewer           │
└────────────────────────────────┬─────────────────────────────────┘
                                 │ REST (OpenAPI)
┌────────────────────────────────▼─────────────────────────────────┐
│  TẦNG 2: ĐIỀU PHỐI (PicoClaw - Go + Python)                     │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  ORCHESTRATOR (state machine)                               │ │
│  │  Classifier → Planner → Executor → Critic → Memory Curator │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────┐│
│  │ PLANNER 8B   │ │ EXECUTOR 4B │ │ CRITIC 8B    │ │ SUPERVISOR││
│  │ • lập kế hoạch│ │ • gọi tool  │ │ • review     │ │ • phê duyệt││
│  └──────────────┘ └──────┬───────┘ └──────────────┘ └──────────┘│
│                          │                                        │
│  ┌───────────────────────▼──────────────────────────────────────┐│
│  │  TOOL SELECTOR (MCP Registry)                                ││
│  │  Risk-aware: low → auto, high → approval                    ││
│  └──────────────────────────────────────────────────────────────┘│
└────────────────────────────────┬─────────────────────────────────┘
                                 │ MCP protocol (JSON-RPC)
         ┌───────────────────────┼───────────────────────┐
┌────────▼─────────┐  ┌─────────▼──────────┐  ┌────────▼─────────┐
│ TẦNG 3A: MODEL   │  │ TẦNG 3B: MEMORY    │  │ TẦNG 3C: TOOLS  │
│ Ollama local     │  │ ChromaDB + SQLite  │  │ MCP servers     │
│ • 4B: tool call  │  │ • episodic         │  │ • data          │
│ • 8B: reasoning  │  │ • semantic         │  │ • communication │
│ • embed: nomic   │  │ • procedural       │  │ • file-ops      │
│ • rerank: bge    │  │ • approval history │  │ • scheduling    │
└──────────────────┘  └────────────────────┘  │ • web-research  │
                                              └──────────────────┘
```

## 5 agents (multi-agent cải tiến)

### 1. Classifier
- **Model:** LLM 4B (Qwen 2.5)
- **Nhiệm vụ:** Phân loại input → 1 trong 7 task types
- **Input:** raw user message
- **Output:** `{task_type, domain, confidence}`
- **Latency target:** < 500ms

### 2. Planner
- **Model:** LLM 8B (Llama 3.1)
- **Nhiệm vụ:** Phân tích yêu cầu, lập kế hoạch các bước
- **Input:** task + memory context
- **Output:** `{steps: [{action, tool, args, expected_result}]}`
- **Có thể chia task phụ** nếu quá phức tạp

### 3. Executor
- **Model:** LLM 4B (Qwen 2.5)
- **Nhiệm vụ:** Gọi MCP tool, xử lý response
- **Input:** 1 step từ Planner
- **Output:** tool result
- **Retry:** 3 lần với backoff 1s/3s/7s

### 4. Critic
- **Model:** LLM 8B (Mistral)
- **Nhiệm vụ:** Review output của Executor
- **Kiểm tra:**
  - Có đúng yêu cầu không
  - Có hallucination không
  - Có PII leak không
  - Có vi phạm policy không
- **Output:** `{approved: bool, score: 0-1, issues: [...]}`

### 5. Memory Curator
- **Model:** LLM 4B
- **Nhiệm vụ:** Cập nhật long-term memory sau task
- **Extract:**
  - Episodic: lưu task + result
  - Semantic: extract patterns
  - Procedural: promote skill nếu success cao
- **Chạy async** sau khi task done

## A2A Protocol (Agent-to-Agent)

Agents trao đổi qua message format chuẩn:

```json
{
  "trace_id": "uuid",
  "from": "planner",
  "to": "executor",
  "type": "request",
  "action": "execute_step",
  "payload": {
    "step_id": 2,
    "tool": "query_db",
    "args": {"sql": "SELECT * FROM orders WHERE id = 123"}
  },
  "context": {
    "task_id": "uuid",
    "user_id": "uuid",
    "domain": "sales"
  },
  "deadline_ms": 5000
}
```

Mọi message đều có `trace_id` để debug xuyên suốt.

## Hierarchical Memory (3 tầng + 1 layer)

### Working memory
- Context hiện tại của task
- Lưu trong RAM, clear khi task xong
- Schema: `{task_id, plan, current_step, intermediate_results}`

### Episodic memory
- "Task X tôi đã làm, kết quả Y"
- ChromaDB collection `episodic`
- Metadata: `{task_type, domain, date, success, user_id}`

### Semantic memory
- Kiến thức chung rút ra từ nhiều episode
- ChromaDB collection `semantic`
- Ví dụ: "Khách hàng VIP cần respond trong 2h"

### Procedural memory
- Skill definitions
- SQLite table `skill_definitions`
- Promote/demote dựa trên success rate

### Approval history
- Tất cả approval decisions
- ChromaDB collection `approval_history`
- Dùng để predict risk cho task tương lai

## Confidence Scoring

5 chỉ số có trọng số, xem chi tiết `specs/02-CONFIDENCE-SCORING.md`.

```
confidence = familiarity × 0.30
           + clarity × 0.20
           + risk × 0.25
           + similarity × 0.15
           + complexity × 0.10
```

- ≥ 0.70: auto-execute
- 0.40-0.69: request approval
- < 0.40: reject hoặc clarify

## Safety (3 lớp)

### Layer 1: Input filter
- Detect prompt injection
- Strip PII nếu là test
- Reject nếu rate limit vượt

### Layer 2: Plan validator
- Kiểm tra plan có vi phạm policy không
- Kiểm tra tool call có hợp lệ không
- Kiểm tra risk level có khớp với confidence không

### Layer 3: Output filter
- Detect PII leak
- Fact-check (nếu có thể)
- Kiểm tra có chứa "injection attempt" không

## Observability

### Trace format (OpenTelemetry-compatible)
```
trace_id: abc-123
├─ span: classify (50ms)
├─ span: plan (1200ms)
│  └─ span: retrieve_memory (180ms)
│     └─ span: vector_search (45ms)
│     └─ span: rerank (95ms)
├─ span: execute_step_1 (210ms)
├─ span: execute_step_2 (340ms)
├─ span: critic (450ms)
└─ span: memory_update (200ms)
```

### Metrics (Prometheus)
- `tasks_total{task_type, domain, status}` counter
- `task_duration_seconds` histogram
- `confidence_score` histogram
- `approval_required_total` counter
- `tool_call_total{tool, status}` counter
- `memory_retrieval_duration_seconds` histogram

### Logs (structured JSON)
```json
{
  "ts": "2026-07-19T02:30:00Z",
  "level": "info",
  "trace_id": "abc-123",
  "task_id": "xyz-789",
  "agent": "executor",
  "event": "tool_call",
  "tool": "query_db",
  "duration_ms": 210,
  "result": "success"
}
```

## Công nghệ

| Layer | Tech | Lý do |
|---|---|---|
| API gateway | FastAPI (Python 3.12) | Async, type-safe, OpenAPI tự sinh |
| Orchestrator | Python (chính) + Go (critical path) | Ecosystem AI tốt + perf cho state machine |
| LLM serving | Ollama | Local, OpenAI-compatible API |
| Vector DB | ChromaDB | Local, persistent, đơn giản |
| RDB | SQLite | Embedded, không cần server |
| Web | Next.js 15 + TypeScript | SSR, fast refresh, ecosystem |
| MCP servers | Python + JSON-RPC | Đơn giản, dễ extend |
| Tracing | OpenTelemetry SDK | Industry standard |
| Metrics | Prometheus client | De facto |
| Container | Docker + Compose | Dev đơn giản |
| Deploy | Docker Swarm hoặc K3s | Single-node đủ cho SME |

## Cải tiến sâu so với bản gốc

| Khía cạnh | Bản gốc | V3.0 |
|---|---|---|
| Orchestration | 1 loop tuần tự | 5 agents song song, A2A protocol |
| Memory | 2 tầng | 3 tầng + 1 layer (procedural + approval) |
| Learning | Không | Self-improving với Memory Curator |
| Tracing | Không | OpenTelemetry + dashboard |
| Safety | 1 threshold | 3 lớp + sandbox + audit |
| Domain mở rộng | Sửa code | 1 file YAML |
| Tool integration | Hardcode | MCP standard, registry pattern |
| Failure recovery | Không | Retry + fallback + circuit breaker |
