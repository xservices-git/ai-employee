"""3-layer safety: input filter, plan validator, output filter."""

from __future__ import annotations

import re
from typing import Any

from core.common.errors import PIILeakError, PromptInjectionError, SafetyViolationError
from core.common.logging import get_logger

logger = get_logger(__name__)


# PII patterns
PII_PATTERNS = {
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    "phone_vn": re.compile(r"\b(0|\+84)[1-9][0-9]{8,9}\b"),
    "cmnd": re.compile(r"\b[0-9]{9,12}\b"),
    "credit_card": re.compile(r"\b[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{4}\b"),
}

# Prompt injection patterns
INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(previous|all|above)\s+(instructions?|prompts?)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+", re.IGNORECASE),
    re.compile(r"system\s*:\s*", re.IGNORECASE),
    re.compile(r"</?(system|user|assistant)>", re.IGNORECASE),
    re.compile(r"reveal\s+(your|the)\s+(prompt|instructions?)", re.IGNORECASE),
]


class InputFilter:
    """Layer 1: filter and validate user input."""

    def check(self, text: str) -> dict[str, Any]:
        """Check input for issues.

        Returns: {ok: bool, issues: list[str], masked: str}
        """
        issues = []

        # Check prompt injection
        for pattern in INJECTION_PATTERNS:
            if pattern.search(text):
                issues.append(f"possible_prompt_injection: {pattern.pattern}")
                raise PromptInjectionError("Prompt injection detected", {"pattern": pattern.pattern})

        # Mask PII (don't fail, just mask for logging)
        masked = self._mask_pii(text)

        if issues:
            logger.warning("safety.input_issues", issues=issues)

        return {
            "ok": len(issues) == 0,
            "issues": issues,
            "masked": masked,
        }

    def _mask_pii(self, text: str) -> str:
        """Mask PII for safe logging."""
        masked = text
        for pii_type, pattern in PII_PATTERNS.items():
            if pii_type == "email":
                masked = pattern.sub("[EMAIL]", masked)
            elif pii_type == "phone_vn":
                masked = pattern.sub("[PHONE]", masked)
            elif pii_type == "cmnd":
                masked = pattern.sub("[ID]", masked)
            elif pii_type == "credit_card":
                masked = pattern.sub("[CARD]", masked)
        return masked


class PlanValidator:
    """Layer 2: validate plan before execution."""

    def __init__(self, tool_registry=None):
        self.tool_registry = tool_registry

    def validate(self, plan: dict[str, Any]) -> dict[str, Any]:
        """Validate plan structure and actions.

        Returns: {ok: bool, issues: list[str]}
        """
        issues = []
        steps = plan.get("steps", [])

        if not steps:
            issues.append("plan_empty")

        # Check each step
        seen_actions = set()
        for i, step in enumerate(steps):
            action = step.get("action", "")
            tool = step.get("tool")

            if not action:
                issues.append(f"step_{i}_no_action")

            # Cycle detection (simple)
            if action in seen_actions:
                issues.append(f"duplicate_action: {action}")
            seen_actions.add(action)

            # Check tool exists
            if tool and self.tool_registry and not self.tool_registry.has(tool):
                issues.append(f"unknown_tool: {tool}")

            # Check args schema (simplified)
            if not isinstance(step.get("args", {}), dict):
                issues.append(f"step_{i}_args_not_dict")

        # Step count limit
        if len(steps) > 20:
            issues.append(f"too_many_steps: {len(steps)} > 20")

        if issues:
            logger.warning("safety.plan_issues", issues=issues)

        return {"ok": len(issues) == 0, "issues": issues}


class OutputFilter:
    """Layer 3: filter AI output before returning to user."""

    def check(self, text: str) -> dict[str, Any]:
        """Check output for PII leak and other issues.

        Returns: {ok: bool, issues: list[str], masked: str}
        """
        issues = []

        # Check PII leak
        pii_found = []
        for pii_type, pattern in PII_PATTERNS.items():
            if pattern.search(text):
                pii_found.append(pii_type)
                if pii_type in ("cmnd", "credit_card"):
                    issues.append(f"pii_leak: {pii_type}")
                    raise PIILeakError(f"PII detected in output: {pii_type}")

        if pii_found:
            logger.warning("safety.output_pii_detected", types=pii_found)
            issues.append(f"pii_present: {pii_found}")

        # Mask for safe logging
        masked = self._mask_pii(text)

        return {
            "ok": len(issues) == 0,
            "issues": issues,
            "masked": masked,
        }

    def _mask_pii(self, text: str) -> str:
        masked = text
        for pii_type, pattern in PII_PATTERNS.items():
            if pii_type == "email":
                masked = pattern.sub("[EMAIL]", masked)
            elif pii_type == "phone_vn":
                masked = pattern.sub("[PHONE]", masked)
            elif pii_type == "cmnd":
                masked = pattern.sub("[ID]", masked)
            elif pii_type == "credit_card":
                masked = pattern.sub("[CARD]", masked)
        return masked


class SafetyGuard:
    """3-layer safety orchestrator."""

    def __init__(self):
        self.input = InputFilter()
        self.plan = PlanValidator()
        self.output = OutputFilter()

    def check_input(self, text: str) -> dict:
        return self.input.check(text)

    def validate_plan(self, plan: dict) -> dict:
        return self.plan.validate(plan)

    def check_output(self, text: str) -> dict:
        return self.output.check(text)


_safety: SafetyGuard | None = None


def get_safety_guard() -> SafetyGuard:
    global _safety
    if _safety is None:
        _safety = SafetyGuard()
    return _safety
