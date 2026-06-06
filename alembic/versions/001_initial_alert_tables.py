"""Initial migration - create alerts table with full schema.

Revision ID: 001_initial_alerts
Revises: 000_base_tables
Create Date: 2026-06-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001_initial_alerts"
down_revision = "000_base_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create alerts table with production schema."""
    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rule_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("metric", sa.String(50), nullable=False),
        sa.Column("actual_value", sa.Float(), nullable=False),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column("operator", sa.String(2), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False, server_default="LOW"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("weather_snapshot", sa.String(2000), nullable=True),
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
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["rule_id"], ["rules.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    # Create indexes
    op.create_index("idx_alerts_location_id", "alerts", ["location_id"])
    op.create_index("idx_alerts_rule_id", "alerts", ["rule_id"])
    op.create_index("idx_alerts_user_id", "alerts", ["user_id"])
    op.create_index("idx_alerts_status", "alerts", ["status"])
    op.create_index("idx_alerts_severity", "alerts", ["severity"])
    op.create_index("idx_alerts_created_at", "alerts", ["created_at"])
    op.create_index("idx_alerts_location_created", "alerts", ["location_id", "created_at"])


def downgrade() -> None:
    """Drop alerts table and indexes."""
    op.drop_index("idx_alerts_location_created")
    op.drop_index("idx_alerts_created_at")
    op.drop_index("idx_alerts_severity")
    op.drop_index("idx_alerts_status")
    op.drop_index("idx_alerts_user_id")
    op.drop_index("idx_alerts_rule_id")
    op.drop_index("idx_alerts_location_id")
    op.drop_table("alerts")
