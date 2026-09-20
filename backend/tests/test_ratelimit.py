"""
test_ratelimit.py — Adaptive limiter: solo gets system budget, crowd shares.
"""

from app.ratelimit import UserLimiter, limit_message


def test_solo_allows_ten_per_minute():
    lim = UserLimiter()
    results = [lim.check("u1", now=1000 + i)["allowed"] for i in range(11)]
    assert results == [True] * 10 + [False]


def test_solo_block_says_solo_message():
    lim = UserLimiter()
    gate = None
    for i in range(11):
        gate = lim.check("u1", now=1000 + i)
    assert gate["mode"] == "solo"
    text = limit_message(gate["wait_seconds"], gate["mode"], gate["active_users"])
    assert "very high" in text
    assert str(gate["wait_seconds"]) in text


def test_two_users_switch_to_shared_cap():
    lim = UserLimiter()
    assert lim.check("u1", now=1000)["mode"] == "solo"
    assert lim.check("u2", now=1001)["mode"] == "shared"
    # u2 gets 3/min in shared mode: 1 used, 2 more allowed, 4th blocked.
    assert lim.check("u2", now=1002)["allowed"] is True
    assert lim.check("u2", now=1003)["allowed"] is True
    assert lim.check("u2", now=1004)["allowed"] is False


def test_shared_block_names_crowd():
    lim = UserLimiter()
    lim.check("u1", now=1000)
    lim.check("u2", now=1001)
    lim.check("u2", now=1002)
    lim.check("u2", now=1003)
    gate = lim.check("u2", now=1004)
    assert gate["allowed"] is False
    text = limit_message(gate["wait_seconds"], gate["mode"], gate["active_users"])
    assert "very high" in text
    assert "3 questions per minute" in text


def test_window_expiry_restores_solo():
    lim = UserLimiter(window=60, solo_cap=2, shared_cap=1)
    lim.check("u1", now=1000)
    lim.check("u1", now=1001)
    assert lim.check("u1", now=1002)["allowed"] is False
    gate = lim.check("u1", now=1070)
    assert gate["allowed"] is True
    assert gate["mode"] == "solo"


def test_missing_id_shares_anon_bucket():
    lim = UserLimiter()
    assert lim.check("", now=1000)["allowed"] is True
    assert lim.active_users(now=1000) == 1
