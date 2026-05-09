# syntax=docker/dockerfile:1.6
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Asia/Kuala_Lumpur

WORKDIR /app

# System deps for lxml and timezone data
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libxml2-dev libxslt1-dev tzdata curl \
 && rm -rf /var/lib/apt/lists/* \
 && ln -fs /usr/share/zoneinfo/$TZ /etc/localtime

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Default to scheduler mode; override via `docker run ... --once`
ENV SCHEDULER_MODE=cron
CMD ["python", "main.py", "--schedule"]
