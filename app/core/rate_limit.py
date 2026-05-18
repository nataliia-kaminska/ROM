from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock
from typing import Callable

from fastapi import HTTPException, Request, status

from app.core.config import settings


_lock = Lock()
_buckets: dict[str, deque[float]] = defaultdict(deque)


def rate_limit(bucket: str) -> Callable[[Request], None]:
    def dependency(request: Request) -> None:
        if not settings.auth_rate_limit_enabled:
            return
        client = request.client.host if request.client else "unknown"
        key = f"{bucket}:{client}"
        now = time.monotonic()
        window_start = now - settings.auth_rate_limit_window_seconds
        with _lock:
            attempts = _buckets[key]
            while attempts and attempts[0] < window_start:
                attempts.popleft()
            if len(attempts) >= settings.auth_rate_limit_max_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many attempts. Please try again later.",
                )
            attempts.append(now)

    return dependency


def reset_rate_limits() -> None:
    with _lock:
        _buckets.clear()
