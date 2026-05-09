#!/usr/bin/env bash
# Wrapper script for cron. Loads the project venv and .env, then runs once.

set -euo pipefail

PROJECT_DIR="/opt/daily-tech-news"
cd "$PROJECT_DIR"

# Load env file if present
if [[ -f "$PROJECT_DIR/.env" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$PROJECT_DIR/.env"
  set +a
fi

# Activate venv if you use one (recommended)
if [[ -f "$PROJECT_DIR/.venv/bin/activate" ]]; then
  # shellcheck disable=SC1090
  source "$PROJECT_DIR/.venv/bin/activate"
fi

exec python main.py --once
