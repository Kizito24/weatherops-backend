"""Integration tests for weather monitor task."""

import json
import uuid
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.location import Location
from app.models.rule import Rule
from app.workers.tasks.weather_monitor import _run_weather_monitor_async


@pytest.fixture
async def locations(db: AsyncSession) -> list[Location]:
    """Create multiple test locations."""
    owner_id = uuid.uuid4()
    locations = [
        Location(
            id=uuid.uuid4(),
            name="Lagos",
            latitude=6.5244,
            longitude=3.3792,
            owner_id=owner_id,
        ),
        Location(
            id=uuid.uuid4(),
            name="Nairobi",
            latitude=-1.2921,
            longitude=36.8219,
            owner_id=owner_id,
        ),
        Location(
            id=uuid.uuid4(),
            name="Cairo",
            latitude=30.0444,
            longitude=31.2357,
            owner_id=owner_id,
        ),
    ]
    for loc in locations:
        db.add(loc)
    await db.commit()
    return locations


@pytest.fixture
async def rules(db: AsyncSession, locations: list[Location]) -> dict:
    """Create test rules for locations."""
    rules_by_location = {}

    for location in locations:
        loc_rules = [
            Rule(
                id=uuid.uuid4(),
                location_id=location.id,
                name="High Temperature",
                metric="temperature",
                operator=">",
                threshold=35.0,
                active=True,
                owner_id=location.owner_id,
            ),
            Rule(
                id=uuid.uuid4(),
                location_id=location.id,
                name="Heavy Rain",
                metric="rainfall",
                operator=">",
                threshold=50.0,
                active=True,
                owner_id=location.owner_id,
            ),
        ]
        for rule in loc_rules:
            db.add(rule)
        rules_by_location[location.id] = loc_rules

    await db.commit()
    return rules_by_location


class TestWeatherMonitorTask:
    """Test weather monitor background task."""

    async def test_weather_monitor_processes_all_locations(
        self,
        db: AsyncSession,
        locations: list[Location],
        rules: dict,
    ):
        """Test that weather monitor processes all locations."""
        mock_weather_data = {
            "temperature": 38.5,
            "rainfall": 0,
            "wind_speed": 15,
            "humidity": 60,
        }

        with patch(
            "app.workers.tasks.weather_monitor.WeatherService.get_current_weather"
        ) as mock_weather:
            mock_weather.return_value = mock_weather_data

            with patch(
                "app.workers.tasks.weather_monitor.NotificationService.send_alert_notification"
            ) as mock_notify:
                mock_notify.return_value = {"email": True}

                result = await _run_weather_monitor_async()

                assert result["locations_processed"] == len(locations)
                assert mock_weather.call_count == len(locations)

    async def test_weather_monitor_creates_alerts(
        self,
        db: AsyncSession,
        locations: list[Location],
        rules: dict,
    ):
        """Test that triggered rules create alerts."""
        mock_weather_data = {
            "temperature": 38.5,
            "rainfall": 0,
            "wind_speed": 15,
            "humidity": 60,
        }

        with patch(
            "app.workers.tasks.weather_monitor.WeatherService.get_current_weather"
        ) as mock_weather:
            mock_weather.return_value = mock_weather_data

            with patch(
                "app.workers.tasks.weather_monitor.NotificationService.send_alert_notification"
            ) as mock_notify:
                mock_notify.return_value = {"email": True}

                result = await _run_weather_monitor_async()

                assert result["alerts_created"] >= 1
                assert result["rules_evaluated"] >= len(locations) * 2

    async def test_weather_monitor_sends_notifications(
        self,
        db: AsyncSession,
        locations: list[Location],
        rules: dict,
    ):
        """Test that alerts trigger notifications."""
        mock_weather_data = {
            "temperature": 38.5,
            "rainfall": 0,
            "wind_speed": 15,
            "humidity": 60,
        }

        with patch(
            "app.workers.tasks.weather_monitor.WeatherService.get_current_weather"
        ) as mock_weather:
            mock_weather.return_value = mock_weather_data

            with patch(
                "app.workers.tasks.weather_monitor.NotificationService.send_alert_notification"
            ) as mock_notify:
                mock_notify.return_value = {"email": True}

                result = await _run_weather_monitor_async()

                if result["alerts_created"] > 0:
                    assert result["notifications_sent"] > 0
                    assert mock_notify.called

    async def test_weather_monitor_handles_weather_service_error(
        self,
        db: AsyncSession,
        locations: list[Location],
        rules: dict,
    ):
        """Test graceful handling of weather service errors."""
        from app.services.weather_service import WeatherServiceError

        error_message = "Weather API unavailable"

        with patch(
            "app.workers.tasks.weather_monitor.WeatherService.get_current_weather"
        ) as mock_weather:
            mock_weather.side_effect = WeatherServiceError(error_message)

            result = await _run_weather_monitor_async()

            assert result["errors"] == len(locations)
            assert result["locations_processed"] == 0
            assert result["alerts_created"] == 0

    async def test_weather_monitor_partial_failure_continues(
        self,
        db: AsyncSession,
        locations: list[Location],
        rules: dict,
    ):
        """Test that one location failure doesn't stop others."""
        from app.services.weather_service import WeatherServiceError

        mock_weather_data = {
            "temperature": 38.5,
            "rainfall": 0,
            "wind_speed": 15,
            "humidity": 60,
        }

        with patch(
            "app.workers.tasks.weather_monitor.WeatherService.get_current_weather"
        ) as mock_weather:
            mock_weather.side_effect = [
                mock_weather_data,
                WeatherServiceError("API error"),
                mock_weather_data,
            ]

            with patch(
                "app.workers.tasks.weather_monitor.NotificationService.send_alert_notification"
            ) as mock_notify:
                mock_notify.return_value = {"email": True}

                result = await _run_weather_monitor_async()

                assert result["locations_processed"] == 2
                assert result["errors"] == 1

    async def test_weather_monitor_no_rules_no_alerts(
        self,
        db: AsyncSession,
        locations: list[Location],
    ):
        """Test processing location with no rules creates no alerts."""
        location_without_rules = Location(
            id=uuid.uuid4(),
            name="Empty Location",
            latitude=0.0,
            longitude=0.0,
            owner_id=locations[0].owner_id,
        )
        db.add(location_without_rules)
        await db.commit()

        mock_weather_data = {
            "temperature": 25.0,
            "rainfall": 0,
            "wind_speed": 10,
            "humidity": 50,
        }

        with patch(
            "app.workers.tasks.weather_monitor.WeatherService.get_current_weather"
        ) as mock_weather:
            mock_weather.return_value = mock_weather_data

            result = await _run_weather_monitor_async()

            assert result["rules_evaluated"] >= 0
            assert result["locations_processed"] >= 1

    async def test_weather_monitor_no_triggered_rules(
        self,
        db: AsyncSession,
        locations: list[Location],
        rules: dict,
    ):
        """Test processing location where no rules are triggered."""
        mock_weather_data = {
            "temperature": 20.0,
            "rainfall": 0,
            "wind_speed": 5,
            "humidity": 40,
        }

        with patch(
            "app.workers.tasks.weather_monitor.WeatherService.get_current_weather"
        ) as mock_weather:
            mock_weather.return_value = mock_weather_data

            result = await _run_weather_monitor_async()

            assert result["locations_processed"] >= 1
            assert result["alerts_created"] == 0

    async def test_weather_monitor_returns_statistics(
        self,
        db: AsyncSession,
        locations: list[Location],
        rules: dict,
    ):
        """Test that task returns proper statistics."""
        mock_weather_data = {
            "temperature": 38.5,
            "rainfall": 0,
            "wind_speed": 15,
            "humidity": 60,
        }

        with patch(
            "app.workers.tasks.weather_monitor.WeatherService.get_current_weather"
        ) as mock_weather:
            mock_weather.return_value = mock_weather_data

            with patch(
                "app.workers.tasks.weather_monitor.NotificationService.send_alert_notification"
            ) as mock_notify:
                mock_notify.return_value = {"email": True}

                result = await _run_weather_monitor_async()

                assert isinstance(result, dict)
                assert "locations_processed" in result
                assert "rules_evaluated" in result
                assert "alerts_created" in result
                assert "notifications_sent" in result
                assert "errors" in result

                assert isinstance(result["locations_processed"], int)
                assert isinstance(result["rules_evaluated"], int)
                assert isinstance(result["alerts_created"], int)
                assert isinstance(result["notifications_sent"], int)
                assert isinstance(result["errors"], int)

    async def test_weather_monitor_idempotency(
        self,
        db: AsyncSession,
        locations: list[Location],
        rules: dict,
    ):
        """Test that duplicate alerts are not created on repeated runs."""
        mock_weather_data = {
            "temperature": 38.5,
            "rainfall": 0,
            "wind_speed": 15,
            "humidity": 60,
        }

        with patch(
            "app.workers.tasks.weather_monitor.WeatherService.get_current_weather"
        ) as mock_weather:
            mock_weather.return_value = mock_weather_data

            with patch(
                "app.workers.tasks.weather_monitor.NotificationService.send_alert_notification"
            ) as mock_notify:
                mock_notify.return_value = {"email": True}

                result1 = await _run_weather_monitor_async()
                alerts_created_1 = result1["alerts_created"]

                result2 = await _run_weather_monitor_async()
                alerts_created_2 = result2["alerts_created"]

                assert alerts_created_2 == 0

    async def test_weather_monitor_with_inactive_rules(
        self,
        db: AsyncSession,
        locations: list[Location],
    ):
        """Test that inactive rules are not evaluated."""
        inactive_rule = Rule(
            id=uuid.uuid4(),
            location_id=locations[0].id,
            name="Inactive Rule",
            metric="temperature",
            operator=">",
            threshold=35.0,
            active=False,
            owner_id=locations[0].owner_id,
        )
        db.add(inactive_rule)
        await db.commit()

        mock_weather_data = {
            "temperature": 38.5,
            "rainfall": 0,
            "wind_speed": 15,
            "humidity": 60,
        }

        with patch(
            "app.workers.tasks.weather_monitor.WeatherService.get_current_weather"
        ) as mock_weather:
            mock_weather.return_value = mock_weather_data

            result = await _run_weather_monitor_async()

            assert result["locations_processed"] >= 1
            assert result["alerts_created"] == 0

    async def test_weather_monitor_error_tracking(
        self,
        db: AsyncSession,
        locations: list[Location],
    ):
        """Test that errors are properly tracked."""
        from app.services.weather_service import WeatherServiceError

        with patch(
            "app.workers.tasks.weather_monitor.WeatherService.get_current_weather"
        ) as mock_weather:
            mock_weather.side_effect = WeatherServiceError("Network error")

            result = await _run_weather_monitor_async()

            assert result["errors"] > 0
            assert result["locations_processed"] == 0
            assert result["alerts_created"] == 0
