"""Approvals API: list, decide."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_orchestrator
from api.schemas import ApprovalDecisionRequest, ApprovalResponse
from core.orchestrator import Orchestrator

router = APIRouter(prefix="/v1/approvals", tags=["approvals"])


@router.get("", response_model=list[ApprovalResponse])
async def list_pending_approvals(
    orchestrator: Orchestrator = Depends(get_orchestrator),
) -> list[ApprovalResponse]:
    """List pending approval requests."""
    return [
        ApprovalResponse(
            id=a.id,
            task_id=a.task_id,
            proposal=a.proposal,
            risk_level=a.risk_level.value,
            reason=a.reason,
            decision=a.decision.value,
            created_at=a.created_at,
            decided_at=a.decided_at,
        )
        for a in orchestrator._pending_approvals.values()  # type: ignore[attr-defined]
        if a.decision.value == "pending"
    ]


@router.post("/{approval_id}/decide", response_model=ApprovalResponse)
async def decide_approval(
    approval_id: str,
    body: ApprovalDecisionRequest,
    orchestrator: Orchestrator = Depends(get_orchestrator),
) -> ApprovalResponse:
    """Approve, reject, or modify an approval request."""
    if approval_id not in orchestrator._pending_approvals:  # type: ignore[attr-defined]
        raise HTTPException(status_code=404, detail="Approval not found")

    await orchestrator.submit_approval(
        approval_id=approval_id,
        decision=body.decision,
        modified_args=body.modified_args,
        feedback=body.feedback,
    )
    approval = orchestrator._pending_approvals[approval_id]  # type: ignore[attr-defined]
    return ApprovalResponse(
        id=approval.id,
        task_id=approval.task_id,
        proposal=approval.proposal,
        risk_level=approval.risk_level.value,
        reason=approval.reason,
        decision=approval.decision.value,
        created_at=approval.created_at,
        decided_at=approval.decided_at,
    )
