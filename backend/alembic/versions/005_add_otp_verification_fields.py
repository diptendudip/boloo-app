"""add otp verification fields

Revision ID: 005_add_otp_verification_fields
Revises: add_conversation_metadata
Create Date: 2025-11-24 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_add_otp_verification_fields'
down_revision = 'add_conversation_metadata'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add OTP verification tracking fields to users table.

    These fields track:
    - phone_verified: Whether user has verified phone via OTP
    - phone_verified_at: Timestamp of first OTP verification
    - last_otp_verified_at: Timestamp of most recent OTP verification
    """
    # Add phone_verified column (default False for existing users)
    op.add_column(
        'users',
        sa.Column('phone_verified', sa.Boolean(), nullable=False, server_default='false')
    )

    # Add phone_verified_at column (nullable, NULL for unverified users)
    op.add_column(
        'users',
        sa.Column('phone_verified_at', sa.DateTime(), nullable=True)
    )

    # Add last_otp_verified_at column (nullable, NULL for unverified users)
    op.add_column(
        'users',
        sa.Column('last_otp_verified_at', sa.DateTime(), nullable=True)
    )

    # Create index on phone_verified for faster queries
    op.create_index(
        'ix_users_phone_verified',
        'users',
        ['phone_verified']
    )


def downgrade():
    """
    Remove OTP verification tracking fields.
    """
    # Drop index
    op.drop_index('ix_users_phone_verified', table_name='users')

    # Drop columns
    op.drop_column('users', 'last_otp_verified_at')
    op.drop_column('users', 'phone_verified_at')
    op.drop_column('users', 'phone_verified')
