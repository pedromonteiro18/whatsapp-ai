"""
OpenRouter adapter implementation.

Provides integration with OpenRouter's unified API for multiple AI providers.
OpenRouter provides access to OpenAI, Anthropic, and many other models through
a single OpenAI-compatible API.
"""

import logging
from typing import Any, Dict, List, Optional, cast

import openai
from openai.types.chat import ChatCompletionMessageParam

from .base import (
    APIError,
    AuthenticationError,
    BaseAIAdapter,
    RateLimitError,
    TimeoutError,
)

logger = logging.getLogger(__name__)


class OpenRouterAdapter(BaseAIAdapter):
    """
    Adapter for OpenRouter's unified AI API.

    OpenRouter provides access to multiple AI providers (OpenAI, Anthropic, etc.)
    through a single OpenAI-compatible API. This adapter works with any model
    available on OpenRouter.

    Examples of supported models:
    - openai/gpt-4
    - openai/gpt-3.5-turbo
    - anthropic/claude-3-opus
    - anthropic/claude-3-sonnet
    - meta-llama/llama-3-70b-instruct
    - google/gemini-pro
    """

    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(
        self,
        api_key: str,
        model: str,
        app_name: Optional[str] = None,
        site_url: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Initialize OpenRouter adapter.

        Args:
            api_key: OpenRouter API key
            model: Model name (e.g., 'openai/gpt-4', 'anthropic/claude-3-sonnet')
            app_name: Optional application name for OpenRouter's request headers
            site_url: Optional site URL for OpenRouter's request headers
            **kwargs: Additional parameters (max_tokens, temperature, etc.)
        """
        super().__init__(api_key, model, **kwargs)

        # Initialize OpenAI client with OpenRouter's base URL
        self.client = openai.OpenAI(
            api_key=api_key, base_url=self.OPENROUTER_BASE_URL, timeout=self.timeout
        )

        # OpenRouter-specific headers
        self.app_name = app_name or "WhatsApp AI Chatbot"
        self.site_url = site_url

    def send_message(
        self, messages: List[Dict[str, str]], **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Send messages to OpenRouter and return response.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
                     Roles: 'system', 'user', 'assistant'
            **kwargs: Additional OpenRouter parameters (override defaults)

        Returns:
            Dict with 'content' (response text) and 'metadata' (usage info)

        Raises:
            AuthenticationError: If API key is invalid
            RateLimitError: If rate limit exceeded
            TimeoutError: If request times out
            APIError: For other API errors
        """
        try:
            # Prepare parameters, allowing kwargs to override defaults
            params = {
                "model": self.model,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
            }
            params.update(kwargs)

            logger.info(
                f"Sending request to OpenRouter: model={params['model']}, "
                f"messages={len(messages)}, max_tokens={params['max_tokens']}"
            )

            # Make API call with retry logic
            response = self._retry_with_exponential_backoff(
                self._make_request, params
            )

            return response

        except (AuthenticationError, RateLimitError, TimeoutError, APIError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error in OpenRouter adapter: {e}")
            raise APIError(f"Unexpected error: {str(e)}")

    def _make_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make the actual API request to OpenRouter.

        Args:
            params: Request parameters

        Returns:
            Dict with response content and metadata

        Raises:
            AuthenticationError, RateLimitError, TimeoutError, APIError
        """
        try:
            # Add OpenRouter-specific headers
            extra_headers = {
                "HTTP-Referer": self.site_url or "https://github.com/whatsapp-ai",
                "X-Title": self.app_name,
            }

            # Cast messages to proper type for OpenAI API
            messages_typed = cast(List[ChatCompletionMessageParam], params["messages"])
            response = self.client.chat.completions.create(
                model=params["model"],
                messages=messages_typed,
                max_tokens=params.get("max_tokens", self.max_tokens),
                temperature=params.get("temperature", self.temperature),
                extra_headers=extra_headers,
            )

            # Extract response content
            choices = list(response.choices)
            content = choices[0].message.content

            # Extract metadata
            usage = response.usage
            metadata: Dict[str, Any] = {
                "model_version": response.model,
                "tokens_used": {
                    "prompt_tokens": usage.prompt_tokens if usage else 0,
                    "completion_tokens": usage.completion_tokens if usage else 0,
                    "total_tokens": usage.total_tokens if usage else 0,
                },
                "finish_reason": choices[0].finish_reason,
            }

            logger.info(
                f"OpenRouter response received: tokens={metadata['tokens_used']['total_tokens']}, "
                f"finish_reason={metadata['finish_reason']}"
            )

            return {"content": content, "metadata": metadata}

        except openai.AuthenticationError as e:
            logger.error(f"OpenRouter authentication failed: {e}")
            raise AuthenticationError(f"Invalid OpenRouter API key: {str(e)}")

        except openai.RateLimitError as e:
            logger.warning(f"OpenRouter rate limit exceeded: {e}")
            retry_after = getattr(e, "retry_after", None)
            raise RateLimitError(
                f"OpenRouter rate limit exceeded: {str(e)}", retry_after=retry_after
            )

        except openai.APITimeoutError as e:
            logger.error(f"OpenRouter request timed out: {e}")
            raise TimeoutError(f"OpenRouter request timed out: {str(e)}")

        except openai.APIError as e:
            logger.error(f"OpenRouter API error: {e}")
            raise APIError(f"OpenRouter API error: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected OpenRouter error: {e}")
            raise APIError(f"Unexpected error: {str(e)}")

    def validate_credentials(self) -> bool:
        """
        Validate OpenRouter API credentials.

        Makes a minimal API call to check if credentials are valid.

        Returns:
            True if credentials are valid

        Raises:
            AuthenticationError: If credentials are invalid
            APIError: For other API errors
        """
        try:
            # Make a minimal request to validate credentials
            test_messages: List[ChatCompletionMessageParam] = [
                {"role": "user", "content": "Hi"}
            ]

            extra_headers = {
                "HTTP-Referer": self.site_url or "https://github.com/whatsapp-ai",
                "X-Title": self.app_name,
            }

            self.client.chat.completions.create(
                model=self.model,
                messages=test_messages,
                max_tokens=1,
                extra_headers=extra_headers,
            )

            logger.info("OpenRouter credentials validated successfully")
            return True

        except openai.AuthenticationError as e:
            logger.error(f"OpenRouter credential validation failed: {e}")
            raise AuthenticationError(f"Invalid OpenRouter API key: {str(e)}")

        except Exception as e:
            logger.error(f"Error validating OpenRouter credentials: {e}")
            raise APIError(f"Error validating credentials: {str(e)}")
