"""Integration tests for automation engine."""

import json
import uuid
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.location import Location
from app.models.rule import Rule
from app.models.alert import Alert
from app.repositories.location_repository import LocationRepository
from app.repositories.rule_repository import RuleRepository
from app.repositories.alert_repository import AlertRepository
from app.services.weather_service import WeatherService
from app.services.rule_engine import RuleEngine, RuleEvaluationResult
from app.services.alert_service import AlertService
from app.services.notification_service import NotificationService


@pytest.fixture
async def location(db: AsyncSession) -> Location:
    """Create test location."""
    location = Location(
        id=uuid.uuid4(),
        name="Test City",
        latitude=10.0,
        longitude=20.0,
        owner_id=uuid.uuid4(),
    )
    db.add(location)
    await db.commit()
    return location


@pytest.fixture
async def rule(db: AsyncSession, location: Location) -> Rule:
    """Create test rule."""
    rule = Rule(
        id=uuid.uuid4(),
        location_id=location.id,
        name="High Temperature",
        metric="temperature",
        operator=">",
        threshold=35.0,
        active=True,
        owner_id=location.owner_id,
    )
    db.add(rule)
    await db.commit()
    return rule


class TestRuleEngine:
    """Test rule evaluation engine."""

    async def test_evaluate_single_rule_greater_than_triggered(
        self,
        db: AsyncSession,
        location: Location,
        rule: Rule,
    ):
        """Test rule evaluation when condition is triggered."""
        engine = RuleEngine(db)
        weather_data = {"temperature": 38.5}

        results = await engine.evaluate_location_rules(location.id, weather_data)

        assert len(results) > 0
        assert results[0].triggered is True
        assert results[0].actual_value == 38.5

    async def test_evaluate_single_rule_greater_than_not_triggered(
        self,
        db: AsyncSession,
        location: Location,
        rule: Rule,
    ):
        """Test rule evaluation when condition is not triggered."""
        engine = RuleEngine(db)
        weather_data = {"temperature": 30.0}

        results = await engine.evaluate_location_rules(location.id, weather_data)

        assert len(results) > 0
        assert results[0].triggered is False

    async def test_get_triggered_rules_only(
        self,
        db: AsyncSession,
        location: Location,
        rule: Rule,
    ):
        """Test getting only triggered rules."""
        engine = RuleEngine(db)
        weather_data = {"temperature": 38.5}

        triggered = await engine.get_triggered_rules(location.id, weather_data)

        assert len(triggered) == 1
        assert triggered[0].triggered is True

    async def test_compare_values_greater_than(self):
        """Test > operator comparison."""
        engine = RuleEngine(None)
        assert engine._compare_values(38.5, ">", 35.0) is True
        assert engine._compare_values(34.0, ">", 35.0) is False

    async def test_compare_values_less_than(self):
        """Test < operator comparison."""
        engine = RuleEngine(None)
        assert engine._compare_values(32.0, "<", 35.0) is True
        assert engine._compare_values(38.0, "<", 35.0) is False

    async def test_compare_values_equal(self):
        """Test == operator comparison."""
        engine = RuleEngine(None)
        assert engine._compare_values(35.0, "==", 35.0) is True
        assert engine._compare_values(35.1, "==", 35.0) is False

    async def test_compare_values_greater_equal(self):
        """Test >= operator comparison."""
        engine = RuleEngine(None)
        assert engine._compare_values(35.0, ">=", 35.0) is True
        assert engine._compare_values(36.0, ">=", 35.0) is True
        assert engine._compare_values(34.0, ">=", 35.0) is False

    async def test_compare_values_less_equal(self):
        """Test <= operator comparison."""
        engine = RuleEngine(None)
        assert engine._compare_values(35.0, "<=", 35.0) is True
        assert engine._compare_values(34.0, "<=", 35.0) is True
        assert engine._compare_values(36.0, "<=", 35.0) is False


class TestAlertService:
    """Test alert creation and management."""

    async def test_create_alert_from_triggered_rule(
        self,
        db: AsyncSession,
        location: Location,
        rule: Rule,
    ):
        """Test creating alert from triggered rule."""
        engine = RuleEngine(db)
        alert_service = AlertService(db)

        weather_data = {"temperature": 38.5, "humidity": 65}
        triggered_rules = await engine.get_triggered_rules(location.id, weather_data)

        alert = await alert_service.create_from_triggered_rule(
            location.id,
            triggered_rules[0],
            weather_data,
        )

        assert alert is not None
        assert alert.location_id == location.id
        assert alert.rule_id == rule.id
        assert alert.actual_value == 38.5
        assert alert.status == "active"

    async def test_duplicate_alert_prevention(
        self,
        db: AsyncSession,
        location: Location,
        rule: Rule,
    ):
        """Test idempotency prevents duplicate alerts."""
        engine = RuleEngine(db)
        alert_service = AlertService(db)

        weather_data = {"temperature": 38.5}
        triggered_rules = await engine.get_triggered_rules(location.id, weather_data)
        result = triggered_rules[0]

        alert1 = await alert_service.create_from_triggered_rule(
            location.id,
            result,
            weather_data,
        )
        assert alert1 is not None

        alert2 = await alert_service.create_from_triggered_rule(
            location.id,
            result,
            weather_data,
        )
        assert alert2 is None

    async def test_duplicate_alert_after_window_expires(
        self,
        db: AsyncSession,
        location: Location,
        rule: Rule,
    ):
        """Test alert can be created after 5-minute window."""
        alert_repo = AlertRepository(db)
        alert_service = AlertService(db)
        engine = RuleEngine(db)

        weather_data = {"temperature": 38.5}
        triggered_rules = await engine.get_triggered_rules(location.id, weather_data)
        result = triggered_rules[0]

        alert1 = await alert_service.create_from_triggered_rule(
            location.id,
            result,
            weather_data,
        )
        assert alert1 is not None

        old_alert = await alert_repo.get_by_id(alert1.id)
        old_alert.created_at = datetime.utcnow() - timedelta(minutes=6)
        db.add(old_alert)
        await db.commit()

        alert2 = await alert_service.create_from_triggered_rule(
            location.id,
            result,
            weather_data,
        )
        assert alert2 is not None
        assert alert2.id != alert1.id

    async def test_resolve_alert(
        self,
        db: AsyncSession,
        location: Location,
        rule: Rule,
    ):
        """Test resolving an alert."""
        alert_service = AlertService(db)
        engine = RuleEngine(db)

        weather_data = {"temperature": 38.5}
        triggered_rules = await engine.get_triggered_rules(location.id, weather_data)

        alert = await alert_service.create_from_triggered_rule(
            location.id,
            triggered_rules[0],
            weather_data,
        )

        await alert_service.resolve_alert(alert.id)

        resolved = await alert_service.get_active_alerts()
        assert alert.id not in [a.id for a in resolved]

    async def test_get_active_alerts(
        self,
        db: AsyncSession,
        location: Location,
        rule: Rule,
    ):
        """Test retrieving active alerts."""
        alert_service = AlertService(db)
        engine = RuleEngine(db)

        weather_data = {"temperature": 38.5}
        triggered_rules = await engine.get_triggered_rules(location.id, weather_data)

        alert = await alert_service.create_from_triggered_rule(
            location.id,
            triggered_rules[0],
            weather_data,
        )

        active = await alert_service.get_active_alerts()

        assert len(active) > 0
        assert alert.id in [a.id for a in active]

    async def test_get_location_alerts(
        self,
        db: AsyncSession,
        location: Location,
        rule: Rule,
    ):
        """Test retrieving alerts for specific location."""
        alert_service = AlertService(db)
        engine = RuleEngine(db)

        weather_data = {"temperature": 38.5}
        triggered_rules = await engine.get_triggered_rules(location.id, weather_data)

        alert = await alert_service.create_from_triggered_rule(
            location.id,
            triggered_rules[0],
            weather_data,
        )

        location_alerts = await alert_service.get_location_alerts(location.id)

        assert len(location_alerts) > 0
        assert alert.id in [a.id for a in location_alerts]


class TestNotificationService:
    """Test notification delivery."""

    async def test_send_notification_email_only(
        self,
        db: AsyncSession,
        location: Location,
        rule: Rule,
    ):
        """Test sending notification via email."""
        alert_service = AlertService(db)
        notification_service = NotificationService()
        engine = RuleEngine(db)

        weather_data = {"temperature": 38.5}
        triggered_rules = await engine.get_triggered_rules(location.id, weather_data)

        alert = await alert_service.create_from_triggered_rule(
            location.id,
            triggered_rules[0],
            weather_data,
        )

        with patch.object(notification_service.channels["email"], "send") as mock_send:
            mock_send.return_value = True

            results = await notification_service.send_alert_notification(
                alert,
                recipients={"email": ["test@example.com"]},
            )

            assert "email" in results
            assert results["email"] is True

    async def test_send_notification_webhook(
        self,
        db: AsyncSession,
        location: Location,
        rule: Rule,
    ):
        """Test sending notification via webhook."""
        alert_service = AlertService(db)
        notification_service = NotificationService()
        engine = RuleEngine(db)

        weather_data = {"temperature": 38.5}
        triggered_rules = await engine.get_triggered_rules(location.id, weather_data)

        alert = await alert_service.create_from_triggered_rule(
            location.id,
            triggered_rules[0],
            weather_data,
        )

        with patch.object(
            notification_service.channels["webhook"], "send"
        ) as mock_send:
            mock_send.return_value = True

            results = await notification_service.send_alert_notification(
                alert,
                recipients={"webhook": ["https://example.com/alerts"]},
            )

            assert "webhook" in results
            assert results["webhook"] is True

    async def test_send_notification_multiple_recipients(
        self,
        db: AsyncSession,
        location: Location,
        rule: Rule,
    ):
        """Test notification to multiple recipients."""
        alert_service = AlertService(db)
        notification_service = NotificationService()
        engine = RuleEngine(db)

        weather_data = {"temperature": 38.5}
        triggered_rules = await engine.get_triggered_rules(location.id, weather_data)

        alert = await alert_service.create_from_triggered_rule(
            location.id,
            triggered_rules[0],
            weather_data,
        )

        with patch.object(notification_service.channels["email"], "send") as mock:
            mock.return_value = True

            results = await notification_service.send_alert_notification(
                alert,
                recipients={
                    "email": ["user1@example.com", "user2@example.com", "user3@example.com"],
                },
            )

            assert results["email"] is True
            assert mock.call_count == 3

    async def test_send_notification_no_recipients(
        self,
        db: AsyncSession,
        location: Location,
        rule: Rule,
    ):
        """Test notification with no recipients."""
        alert_service = AlertService(db)
        notification_service = NotificationService()
        engine = RuleEngine(db)

        weather_data = {"temperature": 38.5}
        triggered_rules = await engine.get_triggered_rules(location.id, weather_data)

        alert = await alert_service.create_from_triggered_rule(
            location.id,
            triggered_rules[0],
            weather_data,
        )

        results = await notification_service.send_alert_notification(alert)

        assert results == {}


class TestCompleteAutomationFlow:
    """Test end-to-end automation flow."""

    async def test_weather_trigger_to_notification(
        self,
        db: AsyncSession,
        location: Location,
        rule: Rule,
    ):
        """Test complete flow: weather → rule → alert → notification."""
        weather_data = {"temperature": 38.5, "humidity": 65}

        engine = RuleEngine(db)
        alert_service = AlertService(db)
        notification_service = NotificationService()

        triggered = await engine.get_triggered_rules(location.id, weather_data)
        assert len(triggered) == 1

        alert = await alert_service.create_from_triggered_rule(
            location.id,
            triggered[0],
            weather_data,
        )
        assert alert is not None

        with patch.object(notification_service.channels["email"], "send") as mock:
            mock.return_value = True

            results = await notification_service.send_alert_notification(
                alert,
                recipients={"email": ["admin@example.com"]},
            )

            assert results["email"] is True

    async def test_multiple_rules_multiple_alerts(
        self,
        db: AsyncSession,
        location: Location,
    ):
        """Test processing multiple rules triggering multiple alerts."""
        rule_repo = RuleRepository(db)
        engine = RuleEngine(db)
        alert_service = AlertService(db)

        rule1 = Rule(
            id=uuid.uuid4(),
            location_id=location.id,
            name="High Temperature",
            metric="temperature",
            operator=">",
            threshold=35.0,
            active=True,
            owner_id=location.owner_id,
        )

        rule2 = Rule(
            id=uuid.uuid4(),
            location_id=location.id,
            name="High Humidity",
            metric="humidity",
            operator=">",
            threshold=80.0,
            active=True,
            owner_id=location.owner_id,
        )

        db.add(rule1)
        db.add(rule2)
        await db.commit()

        weather_data = {"temperature": 38.5, "humidity": 85}

        triggered = await engine.get_triggered_rules(location.id, weather_data)
        assert len(triggered) == 2

        alerts = []
        for result in triggered:
            alert = await alert_service.create_from_triggered_rule(
                location.id,
                result,
                weather_data,
            )
            if alert:
                alerts.append(alert)

        assert len(alerts) == 2
        assert alerts[0].rule_id in [rule1.id, rule2.id]
        assert alerts[1].rule_id in [rule1.id, rule2.id]

    async def test_inactive_rules_not_evaluated(
        self,
        db: AsyncSession,
        location: Location,
    ):
        """Test that inactive rules are not evaluated."""
        rule = Rule(
            id=uuid.uuid4(),
            location_id=location.id,
            name="Inactive Rule",
            metric="temperature",
            operator=">",
            threshold=35.0,
            active=False,
            owner_id=location.owner_id,
        )
        db.add(rule)
        await db.commit()

        engine = RuleEngine(db)
        weather_data = {"temperature": 38.5}

        triggered = await engine.get_triggered_rules(location.id, weather_data)

        assert len(triggered) == 0
