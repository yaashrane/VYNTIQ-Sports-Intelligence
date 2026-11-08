"""Centralized logging configuration for VYNTIQ.

Ensures consistent format, contextual diagnostic records, and safe output without secrets.
"""

import logging
import sys


def setup_logging(log_level: str = "INFO") -> None:
    """Configure root and application loggers with unified formatting."""
    resolved_level = getattr(logging, log_level.upper(), logging.INFO)

    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
    )
    date_format = "%Y-%m-%d %H:%M:%S"

    # Configure root logger
    logging.basicConfig(
        level=resolved_level,
        format=log_format,
        datefmt=date_format,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    # Suppress verbose noise from third-party transport libraries
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a scoped logger instance."""
    return logging.getLogger(name)

