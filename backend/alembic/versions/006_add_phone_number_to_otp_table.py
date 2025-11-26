"""add phone_number to otp table

Revision ID: 006_add_phone_number_to_otp
Revises: 005_add_otp_verification_fields
Create Date: 2025-11-24 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006_add_phone_number_to_otp'
down_revision = '005_add_otp_verification_fields'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add phone_number field to OTP table.

    This allows OTP to be sent to either email OR phone number,
    supporting the chat interface which uses phone-based authentication.

    Changes:
    - Add phone_number VARCHAR(20) nullable to otps table
    - Add index on phone_number for faster lookups
    - Make email nullable (since phone_number is alternative)
    """
    # Add phone_number column (nullable, for phone-based OTP)
    op.add_column(
        'otps',
        sa.Column('phone_number', sa.String(20), nullable=True)
    )

    # Create index on phone_number for faster queries
    op.create_index(
        'ix_otps_phone_number',
        'otps',
        ['phone_number']
    )

    # Make email column nullable (since phone_number is now an alternative)
    op.alter_column(
        'otps',
        'email',
        existing_type=sa.String(255),
        nullable=True
    )


def downgrade():
    """
    Remove phone_number field from OTP table.
    """
    # Restore email as NOT NULL
    op.alter_column(
        'otps',
        'email',
        existing_type=sa.String(255),
        nullable=False
    )

    # Drop index
    op.drop_index('ix_otps_phone_number', table_name='otps')

    # Drop column
    op.drop_column('otps', 'phone_number')
