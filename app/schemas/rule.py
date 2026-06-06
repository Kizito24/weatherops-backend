"""Rule request and response schemas."""

import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class RuleCreate(BaseModel):
    """Create rule request schema."""

    location_id: uuid.UUID = Field(..., description="Location ID")
    metric: str = Field(
        ...,
        pattern="^(temperature|rainfall|wind_speed|humidity)$",
        description="Weather metric to monitor",
    )
    operator: str = Field(
        ...,
        pattern="^(>|<|>=|<=|==)$",
        description="Comparison operator",
    )
    threshold: float = Field(..., description="Threshold value for the metric")

    model_config = {"json_schema_extra": {"example": {
        "location_id": "550e8400-e29b-41d4-a716-446655440000",
        "metric": "temperature",
        "operator": ">",
        "threshold": 35.0,
    }}}


class RuleUpdate(BaseModel):
    """Update rule request schema."""

    metric: str | None = Field(
        None,
        pattern="^(temperature|rainfall|wind_speed|humidity)$",
        description="Weather metric to monitor",
    )
    operator: str | None = Field(
        None,
        pattern="^(>|<|>=|<=|==)$",
        description="Comparison operator",
    )
    threshold: float | None = Field(None, description="Threshold value for the metric")
    is_active: bool | None = Field(None, description="Whether rule is active")

    model_config = {"json_schema_extra": {"example": {
        "metric": "temperature",
        "operator": ">=",
        "threshold": 38.0,
        "is_active": True,
    }}}


class RuleResponse(BaseModel):
    """Rule response schema."""

    id: uuid.UUID = Field(..., description="Rule ID")
    location_id: uuid.UUID = Field(..., description="Location ID")
    metric: str = Field(..., description="Weather metric")
    operator: str = Field(..., description="Comparison operator")
    threshold: float = Field(..., description="Threshold value")
    is_active: bool = Field(..., description="Whether rule is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {"example": {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "location_id": "660e8400-e29b-41d4-a716-446655440000",
            "metric": "temperature",
            "operator": ">",
            "threshold": 35.0,
            "is_active": True,
            "created_at": "2024-06-05T10:30:00Z",
            "updated_at": "2024-06-05T10:30:00Z",
        }}
    }
