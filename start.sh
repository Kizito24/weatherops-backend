#!/bin/bash
set -e

echo "Starting WeatherOps application..."

# Run migrations using Python script
python run_migrations.py || true

# Start the application
echo ""
echo "Starting Uvicorn server on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
