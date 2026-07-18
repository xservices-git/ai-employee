"""Test confidence engine."""

from __future__ import annotations

import pytest

from core.common.types import Plan, PlanStep, RiskLevel
from core.confidence import ConfidenceEngine, risk_level_from_score


def test_risk_level_from_score():
    """Score to risk level mapping."""
    assert risk_level_from_score(0.0) == RiskLevel.CRITICAL
    assert risk_level_from_score(0.10) == RiskLevel.LOW
    assert risk_level_from_score(0.30) == RiskLevel.MEDIUM
    assert risk_level_from_score(0.60) == RiskLevel.HIGH
    assert risk_level_from_score(0.90) == RiskLevel.CRITICAL


@pytest.mark.asyncio
async def test_confidence_no_memory():
    """Without memory, should use defaults."""
    engine = ConfidenceEngine(memory=None)
    score = await engine.calculate(
        task_type="data_processing",
        domain="sales",
        user_id="u1",
        plan=Plan(steps=[PlanStep(step_id=1, action="test", tool="query_db")]),
    )
    assert 0.0 <= score.final <= 1.0
    assert score.simplicity > 0.0  # Simple plan


@pytest.mark.asyncio
async def test_confidence_with_plan():
    """Plan with delete should have low risk score."""
    engine = ConfidenceEngine(memory=None)
    plan = Plan(steps=[
        PlanStep(step_id=1, action="delete", tool="delete_record"),
    ])
    score = await engine.calculate(
        task_type="data_processing",
        domain="sales",
        user_id="u1",
        plan=plan,
    )
    # Risk score = 1.0 - 0.85 = 0.15 (high risk tool)
    assert score.risk < 0.30


def test_decide_action_low_confidence():
    """Low confidence should always clarify."""
    engine = ConfidenceEngine(memory=None)
    action = engine.decide_action(0.30, RiskLevel.LOW)
    assert action == "clarify_or_reject"


def test_decide_action_auto_low_risk():
    """High confidence + low risk = auto."""
    engine = ConfidenceEngine(memory=None)
    action = engine.decide_action(0.90, RiskLevel.LOW)
    assert action == "auto_execute"


def test_decide_action_approval_high_risk():
    """High risk needs approval even with high confidence."""
    engine = ConfidenceEngine(memory=None)
    action = engine.decide_action(0.80, RiskLevel.CRITICAL)
    assert action == "request_approval"


def test_clarity_perfect():
    """All required fields present = 1.0."""
    engine = ConfidenceEngine(memory=None)
    clarity = engine._clarity({"a": 1, "b": "x"}, ["a", "b"])
    assert clarity == 1.0


def test_clarity_missing():
    """Missing fields reduce clarity."""
    engine = ConfidenceEngine(memory=None)
    clarity = engine._clarity({"a": 1}, ["a", "b", "c"])
    # 2 missing: 1.0 - 2*0.15 = 0.7
    assert abs(clarity - 0.70) < 0.01


def test_simplicity_simple_plan():
    """1 step plan = high simplicity."""
    engine = ConfidenceEngine(memory=None)
    plan = Plan(steps=[PlanStep(step_id=1, action="x")])
    simplicity = engine._simplicity(plan)
    assert simplicity == 1.0
