"""
PromptRank — Scoring Engine

Pure-function scoring module implementing all 6 evaluation metrics
from the PRD and Technical Specification:

    Accuracy (40%), Consistency (20%), Format Compliance (15%),
    Token Efficiency (10%), Latency (5%), Robustness (10%)

Final Score = 100 × (0.40×A + 0.20×C + 0.15×F + 0.10×(1−T) + 0.05×(1−L) + 0.10×R)
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from typing import Any


# ── Weights ──────────────────────────────────────────────────────────────────
WEIGHT_ACCURACY = 0.40
WEIGHT_CONSISTENCY = 0.20
WEIGHT_FORMAT = 0.15
WEIGHT_TOKEN_EFFICIENCY = 0.10
WEIGHT_LATENCY = 0.05
WEIGHT_ROBUSTNESS = 0.10


@dataclass
class RunResult:
    """Result from a single LLM run for one testcase."""
    output: str
    tokens_used: int
    latency_ms: int
    is_adversarial: bool = False


@dataclass
class TestcaseResult:
    """Aggregated evaluation of N runs for a single testcase."""
    expected_output: str
    runs: list[RunResult] = field(default_factory=list)
    is_adversarial: bool = False


@dataclass
class ScoringResult:
    """Full scoring breakdown for a submission."""
    accuracy: float = 0.0
    consistency: float = 0.0
    format_compliance: float = 0.0
    token_efficiency: float = 0.0
    latency: float = 0.0
    robustness: float = 0.0
    final_score: float = 0.0

    def to_dict(self) -> dict[str, float]:
        return {
            "accuracy": round(self.accuracy, 4),
            "consistency": round(self.consistency, 4),
            "format_compliance": round(self.format_compliance, 4),
            "token_efficiency": round(self.token_efficiency, 4),
            "latency": round(self.latency, 4),
            "robustness": round(self.robustness, 4),
            "final_score": round(self.final_score, 2),
        }


# ── Format Compliance ────────────────────────────────────────────────────────

def _check_format_compliance(output: str, expected: str) -> float:
    """
    Binary check: is the output valid JSON and does it have the same
    top-level keys as the expected output? Returns 1.0 or 0.0.
    """
    try:
        parsed_output = json.loads(output)
        parsed_expected = json.loads(expected)
    except (json.JSONDecodeError, TypeError):
        return 0.0

    if not isinstance(parsed_output, dict) or not isinstance(parsed_expected, dict):
        # For non-dict JSON (arrays, primitives), just check valid JSON
        return 1.0

    expected_keys = set(parsed_expected.keys())
    output_keys = set(parsed_output.keys())

    # Penalise missing or extra keys
    if expected_keys != output_keys:
        return 0.0

    return 1.0


# ── Accuracy ─────────────────────────────────────────────────────────────────

def _compare_values(actual: Any, expected: Any, tolerance: float = 0.01) -> float:
    """
    Compare two values. Returns 1.0 for a match, 0.0 for a mismatch.
    Supports numeric tolerance and recursive dict/list comparison.
    """
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        if expected == 0:
            return 1.0 if actual == 0 else 0.0
        return 1.0 if abs(actual - expected) / max(abs(expected), 1e-9) <= tolerance else 0.0

    if isinstance(expected, str) and isinstance(actual, str):
        return 1.0 if actual.strip().lower() == expected.strip().lower() else 0.0

    if isinstance(expected, bool) and isinstance(actual, bool):
        return 1.0 if actual == expected else 0.0

    if expected is None:
        return 1.0 if actual is None else 0.0

    if isinstance(expected, list) and isinstance(actual, list):
        if len(expected) == 0:
            return 1.0 if len(actual) == 0 else 0.0
        scores = []
        for i, exp_item in enumerate(expected):
            if i < len(actual):
                scores.append(_compare_values(actual[i], exp_item, tolerance))
            else:
                scores.append(0.0)
        return sum(scores) / len(scores) if scores else 0.0

    if isinstance(expected, dict) and isinstance(actual, dict):
        if not expected:
            return 1.0
        scores = []
        for key in expected:
            if key in actual:
                scores.append(_compare_values(actual[key], expected[key], tolerance))
            else:
                scores.append(0.0)
        return sum(scores) / len(scores) if scores else 0.0

    # Fallback: string comparison
    return 1.0 if str(actual) == str(expected) else 0.0


def _compute_accuracy(output: str, expected: str) -> float:
    """
    Field-by-field accuracy between output and expected JSON.
    Returns 0.0–1.0. Non-JSON outputs get 0.0.
    """
    try:
        parsed_output = json.loads(output)
        parsed_expected = json.loads(expected)
    except (json.JSONDecodeError, TypeError):
        return 0.0

    return _compare_values(parsed_output, parsed_expected)


# ── Consistency ──────────────────────────────────────────────────────────────

def _jaccard_similarity(a: str, b: str) -> float:
    """Token-level Jaccard similarity between two strings."""
    set_a = set(a.lower().split())
    set_b = set(b.lower().split())
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def _compute_consistency(outputs: list[str]) -> float:
    """
    Consistency across N runs:
    Average pairwise Jaccard similarity of outputs.
    High similarity = high consistency.
    """
    if len(outputs) <= 1:
        return 1.0

    similarities = []
    for i in range(len(outputs)):
        for j in range(i + 1, len(outputs)):
            similarities.append(_jaccard_similarity(outputs[i], outputs[j]))

    return sum(similarities) / len(similarities) if similarities else 1.0


# ── Normalization helpers ────────────────────────────────────────────────────

def _normalize_min_max(values: list[float]) -> list[float]:
    """
    Min-max normalize a list of values to 0–1 range.
    Lower original value = lower normalized value.
    """
    if not values:
        return []
    min_val = min(values)
    max_val = max(values)
    spread = max_val - min_val
    if spread == 0:
        return [0.0] * len(values)  # All same → best possible
    return [(v - min_val) / spread for v in values]


# ── Main Scoring Function ───────────────────────────────────────────────────

def score_submission(testcase_results: list[TestcaseResult]) -> ScoringResult:
    """
    Compute the full 6-metric scoring breakdown for a submission.

    Args:
        testcase_results: List of TestcaseResult, each containing N RunResults.

    Returns:
        ScoringResult with all metrics and the final aggregated score.
    """
    if not testcase_results:
        return ScoringResult()

    # Separate normal and adversarial testcases
    normal_results = [tc for tc in testcase_results if not tc.is_adversarial]
    adversarial_results = [tc for tc in testcase_results if tc.is_adversarial]

    # ── Per-testcase metrics ─────────────────────────────────
    all_accuracies: list[float] = []
    all_format_scores: list[float] = []
    all_consistencies: list[float] = []
    all_tokens: list[float] = []
    all_latencies: list[float] = []
    adversarial_accuracies: list[float] = []

    for tc in testcase_results:
        if not tc.runs:
            continue

        # Per-run accuracy and format compliance
        run_accuracies = []
        run_format_scores = []
        run_outputs = []
        run_tokens = []
        run_latencies = []

        for run in tc.runs:
            # Skip LLM errors
            if run.output.startswith("__LLM_ERROR__"):
                run_accuracies.append(0.0)
                run_format_scores.append(0.0)
                run_outputs.append("")
                run_tokens.append(0)
                run_latencies.append(run.latency_ms)
                continue

            acc = _compute_accuracy(run.output, tc.expected_output)
            fmt = _check_format_compliance(run.output, tc.expected_output)
            run_accuracies.append(acc)
            run_format_scores.append(fmt)
            run_outputs.append(run.output)
            run_tokens.append(run.tokens_used)
            run_latencies.append(run.latency_ms)

        # Average accuracy across N runs for this testcase
        tc_accuracy = sum(run_accuracies) / len(run_accuracies) if run_accuracies else 0.0
        tc_format = sum(run_format_scores) / len(run_format_scores) if run_format_scores else 0.0
        tc_consistency = _compute_consistency(run_outputs)

        if tc.is_adversarial:
            adversarial_accuracies.append(tc_accuracy)
        else:
            all_accuracies.append(tc_accuracy)

        all_format_scores.append(tc_format)
        all_consistencies.append(tc_consistency)
        all_tokens.extend(run_tokens)
        all_latencies.extend(run_latencies)

    # ── Aggregate metrics ────────────────────────────────────
    accuracy = sum(all_accuracies) / len(all_accuracies) if all_accuracies else 0.0
    format_compliance = sum(all_format_scores) / len(all_format_scores) if all_format_scores else 0.0
    consistency = sum(all_consistencies) / len(all_consistencies) if all_consistencies else 0.0

    # Token efficiency: normalized (lower = better)
    if all_tokens and max(all_tokens) > min(all_tokens):
        avg_tokens = sum(all_tokens) / len(all_tokens)
        t_norm = (avg_tokens - min(all_tokens)) / (max(all_tokens) - min(all_tokens))
    else:
        t_norm = 0.0  # All equal → best score

    # Latency: normalized (lower = better)
    if all_latencies and max(all_latencies) > min(all_latencies):
        avg_latency = sum(all_latencies) / len(all_latencies)
        l_norm = (avg_latency - min(all_latencies)) / (max(all_latencies) - min(all_latencies))
    else:
        l_norm = 0.0

    # Robustness: accuracy on adversarial testcases
    robustness = (
        sum(adversarial_accuracies) / len(adversarial_accuracies)
        if adversarial_accuracies
        else accuracy  # Fallback: use overall accuracy if no adversarial cases
    )

    # ── Final Score ──────────────────────────────────────────
    final = 100.0 * (
        WEIGHT_ACCURACY * accuracy
        + WEIGHT_CONSISTENCY * consistency
        + WEIGHT_FORMAT * format_compliance
        + WEIGHT_TOKEN_EFFICIENCY * (1.0 - t_norm)
        + WEIGHT_LATENCY * (1.0 - l_norm)
        + WEIGHT_ROBUSTNESS * robustness
    )

    # Clamp to 0–100
    final = max(0.0, min(100.0, final))

    return ScoringResult(
        accuracy=accuracy,
        consistency=consistency,
        format_compliance=format_compliance,
        token_efficiency=1.0 - t_norm,
        latency=1.0 - l_norm,
        robustness=robustness,
        final_score=round(final, 2),
    )
