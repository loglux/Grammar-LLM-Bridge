"""
Rate limiting for Grammar-LLM-Bridge.
"""
import time
import logging
from typing import Dict, Tuple
from collections import defaultdict
from fastapi import HTTPException, status

logger = logging.getLogger("customlt")


class RateLimiter:
    """
    Simple in-memory rate limiter using sliding window.

    For production, consider using Redis-based rate limiting.
    """

    def __init__(self, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour

        # Store: {user_id: [(timestamp, count), ...]}
        self.minute_windows: Dict[int, list] = defaultdict(list)
        self.hour_windows: Dict[int, list] = defaultdict(list)

    def _cleanup_old_entries(self, windows: dict, window_seconds: int):
        """Remove entries older than window_seconds."""
        current_time = time.time()
        for user_id in list(windows.keys()):
            windows[user_id] = [
                (ts, count) for ts, count in windows[user_id]
                if current_time - ts < window_seconds
            ]
            if not windows[user_id]:
                del windows[user_id]

    def _get_request_count(self, windows: dict, user_id: int, window_seconds: int) -> int:
        """Get total request count within window."""
        current_time = time.time()
        return sum(
            count for ts, count in windows.get(user_id, [])
            if current_time - ts < window_seconds
        )

    def check_rate_limit(self, user_id: int):
        """
        Check if user has exceeded rate limits.
        Raises HTTPException if limit exceeded.
        """
        current_time = time.time()

        # Cleanup old entries periodically
        self._cleanup_old_entries(self.minute_windows, 60)
        self._cleanup_old_entries(self.hour_windows, 3600)

        # Check minute limit
        minute_count = self._get_request_count(self.minute_windows, user_id, 60)
        if minute_count >= self.requests_per_minute:
            logger.warning("Rate limit exceeded for user %d: %d requests/minute",
                          user_id, minute_count)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {self.requests_per_minute} requests per minute"
            )

        # Check hour limit
        hour_count = self._get_request_count(self.hour_windows, user_id, 3600)
        if hour_count >= self.requests_per_hour:
            logger.warning("Rate limit exceeded for user %d: %d requests/hour",
                          user_id, hour_count)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {self.requests_per_hour} requests per hour"
            )

        # Record this request
        self.minute_windows[user_id].append((current_time, 1))
        self.hour_windows[user_id].append((current_time, 1))

    def get_limits(self, user_id: int) -> Tuple[int, int, int, int]:
        """
        Get current usage and limits for a user.
        Returns: (minute_used, minute_limit, hour_used, hour_limit)
        """
        minute_used = self._get_request_count(self.minute_windows, user_id, 60)
        hour_used = self._get_request_count(self.hour_windows, user_id, 3600)

        return (
            minute_used,
            self.requests_per_minute,
            hour_used,
            self.requests_per_hour
        )


# Global rate limiter instance
rate_limiter = RateLimiter()
