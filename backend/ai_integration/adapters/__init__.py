"""
AI Adapters package.

Provides adapter implementations for various AI providers through
a unified interface.
"""

from .base import (
    AIError,
    APIError,
    AuthenticationError,
    BaseAIAdapter,
    RateLimitError,
    TimeoutError,
)
from .openrouter_adapter import OpenRouterAdapter

__all__ = [
    # Base classes and exceptions
    "BaseAIAdapter",
    "AIError",
    "AuthenticationError",
    "RateLimitError",
    "TimeoutError",
    "APIError",
    # Adapters
    "OpenRouterAdapter",
]
