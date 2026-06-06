"""Location request and response schemas."""

import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class LocationCreate(BaseModel):
    """Create location request schema."""

    name: str = Field(..., min_length=1, max_length=255, description="Location name")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")

    model_config = {"json_schema_extra": {"example": {
        "name": "Lagos Office",
        "latitude": 6.5244,
        "longitude": 3.3792,
    }}}


class LocationUpdate(BaseModel):
    """Update location request schema."""

    name: str | None = Field(None, min_length=1, max_length=255, description="Location name")
    latitude: float | None = Field(None, ge=-90, le=90, description="Latitude coordinate")
    longitude: float | None = Field(None, ge=-180, le=180, description="Longitude coordinate")

    model_config = {"json_schema_extra": {"example": {
        "name": "Lagos HQ",
        "latitude": 6.5244,
        "longitude": 3.3792,
    }}}


class LocationResponse(BaseModel):
    """Location response schema."""

    id: uuid.UUID = Field(..., description="Location ID")
    user_id: uuid.UUID = Field(..., description="User ID")
    name: str = Field(..., description="Location name")
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {"example": {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "user_id": "660e8400-e29b-41d4-a716-446655440000",
            "name": "Lagos Office",
            "latitude": 6.5244,
            "longitude": 3.3792,
            "created_at": "2024-06-05T10:30:00Z",
            "updated_at": "2024-06-05T10:30:00Z",
        }}
    }
