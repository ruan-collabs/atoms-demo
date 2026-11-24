#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PG_BIN="${PG_BIN:-/opt/homebrew/opt/postgresql@16/bin}"
DATA="$ROOT/.runtime/postgres"
mkdir -p "$ROOT/.runtime"
if [ ! -f "$DATA/PG_VERSION" ]; then
  # Dedicated project cluster; never touches other local databases/services.
  "$PG_BIN/initdb" -D "$DATA" --auth-local=trust --auth-host=trust --username=atoms --encoding=UTF8 --no-locale
fi
if ! "$PG_BIN/pg_ctl" -D "$DATA" status >/dev/null 2>&1; then
  "$PG_BIN/pg_ctl" -D "$DATA" -l "$ROOT/.runtime/postgres.log" -o "-h 127.0.0.1 -p 55432" start
fi
"$ROOT/backend/.venv/bin/python" -c "import psycopg; c=psycopg.connect('postgresql://atoms@127.0.0.1:55432/postgres',autocommit=True); exists=c.execute(\"SELECT 1 FROM pg_database WHERE datname='atoms'\").fetchone(); c.execute('CREATE DATABASE atoms') if not exists else None; c.close()"
printf 'Project PostgreSQL ready on 127.0.0.1:55432\n'
