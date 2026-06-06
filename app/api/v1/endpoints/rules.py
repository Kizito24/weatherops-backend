"""Rule API endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.dependencies.auth import CurrentUser
from app.schemas.rule import RuleCreate, RuleUpdate, RuleResponse
from app.services.rule_service import (
    RuleService,
    RuleNotFoundError,
    RuleAccessError,
    RuleValidationError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rules", tags=["rules"])


@router.post("", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    request: RuleCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_session),
) -> RuleResponse:
    """
    Create a new weather alert rule.

    Args:
        request: Rule creation data.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        Created rule.
    """
    service = RuleService(db)

    try:
        rule = await service.create_rule(current_user.id, request)
        return RuleResponse.model_validate(rule)
    except RuleValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except RuleAccessError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Error creating rule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create rule",
        ) from e


@router.get("/location/{location_id}", response_model=list[RuleResponse])
async def get_location_rules(
    location_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_session),
) -> list[RuleResponse]:
    """
    Get all rules for a location.

    Args:
        location_id: Location ID.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        List of rules for the location.
    """
    service = RuleService(db)

    try:
        rules = await service.get_location_rules(current_user.id, location_id)
        return [RuleResponse.model_validate(rule) for rule in rules]
    except RuleAccessError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Error fetching rules: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch rules",
        ) from e


@router.get("/{rule_id}", response_model=RuleResponse)
async def get_rule(
    rule_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_session),
) -> RuleResponse:
    """
    Get a specific rule.

    Args:
        rule_id: Rule ID.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        Rule details.
    """
    service = RuleService(db)

    try:
        rule = await service.get_rule(current_user.id, rule_id)
        return RuleResponse.model_validate(rule)
    except RuleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except RuleAccessError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Error fetching rule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch rule",
        ) from e


@router.put("/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: UUID,
    request: RuleUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_session),
) -> RuleResponse:
    """
    Update a rule.

    Args:
        rule_id: Rule ID.
        request: Update data.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        Updated rule.
    """
    service = RuleService(db)

    try:
        rule = await service.update_rule(current_user.id, rule_id, request)
        return RuleResponse.model_validate(rule)
    except RuleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except RuleAccessError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e
    except RuleValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Error updating rule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update rule",
        ) from e


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """
    Delete a rule.

    Args:
        rule_id: Rule ID.
        current_user: Authenticated user.
        db: Database session.
    """
    service = RuleService(db)

    try:
        await service.delete_rule(current_user.id, rule_id)
    except RuleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except RuleAccessError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Error deleting rule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete rule",
        ) from e
