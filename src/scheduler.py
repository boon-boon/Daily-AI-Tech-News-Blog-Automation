"""
Long-running scheduler.

Two ways to schedule:

  1. Use this module's `run_forever()` — uses the `schedule` library and
     converts the configured local time (e.g. Malaysia 08:00) into the
     correct UTC time for the host process.

  2. Use system cron (recommended on a Linux server) — a sample cron
     entry is included in the README. In that case set
     SCHEDULER_MODE=oneshot and call `python main.py --once`.
"""

from __future__ import annotations

import time
from datetime import datetime

import pytz
import schedule

from config import settings
from src.pipeline import DailyPipeline
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _local_to_utc_hhmm(local_hhmm: str, tz_name: str) -> str:
    """Convert HH:MM in a named timezone into HH:MM UTC for `schedule`."""
    tz = pytz.timezone(tz_name)
    today = datetime.now(tz).date()
    naive = datetime.strptime(local_hhmm, "%H:%M").replace(
        year=today.year, month=today.month, day=today.day
    )
    local_dt = tz.localize(naive)
    utc_dt = local_dt.astimezone(pytz.utc)
    return utc_dt.strftime("%H:%M")


def run_forever() -> None:
    """Block forever, running the pipeline once per day at the configured time."""
    pipeline = DailyPipeline()

    utc_time = _local_to_utc_hhmm(settings.run_time, settings.timezone)
    logger.info(
        f"Scheduler starting — will run daily at "
        f"{settings.run_time} {settings.timezone} ({utc_time} UTC)."
    )

    schedule.every().day.at(utc_time).do(pipeline.run)

    # Optional: also expose a way to run immediately on startup if requested
    while True:
        schedule.run_pending()
        time.sleep(30)
