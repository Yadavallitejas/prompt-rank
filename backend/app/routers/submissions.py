"""
PromptRank — Submissions Router
POST /submissions            — Submit a prompt for evaluation
GET  /submissions/my         — List current user's submissions (history)
GET  /submissions/{id}       — Get submission status / details
GET  /submissions/{id}/report — Full evaluation report with runs
"""

from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Submission, Run, Contest, Problem, User
from app.schemas import (
    SubmissionCreate, SubmissionOut, SubmissionReport, RunOut,
    SubmissionHistoryItem,
)
from app.auth import get_current_user
from app.worker import evaluate_submission
from app.middleware.anti_cheat import check_ip_rate_limit, check_duplicate_prompt

router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.post("", response_model=SubmissionOut, status_code=status.HTTP_201_CREATED)
async def create_submission(
    payload: SubmissionCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # ── Anti-cheat: IP rate limit ────────────────────────────
    await check_ip_rate_limit(request)

    # ── Anti-cheat: Duplicate prompt detection ───────────────
    await check_duplicate_prompt(
        user_id=str(current_user.id),
        problem_id=str(payload.problem_id),
        prompt_text=payload.prompt_text,
    )

    # ── Rate-limit check ─────────────────────────────────────
    count_result = await db.execute(
        select(func.count())
        .select_from(Submission)
        .where(
            Submission.user_id == current_user.id,
            Submission.problem_id == payload.problem_id,
        )
    )
    count = count_result.scalar()
    
    limit = 3
    if payload.contest_id:
        result = await db.execute(
            select(Contest).where(Contest.id == payload.contest_id)
        )
        contest = result.scalar_one_or_none()
        if not contest:
            raise HTTPException(status_code=404, detail="Contest not found")
        # Ensure we use contest submission limit if it's stricter
        limit = min(limit, contest.submission_limit)

    if count >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"Submission limit ({limit}) reached for this problem",
        )

    # ── Compute version number ───────────────────────────────
    ver_result = await db.execute(
        select(func.count())
        .select_from(Submission)
        .where(
            Submission.user_id == current_user.id,
            Submission.problem_id == payload.problem_id,
        )
    )
    version = (ver_result.scalar() or 0) + 1

    submission = Submission(
        user_id=current_user.id,
        problem_id=payload.problem_id,
        contest_id=payload.contest_id,
        prompt_text=payload.prompt_text,
        version=version,
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)

    # Queue Celery evaluation task
    evaluate_submission.delay(str(submission.id))

    return submission


# ── /my must be before /{submission_id} so "my" isn't parsed as UUID ─────────

@router.get("/my", response_model=List[SubmissionHistoryItem])
async def get_my_submissions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the current user's submissions with problem/contest details."""
    result = await db.execute(
        select(Submission)
        .where(Submission.user_id == current_user.id)
        .options(selectinload(Submission.runs))
        .order_by(Submission.created_at.desc())
    )
    submissions = result.scalars().all()

    items: List[SubmissionHistoryItem] = []
    for sub in submissions:
        # Fetch problem
        prob_result = await db.execute(
            select(Problem).where(Problem.id == sub.problem_id)
        )
        problem = prob_result.scalar_one_or_none()

        # Fetch contest name (if any)
        contest_name = None
        if sub.contest_id:
            contest_result = await db.execute(
                select(Contest.name).where(Contest.id == sub.contest_id)
            )
            contest_name = contest_result.scalar_one_or_none()

        total_runs = len(sub.runs) if sub.runs else 0
        passed_runs = sum(1 for r in sub.runs if r.passed_bool) if sub.runs else 0

        items.append(SubmissionHistoryItem(
            id=sub.id,
            user_id=sub.user_id,
            problem_id=sub.problem_id,
            contest_id=sub.contest_id,
            prompt_text=sub.prompt_text,
            version=sub.version,
            status=sub.status,
            final_score=sub.final_score,
            metrics_json=sub.metrics_json,
            created_at=sub.created_at,
            problem_title=problem.title if problem else "Unknown",
            contest_name=contest_name,
            is_practice=problem.is_practice if problem else False,
            total_runs=total_runs,
            passed_runs=passed_runs,
        ))

    return items


@router.get("/my/problem/{problem_id}", response_model=List[SubmissionHistoryItem])
async def get_my_submissions_for_problem(
    problem_id: UUID,
    contest_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return current user's submissions for a specific problem (optionally scoped to a contest)."""
    filters = [
        Submission.user_id == current_user.id,
        Submission.problem_id == problem_id,
    ]
    if contest_id is not None:
        filters.append(Submission.contest_id == contest_id)

    result = await db.execute(
        select(Submission)
        .where(*filters)
        .options(selectinload(Submission.runs))
        .order_by(Submission.created_at.desc())
    )
    submissions = result.scalars().all()

    # Fetch problem title once
    prob_result = await db.execute(
        select(Problem).where(Problem.id == problem_id)
    )
    problem = prob_result.scalar_one_or_none()

    items: List[SubmissionHistoryItem] = []
    for sub in submissions:
        contest_name = None
        if sub.contest_id:
            contest_result = await db.execute(
                select(Contest.name).where(Contest.id == sub.contest_id)
            )
            contest_name = contest_result.scalar_one_or_none()

        total_runs = len(sub.runs) if sub.runs else 0
        passed_runs = sum(1 for r in sub.runs if r.passed_bool) if sub.runs else 0

        items.append(SubmissionHistoryItem(
            id=sub.id,
            user_id=sub.user_id,
            problem_id=sub.problem_id,
            contest_id=sub.contest_id,
            prompt_text=sub.prompt_text,
            version=sub.version,
            status=sub.status,
            final_score=sub.final_score,
            metrics_json=sub.metrics_json,
            created_at=sub.created_at,
            problem_title=problem.title if problem else "Unknown",
            contest_name=contest_name,
            is_practice=problem.is_practice if problem else False,
            total_runs=total_runs,
            passed_runs=passed_runs,
        ))

    return items


@router.get("/{submission_id}", response_model=SubmissionOut)
async def get_submission(submission_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Submission).where(Submission.id == submission_id))
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return submission


@router.get("/{submission_id}/report", response_model=SubmissionReport)
async def get_submission_report(submission_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Submission).where(Submission.id == submission_id))
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    runs_result = await db.execute(
        select(Run).where(Run.submission_id == submission_id).order_by(Run.run_index)
    )
    runs = runs_result.scalars().all()

    return SubmissionReport(
        submission=SubmissionOut.model_validate(submission),
        runs=[RunOut.model_validate(r) for r in runs],
    )
