"""
Configuration management system for the WhatsApp AI Chatbot.

This module provides centralized configuration management with validation
and type-safe access to all application settings.
"""

import logging

from decouple import config
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


class Config:
    """
    Centralized configuration manager that loads and validates
    all application settings from environment variables.
    """

    # WhatsApp/Twilio Settings
    TWILIO_ACCOUNT_SID: str = config("TWILIO_ACCOUNT_SID", default="")
    TWILIO_AUTH_TOKEN: str = config("TWILIO_AUTH_TOKEN", default="")
    TWILIO_WHATSAPP_NUMBER: str = config("TWILIO_WHATSAPP_NUMBER", default="")

    # AI Provider Settings
    # OpenRouter provides unified access to multiple AI providers
    OPENROUTER_API_KEY: str = config("OPENROUTER_API_KEY", default="")
    AI_MODEL: str = config(
        "AI_MODEL", default="openai/gpt-4"
    )  # Format: provider/model-name
    AI_MAX_TOKENS: int = config("AI_MAX_TOKENS", default=500, cast=int)
    AI_TEMPERATURE: float = config("AI_TEMPERATURE", default=0.7, cast=float)

    # Legacy OpenAI settings (for backward compatibility)
    OPENAI_API_KEY: str = config("OPENAI_API_KEY", default="")
    OPENAI_MODEL: str = config("OPENAI_MODEL", default="gpt-4")
    OPENAI_MAX_TOKENS: int = config("OPENAI_MAX_TOKENS", default=500, cast=int)
    OPENAI_TEMPERATURE: float = config("OPENAI_TEMPERATURE", default=0.7, cast=float)

    # Application Settings
    MAX_CONVERSATION_HISTORY: int = config(
        "MAX_CONVERSATION_HISTORY", default=10, cast=int
    )
    SESSION_TIMEOUT_MINUTES: int = config(
        "SESSION_TIMEOUT_MINUTES", default=30, cast=int
    )
    CONVERSATION_TTL_SECONDS: int = SESSION_TIMEOUT_MINUTES * 60

    # Redis Settings
    REDIS_HOST: str = config("REDIS_HOST", default="localhost")
    REDIS_PORT: int = config("REDIS_PORT", default=6379, cast=int)
    REDIS_DB: int = config("REDIS_DB", default=0, cast=int)

    # Rate Limiting
    RATE_LIMIT_MESSAGES_PER_MINUTE: int = config(
        "RATE_LIMIT_MESSAGES_PER_MINUTE", default=10, cast=int
    )

    @classmethod
    def validate(cls) -> tuple[bool, list[str]]:
        """
        Validate that all required configuration settings are present and valid.

        Returns:
            tuple: (is_valid, list of error messages)
        """
        errors = []

        # Validate Twilio settings
        if not cls.TWILIO_ACCOUNT_SID:
            errors.append("TWILIO_ACCOUNT_SID is required")
        if not cls.TWILIO_AUTH_TOKEN:
            errors.append("TWILIO_AUTH_TOKEN is required")
        if not cls.TWILIO_WHATSAPP_NUMBER:
            errors.append("TWILIO_WHATSAPP_NUMBER is required")
        elif not cls.TWILIO_WHATSAPP_NUMBER.startswith("whatsapp:"):
            errors.append(
                "TWILIO_WHATSAPP_NUMBER must start with 'whatsapp:' "
                "(e.g., whatsapp:+14155238886)"
            )

        # Validate AI provider settings
        # Try OpenRouter first, fall back to legacy OpenAI
        if not cls.OPENROUTER_API_KEY and not cls.OPENAI_API_KEY:
            errors.append(
                "Either OPENROUTER_API_KEY or OPENAI_API_KEY is required for AI integration"
            )

        if not cls.AI_MODEL and not cls.OPENAI_MODEL:
            errors.append("Either AI_MODEL or OPENAI_MODEL must be specified")

        # Validate numeric settings
        max_tokens = cls.AI_MAX_TOKENS or cls.OPENAI_MAX_TOKENS
        if max_tokens <= 0:
            errors.append("AI_MAX_TOKENS (or OPENAI_MAX_TOKENS) must be greater than 0")

        temperature = cls.AI_TEMPERATURE or cls.OPENAI_TEMPERATURE
        if not 0 <= temperature <= 2:
            errors.append(
                "AI_TEMPERATURE (or OPENAI_TEMPERATURE) must be between 0 and 2"
            )

        if cls.MAX_CONVERSATION_HISTORY <= 0:
            errors.append("MAX_CONVERSATION_HISTORY must be greater than 0")

        if cls.SESSION_TIMEOUT_MINUTES <= 0:
            errors.append("SESSION_TIMEOUT_MINUTES must be greater than 0")

        if cls.RATE_LIMIT_MESSAGES_PER_MINUTE <= 0:
            errors.append("RATE_LIMIT_MESSAGES_PER_MINUTE must be greater than 0")

        return (len(errors) == 0, errors)

    @classmethod
    def validate_required(cls) -> None:
        """
        Validate required settings and raise ImproperlyConfigured if any are missing.

        Raises:
            ImproperlyConfigured: If any required settings are missing or invalid
        """
        is_valid, errors = cls.validate()
        if not is_valid:
            error_message = "Configuration validation failed:\n" + "\n".join(
                f"  - {error}" for error in errors
            )
            logger.error("Configuration validation failed: %s", errors)
            raise ImproperlyConfigured(error_message)

        logger.info("Configuration validation passed successfully")

    @classmethod
    def get_ai_api_key(cls) -> str:
        """
        Get the AI API key.

        Prioritizes OpenRouter, falls back to legacy OpenAI key.

        Returns:
            str: The API key

        Raises:
            ImproperlyConfigured: If no API key is configured
        """
        # Try OpenRouter first
        if cls.OPENROUTER_API_KEY:
            return cls.OPENROUTER_API_KEY

        # Fall back to legacy OpenAI
        if cls.OPENAI_API_KEY:
            logger.warning(
                "Using legacy OPENAI_API_KEY. Consider migrating to OPENROUTER_API_KEY"
            )
            return cls.OPENAI_API_KEY

        raise ImproperlyConfigured(
            "No AI API key configured. Set OPENROUTER_API_KEY or OPENAI_API_KEY"
        )

    @classmethod
    def get_ai_model(cls) -> str:
        """
        Get the AI model name.

        Prioritizes AI_MODEL (OpenRouter format), falls back to legacy OPENAI_MODEL.

        Returns:
            str: The model name (e.g., 'openai/gpt-4', 'anthropic/claude-3-sonnet')
        """
        # Try new AI_MODEL first
        if cls.AI_MODEL:
            return cls.AI_MODEL

        # Fall back to legacy OPENAI_MODEL
        if cls.OPENAI_MODEL:
            logger.warning(
                "Using legacy OPENAI_MODEL. Consider migrating to AI_MODEL with provider prefix"
            )
            # Add openai/ prefix if not present
            model = cls.OPENAI_MODEL
            if "/" not in model:
                model = f"openai/{model}"
            return model

        return "openai/gpt-4"  # Ultimate fallback

    @classmethod
    def get_redis_url(cls) -> str:
        """
        Get the Redis connection URL.

        Returns:
            str: Redis URL in format redis://host:port/db
        """
        return f"redis://{cls.REDIS_HOST}:{cls.REDIS_PORT}/{cls.REDIS_DB}"
