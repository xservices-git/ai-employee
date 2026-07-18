"""Tool registry: metadata cho mọi tool (risk, timeout, rate limit)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from core.common.config import get_settings
from core.common.errors import ToolNotFoundError
from core.common.logging import get_logger
from core.common.types import RiskLevel

logger = get_logger(__name__)


@dataclass
class ToolSpec:
    """Specification for a tool."""
    name: str
    server: str
    risk: RiskLevel
    timeout_sec: int = 30
    rate_limit_per_user_hour: int = 100
    rate_limit_per_tool_hour: int = 1000
    requires_approval: bool = False
    description: str = ""
    approval_reason: str = ""


class ToolRegistry:
    """Central registry of all available tools."""

    def __init__(self, config_path: str | Path | None = None):
        self.settings = get_settings()
        self._tools: dict[str, ToolSpec] = {}
        self._config_path = Path(config_path or "domain_configs/tools.yaml")

    def load(self) -> None:
        """Load tool specs from YAML config."""
        if not self._config_path.exists():
            logger.warning(
                "tool_registry.config_not_found",
                path=str(self._config_path),
            )
            return
        try:
            with open(self._config_path) as f:
                data = yaml.safe_load(f)
            for tool_data in data.get("tools", []):
                spec = ToolSpec(
                    name=tool_data["name"],
                    server=tool_data.get("server", ""),
                    risk=RiskLevel(tool_data.get("risk", "low")),
                    timeout_sec=tool_data.get("timeout_sec", 30),
                    rate_limit_per_user_hour=tool_data.get("rate_limit", {}).get("per_user", 100),
                    rate_limit_per_tool_hour=tool_data.get("rate_limit", {}).get("per_tool", 1000),
                    requires_approval=tool_data.get("requires_approval", False),
                    description=tool_data.get("description", ""),
                    approval_reason=tool_data.get("approval_reason", ""),
                )
                self._tools[spec.name] = spec
            logger.info("tool_registry.loaded", count=len(self._tools))
        except Exception as e:
            logger.error("tool_registry.load_failed", error=str(e))

    def get(self, name: str) -> ToolSpec:
        """Get tool spec by name."""
        if name not in self._tools:
            raise ToolNotFoundError(f"Tool not found: {name}")
        return self._tools[name]

    def has(self, name: str) -> bool:
        return name in self._tools

    def list(self) -> list[ToolSpec]:
        return list(self._tools.values())

    def list_by_server(self, server: str) -> list[ToolSpec]:
        return [t for t in self._tools.values() if t.server == server]

    def list_by_risk(self, risk: RiskLevel) -> list[ToolSpec]:
        return [t for t in self._tools.values() if t.risk == risk]

    def register(self, spec: ToolSpec) -> None:
        """Register a tool at runtime (for tests or dynamic tools)."""
        self._tools[spec.name] = spec
        logger.info("tool_registry.registered", name=spec.name)


# Singleton
_registry: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        _registry.load()
    return _registry
