"""
PromptRank -- Global Leaderboard & Rating History Router

GET  /leaderboard               -- Global leaderboard (all users by ELO rating)
GET  /leaderboard/history/{uid} -- Rating history for a specific user
POST /leaderboard/finalize/{cid} -- Admin: finalize contest ratings (triggers ELO)
"""

import json
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, RatingHistory, Contest
from app.schemas import GlobalLeaderboardEntry, RatingHistoryOut
from app.auth import get_current_user, get_current_admin
from app.redis_client import get_redis

from app.rating.service import (
    get_cached_leaderboard,
    set_cached_leaderboard,
)

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get("", response_model=list[GlobalLeaderboardEntry])
async def get_global_leaderboard(
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """
    Global leaderboard: all users sorted by ELO rating (descending).
    Results are cached in Redis for 60 seconds.
    """
    # Check Redis cache
    cached = await get_cached_leaderboard(redis, contest_id=None)
    if cached:
        return json.loads(cached)

    # Fetch from DB
    result = await db.execute(
        select(User).order_by(User.rating.desc())
    )
    users = result.scalars().all()

    entries = []
    for rank, user in enumerate(users, start=1):
        entries.append(GlobalLeaderboardEntry(
            rank=rank,
            user_id=user.id,
            username=user.username,
            rating=user.rating,
            created_at=user.created_at,
        ))

    # Cache result
    serialized = json.dumps(
        [e.model_dump(mode="json") for e in entries]
    )
    await set_cached_leaderboard(redis, serialized, contest_id=None)

    return entries


@router.get("/history/{user_id}", response_model=list[RatingHistoryOut])
async def get_rating_history(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get the full rating history for a user, ordered chronologically.
    """
    result = await db.execute(
        select(RatingHistory)
        .where(RatingHistory.user_id == user_id)
        .order_by(RatingHistory.created_at.asc())
    )
    history = result.scalars().all()
    return history


@router.post("/finalize/{contest_id}")
async def finalize_contest(
    contest_id: UUID,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    admin: User = Depends(get_current_admin),
):
    """
    Admin-only: finalize a contest's ratings.
    Triggers the ELO computation for all participants.
    """
    # Verify contest exists
    result = await db.execute(select(Contest).where(Contest.id == contest_id))
    contest = result.scalar_one_or_none()
    if not contest:
        raise HTTPException(status_code=404, detail="Contest not found")

    # Run finalization in a sync context (rating service uses sync sessions)
    from app.rating.service import finalize_contest_ratings, invalidate_leaderboard_cache

    # Import sync session from worker
    from app.worker import _get_sync_db

    sync_db = _get_sync_db()
    try:
        deltas = finalize_contest_ratings(sync_db, str(contest_id))
    finally:
        sync_db.close()

    # Invalidate caches
    await invalidate_leaderboard_cache(redis, str(contest_id))

    return {
        "contest_id": str(contest_id),
        "participants": len(deltas),
        "rating_changes": [
            {
                "user_id": d.user_id,
                "rating_before": d.rating_before,
                "rating_after": d.rating_after,
                "delta": d.delta,
            }
            for d in deltas
        ],
    }


# ── SSE Stream Endpoints ─────────────────────────────────────────────────────

import asyncio
from fastapi.responses import StreamingResponse
from app.redis_client import (
    redis_pool,
    CHANNEL_GLOBAL_LEADERBOARD,
    CHANNEL_CONTEST_LEADERBOARD,
)
import redis.asyncio as aioredis


async def _sse_leaderboard_generator(channel: str, fetch_data_coro):
    """
    Generic SSE generator: subscribes to a Redis Pub/Sub channel,
    sends a heartbeat every 15s, and pushes the full leaderboard
    JSON whenever a notification arrives.
    """
    # Send initial data immediately
    try:
        initial = await fetch_data_coro()
        yield f"data: {json.dumps(initial)}\n\n"
    except Exception:
        yield f"data: []\n\n"

    # Subscribe to Pub/Sub channel
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
                # New data available — fetch and send
                try:
                    data = await fetch_data_coro()
                    yield f"data: {json.dumps(data)}\n\n"
                except Exception:
                    pass
            else:
                # Heartbeat to keep connection alive
                yield f": heartbeat\n\n"
    except (asyncio.CancelledError, GeneratorExit):
        pass
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()


@router.get("/stream")
async def stream_global_leaderboard(
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """SSE endpoint: streams global leaderboard updates in real-time."""
    async def fetch_global():
        result = await db.execute(select(User).order_by(User.rating.desc()))
        users = result.scalars().all()
        return [
            {
                "rank": i,
                "user_id": str(u.id),
                "username": u.username,
                "rating": u.rating,
                "created_at": u.created_at.isoformat(),
            }
            for i, u in enumerate(users, 1)
        ]

    return StreamingResponse(
        _sse_leaderboard_generator(CHANNEL_GLOBAL_LEADERBOARD, fetch_global),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
