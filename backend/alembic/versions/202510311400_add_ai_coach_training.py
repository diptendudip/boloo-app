"""add AI Coach training tables and fields

Revision ID: 202510311400
Revises: 001
Create Date: 2025-10-31 14:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '202510311400'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Add AI Coach training fields to users table
    op.add_column('users', sa.Column('training_reports_count', sa.Integer(), server_default='0', nullable=True))
    op.add_column('users', sa.Column('training_completed', sa.Boolean(), server_default='false', nullable=True))
    op.add_column('users', sa.Column('training_mode_enabled', sa.Boolean(), server_default='true', nullable=True))

    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('turn_count', sa.Integer(), server_default='1', nullable=True),
        sa.Column('is_complete', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('completeness_score', sa.Float(), server_default='0.0', nullable=True),
        sa.Column('collected_fields', postgresql.ARRAY(sa.String()), server_default='{}', nullable=True),
        sa.Column('missing_fields', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversations_user_id'), 'conversations', ['user_id'], unique=False)
    op.create_index(op.f('ix_conversations_case_id'), 'conversations', ['case_id'], unique=False)
    op.create_index(op.f('ix_conversations_created_at'), 'conversations', ['created_at'], unique=False)

    # Create conversation_turns table
    op.create_table(
        'conversation_turns',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('turn_number', sa.Integer(), nullable=False),
        sa.Column('audio_url', sa.String(length=1000), nullable=True),
        sa.Column('transcript_text', sa.Text(), nullable=False),
        sa.Column('language_detected', sa.String(length=10), nullable=True),
        sa.Column('ai_prompt', sa.Text(), nullable=True),
        sa.Column('ai_response', sa.Text(), nullable=True),
        sa.Column('ai_question_asked', sa.Text(), nullable=True),
        sa.Column('intent', sa.String(length=50), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('fields_extracted', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('conversation_id', 'turn_number', name='uq_conversation_turn')
    )
    op.create_index(op.f('ix_conversation_turns_conversation_id'), 'conversation_turns', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_conversation_turns_created_at'), 'conversation_turns', ['created_at'], unique=False)


def downgrade():
    # Drop conversation_turns table
    op.drop_index(op.f('ix_conversation_turns_created_at'), table_name='conversation_turns')
    op.drop_index(op.f('ix_conversation_turns_conversation_id'), table_name='conversation_turns')
    op.drop_table('conversation_turns')

    # Drop conversations table
    op.drop_index(op.f('ix_conversations_created_at'), table_name='conversations')
    op.drop_index(op.f('ix_conversations_case_id'), table_name='conversations')
    op.drop_index(op.f('ix_conversations_user_id'), table_name='conversations')
    op.drop_table('conversations')

    # Remove AI Coach training fields from users table
    op.drop_column('users', 'training_mode_enabled')
    op.drop_column('users', 'training_completed')
    op.drop_column('users', 'training_reports_count')
