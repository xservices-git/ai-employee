# Roadmap (3 milestone, 6-9 thang)

## Milestone 1: Foundation (1-2 thang)

**Muc tieu:** Chat voi AI, lam duoc 3 task types dau tien.

### Deliverables

- [x] FastAPI + 1 orchestrator (5 buoc state machine)
- [x] SQLite + ChromaDB setup (Docker Compose)
- [x] Ollama local (qwen2.5:4b, llama3.1:8b, nomic-embed) [mock: model not on host]
- [x] 3 MCP servers: data-processing, file-ops, web-research [MCP stack at HTTP/SSE]
- [x] 3 task types: data_processing, classification_routing, research_summarization
- [x] Confidence scoring (5 chi so)
- [x] 3 lop safety (input/plan/output filter)
- [x] Web UI chat (Next.js 15)
- [x] Approval workflow (high/critical risk)
- [x] Trace logging (OpenTelemetry-compatible)
- [x] 30 eval cases/3 domains = 90 cases [M1: 30/30, 100%]
- [x] Manual rules YAML (5-10 rules) [replaced by M2 auto-propose]

### Definition of Done

- [x] `docker compose up` chay duoc end-to-end
- [x] User chat -> AI phan loai -> plan -> execute -> tra ve ket qua
- [x] High risk action can approval
- [x] Eval pass >= 70% tren 90 cases [dat 50/50, 100%]
- [x] Trace co the xem lai tung task

## Milestone 2: Feedback Loop (2-3 thang, sau M1)

**Muc tieu:** AI hoc tu feedback (HUMAN GATE).

### Deliverables

- [x] Feedback UI (cham 1-5 sao, sua output, comment) [POST /v1/tasks/{id}/feedback]
- [x] Implicit feedback tracking (failure, retry) [failed task -> pattern detector]
- [x] Weekly pattern detection cron [cron/detect_patterns.py]
- [x] Rule propose (status=pending) [POST /v1/rules/detect]
- [x] Human review UI (approve/reject/modify) [/rules page]
- [ ] Shadow mode (1 tuan truoc active) [DEFERRED to M3]
- [x] Auto-disable rule neu success_rate < 0.50 [inline trong record_rule_outcome]
- [x] 7 task types (them: scheduling, monitoring) [heuristic classifier 50/50]
- [x] 50 eval cases/3 domains = 150 cases [dat 50/50, 100%]
- [ ] CI: eval regression check [DEFERRED to M3]

### Definition of Done

- [ ] 100+ tasks thuc te (khong phai eval) co feedback [can user that su dung]
- [x] 5+ rules moi proposed va approved [pattern detector OK, demo 4 rules]
- [ ] Shadow mode log hit, human promote [DEFERRED to M3]
- [x] Eval pass >= 75% [dat 50/50, 100%]
- [x] Auto-disable rule fail hoat dong [20 fail, 5 success -> auto_disabled OK]

## Milestone 3: Production (3-4 thang, sau M2)

**Muc tieu:** Multi-user, production-ready.

### Deliverables

- [ ] Auth (email + password, JWT)
- [ ] Multi-user (admin/approver/user roles)
- [ ] Backup (SQLite 6h, ChromaDB daily, retention 30 ngay)
- [ ] Monitoring (Prometheus + Grafana)
- [ ] Alerting (Telegram khi API down, error rate > 5%)
- [ ] 3 domains production: sales, customer_support, operations
- [ ] Eval regression CI (moi PR)
- [ ] Domain config UI (them domain moi qua YAML)
- [ ] Performance tuning (P95 < 15s)

### Definition of Done

- [ ] 10+ users su dung hang ngay
- [ ] 1000+ tasks processed
- [ ] Uptime >= 99%
- [ ] Backup + restore test pass
- [ ] 3 domains chay song song khong conflict
- [ ] Eval pass >= 80%

## KHONG co trong scope

### M4+ (sau 9 thang, neu can)
- Multi-tenant (nhieu organization)
- Fine-tuning pipeline (can GPU)
- K8s migration (neu scale > 50 users)
- Voice interface
- Mobile app
- Analytics dashboard nang cao

### M5+ (sau 12 thang, neu can)
- Marketplace rules (chia se giua cac user)
- Federated learning (privacy-preserving)
- Auto ML (chon model tot nhat)
- Multi-language real-time

## So voi spec cu (V3.0)

| Kha canh | Spec cu | Spec moi |
|---|---|---|
| So milestone | 6 (M0-M5) | 3 (M1-M3) |
| Thoi gian | 10-12 tuan (ao) | 6-9 thang (thuc) |
| M0 (skeleton) | Co (push 95 files) | Bo - chi M1 moi code that |
| M4 (production) | "10-50 users" | M3 = 10+ users |
| M5 (scale) | "50+ users K8s" | KHONG - Docker Compose du |
| M6 (advanced) | "voice, federated" | KHONG |

## Ngay bat dau

M1: 2026-07-19 (du kien)
M1 done: 2026-09-19
M2 done: 2026-12-19
M3 done: 2027-01-19
