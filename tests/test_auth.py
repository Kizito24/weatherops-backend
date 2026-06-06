"""Authentication system tests."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.schemas.auth import UserResponse


@pytest.mark.asyncio
async def test_user_registration(client: AsyncClient):
    """Test user registration endpoint."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "testuser@example.com",
            "password": "SecurePassword123!",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "testuser@example.com"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_user_registration_duplicate_email(client: AsyncClient):
    """Test registration fails with duplicate email."""
    email = "duplicate@example.com"

    # First registration
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SecurePassword123!"},
    )

    # Second registration with same email
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SecurePassword123!"},
    )

    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_user_login(client: AsyncClient):
    """Test user login endpoint."""
    # Register user first
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "logintest@example.com",
            "password": "SecurePassword123!",
        },
    )
    assert register_response.status_code == 201

    # Login
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "logintest@example.com",
            "password": "SecurePassword123!",
        },
    )

    assert login_response.status_code == 200
    data = login_response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    """Test login fails with invalid password."""
    # Register user
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrongpass@example.com",
            "password": "SecurePassword123!",
        },
    )

    # Try login with wrong password
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "wrongpass@example.com",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient):
    """Test get current user endpoint."""
    # Register and login
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "getme@example.com",
            "password": "SecurePassword123!",
        },
    )

    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "getme@example.com",
            "password": "SecurePassword123!",
        },
    )

    access_token = login_response.json()["access_token"]

    # Get current user
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "getme@example.com"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(client: AsyncClient):
    """Test get current user with invalid token."""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token"},
    )

    assert response.status_code == 401
    assert "Invalid or expired" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_current_user_no_token(client: AsyncClient):
    """Test get current user without token."""
    response = await client.get("/api/v1/auth/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient):
    """Test token refresh endpoint."""
    # Register and login
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "refresh@example.com",
            "password": "SecurePassword123!",
        },
    )

    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "refresh@example.com",
            "password": "SecurePassword123!",
        },
    )

    refresh_token = login_response.json()["refresh_token"]

    # Refresh token
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["access_token"] != login_response.json()["access_token"]


@pytest.mark.asyncio
async def test_logout(client: AsyncClient):
    """Test logout endpoint."""
    # Register and login
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "logout@example.com",
            "password": "SecurePassword123!",
        },
    )

    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "logout@example.com",
            "password": "SecurePassword123!",
        },
    )

    access_token = login_response.json()["access_token"]

    # Logout
    response = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 204

    # Try to use old refresh token
    refresh_token = login_response.json()["refresh_token"]
    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert refresh_response.status_code == 401
