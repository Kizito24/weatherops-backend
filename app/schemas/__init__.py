"""Pydantic schemas for API request/response validation."""

from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserResponse,
)
from app.schemas.location import (
    LocationCreate,
    LocationUpdate,
    LocationResponse,
)
from app.schemas.rule import (
    RuleCreate,
    RuleUpdate,
    RuleResponse,
)
from app.schemas.alert import (
    AlertCreate,
    AlertResponse,
)

__all__ = [
    "RegisterRequest",
    "LoginRequest",
    "RefreshTokenRequest",
    "TokenResponse",
    "UserResponse",
    "LocationCreate",
    "LocationUpdate",
    "LocationResponse",
    "RuleCreate",
    "RuleUpdate",
    "RuleResponse",
    "AlertCreate",
    "AlertResponse",
]
