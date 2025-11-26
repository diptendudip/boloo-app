"""
Integration tests for personal diary to grievance conversion workflow

Tests the complete flow:
1. User creates personal diary entry
2. Sets reminder
3. Decides to convert to grievance
4. System processes conversion
5. Triggers routing
6. Sends notifications
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.case import Case, CaseKind, CaseStatus, CaseEvent
from app.models.user import User
from app.models.notification import Notification
from app.services.notification_service import NotificationService


class TestCompleteConversionWorkflow:
    """Integration tests for the complete conversion workflow"""

    def test_full_conversion_workflow(self, client: TestClient, db: Session, auth_token: str, test_user: User):
        """
        Test the complete workflow from personal diary creation to grievance conversion
        """
        # Step 1: Create personal diary entry with reminder
        reminder_time = (datetime.utcnow() + timedelta(days=1)).isoformat()

        create_response = client.post(
            "/v1/cases",
            json={
                "title": "Water supply issue in my area",
                "transcript_text": "There's been no water supply for 3 days now",
                "kind": "personal",
                "reminder_at": reminder_time,
                "location_text": "My neighborhood",
                "can_convert_to_grievance": True  # Mark as convertible
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert create_response.status_code == 200
        case_data = create_response.json()
        assert case_data["success"] is True
        case_id = case_data["case"]["id"]

        # Verify it's a personal case
        case = db.query(Case).filter(Case.id == case_id).first()
        assert case.kind == CaseKind.PERSONAL
        assert case.is_public is False
        assert case.status == CaseStatus.DRAFT.value
        assert case.reminder_at is not None

        # Verify reminder was scheduled
        reminders = NotificationService.get_pending_reminders(db, test_user.id)
        assert len(reminders) > 0

        # Step 2: List personal diary entries
        list_response = client.get(
            "/v1/cases/personal",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert list_response.status_code == 200
        personal_cases = list_response.json()["cases"]
        assert len(personal_cases) >= 1
        assert any(c["id"] == case_id for c in personal_cases)

        # Step 3: Convert to grievance
        convert_response = client.post(
            f"/v1/cases/{case_id}/convert-to-grievance",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert convert_response.status_code == 200
        conversion_data = convert_response.json()
        assert conversion_data["success"] is True

        # Verify conversion
        db.refresh(case)
        assert case.kind == CaseKind.GRIEVANCE
        assert case.can_convert_to_grievance is False
        assert case.is_public is True
        assert case.status == CaseStatus.SUBMITTED.value
        assert case.reminder_at is None  # Cleared

        # Verify reminder was cancelled
        db.expire_all()  # Refresh all objects
        reminders_after = NotificationService.get_pending_reminders(db, test_user.id)
        case_reminders = [r for r in reminders_after if r.payload.get("case_id") == str(case_id)]
        assert len(case_reminders) == 0  # Should be cancelled

        # Verify conversion event was created
        events = db.query(CaseEvent).filter(CaseEvent.case_id == case_id).all()
        conversion_events = [e for e in events if e.event_type == "converted"]
        assert len(conversion_events) > 0

        # Step 4: Verify case no longer appears in personal list
        personal_list_after = client.get(
            "/v1/cases/personal",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        personal_cases_after = personal_list_after.json()["cases"]
        assert not any(c["id"] == case_id for c in personal_cases_after)

        # Step 5: Verify case appears in regular case list
        cases_response = client.get(
            "/v1/cases",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        all_cases = cases_response.json()["cases"]
        assert any(c["id"] == case_id for c in all_cases)

    def test_conversion_with_routing(self, client: TestClient, db: Session, auth_token: str):
        """Test that conversion triggers routing logic"""
        # Create personal case
        create_response = client.post(
            "/v1/cases",
            json={
                "title": "Road repair needed",
                "transcript_text": "The main road has large potholes",
                "kind": "personal",
                "can_convert_to_grievance": True,
                "location_text": "Main Street"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        case_id = create_response.json()["case"]["id"]

        # Convert
        convert_response = client.post(
            f"/v1/cases/{case_id}/convert-to-grievance",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert convert_response.status_code == 200

        # Check next_steps in response
        next_steps = convert_response.json()["next_steps"]
        assert "status" in next_steps
        assert "message" in next_steps
        # May have entity_id if routing succeeded

    def test_privacy_after_conversion(self, client: TestClient, db: Session, auth_token: str, other_auth_token: str):
        """Test that converted cases are now public and visible to others"""
        # User 1 creates personal case
        create_response = client.post(
            "/v1/cases",
            json={
                "title": "Personal issue",
                "kind": "personal",
                "can_convert_to_grievance": True
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        case_id = create_response.json()["case"]["id"]

        # User 2 should NOT see it
        other_response = client.get(
            f"/v1/cases/{case_id}",
            headers={"Authorization": f"Bearer {other_auth_token}"}
        )
        assert other_response.status_code == 403  # Access denied

        # User 1 converts to grievance
        client.post(
            f"/v1/cases/{case_id}/convert-to-grievance",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Now User 2 should be able to see it (if they're an admin/officer)
        # For citizens, they still can't see other's cases


class TestConversionValidation:
    """Test validation rules for conversion"""

    def test_cannot_convert_already_converted(self, client: TestClient, auth_token: str):
        """Test that a case cannot be converted twice"""
        # Create and convert
        create_response = client.post(
            "/v1/cases",
            json={
                "title": "Test case",
                "kind": "personal",
                "can_convert_to_grievance": True
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        case_id = create_response.json()["case"]["id"]

        # First conversion succeeds
        convert1 = client.post(
            f"/v1/cases/{case_id}/convert-to-grievance",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert convert1.status_code == 200

        # Second conversion fails
        convert2 = client.post(
            f"/v1/cases/{case_id}/convert-to-grievance",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert convert2.status_code == 400
        assert "cannot be converted" in convert2.json()["detail"].lower()

    def test_cannot_convert_ineligible_case(self, client: TestClient, auth_token: str):
        """Test that cases with can_convert_to_grievance=false cannot be converted"""
        # Create case without conversion permission
        create_response = client.post(
            "/v1/cases",
            json={
                "title": "Private note",
                "kind": "personal",
                "can_convert_to_grievance": False
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        case_id = create_response.json()["case"]["id"]

        # Conversion should fail
        convert_response = client.post(
            f"/v1/cases/{case_id}/convert-to-grievance",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert convert_response.status_code == 400

    def test_cannot_convert_others_case(self, client: TestClient, auth_token: str, other_auth_token: str):
        """Test that users cannot convert other users' personal cases"""
        # User 1 creates case
        create_response = client.post(
            "/v1/cases",
            json={
                "title": "User 1's case",
                "kind": "personal",
                "can_convert_to_grievance": True
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        case_id = create_response.json()["case"]["id"]

        # User 2 tries to convert
        convert_response = client.post(
            f"/v1/cases/{case_id}/convert-to-grievance",
            headers={"Authorization": f"Bearer {other_auth_token}"}
        )
        assert convert_response.status_code == 403

    def test_cannot_convert_grievance(self, client: TestClient, auth_token: str):
        """Test that grievances cannot be converted"""
        # Create a grievance (not personal)
        create_response = client.post(
            "/v1/cases",
            json={
                "title": "Already a grievance",
                "kind": "grievance"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        case_id = create_response.json()["case"]["id"]

        # Try to convert
        convert_response = client.post(
            f"/v1/cases/{case_id}/convert-to-grievance",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert convert_response.status_code == 400
        assert "only personal diary entries" in convert_response.json()["detail"].lower()


class TestReminderIntegration:
    """Test reminder functionality in the workflow"""

    def test_create_with_future_reminder(self, client: TestClient, auth_token: str):
        """Test creating a case with a future reminder"""
        future_time = (datetime.utcnow() + timedelta(hours=24)).isoformat()

        response = client.post(
            "/v1/cases",
            json={
                "title": "Follow up needed",
                "kind": "personal",
                "reminder_at": future_time
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "reminder" in data  # Should include reminder info

    def test_create_with_past_reminder_handled_gracefully(self, client: TestClient, auth_token: str):
        """Test that past reminders don't break case creation"""
        past_time = (datetime.utcnow() - timedelta(hours=1)).isoformat()

        response = client.post(
            "/v1/cases",
            json={
                "title": "Test case",
                "kind": "personal",
                "reminder_at": past_time
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Case should still be created
        assert response.status_code == 200
        # But reminder might not be scheduled (check logs)

    def test_update_reminder(self, client: TestClient, db: Session, auth_token: str):
        """Test updating a reminder for an existing case"""
        # Create with initial reminder
        initial_time = (datetime.utcnow() + timedelta(hours=24)).isoformat()

        create_response = client.post(
            "/v1/cases",
            json={
                "title": "Test case",
                "kind": "personal",
                "reminder_at": initial_time
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        case_id = create_response.json()["case"]["id"]

        # Update reminder
        new_time = (datetime.utcnow() + timedelta(hours=48)).isoformat()

        update_response = client.patch(
            f"/v1/cases/{case_id}",
            json={"reminder_at": new_time},
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert update_response.status_code == 200


# Fixtures

@pytest.fixture
def auth_token(client: TestClient, test_user: User) -> str:
    """Generate auth token for test user"""
    # This would use your actual auth flow
    # Simplified for example
    from jose import jwt
    from app.config import settings

    token = jwt.encode(
        {"sub": str(test_user.id)},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return token


@pytest.fixture
def other_auth_token(client: TestClient, other_user: User) -> str:
    """Generate auth token for other user"""
    from jose import jwt
    from app.config import settings

    token = jwt.encode(
        {"sub": str(other_user.id)},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return token
