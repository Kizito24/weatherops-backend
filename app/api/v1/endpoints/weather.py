"""Weather API endpoints."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.weather import CurrentWeatherResponse, ForecastResponse, HourlyResponse, UsageResponse, WeatherResponse
from app.services.weather_service import WeatherService, WeatherServiceError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "",
    response_model=WeatherResponse,
    summary="Get full weather data",
    description="Get current conditions, daily forecast, hourly breakdown, and AI summary.",
)
async def get_weather(
    lat: Annotated[float, Query(..., ge=-90, le=90, description="Latitude")],
    lon: Annotated[float, Query(..., ge=-180, le=180, description="Longitude")],
    days: Annotated[int, Query(ge=1, le=7, description="Forecast days (1-7)")] = 7,
    ai: Annotated[bool, Query(description="Include AI summary")] = True,
    units: Annotated[str, Query(regex="^(metric|imperial)$")] = "metric",
    lang: Annotated[str, Query(description="Language code")] = "en",
    current_user: User = Depends(get_current_user),
) -> WeatherResponse:
    """
    Get complete weather data for coordinates.

    Includes current conditions, daily forecast (up to 7 days), hourly breakdown,
    and AI-generated summary (if enabled). Results are cached for 1 hour.
    """
    try:
        service = WeatherService()
        data = await service.get_weather(lat, lon, days, ai, units, lang)
        return WeatherResponse(**data)
    except WeatherServiceError as e:
        logger.error(f"Weather service error: {e}")
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in weather endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/current",
    response_model=CurrentWeatherResponse,
    summary="Get current weather",
    description="Get current weather conditions only.",
)
async def get_current(
    lat: Annotated[float, Query(..., ge=-90, le=90, description="Latitude")],
    lon: Annotated[float, Query(..., ge=-180, le=180, description="Longitude")],
    ai: Annotated[bool, Query(description="Include AI summary")] = False,
    units: Annotated[str, Query(regex="^(metric|imperial)$")] = "metric",
    current_user: User = Depends(get_current_user),
) -> CurrentWeatherResponse:
    """
    Get current weather conditions for coordinates.

    Results are cached for 10 minutes.
    """
    try:
        service = WeatherService()
        data = await service.get_current_weather(lat, lon, ai, units)
        return CurrentWeatherResponse(**data)
    except WeatherServiceError as e:
        logger.error(f"Weather service error: {e}")
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in current weather endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/forecast",
    response_model=ForecastResponse,
    summary="Get daily forecast",
    description="Get day-by-day forecast.",
)
async def get_forecast(
    lat: Annotated[float, Query(..., ge=-90, le=90, description="Latitude")],
    lon: Annotated[float, Query(..., ge=-180, le=180, description="Longitude")],
    days: Annotated[int, Query(ge=1, le=7, description="Forecast days (1-7)")] = 7,
    ai: Annotated[bool, Query(description="Include AI summary")] = False,
    units: Annotated[str, Query(regex="^(metric|imperial)$")] = "metric",
    current_user: User = Depends(get_current_user),
) -> ForecastResponse:
    """
    Get daily forecast for coordinates.

    Results are cached for 1 hour.
    """
    try:
        service = WeatherService()
        data = await service.get_forecast(lat, lon, days, ai, units)
        return ForecastResponse(**data)
    except WeatherServiceError as e:
        logger.error(f"Weather service error: {e}")
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in forecast endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/hourly",
    response_model=HourlyResponse,
    summary="Get hourly forecast",
    description="Get hour-by-hour forecast.",
)
async def get_hourly(
    lat: Annotated[float, Query(..., ge=-90, le=90, description="Latitude")],
    lon: Annotated[float, Query(..., ge=-180, le=180, description="Longitude")],
    days: Annotated[int, Query(ge=1, le=7, description="Forecast days (1-7)")] = 1,
    ai: Annotated[bool, Query(description="Include AI summary")] = False,
    units: Annotated[str, Query(regex="^(metric|imperial)$")] = "metric",
    current_user: User = Depends(get_current_user),
) -> HourlyResponse:
    """
    Get hourly forecast for coordinates.

    Results are cached for 30 minutes.
    """
    try:
        service = WeatherService()
        data = await service.get_hourly(lat, lon, days, ai, units)
        return HourlyResponse(**data)
    except WeatherServiceError as e:
        logger.error(f"Weather service error: {e}")
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in hourly endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/usage",
    response_model=UsageResponse,
    summary="Get WeatherAI usage",
    description="Get monthly usage and quota information.",
)
async def get_usage(
    current_user: User = Depends(get_current_user),
) -> UsageResponse:
    """
    Get WeatherAI usage and quota for current plan.

    Results are cached for 5 minutes.
    """
    try:
        service = WeatherService()
        data = await service.get_usage()
        return UsageResponse(**data)
    except WeatherServiceError as e:
        logger.error(f"Weather service error: {e}")
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in usage endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
