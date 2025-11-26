"""add ai_question_slot to conversation_turns

Revision ID: 96255f04f125
Revises: 234fdd926f88
Create Date: 2025-11-12 12:30:06.497922

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '96255f04f125'
down_revision: Union[str, None] = '234fdd926f88'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add ai_question_slot column to conversation_turns for FSM state tracking"""
    # Add nullable column for slot-filling state machine
    op.add_column(
        'conversation_turns',
        sa.Column('ai_question_slot', sa.String(), nullable=True)
    )

    # Create index for efficient queries by slot
    op.create_index(
        'ix_conversation_turns_ai_question_slot',
        'conversation_turns',
        ['ai_question_slot']
    )


def downgrade() -> None:
    """Remove ai_question_slot column"""
    # Drop index first
    op.drop_index('ix_conversation_turns_ai_question_slot', table_name='conversation_turns')

    # Drop column
    op.drop_column('conversation_turns', 'ai_question_slot')
