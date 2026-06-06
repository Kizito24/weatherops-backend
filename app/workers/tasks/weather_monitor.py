"""Periodic weather monitoring task."""

import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import AsyncSessionLocal
from app.repositories.location_repository import LocationRepository
from app.services.weather_service import WeatherService, WeatherServiceError
from app.services.rule_engine import RuleEngine
from app.services.alert_service import AlertService
from app.services.notification_service import NotificationService
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="tasks.weather_monitor",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3},
    retry_backoff=True,
    retry_backoff_max=600,
)
def run_weather_monitor(self) -> dict[str, int]:
    """
    Periodic task to monitor weather and evaluate rules.

    Runs every 5-10 minutes to:
    1. Fetch all monitored locations
    2. Retrieve current weather for each location
    3. Evaluate all active rules
    4. Create alerts for triggered rules
    5. Send notifications

    Returns:
        Summary dict with stats
    """
    import asyncio

    result = asyncio.run(_run_weather_monitor_async())
    return result


async def _run_weather_monitor_async() -> dict[str, int]:
    """
    Async implementation of weather monitoring.

    Returns:
        Summary with counts
    """
    logger.info("Weather monitor task started")

    async with AsyncSessionLocal() as db:
        location_repo = LocationRepository(db)
        weather_service = WeatherService()
        rule_engine = RuleEngine(db)
        alert_service = AlertService(db)
        notification_service = NotificationService()

        locations = await location_repo.get_all()
        logger.info(f"Processing {len(locations)} locations")

        stats = {
            "locations_processed": 0,
            "rules_evaluated": 0,
            "alerts_created": 0,
            "notifications_sent": 0,
            "errors": 0,
        }

        for location in locations:
            try:
                await _process_location(
                    location,
                    weather_service,
                    rule_engine,
                    alert_service,
                    notification_service,
                    stats,
                )
            except Exception as e:
                logger.error(
                    f"Error processing location {location.id}: {e}",
                    exc_info=True,
                )
                stats["errors"] += 1
                continue

        logger.info(
            f"Weather monitor task completed. "
            f"Locations: {stats['locations_processed']}, "
            f"Rules: {stats['rules_evaluated']}, "
            f"Alerts: {stats['alerts_created']}"
        )

        return stats


async def _process_location(
    location,
    weather_service: WeatherService,
    rule_engine: RuleEngine,
    alert_service: AlertService,
    notification_service: NotificationService,
    stats: dict,
) -> None:
    """
    Process a single location.

    Args:
        location: Location to process
        weather_service: Service for fetching weather
        rule_engine: Service for evaluating rules
        alert_service: Service for creating alerts
        notification_service: Service for sending notifications
        stats: Stats dict to update
    """
    logger.debug(f"Processing location: {location.name} ({location.id})")

    try:
        weather_data = await weather_service.get_current_weather(
            location.latitude,
            location.longitude,
        )
    except WeatherServiceError as e:
        logger.error(
            f"Failed to fetch weather for {location.name}: {e}"
        )
        stats["errors"] += 1
        return

    triggered_results = await rule_engine.get_triggered_rules(
        location.id,
        weather_data,
    )

    stats["locations_processed"] += 1
    stats["rules_evaluated"] += len(triggered_results)

    if not triggered_results:
        logger.debug(f"No rules triggered for {location.name}")
        return

    alerts_created = []

    for result in triggered_results:
        try:
            alert = await alert_service.create_from_triggered_rule(
                location.id,
                result,
                weather_data,
            )

            if alert:
                alerts_created.append(alert)
                stats["alerts_created"] += 1

        except Exception as e:
            logger.error(
                f"Failed to create alert for rule {result.rule.id}: {e}",
                exc_info=True,
            )
            continue

    if alerts_created:
        logger.info(
            f"{location.name}: {len(alerts_created)} alerts created"
        )

        for alert in alerts_created:
            try:
                results = await notification_service.send_alert_notification(
                    alert,
                    recipients={
                        "email": ["admin@weatherops.com"],
                    },
                )

                if any(results.values()):
                    stats["notifications_sent"] += 1

            except Exception as e:
                logger.error(
                    f"Failed to send notification for alert {alert.id}: {e}",
                    exc_info=True,
                )
                continue
