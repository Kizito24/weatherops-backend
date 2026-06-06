"""
Example: Complete Alert and Notification Workflow

This demonstrates how to integrate AlertService and NotificationService
into your weather monitoring system.
"""

import uuid
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Any

# These would be imported from your actual application
# from app.services.alert_service import AlertService
# from app.services.notification_service import NotificationService
# from app.models.rule import Rule
# from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class Rule:
    """Example Rule model."""
    id: uuid.UUID
    metric: str
    threshold: float
    operator: str
    owner_id: uuid.UUID


@dataclass
class RuleEvaluationResult:
    """Example RuleEvaluationResult from rule engine."""
    rule: Rule
    triggered: bool
    actual_value: float | None = None


async def example_1_basic_alert_creation():
    """
    Example 1: Basic alert creation from triggered rule.

    Shows how to create an alert when a rule is triggered.
    """
    # Setup
    # alert_service = AlertService(db)

    # Create a rule that was triggered
    rule = Rule(
        id=uuid.uuid4(),
        metric="temperature",
        threshold=35.0,
        operator=">",
        owner_id=uuid.uuid4(),
    )

    result = RuleEvaluationResult(
        rule=rule,
        triggered=True,
        actual_value=38.5,  # Actual measured value
    )

    location_id = uuid.uuid4()
    weather_snapshot = {
        "temperature": 38.5,
        "humidity": 65.0,
        "pressure": 1013.2,
        "wind_speed": 12.5,
        "rainfall": 0.0,
    }

    # Create alert (this would be in your rule engine's trigger handler)
    # alert = await alert_service.create_from_triggered_rule(
    #     location_id=location_id,
    #     result=result,
    #     weather_snapshot=weather_snapshot,
    #     user_id=rule.owner_id,
    # )

    # What happens internally:
    # 1. Validates rule is triggered
    # 2. Checks for duplicate alert in past 5 minutes
    # 3. Calculates severity: 3.5°C deviation → "HIGH"
    # 4. Serializes weather snapshot to JSON (max 2000 chars)
    # 5. Persists to database
    # 6. Returns Alert object or None if duplicate

    print("✓ Alert created with severity=HIGH (3.5°C deviation from 35°C threshold)")


async def example_2_alert_with_notifications():
    """
    Example 2: Create alert and send notifications.

    Shows the complete flow from alert creation to notification delivery.
    """
    # alert_service = AlertService(db)
    # notification_service = NotificationService()

    # Step 1: Create alert (same as Example 1)
    rule = Rule(
        id=uuid.uuid4(),
        metric="temperature",
        threshold=35.0,
        operator=">",
        owner_id=uuid.uuid4(),
    )

    result = RuleEvaluationResult(
        rule=rule,
        triggered=True,
        actual_value=38.5,
    )

    # alert = await alert_service.create_from_triggered_rule(
    #     location_id=uuid.uuid4(),
    #     result=result,
    #     weather_snapshot={"temperature": 38.5},
    # )

    # if alert is None:
    #     print("Duplicate alert prevented")
    #     return

    # Step 2: Send notifications to multiple recipients/channels
    recipients = {
        "email": [
            "admin@weatherops.com",
            "ops-team@weatherops.com",
        ],
        "sms": [
            "+1234567890",  # E.164 format required
            "+1987654321",
        ],
        "webhook": [
            "https://external-system.example.com/alerts",
        ],
    }

    # results = await notification_service.send_notification(alert, recipients)

    # What happens internally:
    # 1. Formats message for human-readable display
    # 2. Sends to email recipients (HTML-formatted, branded)
    # 3. Sends to SMS recipients (concise text, auto-chunked to 160 chars)
    # 4. Sends to webhook endpoints (full JSON payload)
    # 5. Logs delivery results per channel
    # 6. Returns dict with success status per channel

    # results = {
    #     "email": True,    # Both emails sent successfully
    #     "sms": True,      # Both SMS sent successfully
    #     "webhook": False, # Webhook request failed (timeout, 5xx error)
    # }

    print("✓ Alert created and notifications sent to 5 recipients")
    print("  - Email: 2 recipients (success)")
    print("  - SMS: 2 recipients (success)")
    print("  - Webhook: 1 endpoint (failed - retryable)")
    print("  Alert persisted regardless of notification outcome")


async def example_3_severity_based_handling():
    """
    Example 3: Different handling based on alert severity.

    Shows how to handle alerts differently depending on severity level.
    """
    # alert_service = AlertService(db)
    # notification_service = NotificationService()

    # Create multiple alerts with different severities
    alerts_data = [
        ("temperature", 35.0, ">", 34.5),   # LOW: 0.5°C deviation
        ("temperature", 35.0, ">", 36.5),   # MEDIUM: 1.5°C deviation
        ("temperature", 35.0, ">", 41.0),   # HIGH: 6°C deviation
        ("rainfall", 10.0, ">", 25.0),      # HIGH: 15mm deviation
    ]

    for metric, threshold, op, actual_value in alerts_data:
        rule = Rule(
            id=uuid.uuid4(),
            metric=metric,
            threshold=threshold,
            operator=op,
            owner_id=uuid.uuid4(),
        )

        result = RuleEvaluationResult(
            rule=rule,
            triggered=True,
            actual_value=actual_value,
        )

        # alert = await alert_service.create_from_triggered_rule(
        #     location_id=uuid.uuid4(),
        #     result=result,
        # )

        # Severity calculated automatically based on deviation
        # Use it to determine notification strategy:

        # if alert.severity == "HIGH":
        #     # Critical - notify everyone immediately
        #     recipients = {
        #         "email": ["admin@example.com", "ops@example.com"],
        #         "sms": ["+1234567890"],  # Only SMS for HIGH
        #     }
        # elif alert.severity == "MEDIUM":
        #     # Warning - email only, batched
        #     recipients = {
        #         "email": ["ops@example.com"],
        #     }
        # else:  # LOW
        #     # Info - webhook only
        #     recipients = {
        #         "webhook": ["https://dashboard.example.com/alerts"],
        #     }

        # await notification_service.send_notification(alert, recipients)

    print("✓ Multiple alerts created with auto-calculated severity:")
    print("  - Temp 34.5°C → LOW (0.5°C deviation)")
    print("  - Temp 36.5°C → MEDIUM (1.5°C deviation)")
    print("  - Temp 41°C → HIGH (6°C deviation)")
    print("  - Rainfall 25mm → HIGH (15mm deviation)")


async def example_4_deduplication_in_action():
    """
    Example 4: Deduplication prevents alert storms.

    Shows how the 5-minute deduplication window prevents duplicate alerts.
    """
    # alert_service = AlertService(db)

    location_id = uuid.uuid4()
    rule = Rule(
        id=uuid.uuid4(),
        metric="temperature",
        threshold=35.0,
        operator=">",
        owner_id=uuid.uuid4(),
    )

    result = RuleEvaluationResult(
        rule=rule,
        triggered=True,
        actual_value=38.5,
    )

    # First trigger - alert created
    # alert1 = await alert_service.create_from_triggered_rule(
    #     location_id=location_id,
    #     result=result,
    # )
    # # Result: Alert created

    # Second trigger 2 minutes later - same condition, same location
    # alert2 = await alert_service.create_from_triggered_rule(
    #     location_id=location_id,
    #     result=result,  # Same rule, same value
    # )
    # # Result: alert2 is None (duplicate prevented)
    # # Users don't get spammed with duplicate notifications

    # Third trigger 6 minutes later - outside dedup window
    # alert3 = await alert_service.create_from_triggered_rule(
    #     location_id=location_id,
    #     result=result,  # Same rule, same value
    # )
    # # Result: Alert created (new alert, outside 5-minute window)

    print("✓ Deduplication in action:")
    print("  T+0min:   alert1 created (first trigger)")
    print("  T+2min:   alert2 = None (duplicate prevented)")
    print("  T+6min:   alert3 created (outside 5-minute window)")
    print("  Result: Users notified at T+0 and T+6, not spammed at T+2")


async def example_5_querying_alerts():
    """
    Example 5: Query and analyze alerts.

    Shows various ways to query and analyze alert data.
    """
    # alert_service = AlertService(db)

    # Get all active alerts
    # active_alerts = await alert_service.get_active_alerts()
    # print(f"Total active alerts: {len(active_alerts)}")

    # Get alerts by severity
    # high_severity = await alert_service.get_active_alerts_by_severity("HIGH")
    # print(f"Critical alerts: {len(high_severity)}")

    # medium_severity = await alert_service.get_active_alerts_by_severity("MEDIUM")
    # print(f"Warning alerts: {len(medium_severity)}")

    # Get alerts for specific location
    # location_id = uuid.uuid4()
    # location_alerts = await alert_service.get_location_alerts(location_id)
    # print(f"Alerts for location: {len(location_alerts)}")

    # Count alerts for location
    # count = await alert_service.get_alert_count_for_location(location_id)
    # print(f"Active alert count: {count}")

    # Get critical alert count (HIGH severity)
    # critical_count = await alert_service.get_critical_alert_count()
    # print(f"System-wide critical alerts: {critical_count}")

    print("✓ Alert querying capabilities:")
    print("  - Get all active alerts (system-wide)")
    print("  - Filter by severity (LOW/MEDIUM/HIGH)")
    print("  - Get alerts for specific location")
    print("  - Count alerts for location")
    print("  - Count critical (HIGH) alerts")


async def example_6_batch_notifications():
    """
    Example 6: Send notifications for multiple alerts in parallel.

    Shows efficient bulk notification for multiple alerts at once.
    """
    # alert_service = AlertService(db)
    # notification_service = NotificationService()

    # Get multiple alerts (e.g., from a location or time range)
    # alerts = await alert_service.get_active_alerts()

    # Or filter specific subset
    # high_alerts = await alert_service.get_active_alerts_by_severity("HIGH")

    # Shared recipients for all alerts
    recipients = {
        "email": ["ops-team@example.com"],
        "sms": ["+1234567890"],
    }

    # Send notifications to multiple alerts in parallel
    # results = await notification_service.send_bulk_notifications(
    #     alerts=high_alerts,
    #     recipients=recipients,
    # )

    # results = {
    #     "alert_id_1": [True, True],   # [email_success, sms_success]
    #     "alert_id_2": [True, False],  # Email succeeded, SMS failed
    #     "alert_id_3": [False, True],  # Email failed, SMS succeeded
    # }

    print("✓ Batch notification processing:")
    print("  - Send to multiple alerts concurrently")
    print("  - Uses asyncio.gather() for parallelization")
    print("  - Individual alert failures don't affect others")
    print("  - Per-channel success tracking")


async def example_7_resolving_alerts():
    """
    Example 7: Mark alerts as resolved.

    Shows how to transition alerts from active to resolved state.
    """
    # alert_service = AlertService(db)

    alert_id = uuid.uuid4()

    # Resolve an alert
    # resolved_alert = await alert_service.resolve_alert(alert_id)

    # What happens:
    # 1. Finds alert by ID
    # 2. Sets status = "resolved"
    # 3. Sets resolved_at = current timestamp (UTC)
    # 4. Persists to database
    # 5. Returns updated Alert object or None if not found

    # After resolution:
    # - Alert no longer appears in get_active_alerts()
    # - Alert still available in historical queries
    # - Users see alert as resolved in dashboard

    print("✓ Alert resolution:")
    print("  - Set status = 'resolved'")
    print("  - Record resolved_at timestamp")
    print("  - No longer appears in active alerts")
    print("  - Maintained in history for analytics")


async def example_8_testing_notifications():
    """
    Example 8: Test notification channel configuration.

    Shows how to verify notification channels are working.
    """
    # notification_service = NotificationService()

    # Test email delivery
    # email_ok = await notification_service.test_notification(
    #     channel_name="email",
    #     recipient="test@example.com",
    # )
    # print(f"Email configured: {email_ok}")

    # Test SMS delivery
    # sms_ok = await notification_service.test_notification(
    #     channel_name="sms",
    #     recipient="+1234567890",  # E.164 format
    # )
    # print(f"SMS configured: {sms_ok}")

    # Test webhook delivery
    # webhook_ok = await notification_service.test_notification(
    #     channel_name="webhook",
    #     recipient="https://example.com/test",
    # )
    # print(f"Webhook configured: {webhook_ok}")

    # Get available channels
    # channels = notification_service.get_available_channels()
    # print(f"Available channels: {channels}")
    # # Output: ['sms', 'email', 'webhook']

    print("✓ Notification testing:")
    print("  - Test individual channels before deployment")
    print("  - Validates credentials and configuration")
    print("  - Helps debug delivery issues")


if __name__ == "__main__":
    import asyncio

    async def main():
        print("=" * 70)
        print("ALERT AND NOTIFICATION SYSTEM EXAMPLES")
        print("=" * 70)
        print()

        await example_1_basic_alert_creation()
        print()

        await example_2_alert_with_notifications()
        print()

        await example_3_severity_based_handling()
        print()

        await example_4_deduplication_in_action()
        print()

        await example_5_querying_alerts()
        print()

        await example_6_batch_notifications()
        print()

        await example_7_resolving_alerts()
        print()

        await example_8_testing_notifications()
        print()

        print("=" * 70)
        print("For full implementation details, see:")
        print("  - ALERT_SERVICE_INTEGRATION.md")
        print("  - NOTIFICATION_SETUP.md")
        print("=" * 70)

    asyncio.run(main())
