"""initial schema

Revision ID: 001
Revises: 
Create Date: 2026-02-28

Creates all 7 core tables: users, contests, problems, testcases,
submissions, runs, rating_history.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Users ────────────────────────────────────────────────
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('username', sa.String(50), unique=True, nullable=False, index=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False, server_default='1200'),
        sa.Column('role', sa.Enum('user', 'admin', name='userrole'), nullable=False, server_default='user'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # ── Contests ─────────────────────────────────────────────
    op.create_table(
        'contests',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('status', sa.Enum('scheduled', 'active', 'ended', name='conteststatus'), nullable=False, server_default='scheduled'),
        sa.Column('submission_limit', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('allowed_model', sa.String(100), nullable=False, server_default='gpt-4o-mini'),
        sa.Column('temperature', sa.Float(), nullable=False, server_default='0.7'),
        sa.Column('seed_base', sa.Integer(), nullable=False, server_default='42'),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # ── Problems ─────────────────────────────────────────────
    op.create_table(
        'problems',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('contest_id', UUID(as_uuid=True), sa.ForeignKey('contests.id'), nullable=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('statement', sa.Text(), nullable=False),
        sa.Column('schema_json', sa.JSON(), nullable=True),
        sa.Column('time_limit_sec', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('scoring_config_json', sa.JSON(), nullable=True),
        sa.Column('author_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # ── Testcases ────────────────────────────────────────────
    op.create_table(
        'testcases',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('problem_id', UUID(as_uuid=True), sa.ForeignKey('problems.id'), nullable=False),
        sa.Column('input_blob', sa.Text(), nullable=False),
        sa.Column('expected_output_blob', sa.Text(), nullable=False),
        sa.Column('is_adversarial', sa.Boolean(), nullable=False, server_default='false'),
    )

    # ── Submissions ──────────────────────────────────────────
    op.create_table(
        'submissions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('contest_id', UUID(as_uuid=True), sa.ForeignKey('contests.id'), nullable=True),
        sa.Column('problem_id', UUID(as_uuid=True), sa.ForeignKey('problems.id'), nullable=False),
        sa.Column('prompt_text', sa.Text(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.Enum('queued', 'running', 'evaluated', 'failed', name='submissionstatus'), nullable=False, server_default='queued'),
        sa.Column('final_score', sa.Float(), nullable=True),
        sa.Column('metrics_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # ── Runs ─────────────────────────────────────────────────
    op.create_table(
        'runs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('submission_id', UUID(as_uuid=True), sa.ForeignKey('submissions.id'), nullable=False),
        sa.Column('testcase_id', UUID(as_uuid=True), sa.ForeignKey('testcases.id'), nullable=False),
        sa.Column('run_index', sa.Integer(), nullable=False),
        sa.Column('output_blob', sa.Text(), nullable=True),
        sa.Column('tokens_used', sa.Integer(), server_default='0'),
        sa.Column('latency_ms', sa.Integer(), server_default='0'),
        sa.Column('passed_bool', sa.Boolean(), server_default='false'),
    )

    # ── Rating History ───────────────────────────────────────
    op.create_table(
        'rating_history',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('contest_id', UUID(as_uuid=True), sa.ForeignKey('contests.id'), nullable=False),
        sa.Column('rating_before', sa.Integer(), nullable=False),
        sa.Column('rating_after', sa.Integer(), nullable=False),
        sa.Column('delta', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('rating_history')
    op.drop_table('runs')
    op.drop_table('submissions')
    op.drop_table('testcases')
    op.drop_table('problems')
    op.drop_table('contests')
    op.drop_table('users')
    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute("DROP TYPE IF EXISTS conteststatus")
    op.execute("DROP TYPE IF EXISTS submissionstatus")
