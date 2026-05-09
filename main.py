"""
Daily AI Tech News Blog – CLI entry point.

Usage:
    python main.py --once           # run the pipeline once and exit
    python main.py --schedule       # run forever, executing daily at RUN_TIME
    python main.py --fetch-only     # just fetch + print, skip LLM/publish
"""

from __future__ import annotations

import argparse
import json
import sys

from config import settings
from src.pipeline import DailyPipeline
from src.scheduler import run_forever
from src.utils.logger import get_logger

logger = get_logger("main")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="daily-tech-news",
        description="Automated daily AI / tech news blog generator.",
    )
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--once", action="store_true",
                      help="Run the full pipeline once and exit.")
    mode.add_argument("--schedule", action="store_true",
                      help="Run forever, triggering the pipeline daily at RUN_TIME.")
    mode.add_argument("--fetch-only", action="store_true",
                      help="Only run fetchers; print results as JSON, skip LLM/publish.")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    # Default behaviour driven by env when no flag passed
    if not (args.once or args.schedule or args.fetch_only):
        if settings.scheduler_mode == "cron":
            args.schedule = True
        else:
            args.once = True

    if args.fetch_only:
        pipeline = DailyPipeline()
        items = pipeline.fetch_all()
        print(json.dumps([i.to_dict() for i in items], indent=2, ensure_ascii=False))
        return 0

    if args.schedule:
        run_forever()
        return 0

    # --once
    pipeline = DailyPipeline()
    articles = pipeline.run()
    logger.info(f"Run complete — produced {len(articles)} article(s).")
    for a in articles:
        logger.info(f"  • {a.title}  ->  {a.permalink}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
