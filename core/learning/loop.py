"""Learning loop: process feedback, extract rules, promote skills.

Mục tiêu: self-improving - hệ thống học từ feedback của user và từ chính những sai lầm.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

from core.common.logging import get_logger
from core.memory import MemoryEngine

logger = get_logger(__name__)


class LearningEvent:
    """A learning event extracted from feedback."""
    def __init__(
        self,
        event_type: str,
        task_id: str,
        before_state: dict | None = None,
        after_state: dict | None = None,
        rule_extracted: str | None = None,
    ):
        self.id = str(uuid.uuid4())
        self.event_type = event_type
        self.task_id = task_id
        self.before_state = before_state or {}
        self.after_state = after_state or {}
        self.rule_extracted = rule_extracted
        self.applied = False
        self.created_at = datetime.utcnow()


class LearningLoop:
    """Process feedback → learning events → rules → memory update."""

    def __init__(self, memory: MemoryEngine | None = None):
        self.memory = memory or MemoryEngine()
        self._events: list[LearningEvent] = []

    async def process_feedback(
        self,
        task_id: str,
        score: int,
        notes: str = "",
        corrections: dict | None = None,
        task_result: dict | None = None,
    ) -> list[LearningEvent]:
        """Process user feedback, generate learning events.

        Returns list of new LearningEvent.
        """
        events: list[LearningEvent] = []

        if score <= 2:
            # Low score = mistake
            event = LearningEvent(
                event_type="mistake_correction",
                task_id=task_id,
                before_state={"result": task_result} if task_result else {},
                after_state={"corrections": corrections or {}},
                rule_extracted=self._extract_rule_from_corrections(corrections or {}, notes),
            )
            events.append(event)

        elif score >= 4:
            # High score = good pattern
            event = LearningEvent(
                event_type="approval_learned",
                task_id=task_id,
                before_state={},
                after_state={"successful_pattern": task_result} if task_result else {},
                rule_extracted=notes,
            )
            events.append(event)

        # Apply events
        await self._apply_events(events)
        self._events.extend(events)
        return events

    def _extract_rule_from_corrections(self, corrections: dict, notes: str) -> str:
        """Extract a rule string from user corrections."""
        rules = []
        if corrections:
            for key, val in corrections.items():
                if isinstance(val, str) and val.strip():
                    rules.append(f"{key}: {val}")
        if notes:
            rules.append(notes)
        return " | ".join(rules) if rules else ""

    async def _apply_events(self, events: list[LearningEvent]) -> None:
        """Apply events to memory (store rules in semantic memory)."""
        if self.memory is None:
            return
        try:
            for event in events:
                if event.rule_extracted:
                    topic = f"task_{event.task_id}"
                    await self.memory.store_rule(
                        topic=topic,
                        rule=event.rule_extracted,
                        confidence=0.6,
                    )
                    event.applied = True
        except Exception as e:
            logger.warning("learning.apply_failed", error=str(e))

    async def promote_skill(
        self,
        skill_id: str,
        success_rate: float,
        usage_count: int,
    ) -> bool:
        """Promote a skill if it meets criteria."""
        if success_rate >= 0.85 and usage_count >= 10:
            logger.info(
                "learning.skill_promoted",
                skill_id=skill_id,
                success_rate=success_rate,
                usage_count=usage_count,
            )
            return True
        return False

    async def demote_skill(
        self,
        skill_id: str,
        success_rate: float,
    ) -> bool:
        """Demote a skill if it underperforms."""
        if success_rate < 0.5:
            logger.warning(
                "learning.skill_demoted",
                skill_id=skill_id,
                success_rate=success_rate,
            )
            return True
        return False
