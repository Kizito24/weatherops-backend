"""Tree and agroforestry analysis service."""

import logging
from typing import Any, Optional

from app.core.cache.cache_service import CacheService
from app.core.integrations.weather_ai_client import WeatherAIClient, WeatherAIError

logger = logging.getLogger(__name__)


class TreeServiceError(Exception):
    """Raised when tree service operation fails."""

    pass


class TreeService:
    """Service for tree analysis operations."""

    TREE_ANALYSIS_TTL = 5 * 60

    def __init__(self):
        """Initialize service."""
        self.cache = CacheService()
        self.weather_client = WeatherAIClient()

    async def analyze_image(
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

        Args:
            image_bytes: Binary image data (JPEG, PNG, WEBP, max 20MB).
            filename: Original filename.
            content_type: MIME type (image/jpeg, image/png, image/webp).
            farmer_id: Optional farmer identifier.
            county: Optional county/region.
            land_acres: Optional plot size in acres.
            location: Optional farm name or GPS description.
            notes: Optional context for analysis.

        Returns:
            Analysis result with tree count, health, recommendations, and overlay image URL.

        Raises:
            TreeServiceError: If analysis fails.
        """
        try:
            logger.info(f"Starting tree analysis: {filename}")
            async with self.weather_client as client:
                result = await client.analyze_trees(
                    image_bytes,
                    filename,
                    content_type,
                    farmer_id,
                    county,
                    land_acres,
                    location,
                    notes,
                )
            logger.info(f"Tree analysis completed: {filename}")
            return result
        except WeatherAIError as e:
            logger.error(f"Failed to analyze trees: {e}")
            raise TreeServiceError(f"Failed to analyze trees: {e}") from e

    async def list_analyses(
        self,
        limit: int = 20,
        cursor: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        List past tree analyses with caching.

        Args:
            limit: Results per page (max 100). Default 20.
            cursor: Pagination cursor from previous response.

        Returns:
            Paginated list of analyses.

        Raises:
            TreeServiceError: If fetch fails.
        """
        cache_key = f"trees:analyses:{limit}:{cursor or 'first'}"

        cached = await self.cache.get(cache_key)
        if cached:
            logger.debug(f"Tree analyses cache hit: {cache_key}")
            return cached

        try:
            async with self.weather_client as client:
                data = await client.list_tree_analyses(limit, cursor)
            await self.cache.set(cache_key, data, self.TREE_ANALYSIS_TTL)
            logger.info(f"Tree analyses list fetched: limit={limit}")
            return data
        except WeatherAIError as e:
            logger.error(f"Failed to list analyses: {e}")
            raise TreeServiceError(f"Failed to list analyses: {e}") from e

    async def get_usage(self) -> dict[str, Any]:
        """
        Get tree analysis usage and quota with caching.

        Returns:
            Usage stats: plan, used, limit, remaining, unlimited, resets_at.

        Raises:
            TreeServiceError: If fetch fails.
        """
        cache_key = "trees:usage"

        cached = await self.cache.get(cache_key)
        if cached:
            logger.debug(f"Tree usage cache hit: {cache_key}")
            return cached

        try:
            async with self.weather_client as client:
                data = await client.get_tree_usage()
            await self.cache.set(cache_key, data, self.TREE_ANALYSIS_TTL)
            logger.info("Tree usage fetched")
            return data
        except WeatherAIError as e:
            logger.error(f"Failed to fetch tree usage: {e}")
            raise TreeServiceError(f"Failed to fetch tree usage: {e}") from e
