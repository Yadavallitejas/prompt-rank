"""
PromptRank -- ELO Rating Engine

Implements ELO-style rating calculations for competitive prompt engineering.

The system uses a modified ELO algorithm:
  - K-factor scales inversely with the number of contests a player has competed in
  - Expected score is computed using the standard logistic function
  - Score outcome is based on normalised contest placement (0.0 to 1.0)

Reference: https://en.wikipedia.org/wiki/Elo_rating_system
"""

from __future__ import annotations

import math
from dataclasses import dataclass


# ── Constants ────────────────────────────────────────────────────────────────

# K-factor range: new players change faster, veterans change slower
K_FACTOR_NEW = 40       # For players with < 10 contests
K_FACTOR_ESTABLISHED = 24  # For players with 10-30 contests
K_FACTOR_VETERAN = 16   # For players with > 30 contests

# ELO scaling factor (standard chess uses 400)
ELO_SCALE = 400.0

# Default starting rating
DEFAULT_RATING = 1200


@dataclass
class PlayerResult:
    """A single player's result in a contest."""
    user_id: str
    current_rating: int
    contest_score: float       # Raw final_score from evaluation (0-100)
    contests_played: int = 0   # Number of prior contests (for K-factor)


@dataclass
class RatingDelta:
    """Computed rating change for one player."""
    user_id: str
    rating_before: int
    rating_after: int
    delta: int


def get_k_factor(contests_played: int) -> int:
    """
    Dynamic K-factor based on experience.
    New players have higher volatility.
    """
    if contests_played < 10:
        return K_FACTOR_NEW
    elif contests_played <= 30:
        return K_FACTOR_ESTABLISHED
    else:
        return K_FACTOR_VETERAN


def expected_score(rating_a: int, rating_b: int) -> float:
    """
    Standard ELO expected score for player A against player B.
    Returns probability (0.0 to 1.0) that A wins.
    """
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / ELO_SCALE))


def compute_rating_deltas(results: list[PlayerResult]) -> list[RatingDelta]:
    """
    Compute ELO rating changes for all participants in a contest.

    The algorithm:
    1. Rank players by contest_score (descending)
    2. For each player, compute their "actual score" based on placement:
       - actual_score = (N - rank) / (N - 1) for N players
         This gives 1.0 to the winner, 0.0 to the last place
    3. For each player, compute their "expected score" as the average
       expected outcome against all other players
    4. Apply the ELO formula: delta = K * (actual - expected)

    Args:
        results: List of PlayerResult for all contest participants.

    Returns:
        List of RatingDelta containing the computed changes.
    """
    if len(results) < 2:
        # Need at least 2 players to compute ratings
        return [
            RatingDelta(
                user_id=r.user_id,
                rating_before=r.current_rating,
                rating_after=r.current_rating,
                delta=0,
            )
            for r in results
        ]

    n = len(results)

    # Sort by contest_score descending to determine placement
    sorted_results = sorted(results, key=lambda r: r.contest_score, reverse=True)

    # Assign placement-based actual scores
    actual_scores: dict[str, float] = {}
    for rank_idx, player in enumerate(sorted_results):
        # Normalize rank to 0-1: top player gets 1.0, bottom gets 0.0
        actual_scores[player.user_id] = (n - 1 - rank_idx) / (n - 1)

    # Compute expected scores (average expected outcome vs all opponents)
    expected_scores: dict[str, float] = {}
    for player in results:
        total_expected = 0.0
        for opponent in results:
            if opponent.user_id == player.user_id:
                continue
            total_expected += expected_score(player.current_rating, opponent.current_rating)
        # Average expected score across all opponents
        expected_scores[player.user_id] = total_expected / (n - 1)

    # Compute deltas
    deltas: list[RatingDelta] = []
    for player in sorted_results:
        k = get_k_factor(player.contests_played)
        actual = actual_scores[player.user_id]
        expected = expected_scores[player.user_id]

        raw_delta = k * (actual - expected)
        delta = round(raw_delta)

        new_rating = max(100, player.current_rating + delta)  # Floor at 100

        deltas.append(RatingDelta(
            user_id=player.user_id,
            rating_before=player.current_rating,
            rating_after=new_rating,
            delta=new_rating - player.current_rating,
        ))

    return deltas
