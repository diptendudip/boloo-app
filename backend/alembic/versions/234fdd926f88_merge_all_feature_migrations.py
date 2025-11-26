"""merge_all_feature_migrations

Revision ID: 234fdd926f88
Revises: 004_add_feed_tables, 202510311400, add_push_notifications
Create Date: 2025-11-11 22:37:51.138631

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '234fdd926f88'
down_revision: Union[str, None] = ('004_add_feed_tables', '202510311400', 'add_push_notifications')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
