"""Health + metrics."""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Response

from api.schemas import HealthResponse
from core import __version__

router = APIRouter(tags=["health"])

_startup_time = time.time()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Liveness check."""
    return HealthResponse(
        status="ok",
        version=__version__,
        uptime_sec=int(time.time() - _startup_time),
    )


@router.get("/metrics")
async def metrics() -> Response:
    """Prometheus metrics (M1: stub)."""
    body = """# HELP ai_employee_up Whether the service is up
# TYPE ai_employee_up gauge
ai_employee_up 1
"""
    return Response(content=body, media_type="text/plain; version=0.0.4")
