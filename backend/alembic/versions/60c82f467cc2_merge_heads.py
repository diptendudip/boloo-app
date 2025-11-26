"""merge_heads

Revision ID: 60c82f467cc2
Revises: 002, 003
Create Date: 2025-11-08 15:13:20.699908

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '60c82f467cc2'
down_revision: Union[str, None] = ('002', '003')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
