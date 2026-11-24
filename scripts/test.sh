#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
backend/.venv/bin/python -m pytest backend/tests -q --junitxml=docs/backend-test-results.xml
npm --prefix frontend run test -- --reporter=default --reporter=junit --outputFile=../docs/frontend-test-results.xml
npm --prefix frontend run build
backend/.venv/bin/alembic -c backend/alembic.ini check
python3 tools/project_guard.py check .
