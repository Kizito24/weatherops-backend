"""User preference request and response schemas."""

from pydantic import BaseModel, Field, HttpUrl


class UserPreferenceUpdate(BaseModel):
    """Update user preferences request."""

    # Email preferences
    email_alerts_enabled: bool | None = None
    email_digest_enabled: bool | None = None
    email_digest_frequency: str | None = Field(None, pattern="^(daily|weekly|monthly)$")

    # SMS preferences
    sms_alerts_enabled: bool | None = None
    sms_phone_number: str | None = Field(None, pattern=r"^\+?[1-9]\d{1,14}$")

    # Webhook preferences
    webhook_enabled: bool | None = None
    webhook_url: str | None = None

    # Alert severity filters
    alert_low_enabled: bool | None = None
    alert_medium_enabled: bool | None = None
    alert_high_enabled: bool | None = None

    # Quiet hours
    quiet_hours_enabled: bool | None = None
    quiet_hours_start: str | None = Field(None, pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    quiet_hours_end: str | None = Field(None, pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")

    # Custom severity thresholds
    temperature_high_threshold: float | None = None
    temperature_medium_threshold: float | None = None
    rainfall_high_threshold: float | None = None
    rainfall_medium_threshold: float | None = None
    wind_speed_high_threshold: float | None = None
    wind_speed_medium_threshold: float | None = None


class UserPreferenceResponse(BaseModel):
    """User preference response schema."""

    # Email preferences
    email_alerts_enabled: bool
    email_digest_enabled: bool
    email_digest_frequency: str

    # SMS preferences
    sms_alerts_enabled: bool
    sms_phone_number: str | None = None

    # Webhook preferences
    webhook_enabled: bool
    webhook_url: str | None = None

    # Alert severity filters
    alert_low_enabled: bool
    alert_medium_enabled: bool
    alert_high_enabled: bool

    # Quiet hours
    quiet_hours_enabled: bool
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None

    # Custom severity thresholds
    temperature_high_threshold: float | None = None
    temperature_medium_threshold: float | None = None
    rainfall_high_threshold: float | None = None
    rainfall_medium_threshold: float | None = None
    wind_speed_high_threshold: float | None = None
    wind_speed_medium_threshold: float | None = None

    model_config = {
        "from_attributes": True,
    }
