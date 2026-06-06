"""Alert data access repository - Production-grade alert persistence."""

import uuid
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.models.alert import Alert

logger = logging.getLogger(__name__)


class AlertRepository:
    """
    Repository for alert data access and persistence.

    Handles all database operations for alerts including creation, retrieval,
    status updates, and deduplication queries.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize alert repository.

        Args:
            db: AsyncSession for database operations
        """
        self.db = db

    async def create(
        self,
        location_id: uuid.UUID,
        rule_id: uuid.UUID,
        user_id: uuid.UUID,
        metric: str,
        actual_value: float,
        threshold: float,
        operator: str,
        severity: str = "LOW",
        weather_snapshot: str | None = None,
    ) -> Alert:
        """
        Create a new alert in the database.

        Args:
            location_id: UUID of location where condition triggered
            rule_id: UUID of rule that triggered
            user_id: UUID of user who owns the rule
            metric: Weather metric name (e.g., temperature, rainfall)
            actual_value: Actual measured value
            threshold: Rule threshold value
            operator: Comparison operator (>, <, >=, <=, ==)
            severity: Alert severity (LOW, MEDIUM, HIGH)
            weather_snapshot: JSON string of full weather context

        Returns:
            Created Alert object with database-assigned ID and timestamps

        Raises:
            SQLAlchemyError: On database constraint violation
        """
        alert = Alert(
            location_id=location_id,
            rule_id=rule_id,
            user_id=user_id,
            metric=metric,
            actual_value=actual_value,
            threshold=threshold,
            operator=operator,
            severity=severity,
            weather_snapshot=weather_snapshot,
            status="active",
        )

        self.db.add(alert)
        await self.db.commit()
        await self.db.refresh(alert)

        logger.info(
            "alert_created",
            extra={
                "alert_id": str(alert.id),
                "location_id": str(location_id),
                "rule_id": str(rule_id),
                "metric": metric,
                "actual_value": actual_value,
                "severity": severity,
            },
        )

        return alert

    async def get_by_id(self, alert_id: uuid.UUID) -> Alert | None:
        """
        Retrieve alert by UUID.

        Args:
            alert_id: Alert UUID

        Returns:
            Alert if found, None otherwise
        """
        query = select(Alert).where(Alert.id == alert_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_active_by_location(
        self,
        location_id: uuid.UUID,
    ) -> list[Alert]:
        """
        Get all active alerts for a location, ordered by recency.

        Args:
            location_id: Location UUID

        Returns:
            List of active Alert objects (newest first)
        """
        query = (
            select(Alert)
            .where(
                and_(
                    Alert.location_id == location_id,
                    Alert.status == "active",
                )
            )
            .order_by(Alert.created_at.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_recent_alert(
        self,
        location_id: uuid.UUID,
        rule_id: uuid.UUID,
        metric: str,
        actual_value: float,
        minutes: int = 5,
    ) -> Alert | None:
        """
        Get recent alert for same condition to enforce deduplication.

        Used to prevent duplicate alerts within a time window, implementing
        idempotency for the same rule + location + metric combination.

        Args:
            location_id: Location UUID
            rule_id: Rule UUID
            metric: Metric name
            actual_value: Current value (for duplicate detection)
            minutes: Time window to check (default 5 minutes)

        Returns:
            Recent alert if found within window, None otherwise
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)

        query = (
            select(Alert)
            .where(
                and_(
                    Alert.location_id == location_id,
                    Alert.rule_id == rule_id,
                    Alert.metric == metric,
                    Alert.status == "active",
                    Alert.created_at >= cutoff_time,
                )
            )
            .order_by(Alert.created_at.desc())
            .limit(1)
        )

        result = await self.db.execute(query)
        return result.scalars().first()

    async def resolve_alert(
        self,
        alert_id: uuid.UUID,
    ) -> Alert | None:
        """
        Mark an alert as resolved.

        Args:
            alert_id: Alert UUID to resolve

        Returns:
            Resolved Alert object, or None if not found
        """
        alert = await self.get_by_id(alert_id)
        if not alert:
            logger.warning(f"alert_not_found: {alert_id}")
            return None

        alert.status = "resolved"
        alert.resolved_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(alert)

        logger.info(
            "alert_resolved",
            extra={
                "alert_id": str(alert.id),
                "location_id": str(alert.location_id),
                "resolved_at": alert.resolved_at.isoformat(),
            },
        )

        return alert

    async def get_active_alerts(self) -> list[Alert]:
        """
        Get all active alerts system-wide, ordered by recency.

        Returns:
            List of all active Alert objects (newest first)
        """
        query = (
            select(Alert)
            .where(Alert.status == "active")
            .order_by(Alert.created_at.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_active_alerts_by_severity(
        self,
        severity: str,
    ) -> list[Alert]:
        """
        Get all active alerts of a specific severity level.

        Args:
            severity: Severity level (LOW, MEDIUM, HIGH)

        Returns:
            List of Alert objects with matching severity (newest first)
        """
        query = (
            select(Alert)
            .where(
                and_(
                    Alert.status == "active",
                    Alert.severity == severity,
                )
            )
            .order_by(Alert.created_at.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def count_active_for_location(
        self,
        location_id: uuid.UUID,
    ) -> int:
        """
        Count active alerts for a location.

        Args:
            location_id: Location UUID

        Returns:
            Number of active alerts
        """
        query = select(func.count(Alert.id)).where(
            and_(
                Alert.location_id == location_id,
                Alert.status == "active",
            )
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def count_active_by_severity(self, severity: str) -> int:
        """
        Count active alerts by severity level.

        Args:
            severity: Severity level

        Returns:
            Count of active alerts with matching severity
        """
        query = select(func.count(Alert.id)).where(
            and_(
                Alert.status == "active",
                Alert.severity == severity,
            )
        )
        result = await self.db.execute(query)
        return result.scalar() or 0
