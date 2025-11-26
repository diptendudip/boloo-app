"""add push notifications

Revision ID: add_push_notifications
Revises:
Create Date: 2025-11-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_push_notifications'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add push_token column to users table
    op.add_column('users', sa.Column('push_token', sa.String(), nullable=True))
    op.create_index(op.f('ix_users_push_token'), 'users', ['push_token'], unique=False)

    # Add notification_settings column to users table
    op.add_column('users', sa.Column('notification_settings', postgresql.JSON(astext_type=sa.Text()), nullable=True))


def downgrade():
    # Remove notification_settings column
    op.drop_column('users', 'notification_settings')

    # Remove push_token column and index
    op.drop_index(op.f('ix_users_push_token'), table_name='users')
    op.drop_column('users', 'push_token')
