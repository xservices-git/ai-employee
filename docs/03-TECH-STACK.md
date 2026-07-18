# Tech Stack

## Nguyên tắc chọn công nghệ

1. **Local-first** - ưu tiên giải pháp chạy offline
2. **Production-grade** - không chọn tool chỉ vì "đang hot"
3. **Team maintainable** - có cộng đồng, có docs, có update
4. **Stdlib > Custom** - ưu tiên thư viện chuẩn
5. **Open source** - tránh vendor lock-in

## Stack chính

### Backend - Python 3.12
**Lý do:** Ecosystem AI/ML tốt nhất, có mọi thư viện cần.

```
python 3.12
├── fastapi          # API framework
├── pydantic v2      # validation
├── uvicorn          # ASGI server
├── sqlalchemy 2.0   # ORM (dùng cho SQLite + future Postgres)
├── alembic          # migration
├── chromadb         # vector store
├── ollama           # LLM client
├── httpx            # async HTTP (MCP, Ollama, n8n)
├── structlog        # structured logging
├── opentelemetry-*  # tracing
├── prometheus-client
├── pytest           # test
├── ruff             # lint
├── mypy             # type check
└── uv               # package manager
```

### Critical path - Go 1.22
**Lý do:** Orchestrator state machine cần latency thấp, GC pause 0.

```
go 1.22
├── go-chi           # HTTP router
├── gorilla/websocket
├── prometheus/client_golang
└── open-telemetry/opentelemetry-go
```

Chỉ dùng Go cho: orchestrator state machine, MCP server hot path, A2A message bus.

### Frontend - Next.js 15 + TypeScript
**Lý do:** SSR, ecosystem React lớn nhất, type-safe.

```
next 15
├── react 19
├── typescript 5.5
├── tailwindcss 4
├── shadcn/ui        # component
├── @tanstack/react-query
├── zustand          # state
├── zod              # validation
├── socket.io-client # realtime
└── lucide-react     # icons
```

### LLM serving - Ollama
**Lý do:** Local, OpenAI-compatible, multi-model.

```bash
ollama pull qwen2.5:4b
ollama pull llama3.1:8b
ollama pull nomic-embed-text:v1.5
ollama pull bge-reranker-base
```

### Vector DB - ChromaDB
**Lý do:** Local, persistent, đơn giản, không cần server riêng.

```python
import chromadb
client = chromadb.PersistentClient(path="./data/chroma")
```

### RDB - SQLite
**Lý do:** Embedded, backup đơn giản, đủ cho < 1M records.

```python
DATABASE_URL = "sqlite:///./data/ai-employee.db"
```

Nếu cần scale: migrate sang PostgreSQL 16 (chỉ đổi connection string).

### MCP - JSON-RPC 2.0
**Lý do:** Chuẩn mở, đơn giản, có SDK Python/Go.

MCP servers viết bằng Python, dùng `mcp` package:

```python
from mcp.server import Server
server = Server("data-processing")

@server.tool()
async def query_db(sql: str) -> list[dict]:
    ...
```

### Observability
- **Tracing:** OpenTelemetry → Jaeger hoặc Tempo
- **Metrics:** Prometheus → Grafana
- **Logs:** JSON → Loki hoặc file

### Container & Deploy
- **Dev:** Docker Compose
- **Prod:** Docker Swarm hoặc K3s (single-node đủ)
- **CI:** GitHub Actions

## Không dùng

| Tech | Lý do tránh |
|---|---|
| LangChain | Quá nặng, hard to debug, vendor lock-in |
| LlamaIndex | Tương tự LangChain |
| Pinecone | Cloud, vendor lock-in |
| Weaviate | OK nhưng ChromaDB đơn giản hơn cho local |
| MongoDB | SQLite đủ dùng |
| Redis | Chưa cần, có thể thêm sau nếu cần cache |
| Kubernetes | Quá nặng cho giai đoạn đầu, dùng Swarm/K3s |
| OpenAI API | Vendor lock-in, không local |

## Tại sao không dùng LangChain?

1. **Black box** - khó debug khi prompt chain fail
2. **Versioning hell** - breaking changes mỗi minor version
3. **Overhead** - nhiều abstraction làm chậm
4. **Coupling** - mọi thứ phụ thuộc LangChain

Thay vào đó: viết orchestrator tay, ~500 LOC Python, dễ hiểu, dễ test.

## Tại sao local-first?

1. **Data privacy** - data khách hàng không ra khỏi máy
2. **Cost** - không trả tiền API
3. **Latency** - không phụ thuộc network
4. **Compliance** - GDPR, PDPA dễ chứng minh
5. **Offline** - vẫn chạy khi mất mạng

## Tại sao multi-agent thay vì 1 agent lớn?

1. **Separation of concerns** - mỗi agent 1 việc, dễ test
2. **Specialization** - dùng model phù hợp từng việc (4B cho tool call, 8B cho reasoning)
3. **Scalability** - scale từng agent độc lập
4. **Debuggability** - biết chính xác agent nào fail
5. **Composability** - thêm agent mới không ảnh hưởng agent cũ
