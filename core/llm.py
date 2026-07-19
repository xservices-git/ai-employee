"""LLM client - Ollama local. Fallback to rule-based khi Ollama khong chay.

M1: goi Ollama. Neu fail -> rule-based mock.
M2: streaming + retry.
"""
from __future__ import annotations
import asyncio
import json
from typing import Optional

import httpx

from .config import SETTINGS


class LLMUnavailable(Exception):
    pass


async def _ollama_generate(prompt: str, model: str, timeout: float = 30.0) -> Optional[str]:
    """Generate tu Ollama. Tra ve None neu fail."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(
                f"{SETTINGS.ollama_base_url}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
            )
            if r.status_code != 200:
                return None
            data = r.json()
            return data.get("response", "")
    except Exception:
        return None


async def classify(text: str) -> dict:
    """Phan loai input vao 7 task types + detect domain.

    M1: dung Ollama neu co. Fallback: heuristic keyword match.
    """
    prompt = f"""Phan loai yeu cau sau vao 1 trong cac loai:
- data_processing: truy van/insert/update database
- content_generation: viet noi dung (email, bao cao, bai viet)
- classification_routing: phan loai ticket/email/don hang
- monitoring_alerting: kiem tra trang thai, canh bao
- research_summarization: tim kiem, tom tat tai lieu
- scheduling_coordination: tao lich, reminder, su kien
- decision_support: phan tich, goi y, so sanh

Tra ve JSON: {{"task_type": "...", "domain": "..."}} (domain: sales_ops, customer_support, hr_admin, hoac null)

Yeu cau: {text}
JSON:"""
    out = await _ollama_generate(prompt, SETTINGS.ollama_model_plan, timeout=10.0)
    if out:
        try:
            json_start = out.find("{")
            json_end = out.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(out[json_start:json_end])
        except Exception:
            pass
    return _classify_heuristic(text)


def _classify_heuristic(text: str) -> dict:
    """Rule-based fallback khi Ollama khong co."""
    t = text.lower()
    # Order matters: more specific first

    # Scheduling - phai co keyword cu the
    if any(k in t for k in ["dat lich ", "reminder", "hen gap", "tao cuoc hop", "calendar event"]):
        return {"task_type": "scheduling_coordination", "domain": None}

    # Decision support
    if any(k in t for k in [" nen chon", "lua chon giua", "goi y quyet dinh", "phuong an tot nhat"]):
        return {"task_type": "decision_support", "domain": None}

    # Classification
    if any(k in t for k in ["phan loai ticket", "route email", "phan nhom"]):
        return {"task_type": "classification_routing", "domain": None}

    # Monitoring - chi khi khong co keyword data processing
    has_data_kw = any(k in t for k in [
        "don hang", "khach hang", "invoice", "order", "ticket", "ho tro",
        "lookup", "truy van", "query", "lay thong tin", "doanh thu",
        "products", "bang ", "shop ", "sku", "id ", "so dien thoai",
    ])
    if not has_data_kw and any(k in t for k in ["alert", "canh bao", "trang thai he thong", "health check"]):
        return {"task_type": "monitoring_alerting", "domain": None}

    # Research - phai co keyword cu the
    if any(k in t for k in ["tom tat", "search", "nghien cuu", "research",
                            "summary", "wiki", "docs", "tai lieu", "pdf", "bai bao",
                            "ve ", "thong tin ve"]):
        # Nhung phai la research, khong phai data processing
        if "truy van" not in t and "query" not in t and "lay " not in t and "xem " not in t:
            return {"task_type": "research_summarization", "domain": None}

    # Content - phai co keyword viet/soan/draft/template/content/noi dung
    if any(k in t for k in ["viet ", "soan ", "draft ", "content", "template",
                            "thong bao", "email", "tin nhan", "bai viet",
                            "newsletter", "bao cao", "trang chu", "mo ta"]):
        return {"task_type": "content_generation", "domain": None}

    # Data processing - mac dinh cho cac lookup/query/get/check
    if has_data_kw:
        domain = "customer_support" if any(x in t for x in [
            "support", "khach", "ticket", "ho tro"
        ]) else "sales_ops" if any(x in t for x in [
            "doanh thu", "sales", "invoice", "order", "shop "
        ]) else None
        return {"task_type": "data_processing", "domain": domain}

    return {"task_type": "data_processing", "domain": None}


async def plan(text: str, task_type: str, domain: Optional[str], context: list[dict]) -> dict:
    """Lap ke hoach thuc thi.

    Tra ve: {steps: [...], confidence_clarity: 0-1, action: "..."}
    """
    ctx_str = "\n".join(
        f"- [{ep.get('task_type')}] {ep.get('input_text', '')[:80]} -> success={ep.get('success')}"
        for ep in context[:3]
    ) or "(no history)"
    prompt = f"""Lap ke hoach cho yeu cau:
Task type: {task_type}
Domain: {domain or 'unknown'}
Input: {text}

Lich su lien quan:
{ctx_str}

Tra ve JSON:
{{
  "steps": [{{"action": "ten_action", "tool": "ten_tool (optional)", "args": {{}}, "expected_output": "..."}}],
  "clarity": 0.0-1.0,
  "summary": "1 cau tom tat"
}}

JSON:"""
    out = await _ollama_generate(prompt, SETTINGS.ollama_model_plan, timeout=15.0)
    if out:
        try:
            js = out.find("{")
            je = out.rfind("}") + 1
            if js >= 0 and je > js:
                return json.loads(out[js:je])
        except Exception:
            pass
    return _plan_heuristic(text, task_type, domain)


def _plan_heuristic(text: str, task_type: str, domain: Optional[str]) -> dict:
    return {
        "steps": [
            {"action": "echo", "args": {"text": text}, "expected_output": "text"},
        ],
        "clarity": 0.85,
        "summary": f"Echo task {task_type}",
    }


async def review(input_text: str, output: dict, expected: Optional[dict] = None) -> dict:
    """Review ket qua, tra ve score 0-1 + issues."""
    if expected is None:
        return {"score": 0.75, "issues": [], "ok": True}
    score = 0.8
    issues = []
    if expected.get("task_type") and output.get("task_type") != expected["task_type"]:
        score -= 0.3
        issues.append(f"task_type mismatch: {output.get('task_type')} != {expected['task_type']}")
    if expected.get("must_contain"):
        out_text = json.dumps(output, ensure_ascii=False)
        for kw in expected["must_contain"]:
            if kw.lower() not in out_text.lower():
                score -= 0.2
                issues.append(f"missing keyword: {kw}")
    score = max(0.0, min(1.0, score))
    return {"score": round(score, 3), "issues": issues, "ok": score >= 0.5}
