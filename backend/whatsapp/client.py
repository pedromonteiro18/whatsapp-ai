"""
WhatsApp client for sending messages via Twilio API.

This module provides a client for sending WhatsApp messages through
the Twilio API with retry logic and error handling.
"""

import logging
import time
from typing import Optional

from twilio.base.exceptions import TwilioException, TwilioRestException
from twilio.rest import Client

from backend.chatbot_core.config import Config

logger = logging.getLogger(__name__)


class WhatsAppClientError(Exception):
    """Base exception for WhatsApp client errors."""


class WhatsAppClient:
    """
    Client for sending WhatsApp messages via Twilio API.

    Handles message sending with retry logic and comprehensive error handling.
    """

    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        from_number: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize WhatsApp client.

        Args:
            account_sid: Twilio account SID (defaults to Config value)
            auth_token: Twilio auth token (defaults to Config value)
            from_number: WhatsApp number to send from (defaults to Config value)
            max_retries: Maximum number of retry attempts for failed sends
            retry_delay: Initial delay between retries in seconds
        """
        self.account_sid = account_sid or Config.TWILIO_ACCOUNT_SID
        self.auth_token = auth_token or Config.TWILIO_AUTH_TOKEN
        self.from_number = from_number or Config.TWILIO_WHATSAPP_NUMBER
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Validate configuration
        if not self.account_sid:
            raise WhatsAppClientError("Twilio account SID is not configured")
        if not self.auth_token:
            raise WhatsAppClientError("Twilio auth token is not configured")
        if not self.from_number:
            raise WhatsAppClientError("Twilio WhatsApp number is not configured")

        # Initialize Twilio client
        try:
            self.client = Client(self.account_sid, self.auth_token)
            logger.info("WhatsApp client initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Twilio client: %s", e)
            raise WhatsAppClientError(f"Failed to initialize Twilio client: {e}") from e

    def send_message(self, to: str, message: str) -> bool:
        """
        Send a WhatsApp message to a user.

        Implements retry logic with exponential backoff for transient failures.

        Args:
            to: Recipient phone number in WhatsApp format (e.g., whatsapp:+1234567890)
            message: Message content to send

        Returns:
            bool: True if message was sent successfully, False otherwise

        Raises:
            WhatsAppClientError: If message sending fails after all retries
        """
        # Ensure recipient number has whatsapp: prefix
        if not to.startswith("whatsapp:"):
            to = f"whatsapp:{to}"

        # Validate message content
        if not message or not message.strip():
            logger.error("Cannot send empty message")
            raise WhatsAppClientError("Message content cannot be empty")

        # Attempt to send with retries
        last_error = None
        for attempt in range(self.max_retries):
            try:
                logger.info(
                    "Sending WhatsApp message to %s (attempt %d/%d)",
                    to,
                    attempt + 1,
                    self.max_retries,
                )

                # Send message via Twilio
                twilio_message = self.client.messages.create(
                    body=message, from_=self.from_number, to=to
                )

                logger.info(
                    "Message sent successfully. SID: %s, Status: %s",
                    twilio_message.sid,
                    twilio_message.status,
                )
                return True

            except TwilioRestException as e:
                last_error = e
                logger.warning(
                    "Twilio REST error on attempt %d: Code %s, Message: %s",
                    attempt + 1,
                    e.code,
                    e.msg,
                )

                # Don't retry for certain error codes
                if e.code in [
                    21211,  # Invalid 'To' Phone Number
                    21408,  # Permission to send an SMS/MMS has not been enabled
                    21610,  # Attempt to send to unsubscribed recipient
                ]:
                    logger.error("Non-retryable Twilio error %s: %s", e.code, e.msg)
                    raise WhatsAppClientError(f"Failed to send message: {e.msg}") from e

                # Retry for other errors
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2**attempt)  # Exponential backoff
                    logger.info("Retrying in %s seconds...", delay)
                    time.sleep(delay)

            except TwilioException as e:
                last_error = e
                logger.warning(
                    "Twilio exception on attempt %d: %s", attempt + 1, str(e)
                )

                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2**attempt)
                    logger.info("Retrying in %s seconds...", delay)
                    time.sleep(delay)

            except Exception as e:  # noqa: BLE001
                last_error = e
                logger.error("Unexpected error on attempt %d: %s", attempt + 1, str(e))

                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2**attempt)
                    logger.info("Retrying in %s seconds...", delay)
                    time.sleep(delay)

        # All retries exhausted
        error_msg = f"Failed to send message after {self.max_retries} attempts"
        if last_error:
            error_msg += f": {str(last_error)}"

        logger.error(error_msg)
        raise WhatsAppClientError(error_msg)

    def send_typing_indicator(self, to: str) -> bool:
        """
        Send a typing indicator to show the bot is processing.

        Note: Twilio WhatsApp API has limited support for typing indicators.
        This is a placeholder for future enhancement.

        Args:
            to: Recipient phone number in WhatsApp format

        Returns:
            bool: Always returns False as typing indicators are not fully supported
        """
        logger.debug("Typing indicator requested for %s (not supported)", to)
        return False
