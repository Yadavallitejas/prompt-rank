"""
PromptRank — FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers import auth, contests, submissions, admin, leaderboard, problems

app = FastAPI(
    title="PromptRank",
    description="Competitive prompt engineering platform — API",
    version="1.0.0",
)

# ── CORS (allow Next.js frontend in development) ────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routers ────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(contests.router)
app.include_router(submissions.router)
app.include_router(admin.router)
app.include_router(leaderboard.router)
app.include_router(problems.router)


@app.get("/health")
async def health_check():
    """
    Deep health check: verifies DB and Redis connectivity.
    Returns 200 if all healthy, 503 if any component is down.
    """
    status = {"service": "promptrank-api"}
    all_healthy = True

    # ── Database check ──────────────────────────────────
    try:
        from app.database import engine as async_engine
        from sqlalchemy import text
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        status["database"] = "ok"
    except Exception as e:
        status["database"] = f"error: {str(e)[:100]}"
        all_healthy = False

    # ── Redis check ─────────────────────────────────────
    try:
        from app.redis_client import redis_client
        pong = await redis_client.ping()
        status["redis"] = "ok" if pong else "error: no pong"
        if not pong:
            all_healthy = False
    except Exception as e:
        status["redis"] = f"error: {str(e)[:100]}"
        all_healthy = False

    status["status"] = "healthy" if all_healthy else "degraded"

    if all_healthy:
        return status
    return JSONResponse(status_code=503, content=status)

