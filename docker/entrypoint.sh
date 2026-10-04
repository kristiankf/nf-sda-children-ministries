#!/bin/sh
set -eu

python <<'PY'
import os
import sys
import time

import psycopg

url = os.environ.get("DATABASE_URL", "")
if not url:
    sys.exit("DATABASE_URL is not set")

last_error = None
for _ in range(60):
    try:
        with psycopg.connect(url, connect_timeout=3) as connection:
            connection.execute("SELECT 1")
        break
    except Exception as exc:  # noqa: BLE001 - retry until Postgres accepts connections
        last_error = exc
        time.sleep(1)
else:
    sys.exit(f"Database is not ready: {last_error}")
PY

mkdir -p staticfiles media

python manage.py migrate --noinput

if [ "${COLLECT_STATIC:-0}" = "1" ]; then
    python manage.py collectstatic --noinput
fi

exec "$@"
