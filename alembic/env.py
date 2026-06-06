"""Alembic environment configuration."""

import sys
from pathlib import Path
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

sys.path.insert(0, str(Path(__file__).parent.parent))

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add app models metadata
from app.core.config import get_settings
from app.database.base import Base

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    from sqlalchemy import create_engine

    # Convert async URLs to sync for migrations
    sync_url = settings.DATABASE_URL
    if 'sqlite+aiosqlite' in sync_url:
        sync_url = sync_url.replace('sqlite+aiosqlite', 'sqlite')
    elif 'postgresql+asyncpg' in sync_url:
        # Use psycopg:// (v3) driver for sync connections
        sync_url = sync_url.replace('postgresql+asyncpg://', 'psycopg://')

    print(f"[Alembic] Using database URL: {sync_url.split('@')[0]}@***")

    try:
        connectable = create_engine(sync_url, poolclass=pool.NullPool)
        with connectable.connect() as connection:
            context.configure(connection=connection, target_metadata=target_metadata)
            with context.begin_transaction():
                context.run_migrations()
        print("[Alembic] ✓ Migrations completed successfully")
    except Exception as e:
        print(f"[Alembic] ✗ Migration error: {e}")
        raise


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
