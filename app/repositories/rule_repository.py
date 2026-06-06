"""Rule data access repository."""

import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.rule import Rule

logger = logging.getLogger(__name__)


class RuleRepository:
    """Repository for rule data access."""

    def __init__(self, db: AsyncSession):
        """Initialize repository."""
        self.db = db

    async def create(
        self,
        location_id: uuid.UUID,
        metric: str,
        operator: str,
        threshold: float,
    ) -> Rule:
        """Create a new rule."""
        rule = Rule(
            location_id=location_id,
            metric=metric,
            operator=operator,
            threshold=threshold,
        )
        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)
        logger.info(f"Rule created: {rule.id}")
        return rule

    async def get_by_id(self, rule_id: uuid.UUID) -> Rule | None:
        """Get rule by ID."""
        query = select(Rule).where(Rule.id == rule_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_location(self, location_id: uuid.UUID) -> list[Rule]:
        """Get all rules for a location."""
        query = select(Rule).where(Rule.location_id == location_id).order_by(Rule.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_active_by_location(self, location_id: uuid.UUID) -> list[Rule]:
        """Get active rules for a location."""
        query = select(Rule).where(
            (Rule.location_id == location_id) & (Rule.is_active == True)
        ).order_by(Rule.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update(
        self,
        rule_id: uuid.UUID,
        metric: str | None = None,
        operator: str | None = None,
        threshold: float | None = None,
        is_active: bool | None = None,
    ) -> Rule | None:
        """Update a rule."""
        rule = await self.get_by_id(rule_id)
        if not rule:
            return None

        if metric is not None:
            rule.metric = metric
        if operator is not None:
            rule.operator = operator
        if threshold is not None:
            rule.threshold = threshold
        if is_active is not None:
            rule.is_active = is_active

        await self.db.commit()
        await self.db.refresh(rule)
        logger.info(f"Rule updated: {rule_id}")
        return rule

    async def delete(self, rule_id: uuid.UUID) -> bool:
        """Delete a rule."""
        rule = await self.get_by_id(rule_id)
        if not rule:
            return False

        await self.db.delete(rule)
        await self.db.commit()
        logger.info(f"Rule deleted: {rule_id}")
        return True
