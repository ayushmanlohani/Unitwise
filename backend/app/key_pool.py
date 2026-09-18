"""
key_pool.py — Groq API Key Pool Manager.

Manages multiple Groq API keys with automatic rotation,
usage tracking, and intelligent key selection.

To add a new key:
    1. Add GROQ_API_KEY_6=gsk_xxx to .env
    2. Add "GROQ_API_KEY_6" to KEY_ENV_NAMES list below
    That's it. Nothing else needs to change.
"""

import time
import logging
import asyncio
from dataclasses import dataclass, field
from typing import Optional
from app.config.settings import get_groq_keys

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration — adjust these if Groq changes their limits
# ---------------------------------------------------------------------------
MAX_REQUESTS_PER_MINUTE = 25      # Per key (Groq allows 30, we use 25 for safety)
MAX_TOKENS_PER_MINUTE = 5000      # Per key (Groq allows 6000, we use 5000 for safety)
RESET_INTERVAL_SECONDS = 60       # How often counters reset
AVG_TOKENS_PER_REQUEST = 1500     # Conservative estimate per answer


# ---------------------------------------------------------------------------
# Key State Tracker
# ---------------------------------------------------------------------------
@dataclass
class KeyState:
    key: str
    index: int                          # For logging only (Key #1, #2, etc.)
    requests_this_minute: int = 0
    tokens_this_minute: int = 0
    last_reset: float = field(default_factory=time.time)
    consecutive_errors: int = 0

    def reset_if_due(self):
        """Reset counters if a minute has passed."""
        now = time.time()
        if now - self.last_reset >= RESET_INTERVAL_SECONDS:
            self.requests_this_minute = 0
            self.tokens_this_minute = 0
            self.last_reset = now
            logger.info("[KeyPool] Key #%d counters reset.", self.index)

    @property
    def is_available(self) -> bool:
        self.reset_if_due()
        req_ok = self.requests_this_minute < MAX_REQUESTS_PER_MINUTE
        tok_ok = self.tokens_this_minute < MAX_TOKENS_PER_MINUTE
        return req_ok and tok_ok

    @property
    def seconds_until_reset(self) -> float:
        elapsed = time.time() - self.last_reset
        return max(0.0, RESET_INTERVAL_SECONDS - elapsed)

    def record_request(self, estimated_tokens: int = AVG_TOKENS_PER_REQUEST):
        self.requests_this_minute += 1
        self.tokens_this_minute += estimated_tokens
        logger.info(
            "[KeyPool] Key #%d used | req=%d/%d | tokens=%d/%d",
            self.index,
            self.requests_this_minute, MAX_REQUESTS_PER_MINUTE,
            self.tokens_this_minute, MAX_TOKENS_PER_MINUTE,
        )

    def record_error(self):
        self.consecutive_errors += 1
        logger.warning(
            "[KeyPool] Key #%d error #%d",
            self.index, self.consecutive_errors
        )

    def record_success(self):
        self.consecutive_errors = 0


# ---------------------------------------------------------------------------
# Key Pool Manager
# ---------------------------------------------------------------------------
class KeyPoolManager:
    """
    Manages a pool of Groq API keys.
    Thread-safe via asyncio lock.
    Selects the key with the most remaining capacity.
    """

    def __init__(self, keys: list[str]):
        if not keys:
            raise ValueError("No Groq API keys provided.")

        self._pool: list[KeyState] = [
            KeyState(key=k, index=i + 1)
            for i, k in enumerate(keys)
        ]
        self._lock = asyncio.Lock()
        logger.info("[KeyPool] Initialised with %d key(s).", len(self._pool))

    @property
    def total_keys(self) -> int:
        return len(self._pool)

    def get_best_key(self) -> Optional[KeyState]:
        """
        Return the available key with the most remaining request capacity.
        Returns None if all keys are exhausted.
        """
        available = [k for k in self._pool if k.is_available]
        if not available:
            return None
        # Pick key with most remaining requests
        return min(available, key=lambda k: k.requests_this_minute)

    def seconds_until_any_key_free(self) -> float:
        """
        Return the shortest wait time until any key resets.
        Used for the 'please wait X seconds' message.
        """
        return min(k.seconds_until_reset for k in self._pool)

    async def acquire(self) -> Optional[KeyState]:
        """
        Thread-safe key acquisition.
        Returns the best available key or None if all exhausted.
        """
        async with self._lock:
            key_state = self.get_best_key()
            if key_state:
                key_state.record_request()
            return key_state

    def status(self) -> list[dict]:
        """Return status of all keys for debugging."""
        return [
            {
                "key_index": k.index,
                "available": k.is_available,
                "requests_this_minute": k.requests_this_minute,
                "tokens_this_minute": k.tokens_this_minute,
                "seconds_until_reset": round(k.seconds_until_reset),
            }
            for k in self._pool
        ]


# ---------------------------------------------------------------------------
# Singleton instance — initialised once at startup
# ---------------------------------------------------------------------------
_pool_manager: Optional[KeyPoolManager] = None


def get_pool_manager() -> KeyPoolManager:
    """Return the singleton KeyPoolManager. Initialise on first call."""
    global _pool_manager
    if _pool_manager is None:
        keys = get_groq_keys()
        _pool_manager = KeyPoolManager(keys)
    return _pool_manager