"""Weather service for data fetching and caching."""

import logging
from typing import Any, Optional

from app.core.cache.cache_service import CacheService
from app.core.integrations.weather_ai_client import WeatherAIClient, WeatherAIError

logger = logging.getLogger(__name__)


class WeatherServiceError(Exception):
    """Raised when weather service operation fails."""

    pass


class WeatherService:
    """Service for weather data operations."""

    CURRENT_WEATHER_TTL = 10 * 60
    FORECAST_TTL = 60 * 60
    HOURLY_TTL = 30 * 60
    USAGE_TTL = 5 * 60

    def __init__(self):
        """Initialize service."""
        self.cache = CacheService()
        self.weather_client = WeatherAIClient()

    async def get_weather(
        self,
        latitude: float,
        longitude: float,
        days: int = 7,
        ai: bool = True,
        units: str = "metric",
        lang: str = "en",
    ) -> dict[str, Any]:
        """
        Get full weather data (current, daily, hourly, AI summary) with caching.

        Args:
            latitude: Latitude coordinate.
            longitude: Longitude coordinate.
            days: Number of forecast days (1-7 Free tier). Default 7.
            ai: Include AI summary. Default True.
            units: "metric" or "imperial". Default "metric".
            lang: Language code. Default "en".

        Returns:
            Complete weather data.

        Raises:
            WeatherServiceError: If fetch fails.
        """
        cache_key = CacheService.make_weather_key(latitude, longitude, f"weather_{days}d_ai{ai}")

        cached = await self.cache.get(cache_key)
        if cached:
            logger.debug(f"Weather cache hit: {cache_key}")
            return cached

        try:
            async with self.weather_client as client:
                data = await client.get_weather(latitude, longitude, days, ai, units, lang)
            await self.cache.set(cache_key, data, self.FORECAST_TTL)
            logger.info(f"Full weather fetched and cached: ({latitude}, {longitude})")
            return data
        except WeatherAIError as e:
            logger.error(f"Failed to fetch weather: {e}")
            raise WeatherServiceError(f"Failed to fetch weather: {e}") from e

    async def get_current_weather(
        self,
        latitude: float,
        longitude: float,
        ai: bool = False,
        units: str = "metric",
    ) -> dict[str, Any]:
        """
        Get current weather conditions with caching.

        Args:
            latitude: Latitude coordinate.
            longitude: Longitude coordinate.
            ai: Include AI summary. Default False.
            units: "metric" or "imperial". Default "metric".

        Returns:
            Current weather data.

        Raises:
            WeatherServiceError: If fetch fails.
        """
        cache_key = CacheService.make_weather_key(latitude, longitude, "current")

        cached = await self.cache.get(cache_key)
        if cached:
            logger.debug(f"Current weather cache hit: {cache_key}")
            return cached

        try:
            async with self.weather_client as client:
                data = await client.get_current(latitude, longitude, ai, units)
            await self.cache.set(cache_key, data, self.CURRENT_WEATHER_TTL)
            logger.info(f"Current weather fetched: ({latitude}, {longitude})")
            return data
        except WeatherAIError as e:
            logger.error(f"Failed to fetch current weather: {e}")
            raise WeatherServiceError(f"Failed to fetch weather: {e}") from e

    async def get_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int = 7,
        ai: bool = False,
        units: str = "metric",
    ) -> dict[str, Any]:
        """
        Get daily forecast with caching.

        Args:
            latitude: Latitude coordinate.
            longitude: Longitude coordinate.
            days: Number of forecast days (1-7 Free tier). Default 7.
            ai: Include AI summary. Default False.
            units: "metric" or "imperial". Default "metric".

        Returns:
            Daily forecast data.

        Raises:
            WeatherServiceError: If fetch fails.
        """
        cache_key = CacheService.make_weather_key(latitude, longitude, f"forecast_{days}d")

        cached = await self.cache.get(cache_key)
        if cached:
            logger.debug(f"Forecast cache hit: {cache_key}")
            return cached

        try:
            async with self.weather_client as client:
                data = await client.get_forecast(latitude, longitude, days, ai, units)
            await self.cache.set(cache_key, data, self.FORECAST_TTL)
            logger.info(f"Forecast fetched: ({latitude}, {longitude}) - {days} days")
            return data
        except WeatherAIError as e:
            logger.error(f"Failed to fetch forecast: {e}")
            raise WeatherServiceError(f"Failed to fetch forecast: {e}") from e

    async def get_hourly(
        self,
        latitude: float,
        longitude: float,
        days: int = 1,
        ai: bool = False,
        units: str = "metric",
    ) -> dict[str, Any]:
        """
        Get hourly forecast with caching.

        Args:
            latitude: Latitude coordinate.
            longitude: Longitude coordinate.
            days: Number of days (1-7 Free tier). Default 1.
            ai: Include AI summary. Default False.
            units: "metric" or "imperial". Default "metric".

        Returns:
            Hourly forecast data.

        Raises:
            WeatherServiceError: If fetch fails.
        """
        cache_key = CacheService.make_weather_key(latitude, longitude, f"hourly_{days}d")

        cached = await self.cache.get(cache_key)
        if cached:
            logger.debug(f"Hourly cache hit: {cache_key}")
            return cached

        try:
            async with self.weather_client as client:
                data = await client.get_hourly(latitude, longitude, days, ai, units)
            await self.cache.set(cache_key, data, self.HOURLY_TTL)
            logger.info(f"Hourly forecast fetched: ({latitude}, {longitude}) - {days} days")
            return data
        except WeatherAIError as e:
            logger.error(f"Failed to fetch hourly: {e}")
            raise WeatherServiceError(f"Failed to fetch hourly: {e}") from e

    async def get_usage(self) -> dict[str, Any]:
        """
        Get WeatherAI usage and quota with caching.

        Returns:
            Usage stats.

        Raises:
            WeatherServiceError: If fetch fails.
        """
        cache_key = "weather:usage"

        cached = await self.cache.get(cache_key)
        if cached:
            logger.debug(f"Usage cache hit: {cache_key}")
            return cached

        try:
            async with self.weather_client as client:
                data = await client.get_usage()
            await self.cache.set(cache_key, data, self.USAGE_TTL)
            logger.info("Usage fetched")
            return data
        except WeatherAIError as e:
            logger.error(f"Failed to fetch usage: {e}")
            raise WeatherServiceError(f"Failed to fetch usage: {e}") from e

    def evaluate_rule(
        self,
        metric: str,
        operator: str,
        threshold: float,
        weather_data: dict[str, Any],
    ) -> bool:
        """
        Evaluate if weather data matches a rule condition.

        Args:
            metric: Metric name (temperature, rainfall, wind_speed, humidity).
            operator: Comparison operator (>, <, >=, <=, ==).
            threshold: Threshold value.
            weather_data: Weather data dict to check.

        Returns:
            True if rule condition is met, False otherwise.
        """
        current_value = weather_data.get(metric)

        if current_value is None:
            logger.warning(f"Metric '{metric}' not found in weather data")
            return False

        try:
            if operator == ">":
                return current_value > threshold
            elif operator == "<":
                return current_value < threshold
            elif operator == ">=":
                return current_value >= threshold
            elif operator == "<=":
                return current_value <= threshold
            elif operator == "==":
                return current_value == threshold
            else:
                logger.warning(f"Unknown operator: {operator}")
                return False
        except Exception as e:
            logger.error(f"Error evaluating rule: {e}")
            return False
