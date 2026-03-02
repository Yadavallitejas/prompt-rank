"""
PromptRank — Async Redis Client

Provides a shared Redis connection pool for caching and pub/sub.
"""

import redis.asyncio as aioredis
from app.config import get_settings

settings = get_settings()

redis_pool = aioredis.ConnectionPool.from_url(
    settings.redis_url,
    max_connections=20,
    decode_responses=True,
)

redis_client = aioredis.Redis(connection_pool=redis_pool)

# ── Pub/Sub channel patterns ────────────────────────────────────────────────
CHANNEL_GLOBAL_LEADERBOARD = "leaderboard:global:updates"
CHANNEL_CONTEST_LEADERBOARD = "leaderboard:contest:{contest_id}:updates"


async def get_redis() -> aioredis.Redis:
    """FastAPI dependency — returns the shared async Redis client."""
    return redis_client


async def publish_leaderboard_update(
    client: aioredis.Redis,
    contest_id: str | None = None,
):
    """Publish a notification to the leaderboard Pub/Sub channel."""
    if contest_id:
        channel = CHANNEL_CONTEST_LEADERBOARD.format(contest_id=contest_id)
        await client.publish(channel, "updated")
    # Always publish to the global channel too
    await client.publish(CHANNEL_GLOBAL_LEADERBOARD, "updated")


def publish_leaderboard_update_sync(contest_id: str | None = None):
    """Synchronous version for use inside Celery workers."""
    import redis
    r = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    if contest_id:
        channel = CHANNEL_CONTEST_LEADERBOARD.format(contest_id=contest_id)
        r.publish(channel, "updated")
    r.publish(CHANNEL_GLOBAL_LEADERBOARD, "updated")
    r.close()
