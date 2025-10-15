"""
Error handling utilities for WhatsApp AI Chatbot.

Provides centralized error management including:
- Error categorization and logging
- User-friendly message generation
- Admin notifications for critical errors
"""

import logging
import traceback
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Categories of errors for different handling strategies."""

    WEBHOOK = "webhook"  # Errors from webhook processing
    AI = "ai"  # Errors from AI provider interactions
    DATABASE = "database"  # Database operation errors
    WHATSAPP = "whatsapp"  # WhatsApp/Twilio API errors
    SYSTEM = "system"  # General system errors
    CONFIGURATION = "configuration"  # Configuration or setup errors


class ErrorSeverity(Enum):
    """Severity levels for error handling and notifications."""

    LOW = "low"  # Non-critical, informational
    MEDIUM = "medium"  # Important but not urgent
    HIGH = "high"  # Requires attention
    CRITICAL = "critical"  # Requires immediate action


class ErrorHandler:
    """
    Centralized error handling utility.

    Provides methods for categorizing, logging, and notifying about errors
    with appropriate severity levels and user-friendly messages.
    """

    # User-friendly error messages by category
    USER_MESSAGES = {
        ErrorCategory.AI: (
            "I'm having trouble processing your request right now. "
            "Please try again in a moment."
        ),
        ErrorCategory.WHATSAPP: (
            "There was a problem sending the message. Please try again."
        ),
        ErrorCategory.DATABASE: ("A technical issue occurred. Please try again later."),
        ErrorCategory.SYSTEM: ("An unexpected error occurred. Please try again later."),
        ErrorCategory.CONFIGURATION: (
            "The service is temporarily unavailable. Please contact support."
        ),
        ErrorCategory.WEBHOOK: (
            "There was a problem receiving your message. Please try again."
        ),
    }

    @classmethod
    def handle_error(
        cls,
        error: Exception,
        category: ErrorCategory,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        user_phone: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Handle an error with appropriate logging and notifications.

        Args:
            error: The exception that occurred
            category: Error category for classification
            severity: Error severity level
            context: Additional context about the error
            user_phone: User's phone number if applicable

        Returns:
            Dict containing:
                - user_message: User-friendly error message
                - logged: Whether error was logged
                - notified: Whether admin was notified
        """
        # Build error context
        error_context = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "category": category.value,
            "severity": severity.value,
            "user_phone": user_phone,
        }
        if context:
            error_context.update(context)

        # Log the error
        cls._log_error(error, error_context, severity)

        # Notify admin for critical errors
        notified = False
        if severity == ErrorSeverity.CRITICAL:
            notified = cls.send_admin_alert(
                error=error,
                category=category,
                severity=severity,
                context=error_context,
            )

        # Get user-friendly message
        user_message = cls.get_user_message(category)

        return {
            "user_message": user_message,
            "logged": True,
            "notified": notified,
        }

    @classmethod
    def _log_error(
        cls,
        error: Exception,
        context: Dict[str, Any],
        severity: ErrorSeverity,
    ) -> None:
        """
        Log error with appropriate severity level.

        Args:
            error: The exception to log
            context: Error context information
            severity: Error severity level
        """
        # Format log message
        log_message = (
            f"[{context['category'].upper()}] {context['error_type']}: "
            f"{context['error_message']}"
        )

        # Add context details
        context_str = ", ".join(
            f"{k}={v}"
            for k, v in context.items()
            if k not in ["error_type", "error_message", "category"]
        )
        if context_str:
            log_message += f" | Context: {context_str}"

        # Log with appropriate level based on severity
        if severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message, exc_info=error, extra=context)
        elif severity == ErrorSeverity.HIGH:
            logger.error(log_message, exc_info=error, extra=context)
        elif severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message, exc_info=error, extra=context)
        else:  # LOW
            logger.info(log_message, extra=context)

    @classmethod
    def get_user_message(
        cls, category: ErrorCategory, custom_message: Optional[str] = None
    ) -> str:
        """
        Get user-friendly error message for a category.

        Args:
            category: Error category
            custom_message: Optional custom message to use instead

        Returns:
            User-friendly error message
        """
        if custom_message:
            return custom_message

        return cls.USER_MESSAGES.get(
            category,
            "An error occurred. Please try again later.",
        )

    @classmethod
    def send_admin_alert(
        cls,
        error: Exception,
        category: ErrorCategory,
        severity: ErrorSeverity,
        context: Dict[str, Any],
    ) -> bool:
        """
        Send alert to administrators about critical errors.

        Logs critical errors with full context and traceback to the logging
        system with rate limiting to prevent log spam.

        Args:
            error: The exception that occurred
            category: Error category
            severity: Error severity level
            context: Error context information

        Returns:
            True if alert was logged successfully
        """
        # Check rate limiting to prevent alert spam
        if not cls._should_send_alert(error, category):
            logger.debug(f"Skipping alert for {type(error).__name__} - rate limited")
            return False

        # Format alert message
        alert_title = f"[{severity.value.upper()}] {category.value.capitalize()} Error"
        alert_body = cls._format_alert_message(error, category, severity, context)

        # Log critical alert with full details
        logger.critical(
            f"ADMIN ALERT: {alert_title}\n{alert_body}",
            extra={
                "category": category.value,
                "severity": severity.value,
                "error_type": type(error).__name__,
                "context": context,
            },
        )

        return True

    @classmethod
    def _should_send_alert(cls, error: Exception, category: ErrorCategory) -> bool:
        """
        Check if alert should be sent based on rate limiting.

        Prevents alert fatigue by limiting similar alerts to once per hour.

        Args:
            error: The exception
            category: Error category

        Returns:
            True if alert should be sent
        """
        try:
            import redis

            from .config import Config

            # Create rate limit key based on error type and category
            rate_limit_key = f"alert_ratelimit:{category.value}:{type(error).__name__}"

            # Try to use Redis for distributed rate limiting
            try:
                redis_client = redis.Redis(
                    host=Config.REDIS_HOST,
                    port=Config.REDIS_PORT,
                    db=Config.REDIS_DB,
                    decode_responses=True,
                )

                # Check if we've sent this alert recently (within 1 hour)
                if redis_client.exists(rate_limit_key):
                    return False

                # Set rate limit key with 1 hour expiration
                redis_client.setex(rate_limit_key, 3600, "1")
                return True

            except Exception as redis_error:
                logger.warning(
                    f"Redis unavailable for rate limiting: {redis_error}. "
                    "Allowing alert."
                )
                return True  # Allow alert if Redis is down

        except Exception as e:
            logger.error(f"Error in rate limiting check: {e}")
            return True  # Allow alert on rate limit check failure

    @classmethod
    def _format_alert_message(
        cls,
        error: Exception,
        category: ErrorCategory,
        severity: ErrorSeverity,
        context: Dict[str, Any],
    ) -> str:
        """
        Format error information into readable alert message.

        Args:
            error: The exception
            category: Error category
            severity: Error severity level
            context: Error context

        Returns:
            Formatted alert message
        """
        lines = [
            f"Category: {category.value}",
            f"Severity: {severity.value.upper()}",
            f"Error Type: {type(error).__name__}",
            f"Error Message: {str(error)}",
            "",
            "Context:",
        ]

        # Add context information
        for key, value in context.items():
            if key != "traceback":  # Handle traceback separately
                lines.append(f"  {key}: {value}")

        # Add traceback
        lines.append("")
        lines.append("Traceback:")
        lines.append(traceback.format_exc())

        return "\n".join(lines)

    @classmethod
    def log_webhook_error(
        cls,
        error: Exception,
        request_data: Dict[str, Any],
        user_phone: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Handle webhook processing errors.

        Args:
            error: The exception that occurred
            request_data: Webhook request data
            user_phone: User's phone number if available

        Returns:
            Error handling result dict
        """
        return cls.handle_error(
            error=error,
            category=ErrorCategory.WEBHOOK,
            severity=ErrorSeverity.HIGH,
            context={"request_data": request_data},
            user_phone=user_phone,
        )

    @classmethod
    def log_ai_error(
        cls,
        error: Exception,
        user_phone: str,
        message_content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Handle AI processing errors.

        Args:
            error: The exception that occurred
            user_phone: User's phone number
            message_content: User's message content if available

        Returns:
            Error handling result dict
        """
        # Determine severity based on error type
        from backend.ai_integration.adapters.base import AuthenticationError

        severity = (
            ErrorSeverity.CRITICAL
            if isinstance(error, AuthenticationError)
            else ErrorSeverity.HIGH
        )

        return cls.handle_error(
            error=error,
            category=ErrorCategory.AI,
            severity=severity,
            context={
                "message_content": message_content[:100] if message_content else None
            },
            user_phone=user_phone,
        )

    @classmethod
    def log_database_error(
        cls,
        error: Exception,
        operation: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Handle database operation errors.

        Args:
            error: The exception that occurred
            operation: Database operation that failed
            context: Additional context

        Returns:
            Error handling result dict
        """
        error_context = {"operation": operation}
        if context:
            error_context.update(context)

        return cls.handle_error(
            error=error,
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            context=error_context,
        )

    @classmethod
    def log_system_error(
        cls,
        error: Exception,
        component: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Handle general system errors.

        Args:
            error: The exception that occurred
            component: System component where error occurred
            context: Additional context

        Returns:
            Error handling result dict
        """
        error_context = {"component": component}
        if context:
            error_context.update(context)

        return cls.handle_error(
            error=error,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.MEDIUM,
            context=error_context,
        )
