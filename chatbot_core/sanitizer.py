"""
Input sanitization utilities for WhatsApp AI Chatbot.

Provides utilities for:
- Message content sanitization
- Phone number validation and formatting
- Special character handling
"""

import html
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class Sanitizer:
    """
    Utility class for sanitizing and validating user inputs.

    Protects against injection attacks and ensures data consistency.
    """

    # Phone number pattern (E.164 format)
    PHONE_PATTERN = re.compile(r"^\+?[1-9]\d{1,14}$")

    # Dangerous patterns to remove from messages
    DANGEROUS_PATTERNS = [
        re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL),
        re.compile(r"javascript:", re.IGNORECASE),
        re.compile(r"on\w+\s*=", re.IGNORECASE),  # Event handlers like onclick=
    ]

    @classmethod
    def sanitize_message(cls, message: str, max_length: int = 4096) -> str:
        """
        Sanitize user message content.

        Removes potentially dangerous content while preserving legitimate text.
        Does not escape HTML entities to allow WhatsApp markdown formatting.

        Args:
            message: Raw message content
            max_length: Maximum allowed message length

        Returns:
            Sanitized message content
        """
        if not message:
            return ""

        # Trim whitespace
        sanitized = message.strip()

        # Enforce maximum length
        if len(sanitized) > max_length:
            logger.warning(
                f"Message truncated from {len(sanitized)} to {max_length} characters"
            )
            sanitized = sanitized[:max_length]

        # Remove dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            sanitized = pattern.sub("", sanitized)

        # Remove null bytes
        sanitized = sanitized.replace("\x00", "")

        # Normalize whitespace (collapse multiple spaces/newlines)
        sanitized = re.sub(r"\s+", " ", sanitized)
        sanitized = re.sub(r"\n{3,}", "\n\n", sanitized)  # Max 2 consecutive newlines

        return sanitized.strip()

    @classmethod
    def sanitize_response(cls, response: str) -> str:
        """
        Sanitize AI response before sending to user.

        Ensures response is safe for WhatsApp delivery and doesn't contain
        potentially dangerous content.

        Args:
            response: AI-generated response

        Returns:
            Sanitized response
        """
        if not response:
            return ""

        # Basic sanitization
        sanitized = response.strip()

        # Remove null bytes
        sanitized = sanitized.replace("\x00", "")

        # WhatsApp has a 4096 character limit for messages
        if len(sanitized) > 4096:
            logger.warning(
                f"Response truncated from {len(sanitized)} to 4096 characters"
            )
            sanitized = sanitized[:4093] + "..."

        return sanitized

    @classmethod
    def validate_phone_number(cls, phone: str) -> bool:
        """
        Validate phone number format.

        Checks if phone number conforms to E.164 format.

        Args:
            phone: Phone number to validate

        Returns:
            True if valid, False otherwise
        """
        if not phone:
            return False

        # Remove whatsapp: prefix if present
        if phone.startswith("whatsapp:"):
            phone = phone[9:]

        # Check E.164 format
        return bool(cls.PHONE_PATTERN.match(phone))

    @classmethod
    def format_phone_number(cls, phone: str) -> Optional[str]:
        """
        Format and validate phone number.

        Ensures phone number is in correct format for WhatsApp API.

        Args:
            phone: Phone number to format

        Returns:
            Formatted phone number with whatsapp: prefix, or None if invalid
        """
        if not phone:
            return None

        # Remove whatsapp: prefix if already present
        if phone.startswith("whatsapp:"):
            phone = phone[9:]

        # Validate format
        if not cls.validate_phone_number(phone):
            logger.warning(f"Invalid phone number format: {phone}")
            return None

        # Ensure + prefix
        if not phone.startswith("+"):
            phone = f"+{phone}"

        # Add whatsapp: prefix
        return f"whatsapp:{phone}"

    @classmethod
    def escape_special_characters(cls, text: str) -> str:
        """
        Escape special characters for safe display.

        Useful for logging or displaying user content in admin interfaces.

        Args:
            text: Text to escape

        Returns:
            Escaped text with HTML entities
        """
        if not text:
            return ""

        return html.escape(text)

    @classmethod
    def is_safe_content(cls, content: str) -> bool:
        """
        Check if content appears to be safe.

        Performs basic heuristic checks for potentially dangerous content.

        Args:
            content: Content to check

        Returns:
            True if content appears safe, False if potentially dangerous
        """
        if not content:
            return True

        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if pattern.search(content):
                logger.warning("Dangerous pattern detected in content")
                return False

        # Check for excessive special characters (potential obfuscation)
        special_char_count = sum(
            1 for c in content if not c.isalnum() and not c.isspace()
        )
        if len(content) > 0 and special_char_count / len(content) > 0.3:
            logger.warning(
                f"Excessive special characters in content: {special_char_count}/{len(content)}"
            )
            return False

        return True

    @classmethod
    def truncate_safely(cls, text: str, max_length: int, suffix: str = "...") -> str:
        """
        Truncate text to maximum length without breaking words.

        Args:
            text: Text to truncate
            max_length: Maximum length including suffix
            suffix: Suffix to append if truncated

        Returns:
            Truncated text
        """
        if not text or len(text) <= max_length:
            return text

        # Reserve space for suffix
        truncate_at = max_length - len(suffix)

        # Try to break at word boundary
        last_space = text[:truncate_at].rfind(" ")
        if last_space > truncate_at * 0.8:  # Only if we're not losing too much
            truncate_at = last_space

        return text[:truncate_at].strip() + suffix
