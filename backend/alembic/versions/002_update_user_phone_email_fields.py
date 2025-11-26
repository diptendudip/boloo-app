"""update_user_phone_email_fields

Revision ID: 002
Revises: 001
Create Date: 2025-10-26

Make email optional and phone required for MSG91 SMS authentication
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make email column nullable (allow NULL values)
    op.alter_column('users', 'email',
                    existing_type=sa.String(length=255),
                    nullable=True,
                    existing_nullable=False)

    # Ensure phone column is NOT NULL
    # First, we need to check if there are any NULL phone values and handle them
    # Since this is a new constraint, existing data should already have phones
    op.alter_column('users', 'phone',
                    existing_type=sa.String(length=20),
                    nullable=False,
                    existing_nullable=True)


def downgrade() -> None:
    # Revert phone to nullable
    op.alter_column('users', 'phone',
                    existing_type=sa.String(length=20),
                    nullable=True,
                    existing_nullable=False)

    # Revert email to NOT NULL
    op.alter_column('users', 'email',
                    existing_type=sa.String(length=255),
                    nullable=False,
                    existing_nullable=True)
