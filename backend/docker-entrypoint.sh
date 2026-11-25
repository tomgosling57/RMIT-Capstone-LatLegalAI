#!/bin/bash
set -e

# Check if file logging is disabled
if [ "${ENABLE_FILE_LOGGING}" = "false" ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "⚠️  WARNING: FILE LOGGING IS DISABLED"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "The ENABLE_FILE_LOGGING environment variable is set to 'false'."
    echo "Application logs will NOT be written to files in /app/src/logs/."
    echo "Logs are only available via 'docker logs latmatrix-api'."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
fi

# Check if the log directory is writable (only if logging is enabled)
if [ "${ENABLE_FILE_LOGGING}" != "false" ]; then
    LOG_DIR_PATH="/app/src/logs"
    
    # Ensure the directory exists (it should, as it's a volume mount)
    mkdir -p "$LOG_DIR_PATH" 2>/dev/null || true
    
    # Check if the directory is writable
    if [ ! -w "$LOG_DIR_PATH" ]; then
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "⚠️  WARNING: PERMISSION DENIED FOR LOG DIRECTORY"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "The application cannot write to $LOG_DIR_PATH."
        echo "File logging will likely fail and fallback to console-only logging."
        echo "To fix: chmod 777 backend/src/logs or set ENABLE_FILE_LOGGING=false."
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
    fi
fi

# Run the command passed to the container
exec "$@"
