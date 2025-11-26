"""add_resource_health_monitoring_tables

Revision ID: 001
Revises:
Create Date: 2025-10-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create resource_health table
    op.create_table(
        'resource_health',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('resource_name', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.Enum('internal', 'external', name='resourcetype'), nullable=False),
        sa.Column('resource_category', sa.Enum('api', 'database', 'cache', 'storage', 'ai_service', 'speech_service', 'email_service', 'network', 'worker', name='resourcecategory'), nullable=False),
        sa.Column('health_status', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('response_time_ms', sa.Float(), nullable=True),
        sa.Column('last_check_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_success_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_failure_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('consecutive_failures', sa.Integer(), server_default='0'),
        sa.Column('total_failures', sa.Integer(), server_default='0'),
        sa.Column('total_checks', sa.Integer(), server_default='0'),
        sa.Column('status_message', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('endpoint_url', sa.String(length=500), nullable=True),
        sa.Column('dependencies', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('restart_enabled', sa.Boolean(), server_default='false'),
        sa.Column('restart_command', sa.String(length=500), nullable=True),
        sa.Column('restart_count', sa.Integer(), server_default='0'),
        sa.Column('last_restart_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('check_interval_seconds', sa.Integer(), server_default='60'),
        sa.Column('timeout_seconds', sa.Integer(), server_default='10'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('resource_name')
    )
    op.create_index('ix_resource_health_id', 'resource_health', ['id'])
    op.create_index('ix_resource_health_resource_name', 'resource_health', ['resource_name'])
    op.create_index('ix_resource_health_resource_type', 'resource_health', ['resource_type'])

    # Create health_check_logs table
    op.create_table(
        'health_check_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('resource_name', sa.String(length=100), nullable=False),
        sa.Column('check_timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('health_status', sa.Integer(), nullable=False),
        sa.Column('response_time_ms', sa.Float(), nullable=True),
        sa.Column('status_message', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('check_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_health_check_logs_id', 'health_check_logs', ['id'])
    op.create_index('ix_health_check_logs_resource_name', 'health_check_logs', ['resource_name'])
    op.create_index('ix_health_check_logs_check_timestamp', 'health_check_logs', ['check_timestamp'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_health_check_logs_check_timestamp', table_name='health_check_logs')
    op.drop_index('ix_health_check_logs_resource_name', table_name='health_check_logs')
    op.drop_index('ix_health_check_logs_id', table_name='health_check_logs')

    op.drop_index('ix_resource_health_resource_type', table_name='resource_health')
    op.drop_index('ix_resource_health_resource_name', table_name='resource_health')
    op.drop_index('ix_resource_health_id', table_name='resource_health')

    # Drop tables
    op.drop_table('health_check_logs')
    op.drop_table('resource_health')

    # Drop enums
    sa.Enum(name='resourcecategory').drop(op.get_bind())
    sa.Enum(name='resourcetype').drop(op.get_bind())
