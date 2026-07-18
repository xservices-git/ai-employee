# A2A Protocol (Agent-to-Agent)

## Mục đích

Chuẩn hóa cách các agent giao tiếp với nhau. Mục tiêu:
- **Traceability:** mọi message có trace_id
- **Composability:** thêm agent mới không cần sửa agent cũ
- **Debuggability:** replay được conversation
- **Async-safe:** agents có thể chạy song song

## Message Format

```typescript
interface A2AMessage {
  // Identity
  message_id: string;          // UUID
  trace_id: string;            // UUID, xuyên suốt 1 task
  parent_message_id?: string;  // Reply chain

  // Routing
  from_agent: AgentRole;       // planner, executor, critic, ...
  to_agent: AgentRole | "broadcast";
  type: MessageType;           // request | response | event | error

  // Action
  action: string;              // execute_step, review, update_memory, ...
  payload: Record<string, any>;

  // Context
  task_id: string;
  user_id: string;
  domain?: string;

  // Timing
  created_at: string;          // ISO 8601
  deadline_ms?: number;        // Optional timeout
  ttl_ms?: number;             // Optional expiration

  // Metadata
  attempt: number;             // Retry count, 1 = first try
  correlation_id?: string;     // For async patterns
}

type AgentRole =
  | "classifier"
  | "planner"
  | "executor"
  | "critic"
  | "memory_curator"
  | "supervisor"
  | "user";

type MessageType =
  | "request"    // Expects response
  | "response"   // Reply to request
  | "event"      // Fire-and-forget notification
  | "error";     // Error response
```

## Transport

Mặc định dùng **in-process message bus** (zeroMQ-style pattern, đơn giản hóa):

```python
# core/common/a2a_bus.py
import asyncio
from collections import defaultdict

class A2ABus:
    def __init__(self):
        self._subscribers: dict[AgentRole, asyncio.Queue] = defaultdict(asyncio.Queue)
        self._history: list[A2AMessage] = []  # For debugging

    async def send(self, message: A2AMessage) -> None:
        self._history.append(message)
        if message.to_agent == "broadcast":
            for queue in self._subscribers.values():
                await queue.put(message)
        else:
            await self._subscribers[message.to_agent].put(message)

    async def receive(self, agent: AgentRole, timeout: float = 5.0) -> A2AMessage:
        return await asyncio.wait_for(
            self._subscribers[agent].get(),
            timeout=timeout
        )

    def get_history(self, trace_id: str) -> list[A2AMessage]:
        return [m for m in self._history if m.trace_id == trace_id]
```

Production có thể swap sang **Redis Streams** hoặc **NATS** mà không đổi interface.

## Conversation Pattern

Một task flow điển hình:

```
User → Classifier: [request] classify input
Classifier → Planner: [request] plan task
Planner → Memory: [request] retrieve context (episodic, semantic)
Memory → Planner: [response] context chunks
Planner → Supervisor: [request] approve plan
  (if approved)
Supervisor → Planner: [response] approved
Planner → Executor: [request] execute step 1
Executor → data-processing: [mcp] query_db
Executor → Planner: [response] step 1 result
Planner → Executor: [request] execute step 2
Executor → communication: [mcp] send_email
Executor → Planner: [response] step 2 result
Planner → Critic: [request] review output
Critic → Planner: [response] score + issues
Planner → Memory Curator: [event] store episode
Memory Curator → Planner: [response] stored
Planner → User: [response] final result
```

## Request/Response

```python
# Caller (Planner)
async def ask_executor(plan: Plan) -> list[Result]:
    msg = A2AMessage(
        message_id=uuid4(),
        trace_id=plan.trace_id,
        from_agent="planner",
        to_agent="executor",
        type="request",
        action="execute_steps",
        payload={"steps": plan.steps},
        task_id=plan.task_id,
        user_id=plan.user_id,
        deadline_ms=30000,
    )
    await bus.send(msg)
    response = await bus.receive("planner", timeout=30.0)
    return response.payload["results"]
```

## Event (fire-and-forget)

```python
# Memory Curator update sau khi task done
await bus.send(A2AMessage(
    message_id=uuid4(),
    trace_id=task.trace_id,
    from_agent="memory_curator",
    to_agent="broadcast",
    type="event",
    action="episode_stored",
    payload={"task_id": task.id, "summary": "..."},
    task_id=task.id,
    user_id=task.user_id,
))
```

## Error handling

```python
# Tool failed
error_msg = A2AMessage(
    message_id=uuid4(),
    trace_id=trace_id,
    from_agent="executor",
    to_agent="planner",
    type="error",
    action="step_failed",
    payload={
        "step_id": 2,
        "tool": "query_db",
        "error_code": "TIMEOUT",
        "error_message": "Database query exceeded 10s",
    },
    ...
)
```

Planner nhận error → retry hoặc escalate.

## Retry policy

```python
# core/common/a2a_retry.py
RETRY_POLICIES = {
    "execute_step": {"max_attempts": 3, "backoff": [1, 3, 7]},
    "classify": {"max_attempts": 2, "backoff": [0.5, 2]},
    "plan": {"max_attempts": 2, "backoff": [1, 3]},
    "critique": {"max_attempts": 2, "backoff": [1, 3]},
    "memory_update": {"max_attempts": 5, "backoff": [1, 2, 4, 8, 16]},
}
```

## Timeout & Deadlines

- Mỗi message có `deadline_ms` (relative to `created_at`)
- Bus tự check và reject expired messages
- Agent nên check deadline trước khi xử lý

```python
async def process_message(msg: A2AMessage):
    if msg.deadline_ms:
        age_ms = (now() - parse(msg.created_at)).total_seconds() * 1000
        if age_ms > msg.deadline_ms:
            logger.warning(f"Message {msg.message_id} expired")
            return None
    # ... process
```

## Tracing

Mọi message log:

```json
{
  "ts": "2026-07-19T02:30:00.123Z",
  "level": "info",
  "event": "a2a_message",
  "message_id": "uuid",
  "trace_id": "uuid",
  "from": "planner",
  "to": "executor",
  "type": "request",
  "action": "execute_steps",
  "task_id": "uuid",
  "duration_ms": 0,
  "attempt": 1
}
```

Dashboard có thể visualize:

```
[trace abc-123]
├─ classifier → planner  (50ms) classify=content_generation
├─ planner → memory      (180ms) retrieve context
│  └─ memory → planner   (180ms) 5 chunks
├─ planner → supervisor  (5ms) approve?
├─ supervisor → planner  (2.1s) approved (manual)
├─ planner → executor    (210ms) execute step 1
│  └─ executor → planner (210ms) result: [...]
├─ planner → executor    (340ms) execute step 2
│  └─ executor → planner (340ms) result: [...]
├─ planner → critic      (450ms) review
│  └─ critic → planner   (450ms) score=0.92
└─ planner → memory      (200ms) store episode
```

## Agent Implementation Template

```python
# core/agents/base.py
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    def __init__(self, role: AgentRole, bus: A2ABus):
        self.role = role
        self.bus = bus
        self._running = False

    @abstractmethod
    async def handle(self, msg: A2AMessage) -> A2AMessage | None:
        """Process incoming message, return response if needed."""
        ...

    async def run(self):
        self._running = True
        while self._running:
            try:
                msg = await self.bus.receive(self.role, timeout=1.0)
                response = await self.handle(msg)
                if response:
                    await self.bus.send(response)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.exception(f"Agent {self.role} error")
                # Send error message
                await self.bus.send(A2AMessage(
                    message_id=uuid4(),
                    trace_id=msg.trace_id,
                    from_agent=self.role,
                    to_agent=msg.from_agent,
                    type="error",
                    action="internal_error",
                    payload={"error": str(e)},
                    ...
                ))

    def stop(self):
        self._running = False
```

## Cải tiến so với bản gốc

| Khía cạnh | Bản gốc | V3.0 |
|---|---|---|
| Pattern | Function call tuần tự | Message bus async |
| Trace | Không | Mọi message có trace_id |
| Retry | Không | Có policy |
| Timeout | Không | Deadline-based |
| Replay | Không | History trên bus |
| Scale | In-process | Có thể swap Redis/NATS |
| Debug | Print log | Dashboard visualize |
