"""
Base adapter interface for AI providers.

Defines the contract that all AI provider adapters must implement,
with common retry logic and error handling.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AIError(Exception):
    """Base exception for AI adapter errors."""

    pass


class AuthenticationError(AIError):
    """Raised when API authentication fails."""

    pass


class RateLimitError(AIError):
    """Raised when API rate limit is exceeded."""

    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class TimeoutError(AIError):
    """Raised when API request times out."""

    pass


class APIError(AIError):
    """Raised for general API errors."""

    pass


class BaseAIAdapter(ABC):
    """
    Abstract base class for AI provider adapters.

    Defines the interface that all AI adapters must implement
    and provides common retry and error handling logic.
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize the AI adapter.

        Args:
            api_key: API key for authentication
            model: Model name to use
            max_tokens: Maximum tokens for responses
            temperature: Temperature for response generation (0.0-2.0)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self.max_retries = max_retries

    @abstractmethod
    def send_message(
        self, messages: List[Dict[str, str]], **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Send messages to the AI provider and return response.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            **kwargs: Additional provider-specific parameters

        Returns:
            Dict containing:
                - content: The response text
                - metadata: Dict with tokens_used, model_version, etc.

        Raises:
            AuthenticationError: If API credentials are invalid
            RateLimitError: If rate limit is exceeded
            TimeoutError: If request times out
            APIError: For other API errors
        """
        pass

    @abstractmethod
    def validate_credentials(self) -> bool:
        """
        Validate that the API credentials are valid.

        Returns:
            True if credentials are valid, False otherwise

        Raises:
            AuthenticationError: If credentials are invalid
            APIError: For other API errors
        """
        pass

    def _retry_with_exponential_backoff(self, func, *args, **kwargs) -> Dict[str, Any]:
        """
        Execute a function with exponential backoff retry logic.

        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            The function's return value

        Raises:
            The last exception if all retries fail
        """
        last_exception: Optional[Exception] = None

        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)  # type: ignore[no-any-return]
            except RateLimitError as e:
                last_exception = e
                wait_time = e.retry_after if e.retry_after else (2**attempt)
                logger.warning(
                    f"Rate limit hit, retrying in {wait_time}s "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(wait_time)
            except (TimeoutError, APIError) as e:
                last_exception = e
                wait_time = 2**attempt
                logger.warning(
                    f"API error: {e}, retrying in {wait_time}s "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(wait_time)
            except AuthenticationError as e:
                # Don't retry authentication errors
                logger.error(f"Authentication failed: {e}")
                raise

        # All retries exhausted
        logger.error(f"All {self.max_retries} retry attempts failed")
        if last_exception:
            raise last_exception
        raise APIError("Maximum retry attempts exceeded")

    def _format_error_message(self, error: Exception) -> str:
        """
        Format an error into a user-friendly message.

        Args:
            error: The exception that occurred

        Returns:
            User-friendly error message
        """
        if isinstance(error, AuthenticationError):
            return "The service is temporarily unavailable. Please contact support."
        elif isinstance(error, RateLimitError):
            return "I'm receiving a lot of messages. Please wait a moment before sending another."
        elif isinstance(error, TimeoutError):
            return "This is taking longer than expected. Let me try again..."
        elif isinstance(error, APIError):
            return (
                "I'm having trouble connecting right now. Please try again in a moment."
            )
        else:
            return "An unexpected error occurred. Please try again."

    def __str__(self) -> str:
        """String representation of the adapter."""
        return f"{self.__class__.__name__}(model={self.model})"
