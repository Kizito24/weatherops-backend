"""Alert API endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.dependencies.auth import CurrentUser
from app.models.alert import Alert
from app.repositories.alert_repository import AlertRepository
from app.schemas.alert import AlertResponse
from app.services.alert_service import AlertService, AlertServiceError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertResponse])
async def get_alerts(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_session),
    location_id: UUID | None = Query(None, description="Filter by location"),
    severity: str | None = Query(None, description="Filter by severity (LOW/MEDIUM/HIGH)"),
    status: str | None = Query(None, description="Filter by status (active/resolved)"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> list[AlertResponse]:
    """
    Get alerts with optional filtering.

    Args:
        location_id: Filter by location UUID (optional)
        severity: Filter by severity level (optional)
        status: Filter by status (optional)
        limit: Maximum number of results (default 100, max 1000)
        offset: Number of results to skip
        current_user: Authenticated user
        db: Database session

    Returns:
        List of alerts matching filters
    """
    repo = AlertRepository(db)

    try:
        # Start with all active alerts for the user's locations
        query = select(Alert).where(Alert.user_id == current_user.id)

        # Apply filters
        if location_id:
            query = query.where(Alert.location_id == location_id)

        if severity and severity in ["LOW", "MEDIUM", "HIGH"]:
            query = query.where(Alert.severity == severity)

        if status and status in ["active", "resolved"]:
            query = query.where(Alert.status == status)

        # Order by recency and apply pagination
        query = query.order_by(Alert.created_at.desc()).limit(limit).offset(offset)

        result = await db.execute(query)
        alerts = result.scalars().all()

        return [AlertResponse.model_validate(alert) for alert in alerts]
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch alerts",
        ) from e


@router.get("/location/{location_id}", response_model=list[AlertResponse])
async def get_location_alerts(
    location_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_session),
    severity: str | None = Query(None, description="Filter by severity"),
    limit: int = Query(50, ge=1, le=1000),
) -> list[AlertResponse]:
    """
    Get active alerts for a specific location.

    Args:
        location_id: Location UUID
        severity: Filter by severity (optional)
        limit: Maximum number of results
        current_user: Authenticated user
        db: Database session

    Returns:
        List of location alerts
    """
    alert_service = AlertService(db)

    try:
        if severity and severity in ["LOW", "MEDIUM", "HIGH"]:
            alerts = await alert_service.get_location_alerts(location_id)
            # Filter by severity
            alerts = [a for a in alerts if a.severity == severity][:limit]
        else:
            alerts = await alert_service.get_location_alerts(location_id)
            alerts = alerts[:limit]

        return [AlertResponse.model_validate(alert) for alert in alerts]
    except AlertServiceError as e:
        logger.error(f"Error fetching location alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Error fetching location alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch location alerts",
        ) from e


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_session),
) -> AlertResponse:
    """
    Get a specific alert.

    Args:
        alert_id: Alert UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        Alert details
    """
    repo = AlertRepository(db)

    try:
        alert = await repo.get_by_id(alert_id)

        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found",
            )

        if alert.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        return AlertResponse.model_validate(alert)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch alert",
        ) from e


@router.post("/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    alert_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_session),
) -> AlertResponse:
    """
    Resolve an active alert.

    Args:
        alert_id: Alert UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        Resolved alert
    """
    alert_service = AlertService(db)

    try:
        # Verify alert exists and user has access
        repo = AlertRepository(db)
        alert = await repo.get_by_id(alert_id)

        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found",
            )

        if alert.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        # Resolve the alert
        resolved_alert = await alert_service.resolve_alert(alert_id)

        if not resolved_alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found",
            )

        return AlertResponse.model_validate(resolved_alert)
    except HTTPException:
        raise
    except AlertServiceError as e:
        logger.error(f"Error resolving alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resolve alert",
        ) from e


@router.get("/count/critical", response_model=dict)
async def get_critical_alert_count(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Get count of critical (HIGH severity) alerts for current user.

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
        Count of critical alerts
    """
    try:
        query = db.select(Alert).where(
            (Alert.user_id == current_user.id)
            & (Alert.severity == "HIGH")
            & (Alert.status == "active")
        )
        result = await db.execute(query)
        count = len(result.scalars().all())
        return {"critical_count": count}
    except Exception as e:
        logger.error(f"Error counting critical alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to count critical alerts",
        ) from e


@router.get("/count/by-severity", response_model=dict)
async def get_alert_counts_by_severity(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Get alert counts grouped by severity.

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
        Alert counts by severity
    """
    try:
        counts = {}
        for severity in ["LOW", "MEDIUM", "HIGH"]:
            query = db.select(Alert).where(
                (Alert.user_id == current_user.id)
                & (Alert.severity == severity)
                & (Alert.status == "active")
            )
            result = await db.execute(query)
            counts[severity.lower()] = len(result.scalars().all())

        return {"by_severity": counts}
    except Exception as e:
        logger.error(f"Error counting alerts by severity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to count alerts by severity",
        ) from e
