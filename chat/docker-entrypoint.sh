#!/bin/bash
set -e

# ──────────────────────────────────────────────────────────────────────────────
# Dev-mode page guard
# ──────────────────────────────────────────────────────────────────────────────
# When DEV_MODE is NOT "true", rename Developer_Tool.py → Developer_Tool.py.disabled
# so Streamlit does NOT register it as a page.
# When DEV_MODE IS "true", restore the file if it was previously disabled.
# ──────────────────────────────────────────────────────────────────────────────

if [ "${DEV_MODE}" != "true" ]; then
    # Disable dev-only pages
    if [ -f src/pages/Developer_Tool.py ]; then
        echo "[entrypoint] DEV_MODE is not set — disabling Developer_Tool page"
        mv src/pages/Developer_Tool.py src/pages/Developer_Tool.py.disabled
    fi
else
    # Re-enable if coming from a disabled state (e.g. volume reuse)
    if [ -f src/pages/Developer_Tool.py.disabled ]; then
        echo "[entrypoint] DEV_MODE is set — re-enabling Developer_Tool page"
        mv src/pages/Developer_Tool.py.disabled src/pages/Developer_Tool.py
    fi
fi

# ──────────────────────────────────────────────────────────────────────────────
# Launch Streamlit
# ──────────────────────────────────────────────────────────────────────────────
exec streamlit run src/ui.py --server.port "${PORT:-8501}" --server.address "0.0.0.0"
