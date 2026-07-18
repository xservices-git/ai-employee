"""Test types and schemas."""

from __future__ import annotations

import uuid

from core.common.types import (
    A2AMessage,
    AgentRole,
    ConfidenceScore,
    MessageType,
    Plan,
    PlanStep,
    RiskLevel,
    Task,
    TaskInput,
    TaskStatus,
    TaskType,
)


def test_confidence_score_final():
    """ConfidenceScore.final should be weighted sum."""
    s = ConfidenceScore(
        familiarity=1.0, clarity=1.0, risk=1.0, similarity=1.0, simplicity=1.0
    )
    assert abs(s.final - 1.0) < 0.01

    s = ConfidenceScore()
    assert abs(s.final - 0.0) < 0.01

    # Mixed: familiarity=0.5, others=0
    s = ConfidenceScore(familiarity=0.5)
    assert abs(s.final - 0.15) < 0.01  # 0.5 * 0.30


def test_task_creation():
    """Task should auto-generate IDs."""
    t = Task(user_id="u1", input_data={"input": "test"})
    assert t.id
    assert t.trace_id
    assert t.status == TaskStatus.PENDING
    uuid.UUID(t.id)  # Should be valid UUID
    uuid.UUID(t.trace_id)


def test_task_input_validation():
    """TaskInput should validate input length."""
    import pydantic

    # Empty input should fail
    try:
        TaskInput(input="", user_id="u1")
        assert False, "Should have raised"
    except pydantic.ValidationError:
        pass


def test_plan_structure():
    """Plan should have valid structure."""
    plan = Plan(
        steps=[
            PlanStep(step_id=1, action="test", tool="query_db"),
            PlanStep(step_id=2, action="format"),
        ]
    )
    assert len(plan.steps) == 2
    assert plan.steps[0].risk_level == RiskLevel.LOW


def test_a2a_message():
    """A2AMessage should be creatable."""
    msg = A2AMessage(
        trace_id="t1",
        from_agent=AgentRole.PLANNER,
        to_agent=AgentRole.EXECUTOR,
        type=MessageType.REQUEST,
        action="execute",
        task_id="task1",
        user_id="u1",
    )
    assert msg.from_agent == AgentRole.PLANNER
    assert msg.attempt == 1


def test_task_type_values():
    """All 7 task types should be defined."""
    types = [t.value for t in TaskType]
    expected = [
        "data_processing", "content_generation", "classification_routing",
        "monitoring_alerting", "research_summarization",
        "scheduling_coordination", "decision_support",
    ]
    assert sorted(types) == sorted(expected)
