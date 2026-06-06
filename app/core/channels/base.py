"""Base notification channel."""

from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class NotificationChannel(ABC):
    """Abstract base class for notification channels."""

    @abstractmethod
    async def send(
        self,
        recipient: str,
        subject: str,
        message: str,
        alert_data: dict | None = None,
    ) -> bool:
        """
        Send notification via this channel.

        Args:
            recipient: Channel-specific recipient (email, phone, webhook URL)
            subject: Message subject/title
            message: Message body
            alert_data: Additional alert context

        Returns:
            True if sent successfully, False otherwise
        """
        pass

    def _format_alert_message(
        self,
        subject: str,
        message: str,
        alert_data: dict | None = None,
    ) -> str:
        """Format alert message with context."""
        formatted = f"[ALERT] {subject}\n{message}"

        if alert_data:
            formatted += f"\n\nMetric: {alert_data.get('metric')}"
            formatted += f"\nValue: {alert_data.get('value')}"
            formatted += f"\nThreshold: {alert_data.get('threshold')}"
            formatted += f"\nLocation: {alert_data.get('location_name', 'N/A')}"

        return formatted
