"""Authentication request and response schemas."""

import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """User registration request schema."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User password (minimum 8 characters)",
    )

    model_config = {"json_schema_extra": {"example": {
        "email": "user@example.com",
        "password": "SecurePassword123!",
    }}}


class LoginRequest(BaseModel):
    """User login request schema."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

    model_config = {"json_schema_extra": {"example": {
        "email": "user@example.com",
        "password": "SecurePassword123!",
    }}}


class TokenResponse(BaseModel):
    """Token response schema."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration in seconds")

    model_config = {"json_schema_extra": {"example": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 900,
    }}}


class UserResponse(BaseModel):
    """User response schema."""

    id: uuid.UUID = Field(..., description="User ID")
    email: str = Field(..., description="User email address")
    is_active: bool = Field(..., description="Whether user is active")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {"example": {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "user@example.com",
            "is_active": True,
            "created_at": "2024-06-05T10:30:00Z",
            "updated_at": "2024-06-05T10:30:00Z",
        }}
    }


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""

    refresh_token: str = Field(..., description="Refresh token")

    model_config = {"json_schema_extra": {"example": {
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    }}}
