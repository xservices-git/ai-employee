# Confidence Scoring

## Cong thuc

```
confidence = familiarity x 0.30
           + clarity      x 0.20
           + risk_score   x 0.25
           + similarity   x 0.15
           + simplicity   x 0.10
```

5 chi so, tong = 1.0, moi chi so 0-1.

## 5 chi so chi tiet

### 1. Familiarity (0.30) - Do quen thuoc

```python
def calculate_familiarity(task_type: str, domain: str, user_id: str) -> float:
    similar = episodic_memory.query(
        filter={"task_type": task_type, "domain": domain, "user_id": user_id},
        top_k=20
    )
    if not similar:
        return 0.3  # No history

    success_count = sum(1 for m in similar if m.metadata["success"])
    success_rate = success_count / len(similar)
    experience_factor = min(1.0, len(similar) / 10)  # Saturate at 10+

    return success_rate * experience_factor
```

- 0.0-0.3: chua tung lam
- 0.3-0.6: vai lan, TB
- 0.6-0.9: nhieu lan, tot
- 0.9-1.0: 10+ lan, 90%+ success

### 2. Clarity (0.20) - Do ro rang input

```python
def calculate_clarity(input_data: dict, required_fields: list[str]) -> float:
    missing = sum(1 for f in required_fields if f not in input_data or not input_data[f])
    if missing > 0:
        return max(0.0, 1.0 - missing * 0.15)
    contradictions = llm_detect_contradictions(input_data)
    return max(0.0, 1.0 - min(0.4, contradictions * 0.1))
```

- 1.0: ro rang, du field
- 0.7-0.9: thieu 1-2 field optional
- 0.4-0.6: thieu nhieu field required
- <0.4: mau thuan nhieu

### 3. Risk score (0.25) - Do an toan (inverted)

```python
def calculate_risk_score(domain: str, action: str) -> float:
    risk_matrix = {
        ("sales", "query_order"): 0.05,
        ("sales", "create_quote"): 0.25,
        ("sales", "send_email"): 0.55,
        ("sales", "delete_order"): 0.90,
        ("customer_support", "reply_template"): 0.15,
        ("customer_support", "refund"): 0.85,
    }
    risk = risk_matrix.get((domain, action), 0.5)
    return 1.0 - risk  # Invert
```

Risk matrix config trong `domain_configs/{domain}.yaml`, co the tune.

### 4. Similarity (0.15) - Do tuong dong

```python
def calculate_similarity(input_text: str, task_type: str) -> float:
    results = episodic_memory.query(query_text=input_text, top_k=5)
    if not results:
        return 0.5
    return sum(r.score for r in results) / len(results)
```

- 0.0-0.3: rat khac
- 0.3-0.7: vai diem tuong tu
- 0.7-1.0: rat giong

### 5. Simplicity (0.10) - Do don gian (inverted complexity)

```python
def calculate_simplicity(plan: Plan) -> float:
    step_penalty = min(0.5, len(plan.steps) * 0.05)
    tool_penalty = min(0.3, sum(len(s.tools) for s in plan.steps) * 0.05)
    branch_penalty = min(0.2, count_branches(plan) * 0.05)
    return max(0.0, 1.0 - step_penalty - tool_penalty - branch_penalty)
```

## Action mapping

```
confidence  action              condition
-----------------------------------------------------------
>= 0.85     AUTO_EXECUTE        + tool risk = low
>= 0.70     AUTO_EXECUTE        + tool risk <= medium
>= 0.70     REQUEST_APPROVAL    + tool risk >= high
<  0.70     REQUEST_APPROVAL    always
<  0.40     CLARIFY_OR_REJECT   always
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

## Calibration (ECE)

Confidence phai khop voi thuc te:

```python
def expected_calibration_error(predictions, actuals) -> float:
    bins = [[] for _ in range(10)]
    for conf, actual in zip(predictions, actuals):
        bins[min(9, int(conf * 10))].append(1.0 if actual else 0.0)

    ece = 0.0
    for i, bin_data in enumerate(bins):
        if not bin_data:
            continue
        bin_conf = (i + 0.5) / 10
        bin_acc = sum(bin_data) / len(bin_data)
        ece += abs(bin_acc - bin_conf) * len(bin_data) / len(predictions)
    return ece
```

**Target:** ECE < 0.10 (khong phai 0.05 - thuc te kho dat)

## Threshold tuning theo domain

```yaml
# domain_configs/customer_support.yaml
confidence:
  auto_execute_threshold: 0.65  # Thap hon mac dinh vi domain it rui ro
  approval_threshold: 0.40
  weights:
    familiarity: 0.35
    clarity: 0.20
    risk: 0.20
    similarity: 0.15
    simplicity: 0.10
```

## Logging

Moi lan tinh confidence, log:

```json
{
  "event": "confidence_calculated",
  "task_id": "uuid",
  "trace_id": "uuid",
  "scores": {
    "familiarity": 0.75, "clarity": 0.90, "risk": 0.70,
    "similarity": 0.60, "simplicity": 0.85
  },
  "final": 0.74,
  "action": "request_approval"
}
```

Sau 1 thang, analyze va tune weights (HUMAN lam, khong auto).

## So voi spec cu

| Khía cạnh | Spec cu | Spec moi |
|---|---|---|
| So chi so | 5 | 5 (giong) |
| Trong so | Co dinh | Tune theo domain |
| Target ECE | < 0.05 | < 0.10 (thuc te) |
| Auto tune | Co | KHONG - human lam |
