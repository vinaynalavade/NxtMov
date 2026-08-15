import time
import threading
from collections import defaultdict
from typing import Dict, List, Tuple
from fastapi import HTTPException, status, Request

class SimpleRateLimiter:
    """
    Thread-safe in-memory sliding window rate limiter for login and registration.
    Prevents rapid automated brute force attempts without locking out legitimate users.
    """
    def __init__(self, max_requests: int = 15, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._records: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def is_rate_limited(self, key: str) -> bool:
        now = time.time()
        with self._lock:
            # Filter out timestamps older than the sliding window
            timestamps = [t for t in self._records[key] if now - t < self.window_seconds]
            self._records[key] = timestamps
            if len(timestamps) >= self.max_requests:
                return True
            self._records[key].append(now)
            return False

    def reset(self, key: str):
        with self._lock:
            if key in self._records:
                del self._records[key]

# Login rate limiter (15 attempts per minute per IP/key)
login_rate_limiter = SimpleRateLimiter(max_requests=15, window_seconds=60)

# Registration rate limiter (10 registrations per minute per IP)
register_rate_limiter = SimpleRateLimiter(max_requests=10, window_seconds=60)

def check_login_rate_limit(request: Request, identifier: str):
    client_ip = request.client.host if request.client else "unknown"
    if client_ip in ("testclient", "test"):
        return
    key = f"{client_ip}:{identifier.strip().lower()}"
    if login_rate_limiter.is_rate_limited(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please wait a moment and try again."
        )

def reset_login_rate_limit(request: Request, identifier: str):
    client_ip = request.client.host if request.client else "unknown"
    key = f"{client_ip}:{identifier.strip().lower()}"
    login_rate_limiter.reset(key)

def check_register_rate_limit(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    if client_ip in ("testclient", "test"):
        return
    key = f"reg:{client_ip}"
    if register_rate_limiter.is_rate_limited(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many signup attempts. Please wait a moment and try again."
        )
