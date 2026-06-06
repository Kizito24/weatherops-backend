"""Location model for weather monitoring."""

import uuid
from sqlalchemy import String, Float, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDMixin


class Location(Base, UUIDMixin, TimestampMixin):
    """Represents a geographic location for weather monitoring."""

    __tablename__ = "locations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    __table_args__ = (
        Index("idx_locations_user_id", "user_id"),
        Index("idx_locations_coordinates", "latitude", "longitude"),
    )

    def __repr__(self) -> str:
        return f"<Location(id={self.id}, name={self.name}, lat={self.latitude}, lon={self.longitude})>"
