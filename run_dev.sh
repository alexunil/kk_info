#!/bin/bash
# Development server startup script

echo "Starting Krankenkassen Info API..."
echo ""
echo "API Documentation: http://localhost:8000/docs"
echo "Health Check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
