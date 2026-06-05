"""add speaker and metadata columns

Revision ID: 0002_add_speaker_and_metadata
Revises: 0001_initial_mvp
Create Date: 2026-06-05 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0002_add_speaker_and_metadata'
down_revision: Union[str, None] = '0001_initial_mvp'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add speaker column to sources
    op.add_column('sources', sa.Column('speaker', sa.String(length=255), nullable=True))

    # Add speaker and published_at to chunks (denormalized for fast filtered search)
    op.add_column('chunks', sa.Column('speaker', sa.String(length=255), nullable=True))
    op.add_column('chunks', sa.Column('published_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f('ix_chunks_speaker'), 'chunks', ['speaker'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_chunks_speaker'), table_name='chunks')
    op.drop_column('chunks', 'published_at')
    op.drop_column('chunks', 'speaker')
    op.drop_column('sources', 'speaker')
