"""Pydantic schemas for API request/response."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TaskCreateRequest(BaseModel):
    """POST /v1/tasks body."""
    model_config = ConfigDict(str_strip_whitespace=True)

    input: str = Field(..., min_length=1, max_length=10000, description="Raw user message")
    domain: str | None = Field(default=None, description="Optional domain hint")
    user_id: str = Field(..., description="User ID")
    context: dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=3, ge=1, le=5)


class TaskResponse(BaseModel):
    """Task object in API responses."""
    id: str
    trace_id: str
    user_id: str
    task_type: str | None = None
    domain: str | None = None
    status: str
    priority: int
    input_data: dict[str, Any]
    plan: dict[str, Any] | None = None
    result: dict[str, Any] | None = None
    confidence: dict[str, Any] | None = None
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class TaskListResponse(BaseModel):
    items: list[TaskResponse]
    total: int


class FeedbackRequest(BaseModel):
    """POST /v1/tasks/{id}/feedback body."""
    score: int = Field(..., ge=1, le=5)
    notes: str = ""
    corrections: dict[str, Any] | None = None
    tags: list[str] = Field(default_factory=list)


class FeedbackResponse(BaseModel):
    id: str
    task_id: str
    score: int
    events_created: int
    created_at: datetime


class ApprovalDecisionRequest(BaseModel):
    """POST /v1/approvals/{id}/decide body."""
    decision: str = Field(..., pattern="^(approved|rejected|modified)$")
    modified_args: dict[str, Any] | None = None
    feedback: str | None = None
    approver_id: str | None = None


class ApprovalResponse(BaseModel):
    id: str
    task_id: str
    proposal: dict[str, Any]
    risk_level: str
    reason: str
    decision: str
    created_at: datetime
    decided_at: datetime | None = None


class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_sec: int


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None
