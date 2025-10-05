"""
Conversation Manager for Redis-based conversation history storage.

Manages conversation history with automatic expiration and context window limiting.
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional

import redis

from .config import Config

logger = logging.getLogger(__name__)


class ConversationManager:
    """
    Manages conversation history using Redis for fast access and automatic expiration.

    Uses Redis sorted sets to store messages with timestamps, enabling:
    - Efficient retrieval of recent messages
    - Automatic expiration of old conversations
    - Context window management (limiting message history)
    """

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        max_history: Optional[int] = None,
        ttl_seconds: Optional[int] = None,
    ):
        """
        Initialize the conversation manager.

        Args:
            redis_client: Redis client instance (creates default if None)
            max_history: Maximum messages to keep in context window
            ttl_seconds: Time-to-live for conversation keys in seconds
        """
        self.redis = redis_client or redis.Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            db=Config.REDIS_DB,
            decode_responses=True,
        )
        self.max_history = max_history or Config.MAX_CONVERSATION_HISTORY
        self.ttl_seconds = ttl_seconds or Config.CONVERSATION_TTL_SECONDS

    def _get_key(self, user_id: str) -> str:
        """
        Generate Redis key for a user's conversation.

        Args:
            user_id: User identifier (phone number)

        Returns:
            Redis key string
        """
        return f"conversation:{user_id}"

    def get_history(self, user_id: str, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Retrieve conversation history for a user.

        Args:
            user_id: User identifier (phone number)
            limit: Maximum number of messages to retrieve (defaults to max_history)

        Returns:
            List of message dictionaries with 'role', 'content', and 'timestamp' keys
            Ordered from oldest to newest
        """
        try:
            key = self._get_key(user_id)
            limit = limit or self.max_history

            # Retrieve messages from sorted set (most recent N)
            # zrevrange gets items in reverse order (newest first), so we reverse again
            messages_json = self.redis.zrevrange(key, 0, limit - 1)

            # Parse JSON and reverse to get oldest-to-newest order
            messages = []
            for msg_json in reversed(messages_json):
                try:
                    msg = json.loads(msg_json)
                    messages.append(msg)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse message JSON: {e}")
                    continue

            logger.info(
                f"Retrieved {len(messages)} messages for user {user_id} (limit={limit})"
            )
            return messages

        except redis.RedisError as e:
            logger.error(f"Redis error getting history for user {user_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting history for user {user_id}: {e}")
            return []

    def add_message(
        self, user_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a message to the conversation history.

        Args:
            user_id: User identifier (phone number)
            role: Message role ('user', 'assistant', 'system')
            content: Message content
            metadata: Optional metadata to store with the message

        Returns:
            True if successful, False otherwise
        """
        try:
            key = self._get_key(user_id)
            timestamp = time.time()

            # Create message object
            message = {
                "role": role,
                "content": content,
                "timestamp": timestamp,
            }
            if metadata:
                message["metadata"] = metadata

            # Serialize to JSON
            message_json = json.dumps(message)

            # Add to sorted set with timestamp as score
            self.redis.zadd(key, {message_json: timestamp})

            # Trim to max history size (keep only most recent messages)
            # Keep messages from -(max_history) to -1 (most recent)
            self.redis.zremrangebyrank(key, 0, -(self.max_history + 1))

            # Set expiration on the key
            self.redis.expire(key, self.ttl_seconds)

            logger.info(
                f"Added {role} message for user {user_id} (length={len(content)})"
            )
            return True

        except redis.RedisError as e:
            logger.error(f"Redis error adding message for user {user_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error adding message for user {user_id}: {e}")
            return False

    def clear_history(self, user_id: str) -> bool:
        """
        Clear all conversation history for a user.

        Args:
            user_id: User identifier (phone number)

        Returns:
            True if successful, False otherwise
        """
        try:
            key = self._get_key(user_id)
            deleted = self.redis.delete(key)

            logger.info(
                f"Cleared conversation history for user {user_id} (deleted={deleted})"
            )
            return deleted > 0

        except redis.RedisError as e:
            logger.error(f"Redis error clearing history for user {user_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error clearing history for user {user_id}: {e}")
            return False

    def set_expiration(self, user_id: str, ttl: Optional[int] = None) -> bool:
        """
        Set or update the expiration time for a conversation.

        Args:
            user_id: User identifier (phone number)
            ttl: Time-to-live in seconds (defaults to configured TTL)

        Returns:
            True if successful, False otherwise
        """
        try:
            key = self._get_key(user_id)
            ttl = ttl or self.ttl_seconds

            result = self.redis.expire(key, ttl)
            logger.info(f"Set expiration for user {user_id} to {ttl}s (result={result})")
            return result

        except redis.RedisError as e:
            logger.error(f"Redis error setting expiration for user {user_id}: {e}")
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error setting expiration for user {user_id}: {e}"
            )
            return False

    def get_message_count(self, user_id: str) -> int:
        """
        Get the number of messages in a conversation.

        Args:
            user_id: User identifier (phone number)

        Returns:
            Number of messages in the conversation
        """
        try:
            key = self._get_key(user_id)
            count = self.redis.zcard(key)
            return count

        except redis.RedisError as e:
            logger.error(f"Redis error getting message count for user {user_id}: {e}")
            return 0
        except Exception as e:
            logger.error(
                f"Unexpected error getting message count for user {user_id}: {e}"
            )
            return 0

    def conversation_exists(self, user_id: str) -> bool:
        """
        Check if a conversation exists for a user.

        Args:
            user_id: User identifier (phone number)

        Returns:
            True if conversation exists, False otherwise
        """
        try:
            key = self._get_key(user_id)
            return self.redis.exists(key) > 0

        except redis.RedisError as e:
            logger.error(f"Redis error checking existence for user {user_id}: {e}")
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error checking existence for user {user_id}: {e}"
            )
            return False
