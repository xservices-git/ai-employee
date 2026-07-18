# Confidence Scoring

## Tổng quan

Confidence score là số từ 0-1 thể hiện mức độ "chắc chắn" của AI về một quyết định. Kết hợp 5 chỉ số có trọng số.

## Công thức

```
confidence = familiarity × 0.30
           + clarity      × 0.20
           + risk_score   × 0.25
           + similarity   × 0.15
           + simplicity   × 0.10
```

Tổng = 1.0, mỗi chỉ số cũng 0-1.

## 5 chỉ số chi tiết

### 1. Familiarity (0.30) - Độ quen thuộc

Đo xem task tương tự đã làm bao nhiêu lần và tỉ lệ thành công.

```python
def calculate_familiarity(task_type: str, domain: str, user_id: str) -> float:
    # Query episodic memory
    similar = episodic_memory.query(
        filter={
            "task_type": task_type,
            "domain": domain,
            "user_id": user_id
        },
        top_k=20
    )
    if not similar:
        return 0.3  # No history, default low

    success_count = sum(1 for m in similar if m.metadata["success"])
    total = len(similar)

    # Score = min(success_rate, 1.0) * log_factor
    success_rate = success_count / total
    experience_factor = min(1.0, total / 10)  # Saturate at 10+ tasks

    return success_rate * experience_factor
```

**Range giải thích:**
- 0.0-0.3: chưa từng làm
- 0.3-0.6: làm vài lần, success rate trung bình
- 0.6-0.9: làm nhiều, success rate cao
- 0.9-1.0: làm > 10 lần, success > 90%

### 2. Clarity (0.20) - Độ rõ ràng input

Đo xem input có đầy đủ thông tin và không mâu thuẫn không.

```python
def calculate_clarity(input_data: dict, required_fields: list[str]) -> float:
    missing = sum(1 for f in required_fields if f not in input_data or not input_data[f])
    if missing > 0:
        return max(0.0, 1.0 - missing * 0.15)

    # Check contradictions (semantic)
    contradictions = llm_detect_contradictions(input_data)  # Returns 0-N
    contradiction_penalty = min(0.4, contradictions * 0.1)

    return max(0.0, 1.0 - contradiction_penalty)
```

**Ví dụ:**
- Input rõ ràng, đủ field → 1.0
- Thiếu 1 field optional → 0.85
- Thiếu 2 field required → 0.7
- Mâu thuẫn giá/ngày → 0.6

### 3. Risk score (0.25) - Mức an toàn (inverted risk)

Cao = an toàn, thấp = nguy hiểm.

```python
def calculate_risk_score(domain: str, action: str) -> float:
    risk_matrix = {
        ("sales", "query_order"): 0.05,      # Rất an toàn
        ("sales", "create_quote"): 0.25,      # Cần review giá
        ("sales", "send_email"): 0.55,        # Cần approval
        ("sales", "delete_order"): 0.90,      # Critical
        ("customer_support", "reply_template"): 0.15,
        ("customer_support", "send_email"): 0.50,
        ("customer_support", "refund"): 0.85,
    }
    risk = risk_matrix.get((domain, action), 0.5)  # Default medium

    return 1.0 - risk  # Invert: high risk = low score
```

**Risk matrix config** lưu trong `domain_configs/{domain}.yaml`, có thể tune.

### 4. Similarity (0.15) - Độ tương đồng quá khứ

Cosine similarity trung bình với top 5 task tương tự nhất.

```python
def calculate_similarity(input_text: str, task_type: str) -> float:
    results = episodic_memory.query(
        query_text=input_text,
        filter={"task_type": task_type},
        top_k=5
    )
    if not results:
        return 0.5  # No comparable history, neutral

    avg_score = sum(r.score for r in results) / len(results)
    return avg_score  # Already 0-1 from cosine similarity
```

**Range:**
- 0.0-0.3: input rất khác quá khứ
- 0.3-0.7: có vài điểm tương tự
- 0.7-1.0: rất giống task đã làm

### 5. Simplicity (0.10) - Độ đơn giản

Inverted complexity. Task càng đơn giản → score càng cao.

```python
def calculate_simplicity(plan: Plan) -> float:
    step_count = len(plan.steps)
    tool_count = sum(len(s.tools) for s in plan.steps)
    branch_count = count_branches(plan)  # if/else trong plan

    # Penalty scales
    step_penalty = min(0.5, step_count * 0.05)        # 10 steps = max penalty
    tool_penalty = min(0.3, tool_count * 0.05)        # 6 tools = max
    branch_penalty = min(0.2, branch_count * 0.05)    # 4 branches = max

    return max(0.0, 1.0 - step_penalty - tool_penalty - branch_penalty)
```

## Action mapping

```
confidence  action              condition
─────────────────────────────────────────────────────────
≥ 0.85      AUTO_EXECUTE        + tool risk = low
≥ 0.70      AUTO_EXECUTE        + tool risk ≤ medium
≥ 0.70      REQUEST_APPROVAL    + tool risk ≥ high
< 0.70      REQUEST_APPROVAL    always
< 0.40      CLARIFY_OR_REJECT   always
```

**Pseudocode:**

```python
def decide_action(confidence: float, tool_risk: RiskLevel) -> Action:
    if confidence < 0.40:
        return Action.CLARIFY_OR_REJECT
    if confidence >= 0.85 and tool_risk == RiskLevel.LOW:
        return Action.AUTO_EXECUTE
    if confidence >= 0.70 and tool_risk <= RiskLevel.MEDIUM:
        return Action.AUTO_EXECUTE
    return Action.REQUEST_APPROVAL
```

## Calibration

Confidence phải được **calibrate** để khớp với thực tế:

- Confidence 0.9 → success rate thực tế phải ≈ 90%
- Nếu confidence 0.9 mà success 60% → miscalibrated, giảm trọng số familiarity

Đo calibration bằng **Expected Calibration Error (ECE)**:

```python
def expected_calibration_error(predictions: list[float], actuals: list[bool]) -> float:
    bins = [[] for _ in range(10)]  # 10 bins 0-0.1, 0.1-0.2, ...
    for conf, actual in zip(predictions, actuals):
        bin_idx = min(9, int(conf * 10))
        bins[bin_idx].append(1.0 if actual else 0.0)

    ece = 0.0
    total = len(predictions)
    for i, bin_data in enumerate(bins):
        if not bin_data:
            continue
        bin_conf = (i + 0.5) / 10
        bin_acc = sum(bin_data) / len(bin_data)
        ece += abs(bin_acc - bin_conf) * len(bin_data) / total

    return ece
```

**Target:** ECE < 0.05

## Threshold tuning

Mỗi domain có thể override threshold:

```yaml
# domain_configs/customer_support.yaml
confidence:
  auto_execute_threshold: 0.65    # Thấp hơn mặc định vì domain ít rủi ro
  approval_threshold: 0.40
  weights:
    familiarity: 0.35             # Boost vì có nhiều history
    clarity: 0.20
    risk: 0.20                    # Giảm vì risk matrix đã strict
    similarity: 0.15
    simplicity: 0.10
```

## Cải tiến so với bản gốc

| Khía cạnh | Bản gốc | V3.0 |
|---|---|---|
| Số chỉ số | 5 | 5 (cùng) |
| Trọng số | Cố định | Có thể tune theo domain |
| Calibration | Không đo | ECE tracking |
| Audit | Không log | Log mỗi quyết định |
| User override | Không | Có (override threshold cho domain) |
| Learning | Không | Update weights theo feedback |

## Logging

Mỗi lần tính confidence, log:

```json
{
  "event": "confidence_calculated",
  "task_id": "uuid",
  "trace_id": "uuid",
  "scores": {
    "familiarity": 0.75,
    "clarity": 0.90,
    "risk": 0.70,
    "similarity": 0.60,
    "simplicity": 0.85
  },
  "weights": {
    "familiarity": 0.30,
    "clarity": 0.20,
    "risk": 0.25,
    "similarity": 0.15,
    "simplicity": 0.10
  },
  "final": 0.74,
  "action": "request_approval"
}
```

Sau 1 tháng, có thể analyze và tune weights tự động.
