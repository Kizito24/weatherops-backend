"""Rule evaluation engine for weather conditions."""

import logging
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rule import Rule
from app.repositories.rule_repository import RuleRepository

logger = logging.getLogger(__name__)


class RuleEvaluationResult:
    """Result of a rule evaluation."""

    def __init__(
        self,
        rule: Rule,
        triggered: bool,
        actual_value: float | None = None,
    ):
        """
        Initialize evaluation result.

        Args:
            rule: The rule being evaluated
            triggered: Whether the rule condition was met
            actual_value: The actual metric value
        """
        self.rule = rule
        self.triggered = triggered
        self.actual_value = actual_value

    def __repr__(self) -> str:
        status = "TRIGGERED" if self.triggered else "OK"
        return f"<RuleEval({self.rule.metric} {self.rule.operator} {self.rule.threshold} = {status})>"


class RuleEngine:
    """Engine for evaluating weather rules against actual data."""

    def __init__(self, db: AsyncSession):
        """Initialize rule engine."""
        self.db = db
        self.rule_repo = RuleRepository(db)

    async def evaluate_location_rules(
        self,
        location_id,
        weather_data: dict[str, Any],
    ) -> list[RuleEvaluationResult]:
        """
        Evaluate all active rules for a location.

        Args:
            location_id: Location UUID
            weather_data: Current weather data {metric: value, ...}

        Returns:
            List of evaluation results (triggered + untriggered)
        """
        rules = await self.rule_repo.get_active_by_location(location_id)
        results = []

        for rule in rules:
            result = self._evaluate_single_rule(rule, weather_data)
            results.append(result)

        return results

    async def get_triggered_rules(
        self,
        location_id,
        weather_data: dict[str, Any],
    ) -> list[RuleEvaluationResult]:
        """
        Get only the triggered rules for a location.

        Args:
            location_id: Location UUID
            weather_data: Current weather data

        Returns:
            List of triggered rules only
        """
        all_results = await self.evaluate_location_rules(
            location_id,
            weather_data,
        )
        triggered = [r for r in all_results if r.triggered]

        if triggered:
            logger.info(
                f"Location {location_id}: {len(triggered)} rules triggered"
            )

        return triggered

    @staticmethod
    def _evaluate_single_rule(
        rule: Rule,
        weather_data: dict[str, Any],
    ) -> RuleEvaluationResult:
        """
        Evaluate a single rule against weather data.

        Args:
            rule: Rule to evaluate
            weather_data: Current weather metrics

        Returns:
            Evaluation result
        """
        actual_value = weather_data.get(rule.metric)

        if actual_value is None:
            logger.warning(
                f"Metric '{rule.metric}' not found in weather data for rule {rule.id}"
            )
            return RuleEvaluationResult(rule, False, None)

        try:
            triggered = RuleEngine._compare_values(
                actual_value,
                rule.operator,
                rule.threshold,
            )

            return RuleEvaluationResult(rule, triggered, actual_value)

        except Exception as e:
            logger.error(
                f"Error evaluating rule {rule.id}: {e}",
                exc_info=True,
            )
            return RuleEvaluationResult(rule, False, actual_value)

    @staticmethod
    def _compare_values(
        actual: float,
        operator: str,
        threshold: float,
    ) -> bool:
        """
        Compare actual value against threshold using operator.

        Args:
            actual: Actual metric value
            operator: Comparison operator (>, <, >=, <=, ==)
            threshold: Threshold value

        Returns:
            Whether condition is met

        Raises:
            ValueError: If operator is invalid
        """
        if operator == ">":
            return actual > threshold
        elif operator == "<":
            return actual < threshold
        elif operator == ">=":
            return actual >= threshold
        elif operator == "<=":
            return actual <= threshold
        elif operator == "==":
            return actual == threshold
        else:
            raise ValueError(f"Invalid operator: {operator}")
