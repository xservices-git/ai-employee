"""Orchestrator - 1 process, 5 buoc state machine.

classify -> plan -> approval -> execute -> review -> store

Spec: docs/01-ARCHITECTURE.md
"""
from __future__ import annotations
import asyncio
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

from . import db, memory
from . import llm
from .config import SETTINGS


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ms(t0: float) -> float:
    return round((time.time() - t0) * 1000, 2)


def _span_id() -> str:
    return uuid.uuid4().hex[:16]


def _record(trace_id: str, name: str, parent: Optional[str], t0: float,
            attrs: Optional[dict] = None, status: str = "ok") -> None:
    db.record_span(
        trace_id=trace_id,
        span_id=_span_id(),
        parent_span_id=parent,
        name=name,
        start_time=datetime.fromtimestamp(t0, timezone.utc).isoformat(),
        end_time=_now(),
        duration_ms=_ms(t0),
        attributes=attrs,
        status=status,
    )


# ============ 7 task types ============

VALID_TASK_TYPES = {
    "data_processing",
    "content_generation",
    "classification_routing",
    "monitoring_alerting",
    "research_summarization",
    "scheduling_coordination",
    "decision_support",
}


# ============ Risk theo task_type + action ============

RISK_MATRIX = {
    ("data_processing", "read"): 0.05,
    ("data_processing", "write"): 0.35,
    ("data_processing", "delete"): 0.85,
    ("content_generation", "draft"): 0.15,
    ("content_generation", "send"): 0.55,
    ("classification_routing", "classify"): 0.10,
    ("monitoring_alerting", "check"): 0.05,
    ("monitoring_alerting", "alert"): 0.40,
    ("research_summarization", "fetch"): 0.10,
    ("research_summarization", "summarize"): 0.20,
    ("scheduling_coordination", "create"): 0.25,
    ("scheduling_coordination", "cancel"): 0.65,
    ("decision_support", "analyze"): 0.15,
    ("decision_support", "recommend"): 0.30,
}


def calc_risk(task_type: str, action: str) -> float:
    """0-1: do rui ro cua action."""
    return RISK_MATRIX.get((task_type, action), 0.5)


# ============ Execute (M1: 1 handler per task_type) ============

async def _execute(plan: dict) -> dict:
    """Doc input, tra ket qua (echo + parse). M2 se goi MCP."""
    steps = plan.get("steps", [])
    out = {"steps_executed": []}
    for step in steps:
        action = step.get("action", "echo")
        args = step.get("args", {})
        if action == "echo":
            out["steps_executed"].append({"action": "echo", "out": args.get("text", "")[:200]})
        elif action == "classify":
            out["steps_executed"].append({"action": "classify", "out": "ok"})
        else:
            out["steps_executed"].append({"action": action, "out": "stub"})
    return out


async def _execute_content_generation(plan: dict) -> dict:
    steps = plan.get("steps", [])
    out = {"steps_executed": []}
    for step in steps:
        action = step.get("action", "draft")
        if action == "draft":
            out["steps_executed"].append({
                "action": "draft",
                "subject": f"Draft for: {step.get('args', {}).get('text', '')[:50]}",
                "body": "(stub - M2 will call LLM to generate content)",
            })
        else:
            out["steps_executed"].append({"action": action, "out": "stub"})
    return out


async def _execute_classification(plan: dict) -> dict:
    return {"label": "general", "confidence": 0.8, "route_to": "default"}


async def _execute_monitoring(plan: dict) -> dict:
    return {
        "status": "ok",
        "checked_at": _now(),
        "items": [{"name": "api", "healthy": True}, {"name": "db", "healthy": True}],
    }


async def _execute_research(plan: dict) -> dict:
    return {
        "sources": 0,
        "summary": "(stub - M2 will call web_search/fetch_url MCP)",
    }


async def _execute_scheduling(plan: dict) -> dict:
    return {
        "event_id": str(uuid.uuid4()),
        "scheduled_at": _now(),
        "summary": plan.get("summary", "Event"),
    }


async def _execute_decision(plan: dict) -> dict:
    return {
        "recommendation": "Option A (stub)",
        "alternatives": ["Option B", "Option C"],
        "confidence": 0.65,
    }


EXECUTORS = {
    "data_processing": _execute,
    "content_generation": _execute_content_generation,
    "classification_routing": _execute_classification,
    "monitoring_alerting": _execute_monitoring,
    "research_summarization": _execute_research,
    "scheduling_coordination": _execute_scheduling,
    "decision_support": _execute_decision,
}


# ============ Confidence (5 chi so) ============

def calculate_confidence(
    task_type: str,
    plan: dict,
    domain: Optional[str],
) -> dict:
    """5 chi so, tra ve dict voi scores + final."""
    familiarity = memory.calculate_familiarity(task_type, domain)
    clarity = plan.get("clarity", 0.7)
    action = plan.get("steps", [{}])[0].get("action", "unknown") if plan.get("steps") else "unknown"
    risk = calc_risk(task_type, action)
    risk_inv = 1.0 - risk
    similar = memory.search_similar(plan.get("summary", ""), task_type=task_type, top_k=3)
    similarity = (sum(s["score"] for s in similar) / len(similar)) if similar else 0.5
    steps = plan.get("steps", [])
    step_penalty = min(0.5, len(steps) * 0.05)
    simplicity = max(0.0, 1.0 - step_penalty)

    final = (
        familiarity * 0.30
        + clarity * 0.20
        + risk_inv * 0.25
        + similarity * 0.15
        + simplicity * 0.10
    )
    return {
        "familiarity": round(familiarity, 3),
        "clarity": round(clarity, 3),
        "risk_inv": round(risk_inv, 3),
        "similarity": round(similarity, 3),
        "simplicity": round(simplicity, 3),
        "final": round(final, 3),
    }


# ============ Main orchestrator ============

async def run(task_id: str) -> dict:
    """Chay 1 task theo state machine. Tra ve task object final."""
    task = db.get_task(task_id)
    if not task:
        raise ValueError(f"Task not found: {task_id}")
    trace_id = task["trace_id"]
    input_text = (task.get("input_data") or {}).get("text", "")
    t_total = time.time()

    db.update_task(task_id, status="running")

    # Buoc 1: classify
    t0 = time.time()
    classification = await llm.classify(input_text)
    task_type = classification.get("task_type", "data_processing")
    if task_type not in VALID_TASK_TYPES:
        task_type = "data_processing"
    domain = classification.get("domain") or task.get("domain")
    _record(trace_id, "classify", None, t0,
            {"task_type": task_type, "domain": domain})
    # Luu tam classification (se duoc ghi lai sau buoc plan voi full plan)
    db.update_task(task_id, plan={"classification": classification, "task_type": task_type, "domain": domain})
    db.upsert_skill(f"classify:{task_type}", domain=domain, success=True)

    # Buoc 2: plan + memory context
    t0 = time.time()
    context = memory.search_similar(input_text, task_type=task_type, top_k=5)
    plan = await llm.plan(input_text, task_type, domain, context)
    _record(trace_id, "plan", None, t0,
            {"steps": len(plan.get("steps", [])), "context_used": len(context)})

    # Gan classification vao plan de downstream co the doc
    plan = {**plan, "classification": classification}

    # Buoc 3: confidence + approval gate
    t0 = time.time()
    conf = calculate_confidence(task_type, plan, domain)
    action = plan.get("steps", [{}])[0].get("action", "unknown") if plan.get("steps") else "unknown"
    risk = calc_risk(task_type, action)
    needs_approval = (
        conf["final"] < SETTINGS.auto_approve_threshold
        or risk >= 0.6
    )
    _record(trace_id, "confidence", None, t0, conf | {"risk": risk})

    if needs_approval:
        approval = db.create_approval(
            task_id=task_id,
            proposal={"plan": plan, "action": action, "risk": risk},
            risk_level="high" if risk >= 0.7 else "medium",
            reason=f"confidence={conf['final']:.2f}, risk={risk:.2f}",
        )
        db.update_task(task_id, status="waiting_approval", confidence=conf["final"], plan=plan)
        # Re-fetch de co plan moi nhat
        updated = db.get_task(task_id)
        return {**updated, "approval": approval}

    # Buoc 4: execute
    t0 = time.time()
    try:
        executor = EXECUTORS.get(task_type, _execute)
        result = await executor(plan)
        _record(trace_id, "execute", None, t0, {"task_type": task_type})
    except Exception as e:
        _record(trace_id, "execute", None, t0, {"error": str(e)}, status="error")
        db.update_task(task_id, status="failed", error_message=f"execute failed: {e}",
                       confidence=conf["final"], plan=plan)
        return {**task, "status": "failed", "error_message": str(e)}

    # Buoc 5: review
    t0 = time.time()
    review = await llm.review(input_text, result)
    _record(trace_id, "review", None, t0, review)

    # Final
    success = review.get("ok", True) and result is not None
    db.update_task(
        task_id,
        status="completed" if success else "failed",
        result=result,
        confidence=conf["final"],
        plan=plan,
        error_message=None if success else "; ".join(review.get("issues", [])),
    )

    # Async: store episode (dung thread rieng de tranh event loop conflict)
    import threading
    threading.Thread(
        target=_store_episode_sync,
        args=(task_id, task_type, domain, input_text, str(result)[:500], success, conf["final"]),
        daemon=True,
    ).start()

    _record(trace_id, "store", None, time.time(), {"stored": True})
    _record(trace_id, "total", None, t_total, {"duration_ms": _ms(t_total)})

    return {**db.get_task(task_id), "review": review}


def _store_episode_sync(task_id, task_type, domain, input_text, output_text, success, confidence):
    try:
        memory.store_episode(
            task_id=task_id, task_type=task_type, domain=domain,
            input_text=input_text, output_text=output_text,
            success=success, confidence=confidence,
        )
    except Exception as e:
        print(f"[store_episode] error: {e}")


async def _store_episode_async(**kwargs) -> None:
    try:
        memory.store_episode(**kwargs)
    except Exception:
        pass


# ============ Approval resume ============

async def resume_after_approval(task_id: str, approval_id: str, decision: str,
                                 modified_args: Optional[dict] = None) -> dict:
    """Tiep tuc task sau khi user approve/reject."""
    task = db.get_task(task_id)
    if not task or task["status"] != "waiting_approval":
        return task or {}

    if decision == "rejected":
        db.update_task(task_id, status="cancelled", error_message="user rejected")
        return db.get_task(task_id)

    # approved hoac modified
    plan = task.get("plan", {}) or {}
    if modified_args:
        plan = {**plan, "steps": [{**s, "args": {**s.get("args", {}), **modified_args}}
                                   for s in plan.get("steps", [])]}

    t0 = time.time()
    task_type = plan.get("task_type") or plan.get("classification", {}).get("task_type", "data_processing")
    executor = EXECUTORS.get(task_type, _execute)
    result = await executor(plan)
    db.record_span(
        trace_id=task["trace_id"],
        span_id=_span_id(),
        parent_span_id=None,
        name="execute_after_approval",
        start_time=datetime.fromtimestamp(t0, timezone.utc).isoformat(),
        end_time=_now(),
        duration_ms=_ms(t0),
        attributes={"task_type": task_type, "decision": decision},
        status="ok",
    )
    review = await llm.review("", result)
    db.update_task(
        task_id,
        status="completed",
        result=result,
        plan=plan,
    )
    asyncio.create_task(_store_episode_async(
        task_id=task_id,
        task_type=task_type,
        domain=task.get("domain"),
        input_text=task.get("input_data", {}).get("text", ""),
        output_text=str(result)[:500],
        success=True,
        confidence=task.get("confidence"),
    ))
    return db.get_task(task_id)