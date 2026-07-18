"""MCP client for calling tool servers."""

from __future__ import annotations

import asyncio
import json
import subprocess
from typing import Any

from core.common.config import get_settings
from core.common.errors import ToolError, ToolTimeoutError
from core.common.logging import get_logger
from core.tools.registry import ToolSpec, get_tool_registry

logger = get_logger(__name__)


class MCPClient:
    """Client for calling MCP tool servers via JSON-RPC over stdio."""

    def __init__(self):
        self.settings = get_settings()
        self._processes: dict[str, subprocess.Popen] = {}

    async def call(
        self,
        tool_name: str,
        args: dict[str, Any],
        user_id: str = "system",
    ) -> dict[str, Any]:
        """Call a tool by name with args.

        Returns the tool's response as a dict.
        """
        registry = get_tool_registry()
        spec = registry.get(tool_name)

        logger.info(
            "mcp.call",
            tool=tool_name,
            server=spec.server,
            risk=spec.risk.value,
            user_id=user_id,
        )

        # TODO M2: implement real MCP stdio/HTTP transport
        # For M1: stub response
        try:
            return await asyncio.wait_for(
                self._call_stub(tool_name, args, spec),
                timeout=spec.timeout_sec,
            )
        except asyncio.TimeoutError as e:
            raise ToolTimeoutError(f"Tool {tool_name} timed out after {spec.timeout_sec}s") from e
        except Exception as e:
            raise ToolError(f"Tool {tool_name} failed: {e}") from e

    async def _call_stub(
        self,
        tool_name: str,
        args: dict[str, Any],
        spec: ToolSpec,
    ) -> dict[str, Any]:
        """M1 stub: returns mock response."""
        await asyncio.sleep(0.05)  # Simulate latency
        return {
            "success": True,
            "tool": tool_name,
            "args": args,
            "output": f"[M1 stub] {tool_name} executed with {len(args)} args",
            "metadata": {
                "server": spec.server,
                "risk": spec.risk.value,
            },
        }
