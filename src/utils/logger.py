"""
Centralised logging setup using loguru.

A single rotating log file per day is created under config.settings.log_dir,
plus colourised stdout output suitable for cron/Docker.
"""

from __future__ import annotations

import sys
from functools import lru_cache

from loguru import logger

from config import settings


_LOG_FORMAT_FILE = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
    "{name}:{function}:{line} | {message}"
)
_LOG_FORMAT_STDOUT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)


@lru_cache(maxsize=1)
def _configure_logger() -> None:
    """Configure loguru sinks once per process."""
    logger.remove()
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format=_LOG_FORMAT_STDOUT,
        colorize=True,
        backtrace=True,
        diagnose=False,
    )
    log_path = settings.log_dir / "daily-tech-news_{time:YYYY-MM-DD}.log"
    logger.add(
        str(log_path),
        level=settings.log_level,
        format=_LOG_FORMAT_FILE,
        rotation="00:00",       # roll at midnight
        retention="30 days",
        encoding="utf-8",
        enqueue=True,           # safe across threads
        backtrace=True,
        diagnose=False,
    )


def get_logger(name: str | None = None):
    """Return a loguru logger bound with `name`."""
    _configure_logger()
    if name:
        return logger.bind(name=name)
    return logger
