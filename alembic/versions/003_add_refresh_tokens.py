"""Add refresh tokens table for token management.

Revision ID: 003_refresh_tokens
Revises: 002_user_preferences
Create Date: 2026-06-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "003_refresh_tokens"
down_revision = "002_user_preferences"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create refresh_tokens table."""
    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("idx_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("idx_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"])
    op.create_index("idx_refresh_tokens_revoked", "refresh_tokens", ["revoked"])
    op.create_index("idx_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"])


def downgrade() -> None:
    """Drop refresh_tokens table."""
    op.drop_index("idx_refresh_tokens_expires_at")
    op.drop_index("idx_refresh_tokens_revoked")
    op.drop_index("idx_refresh_tokens_token_hash")
    op.drop_index("idx_refresh_tokens_user_id")
    op.drop_table("refresh_tokens")
