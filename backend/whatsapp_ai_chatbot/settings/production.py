"""
Production environment settings for whatsapp_ai_chatbot project.
Use for live production deployment with strict security settings.
"""

from typing import cast

from decouple import config

from .base import *  # noqa: F403

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Allowed hosts - must be explicitly configured
# CRITICAL: Never use wildcards in production
ALLOWED_HOSTS = cast(
    str,
    config("ALLOWED_HOSTS"),  # No default - must be set explicitly
).split(",")

# CORS Settings - must be explicitly configured
# CRITICAL: Only include your actual frontend domain
CORS_ALLOWED_ORIGINS = cast(
    str,
    config("CORS_ALLOWED_ORIGINS"),  # No default - must be set explicitly
).split(",")
CORS_ALLOW_CREDENTIALS = True

# HTTPS/SSL Settings
# CRITICAL: Enforce HTTPS in production
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# HTTP Strict Transport Security (HSTS)
# CRITICAL: Enable HSTS for production
SECURE_HSTS_SECONDS = config(
    "SECURE_HSTS_SECONDS", default=31536000, cast=int
)  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Additional Security Settings for Production
# Require HTTPS for session cookies
SESSION_COOKIE_AGE = 3600  # 1 hour session timeout

# CRITICAL: Database connection pooling for production
DATABASES["default"]["CONN_MAX_AGE"] = config(  # noqa: F405
    "DB_CONN_MAX_AGE", default=600, cast=int
)  # 10 minutes

# Logging Configuration for Production
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
            "level": "WARNING",  # Only warnings and errors to console in production
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
        "level": "WARNING",  # Only warnings and above for root logger in production
    },
}

# CRITICAL: Ensure these development-only features are disabled in production
# These should never be present in production code
# (removed via environment configuration or code removal)
assert not config(
    "DEV_OTP_CODE", default=None
), "DEV_OTP_CODE must not be set in production"
assert not config(
    "SKIP_WEBHOOK_SIGNATURE_VERIFICATION", default=False, cast=bool
), "SKIP_WEBHOOK_SIGNATURE_VERIFICATION must be False in production"
