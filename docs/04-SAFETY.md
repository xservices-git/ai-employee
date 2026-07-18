# Safety

## Triết lý

> **Safety không phải feature, safety là điều kiện tiên quyết.**

Mọi component đều phải fail-safe: nếu không chắc, từ chối và hỏi người.

## 3 lớp guardrails

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Input filter                                      │
│  • Prompt injection detection                               │
│  • PII detection (mask)                                     │
│  • Rate limiting                                            │
│  • Content moderation (violence, illegal)                   │
└────────────────────────┬────────────────────────────────────┘
                         │ clean input
┌────────────────────────▼────────────────────────────────────┐
│  Layer 2: Plan validator                                    │
│  • Action whitelisting                                      │
│  • Resource limit (token, time, cost)                       │
│  • Risk-class matching (tool risk vs confidence)            │
│  • Cycle detection (A gọi B gọi A)                          │
│  • Side-effect declaration                                   │
└────────────────────────┬────────────────────────────────────┘
                         │ approved plan
┌────────────────────────▼────────────────────────────────────┐
│  Layer 3: Output filter                                     │
│  • PII leak detection                                       │
│  • Fact-check (nếu có thể)                                  │
│  • Hallucination scoring                                    │
│  • Format validation                                        │
│  • Final confidence threshold                               │
└─────────────────────────────────────────────────────────────┘
```

## Risk classification cho tool

| Level | Mô tả | Action |
|---|---|---|
| **low** | Read-only, no side effect | Auto-execute |
| **medium** | Create local data, send non-sensitive | Auto nếu confidence ≥ 0.70 |
| **high** | Send email/SMS, modify user data | Require approval |
| **critical** | Delete data, payment, legal | Always require approval + 2FA |

Ví dụ:
- `query_db` → low
- `create_draft` → medium
- `send_email` → high
- `delete_record` → critical

## Confidence → Action mapping

```
confidence ≥ 0.85 + tool risk low    → AUTO_EXECUTE
confidence ≥ 0.70 + tool risk medium  → AUTO_EXECUTE
confidence ≥ 0.70 + tool risk high    → REQUEST_APPROVAL
confidence ≥ 0.70 + tool risk critical → REQUEST_APPROVAL + 2FA
0.40 ≤ confidence < 0.70              → REQUEST_APPROVAL
confidence < 0.40                     → REJECT_OR_CLARIFY
```

Confidence threshold có thể tune theo domain (file `domain_configs/`).

## Approval workflow

```
1. Task sinh ra approval_request
2. Notification đến approver (UI, email, telegram)
3. Approver có 3 lựa chọn:
   • Approve → Executor chạy tool
   • Reject → Task fail, log reason
   • Modify → Sửa args/proposal, rồi Approve
4. Decision ghi vào approval_history (cho lần sau)
5. Memory Curator học: task nào user hay sửa → tăng caution
```

## PII detection

Dùng regex + heuristic cho PII phổ biến:
- Email, phone, CMND, số tài khoản
- Địa chỉ chính xác
- Tên đầy đủ kết hợp ngày sinh

Khi phát hiện:
- **Trong input:** mask trước khi embed, lưu raw riêng
- **Trong output:** cảnh báo user, yêu cầu xác nhận trước khi gửi
- **Trong memory:** chỉ lưu masked version

## Sandbox tool execution

Mỗi MCP server chạy trong process riêng:
- Process crash không kéo theo orchestrator
- Resource limit: max CPU, max RAM, max disk
- Network: whitelist domain
- File system: chỉ truy cập workspace
- Timeout: mỗi tool có max execution time

## Audit log

Append-only log, mỗi entry có:
- `ts` - timestamp
- `trace_id` - xuyên suốt
- `actor` - user hoặc agent id
- `action` - tool name + args
- `result` - success/fail
- `confidence` - tại thời điểm quyết định
- `approver` - nếu có

Lưu cả local (SQLite) và remote (nếu có S3/MinIO).

## Rate limiting

- Per user: 100 req/hour
- Per tool: 1000 call/hour
- Per domain: 5000 call/hour
- Global: 10000 call/hour (configurable)

Vượt → reject với HTTP 429.

## Incident response

| Severity | Response |
|---|---|
| Tool fails 3x liên tiếp | Circuit breaker mở 5 phút |
| PII leak detected | Stop ngay, alert admin, rotate secrets |
| Prompt injection thành công | Block user 1h, alert admin |
| Hallucination rate > 10% | Auto-disable domain, yêu cầu review |
| Memory corruption | Rollback về snapshot gần nhất |

## Threat model

| Threat | Mitigation |
|---|---|
| User cố ý jailbreak | Layer 1 input filter + rate limit |
| Tool output chứa payload | Layer 3 output filter |
| Skill bị poison qua feedback | Critic review mọi learning event |
| Model bị thay | Versioning + checksum + audit log |
| DB bị tamper | Append-only log + signature |
| Network bị MITM | TLS + cert pinning cho internal service |
| Insider abuse | Audit log + approval cho critical action |

## Không bao giờ

- ❌ Cho phép tool tự ý gọi tool khác mà không qua Executor
- ❌ Lưu raw PII vào vector store
- ❌ Auto-execute critical action kể cả confidence cao
- ❌ Bỏ qua Critic vì "tốn thời gian"
- ❌ Trust memory mà không check provenance
- ❌ Disable safety kể cả khi user yêu cầu "làm nhanh đi"
