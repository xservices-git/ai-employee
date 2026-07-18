"""Test A2A bus."""

from __future__ import annotations

import asyncio

import pytest

from core.common.a2a_bus import A2ABus, get_bus, reset_bus
from core.common.types import A2AMessage, AgentRole, MessageType


@pytest.fixture
def bus():
    reset_bus()
    b = A2ABus()
    yield b
    reset_bus()


@pytest.mark.asyncio
async def test_send_receive(bus):
    """Send and receive should work."""
    msg = A2AMessage(
        trace_id="t1",
        from_agent=AgentRole.PLANNER,
        to_agent=AgentRole.EXECUTOR,
        type=MessageType.REQUEST,
        action="execute",
        task_id="task1",
        user_id="u1",
    )
    await bus.send(msg)
    received = await asyncio.wait_for(bus.receive(AgentRole.EXECUTOR), timeout=1.0)
    assert received.message_id == msg.message_id


@pytest.mark.asyncio
async def test_broadcast(bus):
    """Broadcast should reach all agents."""
    msg = A2AMessage(
        trace_id="t1",
        from_agent=AgentRole.MEMORY_CURATOR,
        to_agent="broadcast",
        type=MessageType.EVENT,
        action="episode_stored",
        task_id="task1",
        user_id="u1",
    )
    await bus.send(msg)
    # All 6 agents should receive
    for role in AgentRole:
        if role == AgentRole.USER:
            continue
        received = await asyncio.wait_for(bus.receive(role), timeout=1.0)
        assert received.message_id == msg.message_id


def test_history(bus):
    """History should be tracked."""
    initial_count = len(bus.get_history())
    msg = A2AMessage(
        trace_id="t1",
        from_agent=AgentRole.PLANNER,
        to_agent=AgentRole.EXECUTOR,
        type=MessageType.EVENT,
        action="x",
        task_id="task1",
        user_id="u1",
    )
    asyncio.run(bus.send(msg))
    assert len(bus.get_history()) == initial_count + 1
    assert len(bus.get_history(trace_id="t1")) == 1


def test_singleton():
    """Bus should be singleton."""
    b1 = get_bus()
    b2 = get_bus()
    assert b1 is b2
