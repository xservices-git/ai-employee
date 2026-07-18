"""Structured logging setup with structlog."""

from __future__ import annotations

import logging
import sys

import structlog
from structlog.types import EventDict, Processor

from core.common.config import get_settings


def add_app_context(_: object, __: str, event_dict: EventDict) -> EventDict:
    """Add app metadata to every log."""
    settings = get_settings()
    event_dict["app"] = "ai-employee"
    event_dict["env"] = settings.app_env
    return event_dict


def setup_logging() -> None:
    """Configure structured JSON logging for production, console for dev."""
    settings = get_settings()

    # Shared processors
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        add_app_context,
    ]

    if settings.is_dev:
        # Pretty console output for dev
        processors = [
            *shared_processors,
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    else:
        # JSON for prod (parseable by Loki/ELK)
        processors = [
            *shared_processors,
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    # Configure stdlib logging to also use structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a logger instance."""
    return structlog.get_logger(name)
