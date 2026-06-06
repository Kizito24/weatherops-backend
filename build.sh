#!/bin/bash
set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Script directory: $SCRIPT_DIR"
echo "Project root: $PROJECT_ROOT"
echo "Current directory: $(pwd)"

echo "Installing Python dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r "$SCRIPT_DIR/requirements/base.txt"

echo "Running database migrations..."
cd "$SCRIPT_DIR"
alembic upgrade head

echo "Build completed successfully!"
