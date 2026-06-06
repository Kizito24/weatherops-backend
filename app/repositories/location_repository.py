"""Location data access repository."""

import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.location import Location

logger = logging.getLogger(__name__)


class LocationRepository:
    """Repository for location data access."""

    def __init__(self, db: AsyncSession):
        """Initialize repository."""
        self.db = db

    async def create(self, user_id: uuid.UUID, name: str, latitude: float, longitude: float) -> Location:
        """Create a new location."""
        location = Location(
            user_id=user_id,
            name=name,
            latitude=latitude,
            longitude=longitude,
        )
        self.db.add(location)
        await self.db.commit()
        await self.db.refresh(location)
        logger.info(f"Location created: {location.id}")
        return location

    async def get_by_id(self, location_id: uuid.UUID) -> Location | None:
        """Get location by ID."""
        query = select(Location).where(Location.id == location_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_user(self, user_id: uuid.UUID) -> list[Location]:
        """Get all locations for a user."""
        query = select(Location).where(Location.user_id == user_id).order_by(Location.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update(
        self,
        location_id: uuid.UUID,
        name: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> Location | None:
        """Update a location."""
        location = await self.get_by_id(location_id)
        if not location:
            return None

        if name is not None:
            location.name = name
        if latitude is not None:
            location.latitude = latitude
        if longitude is not None:
            location.longitude = longitude

        await self.db.commit()
        await self.db.refresh(location)
        logger.info(f"Location updated: {location_id}")
        return location

    async def delete(self, location_id: uuid.UUID) -> bool:
        """Delete a location."""
        location = await self.get_by_id(location_id)
        if not location:
            return False

        await self.db.delete(location)
        await self.db.commit()
        logger.info(f"Location deleted: {location_id}")
        return True

    async def get_all(self) -> list[Location]:
        """Get all locations."""
        query = select(Location).order_by(Location.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all()
