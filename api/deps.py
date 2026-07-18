"""Shared dependencies."""

from __future__ import annotations

from functools import lru_cache

from core.orchestrator import Orchestrator


@lru_cache
def get_orchestrator() -> Orchestrator:
    """Get singleton orchestrator."""
    return Orchestrator()
