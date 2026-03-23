#!/bin/bash
set -e

# Initialize database if it doesn't exist
if [ ! -f /data/kk_info.db ]; then
    echo "Database not found. Creating tables..."
    python -c "from app.database import create_tables; create_tables()"
    echo "Database initialized."
else
    echo "Database found at /data/kk_info.db"
fi

# Start the API
echo "Starting Krankenkassen Info API on port 9000..."
exec uvicorn app.main:app --host 0.0.0.0 --port 9000
