"""Base tables - users, locations, and rules.

Revision ID: 000_base_tables
Revises:
Create Date: 2026-06-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "000_base_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create base tables."""
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("idx_users_email", "users", ["email"])
    op.create_index("idx_users_is_active", "users", ["is_active"])

    # Create locations table
    op.create_table(
        "locations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
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
    )
    op.create_index("idx_locations_user_id", "locations", ["user_id"])
    op.create_index("idx_locations_coordinates", "locations", ["latitude", "longitude"])

    # Create rules table
    op.create_table(
        "rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("metric", sa.String(50), nullable=False),
        sa.Column("operator", sa.String(2), nullable=False),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
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
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_rules_location_id", "rules", ["location_id"])
    op.create_index("idx_rules_active", "rules", ["is_active"])


def downgrade() -> None:
    """Drop base tables."""
    op.drop_index("idx_rules_active")
    op.drop_index("idx_rules_location_id")
    op.drop_table("rules")
    op.drop_index("idx_locations_coordinates")
    op.drop_index("idx_locations_user_id")
    op.drop_table("locations")
    op.drop_index("idx_users_is_active")
    op.drop_index("idx_users_email")
    op.drop_table("users")
