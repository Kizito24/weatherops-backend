"""User notification preferences model."""

import uuid
from sqlalchemy import String, Boolean, ForeignKey, Index, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDMixin


class UserPreference(Base, UUIDMixin, TimestampMixin):
    """User notification preferences and settings."""

    __tablename__ = "user_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Email notifications
    email_alerts_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    email_digest_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    email_digest_frequency: Mapped[str] = mapped_column(
        String(20),
        default="daily",
        nullable=False,
    )  # daily, weekly, monthly

    # SMS notifications
    sms_alerts_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    sms_phone_number: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    # Webhook notifications
    webhook_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    webhook_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Alert severity filters
    alert_low_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    alert_medium_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    alert_high_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Quiet hours
    quiet_hours_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    quiet_hours_start: Mapped[str | None] = mapped_column(
        String(5),
        nullable=True,
    )  # HH:MM format
    quiet_hours_end: Mapped[str | None] = mapped_column(
        String(5),
        nullable=True,
    )  # HH:MM format

    # Custom severity thresholds (override defaults)
    temperature_high_threshold: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    temperature_medium_threshold: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    rainfall_high_threshold: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    rainfall_medium_threshold: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    wind_speed_high_threshold: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    wind_speed_medium_threshold: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    __table_args__ = (
        Index("idx_user_preferences_user_id", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<UserPreference(user_id={self.user_id}, email_enabled={self.email_alerts_enabled})>"
