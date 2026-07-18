# Backlog

## M3 - Learning + Observability

### Self-improving loop
- [ ] Feedback UI component (Next.js)
- [ ] POST /v1/tasks/{id}/feedback endpoint
- [ ] Feedback → learning_events pipeline
- [ ] Learning event types: mistake_correction, approval_learned, skill_created, skill_promoted, skill_demoted
- [ ] Rule extractor (LLM 4B) - extract rule từ feedback
- [ ] Memory Curator: cập nhật semantic memory
- [ ] Skill promotion: success_rate > 0.85 + usage > 10 → version+1
- [ ] Skill demotion: success_rate < 0.5 → flag for review
- [ ] Background job: process learning events mỗi 1h

### Observability
- [ ] OpenTelemetry SDK setup
- [ ] Trace spans cho: classify, plan, execute_step, tool_call, critic, memory_update
- [ ] Prometheus metrics:
  - tasks_total{task_type, domain, status}
  - task_duration_seconds histogram
  - confidence_score histogram
  - approval_required_total
  - tool_call_total{tool, status}
  - memory_retrieval_duration_seconds
- [ ] Grafana dashboards:
  - Task throughput
  - Latency percentiles
  - Error rate
  - Approval queue size
  - Confidence distribution
- [ ] Trace dashboard: xem lại 1 task bất kỳ, span tree
- [ ] Alert: API down, error rate spike, P95 > 10s

### Memory improvements
- [ ] Hybrid search: vector + BM25
- [ ] Re-ranking với bge-reranker-base
- [ ] Metadata filtering
- [ ] PII masking trước embed

---

## M4 - Multi-Domain + Eval

### Domain templates
- [ ] Skill template YAML format
- [ ] Validator cho YAML
- [ ] Hot-reload khi add file mới
- [ ] Domain config UI

### 3 domains
- [ ] customer_support (50 eval cases)
- [ ] sales_ops (50 eval cases)
- [ ] hr_admin (50 eval cases)

### Eval harness
- [ ] Eval dataset format (YAML)
- [ ] Eval runner (CLI + API)
- [ ] Metrics calculator
- [ ] Markdown report generator
- [ ] A/B test support
- [ ] History tracking
- [ ] CI integration (GitHub Actions)
- [ ] PR comment with report

### Safety hardening
- [ ] PII detection (regex + heuristic)
- [ ] PII masking pipeline
- [ ] Audit log append-only (DB trigger)
- [ ] Audit log ship to external storage (optional)
- [ ] Tool sandbox: process isolation, resource limits

---

## M5 - Production GA

### Auth & multi-tenant
- [ ] User auth (JWT)
- [ ] RBAC: admin, approver, user
- [ ] API key cho service-to-service
- [ ] Multi-tenant: org_id, isolation
- [ ] Per-user rate limit
- [ ] Per-org rate limit

### Operations
- [ ] Backup script (cron)
- [ ] Restore procedure + test
- [ ] Log rotation
- [ ] Disk usage monitor
- [ ] Database migration procedure
- [ ] Health check endpoint
- [ ] Graceful shutdown
- [ ] Zero-downtime deploy

### Monitoring & alerting
- [ ] Prometheus full setup
- [ ] Grafana dashboards
- [ ] Alert rules
- [ ] Telegram/Slack notifier
- [ ] Incident response runbook

### Security audit
- [ ] OWASP Top 10 check
- [ ] Penetration test
- [ ] Secret rotation procedure
- [ ] TLS setup (Let's Encrypt)
- [ ] CSP headers
- [ ] CORS policy
- [ ] SQL injection check
- [ ] XSS check
- [ ] Dependency vulnerability scan

### Scale
- [ ] Load test 100 concurrent
- [ ] Bottleneck analysis
- [ ] Multi-node setup
- [ ] Docker Swarm hoặc K3s
- [ ] Tách Ollama node riêng (GPU)
- [ ] Tách vector DB node riêng

### DR
- [ ] RPO/RTO documented
- [ ] Backup to offsite (S3)
- [ ] Restore tested
- [ ] Failover procedure
- [ ] Game day exercise

---

## Post-M5 / Future

### Advanced features
- [ ] Voice input/output (Whisper + TTS local)
- [ ] Mobile app (React Native)
- [ ] Plugin marketplace
- [ ] Multi-modal: image, PDF, video
- [ ] Fine-tuning pipeline (auto fine-tune trên data riêng)
- [ ] A2A federation (cross-org)
- [ ] Crypto audit log (blockchain-style)

### Optimizations
- [ ] Speculative execution (parallel candidates)
- [ ] Caching layer (Redis optional)
- [ ] Streaming responses (SSE)
- [ ] Batch processing
- [ ] Prefetch common queries
- [ ] Model quantization (GGUF Q4)

### Research
- [ ] Agent benchmarking trên các public dataset
- [ ] So sánh model: Qwen vs Llama vs Mistral vs Phi
- [ ] RAG evaluation: BM25 vs vector vs hybrid
- [ ] Prompt optimization tự động
- [ ] Active learning: hỏi user khi uncertainty cao
- [ ] Constitutional AI: self-constraint

### Community
- [ ] Public website + docs site (Docusaurus)
- [ ] Demo video
- [ ] Tutorial series
- [ ] Sample domains library
- [ ] Discord/Telegram community
- [ ] Monthly newsletter

### Business
- [ ] Pricing (nếu có managed version)
- [ ] SLA
- [ ] Support tier
- [ ] Partner program
- [ ] White-label option
