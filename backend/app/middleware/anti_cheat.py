"""
PromptRank — Anti-Cheat Module

Provides:
  - IP-based rate throttling (Redis sliding window)
  - Duplicate prompt detection (hash-based)
"""

import hashlib
from fastapi import HTTPException, Request
from app.redis_client import redis_client


# ── Configuration ────────────────────────────────────────────────────────────

IP_WINDOW_SECONDS = 300   # 5 minutes
IP_MAX_SUBMISSIONS = 10   # max submissions per IP per window
IP_KEY_PREFIX = "anticheat:ip:"

DUPE_KEY_PREFIX = "anticheat:dupe:"
DUPE_TTL = 3600  # 1 hour TTL for duplicate hashes


# ── IP Rate Throttle ─────────────────────────────────────────────────────────

async def check_ip_rate_limit(request: Request):
    """
    Sliding-window rate limit per IP address.
    Raises 429 if exceeded.
    """
    client_ip = request.client.host if request.client else "unknown"
    key = f"{IP_KEY_PREFIX}{client_ip}"

    pipe = redis_client.pipeline()
    pipe.incr(key)
    pipe.ttl(key)
    results = await pipe.execute()

    count = results[0]
    ttl = results[1]

    # Set expiry on first request in window
    if ttl == -1:
        await redis_client.expire(key, IP_WINDOW_SECONDS)

    if count > IP_MAX_SUBMISSIONS:
        raise HTTPException(
            status_code=429,
            detail=f"Too many submissions. Max {IP_MAX_SUBMISSIONS} per {IP_WINDOW_SECONDS // 60} minutes.",
        )


# ── Duplicate Prompt Detection ───────────────────────────────────────────────

async def check_duplicate_prompt(user_id: str, problem_id: str, prompt_text: str):
    """
    Reject identical prompts submitted by the same user for the same problem.
    Uses SHA-256 hash of the normalized prompt text.
    Raises 409 if duplicate found.
    """
    normalized = prompt_text.strip().lower()
    prompt_hash = hashlib.sha256(
        f"{user_id}:{problem_id}:{normalized}".encode()
    ).hexdigest()

    key = f"{DUPE_KEY_PREFIX}{prompt_hash}"

    exists = await redis_client.exists(key)
    if exists:
        raise HTTPException(
            status_code=409,
            detail="This prompt has already been submitted. Please modify your prompt and try again.",
        )

    # Mark this prompt hash as used
    await redis_client.set(key, "1", ex=DUPE_TTL)
