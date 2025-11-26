"""Add metadata column to conversations table for smart location confirmation

Revision ID: add_conversation_metadata
Revises: 6f8cc5330bbf
Create Date: 2025-11-17 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_conversation_metadata'
down_revision = '6f8cc5330bbf'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add session_metadata JSONB column to conversations table.

    This column stores session-specific information such as:
    - profile_location_available: Whether user has location in profile
    - profile_location_formatted: Formatted location string for display
    - profile_location_confirmed: Whether user confirmed the location
    - location_data: Full location data from profile
    """
    # Add session_metadata column with default empty object
    op.add_column(
        'conversations',
        sa.Column('session_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}')
    )


def downgrade():
    """Remove session_metadata column from conversations table"""
    op.drop_column('conversations', 'session_metadata')
