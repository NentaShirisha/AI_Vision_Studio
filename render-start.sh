#!/usr/bin/env bash
set -e
# Render sets PORT; fallback for local runs
export PORT="${PORT:-10000}"
echo "Starting gunicorn on 0.0.0.0:$PORT"
exec gunicorn ai_vision_platform.wsgi:application \
  --bind "0.0.0.0:$PORT" \
  --workers 1 \
  --timeout 300 \
  --access-logfile - \
  --error-logfile -
