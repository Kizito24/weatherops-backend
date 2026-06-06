"""Alert request and response schemas."""

import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class AlertCreate(BaseModel):
    """Create alert request schema."""

    location_id: uuid.UUID
    rule_id: uuid.UUID
    metric: str
    actual_value: float
    threshold: float
    operator: str
    weather_snapshot: str | None = None


class AlertResponse(BaseModel):
    """Alert response schema."""

    id: uuid.UUID
    location_id: uuid.UUID
    rule_id: uuid.UUID
    user_id: uuid.UUID
    metric: str
    actual_value: float
    threshold: float
    operator: str
    severity: str = Field(description="Alert severity: LOW, MEDIUM, HIGH")
    status: str = Field(description="Alert status: active, resolved")
    weather_snapshot: str | None = None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None = None

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {"example": {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "location_id": "660e8400-e29b-41d4-a716-446655440000",
            "rule_id": "770e8400-e29b-41d4-a716-446655440000",
            "user_id": "880e8400-e29b-41d4-a716-446655440000",
            "metric": "temperature",
            "actual_value": 38.5,
            "threshold": 35.0,
            "operator": ">",
            "severity": "HIGH",
            "status": "active",
            "created_at": "2024-06-05T10:30:00Z",
            "updated_at": "2024-06-05T10:30:00Z",
            "resolved_at": None,
        }}
    }
