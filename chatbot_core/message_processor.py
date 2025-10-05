"""
Message Processor for WhatsApp AI Chatbot.

Orchestrates the complete message processing flow including:
- Conversation management (database and Redis)
- AI interaction with conversation history
- Message persistence
- Error handling and user notifications
"""

import logging
from typing import Any, Dict, List, Optional

from django.db import transaction
from django.utils import timezone

from ai_integration.adapters.base import (
    APIError,
    AuthenticationError,
    BaseAIAdapter,
    RateLimitError,
    TimeoutError,
)
from ai_integration.factory import AIAdapterFactory

from .conversation_manager import ConversationManager
from .models import Conversation, Message

logger = logging.getLogger(__name__)


class MessageProcessor:
    """
    Processes incoming WhatsApp messages and generates AI responses.

    Handles the complete message lifecycle:
    1. Retrieve/create user conversation
    2. Load conversation history from Redis
    3. Send message to AI with context
    4. Save messages to database and Redis
    5. Handle errors with user-friendly notifications
    """

    def __init__(
        self,
        whatsapp_client: Any,
        ai_adapter: Optional[BaseAIAdapter] = None,
        conversation_manager: Optional[ConversationManager] = None,
    ):
        """
        Initialize the message processor.

        Args:
            whatsapp_client: WhatsApp client for sending responses
            ai_adapter: AI adapter instance (creates default if None)
            conversation_manager: Conversation manager instance (creates default if None)
        """
        self.whatsapp_client = whatsapp_client
        self.ai_adapter = ai_adapter or AIAdapterFactory.create_adapter()
        self.conversation_manager = conversation_manager or ConversationManager()

    def process_message(self, user_phone: str, message_content: str) -> bool:
        """
        Process an incoming message and send AI response.

        Args:
            user_phone: User's phone number (WhatsApp identifier)
            message_content: The message content from the user

        Returns:
            True if message was processed successfully, False otherwise
        """
        try:
            logger.info(
                f"Processing message from {user_phone}: {message_content[:50]}..."
            )

            # Get or create conversation
            conversation = self._get_or_create_conversation(user_phone)

            # Get conversation history from Redis
            history = self.conversation_manager.get_history(user_phone)

            # Format history for AI adapter
            formatted_history = self._format_history_for_ai(history)

            # Add current user message to history
            formatted_history.append(
                {
                    "role": "user",
                    "content": message_content,
                }
            )

            # Get AI response
            logger.info(f"Sending to AI: {len(formatted_history)} messages in context")
            response = self.ai_adapter.send_message(formatted_history)
            ai_response = response["content"]
            metadata = response.get("metadata", {})

            # Save messages to database
            with transaction.atomic():
                # Save user message
                Message.objects.create(
                    conversation=conversation,
                    role="user",
                    content=message_content,
                )

                # Save AI response
                Message.objects.create(
                    conversation=conversation,
                    role="assistant",
                    content=ai_response,
                    metadata=metadata,
                )

                # Update conversation last_activity (auto_now handles this, but explicit save ensures it)
                conversation.save()

            # Save messages to Redis
            self.conversation_manager.add_message(user_phone, "user", message_content)
            self.conversation_manager.add_message(
                user_phone, "assistant", ai_response, metadata=metadata
            )

            # Send response to user
            self.whatsapp_client.send_message(user_phone, ai_response)

            logger.info(
                f"Successfully processed message for {user_phone}, "
                f"response length: {len(ai_response)}"
            )
            return True

        except (AuthenticationError, RateLimitError, TimeoutError, APIError) as e:
            # Handle known AI errors with user-friendly messages
            logger.error(
                f"AI error processing message for {user_phone}: {type(e).__name__}",
                exc_info=True,
            )

            match e:
                case AuthenticationError():
                    error_message = "The service is temporarily unavailable. Please try again later."
                case RateLimitError():
                    error_message = "We're experiencing high demand. Please try again in a few moments."
                case TimeoutError():
                    error_message = "The request timed out. Please try again."
                case APIError():
                    error_message = "There was an error processing your request. Please try again later."

            try:
                self.whatsapp_client.send_message(user_phone, error_message)
                return True  # Error handled, user notified
            except Exception as notification_error:
                logger.error(
                    f"Failed to send error notification to {user_phone}: {notification_error}"
                )
                return False  # Failed to notify user

        except Exception as e:
            # Handle unexpected errors
            logger.error(
                f"Unexpected error processing message for {user_phone}: {e}",
                exc_info=True,
            )
            try:
                self.whatsapp_client.send_message(
                    user_phone,
                    "An unexpected error occurred. Please try again later."
                )
                return True  # Notified user of unexpected error
            except Exception:
                return False  # Complete failure

    def _get_or_create_conversation(self, user_phone: str) -> Conversation:
        """
        Retrieve or create a conversation for a user.

        Args:
            user_phone: User's phone number

        Returns:
            Conversation instance
        """
        conversation, created = Conversation.objects.get_or_create(
            user_phone=user_phone,
            is_active=True,
            defaults={
                "user_phone": user_phone,
                "is_active": True,
            },
        )

        if created:
            logger.info(f"Created new conversation for {user_phone}")
        else:
            logger.info(f"Retrieved existing conversation for {user_phone}")

        return conversation

    def _format_history_for_ai(
        self, history: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """
        Format conversation history for AI adapter.

        Args:
            history: Raw history from ConversationManager

        Returns:
            List of message dicts with 'role' and 'content' keys
        """
        formatted = []
        for msg in history:
            formatted.append(
                {
                    "role": msg["role"],
                    "content": msg["content"],
                }
            )
        return formatted
