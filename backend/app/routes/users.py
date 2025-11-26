"""
users.py

User-related API endpoints for Boloo app
Includes push token registration and user profile management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, validator
from typing import Optional
import logging

from app.database import get_db
from app.models import User
from app.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


class PushTokenRequest(BaseModel):
    """Request model for storing push token"""
    push_token: str
    device_type: str
    device_info: Optional[dict] = None

    @validator('push_token')
    def validate_push_token(cls, v):
        """Validate Expo push token format"""
        if not v.startswith("ExponentPushToken["):
            raise ValueError("Invalid Expo push token format")
        return v

    @validator('device_type')
    def validate_device_type(cls, v):
        """Validate device type"""
        if v not in ['ios', 'android']:
            raise ValueError("Device type must be 'ios' or 'android'")
        return v


class NotificationSettingsRequest(BaseModel):
    """Request model for updating notification settings"""
    status_updates: bool = True
    case_assignments: bool = True
    case_resolutions: bool = True
    new_comments: bool = True
    system_announcements: bool = True


class PushTokenResponse(BaseModel):
    """Response model for push token operations"""
    success: bool
    message: str


class UserProfileResponse(BaseModel):
    """Response model for user profile"""
    id: str
    email: str
    phone: str
    name: Optional[str]
    address: Optional[str]
    role: str
    is_active: bool
    is_first_timer: bool
    push_token: Optional[str]
    notification_settings: Optional[dict]


@router.post("/push-token", response_model=PushTokenResponse)
async def register_push_token(
    request: PushTokenRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Register or update user's push notification token

    This endpoint stores the Expo push token for the authenticated user,
    enabling push notifications to be sent to their device.
    """
    try:
        # Update user's push token
        current_user.push_token = request.push_token

        # Store device information in notification settings
        if not current_user.notification_settings:
            current_user.notification_settings = {}

        current_user.notification_settings["device_type"] = request.device_type

        if request.device_info:
            current_user.notification_settings["device_info"] = request.device_info

        # Set default notification preferences if not already set
        if "preferences" not in current_user.notification_settings:
            current_user.notification_settings["preferences"] = {
                "status_updates": True,
                "case_assignments": True,
                "case_resolutions": True,
                "new_comments": True,
                "system_announcements": True,
            }

        db.commit()
        db.refresh(current_user)

        logger.info(f"Push token registered for user {current_user.id}")

        return PushTokenResponse(
            success=True,
            message="Push token registered successfully"
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Error registering push token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register push token"
        )


@router.delete("/push-token", response_model=PushTokenResponse)
async def remove_push_token(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove user's push notification token

    This endpoint removes the push token, effectively disabling
    push notifications for the user.
    """
    try:
        current_user.push_token = None
        db.commit()

        logger.info(f"Push token removed for user {current_user.id}")

        return PushTokenResponse(
            success=True,
            message="Push token removed successfully"
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Error removing push token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove push token"
        )


@router.put("/notification-settings", response_model=PushTokenResponse)
async def update_notification_settings(
    settings: NotificationSettingsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user's notification preferences

    Allows users to customize which types of notifications they want to receive.
    """
    try:
        if not current_user.notification_settings:
            current_user.notification_settings = {}

        current_user.notification_settings["preferences"] = {
            "status_updates": settings.status_updates,
            "case_assignments": settings.case_assignments,
            "case_resolutions": settings.case_resolutions,
            "new_comments": settings.new_comments,
            "system_announcements": settings.system_announcements,
        }

        db.commit()

        logger.info(f"Notification settings updated for user {current_user.id}")

        return PushTokenResponse(
            success=True,
            message="Notification settings updated successfully"
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Error updating notification settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notification settings"
        )


@router.get("/notification-settings")
async def get_notification_settings(
    current_user: User = Depends(get_current_user)
):
    """
    Get user's current notification preferences
    """
    if not current_user.notification_settings:
        # Return default settings
        return {
            "preferences": {
                "status_updates": True,
                "case_assignments": True,
                "case_resolutions": True,
                "new_comments": True,
                "system_announcements": True,
            }
        }

    return current_user.notification_settings


@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get authenticated user's profile
    """
    return UserProfileResponse(
        id=str(current_user.id),
        email=current_user.email,
        phone=current_user.phone,
        name=current_user.name,
        address=current_user.address,
        role=current_user.role.value,
        is_active=current_user.is_active,
        is_first_timer=current_user.is_first_timer,
        push_token=current_user.push_token,
        notification_settings=current_user.notification_settings
    )
