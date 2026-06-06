"""Alert creation and management service - Production-grade alerting engine."""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.models.alert import Alert
from app.repositories.alert_repository import AlertRepository
from app.services.rule_engine import RuleEvaluationResult

logger = logging.getLogger(__name__)


class AlertServiceError(Exception):
    """Base exception for alert service errors."""

    pass


class AlertService:
    """
    Production-grade alert creation and management service.

    Responsible for:
    - Creating alerts from triggered rules with deduplication
    - Managing alert lifecycle (create, resolve, retrieve)
    - Calculating alert severity based on deviation
    - Storing weather context snapshots
    - Enforcing idempotency to prevent alert storms

    All alert creation must go through this service to ensure consistency
    and deduplication logic is applied.
    """

    # Time window for deduplication (in minutes)
    DUPLICATE_WINDOW_MINUTES = 5

    # Severity thresholds for different metrics
    SEVERITY_THRESHOLDS = {
        "temperature": {
            "HIGH": 5.0,  # >5°C deviation = HIGH
            "MEDIUM": 2.0,  # >2°C deviation = MEDIUM
        },
        "rainfall": {
            "HIGH": 15.0,  # >15mm deviation = HIGH
            "MEDIUM": 5.0,  # >5mm deviation = MEDIUM
        },
        "wind_speed": {
            "HIGH": 12.0,  # >12 km/h deviation = HIGH
            "MEDIUM": 4.0,  # >4 km/h deviation = MEDIUM
        },
        "humidity": {
            "HIGH": 20.0,  # >20% deviation = HIGH
            "MEDIUM": 10.0,  # >10% deviation = MEDIUM
        },
    }

    def __init__(self, db: AsyncSession):
        """
        Initialize alert service.

        Args:
            db: AsyncSession for database operations
        """
        self.db = db
        self.repo = AlertRepository(db)

    def _calculate_severity(
        self,
        metric: str,
        actual_value: float,
        threshold: float,
        operator: str,
    ) -> str:
        """
        Calculate alert severity based on metric deviation.

        Severity is determined by how far the actual value deviates from
        the threshold. Uses metric-specific thresholds to categorize.

        Args:
            metric: Metric name (temperature, rainfall, etc.)
            actual_value: Actual measured value
            threshold: Rule threshold value
            operator: Comparison operator (>, <, >=, <=, ==)

        Returns:
            Severity level: "HIGH", "MEDIUM", or "LOW"
        """
        metric_lower = metric.lower()

        # Calculate absolute deviation
        deviation = abs(actual_value - threshold)

        # Get severity thresholds for this metric
        thresholds = self.SEVERITY_THRESHOLDS.get(metric_lower, {})

        if not thresholds:
            logger.debug(f"No severity thresholds for metric: {metric}")
            return "LOW"

        # Check if HIGH severity
        if deviation > thresholds.get("HIGH", float("inf")):
            return "HIGH"

        # Check if MEDIUM severity
        if deviation > thresholds.get("MEDIUM", float("inf")):
            return "MEDIUM"

        # Default to LOW
        return "LOW"

    def _serialize_weather_snapshot(
        self,
        weather_data: dict[str, Any] | None,
    ) -> str | None:
        """
        Serialize weather snapshot to JSON string with validation.

        Args:
            weather_data: Dictionary of weather metrics

        Returns:
            JSON string (max 2000 chars) or None if serialization fails
        """
        if not weather_data:
            return None

        try:
            # Serialize with limited precision
            json_str = json.dumps(weather_data, default=str)

            # Truncate to storage limit
            if len(json_str) > 2000:
                json_str = json_str[:1997] + "..."

            return json_str
        except (TypeError, ValueError) as e:
            logger.warning(
                "weather_snapshot_serialization_failed",
                extra={
                    "error": str(e),
                    "data_keys": list(weather_data.keys()) if weather_data else [],
                },
            )
            return None

    async def create_from_triggered_rule(
        self,
        location_id: uuid.UUID,
        result: RuleEvaluationResult,
        weather_snapshot: dict[str, Any] | None = None,
        user_id: uuid.UUID | None = None,
    ) -> Alert | None:
        """
        Create alert from triggered rule evaluation with deduplication.

        Core alert creation logic. Implements idempotency to prevent duplicate
        alerts within DUPLICATE_WINDOW_MINUTES. Only creates alert if:
        1. Rule is actually triggered
        2. Actual value is not None
        3. No recent alert exists for same rule + location + metric

        Args:
            location_id: Location UUID where condition triggered
            result: RuleEvaluationResult from rule engine
            weather_snapshot: Full weather context at time of trigger
            user_id: UUID of user who owns the rule (optional)

        Returns:
            Created Alert object, or None if duplicate detected

        Raises:
            AlertServiceError: On database or serialization error
        """
        rule = result.rule
        actual_value = result.actual_value

        # Validate rule was actually triggered
        if not result.triggered:
            logger.debug(f"Rule {rule.id} not triggered, skipping alert creation")
            return None

        if actual_value is None:
            logger.warning(
                "alert_skipped_no_value",
                extra={"rule_id": str(rule.id), "location_id": str(location_id)},
            )
            return None

        # Check for recent duplicate alert (deduplication)
        try:
            existing = await self.repo.get_recent_alert(
                location_id=location_id,
                rule_id=rule.id,
                metric=rule.metric,
                actual_value=actual_value,
                minutes=self.DUPLICATE_WINDOW_MINUTES,
            )

            if existing:
                logger.info(
                    "alert_duplicate_prevented",
                    extra={
                        "rule_id": str(rule.id),
                        "location_id": str(location_id),
                        "metric": rule.metric,
                        "existing_alert_id": str(existing.id),
                        "window_minutes": self.DUPLICATE_WINDOW_MINUTES,
                    },
                )
                return None

        except SQLAlchemyError as e:
            logger.error(
                "deduplication_check_failed",
                extra={"error": str(e), "rule_id": str(rule.id)},
            )
            raise AlertServiceError(f"Deduplication check failed: {e}") from e

        # Calculate severity
        severity = self._calculate_severity(
            metric=rule.metric,
            actual_value=actual_value,
            threshold=rule.threshold,
            operator=rule.operator,
        )

        # Serialize weather snapshot
        snapshot_json = self._serialize_weather_snapshot(weather_snapshot)

        # Create alert
        try:
            alert = await self.repo.create(
                location_id=location_id,
                rule_id=rule.id,
                user_id=user_id or rule.owner_id,
                metric=rule.metric,
                actual_value=actual_value,
                threshold=rule.threshold,
                operator=rule.operator,
                severity=severity,
                weather_snapshot=snapshot_json,
            )

            logger.info(
                "alert_created_successfully",
                extra={
                    "alert_id": str(alert.id),
                    "rule_id": str(rule.id),
                    "location_id": str(location_id),
                    "metric": rule.metric,
                    "actual_value": actual_value,
                    "threshold": rule.threshold,
                    "severity": severity,
                },
            )

            return alert

        except SQLAlchemyError as e:
            logger.error(
                "alert_creation_failed",
                extra={
                    "rule_id": str(rule.id),
                    "location_id": str(location_id),
                    "error": str(e),
                },
            )
            raise AlertServiceError(f"Failed to create alert: {e}") from e

    async def resolve_alert(self, alert_id: uuid.UUID) -> Alert | None:
        """
        Resolve an active alert, marking it as resolved.

        Args:
            alert_id: Alert UUID to resolve

        Returns:
            Resolved Alert object, or None if not found

        Raises:
            AlertServiceError: On database error
        """
        try:
            alert = await self.repo.resolve_alert(alert_id)
            return alert
        except SQLAlchemyError as e:
            logger.error(
                "alert_resolution_failed",
                extra={"alert_id": str(alert_id), "error": str(e)},
            )
            raise AlertServiceError(f"Failed to resolve alert: {e}") from e

    async def get_active_alerts(self) -> list[Alert]:
        """
        Get all active alerts system-wide.

        Returns:
            List of active Alert objects, ordered by recency (newest first)

        Raises:
            AlertServiceError: On database error
        """
        try:
            return await self.repo.get_active_alerts()
        except SQLAlchemyError as e:
            logger.error("fetch_active_alerts_failed", extra={"error": str(e)})
            raise AlertServiceError(f"Failed to fetch active alerts: {e}") from e

    async def get_active_alerts_by_severity(
        self,
        severity: str,
    ) -> list[Alert]:
        """
        Get active alerts filtered by severity level.

        Args:
            severity: Severity level ("LOW", "MEDIUM", "HIGH")

        Returns:
            List of Alert objects matching severity (newest first)

        Raises:
            AlertServiceError: On database error
        """
        if severity not in ["LOW", "MEDIUM", "HIGH"]:
            logger.warning(f"Invalid severity level: {severity}")
            return []

        try:
            return await self.repo.get_active_alerts_by_severity(severity)
        except SQLAlchemyError as e:
            logger.error(
                "fetch_alerts_by_severity_failed",
                extra={"severity": severity, "error": str(e)},
            )
            raise AlertServiceError(f"Failed to fetch alerts by severity: {e}") from e

    async def get_location_alerts(self, location_id: uuid.UUID) -> list[Alert]:
        """
        Get all active alerts for a specific location.

        Args:
            location_id: Location UUID

        Returns:
            List of active Alert objects for location (newest first)

        Raises:
            AlertServiceError: On database error
        """
        try:
            return await self.repo.get_active_by_location(location_id)
        except SQLAlchemyError as e:
            logger.error(
                "fetch_location_alerts_failed",
                extra={"location_id": str(location_id), "error": str(e)},
            )
            raise AlertServiceError(
                f"Failed to fetch alerts for location {location_id}: {e}"
            ) from e

    async def get_alert_count_for_location(self, location_id: uuid.UUID) -> int:
        """
        Count active alerts for a location.

        Args:
            location_id: Location UUID

        Returns:
            Number of active alerts

        Raises:
            AlertServiceError: On database error
        """
        try:
            return await self.repo.count_active_for_location(location_id)
        except SQLAlchemyError as e:
            logger.error(
                "count_location_alerts_failed",
                extra={"location_id": str(location_id), "error": str(e)},
            )
            raise AlertServiceError(
                f"Failed to count alerts for location {location_id}: {e}"
            ) from e

    async def get_critical_alert_count(self) -> int:
        """
        Get count of critical (HIGH severity) active alerts.

        Returns:
            Number of HIGH severity active alerts

        Raises:
            AlertServiceError: On database error
        """
        try:
            return await self.repo.count_active_by_severity("HIGH")
        except SQLAlchemyError as e:
            logger.error("count_critical_alerts_failed", extra={"error": str(e)})
            raise AlertServiceError(f"Failed to count critical alerts: {e}") from e
