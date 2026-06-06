"""Email notification channel with SendGrid integration."""

import logging
from typing import Any

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, HtmlContent

from app.core.channels.base import NotificationChannel
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class EmailChannel(NotificationChannel):
    """Email notification channel using SendGrid."""

    def __init__(self):
        """Initialize email channel with SendGrid client."""
        settings = get_settings()
        self.from_email = settings.SENDGRID_FROM_EMAIL or "alerts@weatherops.com"
        self.sendgrid_client = SendGridAPIClient(settings.SENDGRID_API_KEY)
        self.enabled = bool(settings.SENDGRID_API_KEY)

    async def send(
        self,
        recipient: str,
        subject: str,
        message: str,
        alert_data: dict[str, Any] | None = None,
    ) -> bool:
        """
        Send email notification via SendGrid.

        Args:
            recipient: Email address to send to
            subject: Email subject
            message: Plain text message body
            alert_data: Alert context data

        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning("SendGrid API key not configured, falling back to logging")
            self._log_fallback(recipient, subject, message, alert_data)
            return False

        try:
            # Build HTML version of email
            html_content = self._build_html_content(subject, message, alert_data)

            # Create Mail object
            mail = Mail(
                from_email=Email(self.from_email, "WeatherOps Alerts"),
                to_emails=To(recipient),
                subject=subject,
                plain_text_content=Content("text/plain", message),
                html_content=HtmlContent(html_content),
            )

            # Add tracking and headers
            mail.reply_to = Email("support@weatherops.com", "WeatherOps Support")

            # Send email
            response = self.sendgrid_client.send(mail)

            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully to {recipient} (ID: {response.headers.get('X-Message-Id')})")
                return True
            else:
                logger.error(f"SendGrid returned status {response.status_code}: {response.body}")
                return False

        except Exception as e:
            logger.error(f"Failed to send email to {recipient}: {e}", exc_info=True)
            return False

    def _build_html_content(
        self,
        subject: str,
        message: str,
        alert_data: dict[str, Any] | None = None,
    ) -> str:
        """
        Build HTML email content.

        Args:
            subject: Email subject
            message: Message body
            alert_data: Alert context

        Returns:
            HTML email content
        """
        alert_html = ""
        if alert_data:
            alert_html = f"""
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-top: 20px;">
                <h3 style="margin-top: 0; color: #333;">Alert Details</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Metric:</strong></td>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;">{alert_data.get('metric', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Actual Value:</strong></td>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;">{alert_data.get('value', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Threshold:</strong></td>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;">{alert_data.get('threshold', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px;"><strong>Operator:</strong></td>
                        <td style="padding: 8px;">{alert_data.get('operator', 'N/A')}</td>
                    </tr>
                </table>
            </div>
            """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #333; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2563eb; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .content {{ background-color: #f9fafb; padding: 20px; border-radius: 5px; }}
                .footer {{ margin-top: 20px; text-align: center; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⚠️ {subject}</h1>
                </div>
                <div class="content">
                    <p>{message}</p>
                    {alert_html}
                </div>
                <div class="footer">
                    <p>This alert was generated by WeatherOps</p>
                    <p><a href="https://weatherops.com">View Dashboard</a> | <a href="https://weatherops.com/settings">Manage Preferences</a></p>
                </div>
            </div>
        </body>
        </html>
        """

    def _log_fallback(
        self,
        recipient: str,
        subject: str,
        message: str,
        alert_data: dict[str, Any] | None = None,
    ) -> None:
        """Log email that would have been sent (fallback when SendGrid disabled)."""
        logger.info(
            f"Email Channel: Would send to {recipient}\n"
            f"Subject: {subject}\n"
            f"Body: {message}\n"
            f"Alert Data: {alert_data}"
        )
