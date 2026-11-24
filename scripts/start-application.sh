#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"
exec .venv/bin/python -m uvicorn app.application_server:app --host 127.0.0.1 --port "${PORT:-8001}" --no-access-log
