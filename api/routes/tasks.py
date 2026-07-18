"""Tasks API: create, get, list, cancel, feedback."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.deps import get_orchestrator
from api.schemas import (
    FeedbackRequest,
    FeedbackResponse,
    TaskCreateRequest,
    TaskListResponse,
    TaskResponse,
)
from core.common.types import TaskInput
from core.orchestrator import Orchestrator

router = APIRouter(prefix="/v1/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    body: TaskCreateRequest,
    orchestrator: Orchestrator = Depends(get_orchestrator),
) -> TaskResponse:
    """Create a new task and process it (synchronous in M1)."""
    task_input = TaskInput(
        input=body.input,
        domain=body.domain,
        user_id=body.user_id,
        context=body.context,
        priority=body.priority,
    )
    task = await orchestrator.process_task(task_input)
    return TaskResponse(**task.model_dump())


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    status_filter: str | None = Query(default=None, alias="status"),
    domain: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    orchestrator: Orchestrator = Depends(get_orchestrator),
) -> TaskListResponse:
    """List tasks (M1: stub, returns empty)."""
    # TODO M2: implement with SQLite
    return TaskListResponse(items=[], total=0)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    orchestrator: Orchestrator = Depends(get_orchestrator),
) -> TaskResponse:
    """Get task by ID."""
    raise HTTPException(status_code=404, detail="Not implemented in M1")


@router.post("/{task_id}/feedback", response_model=FeedbackResponse, status_code=201)
async def submit_feedback(
    task_id: str,
    body: FeedbackRequest,
    orchestrator: Orchestrator = Depends(get_orchestrator),
) -> FeedbackResponse:
    """Submit feedback for a task. Triggers learning loop."""
    from core.learning import LearningLoop

    loop = LearningLoop(memory=orchestrator.memory)
    events = await loop.process_feedback(
        task_id=task_id,
        score=body.score,
        notes=body.notes,
        corrections=body.corrections,
    )
    return FeedbackResponse(
        id=f"fb_{task_id}",
        task_id=task_id,
        score=body.score,
        events_created=len(events),
        created_at=events[0].created_at if events else __import__("datetime").datetime.utcnow(),
    )


@router.delete("/{task_id}", status_code=204)
async def cancel_task(
    task_id: str,
    orchestrator: Orchestrator = Depends(get_orchestrator),
) -> None:
    """Cancel a task."""
    # TODO M2
    return None
