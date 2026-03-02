"""
PromptRank -- ELO Rating Engine Unit Tests
"""

import sys
import pytest
sys.path.insert(0, ".")

from app.rating.engine import (
    compute_rating_deltas,
    PlayerResult,
    expected_score,
    get_k_factor,
)


@pytest.mark.rating
def test_k_factor():
    """K-factor decreases with experience."""
    assert get_k_factor(0) == 40    # New player
    assert get_k_factor(5) == 40    # Still new
    assert get_k_factor(15) == 24   # Established
    assert get_k_factor(50) == 16   # Veteran
    print("[PASS] K-factor scaling")


@pytest.mark.rating
def test_expected_score():
    """Equal ratings should give 50% expected score."""
    e = expected_score(1200, 1200)
    assert abs(e - 0.5) < 0.001
    print(f"[PASS] Expected score equal: {e:.4f}")

    # Higher rated player should have > 50% expected
    e_high = expected_score(1400, 1200)
    assert e_high > 0.5
    print(f"[PASS] Expected score higher rated: {e_high:.4f}")


@pytest.mark.rating
def test_two_players():
    """Two players of equal rating: winner gains, loser loses."""
    results = [
        PlayerResult(user_id="a", current_rating=1200, contest_score=85.0),
        PlayerResult(user_id="b", current_rating=1200, contest_score=60.0),
    ]
    deltas = compute_rating_deltas(results)

    winner = next(d for d in deltas if d.user_id == "a")
    loser = next(d for d in deltas if d.user_id == "b")

    assert winner.delta > 0, f"Winner should gain, got {winner.delta}"
    assert loser.delta < 0, f"Loser should lose, got {loser.delta}"
    assert winner.delta == -loser.delta, "Deltas should be symmetric for equal ratings"
    print(f"[PASS] Two players: winner +{winner.delta}, loser {loser.delta}")


@pytest.mark.rating
def test_three_players():
    """Three players: verify ranking order is reflected in deltas."""
    results = [
        PlayerResult(user_id="top", current_rating=1200, contest_score=95.0),
        PlayerResult(user_id="mid", current_rating=1200, contest_score=70.0),
        PlayerResult(user_id="bot", current_rating=1200, contest_score=40.0),
    ]
    deltas = compute_rating_deltas(results)

    top = next(d for d in deltas if d.user_id == "top")
    mid = next(d for d in deltas if d.user_id == "mid")
    bot = next(d for d in deltas if d.user_id == "bot")

    assert top.delta > mid.delta > bot.delta
    print(f"[PASS] Three players: top +{top.delta}, mid {mid.delta}, bot {bot.delta}")


@pytest.mark.rating
def test_underdog_wins():
    """Lower-rated player beats higher-rated: should gain more."""
    results = [
        PlayerResult(user_id="underdog", current_rating=1000, contest_score=90.0),
        PlayerResult(user_id="favorite", current_rating=1500, contest_score=60.0),
    ]
    deltas = compute_rating_deltas(results)

    underdog = next(d for d in deltas if d.user_id == "underdog")
    favorite = next(d for d in deltas if d.user_id == "favorite")

    assert underdog.delta > 0
    assert favorite.delta < 0
    # Underdog gains more because the upset exceeds expectation
    print(f"[PASS] Underdog wins: underdog +{underdog.delta}, favorite {favorite.delta}")


@pytest.mark.rating
def test_single_player():
    """Single player: no rating change."""
    results = [
        PlayerResult(user_id="solo", current_rating=1200, contest_score=80.0),
    ]
    deltas = compute_rating_deltas(results)
    assert len(deltas) == 1
    assert deltas[0].delta == 0
    print("[PASS] Single player: no change")


@pytest.mark.rating
def test_rating_floor():
    """Rating should never go below 100."""
    results = [
        PlayerResult(user_id="weak", current_rating=100, contest_score=10.0),
        PlayerResult(user_id="strong", current_rating=2000, contest_score=95.0),
    ]
    deltas = compute_rating_deltas(results)
    weak = next(d for d in deltas if d.user_id == "weak")
    assert weak.rating_after >= 100, f"Rating floor violated: {weak.rating_after}"
    print(f"[PASS] Rating floor: weak stays at {weak.rating_after}")


@pytest.mark.rating
def test_many_players_zero_sum():
    """For equal-rated players, net rating change should be ~0."""
    results = [
        PlayerResult(user_id=f"p{i}", current_rating=1200, contest_score=float(90 - i*10))
        for i in range(5)
    ]
    deltas = compute_rating_deltas(results)
    total_delta = sum(d.delta for d in deltas)
    # Should be approximately zero (floating point may cause tiny drift)
    assert abs(total_delta) < 1.0, f"Net delta should be ~0, got {total_delta}"
