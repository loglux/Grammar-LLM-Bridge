"""
Rate limiting for Grammar-LLM-Bridge.
"""
import time
import logging
from collections import defaultdict

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
        self.minute_windows: dict[int, list] = defaultdict(list)
        self.hour_windows: dict[int, list] = defaultdict(list)

    def _get_request_count(self, windows: dict, user_id: int, window_seconds: int) -> int:
        """Get total request count within window."""
        current_time = time.time()
        return sum(
            count for ts, count in windows.get(user_id, [])
            if current_time - ts < window_seconds
        )

    def get_limits(self, user_id: int) -> tuple[int, int, int, int]:
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
