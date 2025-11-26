"""
Feed Router - Social feed system for Boloo app
Enables users to share cases publicly, like, comment, and engage with community content
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case, desc, and_, or_
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from geoalchemy2.elements import WKTElement
import logging
import uuid

from app.database import get_db
from app.models.case import Case, CaseKind, CaseStatus
from app.models.user import User
from app.utils.auth import get_current_user_or_dev

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class FeedPostCreate(BaseModel):
    """Create a new feed post by sharing a case publicly"""
    case_id: str = Field(..., description="Case ID to share publicly")
    is_anonymous: bool = Field(default=False, description="Share anonymously")
    caption: Optional[str] = Field(None, description="Optional caption for the post")


class CommentCreate(BaseModel):
    """Create a comment on a feed post"""
    content: str = Field(..., min_length=1, max_length=1000, description="Comment content")


class FeedResponse(BaseModel):
    """Standard feed response"""
    success: bool
    data: Optional[dict] = None
    message: str


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_engagement_score(likes: int, comments: int, shares: int) -> float:
    """
    Calculate engagement score for ranking algorithm
    Weighted combination of likes, comments, and shares
    """
    return (likes * 1.0) + (comments * 2.0) + (shares * 3.0)


def calculate_recency_score(created_at: datetime) -> float:
    """
    Calculate recency score (newer posts score higher)
    Uses exponential decay: score = e^(-hours_old / 24)
    """
    import math
    hours_old = (datetime.utcnow() - created_at).total_seconds() / 3600
    decay_rate = 24.0  # Half-life of 24 hours
    return math.exp(-hours_old / decay_rate) * 100


def calculate_proximity_score(
    post_lat: Optional[float],
    post_lng: Optional[float],
    user_lat: Optional[float],
    user_lng: Optional[float]
) -> float:
    """
    Calculate proximity score based on distance
    Returns higher score for closer locations
    """
    if not all([post_lat, post_lng, user_lat, user_lng]):
        return 0.0

    import math
    # Haversine formula to calculate distance
    R = 6371  # Earth's radius in km

    lat1, lon1 = math.radians(post_lat), math.radians(post_lng)
    lat2, lon2 = math.radians(user_lat), math.radians(user_lng)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    distance_km = R * c

    # Score: 100 for same location, decreases with distance
    # Max relevant distance: 50km
    if distance_km > 50:
        return 0.0
    return max(0, 100 - (distance_km * 2))


def calculate_relevance_score(
    post_issue_type: Optional[str],
    user_recent_issue_types: List[str]
) -> float:
    """
    Calculate relevance score based on issue type matching
    Returns higher score if user has interacted with similar issues
    """
    if not post_issue_type or not user_recent_issue_types:
        return 0.0

    if post_issue_type in user_recent_issue_types:
        return 50.0
    return 0.0


def get_user_location(db: Session, user_id: uuid.UUID) -> tuple:
    """Get user's location from their most recent case"""
    recent_case = db.query(Case).filter(
        Case.user_id == user_id,
        Case.location_point.isnot(None)
    ).order_by(Case.created_at.desc()).first()

    if recent_case and recent_case.location_point:
        point = to_shape(recent_case.location_point)
        return (point.y, point.x)  # (lat, lng)
    return (None, None)


def get_user_recent_issue_types(db: Session, user_id: uuid.UUID) -> List[str]:
    """Get issue types from user's recent cases"""
    recent_cases = db.query(Case.issue_type).filter(
        Case.user_id == user_id,
        Case.issue_type.isnot(None)
    ).order_by(Case.created_at.desc()).limit(10).all()

    return [c.issue_type for c in recent_cases if c.issue_type]


# ============================================================================
# DATABASE HELPERS (Simulated with Case metadata until proper tables exist)
# ============================================================================

def get_post_likes_count(db: Session, case_id: uuid.UUID) -> int:
    """Get total likes for a case/post"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case or not case.case_metadata:
        return 0
    return case.case_metadata.get("feed_likes_count", 0)


def get_post_comments_count(db: Session, case_id: uuid.UUID) -> int:
    """Get total comments for a case/post"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case or not case.case_metadata:
        return 0
    return case.case_metadata.get("feed_comments_count", 0)


def get_post_shares_count(db: Session, case_id: uuid.UUID) -> int:
    """Get total shares for a case/post"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case or not case.case_metadata:
        return 0
    return case.case_metadata.get("feed_shares_count", 0)


def has_user_liked(db: Session, case_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    """Check if user has liked a post"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case or not case.case_metadata:
        return False
    likes_list = case.case_metadata.get("feed_likes", [])
    return str(user_id) in likes_list


def add_like(db: Session, case_id: uuid.UUID, user_id: uuid.UUID):
    """Add a like to a post"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="केस नहीं मिला (Case not found)")

    if not case.case_metadata:
        case.case_metadata = {}

    likes_list = case.case_metadata.get("feed_likes", [])
    if str(user_id) not in likes_list:
        likes_list.append(str(user_id))
        case.case_metadata["feed_likes"] = likes_list
        case.case_metadata["feed_likes_count"] = len(likes_list)
        db.commit()


def remove_like(db: Session, case_id: uuid.UUID, user_id: uuid.UUID):
    """Remove a like from a post"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        return

    if not case.case_metadata:
        return

    likes_list = case.case_metadata.get("feed_likes", [])
    if str(user_id) in likes_list:
        likes_list.remove(str(user_id))
        case.case_metadata["feed_likes"] = likes_list
        case.case_metadata["feed_likes_count"] = len(likes_list)
        db.commit()


def add_comment(db: Session, case_id: uuid.UUID, user_id: uuid.UUID, content: str) -> dict:
    """Add a comment to a post"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="केस नहीं मिला (Case not found)")

    if not case.case_metadata:
        case.case_metadata = {}

    comments_list = case.case_metadata.get("feed_comments", [])
    comment = {
        "id": str(uuid.uuid4()),
        "user_id": str(user_id),
        "content": content,
        "created_at": datetime.utcnow().isoformat()
    }
    comments_list.append(comment)
    case.case_metadata["feed_comments"] = comments_list
    case.case_metadata["feed_comments_count"] = len(comments_list)
    db.commit()

    return comment


def get_comments(db: Session, case_id: uuid.UUID, skip: int = 0, limit: int = 20) -> List[dict]:
    """Get comments for a post"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case or not case.case_metadata:
        return []

    comments = case.case_metadata.get("feed_comments", [])
    # Sort by created_at descending (newest first)
    comments.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return comments[skip:skip+limit]


def add_share(db: Session, case_id: uuid.UUID, user_id: uuid.UUID):
    """Add a share to a post"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="केस नहीं मिला (Case not found)")

    if not case.case_metadata:
        case.case_metadata = {}

    shares_list = case.case_metadata.get("feed_shares", [])
    share_entry = {
        "user_id": str(user_id),
        "shared_at": datetime.utcnow().isoformat()
    }
    shares_list.append(share_entry)
    case.case_metadata["feed_shares"] = shares_list
    case.case_metadata["feed_shares_count"] = len(shares_list)
    db.commit()


def enrich_post_with_user_data(db: Session, case: Case, current_user: User) -> dict:
    """
    Enrich case data with user information and engagement metrics
    Handles anonymous posts
    """
    post_dict = case.to_dict()

    # Check if post is anonymous
    is_anonymous = case.case_metadata.get("feed_is_anonymous", False) if case.case_metadata else False

    # Get user data (mask if anonymous)
    if is_anonymous:
        post_dict["user"] = {
            "id": None,
            "name": "गुमनाम उपयोगकर्ता (Anonymous User)",
            "is_anonymous": True
        }
    else:
        user = db.query(User).filter(User.id == case.user_id).first()
        if user:
            post_dict["user"] = {
                "id": str(user.id),
                "name": user.name or "उपयोगकर्ता (User)",
                "is_anonymous": False
            }

    # Add engagement metrics
    post_dict["engagement"] = {
        "likes_count": get_post_likes_count(db, case.id),
        "comments_count": get_post_comments_count(db, case.id),
        "shares_count": get_post_shares_count(db, case.id),
        "has_liked": has_user_liked(db, case.id, current_user.id) if current_user else False
    }

    # Add caption if exists
    post_dict["caption"] = case.case_metadata.get("feed_caption") if case.case_metadata else None

    return post_dict


# ============================================================================
# FEED ENDPOINTS
# ============================================================================

@router.get("", response_model=FeedResponse)
async def get_feed(
    skip: int = Query(0, ge=0, description="Number of posts to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of posts to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_dev)
):
    """
    Get personalized feed with ranking algorithm

    Ranking factors:
    - Recency: Newer posts score higher (exponential decay)
    - Engagement: Likes + Comments + Shares (weighted)
    - Proximity: Posts from nearby locations score higher
    - Relevance: Posts matching user's interest (issue types)

    Returns:
        Feed posts sorted by combined ranking score
    """
    try:
        # Get user's location and interests for personalization
        user_lat, user_lng = get_user_location(db, current_user.id)
        user_interests = get_user_recent_issue_types(db, current_user.id)

        # Query public cases (feed posts)
        # Include grievances and community stories, exclude personal
        query = db.query(Case).filter(
            Case.is_public == True,
            Case.kind.in_([CaseKind.GRIEVANCE.value, CaseKind.COMMUNITY_STORY.value]),
            Case.status.notin_([CaseStatus.DRAFT.value, CaseStatus.REJECTED.value])
        )

        # Get all posts for ranking
        all_posts = query.all()

        # Calculate ranking scores for each post
        ranked_posts = []
        for post in all_posts:
            # Extract location
            post_lat, post_lng = None, None
            if post.location_point:
                point = to_shape(post.location_point)
                post_lat, post_lng = point.y, point.x

            # Calculate individual scores
            recency_score = calculate_recency_score(post.created_at)
            engagement_score = calculate_engagement_score(
                get_post_likes_count(db, post.id),
                get_post_comments_count(db, post.id),
                get_post_shares_count(db, post.id)
            )
            proximity_score = calculate_proximity_score(post_lat, post_lng, user_lat, user_lng)
            relevance_score = calculate_relevance_score(post.issue_type, user_interests)

            # Combined ranking score (weighted)
            # Recency: 40%, Engagement: 30%, Proximity: 20%, Relevance: 10%
            total_score = (
                recency_score * 0.4 +
                engagement_score * 0.3 +
                proximity_score * 0.2 +
                relevance_score * 0.1
            )

            ranked_posts.append({
                "post": post,
                "score": total_score
            })

        # Sort by score descending
        ranked_posts.sort(key=lambda x: x["score"], reverse=True)

        # Apply pagination
        paginated_posts = ranked_posts[skip:skip+limit]

        # Enrich with user data and engagement
        enriched_posts = [
            enrich_post_with_user_data(db, item["post"], current_user)
            for item in paginated_posts
        ]

        logger.info(f"User {current_user.id} fetched {len(enriched_posts)} feed posts")

        return FeedResponse(
            success=True,
            data={
                "posts": enriched_posts,
                "total": len(ranked_posts),
                "skip": skip,
                "limit": limit
            },
            message="फीड सफलतापूर्वक लोड किया गया (Feed loaded successfully)"
        )

    except Exception as e:
        logger.error(f"Error fetching feed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"फीड लोड करने में त्रुटि (Error loading feed): {str(e)}"
        )


@router.post("/posts", response_model=FeedResponse)
async def create_feed_post(
    post_data: FeedPostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_dev)
):
    """
    Share a case publicly on the feed

    Creates a feed post by making a case public.
    Users can choose to post anonymously.

    Args:
        post_data: Case ID, anonymity preference, and optional caption

    Returns:
        Created feed post with engagement metrics
    """
    try:
        # Get the case
        case = db.query(Case).filter(Case.id == post_data.case_id).first()

        if not case:
            raise HTTPException(
                status_code=404,
                detail="केस नहीं मिला (Case not found)"
            )

        # Verify ownership
        if case.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="आप केवल अपने केस शेयर कर सकते हैं (You can only share your own cases)"
            )

        # Cannot share personal diary entries
        if case.kind == CaseKind.PERSONAL.value:
            raise HTTPException(
                status_code=400,
                detail="व्यक्तिगत डायरी प्रविष्टियां साझा नहीं की जा सकतीं। कृपया पहले शिकायत में बदलें। (Personal diary entries cannot be shared. Please convert to grievance first.)"
            )

        # Make case public
        case.is_public = True

        # Store feed metadata
        if not case.case_metadata:
            case.case_metadata = {}

        case.case_metadata["feed_is_anonymous"] = post_data.is_anonymous
        if post_data.caption:
            case.case_metadata["feed_caption"] = post_data.caption
        case.case_metadata["feed_shared_at"] = datetime.utcnow().isoformat()

        # Initialize engagement counters
        if "feed_likes_count" not in case.case_metadata:
            case.case_metadata["feed_likes_count"] = 0
            case.case_metadata["feed_likes"] = []
        if "feed_comments_count" not in case.case_metadata:
            case.case_metadata["feed_comments_count"] = 0
            case.case_metadata["feed_comments"] = []
        if "feed_shares_count" not in case.case_metadata:
            case.case_metadata["feed_shares_count"] = 0
            case.case_metadata["feed_shares"] = []

        db.commit()
        db.refresh(case)

        logger.info(f"User {current_user.id} shared case {case.id} on feed (anonymous={post_data.is_anonymous})")

        return FeedResponse(
            success=True,
            data=enrich_post_with_user_data(db, case, current_user),
            message="पोस्ट सफलतापूर्वक साझा किया गया (Post shared successfully)"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating feed post: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"पोस्ट बनाने में त्रुटि (Error creating post): {str(e)}"
        )


@router.post("/posts/{post_id}/like", response_model=FeedResponse)
async def like_post(
    post_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_dev)
):
    """
    Like a feed post

    Toggle like: If already liked, removes like. If not liked, adds like.

    Args:
        post_id: UUID of the post (case) to like

    Returns:
        Updated like status
    """
    try:
        case_id = uuid.UUID(post_id)

        # Verify case exists and is public
        case = db.query(Case).filter(
            Case.id == case_id,
            Case.is_public == True
        ).first()

        if not case:
            raise HTTPException(
                status_code=404,
                detail="पोस्ट नहीं मिला या निजी है (Post not found or private)"
            )

        # Toggle like
        if has_user_liked(db, case_id, current_user.id):
            remove_like(db, case_id, current_user.id)
            action = "unliked"
            message = "लाइक हटाया गया (Like removed)"
        else:
            add_like(db, case_id, current_user.id)
            action = "liked"
            message = "पोस्ट को लाइक किया गया (Post liked)"

        logger.info(f"User {current_user.id} {action} post {post_id}")

        return FeedResponse(
            success=True,
            data={
                "post_id": post_id,
                "likes_count": get_post_likes_count(db, case_id),
                "has_liked": has_user_liked(db, case_id, current_user.id)
            },
            message=message
        )

    except ValueError:
        raise HTTPException(status_code=400, detail="अमान्य पोस्ट ID (Invalid post ID)")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error liking post: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"लाइक करने में त्रुटि (Error liking post): {str(e)}"
        )


@router.post("/posts/{post_id}/comment", response_model=FeedResponse)
async def comment_on_post(
    post_id: str,
    comment_data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_dev)
):
    """
    Comment on a feed post

    Args:
        post_id: UUID of the post (case) to comment on
        comment_data: Comment content

    Returns:
        Created comment data
    """
    try:
        case_id = uuid.UUID(post_id)

        # Verify case exists and is public
        case = db.query(Case).filter(
            Case.id == case_id,
            Case.is_public == True
        ).first()

        if not case:
            raise HTTPException(
                status_code=404,
                detail="पोस्ट नहीं मिला या निजी है (Post not found or private)"
            )

        # Add comment
        comment = add_comment(db, case_id, current_user.id, comment_data.content)

        # Enrich comment with user data
        user = db.query(User).filter(User.id == current_user.id).first()
        comment["user"] = {
            "id": str(user.id),
            "name": user.name or "उपयोगकर्ता (User)"
        }

        logger.info(f"User {current_user.id} commented on post {post_id}")

        return FeedResponse(
            success=True,
            data={
                "comment": comment,
                "comments_count": get_post_comments_count(db, case_id)
            },
            message="टिप्पणी जोड़ी गई (Comment added)"
        )

    except ValueError:
        raise HTTPException(status_code=400, detail="अमान्य पोस्ट ID (Invalid post ID)")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error commenting on post: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"टिप्पणी करने में त्रुटि (Error commenting): {str(e)}"
        )


@router.get("/posts/{post_id}/comments", response_model=FeedResponse)
async def get_post_comments(
    post_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_dev)
):
    """
    Get comments for a feed post

    Args:
        post_id: UUID of the post
        skip: Number of comments to skip (pagination)
        limit: Maximum comments to return

    Returns:
        List of comments with user data
    """
    try:
        case_id = uuid.UUID(post_id)

        # Verify case exists and is public
        case = db.query(Case).filter(
            Case.id == case_id,
            Case.is_public == True
        ).first()

        if not case:
            raise HTTPException(
                status_code=404,
                detail="पोस्ट नहीं मिला या निजी है (Post not found or private)"
            )

        # Get comments
        comments = get_comments(db, case_id, skip, limit)

        # Enrich with user data
        enriched_comments = []
        for comment in comments:
            user = db.query(User).filter(User.id == uuid.UUID(comment["user_id"])).first()
            comment_copy = comment.copy()
            comment_copy["user"] = {
                "id": str(user.id) if user else None,
                "name": user.name if user else "उपयोगकर्ता (User)"
            }
            enriched_comments.append(comment_copy)

        return FeedResponse(
            success=True,
            data={
                "comments": enriched_comments,
                "total": get_post_comments_count(db, case_id),
                "skip": skip,
                "limit": limit
            },
            message="टिप्पणियाँ लोड की गईं (Comments loaded)"
        )

    except ValueError:
        raise HTTPException(status_code=400, detail="अमान्य पोस्ट ID (Invalid post ID)")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching comments: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"टिप्पणियाँ लोड करने में त्रुटि (Error loading comments): {str(e)}"
        )


@router.post("/posts/{post_id}/share", response_model=FeedResponse)
async def share_post(
    post_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_dev)
):
    """
    Share a feed post

    Increments share count for the post.
    In a full implementation, this would create a new post referencing the original.

    Args:
        post_id: UUID of the post to share

    Returns:
        Updated share count
    """
    try:
        case_id = uuid.UUID(post_id)

        # Verify case exists and is public
        case = db.query(Case).filter(
            Case.id == case_id,
            Case.is_public == True
        ).first()

        if not case:
            raise HTTPException(
                status_code=404,
                detail="पोस्ट नहीं मिला या निजी है (Post not found or private)"
            )

        # Add share
        add_share(db, case_id, current_user.id)

        logger.info(f"User {current_user.id} shared post {post_id}")

        return FeedResponse(
            success=True,
            data={
                "post_id": post_id,
                "shares_count": get_post_shares_count(db, case_id)
            },
            message="पोस्ट साझा किया गया (Post shared)"
        )

    except ValueError:
        raise HTTPException(status_code=400, detail="अमान्य पोस्ट ID (Invalid post ID)")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sharing post: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"शेयर करने में त्रुटि (Error sharing): {str(e)}"
        )


@router.delete("/posts/{post_id}", response_model=FeedResponse)
async def delete_post(
    post_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_dev)
):
    """
    Delete a feed post (make it private)

    Only the post owner or admin can delete.
    Actually just makes the post private instead of hard deletion.

    Args:
        post_id: UUID of the post to delete

    Returns:
        Success status
    """
    try:
        case_id = uuid.UUID(post_id)

        # Get the case
        case = db.query(Case).filter(Case.id == case_id).first()

        if not case:
            raise HTTPException(
                status_code=404,
                detail="पोस्ट नहीं मिला (Post not found)"
            )

        # Check permissions: owner or admin
        if case.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=403,
                detail="आपको यह पोस्ट हटाने की अनुमति नहीं है (You don't have permission to delete this post)"
            )

        # Make post private (soft delete from feed)
        case.is_public = False

        if case.case_metadata:
            case.case_metadata["feed_deleted_at"] = datetime.utcnow().isoformat()
            case.case_metadata["feed_deleted_by"] = str(current_user.id)

        db.commit()

        logger.info(f"User {current_user.id} deleted post {post_id}")

        return FeedResponse(
            success=True,
            data={"post_id": post_id},
            message="पोस्ट हटाया गया (Post deleted)"
        )

    except ValueError:
        raise HTTPException(status_code=400, detail="अमान्य पोस्ट ID (Invalid post ID)")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting post: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"पोस्ट हटाने में त्रुटि (Error deleting post): {str(e)}"
        )


@router.get("/trending", response_model=FeedResponse)
async def get_trending_posts(
    hours: int = Query(24, ge=1, le=168, description="Time window in hours (max 1 week)"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_dev)
):
    """
    Get trending posts based on recent engagement

    Trending algorithm:
    - Posts from last N hours
    - Sorted by engagement score (likes + comments*2 + shares*3)
    - Higher weight for recent activity

    Args:
        hours: Time window to consider (default 24 hours)
        limit: Maximum posts to return

    Returns:
        Trending posts sorted by engagement
    """
    try:
        # Calculate time threshold
        time_threshold = datetime.utcnow() - timedelta(hours=hours)

        # Query recent public posts
        recent_posts = db.query(Case).filter(
            Case.is_public == True,
            Case.kind.in_([CaseKind.GRIEVANCE.value, CaseKind.COMMUNITY_STORY.value]),
            Case.created_at >= time_threshold,
            Case.status.notin_([CaseStatus.DRAFT.value, CaseStatus.REJECTED.value])
        ).all()

        # Calculate engagement scores
        scored_posts = []
        for post in recent_posts:
            engagement = calculate_engagement_score(
                get_post_likes_count(db, post.id),
                get_post_comments_count(db, post.id),
                get_post_shares_count(db, post.id)
            )

            # Boost score for very recent posts (last 6 hours get 2x boost)
            hours_old = (datetime.utcnow() - post.created_at).total_seconds() / 3600
            if hours_old < 6:
                engagement *= 2

            scored_posts.append({
                "post": post,
                "score": engagement
            })

        # Sort by engagement score
        scored_posts.sort(key=lambda x: x["score"], reverse=True)

        # Take top N
        top_posts = scored_posts[:limit]

        # Enrich with user data
        enriched_posts = [
            enrich_post_with_user_data(db, item["post"], current_user)
            for item in top_posts
        ]

        logger.info(f"User {current_user.id} fetched {len(enriched_posts)} trending posts")

        return FeedResponse(
            success=True,
            data={
                "posts": enriched_posts,
                "time_window_hours": hours,
                "total": len(scored_posts)
            },
            message="ट्रेंडिंग पोस्ट लोड किए गए (Trending posts loaded)"
        )

    except Exception as e:
        logger.error(f"Error fetching trending posts: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"ट्रेंडिंग पोस्ट लोड करने में त्रुटि (Error loading trending posts): {str(e)}"
        )
