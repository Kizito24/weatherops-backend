"""Notification service for alert delivery - Production-grade multi-channel system."""

import logging
import asyncio
from typing import Any

from app.models.alert import Alert
from app.core.channels import SMSChannel, EmailChannel, WebhookChannel
from app.core.channels.base import NotificationChannel

logger = logging.getLogger(__name__)


class NotificationServiceError(Exception):
    """Base exception for notification service errors."""

    pass


class NotificationService:
    """
    Production-grade multi-channel notification service.

    Responsible for:
    - Formatting alert messages for different channels
    - Dispatching notifications asynchronously
    - Managing multiple notification channels (Email, SMS, Webhook)
    - Handling delivery failures gracefully
    - Batch notification processing

    Design principle: Notification delivery failures MUST NOT break
    alert creation. Alerts are persisted regardless of notification success.

    Supported channels:
    - Email: HTML-formatted with styling and context
    - SMS: Concise text format with automatic chunking
    - Webhook: Full JSON payload via HTTP POST
    """

    def __init__(self):
        """Initialize notification service with available channels."""
        self.channels: dict[str, NotificationChannel] = {
            "sms": SMSChannel(),
            "email": EmailChannel(),
            "webhook": WebhookChannel(),
        }

    def format_alert_message(
        self,
        alert: Alert,
        include_snapshot: bool = False,
    ) -> tuple[str, str]:
        """
        Format alert message for human-readable display.

        Args:
            alert: Alert object
            include_snapshot: Whether to include weather snapshot details

        Returns:
            Tuple of (subject, message)
        """
        subject = f"🚨 {alert.metric.upper()} Alert [{alert.severity}]"

        message = (
            f"Weather alert triggered at {alert.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            f"\nMetric: {alert.metric.capitalize()}\n"
            f"Actual Value: {alert.actual_value}\n"
            f"Threshold: {alert.threshold}\n"
            f"Operator: {alert.operator}\n"
            f"Severity: {alert.severity}\n"
        )

        if include_snapshot and alert.weather_snapshot:
            message += f"\nWeather Snapshot:\n{alert.weather_snapshot}\n"

        return subject, message

    async def send_notification(
        self,
        alert: Alert,
        recipients: dict[str, list[str]],
    ) -> dict[str, bool]:
        """
        Send alert notification through configured channels.

        Single alert notification with recipients specified per channel.
        Failure in one channel does not affect others.

        Args:
            alert: Alert to send
            recipients: Dict mapping channel names to recipient lists
                       e.g., {"email": ["user@example.com"], "sms": ["+1234567890"]}

        Returns:
            Dict mapping channel names to success status (True/False)
        """
        if not recipients:
            logger.debug(f"No recipients configured for alert {alert.id}")
            return {}

        subject, message = self.format_alert_message(alert)

        alert_data = {
            "alert_id": str(alert.id),
            "location_id": str(alert.location_id),
            "rule_id": str(alert.rule_id),
            "metric": alert.metric,
            "value": alert.actual_value,
            "threshold": alert.threshold,
            "operator": alert.operator,
            "severity": alert.severity,
            "status": alert.status,
            "created_at": alert.created_at.isoformat() if alert.created_at else None,
        }

        results: dict[str, bool] = {}

        for channel_name, recipient_list in recipients.items():
            if channel_name not in self.channels:
                logger.warning(
                    "unknown_notification_channel",
                    extra={
                        "channel": channel_name,
                        "alert_id": str(alert.id),
                    },
                )
                results[channel_name] = False
                continue

            if not recipient_list:
                logger.debug(
                    "no_recipients_for_channel",
                    extra={
                        "channel": channel_name,
                        "alert_id": str(alert.id),
                    },
                )
                results[channel_name] = True
                continue

            channel = self.channels[channel_name]
            try:
                channel_results = await self._send_via_channel(
                    channel,
                    channel_name,
                    recipient_list,
                    subject,
                    message,
                    alert_data,
                    alert.id,
                )
                results[channel_name] = all(channel_results)
            except Exception as e:
                logger.error(
                    "notification_channel_error",
                    extra={
                        "channel": channel_name,
                        "alert_id": str(alert.id),
                        "error": str(e),
                    },
                )
                results[channel_name] = False

        return results

    async def send_bulk_notifications(
        self,
        alerts: list[Alert],
        recipients: dict[str, list[str]],
    ) -> dict[str, list[bool]]:
        """
        Send notifications for multiple alerts in parallel.

        Optimizes throughput by sending notifications asynchronously.
        Each alert notification is independent; failures don't cascade.

        Args:
            alerts: List of alerts to send
            recipients: Shared recipients dict for all alerts

        Returns:
            Dict mapping alert IDs (as strings) to list of channel results
        """
        tasks = [
            self.send_notification(alert, recipients)
            for alert in alerts
        ]

        results_list = await asyncio.gather(*tasks, return_exceptions=False)

        results = {
            str(alert.id): [results.get(ch, False) for ch in self.channels.keys()]
            for alert, results in zip(alerts, results_list)
        }

        logger.info(
            "bulk_notifications_completed",
            extra={
                "alert_count": len(alerts),
                "channels": list(self.channels.keys()),
            },
        )

        return results

    async def _send_via_channel(
        self,
        channel: NotificationChannel,
        channel_name: str,
        recipients: list[str],
        subject: str,
        message: str,
        alert_data: dict[str, Any],
        alert_id: Any,
    ) -> list[bool]:
        """
        Send notification via a single channel to multiple recipients.

        Sends to all recipients in parallel and handles individual failures.

        Args:
            channel: Notification channel instance
            channel_name: Name of the channel (for logging)
            recipients: List of recipients
            subject: Message subject
            message: Message body
            alert_data: Full alert context
            alert_id: Alert ID for logging

        Returns:
            List of success results per recipient
        """
        tasks = [
            channel.send(recipient, subject, message, alert_data)
            for recipient in recipients
        ]

        results = await asyncio.gather(*tasks, return_exceptions=False)

        successful = sum(1 for r in results if r)
        failed = len(results) - successful

        logger.info(
            "notification_channel_delivery",
            extra={
                "channel": channel_name,
                "alert_id": str(alert_id),
                "sent": successful,
                "failed": failed,
                "total": len(recipients),
            },
        )

        return results

    def register_channel(
        self,
        name: str,
        channel: NotificationChannel,
    ) -> None:
        """
        Register a custom notification channel.

        Allows runtime extension with new notification backends.

        Args:
            name: Channel name (e.g., "slack", "pagerduty")
            channel: Channel implementation instance
        """
        self.channels[name] = channel
        logger.info(
            "notification_channel_registered",
            extra={"channel": name},
        )

    def get_available_channels(self) -> list[str]:
        """
        Get list of available notification channels.

        Returns:
            List of registered channel names
        """
        return list(self.channels.keys())

    async def test_notification(
        self,
        channel_name: str,
        recipient: str,
    ) -> bool:
        """
        Test a notification channel with a test message.

        Useful for validating channel configuration.

        Args:
            channel_name: Channel to test
            recipient: Test recipient address/number/URL

        Returns:
            True if test notification sent successfully
        """
        if channel_name not in self.channels:
            logger.error(f"Unknown channel for test: {channel_name}")
            return False

        channel = self.channels[channel_name]

        test_subject = "🧪 WeatherOps Test Notification"
        test_message = "This is a test notification from WeatherOps alerting system."
        test_data = {
            "test": True,
            "timestamp": "__now__",
        }

        try:
            result = await channel.send(
                recipient,
                test_subject,
                test_message,
                test_data,
            )

            logger.info(
                "notification_test_completed",
                extra={
                    "channel": channel_name,
                    "recipient": recipient,
                    "success": result,
                },
            )

            return result
        except Exception as e:
            logger.error(
                "notification_test_failed",
                extra={
                    "channel": channel_name,
                    "error": str(e),
                },
            )
            return False
