"""
Configuration management system for the WhatsApp AI Chatbot.

This module provides centralized configuration management with validation
and type-safe access to all application settings.
"""

from typing import Optional
from decouple import config
from django.core.exceptions import ImproperlyConfigured


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
    AI_PROVIDER: str = config("AI_PROVIDER", default="openai")
    OPENAI_API_KEY: str = config("OPENAI_API_KEY", default="")
    OPENAI_MODEL: str = config("OPENAI_MODEL", default="gpt-4")
    OPENAI_MAX_TOKENS: int = config("OPENAI_MAX_TOKENS", default=500, cast=int)
    OPENAI_TEMPERATURE: float = config("OPENAI_TEMPERATURE", default=0.7, cast=float)

    # Anthropic Settings (for future use)
    ANTHROPIC_API_KEY: str = config("ANTHROPIC_API_KEY", default="")
    ANTHROPIC_MODEL: str = config("ANTHROPIC_MODEL", default="claude-3-sonnet-20240229")

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
                "TWILIO_WHATSAPP_NUMBER must start with 'whatsapp:' (e.g., whatsapp:+14155238886)"
            )

        # Validate AI provider settings
        if cls.AI_PROVIDER not in ["openai", "anthropic"]:
            errors.append(
                f"AI_PROVIDER must be 'openai' or 'anthropic', got '{cls.AI_PROVIDER}'"
            )

        if cls.AI_PROVIDER == "openai" and not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required when using OpenAI provider")

        if cls.AI_PROVIDER == "anthropic" and not cls.ANTHROPIC_API_KEY:
            errors.append("ANTHROPIC_API_KEY is required when using Anthropic provider")

        # Validate numeric settings
        if cls.OPENAI_MAX_TOKENS <= 0:
            errors.append("OPENAI_MAX_TOKENS must be greater than 0")

        if not 0 <= cls.OPENAI_TEMPERATURE <= 2:
            errors.append("OPENAI_TEMPERATURE must be between 0 and 2")

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
            raise ImproperlyConfigured(error_message)

    @classmethod
    def get_ai_api_key(cls) -> str:
        """
        Get the API key for the currently configured AI provider.

        Returns:
            str: The API key for the active provider

        Raises:
            ImproperlyConfigured: If the API key is not set
        """
        if cls.AI_PROVIDER == "openai":
            if not cls.OPENAI_API_KEY:
                raise ImproperlyConfigured("OPENAI_API_KEY is not configured")
            return cls.OPENAI_API_KEY
        elif cls.AI_PROVIDER == "anthropic":
            if not cls.ANTHROPIC_API_KEY:
                raise ImproperlyConfigured("ANTHROPIC_API_KEY is not configured")
            return cls.ANTHROPIC_API_KEY
        else:
            raise ImproperlyConfigured(f"Unknown AI provider: {cls.AI_PROVIDER}")

    @classmethod
    def get_ai_model(cls) -> str:
        """
        Get the model name for the currently configured AI provider.

        Returns:
            str: The model name for the active provider
        """
        if cls.AI_PROVIDER == "openai":
            return cls.OPENAI_MODEL
        elif cls.AI_PROVIDER == "anthropic":
            return cls.ANTHROPIC_MODEL
        else:
            return "unknown"

    @classmethod
    def get_redis_url(cls) -> str:
        """
        Get the Redis connection URL.

        Returns:
            str: Redis URL in format redis://host:port/db
        """
        return f"redis://{cls.REDIS_HOST}:{cls.REDIS_PORT}/{cls.REDIS_DB}"
