"""Structured logging configuration using loguru.

Development: colorized human-readable format.
Production: JSON structured logs for log aggregation (ELK, Loki, etc.).
"""

import sys
from pathlib import Path

from loguru import logger

from app.config import settings


def _json_serializer(message) -> str:
    """Custom JSON log format for production log aggregation."""
    record = message.record
    log_entry = {
        "timestamp": record["time"].strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "level": record["level"].name,
        "logger": record["name"],
        "message": record["message"],
        "module": record["module"],
        "function": record["function"],
        "line": record["line"],
    }

    # Add exception info if present
    if record["exception"]:
        log_entry["exception"] = {
            "type": record["exception"].type.__name__ if record["exception"].type else None,
            "value": str(record["exception"].value) if record["exception"].value else None,
        }

    # Add extra fields (structured context)
    if record["extra"]:
        log_entry["extra"] = record["extra"]

    import json
    return json.dumps(log_entry, ensure_ascii=False) + "\n"


def setup_logging() -> None:
    """Configure loguru logger for the application."""
    # Remove default handler
    logger.remove()

    if settings.is_prod:
        # Production: JSON structured logs
        Path("logs").mkdir(exist_ok=True)

        # JSON to stdout (for container log drivers: Docker, K8s)
        logger.add(
            sys.stdout,
            format=_json_serializer,
            level="INFO",
            colorize=False,
            serialize=False,
        )

        # JSON to rotating file
        logger.add(
            "logs/app.log",
            format=_json_serializer,
            rotation="50 MB",
            retention="30 days",
            compression="gz",
            level="INFO",
            serialize=False,
        )

        # Separate error log for alerting
        logger.add(
            "logs/error.log",
            format=_json_serializer,
            rotation="20 MB",
            retention="30 days",
            compression="gz",
            level="ERROR",
            serialize=False,
        )

    else:
        # Development: colorized human-readable
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )

        logger.add(
            sys.stderr,
            format=log_format,
            level="DEBUG" if settings.debug else "INFO",
            colorize=True,
        )

    # Suppress noisy third-party loggers
    import logging
    for noisy in ("uvicorn.access", "sqlalchemy.engine", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
