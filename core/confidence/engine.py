"""Confidence scoring engine.

Tính 5 chỉ số có trọng số, quyết định auto-execute / approval / reject.
Xem specs/02-CONFIDENCE-SCORING.md.
"""

from __future__ import annotations

from core.common.config import get_settings
from core.common.logging import get_logger
from core.common.types import ConfidenceScore, Plan, RiskLevel, TaskType

logger = get_logger(__name__)


# Risk matrix (domain, action) -> risk_level (0.0=safe, 1.0=dangerous)
DEFAULT_RISK_MATRIX: dict[tuple[str, str], float] = {
    # data
    ("*", "query_db"): 0.05,
    ("*", "insert_record"): 0.30,
    ("*", "update_record"): 0.50,
    ("*", "delete_record"): 0.85,
    ("*", "bulk_import"): 0.45,
    ("*", "export_report"): 0.05,
    # communication
    ("*", "create_draft"): 0.20,
    ("*", "send_email"): 0.55,
    ("*", "send_sms"): 0.55,
    ("*", "send_teams"): 0.45,
    # files
    ("*", "read_file"): 0.02,
    ("*", "write_file"): 0.30,
    ("*", "delete_file"): 0.80,
    # scheduling
    ("*", "create_event"): 0.20,
    ("*", "cancel_event"): 0.50,
    # web
    ("*", "web_search"): 0.05,
    ("*", "fetch_url"): 0.10,
}


# Default weights
DEFAULT_WEIGHTS = {
    "familiarity": 0.30,
    "clarity": 0.20,
    "risk": 0.25,
    "similarity": 0.15,
    "simplicity": 0.10,
}


def risk_level_from_score(score: float) -> RiskLevel:
    """Map 0-1 risk to RiskLevel enum."""
    if score < 0.20:
        return RiskLevel.LOW
    if score < 0.50:
        return RiskLevel.MEDIUM
    if score < 0.80:
        return RiskLevel.HIGH
    return RiskLevel.CRITICAL


class ConfidenceEngine:
    """Compute confidence score from 5 dimensions."""

    def __init__(
        self,
        memory: object | None = None,  # MemoryEngine, avoid circular import
        risk_matrix: dict[tuple[str, str], float] | None = None,
        weights: dict[str, float] | None = None,
    ):
        self.settings = get_settings()
        self.memory = memory
        self.risk_matrix = risk_matrix or DEFAULT_RISK_MATRIX
        self.weights = weights or DEFAULT_WEIGHTS

    async def calculate(
        self,
        task_type: TaskType | str,
        domain: str,
        user_id: str,
        plan: Plan | None = None,
        input_data: dict | None = None,
        required_fields: list[str] | None = None,
    ) -> ConfidenceScore:
        """Calculate confidence breakdown.

        Returns ConfidenceScore with all 5 dimensions + final.
        """
        task_type_str = task_type.value if isinstance(task_type, TaskType) else task_type

        familiarity = await self._familiarity(task_type_str, domain, user_id)
        clarity = self._clarity(input_data or {}, required_fields or [])
        risk = self._risk(plan)
        similarity = await self._similarity(input_data or {}, task_type_str, user_id)
        simplicity = self._simplicity(plan)

        score = ConfidenceScore(
            familiarity=familiarity,
            clarity=clarity,
            risk=risk,
            similarity=similarity,
            simplicity=simplicity,
        )

        logger.info(
            "confidence.calculated",
            task_type=task_type_str,
            domain=domain,
            final=score.final,
            familiarity=familiarity,
            clarity=clarity,
            risk=risk,
            similarity=similarity,
            simplicity=simplicity,
        )
        return score

    def decide_action(
        self,
        confidence: float,
        risk_level: RiskLevel,
    ) -> str:
        """Decide action based on confidence + risk level.

        Returns: 'auto_execute' | 'request_approval' | 'clarify_or_reject'
        """
        threshold_low = self.settings.confidence_approval_required
        threshold_high = self.settings.confidence_auto_execute

        if confidence < threshold_low:
            return "clarify_or_reject"
        if confidence >= 0.85 and risk_level == RiskLevel.LOW:
            return "auto_execute"
        if confidence >= threshold_high and risk_level <= RiskLevel.MEDIUM:
            return "auto_execute"
        return "request_approval"

    # === 5 scoring methods ===

    async def _familiarity(self, task_type: str, domain: str, user_id: str) -> float:
        """Score based on history of similar tasks."""
        if self.memory is None:
            return 0.5
        try:
            history = await self.memory.get_task_history(
                task_type=task_type,
                domain=domain,
                user_id=user_id,
                limit=20,
            )
            if not history:
                return 0.3
            success_count = sum(1 for h in history if h.get("success"))
            total = len(history)
            success_rate = success_count / total
            experience_factor = min(1.0, total / 10)
            return min(1.0, success_rate * experience_factor + 0.1)
        except Exception as e:
            logger.warning("confidence.familiarity_error", error=str(e))
            return 0.5

    def _clarity(self, input_data: dict, required_fields: list[str]) -> float:
        """Score based on input completeness and consistency."""
        if not required_fields:
            return 0.85  # No required fields = assume clear
        missing = sum(
            1 for f in required_fields
            if not input_data.get(f) or str(input_data.get(f, "")).strip() == ""
        )
        if missing == 0:
            return 1.0
        return max(0.0, 1.0 - missing * 0.15)

    def _risk(self, plan: Plan | None) -> float:
        """Score inversely proportional to risk. High = safe."""
        if plan is None or not plan.steps:
            return 0.5  # No plan = unknown risk
        max_risk = 0.0
        for step in plan.steps:
            action = step.action
            if step.tool:
                action = step.tool
            risk = self.risk_matrix.get(("*", action), 0.5)
            max_risk = max(max_risk, risk)
        return max(0.0, 1.0 - max_risk)

    async def _similarity(
        self,
        input_data: dict,
        task_type: str,
        user_id: str,
    ) -> float:
        """Score based on semantic similarity to past tasks."""
        if self.memory is None:
            return 0.5
        input_text = str(input_data.get("input", ""))
        if not input_text:
            return 0.5
        try:
            results = await self.memory.search_episodic(
                query=input_text,
                task_type=task_type,
                user_id=user_id,
                top_k=5,
            )
            if not results:
                return 0.5
            return sum(r.get("score", 0.0) for r in results) / len(results)
        except Exception as e:
            logger.warning("confidence.similarity_error", error=str(e))
            return 0.5

    def _simplicity(self, plan: Plan | None) -> float:
        """Score inversely proportional to plan complexity."""
        if plan is None or not plan.steps:
            return 0.5
        step_count = len(plan.steps)
        tool_count = sum(1 for s in plan.steps if s.tool)
        step_penalty = min(0.5, step_count * 0.05)
        tool_penalty = min(0.3, tool_count * 0.05)
        return max(0.0, 1.0 - step_penalty - tool_penalty)
