"""SMS notification channel with Twilio integration."""

import logging
import re
from typing import Any

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from app.core.channels.base import NotificationChannel
from app.core.config import get_settings

logger = logging.getLogger(__name__)

# SMS character limit (standard SMS is 160 characters, but we split long messages)
SMS_CHAR_LIMIT = 160


class SMSChannel(NotificationChannel):
    """SMS notification channel using Twilio."""

    def __init__(self):
        """Initialize SMS channel with Twilio client."""
        settings = get_settings()
        self.from_number = settings.TWILIO_PHONE_NUMBER
        self.twilio_client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN,
        )
        self.enabled = bool(
            settings.TWILIO_ACCOUNT_SID
            and settings.TWILIO_AUTH_TOKEN
            and settings.TWILIO_PHONE_NUMBER
        )

    async def send(
        self,
        recipient: str,
        subject: str,
        message: str,
        alert_data: dict[str, Any] | None = None,
    ) -> bool:
        """
        Send SMS notification via Twilio.

        Args:
            recipient: Phone number to send to (E.164 format: +1234567890)
            subject: Message subject (used in alert prefix)
            message: Message body
            alert_data: Alert context data

        Returns:
            True if SMS sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning("Twilio credentials not configured, falling back to logging")
            self._log_fallback(recipient, subject, message, alert_data)
            return False

        # Validate phone number
        if not self._validate_phone_number(recipient):
            logger.error(f"Invalid phone number format: {recipient}")
            return False

        try:
            # Build SMS message with subject and body
            sms_message = f"🚨 {subject}\n{message}"

            # Chunk message if too long (SMS has 160 char limit)
            chunks = self._chunk_message(sms_message, SMS_CHAR_LIMIT)

            if len(chunks) > 3:
                logger.warning(
                    f"Message for {recipient} is very long ({len(sms_message)} chars), "
                    f"will be split into {len(chunks)} SMS"
                )

            # Send all chunks
            sids = []
            for i, chunk in enumerate(chunks):
                # Add chunk number for multi-part messages
                if len(chunks) > 1:
                    chunk_prefix = f"[{i+1}/{len(chunks)}] "
                    chunk = chunk_prefix + chunk[len(chunk_prefix):]

                sms = self.twilio_client.messages.create(
                    body=chunk,
                    from_=self.from_number,
                    to=recipient,
                )
                sids.append(sms.sid)

                logger.info(f"SMS sent to {recipient} (SID: {sms.sid})")

            return True

        except TwilioRestException as e:
            logger.error(
                f"Twilio error sending SMS to {recipient}: "
                f"{e.code} - {e.msg}",
                exc_info=True,
            )
            return False
        except Exception as e:
            logger.error(
                f"Failed to send SMS to {recipient}: {e}",
                exc_info=True,
            )
            return False

    @staticmethod
    def _validate_phone_number(phone_number: str) -> bool:
        """
        Validate phone number in E.164 format.

        Args:
            phone_number: Phone number to validate

        Returns:
            True if valid E.164 format, False otherwise
        """
        # E.164 format: +[1-9]{1}[0-9]{1,14}
        pattern = r"^\+[1-9]\d{1,14}$"
        return bool(re.match(pattern, phone_number))

    @staticmethod
    def _chunk_message(message: str, max_length: int) -> list[str]:
        """
        Split long message into SMS chunks.

        Args:
            message: Message to split
            max_length: Maximum length per chunk (default 160)

        Returns:
            List of message chunks
        """
        if len(message) <= max_length:
            return [message]

        chunks = []
        current_chunk = ""

        for word in message.split():
            if len(current_chunk) + len(word) + 1 <= max_length:
                current_chunk += word + " "
            else:
                if current_chunk:
                    chunks.append(current_chunk.rstrip())
                current_chunk = word + " "

        if current_chunk:
            chunks.append(current_chunk.rstrip())

        return chunks

    def _log_fallback(
        self,
        recipient: str,
        subject: str,
        message: str,
        alert_data: dict[str, Any] | None = None,
    ) -> None:
        """Log SMS that would have been sent (fallback when Twilio disabled)."""
        sms_message = f"🚨 {subject}\n{message}"
        logger.info(
            f"SMS Channel: Would send to {recipient}\n"
            f"Message: {sms_message[:160]}\n"
            f"Alert Data: {alert_data}"
        )
