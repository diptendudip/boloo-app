"""
AI Coach Training Service.

Handles training mode detection, graduation logic, and mode toggling for new users.
"""

import logging
from typing import Dict, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.conversation import Conversation

logger = logging.getLogger(__name__)


class TrainingServiceError(Exception):
    """Base exception for training service errors"""
    pass


class TrainingService:
    """
    Manages AI Coach training mode for new users.

    Handles:
    - Training mode detection
    - Report count tracking
    - Auto-graduation after 5 successful reports
    - Settings toggle for re-enabling training mode
    """

    def __init__(self, db: Session):
        """
        Initialize training service.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.graduation_threshold = 5  # Reports needed for graduation

    def is_in_training_mode(self, user: User) -> bool:
        """
        Check if user is currently in training mode.

        Args:
            user: User model instance

        Returns:
            True if user should use training mode, False for simple mode

        Logic:
            - Returns True if training_mode_enabled AND not training_completed
            - Returns False if training_completed OR training_mode_enabled is False
        """
        if not user.training_mode_enabled:
            logger.debug(f"User {user.id} has training mode disabled")
            return False

        if user.training_completed:
            logger.debug(f"User {user.id} has completed training")
            return False

        logger.debug(f"User {user.id} is in training mode (reports: {user.training_reports_count})")
        return True

    def should_graduate(self, user: User) -> bool:
        """
        Check if user has met graduation criteria.

        Args:
            user: User model instance

        Returns:
            True if user should graduate from training mode

        Criteria:
            - User must have completed >= graduation_threshold (default 5) reports
            - User must not already be graduated
        """
        if user.training_completed:
            return False

        if user.training_reports_count >= self.graduation_threshold:
            logger.info(
                f"User {user.id} meets graduation criteria "
                f"({user.training_reports_count} >= {self.graduation_threshold})"
            )
            return True

        return False

    def increment_report_count(self, user: User) -> int:
        """
        Increment user's training report count.

        Args:
            user: User model instance

        Returns:
            New report count after increment
        """
        user.training_reports_count += 1
        self.db.commit()
        self.db.refresh(user)

        logger.info(f"User {user.id} report count: {user.training_reports_count}")
        return user.training_reports_count

    def graduate_user(self, user: User) -> Dict[str, Any]:
        """
        Graduate user from training mode.

        Marks the user as having completed training and disables training mode.
        This triggers the celebration screen in the mobile app.

        Args:
            user: User model instance

        Returns:
            Dict containing graduation details
        """
        if user.training_completed:
            logger.warning(f"User {user.id} already graduated")
            return {
                "success": False,
                "message": "User already graduated",
                "reports_count": user.training_reports_count
            }

        user.training_completed = True
        user.training_mode_enabled = False  # Auto-disable training mode
        self.db.commit()
        self.db.refresh(user)

        logger.info(
            f"🎓 User {user.id} graduated after {user.training_reports_count} reports"
        )

        return {
            "success": True,
            "message": "Congratulations! Training completed successfully!",
            "reports_count": user.training_reports_count,
            "graduated_at": datetime.utcnow().isoformat()
        }

    def enable_training_mode(self, user: User) -> bool:
        """
        Enable training mode for a user.

        This can be called from settings to re-enable training mode
        even after graduation.

        Args:
            user: User model instance

        Returns:
            True if training mode was enabled
        """
        user.training_mode_enabled = True
        self.db.commit()
        self.db.refresh(user)

        logger.info(f"Training mode enabled for user {user.id}")
        return True

    def disable_training_mode(self, user: User) -> bool:
        """
        Disable training mode for a user.

        This can be called from settings to disable training mode
        and use simple one-shot recording instead.

        Args:
            user: User model instance

        Returns:
            True if training mode was disabled
        """
        user.training_mode_enabled = False
        self.db.commit()
        self.db.refresh(user)

        logger.info(f"Training mode disabled for user {user.id}")
        return True

    def get_training_progress(self, user: User) -> Dict[str, Any]:
        """
        Get user's training progress details.

        Args:
            user: User model instance

        Returns:
            Dict containing:
                - in_training_mode: bool
                - reports_completed: int
                - reports_remaining: int
                - completion_percentage: int (0-100)
                - training_completed: bool
                - can_graduate: bool
        """
        in_training = self.is_in_training_mode(user)
        reports_completed = user.training_reports_count
        reports_remaining = max(0, self.graduation_threshold - reports_completed)
        completion_pct = min(100, int((reports_completed / self.graduation_threshold) * 100))
        can_graduate = self.should_graduate(user)

        return {
            "in_training_mode": in_training,
            "training_mode_enabled": user.training_mode_enabled,
            "training_completed": user.training_completed,
            "reports_completed": reports_completed,
            "reports_remaining": reports_remaining,
            "completion_percentage": completion_pct,
            "graduation_threshold": self.graduation_threshold,
            "can_graduate": can_graduate
        }

    def reset_training(self, user: User) -> bool:
        """
        Reset user's training progress.

        This is useful for testing or if a user wants to restart training.

        Args:
            user: User model instance

        Returns:
            True if training was reset
        """
        user.training_reports_count = 0
        user.training_completed = False
        user.training_mode_enabled = True
        self.db.commit()
        self.db.refresh(user)

        logger.info(f"Training reset for user {user.id}")
        return True


def get_training_service(db: Session) -> TrainingService:
    """
    Factory function to create TrainingService instance.

    Args:
        db: SQLAlchemy database session

    Returns:
        TrainingService instance
    """
    return TrainingService(db)
