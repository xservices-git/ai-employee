# Roadmap (3 milestone, 6-9 thang)

## Milestone 1: Foundation (1-2 thang)

**Muc tieu:** Chat voi AI, lam duoc 3 task types dau tien.

### Deliverables

- [ ] FastAPI + 1 orchestrator (5 buoc state machine)
- [ ] SQLite + ChromaDB setup (Docker Compose)
- [ ] Ollama local (qwen2.5:4b, llama3.1:8b, nomic-embed)
- [ ] 3 MCP servers: data-processing, file-ops, web-research
- [ ] 3 task types: data_processing, classification_routing, research_summarization
- [ ] Confidence scoring (5 chi so)
- [ ] 3 lop safety (input/plan/output filter)
- [ ] Web UI chat (Next.js 15)
- [ ] Approval workflow (high/critical risk)
- [ ] Trace logging (OpenTelemetry-compatible)
- [ ] 30 eval cases/3 domains = 90 cases
- [ ] Manual rules YAML (5-10 rules)

### Definition of Done

- [ ] `docker compose up` chay duoc end-to-end
- [ ] User chat -> AI phan loai -> plan -> execute -> tra ve ket qua
- [ ] High risk action can approval
- [ ] Eval pass >= 70% tren 90 cases
- [ ] Trace co the xem lai tung task
- [ ] Manual rule apply khi match trigger

## Milestone 2: Feedback Loop (2-3 thang, sau M1)

**Muc tieu:** AI hoc tu feedback (HUMAN GATE).

### Deliverables

- [ ] Feedback UI (cham 1-5 sao, sua output, comment)
- [ ] Implicit feedback tracking (failure, retry)
- [ ] Weekly pattern detection cron
- [ ] Rule propose (LLM, status=pending)
- [ ] Human review UI (approve/reject/modify)
- [ ] Shadow mode (1 tuan truoc active)
- [ ] Auto-disable rule neu success_rate < 0.50
- [ ] 7 task types (them: content_generation, monitoring, scheduling, decision)
- [ ] 50 eval cases/domain x 3 domains = 150 cases
- [ ] CI: eval regression check

### Definition of Done

- [ ] 100+ tasks thuc te (khong phai eval) co feedback
- [ ] 5+ rules moi proposed va approved
- [ ] Shadow mode log hit, human promote
- [ ] Eval pass >= 75%
- [ ] Auto-disable rule fail hoat dong

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
