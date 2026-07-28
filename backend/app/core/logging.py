"""
Curato AI — Structured Logging

JSON-structured logging with structlog for observability.
Includes request correlation IDs and agent-scoped loggers.
"""

import logging
import sys

import structlog

from app.core.config import get_settings


def setup_logging() -> None:
    """Configure structured logging for the application."""
    settings = get_settings()

    # ── structlog processors ─────────────────────────────────────────────
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.app_env == "development":
        # Pretty console output in dev
        renderer: structlog.types.Processor = structlog.dev.ConsoleRenderer(
            colors=True
        )
    else:
        # JSON output in production
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # ── Standard library logging integration ─────────────────────────────
    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(settings.log_level.upper())

    # Silence noisy third-party loggers
    for noisy_logger in ["uvicorn.access", "sqlalchemy.engine", "celery"]:
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a named, bound logger instance."""
    return structlog.get_logger(name)
