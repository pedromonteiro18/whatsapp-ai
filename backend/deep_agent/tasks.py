"""
Celery tasks for deep-agent async message processing.

Provides async task execution for WhatsApp messages processed through
the deep-agent system.
"""

import logging
from typing import Any

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_deep_agent_message(
    self: Any, user_phone: str, message_content: str
) -> bool:
    """
    Process a WhatsApp message asynchronously through the deep-agent.

    This task:
    1. Processes the message through the deep-agent
    2. Sends the response via WhatsApp
    3. Handles errors and retries

    Args:
        user_phone: User's phone number (E.164 format)
        message_content: The message content from the user

    Returns:
        True if message was processed successfully, False otherwise
    """
    try:
        logger.info(
            f"Processing deep-agent message from {user_phone}: {message_content[:50]}..."
        )

        # Import here to avoid circular imports
        from backend.whatsapp.client import WhatsAppClient

        from .agent import process_message

        # Process message through deep-agent
        result = process_message(user_phone, message_content)

        if not result["success"]:
            error_msg = result.get("error", "Unknown error")
            logger.error(
                f"Deep-agent processing failed for {user_phone}: {error_msg}"
            )

            # Send generic error message to user
            whatsapp_client = WhatsAppClient()
            error_response = (
                "I apologize, but I encountered an error processing your request. "
                "Please try again in a moment."
            )
            whatsapp_client.send_message(f"whatsapp:{user_phone}", error_response)

            # Don't retry on agent errors
            return False

        # Send agent's response via WhatsApp
        agent_response = result["response"]
        whatsapp_client = WhatsAppClient()

        # Handle long responses (WhatsApp has ~4096 char limit)
        if len(agent_response) > 4000:
            logger.warning(
                f"Response too long ({len(agent_response)} chars), truncating"
            )
            agent_response = agent_response[:3900] + "\n\n[Response truncated]"

        whatsapp_client.send_message(f"whatsapp:{user_phone}", agent_response)

        logger.info(
            f"Deep-agent response sent to {user_phone} "
            f"(length: {len(agent_response)} chars)"
        )

        return True

    except Exception as e:
        logger.error(
            f"Error in process_deep_agent_message for {user_phone}: {e}",
            exc_info=True,
        )

        # Retry on unexpected errors
        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error(
                f"Max retries exceeded for deep-agent message from {user_phone}"
            )

            # Send final error message to user
            try:
                from backend.whatsapp.client import WhatsAppClient

                whatsapp_client = WhatsAppClient()
                whatsapp_client.send_message(
                    f"whatsapp:{user_phone}",
                    "I'm having trouble responding right now. "
                    "Please try again later or contact our support team.",
                )
            except Exception as notification_error:
                logger.error(f"Failed to send error notification: {notification_error}")

            return False


@shared_task
def test_deep_agent() -> dict:
    """
    Test task to verify deep-agent is working.

    Returns:
        Dictionary with test results
    """
    try:
        from .agent import get_agent

        agent = get_agent()

        logger.info("Testing deep-agent...")

        # Simple test message
        result = agent.process_message("+1234567890", "Hello!")

        if result["success"]:
            logger.info("Deep-agent test successful")
            return {
                "status": "success",
                "message": "Deep-agent is working",
                "response_length": len(result["response"]),
            }
        else:
            logger.error(f"Deep-agent test failed: {result.get('error')}")
            return {
                "status": "failed",
                "error": result.get("error"),
            }

    except Exception as e:
        logger.error(f"Deep-agent test error: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
        }
