"""
PromptRank -- Rating Service

Orchestrates the end-of-contest rating update flow:
  1. Gather all evaluated submissions for the contest
  2. Build the best-score-per-user ranking
  3. Run the ELO engine to compute deltas
  4. Persist RatingHistory rows and update User.rating
  5. Invalidate Redis leaderboard cache
"""

from __future__ import annotations

import uuid
from sqlalchemy import select, func, update
from sqlalchemy.orm import Session

from app.models import (
    User, Contest, Submission, RatingHistory,
    ContestStatus, SubmissionStatus,
)
from app.rating.engine import (
    compute_rating_deltas,
    PlayerResult,
    RatingDelta,
)

# Redis cache key patterns
CONTEST_LEADERBOARD_KEY = "leaderboard:contest:{contest_id}"
GLOBAL_LEADERBOARD_KEY = "leaderboard:global"
LEADERBOARD_TTL = 60  # seconds


def finalize_contest_ratings(
    db: Session,
    contest_id: str,
) -> list[RatingDelta]:
    """
    Finalise ratings for a ended contest.

    Steps:
        1. Fetch all evaluated submissions for the contest
        2. Pick each user's best submission (highest final_score)
        3. Count each user's prior contests for K-factor
        4. Run ELO calculation
        5. Persist RatingHistory and update User.rating
        6. Mark contest as ended

    Args:
        db: Synchronous SQLAlchemy session
        contest_id: UUID string of the contest to finalise

    Returns:
        List of RatingDelta with computed changes
    """
    cid = uuid.UUID(contest_id)

    # ── 1. Fetch all evaluated submissions ───────────────────
    submissions = db.execute(
        select(Submission)
        .where(
            Submission.contest_id == cid,
            Submission.status == SubmissionStatus.evaluated,
            Submission.final_score.isnot(None),
        )
        .order_by(Submission.final_score.desc())
    ).scalars().all()

    if not submissions:
        return []

    # ── 2. Best score per user ───────────────────────────────
    best_per_user: dict[str, float] = {}
    for sub in submissions:
        uid = str(sub.user_id)
        if uid not in best_per_user:
            best_per_user[uid] = sub.final_score

    if len(best_per_user) < 2:
        return []  # Need at least 2 participants

    # ── 3. Build player results with prior contest count ─────
    player_results: list[PlayerResult] = []
    for uid_str, best_score in best_per_user.items():
        uid = uuid.UUID(uid_str)
        user = db.execute(select(User).where(User.id == uid)).scalar_one()

        # Count prior contests (distinct contest_ids in rating_history)
        prior_count = db.execute(
            select(func.count(func.distinct(RatingHistory.contest_id)))
            .where(RatingHistory.user_id == uid)
        ).scalar() or 0

        player_results.append(PlayerResult(
            user_id=uid_str,
            current_rating=user.rating,
            contest_score=best_score,
            contests_played=prior_count,
        ))

    # ── 4. Compute ELO deltas ────────────────────────────────
    deltas = compute_rating_deltas(player_results)

    # ── 5. Persist rating changes ────────────────────────────
    for delta in deltas:
        uid = uuid.UUID(delta.user_id)

        # Insert RatingHistory row
        history = RatingHistory(
            user_id=uid,
            contest_id=cid,
            rating_before=delta.rating_before,
            rating_after=delta.rating_after,
            delta=delta.delta,
        )
        db.add(history)

        # Update user rating
        db.execute(
            update(User)
            .where(User.id == uid)
            .values(rating=delta.rating_after)
        )

    # ── 6. Mark contest as ended ─────────────────────────────
    db.execute(
        update(Contest)
        .where(Contest.id == cid)
        .values(status=ContestStatus.ended)
    )

    db.commit()
    return deltas


async def get_cached_leaderboard(redis_client, contest_id: str | None = None):
    """
    Try to retrieve a leaderboard from Redis cache.

    Args:
        redis_client: Async Redis client
        contest_id: If provided, fetch contest-specific leaderboard.
                    If None, fetch global leaderboard.

    Returns:
        Cached JSON string or None if cache miss.
    """
    if contest_id:
        key = CONTEST_LEADERBOARD_KEY.format(contest_id=contest_id)
    else:
        key = GLOBAL_LEADERBOARD_KEY

    return await redis_client.get(key)


async def set_cached_leaderboard(
    redis_client,
    data: str,
    contest_id: str | None = None,
):
    """
    Store a leaderboard in Redis cache with TTL, then notify SSE listeners.
    """
    if contest_id:
        key = CONTEST_LEADERBOARD_KEY.format(contest_id=contest_id)
    else:
        key = GLOBAL_LEADERBOARD_KEY

    await redis_client.set(key, data, ex=LEADERBOARD_TTL)

    # Notify SSE listeners via Pub/Sub
    from app.redis_client import publish_leaderboard_update
    await publish_leaderboard_update(redis_client, contest_id=contest_id)


async def invalidate_leaderboard_cache(redis_client, contest_id: str | None = None):
    """
    Invalidate leaderboard cache after rating updates.
    """
    if contest_id:
        await redis_client.delete(
            CONTEST_LEADERBOARD_KEY.format(contest_id=contest_id)
        )
    await redis_client.delete(GLOBAL_LEADERBOARD_KEY)
