"""
app/core/logging.py
────────────────────
Structured logging configuration using structlog.

In development  → colourised, human-readable output (via Rich)
In production   → JSON lines so log aggregators (Datadog, Loki, etc.) can parse them
"""

import logging
import sys

import structlog
from structlog.types import EventDict, WrappedLogger

from app.core.config import get_settings


def _add_app_context(
    logger: WrappedLogger,  # noqa: ARG001
    method_name: str,  # noqa: ARG001
    event_dict: EventDict,
) -> EventDict:
    """Inject static app context into every log record."""
    settings = get_settings()
    event_dict["app"] = settings.app_name
    event_dict["version"] = settings.app_version
    event_dict["env"] = settings.app_env
    return event_dict


def configure_logging() -> None:
    """
    Call once at application startup (inside lifespan or main).
    Subsequent calls are idempotent because structlog caches the configuration.
    """
    settings = get_settings()
    log_level = settings.log_level.upper()

    # ── Shared processors ────────────────────────────────────────────────────
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,        # thread-safe context binding
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        _add_app_context,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.is_production:
        # JSON output for log aggregators
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        # Rich, colourised output for local development
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(log_level)

    # Silence noisy third-party loggers
    for noisy in ("httpx", "httpcore", "sentence_transformers", "torch"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Convenience wrapper — use this instead of logging.getLogger()."""
    return structlog.get_logger(name)
