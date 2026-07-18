"""FastAPI app - theo OpenAPI spec/00-OPENAPI.yaml."""
from __future__ import annotations
import asyncio
import sys
from pathlib import Path

# Allow running as script
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Any

from core import db, orchestrator, memory
from core.config import SETTINGS


app = FastAPI(
    title="AI Employee",
    version="0.1.0",
    description="1 orchestrator + 3 memory tang + HUMAN GATE",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ Schemas ============

class TaskCreate(BaseModel):
    input: str = Field(..., description="Raw user message")
    domain: Optional[str] = None
    user_id: str = "local"
    priority: int = 3
    auto_run: bool = True


class FeedbackCreate(BaseModel):
    score: int = Field(..., ge=1, le=5)
    notes: Optional[str] = None
    corrections: Optional[dict] = None


class ApprovalDecision(BaseModel):
    decision: str = Field(..., pattern="^(approved|rejected|modified)$")
    feedback: Optional[str] = None
    modified_args: Optional[dict] = None


# ============ Health ============

@app.on_event("startup")
def _startup():
    db.get_db()  # init schema
    print(f"[startup] ai-employee v0.1.0, env={SETTINGS.env}, data_dir={SETTINGS.data_dir}")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": app.version,
        "env": SETTINGS.env,
    }


@app.get("/")
def root():
    return {
        "name": "ai-employee",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "spec": "../specs/00-OPENAPI.yaml",
    }


# ============ Tasks ============

@app.post("/v1/tasks")
def create_task(req: TaskCreate, bg: BackgroundTasks):
    """Tao task moi. Neu auto_run=True, chay ngay trong background."""
    task = db.create_task(
        task_type="pending",  # se phan loai o buoc classify
        input_data={"text": req.input},
        user_id=req.user_id,
        domain=req.domain,
        priority=req.priority,
    )
    if req.auto_run:
        # Dung thread rieng de khong block FastAPI response.
        import threading
        threading.Thread(target=_run_blocking, args=(task["id"],), daemon=True).start()
    return JSONResponse(task, status_code=201)


def _run_blocking(task_id: str):
    """Chay orchestrator dong bo trong thread (orchestrator.run la async)."""
    import asyncio
    try:
        asyncio.run(orchestrator.run(task_id))
    except Exception as e:
        db.update_task(task_id, status="failed", error_message=str(e)[:500])


@app.get("/v1/tasks")
def list_tasks(status: Optional[str] = None, task_type: Optional[str] = None,
               limit: int = 50, offset: int = 0):
    items, total = db.list_tasks(status=status, task_type=task_type,
                                  limit=limit, offset=offset)
    return {"items": items, "total": total}


@app.get("/v1/tasks/{task_id}")
def get_task(task_id: str):
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(404, f"Task not found: {task_id}")
    return task


@app.get("/v1/tasks/{task_id}/trace")
def get_task_trace(task_id: str):
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(404, f"Task not found: {task_id}")
    spans = db.list_traces(task["trace_id"])
    return {"task_id": task_id, "trace_id": task["trace_id"], "spans": spans}


@app.post("/v1/tasks/{task_id}/feedback")
def submit_feedback(task_id: str, req: FeedbackCreate):
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(404, f"Task not found: {task_id}")
    fb = db.create_feedback(task_id, req.score, req.notes, req.corrections)
    return JSONResponse(fb, status_code=201)


@app.delete("/v1/tasks/{task_id}")
def cancel_task(task_id: str):
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(404, f"Task not found: {task_id}")
    if task["status"] in ("completed", "failed", "cancelled"):
        raise HTTPException(400, f"Task already {task['status']}")
    db.update_task(task_id, status="cancelled")
    return {"id": task_id, "status": "cancelled"}


# ============ Approvals ============

@app.get("/v1/approvals")
def list_approvals(status: str = "pending"):
    if status == "pending":
        return {"items": db.list_pending_approvals()}
    db_conn = db.get_db()
    rows = db_conn.execute(
        "SELECT * FROM approval_requests WHERE decision = ? ORDER BY created_at DESC LIMIT 100",
        (status,),
    ).fetchall()
    return {"items": [db.get_approval(r["id"]) for r in rows]}


@app.get("/v1/approvals/{approval_id}")
def get_approval(approval_id: str):
    ap = db.get_approval(approval_id)
    if not ap:
        raise HTTPException(404, f"Approval not found: {approval_id}")
    return ap


@app.post("/v1/approvals/{approval_id}/decide")
def decide_approval(approval_id: str, req: ApprovalDecision):
    ap = db.get_approval(approval_id)
    if not ap:
        raise HTTPException(404, f"Approval not found: {approval_id}")
    if ap["decision"] != "pending":
        raise HTTPException(400, f"Approval already decided: {ap['decision']}")
    updated = db.decide_approval(approval_id, req.decision, req.feedback)
    if req.decision in ("approved", "modified"):
        import threading
        threading.Thread(
            target=_resume_blocking,
            args=(ap["task_id"], approval_id, req.decision, req.modified_args),
            daemon=True,
        ).start()
    return updated


def _resume_blocking(task_id, approval_id, decision, modified_args):
    import asyncio
    try:
        asyncio.run(orchestrator.resume_after_approval(task_id, approval_id, decision, modified_args))
    except Exception as e:
        db.update_task(task_id, status="failed", error_message=str(e)[:500])


# ============ Memory ============

class MemorySearch(BaseModel):
    query: str
    task_type: Optional[str] = None
    top_k: int = 5


@app.post("/v1/memory/search")
def search_memory(req: MemorySearch):
    results = memory.search_similar(req.query, task_type=req.task_type, top_k=req.top_k)
    return {"results": results, "count": len(results)}


# ============ Rules (HUMAN GATE - stub cho M1) ============

@app.get("/v1/rules")
def list_rules():
    """M1: tra ve rule tu DB metadata. M2: gop voi YAML."""
    db_conn = db.get_db()
    rows = db_conn.execute("SELECT * FROM skill_metadata ORDER BY last_used_at DESC").fetchall()
    items = []
    for r in rows:
        items.append({
            "id": r["id"],
            "skill_name": r["skill_name"],
            "domain": r["domain"],
            "success_rate": r["success_rate"],
            "sample_size": r["sample_size"],
            "status": r["status"],
            "last_used_at": r["last_used_at"],
        })
    return {"items": items, "total": len(items)}


# ============ Eval (stub) ============

@app.get("/v1/eval/status")
def eval_status():
    return {
        "m1_status": "ready",
        "task_types_supported": list(orchestrator.VALID_TASK_TYPES),
        "mcp_servers": [],  # M2: list actual servers
        "test_count": 0,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=SETTINGS.port, reload=False)
