"""
Rate limiting utilities for WhatsApp AI Chatbot.

Provides per-user rate limiting using Redis to prevent abuse and
ensure fair resource usage across all users.
"""

import logging
import time
from typing import Optional

import redis

from .config import Config

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""

    def __init__(self, retry_after: int):
        """
        Initialize exception.

        Args:
            retry_after: Seconds until rate limit resets
        """
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Try again in {retry_after} seconds.")


class RateLimiter:
    """
    Redis-based rate limiter for per-user message throttling.

    Uses token bucket algorithm to allow bursts while maintaining
    average rate limit. Tracks usage per user (phone number) with
    automatic expiration.
    """

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        max_requests: Optional[int] = None,
        window_seconds: Optional[int] = None,
    ):
        """
        Initialize rate limiter.

        Args:
            redis_client: Redis client instance (creates default if None)
            max_requests: Maximum requests per window (defaults to config)
            window_seconds: Time window in seconds (defaults to config)
        """
        self.redis = redis_client or redis.Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            db=Config.REDIS_DB,
            decode_responses=True,
        )
        self.max_requests = max_requests or Config.RATE_LIMIT_MAX_REQUESTS
        self.window_seconds = window_seconds or Config.RATE_LIMIT_WINDOW_SECONDS

    def _get_key(self, user_id: str) -> str:
        """
        Generate Redis key for user rate limit.

        Args:
            user_id: User identifier (phone number)

        Returns:
            Redis key string
        """
        return f"rate_limit:{user_id}"

    def check_rate_limit(self, user_id: str) -> bool:
        """
        Check if user has exceeded rate limit.

        Uses sliding window counter to track requests within the time window.
        Does not increment the counter - use allow_request() for that.

        Args:
            user_id: User identifier (phone number)

        Returns:
            True if user is within rate limit, False if exceeded
        """
        try:
            key = self._get_key(user_id)
            current_count = self.redis.get(key)

            if current_count is None:
                return True  # No previous requests

            return int(current_count) < self.max_requests

        except redis.RedisError as e:
            logger.error(f"Redis error checking rate limit for {user_id}: {e}")
            # Fail open - allow request if Redis is down
            return True
        except Exception as e:
            logger.error(f"Unexpected error checking rate limit for {user_id}: {e}")
            return True

    def allow_request(self, user_id: str) -> bool:
        """
        Check and increment rate limit counter for a user.

        Uses atomic increment to prevent race conditions in distributed
        systems. If rate limit is exceeded, raises RateLimitExceeded.

        Args:
            user_id: User identifier (phone number)

        Returns:
            True if request is allowed

        Raises:
            RateLimitExceeded: If user has exceeded rate limit
        """
        try:
            key = self._get_key(user_id)

            # Use pipeline for atomic operations
            pipe = self.redis.pipeline()
            pipe.incr(key)
            pipe.ttl(key)
            results = pipe.execute()

            count = results[0]
            ttl = results[1]

            # Set expiration on first request
            if ttl == -1:  # Key exists but no expiration
                self.redis.expire(key, self.window_seconds)

            # Check if limit exceeded
            if count > self.max_requests:
                # Calculate retry_after based on remaining TTL
                retry_after = ttl if ttl > 0 else self.window_seconds
                logger.warning(
                    f"Rate limit exceeded for {user_id}: "
                    f"{count}/{self.max_requests} requests"
                )
                raise RateLimitExceeded(retry_after)

            logger.debug(
                f"Rate limit check passed for {user_id}: "
                f"{count}/{self.max_requests} requests"
            )
            return True

        except RateLimitExceeded:
            raise
        except redis.RedisError as e:
            logger.error(f"Redis error for rate limiting {user_id}: {e}")
            # Fail open - allow request if Redis is down
            return True
        except Exception as e:
            logger.error(f"Unexpected error in rate limiting {user_id}: {e}")
            return True

    def get_remaining_requests(self, user_id: str) -> int:
        """
        Get number of remaining requests for a user.

        Args:
            user_id: User identifier (phone number)

        Returns:
            Number of remaining requests (0 if limit exceeded)
        """
        try:
            key = self._get_key(user_id)
            current_count = self.redis.get(key)

            if current_count is None:
                return self.max_requests

            remaining = self.max_requests - int(current_count)
            return max(0, remaining)

        except redis.RedisError as e:
            logger.error(f"Redis error getting remaining requests for {user_id}: {e}")
            return self.max_requests  # Return max if Redis error
        except Exception as e:
            logger.error(
                f"Unexpected error getting remaining requests for {user_id}: {e}"
            )
            return self.max_requests

    def get_reset_time(self, user_id: str) -> Optional[int]:
        """
        Get time when rate limit resets for a user.

        Args:
            user_id: User identifier (phone number)

        Returns:
            Unix timestamp when limit resets, None if no limit active
        """
        try:
            key = self._get_key(user_id)
            ttl = self.redis.ttl(key)

            if ttl <= 0:
                return None

            return int(time.time()) + ttl

        except redis.RedisError as e:
            logger.error(f"Redis error getting reset time for {user_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting reset time for {user_id}: {e}")
            return None

    def reset_limit(self, user_id: str) -> bool:
        """
        Reset rate limit for a user (admin operation).

        Args:
            user_id: User identifier (phone number)

        Returns:
            True if limit was reset
        """
        try:
            key = self._get_key(user_id)
            self.redis.delete(key)
            logger.info(f"Rate limit reset for user {user_id}")
            return True

        except redis.RedisError as e:
            logger.error(f"Redis error resetting limit for {user_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error resetting limit for {user_id}: {e}")
            return False
