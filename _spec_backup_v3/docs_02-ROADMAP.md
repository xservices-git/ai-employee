# Roadmap

## Tổng quan lộ trình

Dự án chia thành **6 giai đoạn**, mỗi giai đoạn có sản phẩm chạy được:

```
M0 ──► M1 ──► M2 ──► M3 ──► M4 ──► M5
│      │      │      │      │      │
│      │      │      │      │      └─ Production GA
│      │      │      │      └─ Multi-domain + Eval
│      │      │      └─ Learning loop + Observability
│      │      └─ Multi-agent + MCP tools
│      └─ Core orchestrator + RAG
└─ Spec & scaffolding
```

---

## M0 - Spec & Foundation (Tuần 1)

**Mục tiêu:** Có bộ spec đầy đủ, repo structure, CI cơ bản.

**Deliverables:**
- [x] VISION.md, ARCHITECTURE.md
- [x] OpenAPI spec
- [x] Database schema docs
- [x] MCP tool catalog
- [x] Confidence scoring spec
- [x] Project scaffolding (Python + FastAPI + Next.js + MCP)
- [x] Docker Compose cơ bản
- [x] CI: lint + test skeleton + pre-commit

**Done khi:** `make test` chạy xanh, repo có README, có thể `docker compose up` lên FastAPI skeleton.

---

## M1 - Core Orchestrator + RAG (Tuần 2-3)

**Mục tiêu:** Chạy được 1 task end-to-end, từ chat → plan → tool call → response.

**Deliverables:**
- [ ] Task Classifier (LLM 4B): phân loại 7 task types
- [ ] Orchestrator Loop: Think → Plan → Risk → Decide
- [ ] Confidence Scoring Engine: 5 chỉ số
- [ ] ChromaDB integration: episodic + semantic collections
- [ ] SQLite schema: tasks, approval_requests, learning_events
- [ ] FastAPI: POST /tasks, GET /tasks/{id}, POST /approvals/{id}
- [ ] 1 MCP server demo: data-processing (query_db)
- [ ] Open WebUI clone đơn giản: chat + approval queue

**Test:** Submit "Tìm đơn hàng #123" → Classifier chọn Data Processing → Query DB → Trả kết quả.

**Done khi:** E2E test pass, P95 < 5s cho task đơn giản.

---

## M2 - Multi-Agent + MCP Tools (Tuần 4-5)

**Mục tiêu:** 5 agents cùng hoạt động, 6 MCP server đầy đủ.

**Deliverables:**
- [ ] Planner agent (LLM 8B)
- [ ] Executor agent (LLM 4B + tools)
- [ ] Critic agent (LLM 8B)
- [ ] Memory Curator agent
- [ ] Supervisor agent (approval logic)
- [ ] A2A protocol: agent-to-agent message format
- [ ] MCP servers: data, communication, file-ops, scheduling, web-research, approval
- [ ] Tool Registry với risk_level metadata
- [ ] Web UI: task dashboard với trace view

**Test:** Submit "Hôm nay có bao nhiêu ticket urgent?" → Classifier → Planner chia task → Executor query DB → Critic verify → Response.

**Done khi:** 5 agents trao đổi qua A2A thành công, trace log đầy đủ.

---

## M3 - Learning Loop + Observability (Tuần 6-7)

**Mục tiêu:** Hệ thống tự học từ feedback, mọi thứ traceable.

**Deliverables:**
- [ ] Feedback UI: chấm điểm 1-5, ghi chú sửa sai
- [ ] Learning event pipeline: từ feedback → learning_events → rule_extracted
- [ ] Memory Curator: promote/demote skills tự động
- [ ] Episodic memory: query tương tự với hybrid search
- [ ] Semantic memory: extract patterns từ episodes
- [ ] OpenTelemetry integration
- [ ] Trace dashboard: xem lại task bất kỳ
- [ ] Metrics: success rate, latency, hallucination rate

**Test:** Submit 100 task, có 10 bị sửa → sau 1 đêm, task tương tự tự success rate tăng.

**Done khi:** Skill_definitions tự tăng version khi success rate tăng, trace dashboard hoạt động.

---

## M4 - Multi-Domain + Eval Harness (Tuần 8-9)

**Mục tiêu:** Thêm domain mới chỉ bằng 1 file YAML, có eval tự động.

**Deliverables:**
- [ ] Skill template YAML format
- [ ] 3 domains mẫu: customer_support, sales_ops, hr_admin
- [ ] Eval datasets: 50-100 task mỗi domain
- [ ] Eval runner: so sánh baseline vs candidate
- [ ] CI integration: regression test trên PR
- [ ] Domain config UI: enable/disable, tune threshold
- [ ] PII detection + masking
- [ ] Audit log append-only

**Test:** Thêm domain "logistics" bằng 1 file YAML + 20 eval cases → CI pass.

**Done khi:** Eval harness chạy được trên 3 domains, regression catch được bug.

---

## M5 - Production GA (Tuần 10-12)

**Mục tiêu:** Chạy production thật, scale được.

**Deliverables:**
- [ ] Auth + RBAC: multi-user, multi-tenant
- [ ] Rate limiting + cost control
- [ ] Backup + restore procedures
- [ ] Monitoring: Prometheus + Grafana
- [ ] Alerting: Slack/Telegram khi fail
- [ ] Documentation: ops runbook, troubleshooting
- [ ] Helm chart hoặc Docker Swarm deploy
- [ ] Load test: 100 concurrent users
- [ ] Security audit: OWASP top 10
- [ ] Disaster recovery: RPO < 1h, RTO < 30min

**Test:** Chạy song song 100 task, latency vẫn < 8s P95.

**Done khi:** 1 doanh nghiệp thật dùng ổn định 1 tháng.

---

## Mở rộng sau M5 (Backlog)

- [ ] Voice input/output (Whisper + TTS local)
- [ ] Mobile app (React Native)
- [ ] Plugin marketplace cho skills
- [ ] Multi-modal: xử lý ảnh, PDF, video
- [ ] Fine-tuning pipeline: tự fine-tune model nhỏ trên data riêng
- [ ] A2A liên tổ chức (federation)
- [ ] Crypto signing cho audit log
- [ ] Auto-scaling trên K8s

## Cải tiến so với bản gốc (tóm tắt)

| Tính năng | Bản gốc | V3.0 (cải tiến) |
|---|---|---|
| Orchestrator | 1 single loop | 5 role-based agents + A2A |
| Memory | ChromaDB + SQLite | Hierarchical 3 tầng + procedural |
| Learning | Không có | Self-improving loop + skill promotion |
| Observability | Log text | OpenTelemetry + trace dashboard |
| Safety | 1 confidence threshold | 3 lớp guardrails + sandbox + audit |
| Eval | Không có | Golden datasets + CI regression |
| Domain mở rộng | Sửa code | 1 file YAML |
| Production | Local dev | K8s + monitoring + DR |

## Tiêu chí ưu tiên khi conflict

1. **Safety > Feature**: nếu phải chọn giữa thêm tính năng và tăng safety → chọn safety
2. **Local > Cloud**: ưu tiên giải pháp không cần Internet
3. **Stdlib > Custom**: dùng thư viện chuẩn, không tự viết lại
4. **Simple > Clever**: code đọc được quan trọng hơn code ngầu
5. **Tested > Fast**: có test mới merge, tối ưu sau
