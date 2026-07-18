# Vision

## Tầm nhìn

Xây dựng một **đội ngũ nhân viên AI local** hoạt động như một tổ chức thật:

- **Tự quyết** các việc có độ tin cậy cao
- **Xin phê duyệt** khi không chắc chắn
- **Học liên tục** từ feedback và từ chính những sai lầm của mình
- **Mở rộng được cho mọi ngành nghề** mà không phải code lại từ đầu

## Vấn đề hiện tại của các hệ AI agent

| Vấn đề | Giải pháp V3.0 |
|---|---|
| Agent làm việc rồi quên, không học | Hierarchical memory (episodic + semantic + procedural) |
| Không phân biệt được việc nào cần hỏi, việc nào tự làm | Confidence scoring đa chiều + ngưỡng an toàn |
| Black box, không debug được | Trace đầy đủ + eval harness + dashboard |
| Prompt hack, jailbreak, hallucination | 3 lớp safety (input, plan, output) + sandbox tool execution |
| Mỗi domain phải code lại | Skill template engine + task taxonomy domain-agnostic |
| Chỉ chạy được trên cloud | 100% local với Ollama + vector DB local |

## Cải tiến sâu so với bản gốc

### 1. Multi-agent collaboration
Thay vì 1 orchestrator đơn lẻ, dùng **role-based agents** giao tiếp qua **A2A (Agent-to-Agent) protocol**:

- **Planner** - phân tích yêu cầu, lập kế hoạch
- **Executor** - gọi tool, thực thi
- **Critic** - review kết quả, rút kinh nghiệm
- **Memory Curator** - cập nhật long-term memory
- **Supervisor** - phê duyệt, override, override chain

### 2. Hierarchical memory (3 tầng)
- **Working memory** - context hiện tại của task
- **Episodic memory** - "task này tôi đã làm ngày X, kết quả Y"
- **Semantic memory** - "kiến thức chung rút ra từ nhiều episode"
- **Procedural memory** - "skill thành công cần các bước A, B, C"

### 3. Self-improving loop
Mỗi task đều sinh ra **learning event**:
- Khi người dùng sửa → học correction
- Khi Critic đánh giá → học self-reflection
- Khi skill thành công nhiều lần → promote lên skill_definitions
- Khi skill fail nhiều lần → downgrade hoặc xóa

### 4. Observability built-in
- Mọi task có **trace ID** xuyên suốt
- Lưu span cho từng bước (plan, retrieve, tool call, evaluate)
- Dashboard xem lại task bất kỳ, debug tại sao fail
- Export OpenTelemetry-compatible

### 5. Safety first
- **3 lớp guardrails**: input filter → plan validator → output filter
- **Tool sandbox**: mỗi tool khai báo risk level, mức cao buộc approval
- **Confidence threshold** linh hoạt theo domain
- **PII detection** tự động mask trước khi ghi memory
- **Audit log** bất biến (append-only) cho compliance

### 6. Eval harness
- Golden datasets cho 7 task groups
- Auto regression test khi update prompt hoặc model
- So sánh baseline vs candidate model
- CI integration

### 7. Domain extensibility
- Mỗi domain (sales, support, HR...) chỉ cần thêm 1 file YAML skill template
- Không cần đụng core code
- Validation tự động cho template mới

## Mục tiêu đo lường được

- **Task success rate ≥ 90%** trên golden set
- **Auto-approval rate ≥ 70%** (chỉ 30% cần hỏi người)
- **P95 latency < 8s** cho task đơn giản, < 30s cho task phức tạp
- **Memory retrieval P95 < 200ms**
- **Hallucination rate < 2%** (đo bằng Critic + fact-check)
- **100% local** - không gửi data ra ngoài

## Không phải mục tiêu

- ❌ Thay thế con người hoàn toàn → **Tăng cường năng lực** con người
- ❌ Làm mọi thứ → **Làm tốt 7 nhóm task** đã định nghĩa
- ❌ Đa ngôn ngữ real-time → **Hỗ trợ tiếng Việt + Anh tốt**, các ngôn ngữ khác là bonus
- ❌ Thay thế ERP/CRM → **Tích hợp** với hệ thống có sẵn

## Đối tượng sử dụng

1. **Doanh nghiệp SME** muốn tự động hóa mà data phải ở local
2. **Team operations** đang ngập trong email, ticket, đơn hàng thủ công
3. **Developer** muốn build AI agent mà không phụ thuộc OpenAI API
4. **Cá nhân** muốn có "trợ lý ảo" hiểu mình qua feedback

## Timeline

Xem `docs/02-ROADMAP.md`.
