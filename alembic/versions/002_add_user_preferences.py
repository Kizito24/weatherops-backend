"""Add user preferences table for notification settings.

Revision ID: 002_user_preferences
Revises: 001_initial_alerts
Create Date: 2026-06-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "002_user_preferences"
down_revision = "001_initial_alerts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create user_preferences table."""
    op.create_table(
        "user_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email_alerts_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("email_digest_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("email_digest_frequency", sa.String(20), nullable=False, server_default="daily"),
        sa.Column("sms_alerts_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sms_phone_number", sa.String(20), nullable=True),
        sa.Column("webhook_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("webhook_url", sa.String(500), nullable=True),
        sa.Column("alert_low_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("alert_medium_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("alert_high_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("quiet_hours_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("quiet_hours_start", sa.String(5), nullable=True),
        sa.Column("quiet_hours_end", sa.String(5), nullable=True),
        sa.Column("temperature_high_threshold", sa.Float(), nullable=True),
        sa.Column("temperature_medium_threshold", sa.Float(), nullable=True),
        sa.Column("rainfall_high_threshold", sa.Float(), nullable=True),
        sa.Column("rainfall_medium_threshold", sa.Float(), nullable=True),
        sa.Column("wind_speed_high_threshold", sa.Float(), nullable=True),
        sa.Column("wind_speed_medium_threshold", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_user_preferences_user_id"),
    )
    op.create_index("idx_user_preferences_user_id", "user_preferences", ["user_id"])


def downgrade() -> None:
    """Drop user_preferences table."""
    op.drop_index("idx_user_preferences_user_id")
    op.drop_table("user_preferences")
