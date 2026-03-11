"""
PromptRank — Pydantic Schemas (Request / Response DTOs)
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any
from datetime import datetime
from uuid import UUID
from app.models import ContestStatus, SubmissionStatus


# ── Auth ─────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: UUID
    username: str
    email: str
    rating: int
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Contests ─────────────────────────────────────────────────────────────────

class ContestCreate(BaseModel):
    name: str = Field(..., max_length=200)
    start_time: datetime
    end_time: datetime
    submission_limit: int = 3
    allowed_model: str = "gpt-4o-mini"
    temperature: float = 0.7
    seed_base: int = 42


class ContestOut(BaseModel):
    id: UUID
    name: str
    start_time: datetime
    end_time: datetime
    status: ContestStatus
    submission_limit: int
    allowed_model: str
    temperature: float
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Problems ─────────────────────────────────────────────────────────────────

class ProblemCreate(BaseModel):
    title: str = Field(..., max_length=200)
    statement: str
    schema_json: Optional[dict] = None
    time_limit_sec: int = 30
    scoring_config_json: Optional[dict] = None
    contest_id: Optional[UUID] = None
    is_practice: bool = False
    difficulty: str = "medium"


class ProblemOut(BaseModel):
    id: UUID
    title: str
    statement: str
    schema_json: Optional[dict]
    time_limit_sec: int
    scoring_config_json: Optional[dict]
    contest_id: Optional[UUID]
    is_practice: bool
    difficulty: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Testcases ────────────────────────────────────────────────────────────────

class TestcaseCreate(BaseModel):
    problem_id: UUID
    input_blob: str
    expected_output_blob: str
    is_adversarial: bool = False


class TestcaseUpdate(BaseModel):
    input_blob: Optional[str] = None
    expected_output_blob: Optional[str] = None
    is_adversarial: Optional[bool] = None


class TestcaseOut(BaseModel):
    id: UUID
    problem_id: UUID
    input_blob: str
    expected_output_blob: str
    is_adversarial: bool

    model_config = {"from_attributes": True}


# ── Submissions ──────────────────────────────────────────────────────────────

class SubmissionCreate(BaseModel):
    problem_id: UUID
    contest_id: Optional[UUID] = None
    prompt_text: str


class SubmissionOut(BaseModel):
    id: UUID
    user_id: UUID
    problem_id: UUID
    contest_id: Optional[UUID]
    prompt_text: str
    version: int
    status: SubmissionStatus
    final_score: Optional[float]
    metrics_json: Optional[dict]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Submission History ───────────────────────────────────────────────────────

class SubmissionHistoryItem(BaseModel):
    id: UUID
    user_id: UUID
    problem_id: UUID
    contest_id: Optional[UUID]
    prompt_text: str
    version: int
    status: SubmissionStatus
    final_score: Optional[float]
    metrics_json: Optional[dict]
    created_at: datetime
    problem_title: str
    contest_name: Optional[str] = None
    is_practice: bool
    total_runs: int = 0
    passed_runs: int = 0

    model_config = {"from_attributes": True}


# ── Submission Report ────────────────────────────────────────────────────────

class RunOut(BaseModel):
    id: UUID
    testcase_id: UUID
    run_index: int
    tokens_used: int
    latency_ms: int
    passed_bool: bool

    model_config = {"from_attributes": True}


class SubmissionReport(BaseModel):
    submission: SubmissionOut
    runs: List[RunOut]


# ── Leaderboard ──────────────────────────────────────────────────────────────

class LeaderboardEntry(BaseModel):
    rank: int
    user_id: UUID
    username: str
    rating: int
    contest_score: Optional[float] = None
    delta: Optional[int] = None


class GlobalLeaderboardEntry(BaseModel):
    rank: int
    user_id: UUID
    username: str
    rating: int
    created_at: datetime

    model_config = {"from_attributes": True}


class RatingHistoryOut(BaseModel):
    id: UUID
    user_id: UUID
    contest_id: UUID
    rating_before: int
    rating_after: int
    delta: int
    created_at: datetime

    model_config = {"from_attributes": True}
