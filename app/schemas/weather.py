"""Weather data schemas."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class CurrentWeatherResponse(BaseModel):
    """Current weather conditions."""

    temperature: Optional[float] = Field(None, description="Temperature in configured units")
    humidity: Optional[float] = Field(None, description="Humidity percentage (0-100)")
    wind_speed: Optional[float] = Field(None, description="Wind speed in km/h or mph")
    rainfall: Optional[float] = Field(None, description="Rainfall amount in mm or inches")
    condition: Optional[str] = Field(None, description="Weather condition string")
    pressure: Optional[float] = Field(None, description="Atmospheric pressure")
    visibility: Optional[float] = Field(None, description="Visibility distance")
    uv_index: Optional[float] = Field(None, description="UV index")
    timestamp: Optional[str] = Field(None, description="ISO timestamp")


class ForecastDayResponse(BaseModel):
    """Daily forecast entry."""

    date: Optional[str] = Field(None, description="Date in YYYY-MM-DD format")
    temperature_max: Optional[float] = Field(None, description="Maximum temperature")
    temperature_min: Optional[float] = Field(None, description="Minimum temperature")
    rainfall_sum: Optional[float] = Field(None, description="Total rainfall for the day")
    wind_speed_max: Optional[float] = Field(None, description="Maximum wind speed")
    condition: Optional[str] = Field(None, description="Weather condition")


class ForecastResponse(BaseModel):
    """Daily forecast data."""

    forecast_days: Optional[list[ForecastDayResponse]] = Field(None, description="List of daily forecasts")


class HourlyEntryResponse(BaseModel):
    """Hourly forecast entry."""

    time: Optional[str] = Field(None, description="ISO timestamp")
    temperature: Optional[float] = Field(None, description="Temperature")
    humidity: Optional[float] = Field(None, description="Humidity percentage")
    wind_speed: Optional[float] = Field(None, description="Wind speed")
    rainfall: Optional[float] = Field(None, description="Rainfall")
    condition: Optional[str] = Field(None, description="Weather condition")


class HourlyResponse(BaseModel):
    """Hourly forecast data."""

    hourly: Optional[list[HourlyEntryResponse]] = Field(None, description="List of hourly entries")


class WeatherResponse(BaseModel):
    """Complete weather data (current, daily, hourly, AI summary)."""

    current: Optional[CurrentWeatherResponse] = Field(None, description="Current conditions")
    daily: Optional[list[ForecastDayResponse]] = Field(None, description="Daily forecast")
    hourly: Optional[list[HourlyEntryResponse]] = Field(None, description="Hourly forecast")
    ai_summary: Optional[str] = Field(None, description="AI-generated weather summary")

    class Config:
        extra = "allow"


class UsageResponse(BaseModel):
    """API usage and quota information."""

    plan: str = Field(..., description="Current plan (Free, Pro, Scale)")
    requests_used: int = Field(..., description="Requests used this month")
    requests_remaining: int = Field(..., description="Requests remaining")
    requests_limit: int = Field(..., description="Monthly request limit")
    ai_requests_used: int = Field(..., description="AI requests used")
    ai_requests_remaining: int = Field(..., description="AI requests remaining")
    period_start: str = Field(..., description="Billing period start (ISO timestamp)")
    period_end: str = Field(..., description="Billing period end (ISO timestamp)")

    class Config:
        extra = "allow"
