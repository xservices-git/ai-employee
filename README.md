# ai-employee

> Local AI Employee System V3.0 - Multi-agent orchestrator with hierarchical memory, RAG, MCP tools, and self-improvement.

## What is this?

A local-first, multi-agent AI system that:

- **Thinks** (Planner + Critic + Reasoning model)
- **Acts** (Executor + MCP tools)
- **Learns** (Memory Curator + feedback loop)
- **Stays safe** (3-layer guardrails + audit log)

Built for businesses that want AI automation without sending data to the cloud.

## Architecture

```
User → Web UI (Next.js) → API (FastAPI) → Orchestrator (5 agents)
                                              ↓
                                           MCP Tools
                                              ↓
                                          Ollama (LLM)
```

See `docs/01-ARCHITECTURE.md` for full diagram.

## Quick start (5 minutes)

```bash
# 1. Clone
git clone https://github.com/xservices-git/ai-employee.git
cd ai-employee

# 2. Install (Python 3.12 + uv required)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync

# 3. Install Ollama + pull models
# macOS: brew install ollama
# Linux: curl -fsSL https://ollama.com/install.sh | sh
ollama serve &
ollama pull qwen2.5:4b
ollama pull llama3.1:8b
ollama pull nomic-embed-text:v1.5

# 4. Setup env
cp .env.example .env
# Edit .env if needed

# 5. Migrate DB
uv run alembic upgrade head

# 6. Start (3 terminals)
uv run python -m api.main          # API on :8000
uv run python -m web               # Web on :3000
```

Open http://localhost:3000 and start chatting.

## Status

🚧 **M0 - Spec & Foundation** ✅ Complete
🚧 **M1 - Core Orchestrator + RAG** ⏳ Next

See `todo/MILESTONES.md` for progress.

## Features

### Implemented (M0)
- ✅ Full architecture spec
- ✅ OpenAPI 3.0 spec
- ✅ Data model (SQLite + ChromaDB)
- ✅ Confidence scoring engine spec
- ✅ MCP tool catalog
- ✅ A2A protocol spec
- ✅ Project structure + CI

### Coming (M1)
- 🚧 Classifier agent (LLM 4B)
- 🚧 Orchestrator state machine
- 🚧 ChromaDB + SQLite integration
- 🚧 1 MCP server (data-processing)
- 🚧 Minimal Web UI

### Roadmap
- M2: Multi-agent + 6 MCP servers
- M3: Self-improving + observability
- M4: Multi-domain + eval harness
- M5: Production GA

## Documentation

| Doc | Purpose |
|---|---|
| [docs/00-VISION.md](docs/00-VISION.md) | Why we built this |
| [docs/01-ARCHITECTURE.md](docs/01-ARCHITECTURE.md) | 4 layers, 5 agents |
| [docs/02-ROADMAP.md](docs/02-ROADMAP.md) | 6 milestones |
| [docs/03-TECH-STACK.md](docs/03-TECH-STACK.md) | Why each tech |
| [docs/04-SAFETY.md](docs/04-SAFETY.md) | 3-layer guardrails |
| [docs/05-EVAL.md](docs/05-EVAL.md) | Eval harness |
| [docs/06-DEPLOY.md](docs/06-DEPLOY.md) | Production setup |
| [docs/07-CONTRIBUTING.md](docs/07-CONTRIBUTING.md) | How to contribute |

| Spec | Purpose |
|---|---|
| [specs/00-OPENAPI.yaml](specs/00-OPENAPI.yaml) | REST API contract |
| [specs/01-DATA-MODEL.md](specs/01-DATA-MODEL.md) | DB schema |
| [specs/02-CONFIDENCE-SCORING.md](specs/02-CONFIDENCE-SCORING.md) | How AI decides |
| [specs/03-MCP-TOOLS.md](specs/03-MCP-TOOLS.md) | Tool catalog |
| [specs/04-PROTOCOL-A2A.md](specs/04-PROTOCOL-A2A.md) | Agent-to-agent |

## Contributing

PRs welcome! See [docs/07-CONTRIBUTING.md](docs/07-CONTRIBUTING.md).

## License

MIT - see [LICENSE](LICENSE).

## Acknowledgments

- [Ollama](https://ollama.com) - Local LLM serving
- [ChromaDB](https://www.trychroma.com) - Vector store
- [MCP](https://modelcontextprotocol.io) - Tool protocol
- [FastAPI](https://fastapi.tiangolo.com) - API framework
- [Open WebUI](https://github.com/open-webui/open-webui) - UI inspiration
