"""User preferences API endpoints."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.session import get_db_session
from app.dependencies.auth import CurrentUser
from app.models.user_preference import UserPreference
from app.schemas.user_preference import UserPreferenceUpdate, UserPreferenceResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/preferences", tags=["preferences"])


@router.get("", response_model=UserPreferenceResponse)
async def get_preferences(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_session),
) -> UserPreferenceResponse:
    """
    Get user preferences.

    Returns default preferences if none exist yet.

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
        User preferences
    """
    try:
        query = select(UserPreference).where(UserPreference.user_id == current_user.id)
        result = await db.execute(query)
        prefs = result.scalars().first()

        if not prefs:
            # Create default preferences
            prefs = UserPreference(user_id=current_user.id)
            db.add(prefs)
            await db.commit()
            await db.refresh(prefs)

        return UserPreferenceResponse.model_validate(prefs)
    except Exception as e:
        logger.error(f"Error fetching preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch preferences",
        ) from e


@router.put("", response_model=UserPreferenceResponse)
async def update_preferences(
    request: UserPreferenceUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_session),
) -> UserPreferenceResponse:
    """
    Update user preferences.

    Args:
        request: Preference updates
        current_user: Authenticated user
        db: Database session

    Returns:
        Updated preferences
    """
    try:
        query = select(UserPreference).where(UserPreference.user_id == current_user.id)
        result = await db.execute(query)
        prefs = result.scalars().first()

        if not prefs:
            prefs = UserPreference(user_id=current_user.id)

        # Update only provided fields
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(prefs, field, value)

        db.add(prefs)
        await db.commit()
        await db.refresh(prefs)

        logger.info(
            "preferences_updated",
            extra={
                "user_id": str(current_user.id),
                "fields_updated": list(update_data.keys()),
            },
        )

        return UserPreferenceResponse.model_validate(prefs)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Error updating preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update preferences",
        ) from e


@router.post("/test/email")
async def test_email_notification(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Send a test email notification to verify settings.

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
        Success status
    """
    try:
        query = select(UserPreference).where(UserPreference.user_id == current_user.id)
        result = await db.execute(query)
        prefs = result.scalars().first()

        if not prefs or not prefs.email_alerts_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email notifications not enabled",
            )

        # Import notification service
        from app.services.notification_service import NotificationService

        service = NotificationService()
        success = await service.test_notification(
            channel_name="email",
            recipient=current_user.email,
        )

        return {
            "success": success,
            "message": "Test notification sent to your email" if success else "Failed to send test notification",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending test email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test notification",
        ) from e


@router.post("/test/sms")
async def test_sms_notification(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Send a test SMS notification to verify settings.

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
        Success status
    """
    try:
        query = select(UserPreference).where(UserPreference.user_id == current_user.id)
        result = await db.execute(query)
        prefs = result.scalars().first()

        if not prefs or not prefs.sms_alerts_enabled or not prefs.sms_phone_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SMS notifications not enabled or phone number not set",
            )

        # Import notification service
        from app.services.notification_service import NotificationService

        service = NotificationService()
        success = await service.test_notification(
            channel_name="sms",
            recipient=prefs.sms_phone_number,
        )

        return {
            "success": success,
            "message": "Test SMS sent to your phone" if success else "Failed to send test SMS",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending test SMS: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test notification",
        ) from e


@router.post("/test/webhook")
async def test_webhook_notification(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Send a test webhook notification to verify settings.

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
        Success status
    """
    try:
        query = select(UserPreference).where(UserPreference.user_id == current_user.id)
        result = await db.execute(query)
        prefs = result.scalars().first()

        if not prefs or not prefs.webhook_enabled or not prefs.webhook_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Webhook notifications not enabled or URL not set",
            )

        # Import notification service
        from app.services.notification_service import NotificationService

        service = NotificationService()
        success = await service.test_notification(
            channel_name="webhook",
            recipient=prefs.webhook_url,
        )

        return {
            "success": success,
            "message": "Test webhook sent successfully" if success else "Failed to send test webhook",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending test webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test notification",
        ) from e
