"""
PromptRank -- Scoring Engine Unit Tests
Verifies the exact scoring math for all 6 metrics.
"""

import json
import sys
import pytest
sys.path.insert(0, ".")

from app.scoring.engine import (
    score_submission,
    TestcaseResult,
    RunResult,
    _compute_accuracy,
    _check_format_compliance,
    _compute_consistency,
    _detect_testcase_leakage,
)


@pytest.mark.scoring
def test_perfect_score():
    """All runs produce perfect output -> score should be ~100."""
    expected = json.dumps({"name": "Alice", "age": 30, "city": "NYC"})
    tc = TestcaseResult(
        expected_output=expected,
        runs=[
            RunResult(output=expected, tokens_used=100, latency_ms=200),
            RunResult(output=expected, tokens_used=100, latency_ms=200),
            RunResult(output=expected, tokens_used=100, latency_ms=200),
        ],
    )
    result = score_submission([tc])
    print(f"[PASS] Perfect score test: {result.final_score} (expected ~100)")
    # Note: robustness=0.0 when there are no adversarial testcases,
    # so max achievable score without adversarial cases is 90.0.
    assert result.final_score >= 89, f"Expected >=89, got {result.final_score}"
    assert result.accuracy == 1.0
    assert result.format_compliance == 1.0
    assert result.consistency == 1.0


@pytest.mark.scoring
def test_zero_score():
    """All runs produce garbage -> score should be low."""
    expected = json.dumps({"name": "Alice", "age": 30})
    tc = TestcaseResult(
        expected_output=expected,
        runs=[
            RunResult(output="not json at all", tokens_used=500, latency_ms=5000),
            RunResult(output="also not json", tokens_used=600, latency_ms=6000),
            RunResult(output="garbage output", tokens_used=700, latency_ms=7000),
        ],
    )
    result = score_submission([tc])
    print(f"[PASS] Zero score test: {result.final_score} (expected low)")
    assert result.final_score < 30, f"Expected <30, got {result.final_score}"
    assert result.accuracy == 0.0
    assert result.format_compliance == 0.0


@pytest.mark.scoring
def test_partial_accuracy():
    """Some fields correct, some wrong -> partial accuracy."""
    expected = json.dumps({"name": "Alice", "age": 30, "city": "NYC"})
    partial = json.dumps({"name": "Alice", "age": 99, "city": "LA"})
    tc = TestcaseResult(
        expected_output=expected,
        runs=[
            RunResult(output=partial, tokens_used=100, latency_ms=200),
        ],
    )
    result = score_submission([tc])
    print(f"[PASS] Partial accuracy test: accuracy={result.accuracy:.3f}, score={result.final_score}")
    assert 0 < result.accuracy < 1.0, f"Expected partial accuracy, got {result.accuracy}"


@pytest.mark.scoring
def test_adversarial_robustness():
    """Adversarial testcases affect robustness score separately."""
    expected = json.dumps({"result": "ok"})
    normal_tc = TestcaseResult(
        expected_output=expected,
        is_adversarial=False,
        runs=[RunResult(output=expected, tokens_used=100, latency_ms=200)],
    )
    adversarial_tc = TestcaseResult(
        expected_output=expected,
        is_adversarial=True,
        runs=[RunResult(output=json.dumps({"result": "fail"}), tokens_used=100, latency_ms=200)],
    )
    result = score_submission([normal_tc, adversarial_tc])
    print(f"[PASS] Robustness test: accuracy={result.accuracy:.3f}, robustness={result.robustness:.3f}")
    assert result.accuracy > result.robustness, "Robustness should be lower when adversarial fails"


@pytest.mark.scoring
def test_consistency_identical():
    """Identical outputs -> consistency = 1.0."""
    output = json.dumps({"x": 1})
    score = _compute_consistency([output, output, output])
    print(f"[PASS] Consistency identical: {score}")
    assert score == 1.0


@pytest.mark.scoring
def test_consistency_divergent():
    """Very different outputs -> low consistency."""
    outputs = [
        "completely different output one",
        "another totally unrelated response",
        "third unique unmatched text here",
    ]
    score = _compute_consistency(outputs)
    print(f"[PASS] Consistency divergent: {score:.3f}")
    assert score < 0.5


@pytest.mark.scoring
def test_llm_error_handling():
    """LLM errors should result in 0 accuracy and 0 format."""
    expected = json.dumps({"name": "Test"})
    tc = TestcaseResult(
        expected_output=expected,
        runs=[
            RunResult(output="__LLM_ERROR__: timeout", tokens_used=0, latency_ms=5000),
        ],
    )
    result = score_submission([tc])
    print(f"[PASS] LLM error handling: accuracy={result.accuracy}, format={result.format_compliance}")
    assert result.accuracy == 0.0
    assert result.format_compliance == 0.0


@pytest.mark.scoring
def test_empty_testcases():
    """No testcases -> default zero scoring result."""
    result = score_submission([])
    assert result.final_score == 0.0
    assert result.accuracy == 0.0


@pytest.mark.scoring
def test_score_clamped_to_100():
    """Final score should never exceed 100."""
    expected = json.dumps({"x": 1})
    tc = TestcaseResult(
        expected_output=expected,
        runs=[RunResult(output=expected, tokens_used=1, latency_ms=1)],
    )
    result = score_submission([tc])
    assert result.final_score <= 100.0


@pytest.mark.scoring
def test_all_llm_errors_score_near_zero():
    """
    Regression test: when ALL runs return LLM errors (e.g. Ollama 404),
    the final score must be near 0, NOT ~34.6.

    Previously broken because:
      - consistency returned 1.0 for all-empty outputs
      - token_efficiency returned 1.0 when all tokens == 0
    """
    tc = TestcaseResult(
        expected_output='{"result": "ok"}',
        runs=[
            RunResult(output="__LLM_ERROR__: 404 Not Found", tokens_used=0, latency_ms=3000)
            for _ in range(5)
        ],
    )
    result = score_submission([tc])
    print(f"[REGRESSION] All-error score: {result.final_score} (expected <5)")
    print(f"  consistency={result.consistency}, token_efficiency={result.token_efficiency}")
    # Core assertions
    assert result.consistency == 0.0, f"Consistency should be 0.0, got {result.consistency}"
    assert result.token_efficiency == 0.0, f"Token efficiency should be 0.0, got {result.token_efficiency}"
    assert result.accuracy == 0.0
    assert result.format_compliance == 0.0
    # All errors → only latency metric can score (5 pts when all latencies equal → no spread → 1.0)
    # So expected score is exactly 5.0 (latency only, all other metrics = 0)
    assert result.final_score <= 5.0, f"Expected <=5.0, got {result.final_score} (was 34.6 before fix)"


@pytest.mark.scoring
def test_completely_unrelated_prompt():
    """
    If a prompt returns completely unrelated text (0 accuracy, 0 format),
    the final score should be exactly 0, rather than getting free points
    from consistency, tokens, and latency.
    """
    tc = TestcaseResult(
        expected_output='{"answer": 42}',
        runs=[
            RunResult(output="vtgctctvy vtc6y6 yvy6vht", tokens_used=6, latency_ms=100),
            RunResult(output="vtgctctvy vtc6y6 yvy6vht", tokens_used=6, latency_ms=105),
            RunResult(output="vtgctctvy vtc6y6 yvy6vht", tokens_used=6, latency_ms=110),
        ],
    )
    result = score_submission([tc])
    print(f"[PASS] Unrelated prompt score: {result.final_score} (expected 0.0)")
    assert result.accuracy == 0.0
    assert result.format_compliance == 0.0
    assert result.consistency == 0.0
    assert result.token_efficiency == 0.0
    assert result.latency == 0.0
    assert result.robustness == 0.0
    assert result.final_score == 0.0


@pytest.mark.scoring
def test_testcase_leakage_detected():
    """
    If the user copies expected output into their prompt,
    leakage should be detected and score set to 0.
    """
    expected = "1. Cost of notebooks: 4 × $3.50\n2. Total cost: $14.00\n3. Change: $20.00 - $14.00 = $6.00\n\nAnswer: 6.00"
    # User copies the expected output into their prompt
    cheating_prompt = (
        "Solve math problems. Follow this exact format:\n"
        "1. Cost of notebooks: 4 × $3.50\n"
        "2. Total cost: $14.00\n"
        "3. Change: $20.00 - $14.00 = $6.00\n"
        "Answer: 6.00"
    )

    tc = TestcaseResult(
        expected_output=expected,
        runs=[
            RunResult(output=expected, tokens_used=100, latency_ms=200),
            RunResult(output=expected, tokens_used=100, latency_ms=200),
        ],
    )
    result = score_submission([tc], prompt_text=cheating_prompt)
    print(f"[PASS] Leakage test: score={result.final_score}, leakage={result.leakage_detected}, overlap={result.leakage_overlap}")
    assert result.leakage_detected is True
    assert result.leakage_overlap >= 0.6
    assert result.final_score == 0.0


@pytest.mark.scoring
def test_no_leakage_for_normal_prompt():
    """
    A well-crafted prompt with no copied expected output
    should NOT trigger leakage detection.
    """
    expected = json.dumps({"name": "Alice", "age": 30, "city": "NYC"})
    normal_prompt = "Extract the person's name, age, and city from the given text and return as JSON."

    tc = TestcaseResult(
        expected_output=expected,
        runs=[
            RunResult(output=expected, tokens_used=100, latency_ms=200),
        ],
    )
    result = score_submission([tc], prompt_text=normal_prompt)
    print(f"[PASS] No leakage test: score={result.final_score}, leakage={result.leakage_detected}")
    assert result.leakage_detected is False
    assert result.final_score > 0


@pytest.mark.scoring
def test_leakage_detection_direct():
    """Direct test of the leakage detection function."""
    expected_output = "1. Cost of notebooks: 4 × $3.50\n2. Total cost: $14.00\n3. Change: $20.00 - $14.00 = $6.00\n\nAnswer: 6.00"
    prompt_with_leakage = (
        "Solve math problems step by step. Follow this format:\n"
        "1. Cost of notebooks: 4 × $3.50\n2. Total cost: $14.00\n"
        "3. Change: $20.00 - $14.00 = $6.00\nAnswer: 6.00"
    )
    tc = TestcaseResult(expected_output=expected_output)
    detected, overlap = _detect_testcase_leakage(prompt_with_leakage, [tc])
    print(f"[PASS] Direct leakage: detected={detected}, overlap={overlap}")
    assert detected is True
    assert overlap >= 0.5
