"""
PromptRank — Celery Worker & Evaluation Pipeline

This module implements the full evaluation pipeline:
  1. Fetch submission + problem + hidden testcases from DB
  2. Update status → running
  3. For each testcase: run LLM N times with deterministic seeds
  4. Score using scoring.engine (6 metrics)
  5. Persist metrics_json + final_score, update status → evaluated
  6. Error handling with retries
"""

import asyncio
import uuid
import traceback

from celery import Celery
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session

from app.config import get_settings
from app.models import Submission, Problem, Testcase, Run, Contest, SubmissionStatus
from app.database import Base
from app.llm.factory import get_llm_provider
from app.scoring.engine import (
    score_submission,
    TestcaseResult,
    RunResult,
)

settings = get_settings()

# ── Celery App ───────────────────────────────────────────────────────────────

celery_app = Celery(
    "promptrank",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


# ── Synchronous DB session for Celery workers ───────────────────────────────
# Celery tasks are sync; we use a sync engine for DB access inside workers.

_sync_url = settings.database_url.replace("+asyncpg", "")
_sync_engine = create_engine(_sync_url, pool_size=5, max_overflow=5)
SyncSession = sessionmaker(bind=_sync_engine)


def _get_sync_db() -> Session:
    """Create a new sync session for use inside a Celery task."""
    return SyncSession()


# ── Async helper ─────────────────────────────────────────────────────────────
# The LLM provider is async; we need a way to call it from sync Celery tasks.

def _run_async(coro):
    """Run an async coroutine from a sync Celery task."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If there's already a running loop (shouldn't happen in Celery)
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


# ── Main Evaluation Task ────────────────────────────────────────────────────

@celery_app.task(name="evaluate_submission", bind=True, max_retries=3)
def evaluate_submission(self, submission_id: str):
    """
    Full evaluation pipeline for a submission.
    """
    db = _get_sync_db()

    try:
        # ── 1. Fetch submission ──────────────────────────────
        submission = db.execute(
            select(Submission).where(Submission.id == uuid.UUID(submission_id))
        ).scalar_one_or_none()

        if not submission:
            return {"error": f"Submission {submission_id} not found"}

        # ── 2. Update status → running ───────────────────────
        submission.status = SubmissionStatus.running
        db.commit()

        # ── 3. Fetch problem and testcases ───────────────────
        problem = db.execute(
            select(Problem).where(Problem.id == submission.problem_id)
        ).scalar_one_or_none()

        if not problem:
            submission.status = SubmissionStatus.failed
            submission.metrics_json = {"error": "Problem not found"}
            db.commit()
            return {"error": "Problem not found"}

        testcases = db.execute(
            select(Testcase).where(Testcase.problem_id == problem.id)
        ).scalars().all()

        if not testcases:
            submission.status = SubmissionStatus.failed
            submission.metrics_json = {"error": "No testcases found"}
            db.commit()
            return {"error": "No testcases found"}

        # ── Anti-cheat: Randomize testcase ordering ──────────
        import random
        rng = random.Random(submission_id)  # Deterministic per submission
        testcases = list(testcases)
        rng.shuffle(testcases)

        # ── 4. Get contest settings (or defaults) ────────────
        seed_base = settings.eval_sampling_n  # default seed
        temperature = settings.eval_fixed_temperature
        max_tokens = settings.eval_max_tokens
        sampling_n = settings.eval_sampling_n
        model = settings.llm_default_model

        if submission.contest_id:
            contest = db.execute(
                select(Contest).where(Contest.id == submission.contest_id)
            ).scalar_one_or_none()
            if contest:
                seed_base = contest.seed_base
                temperature = contest.temperature
                model = contest.allowed_model

        # ── 5. Get LLM provider ──────────────────────────────
        llm = get_llm_provider()

        # ── 6. Run evaluation loop ───────────────────────────
        testcase_results: list[TestcaseResult] = []

        for testcase in testcases:
            tc_result = TestcaseResult(
                expected_output=testcase.expected_output_blob,
                is_adversarial=testcase.is_adversarial,
            )

            for run_index in range(sampling_n):
                seed = seed_base + run_index

                # Call LLM (async via wrapper)
                llm_response = _run_async(
                    llm.run(
                        system_prompt=submission.prompt_text,
                        user_input=testcase.input_blob,
                        model=model,
                        temperature=temperature,
                        seed=seed,
                        max_tokens=max_tokens,
                    )
                )

                # Determine pass/fail
                passed = not llm_response.content.startswith("__LLM_ERROR__")

                # Save Run record
                run = Run(
                    submission_id=submission.id,
                    testcase_id=testcase.id,
                    run_index=run_index,
                    output_blob=llm_response.content,
                    tokens_used=llm_response.tokens_used,
                    latency_ms=llm_response.latency_ms,
                    passed_bool=passed,
                )
                db.add(run)

                tc_result.runs.append(RunResult(
                    output=llm_response.content,
                    tokens_used=llm_response.tokens_used,
                    latency_ms=llm_response.latency_ms,
                    is_adversarial=testcase.is_adversarial,
                ))

            testcase_results.append(tc_result)

        # ── 7. Compute scores ────────────────────────────────
        scoring_result = score_submission(testcase_results)

        # ── 8. Persist results ───────────────────────────────
        submission.final_score = scoring_result.final_score
        submission.metrics_json = scoring_result.to_dict()
        submission.status = SubmissionStatus.evaluated
        db.commit()

        # ── 9. Publish leaderboard update via Redis Pub/Sub ──
        try:
            from app.redis_client import publish_leaderboard_update_sync
            contest_id_str = str(submission.contest_id) if submission.contest_id else None
            publish_leaderboard_update_sync(contest_id=contest_id_str)
        except Exception:
            pass  # Non-critical: don't fail submission on pub/sub errors

        return {
            "status": "evaluated",
            "submission_id": submission_id,
            "final_score": scoring_result.final_score,
            "metrics": scoring_result.to_dict(),
        }

    except Exception as exc:
        db.rollback()
        # Try to mark as failed
        try:
            submission = db.execute(
                select(Submission).where(Submission.id == uuid.UUID(submission_id))
            ).scalar_one_or_none()
            if submission:
                submission.status = SubmissionStatus.failed
                submission.metrics_json = {"error": str(exc), "traceback": traceback.format_exc()}
                db.commit()
        except Exception:
            pass

        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries * 10)

    finally:
        db.close()
