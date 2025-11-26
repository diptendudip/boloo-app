"""add feed tables

Revision ID: 004_add_feed_tables
Revises: 60c82f467cc2
Create Date: 2025-11-11

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_add_feed_tables'
down_revision = '60c82f467cc2'
branch_labels = None
depends_on = None


def upgrade():
    # Create feed_visibility enum type
    feed_visibility_enum = postgresql.ENUM(
        'public', 'friends', 'private',
        name='feedvisibility',
        create_type=True
    )
    feed_visibility_enum.create(op.get_bind(), checkfirst=True)

    # Create feed_posts table
    op.create_table(
        'feed_posts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('visibility', feed_visibility_enum, nullable=False, server_default='public'),
        sa.Column('location_latitude', sa.String(), nullable=True),
        sa.Column('location_longitude', sa.String(), nullable=True),
        sa.Column('location_address', sa.Text(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # Create indexes for feed_posts
    op.create_index('ix_feed_posts_case_id', 'feed_posts', ['case_id'])
    op.create_index('ix_feed_posts_user_id', 'feed_posts', ['user_id'])
    op.create_index('ix_feed_posts_created_at', 'feed_posts', ['created_at'])
    op.create_index('ix_feed_posts_is_deleted', 'feed_posts', ['is_deleted'])
    op.create_index('ix_feed_posts_visibility', 'feed_posts', ['visibility'])
    # Composite index for feed queries (most common query pattern)
    op.create_index(
        'ix_feed_posts_deleted_created',
        'feed_posts',
        ['is_deleted', 'created_at'],
        postgresql_where=sa.text('is_deleted = false')
    )

    # Create feed_likes table
    op.create_table(
        'feed_likes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('post_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['post_id'], ['feed_posts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # Create indexes for feed_likes
    op.create_index('ix_feed_likes_post_id', 'feed_likes', ['post_id'])
    op.create_index('ix_feed_likes_user_id', 'feed_likes', ['user_id'])
    op.create_index('ix_feed_likes_created_at', 'feed_likes', ['created_at'])
    # Composite unique constraint for active likes (one like per user per post)
    op.create_index(
        'uq_feed_likes_post_user_active',
        'feed_likes',
        ['post_id', 'user_id'],
        unique=True,
        postgresql_where=sa.text('is_deleted = false')
    )

    # Create feed_comments table
    op.create_table(
        'feed_comments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('post_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('comment_text', sa.Text(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['post_id'], ['feed_posts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # Create indexes for feed_comments
    op.create_index('ix_feed_comments_post_id', 'feed_comments', ['post_id'])
    op.create_index('ix_feed_comments_user_id', 'feed_comments', ['user_id'])
    op.create_index('ix_feed_comments_created_at', 'feed_comments', ['created_at'])
    # Composite index for comment queries
    op.create_index(
        'ix_feed_comments_post_deleted',
        'feed_comments',
        ['post_id', 'is_deleted', 'created_at']
    )

    # Create feed_shares table
    op.create_table(
        'feed_shares',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('post_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['post_id'], ['feed_posts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # Create indexes for feed_shares
    op.create_index('ix_feed_shares_post_id', 'feed_shares', ['post_id'])
    op.create_index('ix_feed_shares_user_id', 'feed_shares', ['user_id'])
    op.create_index('ix_feed_shares_created_at', 'feed_shares', ['created_at'])
    # Composite index for share queries
    op.create_index(
        'ix_feed_shares_post_deleted',
        'feed_shares',
        ['post_id', 'is_deleted']
    )


def downgrade():
    # Drop tables in reverse order
    op.drop_table('feed_shares')
    op.drop_table('feed_comments')
    op.drop_table('feed_likes')
    op.drop_table('feed_posts')

    # Drop enum type
    feed_visibility_enum = postgresql.ENUM(
        'public', 'friends', 'private',
        name='feedvisibility'
    )
    feed_visibility_enum.drop(op.get_bind(), checkfirst=True)
