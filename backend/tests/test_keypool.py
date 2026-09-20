"""
test_keypool.py — Pool picks by tokens, 429 burns the key.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.key_pool import (
    AVG_TOKENS_PER_REQUEST,
    MAX_TOKENS_PER_MINUTE,
    KeyPoolManager,
)


def test_estimate_matches_measured_cost():
    assert AVG_TOKENS_PER_REQUEST == 3000


def test_cap_is_80_percent_of_8k_tier():
    assert MAX_TOKENS_PER_MINUTE == 6400


def test_picks_key_with_most_tokens_left():
    pool = KeyPoolManager(["k1", "k2"])
    pool._pool[0].tokens_this_minute = 6000
    pool._pool[1].tokens_this_minute = 1000
    assert pool.get_best_key().index == 2


def test_exhausted_key_skipped():
    pool = KeyPoolManager(["k1", "k2"])
    pool._pool[0].mark_exhausted()
    best = pool.get_best_key()
    assert best is not None and best.index == 2


def test_all_exhausted_returns_none():
    pool = KeyPoolManager(["k1"])
    pool._pool[0].mark_exhausted()
    assert pool.get_best_key() is None
