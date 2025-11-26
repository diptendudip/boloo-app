"""
Next Steps API Router

Provides "Agla Kya Hoga?" (What Happens Next) information for cases.
Returns SLA tracking, responsible entities, escalation paths, and updates.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging
from datetime import datetime, timedelta

from app.database import get_db
from app.models.case import Case, CaseStatus
from app.models.entity import Entity
from app.services.sla_service import SLAService
from app.services.routing_service import RoutingService

router = APIRouter(prefix="/cases", tags=["next-steps"])
logger = logging.getLogger(__name__)


def _get_dummy_next_steps(case_id: str) -> Dict[str, Any]:
    """Return dummy next steps for offline testing cases."""
    now = datetime.utcnow()
    created_at = now - timedelta(minutes=5)

    # Extract reference from case ID (e.g., "real-case-1761622130709" -> "BOL22130709")
    timestamp_part = case_id.split("-")[-1][-8:] if "-" in case_id else "12345678"
    reference = f"BOL{timestamp_part}"

    return {
        "success": True,
        "next_steps": {
            "case_id": case_id,
            "case_reference": reference,
            "status": "pending",
            "created_at": created_at.isoformat(),
            "updated_at": now.isoformat(),
            "responsible_entity": {
                "type": "municipal_corporation",
                "name": "रायपुर नगर निगम",
                "contact_phone": "+91-771-2535353",
                "office_location": "Raipur Municipal Corporation, Civil Lines, Raipur",
                "jurisdiction": "Raipur City"
            },
            "sla": {
                "sla_hours": 72,
                "elapsed_hours": 0,
                "remaining_hours": 72,
                "percentage_used": 0,
                "is_escalated": False,
                "escalation_level": 0
            },
            "escalation_path": {
                "current": "रायपुर नगर निगम - वार्ड अधिकारी",
                "next": "सहायक आयुक्त",
                "escalates_at": (now + timedelta(hours=72)).isoformat(),
                "escalation_reason": "SLA timeout"
            },
            "expected_actions": [
                "🧪 TESTING MODE: आपकी शिकायत की समीक्षा की जाएगी",
                "प्राथमिकता निर्धारित की जाएगी",
                "आपको पावती संदेश मिलेगा (24 घंटे में)"
            ],
            "citizen_actions": [
                "स्थिति पर नज़र रखें",
                "अपडेट के लिए चेक करें",
                "यदि आवश्यक हो तो अतिरिक्त जानकारी प्रदान करें"
            ],
            "updates": [
                {
                    "id": f"{case_id}_created",
                    "timestamp": created_at.isoformat(),
                    "message": "🧪 शिकायत दर्ज की गई (Testing Mode - Offline)",
                    "actor": {"type": "citizen"}
                },
                {
                    "id": f"{case_id}_received",
                    "timestamp": now.isoformat(),
                    "message": "शिकायत प्राप्त हुई और समीक्षा के लिए भेजी गई",
                    "actor": {"type": "system"}
                }
            ]
        }
    }


@router.get("/{case_id}/next-steps")
async def get_case_next_steps(
    case_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get detailed next steps information for a case.

    Returns "Agla Kya Hoga?" (What Happens Next) card data including:
    - Responsible entity (office/official handling the case)
    - SLA countdown and escalation timeline
    - Expected actions from officials
    - Required actions from citizen
    - Case updates and timeline

    Args:
        case_id: Case ID
        user_id: Current user ID
        db: Database session

    Returns:
        Next steps information with SLA tracking

    Raises:
        HTTPException: If case not found or access denied
    """
    try:
        # TESTING MODE: Support offline cases (test-case-* or real-case-*)
        if case_id.startswith(("test-case-", "real-case-")):
            logger.info(f"[TESTING MODE] Returning dummy next steps for offline case: {case_id}")
            return _get_dummy_next_steps(case_id)

        # Get case from database
        case = db.query(Case).filter(Case.id == case_id).first()

        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found",
            )

        logger.info(f"Fetching next steps for case {case_id}")

        # Initialize services
        sla_service = SLAService(db)
        routing_service = RoutingService(db)

        # Get SLA status
        sla_status = sla_service.get_sla_status(str(case.id))

        # Get responsible entity
        if case.entity_id:
            entity = db.query(Entity).filter(Entity.id == case.entity_id).first()
            responsible_entity = {
                "type": entity.type if entity else "municipal_corporation",
                "name": entity.name if entity else "Unknown Entity",
                "contact_phone": entity.contact_phone if entity else None,
                "office_location": entity.address if entity else None,
                "jurisdiction": entity.jurisdiction if entity and hasattr(entity, 'jurisdiction') else None,
            }
        else:
            # Fallback if no entity assigned yet
            responsible_entity = {
                "type": "municipal_corporation",
                "name": "रायपुर नगर निगम",
                "contact_phone": "+91-771-2535353",
                "office_location": "Raipur Municipal Corporation, Civil Lines, Raipur",
                "jurisdiction": "Raipur City"
            }

        # Calculate SLA information
        if sla_status.get("active"):
            sla_info = {
                "sla_hours": sla_status.get("sla_hours", 72),
                "elapsed_hours": sla_status.get("sla_hours", 72) - sla_status.get("time_remaining_hours", 72),
                "remaining_hours": sla_status.get("time_remaining_hours", 72),
                "percentage_used": sla_status.get("progress_percentage", 0),
                "is_escalated": sla_status.get("escalation_level", 0) > 0,
                "escalation_level": sla_status.get("escalation_level", 0),
            }
        else:
            # Calculate basic SLA if no tracking exists
            elapsed_hours = int((datetime.utcnow() - case.created_at).total_seconds() / 3600)
            default_sla_hours = 72
            sla_info = {
                "sla_hours": default_sla_hours,
                "elapsed_hours": elapsed_hours,
                "remaining_hours": max(0, default_sla_hours - elapsed_hours),
                "percentage_used": min(100, int((elapsed_hours / default_sla_hours) * 100)),
                "is_escalated": False,
                "escalation_level": 0,
            }

        # Get escalation path
        if case.entity_id:
            entity = db.query(Entity).filter(Entity.id == case.entity_id).first()
            escalation_entity = routing_service.get_escalation_entity(entity) if entity else None

            escalation_path = {
                "current": responsible_entity["name"],
                "next": escalation_entity.name if escalation_entity else None,
                "escalates_at": (datetime.utcnow() + timedelta(hours=sla_info["remaining_hours"])).isoformat() if sla_info["remaining_hours"] > 0 else None,
                "escalation_reason": "SLA timeout" if sla_info["remaining_hours"] <= 0 else None,
            }
        else:
            escalation_path = {
                "current": responsible_entity["name"],
                "next": "सहायक आयुक्त",
                "escalates_at": (datetime.utcnow() + timedelta(hours=sla_info["remaining_hours"])).isoformat() if sla_info["remaining_hours"] > 0 else None,
                "escalation_reason": "SLA timeout" if sla_info["remaining_hours"] <= 0 else None,
            }

        # Generate expected actions based on case status
        expected_actions = _generate_expected_actions(case, responsible_entity)

        # Generate citizen actions if needed
        citizen_actions = _generate_citizen_actions(case)

        # Get recent updates
        updates = _get_case_updates(case, db)

        # Generate reference number if not available
        case_reference = f"BOL{str(case.id)[:8].upper()}"

        return {
            "success": True,
            "next_steps": {
                "case_id": str(case.id),
                "case_reference": case_reference,
                "status": case.status,
                "created_at": case.created_at.isoformat(),
                "updated_at": case.updated_at.isoformat(),
                "responsible_entity": {
                    "type": responsible_entity["type"],
                    "name": responsible_entity["name"],
                    "contact_phone": responsible_entity.get("contact_phone"),
                    "office_location": responsible_entity.get("office_location"),
                    "jurisdiction": responsible_entity.get("jurisdiction"),
                },
                "sla": {
                    "sla_hours": sla_info["sla_hours"],
                    "elapsed_hours": sla_info["elapsed_hours"],
                    "remaining_hours": sla_info["remaining_hours"],
                    "percentage_used": sla_info["percentage_used"],
                    "is_escalated": sla_info["is_escalated"],
                    "escalation_level": sla_info["escalation_level"],
                },
                "escalation_path": {
                    "current": escalation_path["current"],
                    "next": escalation_path.get("next"),
                    "escalates_at": escalation_path.get("escalates_at"),
                    "escalation_reason": escalation_path.get("escalation_reason"),
                },
                "expected_actions": expected_actions,
                "citizen_actions": citizen_actions,
                "updates": updates,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching next steps for case {case_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch next steps information",
        )


def _generate_expected_actions(case: Case, responsible_entity: Dict[str, Any]) -> list:
    """Generate expected actions based on case status."""
    entity_name = responsible_entity["name"]

    if case.status == CaseStatus.OPEN:
        return [
            f"{entity_name} आपकी शिकायत की समीक्षा करेंगे",
            "प्राथमिकता निर्धारित की जाएगी",
            "आपको पावती संदेश मिलेगा",
        ]
    elif case.status == CaseStatus.IN_PROGRESS:
        return [
            f"{entity_name} समस्या का निरीक्षण करेंगे",
            "आवश्यक कार्रवाई शुरू की जाएगी",
            "प्रगति का अपडेट मिलेगा",
        ]
    elif case.status == CaseStatus.WAITING_INFO:
        return [
            "अधिक जानकारी के लिए प्रतीक्षा",
            "आपसे संपर्क किया जा सकता है",
            "आवश्यक दस्तावेज़ या फोटो मांगे जा सकते हैं",
        ]
    elif case.status == CaseStatus.RESOLVED:
        return [
            "समाधान पूर्ण हो गया है",
            "कृपया पुष्टि करें कि समस्या ठीक हो गई है",
            "फीडबैक दें",
        ]
    elif case.status == CaseStatus.ESCALATED:
        return [
            f"केस को {responsible_entity['name']} को भेजा गया है",
            "उच्च प्राथमिकता के साथ समीक्षा की जाएगी",
            "तेज़ कार्रवाई अपेक्षित है",
        ]
    else:
        return ["स्थिति अपडेट का इंतज़ार करें"]


def _generate_citizen_actions(case: Case) -> list:
    """Generate required citizen actions if any."""
    actions = []

    if case.status == CaseStatus.WAITING_INFO:
        actions.append("अतिरिक्त जानकारी या दस्तावेज़ प्रदान करें")

    if case.status == CaseStatus.RESOLVED:
        actions.append("समाधान की पुष्टि करें")
        actions.append("अपना अनुभव साझा करें")

    # Always available actions
    if case.status not in [CaseStatus.CLOSED, CaseStatus.RESOLVED]:
        actions.append("स्थिति पर नज़र रखें और अपडेट के लिए चेक करें")

    return actions


def _get_case_updates(case: Case, db: Session) -> list:
    """Get recent case updates."""
    # This would typically query a CaseUpdate table
    # For now, return basic updates from case history

    updates = []

    # Add creation update
    updates.append({
        "id": f"{case.id}_created",
        "timestamp": case.created_at.isoformat(),
        "message": "शिकायत दर्ज की गई",
        "actor": {
            "type": "system",
        },
    })

    # Add status change updates
    if case.status != CaseStatus.DRAFT.value:
        updates.append({
            "id": f"{case.id}_status_change",
            "timestamp": case.updated_at.isoformat(),
            "message": f"स्थिति बदली: {case.status}",
            "status_change": {
                "from": "DRAFT",
                "to": case.status,
            },
            "actor": {
                "type": "official",
            },
        })

    # Add escalation update if escalated
    if case.case_metadata and case.case_metadata.get("escalated"):
        escalation_data = case.case_metadata["escalated"]
        updates.append({
            "id": f"{case.id}_escalated",
            "timestamp": escalation_data.get("timestamp", case.updated_at.isoformat()),
            "message": f"उच्च कार्यालय को भेजा गया: {escalation_data.get('reason', 'SLA timeout')}",
            "actor": {
                "type": "system",
            },
        })

    return sorted(updates, key=lambda x: x["timestamp"], reverse=True)


@router.get("/{case_id}/timeline")
async def get_case_timeline(
    case_id: str,
    limit: int = 10,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get detailed timeline of case events.

    Returns chronological list of all case updates, actions, and changes.

    Args:
        case_id: Case ID
        limit: Maximum number of events to return
        user_id: Current user ID
        db: Database session

    Returns:
        Case timeline with events

    Raises:
        HTTPException: If case not found
    """
    try:
        # TESTING MODE: Support offline cases
        if case_id.startswith(("test-case-", "real-case-")):
            logger.info(f"[TESTING MODE] Returning dummy timeline for offline case: {case_id}")
            dummy_steps = _get_dummy_next_steps(case_id)
            return {
                "success": True,
                "case_id": case_id,
                "case_reference": dummy_steps["next_steps"]["case_reference"],
                "timeline": dummy_steps["next_steps"]["updates"][:limit],
                "total_events": len(dummy_steps["next_steps"]["updates"])
            }

        # Get case from database
        case = db.query(Case).filter(Case.id == case_id).first()

        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found",
            )

        # Get all updates
        updates = _get_case_updates(case, db)

        # Generate reference number if not available
        case_reference = f"BOL{str(case.id)[:8].upper()}"

        return {
            "success": True,
            "case_id": str(case.id),
            "case_reference": case_reference,
            "timeline": updates[:limit],
            "total_events": len(updates),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching timeline for case {case_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch case timeline",
        )
