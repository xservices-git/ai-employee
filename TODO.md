# TODO - AI Employee

## M3 Con lai (2/9)

### BLOCKED - can user that su dung
- [ ] 3 domains production real-world: sales, customer_support, operations
  - eval co 3 domains, production chua co task nao
  - Can: deploy + 10+ users + 1000+ tasks
- [ ] 10+ users su dung hang ngay
- [ ] 1000+ tasks processed
- [ ] Uptime >= 99% (can production deploy)
- [ ] P95 latency < 15s (can real load)

### TODO ngay (tu lam duoc)
- [ ] Restart app de route moi hoat dong (auth audit, domains)
- [ ] Wire auth vao task endpoints (user_id tu Bearer token)
- [ ] Wire auth vao approval + rule endpoints (optional auth)
- [ ] Add password_hash + role cols to users table DDL in 02-DATA-MODEL.md
- [ ] Add /v1/domains + /v1/auth/audit endpoints to specs/00-OPENAPI.yaml
- [ ] Write domain_configs/*/rules.yaml (3 domains, rules placeholder)
- [ ] Update VISION.md: M3 section reflects progress
- [ ] Rerun eval baseline (M3 code co the thay doi pass rate)

## DONE (2026-07-19)

### M3 Delivered
- [x] Auth: JWT HS256 + pbkdf2_sha256 + register/login/me
- [x] Multi-user: admin/approver/user roles, first-user auto-admin
- [x] Backup: scripts/backup.py + cron/backup_cron.py + Telegram alert
- [x] Monitoring: Prometheus /metrics, stdlib
- [x] Alerting: Telegram send_alert + /v1/alerts/test
- [x] Audit log: append-only table + triggers + log_action on 4 endpoints
- [x] Eval regression CI: scripts/eval_regression.py --baseline
- [x] Domain config: core/domain_config.py + /v1/domains API + 3 seed YAML
- [x] Stale tests cleanup: removed 6 V3 spec test files (-457 LOC)

### M2 Delivered
- [x] Feedback UI (1-5 stars, corrections, notes)
- [x] Pattern detection cron
- [x] Rule propose + human approve/reject/modify
- [x] Auto-disable rules fail >50%
- [x] 7 task types (heuristic classifier)
- [x] 50 eval cases / 3 domains (150 total)

### M1 Delivered
- [x] FastAPI + 1 orchestrator (5-step state machine)
- [x] SQLite + ChromaDB setup
- [x] 3 MCP servers: data-processing, file-ops, web-research
- [x] 3 task types (data_processing, classification_routing, research_summarization)
- [x] Confidence scoring (5 metrics)
- [x] 3 safety layers (input/plan/output filter)
- [x] Approval workflow
- [x] Trace logging
- [x] 90 eval cases (3 domains x 30)

## Notes

### Architecture decisions
- 1 orchestrator, KHONG multi-agent 5 roles
- HUMAN GATE, KHONG auto-promote rules
- Docker Compose, KHONG K8s
- 100% local, KHONG external API

### Key metrics (current)
- Eval: 50/50 (100%) - M2 golden set
- Auth: register + login + me working
- Audit: 19 tests pass (10 audit + 9 M3)
- Domains: 3 seed configs (sales, customer_support, operations)
- Backup: cron/backup_cron.py (6h cadence, Telegram alert on fail)
