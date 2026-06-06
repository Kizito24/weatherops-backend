"""Service layer tests."""

import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.location import Location
from app.models.rule import Rule
from app.schemas.location import LocationCreate, LocationUpdate
from app.schemas.rule import RuleCreate, RuleUpdate
from app.services.location_service import (
    LocationService,
    LocationNotFoundError,
    LocationAccessError,
)
from app.services.rule_service import (
    RuleService,
    RuleValidationError,
    RuleNotFoundError,
    RuleAccessError,
)


# Test Locations
@pytest.mark.asyncio
async def test_create_location(test_db: AsyncSession):
    """Test location creation."""
    service = LocationService(test_db)
    user_id = uuid.uuid4()

    location_data = LocationCreate(
        name="Test Location",
        latitude=10.5,
        longitude=20.5,
    )

    location = await service.create_location(user_id, location_data)

    assert location.user_id == user_id
    assert location.name == "Test Location"
    assert location.latitude == 10.5
    assert location.longitude == 20.5


@pytest.mark.asyncio
async def test_get_user_locations(test_db: AsyncSession):
    """Test fetching user locations."""
    service = LocationService(test_db)
    user_id = uuid.uuid4()

    # Create multiple locations
    for i in range(3):
        await service.create_location(
            user_id,
            LocationCreate(name=f"Location {i}", latitude=10.0, longitude=20.0),
        )

    locations = await service.get_user_locations(user_id)
    assert len(locations) == 3


@pytest.mark.asyncio
async def test_update_location(test_db: AsyncSession):
    """Test location update."""
    service = LocationService(test_db)
    user_id = uuid.uuid4()

    location = await service.create_location(
        user_id,
        LocationCreate(name="Original", latitude=10.0, longitude=20.0),
    )

    updated = await service.update_location(
        user_id,
        location.id,
        LocationUpdate(name="Updated", latitude=15.0),
    )

    assert updated.name == "Updated"
    assert updated.latitude == 15.0
    assert updated.longitude == 20.0


@pytest.mark.asyncio
async def test_location_ownership_validation(test_db: AsyncSession):
    """Test that users can only access their own locations."""
    service = LocationService(test_db)
    user1_id = uuid.uuid4()
    user2_id = uuid.uuid4()

    location = await service.create_location(
        user1_id,
        LocationCreate(name="User1 Location", latitude=10.0, longitude=20.0),
    )

    # User2 should not access User1's location
    with pytest.raises(LocationAccessError):
        await service.get_location(user2_id, location.id)


@pytest.mark.asyncio
async def test_delete_location(test_db: AsyncSession):
    """Test location deletion."""
    service = LocationService(test_db)
    user_id = uuid.uuid4()

    location = await service.create_location(
        user_id,
        LocationCreate(name="Delete Me", latitude=10.0, longitude=20.0),
    )

    await service.delete_location(user_id, location.id)

    with pytest.raises(LocationNotFoundError):
        await service.get_location(user_id, location.id)


# Test Rules
@pytest.mark.asyncio
async def test_create_rule(test_db: AsyncSession):
    """Test rule creation."""
    service = RuleService(test_db)
    user_id = uuid.uuid4()

    location = await LocationService(test_db).create_location(
        user_id,
        LocationCreate(name="Test", latitude=10.0, longitude=20.0),
    )

    rule_data = RuleCreate(
        location_id=location.id,
        metric="temperature",
        operator=">",
        threshold=35.0,
    )

    rule = await service.create_rule(user_id, rule_data)

    assert rule.location_id == location.id
    assert rule.metric == "temperature"
    assert rule.operator == ">"
    assert rule.threshold == 35.0
    assert rule.is_active is True


@pytest.mark.asyncio
async def test_invalid_metric_validation(test_db: AsyncSession):
    """Test that invalid metrics are rejected."""
    service = RuleService(test_db)
    user_id = uuid.uuid4()

    location = await LocationService(test_db).create_location(
        user_id,
        LocationCreate(name="Test", latitude=10.0, longitude=20.0),
    )

    rule_data = RuleCreate(
        location_id=location.id,
        metric="invalid_metric",
        operator=">",
        threshold=35.0,
    )

    with pytest.raises(RuleValidationError):
        await service.create_rule(user_id, rule_data)


@pytest.mark.asyncio
async def test_invalid_operator_validation(test_db: AsyncSession):
    """Test that invalid operators are rejected."""
    service = RuleService(test_db)
    user_id = uuid.uuid4()

    location = await LocationService(test_db).create_location(
        user_id,
        LocationCreate(name="Test", latitude=10.0, longitude=20.0),
    )

    rule_data = RuleCreate(
        location_id=location.id,
        metric="temperature",
        operator=">>",
        threshold=35.0,
    )

    with pytest.raises(RuleValidationError):
        await service.create_rule(user_id, rule_data)


@pytest.mark.asyncio
async def test_get_location_rules(test_db: AsyncSession):
    """Test fetching rules for a location."""
    service = RuleService(test_db)
    user_id = uuid.uuid4()

    location = await LocationService(test_db).create_location(
        user_id,
        LocationCreate(name="Test", latitude=10.0, longitude=20.0),
    )

    # Create multiple rules
    for metric in ["temperature", "rainfall"]:
        await service.create_rule(
            user_id,
            RuleCreate(
                location_id=location.id,
                metric=metric,
                operator=">",
                threshold=30.0,
            ),
        )

    rules = await service.get_location_rules(user_id, location.id)
    assert len(rules) == 2


@pytest.mark.asyncio
async def test_update_rule(test_db: AsyncSession):
    """Test rule update."""
    service = RuleService(test_db)
    user_id = uuid.uuid4()

    location = await LocationService(test_db).create_location(
        user_id,
        LocationCreate(name="Test", latitude=10.0, longitude=20.0),
    )

    rule = await service.create_rule(
        user_id,
        RuleCreate(
            location_id=location.id,
            metric="temperature",
            operator=">",
            threshold=35.0,
        ),
    )

    updated = await service.update_rule(
        user_id,
        rule.id,
        RuleUpdate(threshold=40.0, is_active=False),
    )

    assert updated.threshold == 40.0
    assert updated.is_active is False
    assert updated.metric == "temperature"


@pytest.mark.asyncio
async def test_rule_ownership_validation(test_db: AsyncSession):
    """Test that users can only access their own rules."""
    user1_id = uuid.uuid4()
    user2_id = uuid.uuid4()

    loc_service = LocationService(test_db)
    rule_service = RuleService(test_db)

    location = await loc_service.create_location(
        user1_id,
        LocationCreate(name="Test", latitude=10.0, longitude=20.0),
    )

    rule = await rule_service.create_rule(
        user1_id,
        RuleCreate(
            location_id=location.id,
            metric="temperature",
            operator=">",
            threshold=35.0,
        ),
    )

    # User2 should not access User1's rule
    with pytest.raises(RuleAccessError):
        await rule_service.get_rule(user2_id, rule.id)


@pytest.mark.asyncio
async def test_delete_rule(test_db: AsyncSession):
    """Test rule deletion."""
    service = RuleService(test_db)
    user_id = uuid.uuid4()

    location = await LocationService(test_db).create_location(
        user_id,
        LocationCreate(name="Test", latitude=10.0, longitude=20.0),
    )

    rule = await service.create_rule(
        user_id,
        RuleCreate(
            location_id=location.id,
            metric="temperature",
            operator=">",
            threshold=35.0,
        ),
    )

    await service.delete_rule(user_id, rule.id)

    with pytest.raises(RuleNotFoundError):
        await service.get_rule(user_id, rule.id)
