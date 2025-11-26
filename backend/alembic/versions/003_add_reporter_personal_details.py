"""add_reporter_personal_details

Revision ID: 003
Revises: 202510311400
Create Date: 2025-01-08

Add reporter name, phone, and address fields to cases table for mandatory personal details collection
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '202510311400'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add reporter personal details columns to cases table
    op.add_column('cases', sa.Column('reporter_name', sa.Text(), nullable=True))
    op.add_column('cases', sa.Column('reporter_phone', sa.Text(), nullable=True))
    op.add_column('cases', sa.Column('reporter_address', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove reporter personal details columns
    op.drop_column('cases', 'reporter_address')
    op.drop_column('cases', 'reporter_phone')
    op.drop_column('cases', 'reporter_name')
