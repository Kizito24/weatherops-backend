#!/bin/bash

# Run database migrations with error handling
echo "Running database migrations..."
if alembic upgrade head; then
    echo "✓ Migrations completed successfully"
else
    echo "⚠ Migration failed or database not ready, continuing startup..."
fi

# Start the application
echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
