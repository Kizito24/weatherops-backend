#!/usr/bin/env python
"""Database migration runner - called before starting the app."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def run_migrations():
    """Run Alembic migrations."""
    from alembic.config import Config
    from alembic.command import upgrade

    try:
        print("=" * 50)
        print("Running database migrations...")
        print("=" * 50)

        alembic_cfg = Config("alembic.ini")
        upgrade(alembic_cfg, "head")

        print("=" * 50)
        print("✓ Migrations completed successfully")
        print("=" * 50)
        return True

    except Exception as e:
        print("=" * 50)
        print(f"✗ Migration failed: {e}")
        print("=" * 50)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)
