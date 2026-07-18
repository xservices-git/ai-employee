"""A2A message bus for inter-agent communication."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any

from core.common.logging import get_logger
from core.common.types import A2AMessage, AgentRole, MessageType

logger = get_logger(__name__)


class A2ABus:
    """In-process message bus for agent communication.

    Default implementation uses asyncio.Queue per agent.
    Can be swapped to Redis Streams or NATS for production scale.
    """

    def __init__(self, max_history: int = 10000):
        self._subscribers: dict[AgentRole, asyncio.Queue[A2AMessage]] = defaultdict(
            asyncio.Queue
        )
        self._history: list[A2AMessage] = []
        self._max_history = max_history
        self._lock = asyncio.Lock()

    async def send(self, message: A2AMessage) -> None:
        """Send a message to target agent(s)."""
        async with self._lock:
            self._history.append(message)
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history :]

        logger.info(
            "a2a.send",
            message_id=message.message_id,
            trace_id=message.trace_id,
            from_agent=message.from_agent,
            to_agent=message.to_agent,
            type=message.type,
            action=message.action,
        )

        if message.to_agent == "broadcast":
            for queue in self._subscribers.values():
                await queue.put(message)
        else:
            target = AgentRole(message.to_agent)
            await self._subscribers[target].put(message)

    async def receive(
        self,
        agent: AgentRole,
        timeout: float = 5.0,
    ) -> A2AMessage:
        """Receive a message for an agent (blocking with timeout)."""
        return await asyncio.wait_for(
            self._subscribers[agent].get(),
            timeout=timeout,
        )

    def get_history(self, trace_id: str | None = None) -> list[A2AMessage]:
        """Get message history, optionally filtered by trace_id."""
        if trace_id is None:
            return list(self._history)
        return [m for m in self._history if m.trace_id == trace_id]

    def clear(self) -> None:
        """Clear all history (for testing)."""
        self._history.clear()
        for queue in self._subscribers.values():
            while not queue.empty():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    break


# Singleton instance (process-wide)
_bus: A2ABus | None = None


def get_bus() -> A2ABus:
    """Get the singleton A2A bus."""
    global _bus
    if _bus is None:
        _bus = A2ABus()
    return _bus


def reset_bus() -> None:
    """Reset the bus (for testing)."""
    global _bus
    if _bus is not None:
        _bus.clear()
    _bus = None
