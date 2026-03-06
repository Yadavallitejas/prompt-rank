"""
PromptRank — Scoring Engine

Pure-function scoring module implementing all 6 evaluation metrics
from the PRD and Technical Specification:

    Accuracy (40%), Consistency (20%), Format Compliance (15%),
    Token Efficiency (10%), Latency (5%), Robustness (10%)

Final Score = 100 × (0.40×A + 0.20×C + 0.15×F + 0.10×(1−T) + 0.05×(1−L) + 0.10×R)

Anti-cheat: Test-case leakage detection penalises prompts that embed
expected output text directly.
"""

from __future__ import annotations

import difflib
import json
import logging
import math
import re
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


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
    leakage_detected: bool = False
    leakage_overlap: float = 0.0

    def to_dict(self) -> dict[str, float]:
        d: dict[str, Any] = {
            "accuracy": round(self.accuracy, 4),
            "consistency": round(self.consistency, 4),
            "format_compliance": round(self.format_compliance, 4),
            "token_efficiency": round(self.token_efficiency, 4),
            "latency": round(self.latency, 4),
            "robustness": round(self.robustness, 4),
            "final_score": round(self.final_score, 2),
        }
        if self.leakage_detected:
            d["leakage_detected"] = True
            d["leakage_overlap"] = self.leakage_overlap
        return d


# ── Helper: detect if a string is JSON ──────────────────────────────────────

def _is_json(text: str) -> bool:
    """Check whether text is valid JSON."""
    try:
        json.loads(text)
        return True
    except (json.JSONDecodeError, TypeError):
        return False


# ── Text Similarity Helpers ─────────────────────────────────────────────────

def _token_overlap(output: str, expected: str) -> float:
    """
    Compute token-level overlap (F1-style) between output and expected.
    This gives partial credit for outputs that contain the right information.
    """
    out_tokens = output.lower().split()
    exp_tokens = expected.lower().split()
    if not exp_tokens:
        return 1.0 if not out_tokens else 0.0
    if not out_tokens:
        return 0.0
    out_set = set(out_tokens)
    exp_set = set(exp_tokens)
    common = out_set & exp_set
    if not common:
        return 0.0
    precision = len(common) / len(out_set)
    recall = len(common) / len(exp_set)
    return 2 * precision * recall / (precision + recall)


def _extract_final_answer(text: str) -> str | None:
    """
    Extract the value after 'Answer:' line in the output.
    Returns None if no answer line is found.
    """
    for line in text.strip().splitlines():
        line_stripped = line.strip()
        match = re.match(r'^[Aa]nswer\s*:\s*(.+)$', line_stripped)
        if match:
            return match.group(1).strip()
    return None


def _normalize_number(s: str) -> float | None:
    """Try to parse a string as a number, stripping currency symbols etc."""
    cleaned = re.sub(r'[,$%\s]', '', s)
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


# ── Format Compliance ────────────────────────────────────────────────────────

def _check_format_compliance(output: str, expected: str) -> float:
    """
    Check if output follows the same structural format as expected.
    For JSON: same top-level keys. For plain text: structural similarity.
    """
    expected_is_json = _is_json(expected)
    output_is_json = _is_json(output)

    # ── JSON mode ────────────────────────────────────────────
    if expected_is_json:
        if not output_is_json:
            return 0.0
        parsed_output = json.loads(output)
        parsed_expected = json.loads(expected)
        if not isinstance(parsed_output, dict) or not isinstance(parsed_expected, dict):
            return 1.0
        expected_keys = set(parsed_expected.keys())
        output_keys = set(parsed_output.keys())
        if expected_keys != output_keys:
            return 0.0
        return 1.0

    # ── Plain-text mode ──────────────────────────────────────
    # Check structural similarity: line count, presence of key patterns
    out_stripped = output.strip()
    exp_stripped = expected.strip()

    if not out_stripped:
        return 0.0

    score = 0.0
    checks = 0

    # Check 1: Does the output have a similar number of lines?
    exp_lines = exp_stripped.splitlines()
    out_lines = out_stripped.splitlines()
    if len(exp_lines) > 0:
        checks += 1
        line_ratio = min(len(out_lines), len(exp_lines)) / max(len(out_lines), len(exp_lines))
        score += line_ratio

    # Check 2: If expected has "Answer:" line, does output?
    exp_answer = _extract_final_answer(exp_stripped)
    if exp_answer is not None:
        checks += 1
        out_answer = _extract_final_answer(out_stripped)
        if out_answer is not None:
            score += 1.0

    # Check 3: If expected has numbered steps (1., 2., 3.), does output?
    exp_numbered = len(re.findall(r'^\s*\d+[\.\)]\s', exp_stripped, re.MULTILINE))
    if exp_numbered > 0:
        checks += 1
        out_numbered = len(re.findall(r'^\s*\d+[\.\)]\s', out_stripped, re.MULTILINE))
        if out_numbered > 0:
            ratio = min(out_numbered, exp_numbered) / max(out_numbered, exp_numbered)
            score += ratio

    # Check 4: If expected is a single-word/line, output should also be short
    if len(exp_lines) == 1 and len(exp_stripped.split()) <= 3:
        checks += 1
        if len(out_lines) == 1 and len(out_stripped.split()) <= 5:
            score += 1.0

    if checks == 0:
        # Fallback: basic non-empty check
        return 1.0 if out_stripped else 0.0

    return score / checks


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


def _compute_text_accuracy(output: str, expected: str) -> float:
    """
    Compute accuracy for plain-text (non-JSON) outputs using a
    multi-signal approach:
      1. Exact match → 1.0
      2. If expected has an "Answer:" line, compare final answers (heavy weight)
      3. Token-overlap similarity for the full text
      4. Sequence similarity (difflib) for structural matching
    """
    out_stripped = output.strip()
    exp_stripped = expected.strip()

    # Exact match
    if out_stripped.lower() == exp_stripped.lower():
        return 1.0

    signals: list[float] = []
    weights: list[float] = []

    # Signal 1: Final answer comparison (if applicable)
    exp_answer = _extract_final_answer(exp_stripped)
    if exp_answer is not None:
        out_answer = _extract_final_answer(out_stripped)
        if out_answer is not None:
            # Try numeric comparison
            exp_num = _normalize_number(exp_answer)
            out_num = _normalize_number(out_answer)
            if exp_num is not None and out_num is not None:
                if exp_num == 0:
                    ans_score = 1.0 if out_num == 0 else 0.0
                else:
                    ans_score = 1.0 if abs(out_num - exp_num) / max(abs(exp_num), 1e-9) <= 0.01 else 0.0
            else:
                # String comparison of answer
                ans_score = 1.0 if out_answer.lower() == exp_answer.lower() else 0.0
            signals.append(ans_score)
            weights.append(0.60)  # Final answer is most important
        else:
            signals.append(0.0)
            weights.append(0.60)

    # Signal 2: Token overlap (captures whether the right info is present)
    tok_sim = _token_overlap(out_stripped, exp_stripped)
    signals.append(tok_sim)
    weights.append(0.25 if exp_answer is not None else 0.50)

    # Signal 3: Sequence similarity (captures ordering and structure)
    seq_sim = difflib.SequenceMatcher(None, out_stripped.lower(), exp_stripped.lower()).ratio()
    signals.append(seq_sim)
    weights.append(0.15 if exp_answer is not None else 0.50)

    if not weights:
        return 0.0

    total_weight = sum(weights)
    return sum(s * w for s, w in zip(signals, weights)) / total_weight


def _compute_accuracy(output: str, expected: str) -> float:
    """
    Accuracy between output and expected.
    Uses JSON field-by-field comparison when both are valid JSON,
    otherwise falls back to text-based similarity.
    Returns 0.0–1.0.
    """
    expected_is_json = _is_json(expected)
    output_is_json = _is_json(output)

    # Both JSON → structured comparison
    if expected_is_json and output_is_json:
        parsed_output = json.loads(output)
        parsed_expected = json.loads(expected)
        return _compare_values(parsed_output, parsed_expected)

    # Expected is JSON but output is not → low accuracy (wrong format)
    if expected_is_json and not output_is_json:
        return 0.0

    # Plain-text comparison (expected is not JSON)
    return _compute_text_accuracy(output, expected)


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
    # All empty outputs (e.g. all LLM errors) → no meaningful consistency
    non_empty = [o for o in outputs if o.strip()]
    if not non_empty:
        return 0.0
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


# ── Test-case leakage detection ─────────────────────────────────────────────

LEAKAGE_THRESHOLD = 0.6  # If ≥60 % of expected-output tokens appear in prompt → leakage
MIN_EXPECTED_TOKENS = 5  # Skip very short expected outputs to avoid false positives
MIN_OVERLAP_TOKENS = 4   # Require at least this many overlapping tokens


def _tokenize(text: str) -> list[str]:
    """Simple whitespace + punctuation tokenizer, lowercased."""
    return re.findall(r'[a-z0-9_]+', text.lower())


def _detect_testcase_leakage(
    prompt_text: str,
    testcase_results: list[TestcaseResult],
) -> tuple[bool, float]:
    """
    Detect if the user's prompt contains a significant portion of any
    testcase expected output.  This catches the cheat where a user copies
    the visible sample outputs into their prompt.

    Uses both unigram overlap AND bigram (consecutive token pair) overlap
    to reduce false positives from common field names like "name", "age".

    Returns:
        (leakage_detected: bool, max_overlap_ratio: float)
    """
    if not prompt_text:
        return False, 0.0

    prompt_token_list = _tokenize(prompt_text)
    prompt_tokens = set(prompt_token_list)
    # Build bigrams for stricter matching
    prompt_bigrams = set(
        zip(prompt_token_list, prompt_token_list[1:])
    ) if len(prompt_token_list) >= 2 else set()

    if not prompt_tokens:
        return False, 0.0

    max_ratio = 0.0
    for tc in testcase_results:
        expected_list = _tokenize(tc.expected_output)
        expected_tokens = set(expected_list)
        if len(expected_tokens) < MIN_EXPECTED_TOKENS:
            continue

        # Unigram overlap
        overlap = prompt_tokens & expected_tokens
        if len(overlap) < MIN_OVERLAP_TOKENS:
            continue
        unigram_ratio = len(overlap) / len(expected_tokens)

        # Bigram overlap (consecutive pairs from expected output)
        expected_bigrams = set(
            zip(expected_list, expected_list[1:])
        ) if len(expected_list) >= 2 else set()

        if expected_bigrams:
            bigram_overlap = prompt_bigrams & expected_bigrams
            bigram_ratio = len(bigram_overlap) / len(expected_bigrams)
        else:
            bigram_ratio = 0.0

        # Use the higher signal: either strong unigram OR bigram match
        ratio = max(unigram_ratio, bigram_ratio)
        max_ratio = max(max_ratio, ratio)

    leakage = max_ratio >= LEAKAGE_THRESHOLD
    if leakage:
        logger.warning(
            "[Scoring] Test-case leakage detected — %.0f%% overlap",
            max_ratio * 100,
        )
    return leakage, round(max_ratio, 4)


# ── Main Scoring Function ───────────────────────────────────────────────────

def score_submission(
    testcase_results: list[TestcaseResult],
    prompt_text: Optional[str] = None,
) -> ScoringResult:
    """
    Compute the full 6-metric scoring breakdown for a submission.

    Args:
        testcase_results: List of TestcaseResult, each containing N RunResults.
        prompt_text: The user's submitted prompt (for leakage detection).

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
    if all_tokens and sum(all_tokens) == 0:
        # All runs errored (tokens_used=0) → worst efficiency, no credit
        t_norm = 1.0
    elif all_tokens and max(all_tokens) > min(all_tokens):
        avg_tokens = sum(all_tokens) / len(all_tokens)
        t_norm = (avg_tokens - min(all_tokens)) / (max(all_tokens) - min(all_tokens))
    else:
        t_norm = 0.0  # All equal non-zero → best score

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
        else 0.0  # No adversarial cases → no robustness credit
    )

    # ── Zero-out logic for completely unrelated prompts ──────
    if accuracy == 0.0 and format_compliance == 0.0:
        consistency = 0.0
        t_norm = 1.0
        l_norm = 1.0
        robustness = 0.0

    # ── Test-case leakage detection ───────────────────────────
    leakage_detected = False
    leakage_overlap = 0.0
    if prompt_text:
        leakage_detected, leakage_overlap = _detect_testcase_leakage(
            prompt_text, testcase_results,
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

    # ── Apply leakage penalty ────────────────────────────────
    if leakage_detected:
        final = 0.0

    return ScoringResult(
        accuracy=accuracy,
        consistency=consistency,
        format_compliance=format_compliance,
        token_efficiency=1.0 - t_norm,
        latency=1.0 - l_norm,
        robustness=robustness,
        final_score=round(final, 2),
        leakage_detected=leakage_detected,
        leakage_overlap=leakage_overlap,
    )
