"""
User Management Router - Profile & AI Coach Training Endpoints
"""

import logging
from typing import Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.services.training_service import get_training_service
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/users", tags=["users"])


@router.get("/me")
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current user's profile including location.

    Returns user data with hierarchical location fields:
    - Basic info (name, phone, email)
    - Location hierarchy (street, village, panchayat, block, district, state)
    - GPS coordinates if available
    - Formatted address

    Use case: Display user profile with location in mobile app settings.
    This location will be used automatically for reports unless user overrides.
    """
    return current_user.to_dict()


@router.get("/{user_id}/training-progress")
async def get_training_progress(
    user_id: UUID,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get user's AI Coach training progress.

    Returns:
        - in_training_mode: bool
        - training_mode_enabled: bool
        - training_completed: bool
        - reports_completed: int
        - reports_remaining: int
        - completion_percentage: int
        - graduation_threshold: int
        - can_graduate: bool
    """
    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )

        # Get training service
        training_service = get_training_service(db)

        # Get progress
        progress = training_service.get_training_progress(user)

        logger.info(f"Training progress for user {user_id}: {progress}")

        return progress

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting training progress: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get training progress: {str(e)}"
        )


@router.post("/{user_id}/enable-training")
async def enable_training_mode(
    user_id: UUID,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Enable AI Coach training mode for user.

    Can be used to re-enable training after graduation.
    """
    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )

        # Get training service
        training_service = get_training_service(db)

        # Enable training
        success = training_service.enable_training_mode(user)

        return {
            "success": success,
            "message": "Training mode enabled",
            "training_mode_enabled": user.training_mode_enabled
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling training mode: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enable training mode: {str(e)}"
        )


@router.post("/{user_id}/disable-training")
async def disable_training_mode(
    user_id: UUID,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Disable AI Coach training mode for user.

    User will use simple voice recording mode.
    """
    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )

        # Get training service
        training_service = get_training_service(db)

        # Disable training
        success = training_service.disable_training_mode(user)

        return {
            "success": success,
            "message": "Training mode disabled",
            "training_mode_enabled": user.training_mode_enabled
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling training mode: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disable training mode: {str(e)}"
        )


@router.post("/{user_id}/reset-training")
async def reset_training(
    user_id: UUID,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Reset user's training progress (for testing/debugging).

    Resets report count to 0 and marks training as incomplete.
    """
    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )

        # Get training service
        training_service = get_training_service(db)

        # Reset training
        success = training_service.reset_training(user)

        return {
            "success": success,
            "message": "Training progress reset",
            "training_reports_count": user.training_reports_count,
            "training_completed": user.training_completed,
            "training_mode_enabled": user.training_mode_enabled
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting training: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset training: {str(e)}"
        )
