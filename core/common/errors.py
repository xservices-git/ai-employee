"""Custom exceptions."""

from __future__ import annotations


class AIEmployeeError(Exception):
    """Base exception for the system."""
    code: str = "internal_error"

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigError(AIEmployeeError):
    code = "config_error"


class LLMError(AIEmployeeError):
    code = "llm_error"


class ToolError(AIEmployeeError):
    code = "tool_error"


class ToolTimeoutError(ToolError):
    code = "tool_timeout"


class ToolNotFoundError(ToolError):
    code = "tool_not_found"


class ToolPermissionError(ToolError):
    code = "tool_permission_denied"


class MemoryError(AIEmployeeError):
    code = "memory_error"


class ConfidenceError(AIEmployeeError):
    code = "confidence_error"


class ApprovalRequiredError(AIEmployeeError):
    """Task needs human approval."""
    code = "approval_required"

    def __init__(self, approval_id: str, message: str = "Approval required"):
        super().__init__(message)
        self.approval_id = approval_id


class SafetyViolationError(AIEmployeeError):
    code = "safety_violation"


class PIILeakError(SafetyViolationError):
    code = "pii_leak"


class PromptInjectionError(SafetyViolationError):
    code = "prompt_injection"


class RateLimitError(AIEmployeeError):
    code = "rate_limited"
