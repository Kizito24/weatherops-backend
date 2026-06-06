#!/usr/bin/env python
"""Database migration runner - called before starting the app."""

import subprocess
import sys

def run_migrations():
    """Run Alembic migrations using subprocess."""
    try:
        print("=" * 50)
        print("Running database migrations...")
        print("=" * 50)

        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=False,
            text=True
        )

        if result.returncode == 0:
            print("=" * 50)
            print("✓ Migrations completed successfully")
            print("=" * 50)
            return True
        else:
            print("=" * 50)
            print(f"✗ Migration failed with exit code: {result.returncode}")
            print("=" * 50)
            return False

    except Exception as e:
        print("=" * 50)
        print(f"✗ Migration error: {e}")
        print("=" * 50)
        return False


if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)
