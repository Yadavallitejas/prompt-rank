"""
PromptRank — Admin Router (JWT + admin-role protected)

CRUD endpoints for managing contests, problems, and testcases.
All endpoints require admin role.

POST   /admin/contest                — Create contest
GET    /admin/contests               — List all contests
DELETE /admin/contests/{id}          — Delete a contest

POST   /admin/problem               — Create problem
GET    /admin/contests/{id}/problems — List problems for a contest
DELETE /admin/problems/{id}          — Delete a problem

POST   /admin/testcases              — Upload hidden testcase
GET    /admin/problems/{id}/testcases — List testcases for a problem
DELETE /admin/testcases/{id}         — Delete a testcase

GET    /admin/stats                  — Dashboard stats
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Contest, Problem, Testcase, User, Submission
from app.schemas import ContestCreate, ContestOut, ProblemCreate, ProblemOut, TestcaseCreate, TestcaseOut, TestcaseUpdate
from app.auth import get_current_admin

router = APIRouter(prefix="/admin", tags=["admin"])


# ── Contests ─────────────────────────────────────────────────────────────────

@router.post("/contest", response_model=ContestOut, status_code=status.HTTP_201_CREATED)
async def create_contest(
    payload: ContestCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    contest = Contest(
        name=payload.name,
        start_time=payload.start_time,
        end_time=payload.end_time,
        submission_limit=payload.submission_limit,
        allowed_model=payload.allowed_model,
        temperature=payload.temperature,
        seed_base=payload.seed_base,
        created_by=admin.id,
    )
    db.add(contest)
    await db.commit()
    await db.refresh(contest)
    return contest


@router.get("/contests", response_model=list[ContestOut])
async def list_all_contests(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    result = await db.execute(select(Contest).order_by(Contest.start_time.desc()))
    return result.scalars().all()


@router.delete("/contests/{contest_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contest(
    contest_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    result = await db.execute(select(Contest).where(Contest.id == contest_id))
    contest = result.scalar_one_or_none()
    if not contest:
        raise HTTPException(status_code=404, detail="Contest not found")
    await db.delete(contest)
    await db.commit()


# ── Problems ─────────────────────────────────────────────────────────────────

@router.post("/problem", response_model=ProblemOut, status_code=status.HTTP_201_CREATED)
async def create_problem(
    payload: ProblemCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    problem = Problem(
        title=payload.title,
        statement=payload.statement,
        schema_json=payload.schema_json,
        time_limit_sec=payload.time_limit_sec,
        scoring_config_json=payload.scoring_config_json,
        contest_id=payload.contest_id,
        is_practice=payload.is_practice,
        difficulty=payload.difficulty,
        author_id=admin.id,
    )
    db.add(problem)
    await db.commit()
    await db.refresh(problem)
    return problem


@router.get("/contests/{contest_id}/problems", response_model=list[ProblemOut])
async def list_contest_problems(
    contest_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    result = await db.execute(
        select(Problem).where(Problem.contest_id == contest_id)
    )
    return result.scalars().all()


@router.delete("/problems/{problem_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_problem(
    problem_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    result = await db.execute(select(Problem).where(Problem.id == problem_id))
    problem = result.scalar_one_or_none()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    await db.delete(problem)
    await db.commit()


# ── Testcases ────────────────────────────────────────────────────────────────

@router.post("/testcases", response_model=TestcaseOut, status_code=status.HTTP_201_CREATED)
async def create_testcase(
    payload: TestcaseCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    testcase = Testcase(
        problem_id=payload.problem_id,
        input_blob=payload.input_blob,
        expected_output_blob=payload.expected_output_blob,
        is_adversarial=payload.is_adversarial,
    )
    db.add(testcase)
    await db.commit()
    await db.refresh(testcase)
    return testcase


@router.get("/problems/{problem_id}/testcases", response_model=list[TestcaseOut])
async def list_problem_testcases(
    problem_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    result = await db.execute(
        select(Testcase).where(Testcase.problem_id == problem_id)
    )
    return result.scalars().all()


@router.delete("/testcases/{testcase_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_testcase(
    testcase_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    result = await db.execute(select(Testcase).where(Testcase.id == testcase_id))
    testcase = result.scalar_one_or_none()
    if not testcase:
        raise HTTPException(status_code=404, detail="Testcase not found")
    await db.delete(testcase)
    await db.commit()


@router.put("/testcases/{testcase_id}", response_model=TestcaseOut)
async def update_testcase(
    testcase_id: UUID,
    payload: TestcaseUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    result = await db.execute(select(Testcase).where(Testcase.id == testcase_id))
    testcase = result.scalar_one_or_none()
    if not testcase:
        raise HTTPException(status_code=404, detail="Testcase not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(testcase, field, value)

    await db.commit()
    await db.refresh(testcase)
    return testcase


# ── Dashboard Stats ──────────────────────────────────────────────────────────

@router.get("/stats")
async def get_admin_stats(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    contests = (await db.execute(select(func.count()).select_from(Contest))).scalar()
    problems = (await db.execute(select(func.count()).select_from(Problem))).scalar()
    users = (await db.execute(select(func.count()).select_from(User))).scalar()
    submissions = (await db.execute(select(func.count()).select_from(Submission))).scalar()

    return {
        "total_contests": contests,
        "total_problems": problems,
        "total_users": users,
        "total_submissions": submissions,
    }
