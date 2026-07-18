# Milestones Detail

## M0 - Spec & Foundation ✅

**Trạng thái:** Hoàn thành
**Ngày:** 2026-07-19

### Done
- ✅ Bộ docs đầy đủ (VISION, ARCHITECTURE, TECH-STACK, SAFETY, EVAL, DEPLOY, CONTRIBUTING)
- ✅ OpenAPI spec cho 30+ endpoints
- ✅ Data model với 7 bảng SQLite + 4 ChromaDB collections
- ✅ Confidence scoring với 5 chỉ số + weights
- ✅ MCP tool catalog: 6 servers, ~20 tools
- ✅ A2A protocol spec
- ✅ Roadmap 6 milestones
- ✅ Repo structure chuẩn
- ✅ pyproject.toml
- ✅ README
- ✅ Docker Compose skeleton
- ✅ CI workflow
- ✅ .gitignore, LICENSE (MIT)

### Files
- 7 docs (VISION, ARCHITECTURE, ROADMAP, TECH-STACK, SAFETY, EVAL, DEPLOY, CONTRIBUTING)
- 5 specs (OpenAPI, Data Model, Confidence, MCP Tools, A2A Protocol)
- 3 todo files (ROADMAP, MILESTONES, BACKLOG)

### Next: M1
Bắt đầu code:
1. `core/classifier/` - LLM 4B classifier
2. `core/orchestrator/` - state machine
3. `core/memory/` - ChromaDB + SQLite
4. `api/` - FastAPI
5. `mcp-servers/data-processing/`
6. `web/` - minimal UI

---

## M1 - Core Orchestrator + RAG (Upcoming)

**Trạng thái:** Chưa bắt đầu
**Target:** 2 tuần

### Tasks
- [ ] Setup pyproject dependencies
- [ ] Implement Classifier
- [ ] Implement Orchestrator loop
- [ ] Implement Confidence engine
- [ ] Setup ChromaDB collections
- [ ] Setup SQLite + migrations
- [ ] FastAPI routes
- [ ] 1 MCP server (data-processing)
- [ ] Minimal Web UI (chat only)
- [ ] E2E test
- [ ] Performance test P95 < 5s

### Risks
- Ollama setup trên máy user phức tạp → cần Docker image sẵn
- ChromaDB persistent có thể chậm với dataset lớn → benchmark sớm
- LLM 4B có thể không đủ thông minh cho classifier → test với 50 sample trước

---

## M2 - Multi-Agent + MCP Tools (Future)

**Trạng thái:** Chưa bắt đầu

### Tasks
- [ ] A2A bus implementation
- [ ] Planner agent
- [ ] Executor agent
- [ ] Critic agent
- [ ] Memory Curator agent
- [ ] Supervisor agent
- [ ] 5 MCP servers còn lại
- [ ] Tool registry
- [ ] Web UI: task dashboard + approval queue
- [ ] Trace logging
- [ ] Multi-task E2E

---

## M3-M5 (Backlog)

Xem `BACKLOG.md`.
