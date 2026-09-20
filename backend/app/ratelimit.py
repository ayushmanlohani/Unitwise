"""
ratelimit.py — Adaptive per-user rate limiter, in-memory.

Two modes from one counter:
    Solo (1 active user in the last 60s): 10 queries/min ≈ 35k tokens.
    Shared (2+ active users): 3 queries/min each, fair share.

User ids are self-told by the frontend (Supabase id). No token checks —
goal is fair share, not security. Missing id shares the "anon" bucket.
"""

import time
from collections import deque

WINDOW_SECONDS = 60
SOLO_PER_MINUTE = 10      # ~10 x 3500 tokens ≈ 35k, inside the 40k system budget
SHARED_PER_MINUTE = 3     # fair share when 2+ users are active
SHARED_THRESHOLD = 2      # active users needed to switch to shared mode


class UserLimiter:
    def __init__(
        self,
        window: int = WINDOW_SECONDS,
        solo_cap: int = SOLO_PER_MINUTE,
        shared_cap: int = SHARED_PER_MINUTE,
    ):
        self.window = window
        self.solo_cap = solo_cap
        self.shared_cap = shared_cap
        self._hits: dict[str, deque] = {}

    def _prune(self, user_id: str, now: float) -> deque:
        hits = self._hits.get(user_id)
        if hits is None:
            hits = self._hits[user_id] = deque()
        while hits and now - hits[0] >= self.window:
            hits.popleft()
        return hits

    def active_users(self, now: float | None = None) -> int:
        """Distinct ids seen inside the window."""
        now = time.time() if now is None else now
        count = 0
        for user_id in list(self._hits):
            if self._prune(user_id, now):
                count += 1
        return count

    def check(self, user_id: str, now: float | None = None) -> dict:
        """
        Record nothing; return allowed + wait + mode.
        Caller records the hit only when the query is actually served...
        here we record on allow so the stream path stays single-call.
        """
        now = time.time() if now is None else now
        user_id = user_id or "anon"
        others = self.active_users(now)
        hits = self._prune(user_id, now)
        # Caller is active too: solo only when nobody else is in the window.
        active = others if hits else others + 1
        shared = active >= SHARED_THRESHOLD
        cap = self.shared_cap if shared else self.solo_cap
        if len(hits) >= cap:
            wait = int(self.window - (now - hits[0])) + 1
            return {
                "allowed": False,
                "wait_seconds": max(wait, 1),
                "mode": "shared" if shared else "solo",
                "active_users": active,
            }
        hits.append(now)
        return {
            "allowed": True,
            "wait_seconds": 0,
            "mode": "shared" if shared else "solo",
            "active_users": active,
        }


_limiter: UserLimiter | None = None


def get_limiter() -> UserLimiter:
    global _limiter
    if _limiter is None:
        _limiter = UserLimiter()
    return _limiter


def limit_message(wait_seconds: int, mode: str, active_users: int) -> str:
    """Exact user-facing text per mode."""
    if mode == "shared":
        return (
            "⚠️ **Usage is very high right now.** "
            f"You can only ask **{SHARED_PER_MINUTE} questions per minute**. "
            f"Please wait **{wait_seconds} seconds** and ask your question again."
        )
    return (
        "⚠️ **Usage is very high right now.** "
        f"Please wait **{wait_seconds} seconds** and ask your question again."
    )
