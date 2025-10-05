"""
Celery tasks for asynchronous message processing and maintenance.

This module contains Celery tasks for:
- Processing incoming WhatsApp messages asynchronously
- Cleaning up expired conversations periodically
"""

import logging
from datetime import timedelta
from typing import Any

from celery import shared_task
from django.utils import timezone

from whatsapp.client import WhatsAppClient, WhatsAppClientError

from .message_processor import MessageProcessor
from .models import Conversation

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 minute
    time_limit=300,  # 5 minutes hard limit
    soft_time_limit=240,  # 4 minutes soft limit
    acks_late=True,  # Acknowledge after task completes
    reject_on_worker_lost=True,  # Reject if worker crashes
)
def process_whatsapp_message(
    self: Any, user_phone: str, message_content: str
) -> bool:
    """
    Process an incoming WhatsApp message asynchronously.

    This task wraps the MessageProcessor to handle messages in the background,
    allowing the webhook to respond quickly while processing happens async.

    Args:
        self: Celery task instance (bound)
        user_phone: User's phone number (WhatsApp identifier)
        message_content: The message content from the user

    Returns:
        bool: True if message was processed successfully

    Raises:
        Exception: Retries on transient failures, fails permanently on critical errors
    """
    task_id = self.request.id
    logger.info(
        f"[Task {task_id}] Processing WhatsApp message from {user_phone}: "
        f"{message_content[:50]}..."
    )

    try:
        # Initialize WhatsApp client and message processor
        whatsapp_client = WhatsAppClient()
        processor = MessageProcessor(whatsapp_client)

        # Process the message
        success = processor.process_message(user_phone, message_content)

        if success:
            logger.info(
                f"[Task {task_id}] Successfully processed message for {user_phone}"
            )
            return True
        else:
            logger.error(
                f"[Task {task_id}] Failed to process message for {user_phone}"
            )
            return False

    except WhatsAppClientError as e:
        # WhatsApp client initialization or sending failed
        logger.error(
            f"[Task {task_id}] WhatsApp client error for {user_phone}: {e}",
            exc_info=True,
        )
        # Don't retry WhatsApp client errors - they're likely configuration issues
        return False

    except Exception as e:
        # Unexpected error - retry with exponential backoff
        logger.error(
            f"[Task {task_id}] Unexpected error processing message for {user_phone}: {e}",
            exc_info=True,
        )

        # Retry with exponential backoff (60s, 120s, 240s)
        try:
            # Calculate exponential backoff: 60 * 2^retry_count
            retry_delay = 60 * (2 ** self.request.retries)
            raise self.retry(exc=e, countdown=retry_delay)
        except self.MaxRetriesExceededError:
            logger.error(
                f"[Task {task_id}] Max retries exceeded for {user_phone}. Giving up."
            )
            return False


@shared_task(
    bind=True,
    time_limit=600,  # 10 minutes hard limit
    soft_time_limit=540,  # 9 minutes soft limit
)
def cleanup_expired_conversations(self: Any) -> dict[str, int]:
    """
    Clean up expired conversations from the database.

    This periodic task removes inactive conversations that are older than
    the configured TTL. It helps maintain database hygiene and prevents
    unbounded growth.

    Args:
        self: Celery task instance (bound)

    Returns:
        dict: Statistics about the cleanup operation
            - deleted_count: Number of conversations deleted
            - checked_count: Number of conversations checked
    """
    task_id = self.request.id
    logger.info(f"[Task {task_id}] Starting conversation cleanup")

    try:
        # Import here to avoid circular imports
        from .config import Config

        # Calculate cutoff time based on TTL
        ttl_seconds = Config.CONVERSATION_TTL_SECONDS
        cutoff_time = timezone.now() - timedelta(seconds=ttl_seconds)

        logger.info(
            f"[Task {task_id}] Looking for conversations older than {cutoff_time}"
        )

        # Find inactive conversations older than TTL
        expired_conversations = Conversation.objects.filter(
            is_active=False, last_activity__lt=cutoff_time
        )

        checked_count = expired_conversations.count()
        logger.info(
            f"[Task {task_id}] Found {checked_count} expired conversations to delete"
        )

        # Delete expired conversations
        deleted_count, _ = expired_conversations.delete()

        logger.info(
            f"[Task {task_id}] Cleanup complete: deleted {deleted_count} conversations"
        )

        return {"deleted_count": deleted_count, "checked_count": checked_count}

    except Exception as e:
        logger.error(
            f"[Task {task_id}] Error during conversation cleanup: {e}", exc_info=True
        )
        raise
