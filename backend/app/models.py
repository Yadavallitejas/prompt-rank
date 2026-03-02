"""
PromptRank — SQLAlchemy ORM Models

Tables:
  users, contests, problems, testcases, submissions, runs, rating_history

All models follow the finalized data-model from the Technical Specification.
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON, Enum as SAEnum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum


# ── Enums ────────────────────────────────────────────────────────────────────

class ContestStatus(str, enum.Enum):
    scheduled = "scheduled"
    active = "active"
    ended = "ended"


class SubmissionStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    evaluated = "evaluated"
    failed = "failed"


class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"


# ── Models ───────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    rating = Column(Integer, default=1200, nullable=False)
    role = Column(SAEnum(UserRole), default=UserRole.user, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    submissions = relationship("Submission", back_populates="user", lazy="selectin")
    rating_history = relationship("RatingHistory", back_populates="user", lazy="selectin")


class Contest(Base):
    __tablename__ = "contests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(SAEnum(ContestStatus), default=ContestStatus.scheduled, nullable=False)
    submission_limit = Column(Integer, default=3, nullable=False)
    allowed_model = Column(String(100), default="gpt-4o-mini", nullable=False)
    temperature = Column(Float, default=0.7, nullable=False)
    seed_base = Column(Integer, default=42, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    problems = relationship("Problem", back_populates="contest", lazy="selectin")
    submissions = relationship("Submission", back_populates="contest", lazy="selectin")


class Problem(Base):
    __tablename__ = "problems"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contest_id = Column(UUID(as_uuid=True), ForeignKey("contests.id"), nullable=True)
    title = Column(String(200), nullable=False)
    statement = Column(Text, nullable=False)
    schema_json = Column(JSON, nullable=True)
    time_limit_sec = Column(Integer, default=30, nullable=False)
    scoring_config_json = Column(JSON, nullable=True)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    is_practice = Column(Boolean, default=False, nullable=False, index=True)
    difficulty = Column(String(20), default="medium", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    contest = relationship("Contest", back_populates="problems")
    testcases = relationship("Testcase", back_populates="problem", lazy="selectin")


class Testcase(Base):
    __tablename__ = "testcases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    problem_id = Column(UUID(as_uuid=True), ForeignKey("problems.id"), nullable=False)
    input_blob = Column(Text, nullable=False)
    expected_output_blob = Column(Text, nullable=False)
    is_adversarial = Column(Boolean, default=False, nullable=False)

    # Relationships
    problem = relationship("Problem", back_populates="testcases")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    contest_id = Column(UUID(as_uuid=True), ForeignKey("contests.id"), nullable=True)
    problem_id = Column(UUID(as_uuid=True), ForeignKey("problems.id"), nullable=False)
    prompt_text = Column(Text, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    status = Column(SAEnum(SubmissionStatus), default=SubmissionStatus.queued, nullable=False)
    final_score = Column(Float, nullable=True)
    metrics_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="submissions")
    contest = relationship("Contest", back_populates="submissions")
    runs = relationship("Run", back_populates="submission", lazy="selectin")


class Run(Base):
    __tablename__ = "runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("submissions.id"), nullable=False)
    testcase_id = Column(UUID(as_uuid=True), ForeignKey("testcases.id"), nullable=False)
    run_index = Column(Integer, nullable=False)
    output_blob = Column(Text, nullable=True)
    tokens_used = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)
    passed_bool = Column(Boolean, default=False)

    # Relationships
    submission = relationship("Submission", back_populates="runs")


class RatingHistory(Base):
    __tablename__ = "rating_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    contest_id = Column(UUID(as_uuid=True), ForeignKey("contests.id"), nullable=False)
    rating_before = Column(Integer, nullable=False)
    rating_after = Column(Integer, nullable=False)
    delta = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="rating_history")
