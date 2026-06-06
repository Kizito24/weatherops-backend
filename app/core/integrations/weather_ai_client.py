"""WeatherAI API client for weather data integration.

Integrates with https://api.weather-ai.co/v1 endpoints.
"""

import io
import logging
from typing import Any, Optional

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class WeatherAIError(Exception):
    """Base exception for WeatherAI API errors."""

    pass


class WeatherAIClient:
    """Async client for WeatherAI API integration.

    Uses WeatherAI v1 endpoints:
    - GET /v1/weather - Full weather with current, daily, hourly, and AI summary
    - GET /v1/weather/current - Current weather only
    - GET /v1/weather/forecast - Daily forecast only
    - GET /v1/weather/hourly - Hourly breakdown
    - GET /v1/usage - Monthly usage and quota
    - POST /v1/trees/analyze - Analyze farm images for tree counts
    - GET /v1/trees/analyses - List past analyses
    - GET /v1/trees/usage - Tree analysis quota
    """

    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        """
        Initialize WeatherAI client.

        Args:
            base_url: Base URL for WeatherAI API (defaults to https://api.weather-ai.co)
            api_key: API key for authentication.
        """
        settings = get_settings()
        self.base_url = (base_url or settings.WEATHERAI_BASE_URL or "https://api.weather-ai.co").rstrip("/")
        self.api_key = api_key or settings.WEATHERAI_API_KEY
        self.client: httpx.AsyncClient | None = None
        self.timeout = 30.0

    async def __aenter__(self):
        """Async context manager entry."""
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
            },
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """
        Make HTTP request to WeatherAI API.

        Args:
            method: HTTP method (GET, POST, etc.).
            endpoint: API endpoint path (with leading /).
            **kwargs: Additional request parameters (params, json, files, data, etc.).

        Returns:
            JSON response from API.

        Raises:
            WeatherAIError: If request fails or API returns error.
        """
        if not self.client:
            self.client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                },
            )

        url = f"{self.base_url}{endpoint}"
        try:
            logger.debug(f"WeatherAI API request: {method} {endpoint}")
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_msg = f"WeatherAI API error {e.response.status_code}: {e.response.text}"
            logger.error(error_msg)
            raise WeatherAIError(error_msg) from e
        except httpx.HTTPError as e:
            logger.error(f"WeatherAI API error: {e}")
            raise WeatherAIError(f"WeatherAI API error: {e}") from e

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
        Get full weather data (current, daily, hourly, and AI summary).

        Endpoint: GET /v1/weather
        Documentation: https://api.weather-ai.co/docs#/weather/get_weather

        Args:
            latitude: Latitude coordinate (-90 to 90).
            longitude: Longitude coordinate (-180 to 180).
            days: Number of forecast days (1-7 Free, 1-14 Pro, 1-16 Scale). Default 7.
            ai: Include AI summary. Default True.
            units: "metric" (°C) or "imperial" (°F). Default "metric".
            lang: Language code (en, sw, etc.). Default "en".

        Returns:
            Complete weather data including current, daily, hourly, and AI summary.

        Raises:
            WeatherAIError: If request fails.
        """
        logger.info(f"Fetching full weather for ({latitude}, {longitude}) - {days} days")
        response = await self._request(
            "GET",
            "/v1/weather",
            params={
                "lat": latitude,
                "lon": longitude,
                "days": max(1, min(days, 7)),
                "ai": str(ai).lower(),
                "units": units,
                "lang": lang,
            },
        )
        return response

    async def get_current(
        self,
        latitude: float,
        longitude: float,
        ai: bool = False,
        units: str = "metric",
    ) -> dict[str, Any]:
        """
        Get current weather conditions only.

        Endpoint: GET /v1/weather/current
        Documentation: https://api.weather-ai.co/docs#/weather/get_current

        Args:
            latitude: Latitude coordinate (-90 to 90).
            longitude: Longitude coordinate (-180 to 180).
            ai: Include AI summary. Default False.
            units: "metric" or "imperial". Default "metric".

        Returns:
            Current weather data.

        Raises:
            WeatherAIError: If request fails.
        """
        logger.info(f"Fetching current weather for ({latitude}, {longitude})")
        response = await self._request(
            "GET",
            "/v1/weather/current",
            params={
                "lat": latitude,
                "lon": longitude,
                "ai": str(ai).lower(),
                "units": units,
            },
        )
        return response

    async def get_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int = 7,
        ai: bool = False,
        units: str = "metric",
    ) -> dict[str, Any]:
        """
        Get daily forecast.

        Endpoint: GET /v1/weather/forecast
        Documentation: https://api.weather-ai.co/docs#/weather/get_forecast

        Args:
            latitude: Latitude coordinate (-90 to 90).
            longitude: Longitude coordinate (-180 to 180).
            days: Number of forecast days (1-7 Free). Default 7.
            ai: Include AI summary. Default False.
            units: "metric" or "imperial". Default "metric".

        Returns:
            Daily forecast data.

        Raises:
            WeatherAIError: If request fails.
        """
        logger.info(f"Fetching forecast for ({latitude}, {longitude}) - {days} days")
        response = await self._request(
            "GET",
            "/v1/weather/forecast",
            params={
                "lat": latitude,
                "lon": longitude,
                "days": max(1, min(days, 7)),
                "ai": str(ai).lower(),
                "units": units,
            },
        )
        return response

    async def get_hourly(
        self,
        latitude: float,
        longitude: float,
        days: int = 1,
        ai: bool = False,
        units: str = "metric",
    ) -> dict[str, Any]:
        """
        Get hourly forecast.

        Endpoint: GET /v1/weather/hourly
        Documentation: https://api.weather-ai.co/docs#/weather/get_hourly

        Args:
            latitude: Latitude coordinate (-90 to 90).
            longitude: Longitude coordinate (-180 to 180).
            days: Number of days (1-7 Free). Default 1.
            ai: Include AI summary. Default False.
            units: "metric" or "imperial". Default "metric".

        Returns:
            Hourly forecast data.

        Raises:
            WeatherAIError: If request fails.
        """
        logger.info(f"Fetching hourly forecast for ({latitude}, {longitude}) - {days} days")
        response = await self._request(
            "GET",
            "/v1/weather/hourly",
            params={
                "lat": latitude,
                "lon": longitude,
                "days": max(1, min(days, 7)),
                "ai": str(ai).lower(),
                "units": units,
            },
        )
        return response

    async def get_usage(self) -> dict[str, Any]:
        """
        Get WeatherAI usage and quota info.

        Endpoint: GET /v1/usage

        Returns:
            Usage stats including requests used/remaining and plan info.

        Raises:
            WeatherAIError: If request fails.
        """
        logger.info("Fetching WeatherAI usage")
        response = await self._request("GET", "/v1/usage")
        return response

    async def analyze_trees(
        self,
        image_bytes: bytes,
        filename: str,
        content_type: str,
        farmer_id: Optional[str] = None,
        county: Optional[str] = None,
        land_acres: Optional[float] = None,
        location: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Analyze a farm image for tree count and canopy health.

        Endpoint: POST /v1/trees/analyze
        Documentation: https://api.weather-ai.co/docs#/agroforestry/analyze_trees

        Args:
            image_bytes: Binary image data (JPEG, PNG, WEBP, max 20MB).
            filename: Original filename for context.
            content_type: MIME type (image/jpeg, image/png, image/webp).
            farmer_id: Optional farmer identifier.
            county: Optional county/region name.
            land_acres: Optional plot size in acres.
            location: Optional farm name or GPS description.
            notes: Optional context for analysis (e.g., "Tea plantation").

        Returns:
            Analysis result with tree count, health breakdown, overlay image URL, recommendations.

        Raises:
            WeatherAIError: If request fails.
        """
        logger.info(f"Analyzing farm image: {filename}")

        files = {
            "image": (filename, io.BytesIO(image_bytes), content_type),
        }
        data = {}
        if farmer_id:
            data["farmerId"] = farmer_id
        if county:
            data["county"] = county
        if land_acres:
            data["landAcres"] = land_acres
        if location:
            data["location"] = location
        if notes:
            data["notes"] = notes

        response = await self._request(
            "POST",
            "/v1/trees/analyze",
            files=files,
            data=data,
        )
        return response

    async def list_tree_analyses(
        self,
        limit: int = 20,
        cursor: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        List past tree analyses.

        Endpoint: GET /v1/trees/analyses
        Documentation: https://api.weather-ai.co/docs#/agroforestry/list_analyses

        Args:
            limit: Results per page (max 100). Default 20.
            cursor: Pagination cursor from previous response.

        Returns:
            Paginated list of analyses with metadata.

        Raises:
            WeatherAIError: If request fails.
        """
        logger.info("Fetching tree analyses list")
        params = {"limit": min(limit, 100)}
        if cursor:
            params["cursor"] = cursor

        response = await self._request("GET", "/v1/trees/analyses", params=params)
        return response

    async def get_tree_usage(self) -> dict[str, Any]:
        """
        Get tree analysis usage and quota.

        Endpoint: GET /v1/trees/usage
        Documentation: https://api.weather-ai.co/docs#/agroforestry/get_usage

        Returns:
            Usage stats: plan, used, limit, remaining, unlimited, resets_at.

        Raises:
            WeatherAIError: If request fails.
        """
        logger.info("Fetching tree analysis usage")
        response = await self._request("GET", "/v1/trees/usage")
        return response

