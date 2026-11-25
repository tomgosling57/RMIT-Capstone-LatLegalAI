#!/bin/bash
set -e

# ──────────────────────────────────────────────────────────────────────────────
# Auto-migrate database schema before starting Chainlit
# ──────────────────────────────────────────────────────────────────────────────
echo "[entrypoint] Checking and migrating database schema..."
if python /app/src/scripts/verify_db_schema.py --migrate; then
    echo "[entrypoint] Database schema is up to date."
else
    echo "[entrypoint] FATAL: Schema migration failed. Check the error above."
    exit 1
fi

# ──────────────────────────────────────────────────────────────────────────────
# Launch Chainlit
# Use CHAINLIT_PORT to avoid conflict with the global PORT variable (8501)
# ──────────────────────────────────────────────────────────────────────────────
exec chainlit run app.py --port "${CHAINLIT_PORT:-8001}" --host "0.0.0.0" --headless --root-path /chat
