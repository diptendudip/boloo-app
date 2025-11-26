"""
SQLAlchemy models for Boloo application
"""

from app.models.user import User
from app.models.entity import Entity
from app.models.taxonomy import Taxonomy
from app.models.case import Case, CaseEvent, CaseKind, TriageIntent
from app.models.case_sla_tracking import CaseSLATracking
from app.models.community_post import CommunityPost
from app.models.otp import OTP
from app.models.notification import Notification
from app.models.flag import Flag
from app.models.audit_log import AuditLog
from app.models.metric import Metric
from app.models.resource_health import (
    ResourceHealth,
    HealthCheckLog,
    ResourceType,
    ResourceCategory,
    HealthStatus
)
# AI Coach Onboarding models (Phase 2D)
from app.models.conversation import Conversation
from app.models.conversation_turn import ConversationTurn

# Social Feed models
from app.models.feed_post import FeedPost, FeedVisibility
from app.models.feed_like import FeedLike
from app.models.feed_comment import FeedComment
from app.models.feed_share import FeedShare

__all__ = [
    "User",
    "Entity",
    "Taxonomy",
    "Case",
    "CaseEvent",
    "CaseKind",
    "TriageIntent",
    "CaseSLATracking",
    "CommunityPost",
    "OTP",
    "Notification",
    "Flag",
    "AuditLog",
    "Metric",
    "ResourceHealth",
    "HealthCheckLog",
    "ResourceType",
    "ResourceCategory",
    "HealthStatus",
    "Conversation",
    "ConversationTurn",
    # Feed models
    "FeedPost",
    "FeedVisibility",
    "FeedLike",
    "FeedComment",
    "FeedShare",
]
