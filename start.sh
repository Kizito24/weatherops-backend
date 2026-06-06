#!/bin/bash

# Run database migrations with detailed logging
echo "================================================"
echo "Running database migrations..."
echo "================================================"
if alembic upgrade head 2>&1; then
    echo "================================================"
    echo "✓ Migrations completed successfully"
    echo "================================================"
else
    MIGRATION_EXIT=$?
    echo "================================================"
    echo "⚠ Migration exited with code: $MIGRATION_EXIT"
    echo "⚠ Continuing startup (tables may not exist)..."
    echo "================================================"
fi

# Start the application
echo ""
echo "Starting application on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
