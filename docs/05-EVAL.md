# Eval Harness

## Mục đích

Đo lường chất lượng hệ thống một cách **tự động, lặp lại được**, để:

1. Catch regression khi update prompt hoặc model
2. So sánh baseline vs candidate (A/B test model)
3. Đánh giá từng domain riêng biệt
4. Track improvement qua thời gian

## Cấu trúc eval set

Mỗi domain có 1 file YAML:

```yaml
# eval/datasets/customer_support.yaml
domain: customer_support
version: 1.0
description: "Customer support tickets handling"

cases:
  - id: cs_001
    input: "Khách hàng phàn nàn đơn hàng #123 giao trễ 3 ngày"
    expected:
      task_type: classification_routing
      tools_called: [query_orders, send_email]
      should_contain: ["xin lỗi", "đơn hàng #123"]
      should_not_contain: ["không biết"]
    risk_level: medium
    timeout_sec: 30

  - id: cs_002
    input: "Refund đơn hàng #456 vì khách trả hàng"
    expected:
      task_type: data_processing
      tools_called: [query_orders, update_record]
      should_approve: true  # vì có refund
    risk_level: high
    timeout_sec: 30
```

## Metrics

### Task-level
- **Success rate:** % task pass tất cả checks
- **Tool call accuracy:** % task gọi đúng tools
- **Latency P50/P95/P99:** thời gian xử lý
- **Confidence calibration:** confidence có khớp với success rate không

### System-level
- **Auto-approval rate:** % task chạy không cần hỏi
- **Hallucination rate:** % output chứa fact sai (đo bằng Critic)
- **PII leak rate:** % output có PII không mask
- **Safety violation rate:** % task vượt guardrail

### Cost
- **Tokens/task:** trung bình input + output
- **Time/task:** wall clock
- **Memory retrievals/task:** số query vector DB

## Cách chạy

```bash
# Chạy full eval
uv run python -m eval.runner --domain all

# Chạy 1 domain
uv run python -m eval.runner --domain customer_support

# So sánh 2 model
uv run python -m eval.runner \
  --baseline ollama:llama3.1:8b \
  --candidate ollama:mistral:7b

# Regression test trong CI
uv run python -m eval.runner --ci --fail-on-regression
```

## Output report

```
$ uv run python -m eval.runner --domain customer_support

=== Customer Support Eval v1.0 ===
Running 50 cases against ollama:qwen2.5:4b + llama3.1:8b...

✓ 47/50 passed (94.0%)
✗ 3 failed:
  - cs_023: timeout (30s)
  - cs_031: wrong tool called (used update_record instead of query)
  - cs_044: hallucination (mentioned order #999 which doesn't exist)

Latency:
  P50: 1.2s
  P95: 4.5s
  P99: 8.1s

Auto-approval rate: 78% (39/50)
Hallucination rate: 2% (1/50)
PII leak rate: 0%

Cost:
  Avg tokens: 1,245/task
  Avg time: 2.3s

Regression check vs baseline:
  ✓ Success rate: 94.0% (baseline: 92.0%) +2.0%
  ✓ Latency P95: 4.5s (baseline: 5.1s) -0.6s
  ⚠ Hallucination: 2% (baseline: 0%) +2.0% ← REGRESSION

FAIL: hallucination rate increased
```

## Golden datasets

### Ban đầu (M1-M2)
- 50 cases/domain × 3 domains = 150 cases
- Hand-crafted, review bởi expert
- Commit vào repo, không thay đổi trừ khi có lý do chính đáng

### Sau M3
- Thu thập từ production (ẩn danh)
- Label bởi Critic + human review
- Add vào golden set theo quý

### Sau M4
- Synthetic generation: dùng model sinh ra cases, human verify
- Adversarial set: cố tình craft case khó

## CI integration

```yaml
# .github/workflows/eval.yml
name: Eval
on: [pull_request]

jobs:
  eval:
    runs-on: [self-hosted, gpu]  # GPU runner cho Ollama
    steps:
      - uses: actions/checkout@v4
      - name: Pull models
        run: |
          ollama pull qwen2.5:4b
          ollama pull llama3.1:8b
      - name: Run eval
        run: uv run python -m eval.runner --ci
      - name: Comment on PR
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('eval/reports/latest.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: report
            });
```

## Failure modes đo được

| Failure | Cách detect |
|---|---|
| Hallucination | Critic score + fact-check tool |
| Wrong tool | So expected vs actual tools_called |
| Timeout | Đo wall clock, fail nếu > timeout_sec |
| Format error | Validate output schema với pydantic |
| Safety violation | Detect PII, prompt injection, off-topic |
| Wrong confidence | Calibrate: confidence 0.9 phải pass 90% |
| Inconsistency | Chạy lại 3 lần, so kết quả |

## A/B testing model

```bash
# So sánh 2 model trên cùng golden set
uv run python -m eval.runner \
  --baseline-config config/baseline.yaml \
  --candidate-config config/candidate.yaml \
  --output eval/reports/ab_2026_07_19.md
```

Report sẽ highlight:
- Metric nào cải thiện
- Metric nào tệ đi
- Recommendation: nên switch sang candidate hay không

## Track qua thời gian

Mỗi eval run lưu vào `eval/reports/history/`:
```
history/
├── 2026-07-19_baseline.json
├── 2026-07-19_candidate-mistral.json
├── 2026-07-20_after-prompt-tuning.json
└── ...
```

Dashboard vẽ graph success rate, latency, hallucination rate theo thời gian.

## Definition of Done cho M4

- [ ] 3 domain × 50 cases = 150 eval cases
- [ ] CI chạy eval trên mỗi PR
- [ ] Regression catch bug 1 lần trước khi merge
- [ ] Report format markdown + JSON
- [ ] History track được 30 ngày
- [ ] A/B test 2 model trong 1 tuần
