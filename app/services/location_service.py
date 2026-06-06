"""Location service business logic."""

import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.location import Location
from app.repositories.location_repository import LocationRepository
from app.schemas.location import LocationCreate, LocationUpdate

logger = logging.getLogger(__name__)


class LocationNotFoundError(Exception):
    """Raised when location is not found."""

    pass


class LocationAccessError(Exception):
    """Raised when user doesn't own the location."""

    pass


class LocationService:
    """Service for location operations."""

    def __init__(self, db: AsyncSession):
        """Initialize service."""
        self.db = db
        self.repo = LocationRepository(db)

    async def create_location(
        self,
        user_id: uuid.UUID,
        data: LocationCreate,
    ) -> Location:
        """
        Create a new location for a user.

        Args:
            user_id: User ID.
            data: Location data.

        Returns:
            Created location.
        """
        location = await self.repo.create(
            user_id=user_id,
            name=data.name,
            latitude=data.latitude,
            longitude=data.longitude,
        )
        logger.info(f"Location created by user {user_id}: {location.id}")
        return location

    async def get_location(
        self,
        user_id: uuid.UUID,
        location_id: uuid.UUID,
    ) -> Location:
        """
        Get a location with ownership validation.

        Args:
            user_id: User ID.
            location_id: Location ID.

        Returns:
            Location.

        Raises:
            LocationNotFoundError: If location not found.
            LocationAccessError: If user doesn't own location.
        """
        location = await self.repo.get_by_id(location_id)

        if not location:
            raise LocationNotFoundError(f"Location {location_id} not found")

        if location.user_id != user_id:
            logger.warning(f"Unauthorized access attempt to location {location_id} by user {user_id}")
            raise LocationAccessError("You don't have access to this location")

        return location

    async def get_user_locations(self, user_id: uuid.UUID) -> list[Location]:
        """
        Get all locations for a user.

        Args:
            user_id: User ID.

        Returns:
            List of locations.
        """
        locations = await self.repo.get_by_user(user_id)
        logger.debug(f"Retrieved {len(locations)} locations for user {user_id}")
        return locations

    async def update_location(
        self,
        user_id: uuid.UUID,
        location_id: uuid.UUID,
        data: LocationUpdate,
    ) -> Location:
        """
        Update a location with ownership validation.

        Args:
            user_id: User ID.
            location_id: Location ID.
            data: Update data.

        Returns:
            Updated location.

        Raises:
            LocationNotFoundError: If location not found.
            LocationAccessError: If user doesn't own location.
        """
        location = await self.get_location(user_id, location_id)

        updated = await self.repo.update(
            location_id=location_id,
            name=data.name,
            latitude=data.latitude,
            longitude=data.longitude,
        )

        logger.info(f"Location updated by user {user_id}: {location_id}")
        return updated

    async def delete_location(
        self,
        user_id: uuid.UUID,
        location_id: uuid.UUID,
    ) -> None:
        """
        Delete a location with ownership validation.

        Args:
            user_id: User ID.
            location_id: Location ID.

        Raises:
            LocationNotFoundError: If location not found.
            LocationAccessError: If user doesn't own location.
        """
        await self.get_location(user_id, location_id)

        deleted = await self.repo.delete(location_id)

        if not deleted:
            raise LocationNotFoundError(f"Failed to delete location {location_id}")

        logger.info(f"Location deleted by user {user_id}: {location_id}")
