"""
Beta/Staging environment settings for whatsapp_ai_chatbot project.
Use for testing and QA before production deployment.
"""

from typing import cast

from decouple import config

from .base import *  # noqa: F403

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Allowed hosts - must be explicitly configured
ALLOWED_HOSTS = cast(
    str,
    config(
        "ALLOWED_HOSTS",
        default="beta.yourdomain.com",
    ),
).split(",")

# CORS Settings - must be explicitly configured
CORS_ALLOWED_ORIGINS = cast(
    str,
    config(
        "CORS_ALLOWED_ORIGINS",
        default="https://beta.yourdomain.com",
    ),
).split(",")
CORS_ALLOW_CREDENTIALS = True

# HTTPS/SSL Settings
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# HTTP Strict Transport Security (HSTS) - moderate settings for beta
SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=3600, cast=int)  # 1 hour
SECURE_HSTS_INCLUDE_SUBDOMAINS = False  # Don't include subdomains in beta
SECURE_HSTS_PRELOAD = False  # Don't preload in beta

# Logging Configuration for Beta
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {asctime} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "whatsapp_chatbot.log",  # noqa: F405
            "maxBytes": 1024 * 1024 * 10,  # 10 MB
            "backupCount": 5,
            "formatter": "verbose",
        },
        "error_file": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "errors.log",  # noqa: F405
            "maxBytes": 1024 * 1024 * 10,  # 10 MB
            "backupCount": 5,
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "backend.chatbot_core": {
            "handlers": ["console", "file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        "backend.whatsapp": {
            "handlers": ["console", "file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        "backend.ai_integration": {
            "handlers": ["console", "file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        "celery": {
            "handlers": ["console", "file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        "backend.booking_system": {
            "handlers": ["console", "file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
}
