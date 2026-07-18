"""Common types used across the system."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


# === Enums ===

class TaskType(StrEnum):
    """7 task groups (domain-agnostic)."""
    DATA_PROCESSING = "data_processing"
    CONTENT_GENERATION = "content_generation"
    CLASSIFICATION_ROUTING = "classification_routing"
    MONITORING_ALERTING = "monitoring_alerting"
    RESEARCH_SUMMARIZATION = "research_summarization"
    SCHEDULING_COORDINATION = "scheduling_coordination"
    DECISION_SUPPORT = "decision_support"


class TaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalDecision(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"


class AgentRole(StrEnum):
    CLASSIFIER = "classifier"
    PLANNER = "planner"
    EXECUTOR = "executor"
    CRITIC = "critic"
    MEMORY_CURATOR = "memory_curator"
    SUPERVISOR = "supervisor"
    USER = "user"


class MessageType(StrEnum):
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    ERROR = "error"


# === Base models ===

class BaseSchema(BaseModel):
    """Base Pydantic model."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        use_enum_values=False,
        populate_by_name=True,
    )


# === Core schemas ===

class TaskInput(BaseSchema):
    """Input for creating a new task."""
    input: str = Field(..., min_length=1, max_length=10000)
    domain: str | None = None
    user_id: str
    context: dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=3, ge=1, le=5)


class PlanStep(BaseSchema):
    """A single step in a plan."""
    step_id: int
    action: str
    tool: str | None = None
    args: dict[str, Any] = Field(default_factory=dict)
    expected_result: str | None = None
    risk_level: RiskLevel = RiskLevel.LOW


class Plan(BaseSchema):
    """A plan consisting of multiple steps."""
    steps: list[PlanStep]
    reasoning: str = ""
    estimated_duration_sec: int = 30


class ConfidenceScore(BaseSchema):
    """Breakdown of confidence calculation."""
    familiarity: float = 0.0
    clarity: float = 0.0
    risk: float = 0.0
    similarity: float = 0.0
    simplicity: float = 0.0

    @property
    def final(self) -> float:
        """Weighted final score."""
        return (
            self.familiarity * 0.30
            + self.clarity * 0.20
            + self.risk * 0.25
            + self.similarity * 0.15
            + self.simplicity * 0.10
        )


class Task(BaseSchema):
    """A task in the system."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    task_type: TaskType | None = None
    domain: str | None = None
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 3
    input_data: dict[str, Any]
    plan: Plan | None = None
    result: dict[str, Any] | None = None
    confidence: ConfidenceScore | None = None
    error_message: str | None = None
    feedback_id: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None


class ApprovalRequest(BaseSchema):
    """An approval request for a task."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    proposal: dict[str, Any]
    risk_level: RiskLevel
    reason: str = ""
    precedents: list[dict[str, Any]] = Field(default_factory=list)
    decision: ApprovalDecision = ApprovalDecision.PENDING
    modified_args: dict[str, Any] | None = None
    feedback: str | None = None
    approver_id: str | None = None
    decided_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class A2AMessage(BaseSchema):
    """Agent-to-Agent message."""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str
    parent_message_id: str | None = None
    from_agent: AgentRole
    to_agent: AgentRole | Literal["broadcast"]
    type: MessageType
    action: str
    payload: dict[str, Any] = Field(default_factory=dict)
    task_id: str
    user_id: str
    domain: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    deadline_ms: int | None = None
    attempt: int = 1
    correlation_id: str | None = None
