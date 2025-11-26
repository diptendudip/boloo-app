"""
Privacy Enforcement Middleware

This middleware ensures that personal diary entries (kind=PERSONAL) are:
- Never exposed in public feeds or queries
- Never visible in admin dashboards (unless explicitly filtered)
- Never accessible in entity views
- Only accessible by the creator

CRITICAL PRIVACY GUARANTEE:
Personal diary entries MUST remain 100% private to the user who created them.
This middleware acts as a final safety layer to prevent accidental data leaks.
"""

from fastapi import Request, HTTPException, status
from sqlalchemy.orm import Query
from typing import Optional
import logging
import uuid

from app.models.case import Case, CaseKind
from app.models.user import User

logger = logging.getLogger(__name__)


class PrivacyEnforcer:
    """
    Enforces privacy rules for personal diary entries.

    This class provides utilities to ensure personal cases are never
    exposed outside of their owner's context.
    """

    @staticmethod
    def filter_personal_cases(query: Query, current_user: Optional[User] = None) -> Query:
        """
        Filter out personal cases from a query unless the user is the owner.

        This should be applied to ALL case queries that could potentially
        return results to non-owners (public feeds, admin views, etc.)

        Args:
            query: SQLAlchemy query object
            current_user: Current authenticated user (if any)

        Returns:
            Query: Filtered query that excludes personal cases (or only shows user's own)

        Example:
            query = db.query(Case)
            query = PrivacyEnforcer.filter_personal_cases(query, current_user)
            cases = query.all()  # Will never include other users' personal notes
        """
        # If no user is authenticated, exclude ALL personal cases
        if not current_user:
            return query.filter(Case.kind != CaseKind.PERSONAL)

        # For authenticated users, exclude personal cases from OTHER users
        # This uses an OR condition:
        # - Show all non-personal cases
        # - OR show personal cases only if they belong to this user
        return query.filter(
            (Case.kind != CaseKind.PERSONAL) |
            ((Case.kind == CaseKind.PERSONAL) & (Case.user_id == current_user.id))
        )

    @staticmethod
    def ensure_personal_case_access(
        case: Case,
        current_user: User
    ) -> None:
        """
        Ensure the current user has access to a personal case.

        This MUST be called before returning any personal case data.
        Raises HTTP 403 if access is denied.

        Args:
            case: The case being accessed
            current_user: Current authenticated user

        Raises:
            HTTPException: 403 Forbidden if user doesn't own the personal case

        Example:
            case = db.query(Case).filter(Case.id == case_id).first()
            PrivacyEnforcer.ensure_personal_case_access(case, current_user)
            return case.to_dict()  # Safe to return now
        """
        if case.kind == CaseKind.PERSONAL and case.user_id != current_user.id:
            logger.warning(
                f"Privacy violation attempt: User {current_user.id} tried to access "
                f"personal case {case.id} owned by {case.user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Personal diary entries are private."
            )

    @staticmethod
    def validate_personal_case_creation(
        kind: CaseKind,
        is_public: Optional[bool],
        entity_id: Optional[uuid.UUID]
    ) -> tuple[bool, Optional[uuid.UUID]]:
        """
        Validate and enforce privacy settings for personal case creation.

        Personal cases MUST:
        - Have is_public = False
        - Have entity_id = None (not routed to any entity)

        This method enforces these rules regardless of what the client sends.

        Args:
            kind: The case kind (PERSONAL, GRIEVANCE, etc.)
            is_public: Requested public status (will be overridden for PERSONAL)
            entity_id: Requested entity routing (will be cleared for PERSONAL)

        Returns:
            tuple: (corrected_is_public, corrected_entity_id)

        Example:
            is_public, entity_id = PrivacyEnforcer.validate_personal_case_creation(
                kind=CaseKind.PERSONAL,
                is_public=True,  # Will be forced to False
                entity_id=some_uuid  # Will be forced to None
            )
            # is_public = False, entity_id = None
        """
        if kind == CaseKind.PERSONAL:
            # Force privacy settings for personal cases
            if is_public:
                logger.info("Forcing is_public=False for personal diary entry")
            if entity_id:
                logger.info("Clearing entity_id for personal diary entry")

            return False, None  # Always private, never routed

        # For non-personal cases, use the provided values
        return is_public if is_public is not None else False, entity_id

    @staticmethod
    def validate_case_visibility_in_list(
        cases: list[Case],
        current_user: Optional[User] = None
    ) -> list[Case]:
        """
        Filter a list of cases to remove personal entries that don't belong to the user.

        This is a safety check that should be applied to list responses.
        Ideally, the query should already be filtered, but this provides defense in depth.

        Args:
            cases: List of case objects
            current_user: Current authenticated user (if any)

        Returns:
            list[Case]: Filtered list with only visible cases

        Example:
            cases = db.query(Case).all()  # Might accidentally include personal cases
            cases = PrivacyEnforcer.validate_case_visibility_in_list(cases, current_user)
            # Now guaranteed safe to return
        """
        if not current_user:
            # No authenticated user: exclude ALL personal cases
            return [c for c in cases if c.kind != CaseKind.PERSONAL]

        # Filter out personal cases that don't belong to this user
        return [
            c for c in cases
            if c.kind != CaseKind.PERSONAL or c.user_id == current_user.id
        ]

    @staticmethod
    def log_privacy_access(
        case_id: uuid.UUID,
        user_id: uuid.UUID,
        action: str,
        success: bool
    ) -> None:
        """
        Log privacy-sensitive access for audit purposes.

        This helps detect potential privacy violations or suspicious access patterns.

        Args:
            case_id: UUID of the case being accessed
            user_id: UUID of the user attempting access
            action: Description of the action (e.g., "view", "update", "convert")
            success: Whether the access was granted
        """
        log_level = logging.INFO if success else logging.WARNING
        status_str = "granted" if success else "denied"

        logger.log(
            log_level,
            f"Privacy access {status_str}: User {user_id} attempted to {action} "
            f"personal case {case_id}"
        )


# Convenience functions for common use cases

def exclude_personal_from_query(
    query: Query,
    current_user: Optional[User] = None
) -> Query:
    """
    Convenience wrapper for PrivacyEnforcer.filter_personal_cases.
    Use this in routers to quickly add privacy filtering.

    Example:
        query = db.query(Case).filter(Case.status == "submitted")
        query = exclude_personal_from_query(query, current_user)
        cases = query.all()
    """
    return PrivacyEnforcer.filter_personal_cases(query, current_user)


def check_personal_case_access(case: Case, user: User) -> None:
    """
    Convenience wrapper for PrivacyEnforcer.ensure_personal_case_access.
    Use this before returning case details.

    Example:
        case = db.query(Case).filter(Case.id == case_id).first()
        check_personal_case_access(case, current_user)
        return case.to_dict()
    """
    PrivacyEnforcer.ensure_personal_case_access(case, user)
