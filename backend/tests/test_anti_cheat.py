"""
PromptRank -- Anti-Cheat Module Unit Tests

Tests the IP rate limiter and duplicate prompt detection logic
without requiring a running Redis instance (mocked).
"""

import sys
import hashlib
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, ".")


# ── Test: Duplicate Prompt Hash Consistency ──────────────────────────────────

@pytest.mark.anticheat
class TestDuplicatePromptDetection:

    def test_hash_consistency(self):
        """Same input should always produce the same hash."""
        user = "user-1"
        problem = "problem-1"
        prompt = "  Extract the JSON data  "
        normalized = prompt.strip().lower()
        h1 = hashlib.sha256(f"{user}:{problem}:{normalized}".encode()).hexdigest()
        h2 = hashlib.sha256(f"{user}:{problem}:{normalized}".encode()).hexdigest()
        assert h1 == h2

    def test_different_prompts_different_hash(self):
        """Different prompts should produce different hashes."""
        user = "user-1"
        problem = "problem-1"
        h1 = hashlib.sha256(f"{user}:{problem}:prompt a".encode()).hexdigest()
        h2 = hashlib.sha256(f"{user}:{problem}:prompt b".encode()).hexdigest()
        assert h1 != h2

    def test_different_users_different_hash(self):
        """Same prompt from different users should produce different hashes."""
        prompt = "same prompt"
        h1 = hashlib.sha256(f"user-1:prob:{ prompt}".encode()).hexdigest()
        h2 = hashlib.sha256(f"user-2:prob:{prompt}".encode()).hexdigest()
        assert h1 != h2

    def test_whitespace_normalization(self):
        """Prompts differing only by whitespace should hash the same."""
        user = "u1"
        problem = "p1"
        p1 = "  Hello World  "
        p2 = "Hello World"
        n1 = p1.strip().lower()
        n2 = p2.strip().lower()
        h1 = hashlib.sha256(f"{user}:{problem}:{n1}".encode()).hexdigest()
        h2 = hashlib.sha256(f"{user}:{problem}:{n2}".encode()).hexdigest()
        assert h1 == h2

    def test_case_normalization(self):
        """Prompts differing only by case should hash the same."""
        user = "u1"
        problem = "p1"
        p1 = "EXTRACT JSON"
        p2 = "extract json"
        n1 = p1.strip().lower()
        n2 = p2.strip().lower()
        h1 = hashlib.sha256(f"{user}:{problem}:{n1}".encode()).hexdigest()
        h2 = hashlib.sha256(f"{user}:{problem}:{n2}".encode()).hexdigest()
        assert h1 == h2


# ── Test: IP Rate Limit Logic ────────────────────────────────────────────────

@pytest.mark.anticheat
class TestIPRateLimitLogic:

    def test_rate_limit_constants(self):
        """Verify the rate limit configuration."""
        try:
            from app.middleware.anti_cheat import IP_WINDOW_SECONDS, IP_MAX_SUBMISSIONS
        except ImportError:
            pytest.skip("redis not installed")
        assert IP_WINDOW_SECONDS == 300  # 5 minutes
        assert IP_MAX_SUBMISSIONS == 10

    def test_key_format(self):
        """IP key should follow the expected pattern."""
        try:
            from app.middleware.anti_cheat import IP_KEY_PREFIX
        except ImportError:
            pytest.skip("redis not installed")
        ip = "192.168.1.100"
        key = f"{IP_KEY_PREFIX}{ip}"
        assert key == "anticheat:ip:192.168.1.100"

    def test_dupe_key_format(self):
        """Duplicate prompt key should use SHA-256 hash."""
        try:
            from app.middleware.anti_cheat import DUPE_KEY_PREFIX
        except ImportError:
            pytest.skip("redis not installed")
        fake_hash = hashlib.sha256(b"test").hexdigest()
        key = f"{DUPE_KEY_PREFIX}{fake_hash}"
        assert key.startswith("anticheat:dupe:")
        assert len(key) == len("anticheat:dupe:") + 64  # SHA-256 = 64 hex chars


# ── Test: Randomized Testcase Ordering ───────────────────────────────────────

@pytest.mark.anticheat
class TestRandomizedTestcaseOrdering:

    def test_deterministic_shuffling(self):
        """Same seed should always produce the same shuffle."""
        import random
        items = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        rng1 = random.Random("submission-uuid-123")
        list1 = items.copy()
        rng1.shuffle(list1)

        rng2 = random.Random("submission-uuid-123")
        list2 = items.copy()
        rng2.shuffle(list2)

        assert list1 == list2, "Same seed must produce identical ordering"

    def test_different_seeds_different_order(self):
        """Different submission IDs should produce different orderings."""
        import random
        items = list(range(20))  # Use more items to reduce collision chance

        rng1 = random.Random("submission-A")
        list1 = items.copy()
        rng1.shuffle(list1)

        rng2 = random.Random("submission-B")
        list2 = items.copy()
        rng2.shuffle(list2)

        assert list1 != list2, "Different seeds should produce different orderings"
