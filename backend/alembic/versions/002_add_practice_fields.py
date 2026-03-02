"""add practice fields to problems

Revision ID: 002_add_practice_fields
Revises: 001_initial_schema
Create Date: 2026-03-02

Adds is_practice (boolean) and difficulty (string) columns to the problems table
to support standalone practice problems outside of contests.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = '002_add_practice_fields'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('problems', sa.Column('is_practice', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('problems', sa.Column('difficulty', sa.String(20), nullable=False, server_default='medium'))
    op.create_index('ix_problems_is_practice', 'problems', ['is_practice'])


def downgrade() -> None:
    op.drop_index('ix_problems_is_practice', table_name='problems')
    op.drop_column('problems', 'difficulty')
    op.drop_column('problems', 'is_practice')
