"""
AI Adapter Factory for creating AI provider adapters.

Provides a factory pattern for instantiating the correct AI adapter
based on configuration.
"""

import logging
from typing import Any, Dict, Optional

from django.core.exceptions import ImproperlyConfigured

from backend.chatbot_core.config import Config
from backend.chatbot_core.models import AIConfiguration

from .adapters.base import BaseAIAdapter
from .adapters.openrouter_adapter import OpenRouterAdapter

logger = logging.getLogger(__name__)


class AIAdapterFactory:
    """
    Factory class for creating AI adapter instances.

    Supports loading configuration from environment variables or database.
    """

    @staticmethod
    def create_adapter(
        config_source: str = "env",
        config_name: Optional[str] = None,
        **override_params,
    ) -> BaseAIAdapter:
        """
        Create an AI adapter instance based on configuration.

        Args:
            config_source: Configuration source ('env' or 'db')
                - 'env': Load from environment variables via Config class
                - 'db': Load from AIConfiguration model in database
            config_name: Name of configuration to load from database
                        (required if config_source='db')
            **override_params: Parameters to override from configuration
                             (e.g., max_tokens, temperature)

        Returns:
            BaseAIAdapter instance (currently OpenRouterAdapter)

        Raises:
            ImproperlyConfigured: If configuration is invalid or missing
            ValueError: If config_source is invalid

        Examples:
            # Load from environment variables
            adapter = AIAdapterFactory.create_adapter()

            # Load from database
            adapter = AIAdapterFactory.create_adapter(
                config_source='db',
                config_name='production'
            )

            # Override default parameters
            adapter = AIAdapterFactory.create_adapter(
                max_tokens=1000,
                temperature=0.8
            )
        """
        if config_source == "env":
            return AIAdapterFactory._create_from_env(**override_params)
        elif config_source == "db":
            if not config_name:
                raise ValueError("config_name is required when config_source='db'")
            return AIAdapterFactory._create_from_db(config_name, **override_params)
        else:
            raise ValueError(
                f"Invalid config_source: {config_source}. Must be 'env' or 'db'"
            )

    @staticmethod
    def _create_from_env(**override_params) -> BaseAIAdapter:
        """
        Create adapter from environment variables.

        Args:
            **override_params: Parameters to override from Config

        Returns:
            BaseAIAdapter instance

        Raises:
            ImproperlyConfigured: If required environment variables are missing
        """
        try:
            # Get API key - try OpenRouter first, fall back to OpenAI
            api_key = Config.get_ai_api_key()

            # Get model name
            model = Config.get_ai_model()

            # Get other parameters with defaults
            params: Dict[str, Any] = {
                "api_key": api_key,
                "model": model,
                "max_tokens": Config.OPENAI_MAX_TOKENS,
                "temperature": Config.OPENAI_TEMPERATURE,
                "timeout": 30,
                "max_retries": 3,
            }

            # Override with any provided parameters
            params.update(override_params)

            logger.info(
                f"Creating OpenRouter adapter from environment: model={params['model']}"
            )

            return OpenRouterAdapter(**params)

        except ImproperlyConfigured as e:
            logger.error(f"Failed to create adapter from environment: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating adapter from environment: {e}")
            raise ImproperlyConfigured(
                f"Failed to create AI adapter from environment: {str(e)}"
            )

    @staticmethod
    def _create_from_db(config_name: str, **override_params) -> BaseAIAdapter:
        """
        Create adapter from database configuration.

        Args:
            config_name: Name of the AIConfiguration to use
            **override_params: Parameters to override from database config

        Returns:
            BaseAIAdapter instance

        Raises:
            ImproperlyConfigured: If configuration not found or invalid
        """
        try:
            # Get active configuration from database
            config = AIConfiguration.objects.filter(
                name=config_name, is_active=True
            ).first()

            if not config:
                raise ImproperlyConfigured(
                    f"AI configuration '{config_name}' not found or not active"
                )

            # Prepare parameters from database config
            params: Dict[str, Any] = {
                "api_key": config.api_key,
                "model": config.model_name,
                "max_tokens": config.max_tokens,
                "temperature": config.temperature,
                "timeout": 30,
                "max_retries": 3,
            }

            # Add any provider-specific settings from metadata
            if config.metadata:
                params.update(config.metadata)

            # Override with any provided parameters
            params.update(override_params)

            logger.info(
                f"Creating OpenRouter adapter from database: "
                f"config={config_name}, model={params['model']}"
            )

            return OpenRouterAdapter(**params)

        except AIConfiguration.DoesNotExist:
            error_msg = f"AI configuration '{config_name}' not found"
            logger.error(error_msg)
            raise ImproperlyConfigured(error_msg)
        except Exception as e:
            logger.error(f"Unexpected error creating adapter from database: {e}")
            raise ImproperlyConfigured(
                f"Failed to create AI adapter from database: {str(e)}"
            )

    @staticmethod
    def validate_adapter(adapter: BaseAIAdapter) -> bool:
        """
        Validate that an adapter is properly configured.

        Args:
            adapter: The adapter instance to validate

        Returns:
            True if adapter is valid and credentials work

        Raises:
            AuthenticationError: If credentials are invalid
            APIError: For other validation errors
        """
        logger.info(f"Validating adapter: {adapter}")
        return adapter.validate_credentials()
