"""Rule model for weather-based alerts."""

import uuid
from sqlalchemy import String, Float, ForeignKey, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDMixin


class Rule(Base, UUIDMixin, TimestampMixin):
    """Represents a weather condition rule for triggering alerts."""

    __tablename__ = "rules"

    location_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    metric: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    operator: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
    )
    threshold: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    __table_args__ = (
        Index("idx_rules_location_id", "location_id"),
        Index("idx_rules_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Rule(id={self.id}, metric={self.metric}, operator={self.operator}, threshold={self.threshold})>"
