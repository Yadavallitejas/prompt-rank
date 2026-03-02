"""
Shared pytest fixtures for PromptRank test suites.
"""

import json
import sys
import pytest

sys.path.insert(0, ".")


# ── Scoring Fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def perfect_run():
    """A RunResult with perfect output matching expected."""
    from app.scoring.engine import RunResult
    def _factory(expected_json: dict, tokens: int = 100, latency: int = 200):
        return RunResult(
            output=json.dumps(expected_json),
            tokens_used=tokens,
            latency_ms=latency,
        )
    return _factory


@pytest.fixture
def error_run():
    """A RunResult simulating an LLM error."""
    from app.scoring.engine import RunResult
    return RunResult(
        output="__LLM_ERROR__: model timeout",
        tokens_used=0,
        latency_ms=5000,
    )


@pytest.fixture
def make_testcase():
    """Factory fixture to create TestcaseResult objects."""
    from app.scoring.engine import TestcaseResult, RunResult
    def _factory(
        expected: dict,
        outputs: list | None = None,
        is_adversarial: bool = False,
        tokens: int = 100,
        latency: int = 200,
    ):
        if outputs is None:
            outputs = [expected]
        runs = []
        for out in outputs:
            if isinstance(out, dict):
                out_str = json.dumps(out)
            else:
                out_str = out
            runs.append(RunResult(output=out_str, tokens_used=tokens, latency_ms=latency))
        return TestcaseResult(
            expected_output=json.dumps(expected),
            runs=runs,
            is_adversarial=is_adversarial,
        )
    return _factory


# ── Rating Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def make_player():
    """Factory fixture to create PlayerResult objects."""
    from app.rating.engine import PlayerResult
    def _factory(user_id: str, rating: int = 1200, score: float = 50.0):
        return PlayerResult(
            user_id=user_id,
            current_rating=rating,
            contest_score=score,
        )
    return _factory

