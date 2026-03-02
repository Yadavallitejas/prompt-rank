"""
PromptRank -- Contests Router
GET  /contests              -- List all contests
GET  /contests/{id}         -- Get contest detail
GET  /contests/{id}/leaderboard -- Contest leaderboard (Redis-cached)
"""

import json
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Contest, Submission, User, RatingHistory
from app.schemas import ContestOut, LeaderboardEntry, ProblemOut
from app.auth import get_current_user
from app.redis_client import get_redis
from app.rating.service import (
    get_cached_leaderboard,
    set_cached_leaderboard,
)

router = APIRouter(prefix="/contests", tags=["contests"])


@router.get("", response_model=list[ContestOut])
async def list_contests(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Contest).order_by(Contest.start_time.desc()))
    return result.scalars().all()


@router.get("/{contest_id}", response_model=ContestOut)
async def get_contest(contest_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Contest).where(Contest.id == contest_id))
    contest = result.scalar_one_or_none()
    if not contest:
        raise HTTPException(status_code=404, detail="Contest not found")
    return contest


@router.get("/{contest_id}/problems", response_model=list[ProblemOut])
async def get_contest_problems(contest_id: UUID, db: AsyncSession = Depends(get_db)):
    from app.models import Problem
    result = await db.execute(
        select(Problem).where(Problem.contest_id == contest_id)
    )
    return result.scalars().all()


@router.get("/{contest_id}/leaderboard", response_model=list[LeaderboardEntry])
async def get_leaderboard(
    contest_id: UUID,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """
    Contest leaderboard: each user's best submission score, with ELO delta if available.
    Results are cached in Redis for 60 seconds.
    """
    # Check Redis cache
    cached = await get_cached_leaderboard(redis, str(contest_id))
    if cached:
        return json.loads(cached)

    # Fetch evaluated submissions, ordered by score
    result = await db.execute(
        select(Submission)
        .where(Submission.contest_id == contest_id)
        .where(Submission.final_score.isnot(None))
        .order_by(Submission.final_score.desc())
    )
    submissions = result.scalars().all()

    # De-duplicate: keep each user's best score
    seen: dict[UUID, Submission] = {}
    for sub in submissions:
        if sub.user_id not in seen:
            seen[sub.user_id] = sub

    # Build leaderboard entries with ELO delta
    entries: list[LeaderboardEntry] = []
    for rank, (uid, sub) in enumerate(seen.items(), start=1):
        user_result = await db.execute(select(User).where(User.id == uid))
        user = user_result.scalar_one()

        # Try to fetch ELO delta from rating_history
        delta_result = await db.execute(
            select(RatingHistory)
            .where(RatingHistory.user_id == uid, RatingHistory.contest_id == contest_id)
        )
        rating_entry = delta_result.scalar_one_or_none()
        elo_delta = rating_entry.delta if rating_entry else None

        entries.append(LeaderboardEntry(
            rank=rank,
            user_id=uid,
            username=user.username,
            rating=user.rating,
            contest_score=sub.final_score,
            delta=elo_delta,
        ))

    # Cache result
    serialized = json.dumps(
        [e.model_dump(mode="json") for e in entries]
    )
    await set_cached_leaderboard(redis, serialized, str(contest_id))

    return entries


# ── SSE Stream for Contest Leaderboard ───────────────────────────────────────

import asyncio
from fastapi.responses import StreamingResponse
from app.redis_client import (
    redis_pool,
    CHANNEL_CONTEST_LEADERBOARD,
)
import redis.asyncio as aioredis


async def _sse_contest_lb_generator(channel: str, fetch_coro):
    """SSE generator for contest leaderboard."""
    try:
        initial = await fetch_coro()
        yield f"data: {json.dumps(initial)}\n\n"
    except Exception:
        yield f"data: []\n\n"

    sub_client = aioredis.Redis(connection_pool=redis_pool)
    pubsub = sub_client.pubsub()
    await pubsub.subscribe(channel)

    try:
        while True:
            msg = await asyncio.wait_for(
                pubsub.get_message(ignore_subscribe_messages=True, timeout=15),
                timeout=20,
            )
            if msg and msg["type"] == "message":
                try:
                    data = await fetch_coro()
                    yield f"data: {json.dumps(data)}\n\n"
                except Exception:
                    pass
            else:
                yield f": heartbeat\n\n"
    except (asyncio.CancelledError, GeneratorExit):
        pass
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()


@router.get("/{contest_id}/leaderboard/stream")
async def stream_contest_leaderboard(
    contest_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """SSE endpoint: streams contest leaderboard updates."""
    async def fetch_contest_lb():
        result = await db.execute(
            select(Submission)
            .where(Submission.contest_id == contest_id)
            .where(Submission.final_score.isnot(None))
            .order_by(Submission.final_score.desc())
        )
        submissions = result.scalars().all()
        seen: dict = {}
        for sub in submissions:
            if str(sub.user_id) not in seen:
                seen[str(sub.user_id)] = sub

        entries = []
        for rank, (uid_str, sub) in enumerate(seen.items(), start=1):
            user_result = await db.execute(
                select(User).where(User.id == sub.user_id)
            )
            user = user_result.scalar_one()
            entries.append({
                "rank": rank,
                "user_id": uid_str,
                "username": user.username,
                "rating": user.rating,
                "contest_score": float(sub.final_score) if sub.final_score else None,
                "delta": None,
            })
        return entries

    channel = CHANNEL_CONTEST_LEADERBOARD.format(contest_id=str(contest_id))
    return StreamingResponse(
        _sse_contest_lb_generator(channel, fetch_contest_lb),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
