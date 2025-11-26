"""Cases router with personal diary support and privacy enforcement"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import logging

from app.database import get_db
from app.models import Case, CaseEvent, User
from app.models.case import CaseKind, CaseStatus
from app.utils.auth import get_current_user, get_current_user_or_dev
from app.services.notification_service import NotificationService
from app.middleware.privacy import (
    PrivacyEnforcer,
    exclude_personal_from_query,
    check_personal_case_access
)

router = APIRouter()
logger = logging.getLogger(__name__)


class CaseCreate(BaseModel):
    title: Optional[str] = None
    transcript_text: Optional[str] = None
    audio_url: Optional[str] = None
    location_text: Optional[str] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    issue_type: Optional[str] = None
    kind: Optional[str] = Field(default="grievance", description="Case type: grievance, community_story, or personal")
    reminder_at: Optional[datetime] = Field(default=None, description="Reminder datetime for personal diary entries")
    is_public: Optional[bool] = Field(default=False, description="Whether case is publicly visible")


class CaseUpdate(BaseModel):
    status: Optional[str] = None
    note: Optional[str] = None
    reminder_at: Optional[datetime] = None


class ConvertToGrievanceResponse(BaseModel):
    success: bool
    case: dict
    next_steps: dict


@router.post("")
async def create_case(
    case_data: CaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new case (grievance, community story, or personal diary entry).

    For personal diary entries:
    - Set kind="personal"
    - Optionally set reminder_at for future reminders
    - is_public will be forced to False
    - entity_id will be cleared (not routed)

    For grievances:
    - Set kind="grievance" (default)
    - Will be routed to appropriate entity
    - Can be public or private

    Returns:
        dict: Success status and created case data
    """
    try:
        from geoalchemy2.elements import WKTElement

        # Parse and validate case kind
        try:
            case_kind = CaseKind(case_data.kind.lower())
        except (ValueError, AttributeError):
            case_kind = CaseKind.GRIEVANCE

        # Enforce privacy for personal cases
        is_public, entity_id = PrivacyEnforcer.validate_personal_case_creation(
            kind=case_kind,
            is_public=case_data.is_public,
            entity_id=None  # Will be set by routing service for grievances
        )

        # Determine status and title based on kind
        if case_kind == CaseKind.PERSONAL:
            status = CaseStatus.DRAFT.value
            title = case_data.title or "Personal Note"
        else:
            status = CaseStatus.SUBMITTED.value
            title = case_data.title or "New Grievance"

        case = Case(
            user_id=current_user.id,
            title=title,
            transcript_text=case_data.transcript_text,
            audio_url=case_data.audio_url,
            location_text=case_data.location_text,
            issue_type=case_data.issue_type,
            kind=case_kind,
            status=status,
            is_public=is_public,
            reminder_at=case_data.reminder_at
        )

        if case_data.location_lat and case_data.location_lng:
            case.location_point = WKTElement(
                f'POINT({case_data.location_lng} {case_data.location_lat})',
                srid=4326
            )

        db.add(case)
        db.commit()
        db.refresh(case)

        # Create event
        event_type = "created" if case_kind == CaseKind.PERSONAL else "submitted"
        event = CaseEvent(
            case_id=case.id,
            event_type=event_type,
            actor_id=current_user.id,
            actor_role=current_user.role,
            note=f"Created {case_kind.value} entry"
        )
        db.add(event)
        db.commit()

        # Schedule reminder for personal diary entries
        notification = None
        if case_kind == CaseKind.PERSONAL and case_data.reminder_at:
            try:
                notification = NotificationService.schedule_reminder(
                    db=db,
                    user_id=current_user.id,
                    case_id=case.id,
                    reminder_at=case_data.reminder_at,
                    case_title=case.title
                )
                logger.info(f"Scheduled reminder for personal case {case.id}")
            except ValueError as e:
                logger.warning(f"Failed to schedule reminder: {e}")
                # Don't fail case creation if reminder fails

        logger.info(f"Case created: {case.id} (kind={case_kind.value})")

        response = {
            "success": True,
            "case": case.to_dict()
        }

        if notification:
            response["reminder"] = notification.to_dict()

        return response

    except Exception as e:
        logger.error(f"Error creating case: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def list_cases(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_dev)
):
    """
    List cases (excludes personal diary entries from other users).

    Citizens see only their own cases.
    Admins/Officers see all non-personal cases + their own personal cases.

    This endpoint automatically filters out personal diary entries to maintain privacy.
    """
    query = db.query(Case)

    # Apply privacy filter to exclude other users' personal cases
    query = exclude_personal_from_query(query, current_user)

    if current_user.role == "citizen":
        query = query.filter(Case.user_id == current_user.id)

    if status:
        query = query.filter(Case.status == status)

    cases = query.order_by(Case.created_at.desc()).offset(skip).limit(limit).all()

    # Additional safety check (defense in depth)
    cases = PrivacyEnforcer.validate_case_visibility_in_list(cases, current_user)

    return {"cases": [c.to_dict() for c in cases], "total": query.count()}


@router.get("/personal")
async def list_personal_cases(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List personal diary entries for the current user.

    Returns only cases where:
    - kind = PERSONAL
    - user_id = current_user
    - Includes reminder information if set

    This endpoint is ALWAYS private to the authenticated user.
    """
    query = db.query(Case).filter(
        Case.kind == CaseKind.PERSONAL,
        Case.user_id == current_user.id
    )

    cases = query.order_by(Case.created_at.desc()).offset(skip).limit(limit).all()

    # Get pending reminders for these cases
    pending_reminders = NotificationService.get_pending_reminders(db, current_user.id)
    reminder_map = {
        str(n.payload.get("case_id")): n.to_dict()
        for n in pending_reminders
        if n.payload and n.payload.get("case_id")
    }

    # Enrich case data with reminder info
    enriched_cases = []
    for case in cases:
        case_dict = case.to_dict()
        case_dict["reminder"] = reminder_map.get(str(case.id))
        enriched_cases.append(case_dict)

    logger.info(f"User {current_user.id} listed {len(enriched_cases)} personal diary entries")

    return {
        "cases": enriched_cases,
        "total": query.count()
    }


@router.get("/{case_id}")
async def get_case(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get case details.

    For personal diary entries, only the owner can access.
    For other cases, standard role-based permissions apply.
    """
    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Check permissions for personal cases (CRITICAL PRIVACY CHECK)
    check_personal_case_access(case, current_user)

    # Check permissions for non-personal cases
    if current_user.role == "citizen" and case.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    PrivacyEnforcer.log_privacy_access(
        case_id=case.id,
        user_id=current_user.id,
        action="view",
        success=True
    )

    return {"case": case.to_dict(), "events": [e.to_dict() for e in case.events]}


@router.post("/{case_id}/convert-to-grievance")
async def convert_to_grievance(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ConvertToGrievanceResponse:
    """
    Convert a personal diary entry to a grievance.

    Validation:
    - Case must have can_convert_to_grievance = true
    - Case must be kind = PERSONAL
    - User must be the owner

    Actions:
    - Update kind to GRIEVANCE
    - Set can_convert_to_grievance = false (prevent re-conversion)
    - Update status to SUBMITTED
    - Set is_public = true (or configurable)
    - Cancel any pending reminders
    - Trigger routing logic
    - Create event log
    - Send notification

    Returns:
        ConvertToGrievanceResponse with next steps for the grievance
    """
    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Verify ownership
    if case.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the case owner can convert to grievance"
        )

    # Verify it's a personal case
    if case.kind != CaseKind.PERSONAL:
        raise HTTPException(
            status_code=400,
            detail="Only personal diary entries can be converted to grievances"
        )

    # Verify conversion is allowed
    if not case.can_convert_to_grievance:
        raise HTTPException(
            status_code=400,
            detail="This case cannot be converted to a grievance (already converted or not eligible)"
        )

    try:
        # Cancel any pending reminders
        cancelled_count = NotificationService.cancel_reminder(db, case.id)
        logger.info(f"Cancelled {cancelled_count} reminder(s) for case {case_id}")

        # Update case to grievance
        case.kind = CaseKind.GRIEVANCE
        case.can_convert_to_grievance = False  # Prevent re-conversion
        case.status = CaseStatus.SUBMITTED.value
        case.is_public = True  # Grievances are typically public
        case.reminder_at = None  # Clear reminder

        db.commit()

        # Create conversion event
        event = CaseEvent(
            case_id=case.id,
            event_type="converted",
            actor_id=current_user.id,
            actor_role=current_user.role,
            note="Converted from personal diary entry to grievance"
        )
        db.add(event)
        db.commit()

        # Send conversion notification
        NotificationService.send_conversion_notification(
            db=db,
            user_id=current_user.id,
            case_id=case.id,
            case_title=case.title
        )

        # Trigger routing logic (import routing service if available)
        try:
            from app.services.routing_service import RoutingService
            routing_result = RoutingService.route_case(db, case)
            next_steps = {
                "status": "routed",
                "entity_id": str(routing_result.get("entity_id")) if routing_result else None,
                "estimated_resolution": "7-14 days",
                "message": "Your grievance has been submitted and will be routed to the appropriate department."
            }
        except (ImportError, Exception) as e:
            logger.warning(f"Could not trigger routing: {e}")
            next_steps = {
                "status": "submitted",
                "entity_id": None,
                "estimated_resolution": "7-14 days",
                "message": "Your grievance has been submitted and is pending review."
            }

        db.refresh(case)

        logger.info(f"Successfully converted personal case {case_id} to grievance")

        PrivacyEnforcer.log_privacy_access(
            case_id=case.id,
            user_id=current_user.id,
            action="convert_to_grievance",
            success=True
        )

        return ConvertToGrievanceResponse(
            success=True,
            case=case.to_dict(),
            next_steps=next_steps
        )

    except Exception as e:
        logger.error(f"Error converting case to grievance: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{case_id}")
async def update_case(
    case_id: str,
    update_data: CaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update case (including reminder updates for personal diary entries).

    For personal cases:
    - Can update reminder_at to reschedule reminders
    - Only owner can update

    For grievances:
    - Standard role-based permissions apply
    """
    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Check personal case access
    check_personal_case_access(case, current_user)

    # Check ownership for updates
    if case.user_id != current_user.id and current_user.role == "citizen":
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        # Update status if provided
        if update_data.status:
            case.status = update_data.status

        # Update reminder for personal cases
        if case.kind == CaseKind.PERSONAL and update_data.reminder_at:
            try:
                NotificationService.update_reminder(
                    db=db,
                    case_id=case.id,
                    new_reminder_at=update_data.reminder_at,
                    case_title=case.title
                )
                case.reminder_at = update_data.reminder_at
                logger.info(f"Updated reminder for case {case_id}")
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

        db.commit()

        # Create event
        event = CaseEvent(
            case_id=case.id,
            event_type="updated",
            actor_id=current_user.id,
            actor_role=current_user.role,
            note=update_data.note
        )
        db.add(event)
        db.commit()

        db.refresh(case)

        return {"success": True, "case": case.to_dict()}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating case: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
