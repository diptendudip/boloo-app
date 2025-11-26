# Feed Database Schema Documentation

## Overview
The feed database schema provides social networking capabilities for the Boloo grievance reporting system, allowing users to interact with cases through likes, comments, and shares.

## Schema Design

### Entity Relationship Diagram

```
User (1) ──────────── (M) FeedPost (1) ──────────── (1) Case
                           │
                           ├── (M) FeedLike (M) ──────── User
                           │
                           ├── (M) FeedComment (M) ────── User
                           │
                           └── (M) FeedShare (M) ──────── User
```

## Tables

### 1. feed_posts
Main table storing social feed posts linked to grievance cases.

**Columns:**
- `id` (UUID, PK) - Unique identifier
- `case_id` (UUID, FK → cases.id, UNIQUE) - One-to-one link to case
- `user_id` (UUID, FK → users.id) - Post author
- `content` (TEXT) - Post content/description
- `visibility` (ENUM) - Post visibility: 'public', 'friends', 'private'
- `location_latitude` (STRING) - Geolocation latitude
- `location_longitude` (STRING) - Geolocation longitude
- `location_address` (TEXT) - Human-readable address
- `is_deleted` (BOOLEAN) - Soft delete flag
- `created_at` (TIMESTAMP) - Creation timestamp
- `updated_at` (TIMESTAMP) - Last update timestamp

**Indexes:**
- `ix_feed_posts_case_id` - Fast case lookups
- `ix_feed_posts_user_id` - Fast user post queries
- `ix_feed_posts_created_at` - Chronological ordering
- `ix_feed_posts_is_deleted` - Filter deleted posts
- `ix_feed_posts_visibility` - Filter by visibility
- `ix_feed_posts_deleted_created` (Partial) - Optimized feed queries (WHERE is_deleted = false)

**Constraints:**
- `case_id` UNIQUE - One feed post per case
- CASCADE delete on case/user deletion

### 2. feed_likes
Stores user likes on feed posts.

**Columns:**
- `id` (UUID, PK) - Unique identifier
- `post_id` (UUID, FK → feed_posts.id) - Referenced post
- `user_id` (UUID, FK → users.id) - User who liked
- `is_deleted` (BOOLEAN) - Soft delete (unlike)
- `created_at` (TIMESTAMP) - Like timestamp

**Indexes:**
- `ix_feed_likes_post_id` - Fast post like queries
- `ix_feed_likes_user_id` - Fast user like queries
- `ix_feed_likes_created_at` - Chronological ordering
- `uq_feed_likes_post_user_active` (UNIQUE, Partial) - One active like per user per post

**Constraints:**
- Composite unique constraint on (post_id, user_id) WHERE is_deleted = false
- CASCADE delete on post/user deletion

### 3. feed_comments
Stores user comments on feed posts.

**Columns:**
- `id` (UUID, PK) - Unique identifier
- `post_id` (UUID, FK → feed_posts.id) - Referenced post
- `user_id` (UUID, FK → users.id) - Comment author
- `comment_text` (TEXT) - Comment content
- `is_deleted` (BOOLEAN) - Soft delete flag
- `created_at` (TIMESTAMP) - Comment timestamp
- `updated_at` (TIMESTAMP) - Last edit timestamp

**Indexes:**
- `ix_feed_comments_post_id` - Fast post comment queries
- `ix_feed_comments_user_id` - Fast user comment queries
- `ix_feed_comments_created_at` - Chronological ordering
- `ix_feed_comments_post_deleted` - Optimized comment listing

**Constraints:**
- CASCADE delete on post/user deletion

### 4. feed_shares
Tracks post shares/reposts by users.

**Columns:**
- `id` (UUID, PK) - Unique identifier
- `post_id` (UUID, FK → feed_posts.id) - Shared post
- `user_id` (UUID, FK → users.id) - User who shared
- `is_deleted` (BOOLEAN) - Soft delete (unshare)
- `created_at` (TIMESTAMP) - Share timestamp

**Indexes:**
- `ix_feed_shares_post_id` - Fast post share queries
- `ix_feed_shares_user_id` - Fast user share queries
- `ix_feed_shares_created_at` - Chronological ordering
- `ix_feed_shares_post_deleted` - Optimized share counting

**Constraints:**
- CASCADE delete on post/user deletion

## Enums

### FeedVisibility
```python
class FeedVisibility(str, enum.Enum):
    public = "public"      # Visible to all users
    friends = "friends"    # Visible to friends only
    private = "private"    # Visible to post author only
```

## Key Features

### 1. Soft Delete Pattern
All feed tables implement soft delete using `is_deleted` boolean flag:
- Allows data recovery
- Maintains referential integrity
- Enables "unlike" and "unshare" functionality
- Historical data preservation

### 2. Performance Optimization
**Composite Indexes:**
- `(is_deleted, created_at)` on feed_posts for feed queries
- `(post_id, is_deleted, created_at)` on feed_comments for comment listing
- `(post_id, user_id)` on feed_likes with partial unique constraint

**Query Patterns:**
```sql
-- Optimized feed query
SELECT * FROM feed_posts
WHERE is_deleted = false
ORDER BY created_at DESC
LIMIT 20;

-- Optimized like count
SELECT COUNT(*) FROM feed_likes
WHERE post_id = ? AND is_deleted = false;

-- Optimized comment listing
SELECT * FROM feed_comments
WHERE post_id = ? AND is_deleted = false
ORDER BY created_at ASC;
```

### 3. One-to-One Case Relationship
Each case can have exactly ONE feed post (enforced by UNIQUE constraint on `case_id`).
This ensures:
- No duplicate posts for the same case
- Simple bidirectional navigation
- Consistent data model

### 4. Cascade Deletion
Foreign key constraints with CASCADE delete ensure:
- Deleting a case removes its feed post and all interactions
- Deleting a user removes all their posts, likes, comments, shares
- Data integrity maintained automatically

## SQLAlchemy Models

### Model Relationships
```python
# FeedPost relationships
FeedPost.case → Case (one-to-one)
FeedPost.user → User (many-to-one)
FeedPost.likes → [FeedLike] (one-to-many, cascade)
FeedPost.comments → [FeedComment] (one-to-many, cascade)
FeedPost.shares → [FeedShare] (one-to-many, cascade)

# Backref relationships
Case.feed_post → FeedPost
User.feed_posts → [FeedPost]
User.feed_likes → [FeedLike]
User.feed_comments → [FeedComment]
User.feed_shares → [FeedShare]
```

### to_dict() Methods
All models include `to_dict()` serialization methods for API responses:
- UUID fields converted to strings
- Timestamp fields converted to ISO format
- Related counts computed (likes_count, comments_count, shares_count)
- Soft-deleted items excluded from counts

## Migration

### Apply Migration
```bash
cd backend
alembic upgrade head
```

### Rollback Migration
```bash
cd backend
alembic downgrade -1
```

### Check Migration Status
```bash
cd backend
alembic current
alembic history
```

## Usage Examples

### Create Feed Post from Case
```python
from app.models import FeedPost, FeedVisibility

feed_post = FeedPost(
    case_id=case.id,
    user_id=user.id,
    content="Road pothole reported at Main Street",
    visibility=FeedVisibility.public,
    location_latitude=case.location_latitude,
    location_longitude=case.location_longitude,
    location_address=case.location_address
)
db.add(feed_post)
db.commit()
```

### Like a Post
```python
from app.models import FeedLike

# Check if already liked
existing_like = db.query(FeedLike).filter(
    FeedLike.post_id == post_id,
    FeedLike.user_id == user_id,
    FeedLike.is_deleted == False
).first()

if not existing_like:
    like = FeedLike(post_id=post_id, user_id=user_id)
    db.add(like)
    db.commit()
```

### Add Comment
```python
from app.models import FeedComment

comment = FeedComment(
    post_id=post_id,
    user_id=user_id,
    comment_text="Thanks for reporting this!"
)
db.add(comment)
db.commit()
```

### Get Feed with Counts
```python
from sqlalchemy import func

posts = db.query(
    FeedPost,
    func.count(distinct(FeedLike.id)).filter(FeedLike.is_deleted == False).label('likes_count'),
    func.count(distinct(FeedComment.id)).filter(FeedComment.is_deleted == False).label('comments_count'),
    func.count(distinct(FeedShare.id)).filter(FeedShare.is_deleted == False).label('shares_count')
).outerjoin(FeedLike).outerjoin(FeedComment).outerjoin(FeedShare)\
 .filter(FeedPost.is_deleted == False)\
 .group_by(FeedPost.id)\
 .order_by(FeedPost.created_at.desc())\
 .limit(20).all()
```

## Security Considerations

1. **Visibility Control**: Implement middleware to check `visibility` field
2. **User Authorization**: Verify user owns post before edit/delete
3. **Rate Limiting**: Prevent spam likes/comments/shares
4. **Content Moderation**: Monitor comment_text for inappropriate content
5. **Cascade Deletes**: Be cautious with user account deletion (affects all feed data)

## Performance Tips

1. Use partial indexes for common query patterns
2. Leverage soft deletes for "undo" functionality
3. Compute counts at query time (cached if needed)
4. Consider pagination for large result sets
5. Use connection pooling for high concurrency
6. Monitor slow query log for optimization opportunities

## Future Enhancements

- [ ] Nested comments/replies
- [ ] Post reactions (beyond simple likes)
- [ ] Post tags/hashtags
- [ ] User mentions (@username)
- [ ] Post editing history
- [ ] Media attachments (photos/videos)
- [ ] Push notifications for interactions
- [ ] Trending posts algorithm
- [ ] Feed personalization
- [ ] Moderation flags

## Related Files

- Models: `/Users/diptendu/boloo app/boloo-app/backend/app/models.py`
- Migration: `/Users/diptendu/boloo app/boloo-app/backend/alembic/versions/004_add_feed_tables.py`
- API Routes: (To be implemented)
- Tests: (To be implemented)

## Support

For issues or questions regarding the feed schema, please contact the development team or file an issue in the project repository.
