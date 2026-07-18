# Roadmap & Milestones

## 6 giai đoạn, mỗi giai đoạn có sản phẩm chạy được

Xem chi tiết trong `docs/02-ROADMAP.md`. Tóm tắt:

| M | Tên | Tuần | Output chính |
|---|---|---|---|
| M0 | Spec & Foundation | 1 | Repo + docs + skeleton + CI |
| M1 | Core Orchestrator + RAG | 2-3 | 1 task E2E |
| M2 | Multi-Agent + MCP Tools | 4-5 | 5 agents + 6 MCP servers |
| M3 | Learning + Observability | 6-7 | Self-improving + trace |
| M4 | Multi-Domain + Eval | 8-9 | 3 domains + eval CI |
| M5 | Production GA | 10-12 | 100 concurrent, security audit |

## Definition of Done cho mỗi giai đoạn

### M0
- [x] VISION, ARCHITECTURE, TECH-STACK, SAFETY, EVAL, DEPLOY, CONTRIBUTING
- [x] OpenAPI spec
- [x] Data model spec
- [x] Confidence scoring spec
- [x] MCP tools catalog
- [x] A2A protocol spec
- [x] Repo structure
- [x] pyproject.toml, README
- [x] Docker Compose skeleton
- [x] CI workflow (lint + test)
- [x] License

### M1
- [ ] Classifier agent (LLM 4B)
- [ ] Orchestrator state machine
- [ ] Confidence scoring engine
- [ ] ChromaDB integration
- [ ] SQLite schema + migrations
- [ ] FastAPI: /v1/tasks, /v1/approvals
- [ ] 1 MCP server: data-processing
- [ ] Minimal Web UI
- [ ] E2E test: "Tìm đơn hàng #123"
- [ ] P95 < 5s cho task đơn giản

### M2
- [ ] Planner agent (LLM 8B)
- [ ] Executor agent (LLM 4B)
- [ ] Critic agent (LLM 8B)
- [ ] Memory Curator agent
- [ ] Supervisor agent
- [ ] A2A bus
- [ ] 6 MCP servers
- [ ] Tool registry với risk levels
- [ ] Web UI: task dashboard
- [ ] Trace logging
- [ ] Multi-task E2E test

### M3
- [ ] Feedback UI
- [ ] Learning event pipeline
- [ ] Memory Curator: promote/demote skills
- [ ] Episodic memory: hybrid search
- [ ] Semantic memory: pattern extraction
- [ ] OpenTelemetry integration
- [ ] Trace dashboard
- [ ] Metrics: success rate, latency, hallucination
- [ ] Self-improving demo: 10 task → improved skill

### M4
- [ ] Skill template YAML format
- [ ] 3 domains: customer_support, sales_ops, hr_admin
- [ ] 150 eval cases (50/domain)
- [ ] Eval runner
- [ ] CI: regression on PR
- [ ] PII detection + masking
- [ ] Audit log append-only
- [ ] Eval passes 90% on 3 domains

### M5
- [ ] Auth + RBAC
- [ ] Rate limiting
- [ ] Backup/restore
- [ ] Prometheus + Grafana
- [ ] Alerting (Telegram/Slack)
- [ ] Ops runbook
- [ ] Load test 100 concurrent
- [ ] Security audit
- [ ] DR tested: RPO < 1h, RTO < 30min
- [ ] 1 customer dùng ổn định 1 tháng
