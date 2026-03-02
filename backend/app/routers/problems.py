"""
PromptRank — Practice Problems Router

Public-facing endpoints for browsable, prebuilt practice problems
(independent of any contest).

GET  /problems            — List all practice problems (filterable by difficulty)
GET  /problems/{id}       — Get a single practice problem detail
"""

from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Problem
from app.schemas import ProblemOut

router = APIRouter(prefix="/problems", tags=["problems"])


@router.get("", response_model=list[ProblemOut])
async def list_practice_problems(
    difficulty: Optional[str] = Query(None, description="Filter by difficulty: easy, medium, hard"),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns all practice problems (is_practice=True).
    Optionally filter by difficulty level.
    """
    query = select(Problem).where(Problem.is_practice == True)  # noqa: E712

    if difficulty:
        query = query.where(Problem.difficulty == difficulty.lower())

    query = query.order_by(Problem.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{problem_id}", response_model=ProblemOut)
async def get_practice_problem(problem_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Returns a single practice problem by ID.
    Only returns problems marked as practice; contest-only problems are not exposed here.
    """
    result = await db.execute(
        select(Problem).where(Problem.id == problem_id, Problem.is_practice == True)  # noqa: E712
    )
    problem = result.scalar_one_or_none()
    if not problem:
        raise HTTPException(status_code=404, detail="Practice problem not found")
    return problem
