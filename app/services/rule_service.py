"""Rule service business logic."""

import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rule import Rule
from app.repositories.rule_repository import RuleRepository
from app.repositories.location_repository import LocationRepository
from app.schemas.rule import RuleCreate, RuleUpdate
from app.services.location_service import LocationService

logger = logging.getLogger(__name__)


VALID_METRICS = {"temperature", "rainfall", "wind_speed", "humidity"}
VALID_OPERATORS = {">", "<", ">=", "<=", "=="}


class RuleValidationError(Exception):
    """Raised when rule validation fails."""

    pass


class RuleNotFoundError(Exception):
    """Raised when rule is not found."""

    pass


class RuleAccessError(Exception):
    """Raised when user doesn't have access to rule."""

    pass


class RuleService:
    """Service for rule operations."""

    def __init__(self, db: AsyncSession):
        """Initialize service."""
        self.db = db
        self.repo = RuleRepository(db)
        self.location_repo = LocationRepository(db)
        self.location_service = LocationService(db)

    async def create_rule(
        self,
        user_id: uuid.UUID,
        data: RuleCreate,
    ) -> Rule:
        """
        Create a new rule with validation.

        Args:
            user_id: User ID.
            data: Rule data.

        Returns:
            Created rule.

        Raises:
            RuleValidationError: If validation fails.
            RuleAccessError: If user doesn't own location.
        """
        self._validate_rule_data(data.metric, data.operator, data.threshold)

        await self.location_service.get_location(user_id, data.location_id)

        rule = await self.repo.create(
            location_id=data.location_id,
            metric=data.metric,
            operator=data.operator,
            threshold=data.threshold,
        )

        logger.info(f"Rule created by user {user_id}: {rule.id}")
        return rule

    async def get_rule(
        self,
        user_id: uuid.UUID,
        rule_id: uuid.UUID,
    ) -> Rule:
        """
        Get a rule with ownership validation.

        Args:
            user_id: User ID.
            rule_id: Rule ID.

        Returns:
            Rule.

        Raises:
            RuleNotFoundError: If rule not found.
            RuleAccessError: If user doesn't own location.
        """
        rule = await self.repo.get_by_id(rule_id)

        if not rule:
            raise RuleNotFoundError(f"Rule {rule_id} not found")

        location = await self.location_repo.get_by_id(rule.location_id)
        if location.user_id != user_id:
            logger.warning(f"Unauthorized access to rule {rule_id} by user {user_id}")
            raise RuleAccessError("You don't have access to this rule")

        return rule

    async def get_location_rules(
        self,
        user_id: uuid.UUID,
        location_id: uuid.UUID,
    ) -> list[Rule]:
        """
        Get all rules for a location with ownership validation.

        Args:
            user_id: User ID.
            location_id: Location ID.

        Returns:
            List of rules.

        Raises:
            RuleAccessError: If user doesn't own location.
        """
        await self.location_service.get_location(user_id, location_id)
        rules = await self.repo.get_by_location(location_id)
        logger.debug(f"Retrieved {len(rules)} rules for location {location_id}")
        return rules

    async def update_rule(
        self,
        user_id: uuid.UUID,
        rule_id: uuid.UUID,
        data: RuleUpdate,
    ) -> Rule:
        """
        Update a rule with validation.

        Args:
            user_id: User ID.
            rule_id: Rule ID.
            data: Update data.

        Returns:
            Updated rule.

        Raises:
            RuleNotFoundError: If rule not found.
            RuleAccessError: If user doesn't own location.
            RuleValidationError: If validation fails.
        """
        rule = await self.get_rule(user_id, rule_id)

        if data.metric or data.operator or data.threshold:
            metric = data.metric or rule.metric
            operator = data.operator or rule.operator
            threshold = data.threshold or rule.threshold
            self._validate_rule_data(metric, operator, threshold)

        updated = await self.repo.update(
            rule_id=rule_id,
            metric=data.metric,
            operator=data.operator,
            threshold=data.threshold,
            is_active=data.is_active,
        )

        logger.info(f"Rule updated by user {user_id}: {rule_id}")
        return updated

    async def delete_rule(
        self,
        user_id: uuid.UUID,
        rule_id: uuid.UUID,
    ) -> None:
        """
        Delete a rule with ownership validation.

        Args:
            user_id: User ID.
            rule_id: Rule ID.

        Raises:
            RuleNotFoundError: If rule not found.
            RuleAccessError: If user doesn't own location.
        """
        await self.get_rule(user_id, rule_id)

        deleted = await self.repo.delete(rule_id)

        if not deleted:
            raise RuleNotFoundError(f"Failed to delete rule {rule_id}")

        logger.info(f"Rule deleted by user {user_id}: {rule_id}")

    @staticmethod
    def _validate_rule_data(
        metric: str,
        operator: str,
        threshold: float,
    ) -> None:
        """
        Validate rule data.

        Args:
            metric: Metric name.
            operator: Comparison operator.
            threshold: Threshold value.

        Raises:
            RuleValidationError: If validation fails.
        """
        if metric not in VALID_METRICS:
            raise RuleValidationError(
                f"Invalid metric '{metric}'. Must be one of: {', '.join(VALID_METRICS)}"
            )

        if operator not in VALID_OPERATORS:
            raise RuleValidationError(
                f"Invalid operator '{operator}'. Must be one of: {', '.join(VALID_OPERATORS)}"
            )

        if not isinstance(threshold, (int, float)):
            raise RuleValidationError("Threshold must be a number")
