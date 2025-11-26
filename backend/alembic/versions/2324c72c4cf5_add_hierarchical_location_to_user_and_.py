"""add_hierarchical_location_to_user_and_case

Revision ID: 2324c72c4cf5
Revises: 96255f04f125
Create Date: 2025-11-17 13:35:15.472673

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2324c72c4cf5'
down_revision: Union[str, None] = '96255f04f125'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add hierarchical location fields to users table
    op.add_column('users', sa.Column('location_street', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('location_village', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('location_panchayat', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('location_block', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('location_subdivision', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('location_district', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('location_state', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('location_lat', sa.Float, nullable=True))
    op.add_column('users', sa.Column('location_lng', sa.Float, nullable=True))
    op.add_column('users', sa.Column('location_metadata', sa.JSON, nullable=True))
    op.add_column('users', sa.Column('location_formatted_address', sa.String(1000), nullable=True))

    # Add indexes for commonly queried location fields
    op.create_index('ix_users_location_village', 'users', ['location_village'])
    op.create_index('ix_users_location_block', 'users', ['location_block'])
    op.create_index('ix_users_location_district', 'users', ['location_district'])

    # Add location_hierarchy JSON field to cases table
    op.add_column('cases', sa.Column('location_hierarchy', sa.JSON, nullable=True))


def downgrade() -> None:
    # Remove location_hierarchy from cases
    op.drop_column('cases', 'location_hierarchy')

    # Remove indexes from users
    op.drop_index('ix_users_location_district', 'users')
    op.drop_index('ix_users_location_block', 'users')
    op.drop_index('ix_users_location_village', 'users')

    # Remove hierarchical location fields from users
    op.drop_column('users', 'location_formatted_address')
    op.drop_column('users', 'location_metadata')
    op.drop_column('users', 'location_lng')
    op.drop_column('users', 'location_lat')
    op.drop_column('users', 'location_state')
    op.drop_column('users', 'location_district')
    op.drop_column('users', 'location_subdivision')
    op.drop_column('users', 'location_block')
    op.drop_column('users', 'location_panchayat')
    op.drop_column('users', 'location_village')
    op.drop_column('users', 'location_street')
