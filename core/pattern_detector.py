"""Pattern detector - quet failed tasks + feedback, suggest rules.

M2 cron: chay hang tuan (hoac sau moi N tasks) de detect:
- Failed tasks co pattern chung (cung domain, cung keyword, cung action)
- User corrections co xu huong sua thanh X
- Score thap < 3 nhieu lan voi cung task_type/domain

Rule proposal tu LLM (hoac rule-based fallback neu khong co Ollama).
"""
from __future__ import annotations
import re
from collections import Counter, defaultdict
from typing import Optional

from . import db


# Stopwords tieng Viet + English co ban
STOPWORDS = {
    "toi", "ban", "cho", "cua", "khong", "thi", "den", "mot", "nhu", "the",
    "this", "that", "with", "from", "have", "been", "will", "your", "their",
    "the", "and", "for", "are", "but", "not", "you", "all", "can", "her",
    "hay", "hoac", "neu", "tuy", "nhung", "vi", "da", "dang", "se", "duoc",
    "lam", "theo", "de", "tren", "duoi", "trong", "ngoai", "khi", "luc",
}

def _tokenize(text: str) -> list[str]:
    """Lowercase + remove punctuation, return meaningful tokens."""
    if not text:
        return []
    t = text.lower()
    t = re.sub(r"[^a-z0-9\sáàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ_]", " ", t)
    tokens = [w for w in t.split() if len(w) > 2 and w not in STOPWORDS]
    return tokens


def detect_failed_patterns(
    task_type: Optional[str] = None,
    domain: Optional[str] = None,
    min_occurrences: int = 3,
    lookback_days: int = 30,
) -> list[dict]:
    """Tim cac pattern xuat hien trong failed tasks / low-score feedback.

    Returns: [{pattern_keyword, task_type, domain, count, sample_task_ids}, ...]
    """
    db_conn = db.get_db()
    # Failed tasks trong N ngay
    rows = db_conn.execute(
        """SELECT t.id, t.task_type, t.domain, t.input_data, t.error_message,
                  f.score, f.notes, f.corrections
           FROM tasks t
           LEFT JOIN feedback f ON f.task_id = t.id
           WHERE (t.status = 'failed' OR (f.score IS NOT NULL AND f.score <= 2))
             AND t.created_at >= datetime('now', ?)""",
        (f"-{lookback_days} days",),
    ).fetchall()

    # Group by (task_type, domain) + token
    groups = defaultdict(list)
    for r in rows:
        if task_type and r["task_type"] != task_type:
            continue
        if domain and r["domain"] != domain:
            continue
        input_text = json_load(r["input_data"])
        text = input_text.get("text", "") if isinstance(input_text, dict) else str(input_text)
        tokens = _tokenize(text)
        if not tokens:
            continue
        # Lay top 3 tokens quan trong
        for tok in set(tokens[:30]):  # chi xet 30 token dau de khong qua nhieu
            key = (r["task_type"], r["domain"], tok)
            groups[key].append(r["id"])

    # Filter pattern xuat hien >= min_occurrences
    patterns = []
    for (tt, dom, tok), task_ids in groups.items():
        if len(task_ids) >= min_occurrences:
            patterns.append({
                "pattern_keyword": tok,
                "task_type": tt,
                "domain": dom,
                "count": len(task_ids),
                "sample_task_ids": task_ids[:5],
            })
    return sorted(patterns, key=lambda x: -x["count"])


def _suggest_rule_text(pattern: dict) -> str:
    """Sinh rule text tu pattern. M2: LLM call, M2-mini: rule-based."""
    tok = pattern["pattern_keyword"]
    tt = pattern["task_type"]
    dom = pattern["domain"]
    count = pattern["count"]

    templates = [
        f"Khi input chua tu khoa '{tok}' (task={tt}, domain={dom}), can xac minh them truoc khi xu ly",
        f"Task {tt}/{dom} voi '{tok}' xuat hien {count} lan - can them validation step",
        f"Tranh auto-execute khi gap pattern '{tok}' - yeu cau approval",
        f"Neu gap '{tok}', fallback sang rule-based thay LLM (do LLM hay sai)",
    ]
    # Lay rule cu nhat chua duoc propose
    return templates[0]


def detect_correction_patterns(lookback_days: int = 30) -> list[dict]:
    """Tim user corrections co xu huong sua thanh gi.

    Vi du: corrections = {"old_field": "new_value"} xuat hien nhieu lan
    """
    db_conn = db.get_db()
    rows = db_conn.execute(
        """SELECT f.corrections, t.task_type, t.domain
           FROM feedback f
           JOIN tasks t ON t.id = f.task_id
           WHERE f.corrections IS NOT NULL
             AND f.created_at >= datetime('now', ?)""",
        (f"-{lookback_days} days",),
    ).fetchall()

    # Group corrections
    counter = Counter()
    for r in rows:
        corr = json_load(r["corrections"])
        if not isinstance(corr, dict):
            continue
        # Flatten key=value
        for k, v in corr.items():
            if isinstance(v, (str, int, float, bool)):
                counter[(r["task_type"], r["domain"], str(k), str(v))] += 1
    out = []
    for (tt, dom, k, v), cnt in counter.most_common(20):
        if cnt >= 2:  # it nhat 2 lan
            out.append({
                "field": k,
                "new_value": v,
                "task_type": tt,
                "domain": dom,
                "count": cnt,
            })
    return out


def json_load(s):
    """Load JSON safe."""
    import json
    if not s:
        return {}
    try:
        return json.loads(s)
    except Exception:
        return {}


def run_pattern_detection(
    min_occurrences: int = 3,
    lookback_days: int = 30,
    dry_run: bool = False,
) -> dict:
    """Main entry - chay detection + propose rules.

    Args:
        dry_run: Neu True, khong ghi proposed_rules vao DB (chi detect + count).

    Returns: {patterns_found, rules_proposed, corrections_found}
    """
    # 1. Detect failed patterns
    patterns = detect_failed_patterns(
        min_occurrences=min_occurrences, lookback_days=lookback_days,
    )
    rules_proposed = []
    for pat in patterns[:10]:  # chi propose 10 pattern top
        rule_text = _suggest_rule_text(pat)
        # Check duplicate: da propose chua?
        existing = db.list_proposed_rules(domain=pat["domain"], limit=100)
        if any(r["rule_text"] == rule_text for r in existing):
            continue
        if dry_run:
            rules_proposed.append({"rule_text": rule_text, "pattern": pat})
            continue
        r = db.create_proposed_rule(
            rule_text=rule_text,
            condition_pattern=f"task_type={pat['task_type']} & keyword={pat['pattern_keyword']}",
            action_type="require_approval",
            domain=pat["domain"],
            proposed_by="pattern_detector_v1",
        )
        rules_proposed.append(r)

    # 2. Detect corrections
    corrections = detect_correction_patterns(lookback_days=lookback_days)
    for c in corrections[:5]:
        rule_text = f"Mac dinh gia tri '{c['field']}' = '{c['new_value']}' cho task {c['task_type']}/{c['domain']}"
        existing = db.list_proposed_rules(domain=c["domain"], limit=100)
        if any(r["rule_text"] == rule_text for r in existing):
            continue
        if dry_run:
            rules_proposed.append({"rule_text": rule_text, "correction": c})
            continue
        r = db.create_proposed_rule(
            rule_text=rule_text,
            condition_pattern=f"task_type={c['task_type']} & field={c['field']}",
            action_type="default_value",
            domain=c["domain"],
            proposed_by="correction_detector_v1",
        )
        rules_proposed.append(r)

    return {
        "patterns_found": len(patterns),
        "rules_proposed": len(rules_proposed),
        "corrections_found": len(corrections),
        "proposed_rule_ids": [r["id"] for r in rules_proposed] if not dry_run else [],
    }
