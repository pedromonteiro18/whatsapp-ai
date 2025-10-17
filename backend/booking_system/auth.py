"""Authentication utilities for booking system."""

import logging
import random
import secrets
from typing import Optional, Tuple

import redis
from django.conf import settings

logger = logging.getLogger(__name__)

# Initialize Redis connection
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True,
)

# Constants
OTP_EXPIRY_SECONDS = 300  # 5 minutes
SESSION_EXPIRY_SECONDS = 86400  # 24 hours
OTP_LENGTH = 6
RATE_LIMIT_WINDOW = 600  # 10 minutes
RATE_LIMIT_MAX_REQUESTS = 3


def generate_otp() -> str:
    """
    Generate a 6-digit OTP code.

    Returns:
        str: 6-digit OTP code
    """
    otp = "".join([str(random.randint(0, 9)) for _ in range(OTP_LENGTH)])
    logger.info("Generated OTP (length: %d)", len(otp))
    return otp


def store_otp(phone_number: str, otp: str) -> bool:
    """
    Store OTP in Redis with 5-minute expiry.

    Args:
        phone_number: User's phone number
        otp: OTP code to store

    Returns:
        bool: True if stored successfully
    """
    try:
        key = f"otp:{phone_number}"
        redis_client.setex(key, OTP_EXPIRY_SECONDS, otp)
        logger.info(
            "Stored OTP for phone %s with %d second expiry",
            phone_number,
            OTP_EXPIRY_SECONDS,
        )
        return True
    except redis.RedisError as e:
        logger.error("Failed to store OTP in Redis: %s", e)
        return False


def verify_otp(phone_number: str, otp: str) -> bool:
    """
    Verify OTP from Redis.

    In development mode, if DEV_OTP_CODE is set, that code will be accepted
    instead of requiring a real OTP from Redis.

    Args:
        phone_number: User's phone number
        otp: OTP code to verify

    Returns:
        bool: True if OTP is valid
    """
    # Check for development bypass
    from decouple import config

    dev_otp_code = config("DEV_OTP_CODE", default=None)
    if dev_otp_code and otp == dev_otp_code:
        logger.warning(
            "⚠️  DEVELOPMENT MODE: Accepted dev OTP code for phone %s", phone_number
        )
        return True

    try:
        key = f"otp:{phone_number}"
        stored_otp = redis_client.get(key)

        if stored_otp is None:
            logger.warning("No OTP found for phone %s", phone_number)
            return False

        if stored_otp == otp:
            logger.info("OTP verified successfully for phone %s", phone_number)
            return True

        logger.warning("Invalid OTP for phone %s", phone_number)
        return False
    except redis.RedisError as e:
        logger.error("Failed to verify OTP from Redis: %s", e)
        return False


def delete_otp(phone_number: str) -> bool:
    """
    Delete OTP from Redis after verification.

    Args:
        phone_number: User's phone number

    Returns:
        bool: True if deleted successfully
    """
    try:
        key = f"otp:{phone_number}"
        redis_client.delete(key)
        logger.info("Deleted OTP for phone %s", phone_number)
        return True
    except redis.RedisError as e:
        logger.error("Failed to delete OTP from Redis: %s", e)
        return False


def generate_session_token() -> str:
    """
    Generate a secure session token.

    Returns:
        str: Secure random token
    """
    token = secrets.token_urlsafe(32)
    logger.info("Generated session token")
    return token


def store_session(token: str, phone_number: str) -> bool:
    """
    Store session token in Redis with 24-hour expiry.

    Args:
        token: Session token
        phone_number: User's phone number

    Returns:
        bool: True if stored successfully
    """
    try:
        key = f"session:{token}"
        redis_client.setex(key, SESSION_EXPIRY_SECONDS, phone_number)
        logger.info(
            "Stored session for phone %s with %d second expiry",
            phone_number,
            SESSION_EXPIRY_SECONDS,
        )
        return True
    except redis.RedisError as e:
        logger.error("Failed to store session in Redis: %s", e)
        return False


def get_phone_from_session(token: str) -> Optional[str]:
    """
    Get phone number from session token.

    Args:
        token: Session token

    Returns:
        Optional[str]: Phone number if session is valid, None otherwise
    """
    try:
        key = f"session:{token}"
        phone_number = redis_client.get(key)

        if phone_number:
            logger.info("Retrieved phone number from session")
            return phone_number

        logger.warning("No session found for token")
        return None
    except redis.RedisError as e:
        logger.error("Failed to get session from Redis: %s", e)
        return None


def delete_session(token: str) -> bool:
    """
    Delete session from Redis.

    Args:
        token: Session token

    Returns:
        bool: True if deleted successfully
    """
    try:
        key = f"session:{token}"
        redis_client.delete(key)
        logger.info("Deleted session")
        return True
    except redis.RedisError as e:
        logger.error("Failed to delete session from Redis: %s", e)
        return False


def check_rate_limit(phone_number: str) -> Tuple[bool, int]:
    """
    Check if phone number has exceeded OTP request rate limit.

    Rate limit: 3 requests per 10 minutes.

    Args:
        phone_number: User's phone number

    Returns:
        Tuple[bool, int]: (is_allowed, remaining_requests)
    """
    try:
        key = f"rate_limit:{phone_number}"
        current_count_raw = redis_client.get(key)

        if current_count_raw is None:
            # First request
            redis_client.setex(key, RATE_LIMIT_WINDOW, 1)
            return True, RATE_LIMIT_MAX_REQUESTS - 1

        # Redis returns bytes or str, convert to int
        current_count = int(current_count_raw)

        if current_count >= RATE_LIMIT_MAX_REQUESTS:
            logger.warning("Rate limit exceeded for phone %s", phone_number)
            return False, 0

        # Increment counter
        redis_client.incr(key)
        remaining = RATE_LIMIT_MAX_REQUESTS - current_count - 1
        logger.info(
            "Rate limit check passed for phone %s, remaining: %d",
            phone_number,
            remaining,
        )
        return True, remaining
    except redis.RedisError as e:
        logger.error("Failed to check rate limit in Redis: %s", e)
        # Allow request on Redis error to avoid blocking users
        return True, RATE_LIMIT_MAX_REQUESTS
