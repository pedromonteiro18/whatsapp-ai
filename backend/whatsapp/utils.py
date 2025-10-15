"""
Utility functions for WhatsApp integration.

This module provides helper functions for webhook signature verification
and other WhatsApp-related utilities.
"""

import logging
from typing import Optional

from twilio.request_validator import RequestValidator

from backend.chatbot_core.config import Config

logger = logging.getLogger(__name__)


def verify_webhook_signature(
    url: str,
    post_data: dict,
    signature: str,
    auth_token: Optional[str] = None,
) -> bool:
    """
    Verify that a webhook request came from Twilio.

    Uses Twilio's request validator to verify the X-Twilio-Signature header
    matches the expected signature for the request.

    Args:
        url: The full URL of the webhook endpoint (including protocol and domain)
        post_data: Dictionary of POST parameters from the request
        signature: The X-Twilio-Signature header value from the request
        auth_token: Twilio auth token (defaults to Config value)

    Returns:
        bool: True if signature is valid, False otherwise

    Example:
        >>> url = "https://example.com/api/whatsapp/webhook/"
        >>> post_data = {"From": "whatsapp:+1234567890", "Body": "Hello"}
        >>> signature = request.headers.get("X-Twilio-Signature")
        >>> is_valid = verify_webhook_signature(url, post_data, signature)
    """
    if not signature:
        logger.warning("No signature provided for webhook verification")
        return False

    # Use configured auth token if not provided
    token = auth_token or Config.TWILIO_AUTH_TOKEN
    if not token:
        logger.error("Twilio auth token not configured")
        return False

    try:
        # Create validator with auth token
        validator = RequestValidator(token)

        # Validate the request
        is_valid = validator.validate(url, post_data, signature)

        if is_valid:
            logger.debug("Webhook signature verified successfully")
        else:
            logger.warning("Webhook signature verification failed")

        return bool(is_valid)

    except Exception as e:  # noqa: BLE001
        logger.error("Error during webhook signature verification: %s", e)
        return False
