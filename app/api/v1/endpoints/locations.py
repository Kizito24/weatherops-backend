"""Location API endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.dependencies.auth import CurrentUser
from app.schemas.location import LocationCreate, LocationUpdate, LocationResponse
from app.services.location_service import (
    LocationService,
    LocationNotFoundError,
    LocationAccessError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/locations", tags=["locations"])


@router.post("", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    request: LocationCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_session),
) -> LocationResponse:
    """
    Create a new weather monitoring location.

    Args:
        request: Location creation data.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        Created location.
    """
    service = LocationService(db)

    try:
        location = await service.create_location(current_user.id, request)
        return LocationResponse.model_validate(location)
    except Exception as e:
        logger.error(f"Error creating location: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create location",
        ) from e


@router.get("", response_model=list[LocationResponse])
async def list_locations(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_session),
) -> list[LocationResponse]:
    """
    Get all locations for the authenticated user.

    Args:
        current_user: Authenticated user.
        db: Database session.

    Returns:
        List of user's locations.
    """
    service = LocationService(db)

    try:
        locations = await service.get_user_locations(current_user.id)
        return [LocationResponse.model_validate(loc) for loc in locations]
    except Exception as e:
        logger.error(f"Error fetching locations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch locations",
        ) from e


@router.get("/{location_id}", response_model=LocationResponse)
async def get_location(
    location_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_session),
) -> LocationResponse:
    """
    Get a specific location.

    Args:
        location_id: Location ID.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        Location details.
    """
    service = LocationService(db)

    try:
        location = await service.get_location(current_user.id, location_id)
        return LocationResponse.model_validate(location)
    except LocationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except LocationAccessError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Error fetching location: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch location",
        ) from e


@router.put("/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: UUID,
    request: LocationUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_session),
) -> LocationResponse:
    """
    Update a location.

    Args:
        location_id: Location ID.
        request: Update data.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        Updated location.
    """
    service = LocationService(db)

    try:
        location = await service.update_location(current_user.id, location_id, request)
        return LocationResponse.model_validate(location)
    except LocationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except LocationAccessError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Error updating location: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update location",
        ) from e


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(
    location_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """
    Delete a location.

    Args:
        location_id: Location ID.
        current_user: Authenticated user.
        db: Database session.
    """
    service = LocationService(db)

    try:
        await service.delete_location(current_user.id, location_id)
    except LocationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except LocationAccessError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Error deleting location: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete location",
        ) from e
