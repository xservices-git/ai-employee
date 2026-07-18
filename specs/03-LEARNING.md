# Learning Loop (HUMAN GATE)

## Nguyen tac

**AI KHONG BAO GIO tu promote rule production.** Moi rule moi can human approve.

Ly do:
- AI hoc sai se pha he thong (rule sai apply cho moi task)
- Human review 1-2 rule/ngay la du, khong qua tai
- Shadow mode 1 tuan truoc khi active

## Flow

```
Task chay
  |
  v
Outcome (success/fail)
  |
  v
Feedback thu thap
  |
  +-- Implicit: task fail, user mo lai, retry count
  |
  +-- Explicit: user cham 1-5 sao, sua output, comment
  |
  v
Weekly cron: pattern detection
  |
  +-- Group feedback theo (task_type, error_code, domain)
  |
  +-- Neu 1 error lap 5+ lan -> propose rule
  |
  v
AI propose rules (status=pending)
  |
  v
HUMAN review qua UI
  |
  +-- Approve -> rule status=shadow
  |
  +-- Reject -> luu ly do, khong apply
  |
  +-- Modify -> sua rule, roi approve
  |
  v
Shadow mode 1 tuan (log nhung khong apply)
  |
  v
HUMAN promote -> rule status=active
```

## Code

### 1. Feedback collection

```python
# Implicit: track trong task result
def track_implicit_feedback(task: Task):
    if task.status == "failed":
        emit("feedback_implicit", {"task_id": task.id, "type": "failure"})
    if task.retry_count > 2:
        emit("feedback_implicit", {"task_id": task.id, "type": "retry"})

# Explicit: user POST /v1/tasks/{id}/feedback
@router.post("/v1/tasks/{task_id}/feedback")
async def submit_feedback(task_id: str, fb: Feedback):
    feedback = Feedback(
        id=uuid4(),
        task_id=task_id,
        score=fb.score,
        notes=fb.notes,
        corrections=fb.corrections,
    )
    db.add(feedback)
    await db.commit()
    emit("feedback_explicit", {"task_id": task_id, "score": fb.score})
    return {"id": feedback.id}
```

### 2. Weekly pattern detection (cron)

```python
# scripts/weekly_pattern_detection.py
async def detect_patterns():
    # Lay feedback 7 ngay qua
    feedbacks = db.query(Feedback).filter(
        Feedback.created_at >= datetime.now() - timedelta(days=7)
    ).all()

    # Group theo (task_type, error_code)
    groups = defaultdict(list)
    for fb in feedbacks:
        task = db.query(Task).get(fb.task_id)
        if task.error_message:
            error_code = extract_error_code(task.error_message)
            groups[(task.task_type, error_code)].append(fb)

    # Propose rules cho group co 5+ feedback
    proposed = []
    for (task_type, error_code), group in groups.items():
        if len(group) >= 5:
            rule = await llm_propose_rule(task_type, error_code, group)
            proposed.append(rule)

    # Luu vao learning_events
    for rule in proposed:
        event = LearningEvent(
            id=uuid4(),
            event_type="rule_proposed",
            rule_extracted=json.dumps(rule),
            status="pending",
        )
        db.add(event)
    await db.commit()

    return len(proposed)
```

### 3. Human review (UI)

Web UI cho phep user xem + approve/reject:

```
┌─────────────────────────────────────────┐
│  Proposed Rules (3)                     │
├─────────────────────────────────────────┤
│ Rule #abc-123                           │
│  Domain: stuvia                         │
│  Trigger: gen_mode=auto_gen, error 403  │
│  Action: Switch to demo_file_url        │
│  Source: 5 failures in 3 days           │
│  Example:                               │
│    Input: product_id=123, gen_mode=auto │
│    Action: Use pdf_url (demo)           │
│  Confidence: 0.87                       │
│                                         │
│  [Approve]  [Reject]  [Modify]          │
└─────────────────────────────────────────┘
```

### 4. Shadow mode

```python
async def apply_rules(task: Task) -> list[Rule]:
    active = load_rules(status="active")
    shadow = load_rules(status="shadow")

    # Active: apply that
    for rule in active:
        if match(rule, task):
            apply_rule(rule, task)

    # Shadow: chi log, khong apply
    for rule in shadow:
        if match(rule, task):
            log_shadow_hit(rule, task)
    # Sau 1 tuan: tinh success rate shadow, neu >= active -> cho promote
```

## Stats tracking

Moi rule co metadata:

```yaml
# Domain stats (DB, khong luu YAML)
success_count: 47
fail_count: 3
success_rate: 0.94
sample_size: 50
last_used_at: 2026-07-19
```

**Auto-disable** (neu fail nhieu):
- Sample size >= 20
- Success rate < 0.50
- Auto disable, alert admin

**Auto-promote shadow** (neu tot):
- Sample size >= 100
- Success rate >= 0.90
- De xuat promote (HUMAN quyet dinh, khong auto)

## Toc do thuc te

- 5-10 rules moi / thang (HUMAN review)
- 1-2 rule/ngay can review
- ~5 phut/rule review (test 5 cases)
- **KHONG the nhanh hon** neu muon an toan

## So voi spec cu

| Kha canh | Spec cu (auto) | Spec moi (HUMAN GATE) |
|---|---|---|
| Propose rule | Auto | Auto (LLM) |
| Promote rule | Auto | HUMAN (review UI) |
| So rule/thang | Vo han (ao) | 5-10 (thuc) |
| Risk | Hoc sai pha he thong | An toan, co nguoi check |

## Thay the A2A Protocol

Spec cu co A2A Protocol de 5 agents giao tiep. Spec moi KHONG CAN vi:
- 1 orchestrator, khong co agents rieng
- 5 buoc lien tiep, dung function call thay message bus
- Neu can scale: spawn nhieu orchestrator process (khong can protocol)
