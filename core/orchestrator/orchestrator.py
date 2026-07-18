"""Orchestrator: state machine điều phối 5 agents.

Flow chính:
1. Nhận task từ API
2. Classifier phân loại
3. Planner lập kế hoạch
4. (optional) Supervisor duyệt plan
5. Executor thực thi từng step
6. Critic review
7. (optional) Memory Curator cập nhật long-term memory
8. Trả về user
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

from core.classifier import Classifier
from core.common.a2a_bus import get_bus
from core.common.config import get_settings
from core.common.errors import ApprovalRequiredError
from core.common.logging import get_logger
from core.common.types import (
    AgentRole,
    A2AMessage,
    ApprovalRequest,
    MessageType,
    Plan,
    RiskLevel,
    Task,
    TaskInput,
    TaskStatus,
    TaskType,
)
from core.confidence import ConfidenceEngine, risk_level_from_score
from core.memory import MemoryEngine

logger = get_logger(__name__)


class Orchestrator:
    """Main orchestrator coordinating 5 agents."""

    def __init__(
        self,
        classifier: Classifier | None = None,
        memory: MemoryEngine | None = None,
        confidence: ConfidenceEngine | None = None,
    ):
        self.settings = get_settings()
        self.classifier = classifier or Classifier()
        self.memory = memory or MemoryEngine()
        self.confidence = confidence or ConfidenceEngine(memory=self.memory)
        self.bus = get_bus()
        self._pending_approvals: dict[str, ApprovalRequest] = {}

    async def process_task(self, task_input: TaskInput) -> Task:
        """Process a task end-to-end.

        Returns: Task with status, result, and trace.
        """
        task = Task(
            id=str(uuid.uuid4()),
            trace_id=str(uuid.uuid4()),
            user_id=task_input.user_id,
            input_data={"input": task_input.input, **task_input.context},
            priority=task_input.priority,
        )

        logger.info(
            "orchestrator.task_started",
            task_id=task.id,
            trace_id=task.trace_id,
            user_id=task_input.user_id,
        )

        try:
            # 1. Initialize memory
            await self.memory.initialize()

            # 2. Classify
            task.status = TaskStatus.RUNNING
            classification = await self.classifier.classify(
                input_text=task_input.input,
                user_id=task_input.user_id,
                domain_hint=task_input.domain,
            )
            task.task_type = TaskType(classification["task_type"])
            task.domain = classification.get("domain") or task_input.domain

            await self.bus.send(A2AMessage(
                trace_id=task.trace_id,
                from_agent=AgentRole.CLASSIFIER,
                to_agent=AgentRole.PLANNER,
                type=MessageType.EVENT,
                action="classified",
                payload=classification,
                task_id=task.id,
                user_id=task_input.user_id,
            ))

            # 3. Plan (simplified for M1: skip LLM plan, use rule-based)
            plan = self._simple_plan(task, classification)
            task.plan = plan

            # 4. Confidence scoring
            confidence_score = await self.confidence.calculate(
                task_type=task.task_type,
                domain=task.domain or "unknown",
                user_id=task_input.user_id,
                plan=plan,
                input_data=task.input_data,
            )
            task.confidence = confidence_score

            # 5. Risk + decision
            max_risk = risk_level_from_score(1.0 - self.confidence._risk(plan)) if plan else RiskLevel.LOW

            action = self.confidence.decide_action(confidence_score.final, max_risk)

            logger.info(
                "orchestrator.decision",
                task_id=task.id,
                confidence=confidence_score.final,
                risk_level=max_risk.value,
                action=action,
            )

            # 6. Execute based on action
            if action == "clarify_or_reject":
                task.status = TaskStatus.FAILED
                task.error_message = "Confidence too low. Please provide more details."
                return task

            if action == "request_approval":
                approval = ApprovalRequest(
                    task_id=task.id,
                    proposal={"plan": plan.model_dump(), "input": task_input.input},
                    risk_level=max_risk,
                    reason=f"Confidence {confidence_score.final:.2f} below auto-execute threshold",
                )
                self._pending_approvals[approval.id] = approval
                task.status = TaskStatus.WAITING_APPROVAL
                # In real impl: emit event to UI
                logger.info(
                    "orchestrator.approval_required",
                    task_id=task.id,
                    approval_id=approval.id,
                )
                # For M1 demo: auto-approve if confidence above half threshold
                if confidence_score.final > (self.settings.confidence_auto_execute + self.settings.confidence_approval_required) / 2:
                    approval.decision = "approved"
                    task.status = TaskStatus.RUNNING
                else:
                    raise ApprovalRequiredError(approval.id, "Manual approval required")

            # 7. Execute plan (simplified for M1)
            result = await self._execute_plan(task, plan)
            task.result = result

            # 8. Store in episodic memory
            try:
                await self.memory.store_episode(
                    task_id=task.id,
                    user_id=task_input.user_id,
                    task_type=task.task_type.value,
                    domain=task.domain or "unknown",
                    input_text=task_input.input,
                    result_text=json.dumps(result) if result else "",
                    success=True,
                    confidence=confidence_score.final,
                    tools_used=[s.tool for s in plan.steps if s.tool],
                )
            except Exception as e:
                logger.warning("orchestrator.memory_store_failed", error=str(e))

            # 9. Mark complete
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            logger.info(
                "orchestrator.task_completed",
                task_id=task.id,
                confidence=confidence_score.final,
            )
            return task

        except ApprovalRequiredError as e:
            # Already handled, return waiting task
            logger.info("orchestrator.task_waiting_approval", task_id=task.id, approval_id=e.approval_id)
            return task

        except Exception as e:
            logger.exception("orchestrator.task_failed", task_id=task.id)
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.utcnow()
            return task

    def _simple_plan(
        self,
        task: Task,
        classification: dict[str, Any],
    ) -> Plan:
        """Generate a simple plan from classification. M1: rule-based."""
        task_type = task.task_type
        steps = []

        if task_type == TaskType.DATA_PROCESSING:
            steps.append(PlanStep(
                step_id=1,
                action="query_database",
                tool="query_db",
                args={"sql": "SELECT 1"},  # placeholder
                expected_result="Records matching query",
            ))
        elif task_type == TaskType.CONTENT_GENERATION:
            steps.append(PlanStep(
                step_id=1,
                action="generate_content",
                tool="llm_generate",
                args={"prompt": task.input_data.get("input", "")},
                expected_result="Generated text",
            ))
        elif task_type == TaskType.RESEARCH_SUMMARIZATION:
            steps.append(PlanStep(
                step_id=1,
                action="search_web",
                tool="web_search",
                args={"query": task.input_data.get("input", "")},
                expected_result="Search results",
            ))
            steps.append(PlanStep(
                step_id=2,
                action="summarize",
                tool="llm_summarize",
                args={"text": "<from step 1>"},
                expected_result="Summary",
            ))
        else:
            # Default: 1 step
            steps.append(PlanStep(
                step_id=1,
                action="process",
                tool=None,
                args={"input": task.input_data.get("input", "")},
                expected_result="Result",
            ))

        return Plan(steps=steps, reasoning=f"Auto plan for {task_type.value}")

    async def _execute_plan(self, task: Task, plan: Plan) -> dict[str, Any]:
        """Execute a plan. M1: stub, returns mock results."""
        results = []
        for step in plan.steps:
            # TODO M2: gọi MCP tool
            result = {
                "step_id": step.step_id,
                "action": step.action,
                "tool": step.tool,
                "status": "completed",
                "output": f"[M1 stub] Executed {step.action} with args {step.args}",
            }
            results.append(result)
            await self.bus.send(A2AMessage(
                trace_id=task.trace_id,
                from_agent=AgentRole.EXECUTOR,
                to_agent=AgentRole.PLANNER,
                type=MessageType.EVENT,
                action="step_completed",
                payload=result,
                task_id=task.id,
                user_id=task.user_id,
            ))
        return {"steps": results, "summary": f"Task {task.id} completed in M1 stub mode"}

    async def submit_approval(
        self,
        approval_id: str,
        decision: str,
        modified_args: dict | None = None,
        feedback: str | None = None,
    ) -> Task | None:
        """Submit approval decision, resume task if approved."""
        approval = self._pending_approvals.get(approval_id)
        if approval is None:
            return None
        approval.decision = decision
        approval.modified_args = modified_args
        approval.feedback = feedback
        approval.decided_at = datetime.utcnow()

        # Store in approval history
        try:
            await self.memory.store_approval(
                approval_id=approval_id,
                task_id=approval.task_id,
                user_id="",  # TODO: get from task
                task_type="",
                domain="",
                tool_name="",
                risk_level=approval.risk_level.value,
                decision=decision,
                modified=bool(modified_args),
            )
        except Exception as e:
            logger.warning("orchestrator.approval_store_failed", error=str(e))

        # TODO M2: resume task execution
        return None
