"""Tree analysis schemas."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class TreeHealthResponse(BaseModel):
    """Tree health breakdown."""

    healthy: int = Field(..., description="Number of healthy trees")
    needs_care: int = Field(..., description="Number of trees needing care")
    needs_replacement: int = Field(..., description="Number of trees needing replacement")


class TreeAnalysisResponse(BaseModel):
    """Tree analysis result from WeatherAI."""

    analysis_id: str = Field(..., description="Unique analysis identifier")
    timestamp: str = Field(..., description="Analysis timestamp")
    farmer_id: Optional[str] = Field(None, description="Farmer identifier")
    county: Optional[str] = Field(None, description="County or region")
    location: Optional[str] = Field(None, description="Farm name or GPS description")
    land_acres: Optional[float] = Field(None, description="Plot size in acres")
    total_tree_count: int = Field(..., description="Total number of trees detected")
    tree_density_per_acre: Optional[float] = Field(None, description="Trees per acre")
    confidence_score: float = Field(..., description="Confidence score (0-1)")
    canopy_coverage_pct: float = Field(..., description="Canopy coverage percentage")
    tree_health: TreeHealthResponse = Field(..., description="Health breakdown")
    low_confidence: bool = Field(..., description="Whether analysis confidence is low")
    tree_species_guess: Optional[str] = Field(None, description="Guessed tree species")
    observations: list[str] = Field(default_factory=list, description="Analysis observations")
    recommendations: list[str] = Field(default_factory=list, description="Agronomic recommendations")
    original_image_url: str = Field(..., description="URL to original uploaded image")
    overlay_image_url: str = Field(..., description="URL to overlay image with detected crowns")

    class Config:
        extra = "allow"


class TreeUsageResponse(BaseModel):
    """Tree analysis usage and quota."""

    plan: str = Field(..., description="Current plan (Free, Pro, Scale)")
    used: int = Field(..., description="Analyses used this month")
    limit: int = Field(..., description="Monthly analysis limit")
    remaining: int = Field(..., description="Analyses remaining")
    unlimited: bool = Field(False, description="Whether plan has unlimited analyses")
    resets_at: Optional[str] = Field(None, description="When quota resets (ISO timestamp)")

    class Config:
        extra = "allow"


class TreeAnalysesListResponse(BaseModel):
    """Paginated list of tree analyses."""

    analyses: list[Any] = Field(default_factory=list, description="List of analyses")
    cursor: Optional[str] = Field(None, description="Cursor for pagination")
    has_more: bool = Field(False, description="Whether more results exist")

    class Config:
        extra = "allow"
