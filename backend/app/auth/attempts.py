"""In-memory login attempt tracker (Q2=A, Q3=A, Q4=A).

Admin logins only (BR-U1-6a). Keyed by ``(store_id, username)``. After
``max_login_attempts`` failures the key is locked for ``lockout_minutes``;
the lock auto-releases once the window passes (time-based, lazy). Process
memory only — reset on restart (local/workshop acceptable, BR-U1-6).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.common.config import settings


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class _AttemptState:
    failed_count: int = 0
    locked_until: datetime | None = None


class LoginAttemptTracker:
    def __init__(
        self,
        max_attempts: int | None = None,
        lockout_minutes: int | None = None,
    ):
        self._max = max_attempts if max_attempts is not None else settings.max_login_attempts
        self._lockout = (
            lockout_minutes if lockout_minutes is not None else settings.lockout_minutes
        )
        self._store: dict[tuple[int, str], _AttemptState] = {}

    def _get(self, key: tuple[int, str]) -> _AttemptState:
        state = self._store.get(key)
        if state is None:
            state = _AttemptState()
            self._store[key] = state
        return state

    def is_locked(self, store_id: int, username: str) -> bool:
        """True if currently locked. Auto-releases an expired lock (BR-U1-6)."""
        key = (store_id, username)
        state = self._store.get(key)
        if state is None or state.locked_until is None:
            return False
        if _now() >= state.locked_until:
            # Time-based auto-unlock: reset state and allow retry.
            self._store.pop(key, None)
            return False
        return True

    def record_failure(self, store_id: int, username: str) -> None:
        """Increment failure count; lock once the threshold is reached (BR-U1-3)."""
        key = (store_id, username)
        state = self._get(key)
        state.failed_count += 1
        if state.failed_count >= self._max:
            state.locked_until = _now() + timedelta(minutes=self._lockout)

    def reset(self, store_id: int, username: str) -> None:
        """Clear counter/lock on success (BR-U1-5)."""
        self._store.pop((store_id, username), None)


# Process-wide shared tracker (in-memory state persists across requests).
tracker = LoginAttemptTracker()
