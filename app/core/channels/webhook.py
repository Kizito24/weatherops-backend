"""Webhook notification channel."""

import json
import logging
import httpx

from app.core.channels.base import NotificationChannel

logger = logging.getLogger(__name__)


class WebhookChannel(NotificationChannel):
    """Webhook notification channel for HTTP callbacks."""

    TIMEOUT = 10.0

    async def send(
        self,
        recipient: str,
        subject: str,
        message: str,
        alert_data: dict | None = None,
    ) -> bool:
        """
        Send webhook notification.

        Args:
            recipient: Webhook URL
            subject: Message subject
            message: Message body
            alert_data: Alert context

        Returns:
            True if successful, False otherwise
        """
        payload = {
            "subject": subject,
            "message": message,
            "alert": alert_data or {},
            "timestamp": str(__import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            )),
        }

        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                response = await client.post(
                    recipient,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code in (200, 201, 202, 204):
                    logger.info(f"Webhook {recipient}: {response.status_code} OK")
                    return True
                else:
                    logger.warning(
                        f"Webhook {recipient}: {response.status_code} "
                        f"{response.text[:200]}"
                    )
                    return False

        except httpx.TimeoutException:
            logger.error(f"Webhook {recipient}: Request timeout")
            return False
        except httpx.RequestError as e:
            logger.error(f"Webhook {recipient}: Request error - {e}")
            return False
        except Exception as e:
            logger.error(f"Webhook {recipient}: Unexpected error - {e}")
            return False
