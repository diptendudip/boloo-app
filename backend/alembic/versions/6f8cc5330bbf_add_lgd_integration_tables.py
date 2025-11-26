"""add_lgd_integration_tables

Revision ID: 6f8cc5330bbf
Revises: 2324c72c4cf5
Create Date: 2025-11-17 16:12:06.772970

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6f8cc5330bbf'
down_revision: Union[str, None] = '2324c72c4cf5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create lgd_admin_units table
    op.create_table(
        'lgd_admin_units',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lgd_code', sa.String(length=20), nullable=False),
        sa.Column('name_en', sa.String(length=255), nullable=False),
        sa.Column('name_hi', sa.String(length=255), nullable=True),
        sa.Column('name_local', sa.String(length=255), nullable=True),
        sa.Column('level', sa.String(length=20), nullable=False),
        sa.Column('parent_lgd_code', sa.String(length=20), nullable=True),
        sa.Column('state_code', sa.String(length=5), nullable=True),
        sa.Column('district_code', sa.String(length=5), nullable=True),
        sa.Column('census_code', sa.String(length=20), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('lgd_code'),
        sa.ForeignKeyConstraint(['parent_lgd_code'], ['lgd_admin_units.lgd_code'], ondelete='SET NULL')
    )

    # Create indexes for lgd_admin_units table
    op.create_index('idx_lgd_name_en', 'lgd_admin_units', ['name_en'])
    op.create_index('idx_lgd_name_hi', 'lgd_admin_units', ['name_hi'])
    op.create_index('idx_lgd_level', 'lgd_admin_units', ['level'])
    op.create_index('idx_lgd_parent', 'lgd_admin_units', ['parent_lgd_code'])
    op.create_index('idx_lgd_state_code', 'lgd_admin_units', ['state_code'])
    op.create_index('idx_lgd_district_code', 'lgd_admin_units', ['district_code'])
    op.create_index('idx_lgd_is_active', 'lgd_admin_units', ['is_active'])

    # Create composite index for level + parent queries (common pattern)
    op.create_index('idx_lgd_level_parent', 'lgd_admin_units', ['level', 'parent_lgd_code'])

    # Create lgd_name_aliases table for fuzzy matching
    op.create_table(
        'lgd_name_aliases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lgd_code', sa.String(length=20), nullable=False),
        sa.Column('alias', sa.String(length=255), nullable=False),
        sa.Column('language', sa.String(length=10), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False, server_default=sa.text('1.0')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['lgd_code'], ['lgd_admin_units.lgd_code'], ondelete='CASCADE')
    )

    # Create indexes for lgd_name_aliases table
    op.create_index('idx_alias_name', 'lgd_name_aliases', ['alias'])
    op.create_index('idx_alias_lgd_code', 'lgd_name_aliases', ['lgd_code'])
    op.create_index('idx_alias_language', 'lgd_name_aliases', ['language'])

    # Create composite index for alias + language queries
    op.create_index('idx_alias_name_lang', 'lgd_name_aliases', ['alias', 'language'])

    # Add LGD code columns to users table
    op.add_column('users', sa.Column('location_village_lgd_code', sa.String(length=20), nullable=True))
    op.add_column('users', sa.Column('location_panchayat_lgd_code', sa.String(length=20), nullable=True))
    op.add_column('users', sa.Column('location_block_lgd_code', sa.String(length=20), nullable=True))
    op.add_column('users', sa.Column('location_district_lgd_code', sa.String(length=20), nullable=True))
    op.add_column('users', sa.Column('location_state_lgd_code', sa.String(length=20), nullable=True))

    # Add LGD validation metadata to users table
    op.add_column('users', sa.Column('lgd_validated', sa.Boolean(), nullable=True, server_default=sa.text('false')))
    op.add_column('users', sa.Column('lgd_validation_confidence', sa.Float(), nullable=True))
    op.add_column('users', sa.Column('lgd_validation_timestamp', sa.TIMESTAMP(), nullable=True))

    # Create indexes for LGD code lookups on users table
    op.create_index('ix_users_village_lgd', 'users', ['location_village_lgd_code'])
    op.create_index('ix_users_block_lgd', 'users', ['location_block_lgd_code'])
    op.create_index('ix_users_district_lgd', 'users', ['location_district_lgd_code'])

    # Add foreign key constraints for users LGD codes
    op.create_foreign_key(
        'fk_users_village_lgd',
        'users',
        'lgd_admin_units',
        ['location_village_lgd_code'],
        ['lgd_code'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_users_panchayat_lgd',
        'users',
        'lgd_admin_units',
        ['location_panchayat_lgd_code'],
        ['lgd_code'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_users_block_lgd',
        'users',
        'lgd_admin_units',
        ['location_block_lgd_code'],
        ['lgd_code'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_users_district_lgd',
        'users',
        'lgd_admin_units',
        ['location_district_lgd_code'],
        ['lgd_code'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_users_state_lgd',
        'users',
        'lgd_admin_units',
        ['location_state_lgd_code'],
        ['lgd_code'],
        ondelete='SET NULL'
    )

    # Add LGD code columns to cases table
    op.add_column('cases', sa.Column('location_village_lgd_code', sa.String(length=20), nullable=True))
    op.add_column('cases', sa.Column('location_block_lgd_code', sa.String(length=20), nullable=True))
    op.add_column('cases', sa.Column('location_district_lgd_code', sa.String(length=20), nullable=True))

    # Add LGD validation metadata to cases table
    op.add_column('cases', sa.Column('lgd_validated', sa.Boolean(), nullable=True, server_default=sa.text('false')))
    op.add_column('cases', sa.Column('lgd_validation_confidence', sa.Float(), nullable=True))

    # Create indexes for LGD code lookups on cases table
    op.create_index('ix_cases_village_lgd', 'cases', ['location_village_lgd_code'])
    op.create_index('ix_cases_block_lgd', 'cases', ['location_block_lgd_code'])
    op.create_index('ix_cases_district_lgd', 'cases', ['location_district_lgd_code'])

    # Add foreign key constraints for cases LGD codes
    op.create_foreign_key(
        'fk_cases_village_lgd',
        'cases',
        'lgd_admin_units',
        ['location_village_lgd_code'],
        ['lgd_code'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_cases_block_lgd',
        'cases',
        'lgd_admin_units',
        ['location_block_lgd_code'],
        ['lgd_code'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_cases_district_lgd',
        'cases',
        'lgd_admin_units',
        ['location_district_lgd_code'],
        ['lgd_code'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    # Drop foreign key constraints from cases table
    op.drop_constraint('fk_cases_district_lgd', 'cases', type_='foreignkey')
    op.drop_constraint('fk_cases_block_lgd', 'cases', type_='foreignkey')
    op.drop_constraint('fk_cases_village_lgd', 'cases', type_='foreignkey')

    # Drop indexes from cases table
    op.drop_index('ix_cases_district_lgd', 'cases')
    op.drop_index('ix_cases_block_lgd', 'cases')
    op.drop_index('ix_cases_village_lgd', 'cases')

    # Drop LGD columns from cases table
    op.drop_column('cases', 'lgd_validation_confidence')
    op.drop_column('cases', 'lgd_validated')
    op.drop_column('cases', 'location_district_lgd_code')
    op.drop_column('cases', 'location_block_lgd_code')
    op.drop_column('cases', 'location_village_lgd_code')

    # Drop foreign key constraints from users table
    op.drop_constraint('fk_users_state_lgd', 'users', type_='foreignkey')
    op.drop_constraint('fk_users_district_lgd', 'users', type_='foreignkey')
    op.drop_constraint('fk_users_block_lgd', 'users', type_='foreignkey')
    op.drop_constraint('fk_users_panchayat_lgd', 'users', type_='foreignkey')
    op.drop_constraint('fk_users_village_lgd', 'users', type_='foreignkey')

    # Drop indexes from users table
    op.drop_index('ix_users_district_lgd', 'users')
    op.drop_index('ix_users_block_lgd', 'users')
    op.drop_index('ix_users_village_lgd', 'users')

    # Drop LGD columns from users table
    op.drop_column('users', 'lgd_validation_timestamp')
    op.drop_column('users', 'lgd_validation_confidence')
    op.drop_column('users', 'lgd_validated')
    op.drop_column('users', 'location_state_lgd_code')
    op.drop_column('users', 'location_district_lgd_code')
    op.drop_column('users', 'location_block_lgd_code')
    op.drop_column('users', 'location_panchayat_lgd_code')
    op.drop_column('users', 'location_village_lgd_code')

    # Drop indexes from lgd_name_aliases table
    op.drop_index('idx_alias_name_lang', 'lgd_name_aliases')
    op.drop_index('idx_alias_language', 'lgd_name_aliases')
    op.drop_index('idx_alias_lgd_code', 'lgd_name_aliases')
    op.drop_index('idx_alias_name', 'lgd_name_aliases')

    # Drop lgd_name_aliases table
    op.drop_table('lgd_name_aliases')

    # Drop indexes from lgd_admin_units table
    op.drop_index('idx_lgd_level_parent', 'lgd_admin_units')
    op.drop_index('idx_lgd_is_active', 'lgd_admin_units')
    op.drop_index('idx_lgd_district_code', 'lgd_admin_units')
    op.drop_index('idx_lgd_state_code', 'lgd_admin_units')
    op.drop_index('idx_lgd_parent', 'lgd_admin_units')
    op.drop_index('idx_lgd_level', 'lgd_admin_units')
    op.drop_index('idx_lgd_name_hi', 'lgd_admin_units')
    op.drop_index('idx_lgd_name_en', 'lgd_admin_units')

    # Drop lgd_admin_units table
    op.drop_table('lgd_admin_units')
