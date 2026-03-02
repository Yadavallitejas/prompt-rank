"""
PromptRank — Submissions Router
POST /submissions            — Submit a prompt for evaluation
GET  /submissions/{id}       — Get submission status / details
GET  /submissions/{id}/report — Full evaluation report with runs
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Submission, Run, Contest, User
from app.schemas import SubmissionCreate, SubmissionOut, SubmissionReport, RunOut
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
    if payload.contest_id:
        result = await db.execute(
            select(Contest).where(Contest.id == payload.contest_id)
        )
        contest = result.scalar_one_or_none()
        if not contest:
            raise HTTPException(status_code=404, detail="Contest not found")

        count_result = await db.execute(
            select(func.count())
            .select_from(Submission)
            .where(
                Submission.user_id == current_user.id,
                Submission.contest_id == payload.contest_id,
                Submission.problem_id == payload.problem_id,
            )
        )
        count = count_result.scalar()
        if count >= contest.submission_limit:
            raise HTTPException(
                status_code=429,
                detail=f"Submission limit ({contest.submission_limit}) reached for this problem",
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
