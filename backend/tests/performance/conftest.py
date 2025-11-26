"""
Pytest configuration for performance tests.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.user import User
from app.models.conversation import Conversation
from app.models.conversation_turn import ConversationTurn
import uuid
from datetime import datetime


@pytest.fixture(scope="session")
def performance_db_engine():
    """Create in-memory database for performance tests"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def performance_db_session(performance_db_engine):
    """Create database session for each test"""
    Session = sessionmaker(bind=performance_db_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def test_user(performance_db_session):
    """Create test user"""
    user = User(
        id=uuid.uuid4(),
        phone="+919876543210",
        name="Test User",
        is_active=True
    )
    performance_db_session.add(user)
    performance_db_session.commit()
    return user


@pytest.fixture
def create_test_conversation(performance_db_session, test_user):
    """Factory function to create conversations with N turns"""

    def _create_conversation(num_turns: int = 10):
        """Create conversation with specified number of turns"""
        conversation = Conversation(
            id=uuid.uuid4(),
            user_id=test_user.id,
            turn_count=num_turns,
            is_complete=False,
            completeness_score=0.5,
            collected_fields=["location"],
            missing_fields=[{"field": "issue_description", "importance": "critical"}],
            extracted_data={"location": "Raipur"}
        )
        performance_db_session.add(conversation)
        performance_db_session.commit()

        # Add turns
        for i in range(num_turns):
            turn = ConversationTurn(
                id=uuid.uuid4(),
                conversation_id=conversation.id,
                turn_number=i + 1,
                transcript_text=f"यह टर्न नंबर {i+1} का संदेश है। पानी की समस्या के बारे में बात कर रहा हूं।",
                ai_response=f"धन्यवाद! आपकी समस्या समझ में आई। कृपया और जानकारी दें।",
                ai_question_asked=f"कृपया बताइए कि समस्या कहां है? (टर्न {i+1})",
                language_detected="hi",
                intent="grievance",
                confidence=0.85,
                fields_extracted={"location": f"Area_{i+1}"},
                created_at=datetime.utcnow()
            )
            performance_db_session.add(turn)

        performance_db_session.commit()
        performance_db_session.refresh(conversation)

        return conversation

    return _create_conversation
