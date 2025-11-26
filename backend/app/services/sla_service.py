"""
SLA Tracking Service - "Agla Kya Hoga" (What Happens Next)

Manages:
1. SLA timers and deadlines
2. Auto-escalation when SLA breached
3. "Who has the ball" tracking
4. Timeline generation
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.case import Case
from app.models.entity import Entity
from app.models.case_sla_tracking import CaseSLATracking


class SLAService:
    """Service to manage SLA tracking and escalations"""

    def __init__(self, db: Session):
        self.db = db

    def start_sla_tracking(
        self,
        case_id: str,
        entity_id: str,
        sla_hours: int,
        who_has_ball: str = "moderator"
    ) -> CaseSLATracking:
        """
        Start SLA tracking for a case

        Args:
            case_id: UUID of the case
            entity_id: UUID of responsible entity
            sla_hours: Expected response time in hours
            who_has_ball: Who currently has responsibility

        Returns:
            CaseSLATracking record
        """
        tracking = CaseSLATracking(
            case_id=case_id,
            responsible_entity_id=entity_id,
            sla_hours=sla_hours,
            started_at=datetime.utcnow(),
            who_has_ball=who_has_ball,
            escalation_level=0
        )

        self.db.add(tracking)
        self.db.commit()
        self.db.refresh(tracking)

        return tracking

    def update_ball_holder(
        self,
        case_id: str,
        new_holder: str,
        action_needed: Optional[str] = None
    ) -> Optional[CaseSLATracking]:
        """
        Update who has the ball

        Args:
            case_id: UUID of the case
            new_holder: New ball holder (citizen/moderator/officer/system)
            action_needed: Description of action needed from citizen

        Returns:
            Updated tracking record
        """
        tracking = self.db.query(CaseSLATracking).filter(
            and_(
                CaseSLATracking.case_id == case_id,
                CaseSLATracking.responded_at.is_(None)  # Active tracking only
            )
        ).first()

        if tracking:
            tracking.who_has_ball = new_holder
            tracking.updated_at = datetime.utcnow()

            # Store action_needed in metadata if needed
            # (You may want to add a metadata JSONB column to the model)

            self.db.commit()
            self.db.refresh(tracking)

        return tracking

    def mark_responded(
        self,
        case_id: str,
        response_time: Optional[datetime] = None
    ) -> Optional[CaseSLATracking]:
        """
        Mark that entity has responded to case

        Args:
            case_id: UUID of the case
            response_time: When response occurred (default: now)

        Returns:
            Updated tracking record
        """
        tracking = self.db.query(CaseSLATracking).filter(
            and_(
                CaseSLATracking.case_id == case_id,
                CaseSLATracking.responded_at.is_(None)
            )
        ).first()

        if tracking:
            tracking.responded_at = response_time or datetime.utcnow()
            tracking.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(tracking)

        return tracking

    def check_and_escalate(
        self,
        case_id: str,
        escalation_entity_id: Optional[str] = None,
        escalation_sla_hours: Optional[int] = None
    ) -> Optional[CaseSLATracking]:
        """
        Check if SLA is breached and escalate if needed

        Args:
            case_id: UUID of the case
            escalation_entity_id: Entity to escalate to
            escalation_sla_hours: SLA hours for escalated level

        Returns:
            New tracking record if escalated, None otherwise
        """
        current_tracking = self.db.query(CaseSLATracking).filter(
            and_(
                CaseSLATracking.case_id == case_id,
                CaseSLATracking.responded_at.is_(None)
            )
        ).first()

        if not current_tracking:
            return None

        # Calculate SLA deadline
        deadline = current_tracking.started_at + timedelta(hours=current_tracking.sla_hours)
        now = datetime.utcnow()

        # Check if breached
        if now < deadline:
            return None  # Still within SLA

        # Mark current tracking as escalated
        current_tracking.escalated_at = now
        current_tracking.updated_at = now

        # Create new tracking for escalated level
        if escalation_entity_id and escalation_sla_hours:
            new_tracking = CaseSLATracking(
                case_id=case_id,
                responsible_entity_id=escalation_entity_id,
                sla_hours=escalation_sla_hours,
                started_at=now,
                who_has_ball="officer",
                escalation_level=current_tracking.escalation_level + 1
            )

            self.db.add(new_tracking)

        self.db.commit()

        if escalation_entity_id:
            self.db.refresh(new_tracking)
            return new_tracking

        return current_tracking

    def get_sla_status(self, case_id: str) -> Dict:
        """
        Get current SLA status for a case

        Args:
            case_id: UUID of the case

        Returns:
            Dict with SLA status information
        """
        tracking = self.db.query(CaseSLATracking).filter(
            and_(
                CaseSLATracking.case_id == case_id,
                CaseSLATracking.responded_at.is_(None)
            )
        ).first()

        if not tracking:
            return {
                "active": False,
                "message": "कोई सक्रिय SLA नहीं"
            }

        # Get responsible entity
        entity = self.db.query(Entity).filter(
            Entity.id == tracking.responsible_entity_id
        ).first()

        # Calculate time remaining
        deadline = tracking.started_at + timedelta(hours=tracking.sla_hours)
        now = datetime.utcnow()
        time_remaining = deadline - now

        # Get escalation entity if exists
        escalation_entity = None
        if entity and entity.parent_entity_id:
            escalation_entity = self.db.query(Entity).filter(
                Entity.id == entity.parent_entity_id
            ).first()

        # Calculate percentage elapsed
        total_seconds = timedelta(hours=tracking.sla_hours).total_seconds()
        elapsed_seconds = (now - tracking.started_at).total_seconds()
        progress_percentage = min(100, int((elapsed_seconds / total_seconds) * 100))

        # Determine status
        if time_remaining.total_seconds() <= 0:
            status = "breached"
            status_hindi = "समय सीमा समाप्त"
        elif time_remaining.total_seconds() < 86400:  # < 24 hours
            status = "urgent"
            status_hindi = "जल्द ही समाप्त होगी"
        else:
            status = "on_track"
            status_hindi = "समय पर चल रहा है"

        return {
            "active": True,
            "responsible_entity": entity.name if entity else "Unknown",
            "responsible_entity_id": str(tracking.responsible_entity_id),
            "sla_hours": tracking.sla_hours,
            "started_at": tracking.started_at.isoformat(),
            "deadline": deadline.isoformat(),
            "time_remaining_hours": max(0, int(time_remaining.total_seconds() / 3600)),
            "time_remaining_minutes": max(0, int((time_remaining.total_seconds() % 3600) / 60)),
            "progress_percentage": progress_percentage,
            "status": status,
            "status_hindi": status_hindi,
            "who_has_ball": tracking.who_has_ball,
            "escalation_level": tracking.escalation_level,
            "escalation_entity": escalation_entity.name if escalation_entity else None,
            "escalation_entity_id": str(escalation_entity.id) if escalation_entity else None,
        }

    def get_timeline(self, case_id: str) -> List[Dict]:
        """
        Get complete timeline of SLA tracking events

        Args:
            case_id: UUID of the case

        Returns:
            List of timeline events
        """
        all_tracking = self.db.query(CaseSLATracking).filter(
            CaseSLATracking.case_id == case_id
        ).order_by(CaseSLATracking.created_at).all()

        timeline = []

        for idx, tracking in enumerate(all_tracking):
            entity = self.db.query(Entity).filter(
                Entity.id == tracking.responsible_entity_id
            ).first()

            # Started event
            timeline.append({
                "timestamp": tracking.started_at.isoformat(),
                "event_type": "escalated" if idx > 0 else "assigned",
                "event_hindi": f"{'एस्केलेट किया' if idx > 0 else 'भेजा गया'}: {entity.name if entity else 'Unknown'}",
                "event_english": f"{'Escalated' if idx > 0 else 'Assigned'} to {entity.name if entity else 'Unknown'}",
                "who_has_ball": tracking.who_has_ball,
                "escalation_level": tracking.escalation_level
            })

            # Responded event
            if tracking.responded_at:
                timeline.append({
                    "timestamp": tracking.responded_at.isoformat(),
                    "event_type": "responded",
                    "event_hindi": f"{entity.name if entity else 'दफ्तर'} ने जवाब दिया",
                    "event_english": f"{entity.name if entity else 'Office'} responded",
                    "who_has_ball": "officer",
                    "escalation_level": tracking.escalation_level
                })

            # Escalated event
            if tracking.escalated_at:
                timeline.append({
                    "timestamp": tracking.escalated_at.isoformat(),
                    "event_type": "sla_breached",
                    "event_hindi": f"समय सीमा समाप्त - आगे बढ़ाया गया",
                    "event_english": f"SLA breached - escalated",
                    "who_has_ball": "system",
                    "escalation_level": tracking.escalation_level
                })

        return timeline

    def get_pending_escalations(self) -> List[Dict]:
        """
        Get all cases that need escalation (SLA breached)

        Returns:
            List of cases needing escalation
        """
        # Find all active SLA tracking records
        active_tracking = self.db.query(CaseSLATracking).filter(
            and_(
                CaseSLATracking.responded_at.is_(None),
                CaseSLATracking.escalated_at.is_(None)
            )
        ).all()

        pending = []
        now = datetime.utcnow()

        for tracking in active_tracking:
            deadline = tracking.started_at + timedelta(hours=tracking.sla_hours)

            if now >= deadline:
                case = self.db.query(Case).filter(Case.id == tracking.case_id).first()
                entity = self.db.query(Entity).filter(
                    Entity.id == tracking.responsible_entity_id
                ).first()

                pending.append({
                    "case_id": str(tracking.case_id),
                    "case_title": case.title if case else "Unknown",
                    "current_entity": entity.name if entity else "Unknown",
                    "hours_overdue": int((now - deadline).total_seconds() / 3600),
                    "escalation_level": tracking.escalation_level
                })

        return pending


def create_sla_service(db: Session) -> SLAService:
    """Factory function to create SLA service"""
    return SLAService(db)
