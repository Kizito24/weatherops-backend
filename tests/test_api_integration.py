"""API integration tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_location_flow(client: AsyncClient):
    """Test complete location workflow."""
    # Register
    register_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "location@test.com", "password": "SecurePassword123!"},
    )
    assert register_response.status_code == 201

    # Login
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "location@test.com", "password": "SecurePassword123!"},
    )
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}

    # Create location
    create_response = await client.post(
        "/api/v1/locations",
        headers=headers,
        json={
            "name": "Test Office",
            "latitude": 6.5244,
            "longitude": 3.3792,
        },
    )
    assert create_response.status_code == 201
    location_id = create_response.json()["id"]

    # Get location
    get_response = await client.get(
        f"/api/v1/locations/{location_id}",
        headers=headers,
    )
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Test Office"

    # List locations
    list_response = await client.get(
        "/api/v1/locations",
        headers=headers,
    )
    assert list_response.status_code == 200
    assert len(list_response.json()) >= 1

    # Update location
    update_response = await client.put(
        f"/api/v1/locations/{location_id}",
        headers=headers,
        json={"name": "Updated Office"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Updated Office"

    # Delete location
    delete_response = await client.delete(
        f"/api/v1/locations/{location_id}",
        headers=headers,
    )
    assert delete_response.status_code == 204

    # Verify deleted
    get_deleted = await client.get(
        f"/api/v1/locations/{location_id}",
        headers=headers,
    )
    assert get_deleted.status_code == 404


@pytest.mark.asyncio
async def test_rule_flow(client: AsyncClient):
    """Test complete rule workflow."""
    # Register and login
    await client.post(
        "/api/v1/auth/register",
        json={"email": "rule@test.com", "password": "SecurePassword123!"},
    )
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "rule@test.com", "password": "SecurePassword123!"},
    )
    access_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Create location first
    loc_response = await client.post(
        "/api/v1/locations",
        headers=headers,
        json={
            "name": "Test Location",
            "latitude": 6.5244,
            "longitude": 3.3792,
        },
    )
    location_id = loc_response.json()["id"]

    # Create rule
    create_response = await client.post(
        "/api/v1/rules",
        headers=headers,
        json={
            "location_id": location_id,
            "metric": "temperature",
            "operator": ">",
            "threshold": 35.0,
        },
    )
    assert create_response.status_code == 201
    rule_id = create_response.json()["id"]

    # Get rule
    get_response = await client.get(
        f"/api/v1/rules/{rule_id}",
        headers=headers,
    )
    assert get_response.status_code == 200
    assert get_response.json()["metric"] == "temperature"

    # Get location rules
    list_response = await client.get(
        f"/api/v1/rules/location/{location_id}",
        headers=headers,
    )
    assert list_response.status_code == 200
    assert len(list_response.json()) >= 1

    # Update rule
    update_response = await client.put(
        f"/api/v1/rules/{rule_id}",
        headers=headers,
        json={"threshold": 40.0},
    )
    assert update_response.status_code == 200
    assert update_response.json()["threshold"] == 40.0

    # Delete rule
    delete_response = await client.delete(
        f"/api/v1/rules/{rule_id}",
        headers=headers,
    )
    assert delete_response.status_code == 204


@pytest.mark.asyncio
async def test_rule_validation(client: AsyncClient):
    """Test rule validation."""
    # Setup
    await client.post(
        "/api/v1/auth/register",
        json={"email": "validate@test.com", "password": "SecurePassword123!"},
    )
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "validate@test.com", "password": "SecurePassword123!"},
    )
    access_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Create location
    loc_response = await client.post(
        "/api/v1/locations",
        headers=headers,
        json={
            "name": "Test",
            "latitude": 6.5244,
            "longitude": 3.3792,
        },
    )
    location_id = loc_response.json()["id"]

    # Test invalid metric
    invalid_metric_response = await client.post(
        "/api/v1/rules",
        headers=headers,
        json={
            "location_id": location_id,
            "metric": "invalid_metric",
            "operator": ">",
            "threshold": 35.0,
        },
    )
    assert invalid_metric_response.status_code == 400
    assert "Invalid metric" in invalid_metric_response.json()["detail"]

    # Test invalid operator
    invalid_operator_response = await client.post(
        "/api/v1/rules",
        headers=headers,
        json={
            "location_id": location_id,
            "metric": "temperature",
            "operator": ">>",
            "threshold": 35.0,
        },
    )
    assert invalid_operator_response.status_code == 400
    assert "Invalid operator" in invalid_operator_response.json()["detail"]


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    """Test that users can't access other users' data."""
    # User 1 creates location
    user1 = "user1@test.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": user1, "password": "SecurePassword123!"},
    )
    login1 = await client.post(
        "/api/v1/auth/login",
        json={"email": user1, "password": "SecurePassword123!"},
    )
    token1 = login1.json()["access_token"]
    headers1 = {"Authorization": f"Bearer {token1}"}

    loc_response = await client.post(
        "/api/v1/locations",
        headers=headers1,
        json={
            "name": "User1 Location",
            "latitude": 6.5244,
            "longitude": 3.3792,
        },
    )
    location_id = loc_response.json()["id"]

    # User 2 tries to access it
    user2 = "user2@test.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": user2, "password": "SecurePassword123!"},
    )
    login2 = await client.post(
        "/api/v1/auth/login",
        json={"email": user2, "password": "SecurePassword123!"},
    )
    token2 = login2.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    # Should be forbidden
    access_response = await client.get(
        f"/api/v1/locations/{location_id}",
        headers=headers2,
    )
    assert access_response.status_code == 403


@pytest.mark.asyncio
async def test_missing_location_returns_404(client: AsyncClient):
    """Test that missing locations return 404."""
    # Setup
    await client.post(
        "/api/v1/auth/register",
        json={"email": "notfound@test.com", "password": "SecurePassword123!"},
    )
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "notfound@test.com", "password": "SecurePassword123!"},
    )
    access_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Try to get non-existent location
    response = await client.get(
        "/api/v1/locations/00000000-0000-0000-0000-000000000000",
        headers=headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_missing_rule_returns_404(client: AsyncClient):
    """Test that missing rules return 404."""
    # Setup
    await client.post(
        "/api/v1/auth/register",
        json={"email": "rulenot@test.com", "password": "SecurePassword123!"},
    )
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "rulenot@test.com", "password": "SecurePassword123!"},
    )
    access_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Try to get non-existent rule
    response = await client.get(
        "/api/v1/rules/00000000-0000-0000-0000-000000000000",
        headers=headers,
    )
    assert response.status_code == 404
