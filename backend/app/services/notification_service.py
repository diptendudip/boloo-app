"""
Notification Service for handling reminders and push notifications

This service manages:
- Scheduling reminder notifications for personal diary entries
- Storing notifications in the database
- Future integration with push notification services (FCM, APNs)
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
import uuid

from app.models.notification import Notification
from app.models.case import Case
from app.models.user import User

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for managing notifications and reminders.

    Responsibilities:
    - Create reminder notifications for personal diary entries
    - Store notifications in the database with proper status tracking
    - Prepare for future push notification integration (FCM, APNs)
    """

    @staticmethod
    def schedule_reminder(
        db: Session,
        user_id: uuid.UUID,
        case_id: uuid.UUID,
        reminder_at: datetime,
        case_title: str
    ) -> Notification:
        """
        Schedule a reminder notification for a personal diary entry.

        Args:
            db: Database session
            user_id: UUID of the user to notify
            case_id: UUID of the case/diary entry
            reminder_at: Datetime when the reminder should be sent
            case_title: Title of the diary entry for notification content

        Returns:
            Notification: Created notification object

        Raises:
            ValueError: If reminder_at is in the past

        Example:
            notification = NotificationService.schedule_reminder(
                db=db,
                user_id=user.id,
                case_id=case.id,
                reminder_at=datetime.utcnow() + timedelta(hours=24),
                case_title="Follow up on health checkup"
            )
        """
        if reminder_at <= datetime.utcnow():
            raise ValueError("Reminder time must be in the future")

        # Create notification payload
        payload = {
            "type": "diary_reminder",
            "case_id": str(case_id),
            "title": "Diary Reminder",
            "message": f"Reminder: {case_title}",
            "scheduled_for": reminder_at.isoformat(),
            "action_url": f"/cases/{case_id}"
        }

        # Create notification record
        notification = Notification(
            user_id=user_id,
            channel="push",  # Default to push, can support sms/email/voice later
            template_id="diary_reminder",
            payload=payload,
            status="pending",
            created_at=datetime.utcnow()
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        logger.info(
            f"Scheduled reminder notification {notification.id} for user {user_id} "
            f"at {reminder_at.isoformat()}"
        )

        return notification

    @staticmethod
    def cancel_reminder(db: Session, case_id: uuid.UUID) -> int:
        """
        Cancel all pending reminder notifications for a specific case.

        Args:
            db: Database session
            case_id: UUID of the case

        Returns:
            int: Number of notifications cancelled

        Example:
            cancelled_count = NotificationService.cancel_reminder(db, case_id)
        """
        # Find all pending notifications for this case
        notifications = db.query(Notification).filter(
            Notification.payload["case_id"].astext == str(case_id),
            Notification.status == "pending"
        ).all()

        cancelled_count = 0
        for notification in notifications:
            notification.status = "cancelled"
            notification.error_message = "Case converted to grievance or deleted"
            cancelled_count += 1

        if cancelled_count > 0:
            db.commit()
            logger.info(f"Cancelled {cancelled_count} reminder(s) for case {case_id}")

        return cancelled_count

    @staticmethod
    def update_reminder(
        db: Session,
        case_id: uuid.UUID,
        new_reminder_at: datetime,
        case_title: str
    ) -> Optional[Notification]:
        """
        Update the reminder time for an existing case.

        Args:
            db: Database session
            case_id: UUID of the case
            new_reminder_at: New datetime for the reminder
            case_title: Updated title for the notification

        Returns:
            Notification: Updated notification object or None if not found

        Raises:
            ValueError: If new_reminder_at is in the past
        """
        if new_reminder_at <= datetime.utcnow():
            raise ValueError("Reminder time must be in the future")

        # Find the pending notification for this case
        notification = db.query(Notification).filter(
            Notification.payload["case_id"].astext == str(case_id),
            Notification.status == "pending"
        ).first()

        if not notification:
            logger.warning(f"No pending reminder found for case {case_id}")
            return None

        # Update the notification payload
        notification.payload["scheduled_for"] = new_reminder_at.isoformat()
        notification.payload["message"] = f"Reminder: {case_title}"

        db.commit()
        db.refresh(notification)

        logger.info(f"Updated reminder notification {notification.id} to {new_reminder_at.isoformat()}")

        return notification

    @staticmethod
    def get_pending_reminders(db: Session, user_id: uuid.UUID) -> list[Notification]:
        """
        Get all pending reminder notifications for a user.

        Args:
            db: Database session
            user_id: UUID of the user

        Returns:
            list[Notification]: List of pending notifications
        """
        notifications = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.status == "pending",
            Notification.template_id == "diary_reminder"
        ).order_by(Notification.created_at.desc()).all()

        return notifications

    @staticmethod
    def mark_as_sent(db: Session, notification_id: uuid.UUID) -> bool:
        """
        Mark a notification as sent (for future push notification integration).

        Args:
            db: Database session
            notification_id: UUID of the notification

        Returns:
            bool: True if marked successfully, False if not found
        """
        notification = db.query(Notification).filter(
            Notification.id == notification_id
        ).first()

        if not notification:
            return False

        notification.status = "sent"
        notification.sent_at = datetime.utcnow()
        db.commit()

        logger.info(f"Marked notification {notification_id} as sent")
        return True

    @staticmethod
    def mark_as_failed(
        db: Session,
        notification_id: uuid.UUID,
        error_message: str
    ) -> bool:
        """
        Mark a notification as failed with an error message.

        Args:
            db: Database session
            notification_id: UUID of the notification
            error_message: Description of the failure

        Returns:
            bool: True if marked successfully, False if not found
        """
        notification = db.query(Notification).filter(
            Notification.id == notification_id
        ).first()

        if not notification:
            return False

        notification.status = "failed"
        notification.error_message = error_message
        db.commit()

        logger.error(f"Notification {notification_id} failed: {error_message}")
        return True

    @staticmethod
    def send_conversion_notification(
        db: Session,
        user_id: uuid.UUID,
        case_id: uuid.UUID,
        case_title: str
    ) -> Notification:
        """
        Send a notification when a personal diary entry is converted to a grievance.

        Args:
            db: Database session
            user_id: UUID of the user
            case_id: UUID of the case
            case_title: Title of the converted case

        Returns:
            Notification: Created notification object
        """
        payload = {
            "type": "diary_converted",
            "case_id": str(case_id),
            "title": "Diary Entry Converted",
            "message": f"Your diary entry '{case_title}' has been converted to a grievance and will be processed.",
            "action_url": f"/cases/{case_id}"
        }

        notification = Notification(
            user_id=user_id,
            channel="push",
            template_id="diary_converted",
            payload=payload,
            status="pending",
            created_at=datetime.utcnow()
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        logger.info(f"Created conversion notification {notification.id} for user {user_id}")

        return notification
