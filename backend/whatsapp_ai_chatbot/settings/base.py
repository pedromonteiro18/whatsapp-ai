"""
Base Django settings for whatsapp_ai_chatbot project.
These settings are common across all environments.
"""

from pathlib import Path
from typing import cast

from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# settings/base.py is in backend/whatsapp_ai_chatbot/settings/, so:
# parent.parent.parent gives us backend/
# parent.parent.parent.parent gives us the project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config(
    "SECRET_KEY",
    default="django-insecure-(kewfu)ac&ih-+sv@gcgni0ei($)wlgq@zs61s8w!a3wyqy6-z",
)

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party apps
    "rest_framework",
    "corsheaders",
    "django_celery_beat",
    "django_celery_results",
    # Local apps
    "backend.chatbot_core",
    "backend.whatsapp",
    "backend.ai_integration",
    "backend.booking_system",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "backend.whatsapp_ai_chatbot.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.whatsapp_ai_chatbot.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME", default="whatsapp_chatbot"),
        "USER": config("DB_USER", default="postgres"),
        "PASSWORD": config("DB_PASSWORD", default="postgres"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files (User-uploaded content)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# REST Framework Configuration
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
}

# Celery Configuration
CELERY_BROKER_URL = config("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = config(
    "CELERY_RESULT_BACKEND", default="redis://localhost:6379/0"
)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# Redis Configuration
REDIS_HOST = config("REDIS_HOST", default="localhost")
REDIS_PORT = config("REDIS_PORT", default=6379, cast=int)
REDIS_DB = config("REDIS_DB", default=0, cast=int)

# Twilio Configuration
TWILIO_ACCOUNT_SID = config("TWILIO_ACCOUNT_SID", default="")
TWILIO_AUTH_TOKEN = config("TWILIO_AUTH_TOKEN", default="")
TWILIO_WHATSAPP_NUMBER = config("TWILIO_WHATSAPP_NUMBER", default="")

# OpenAI Configuration
OPENAI_API_KEY = config("OPENAI_API_KEY", default="")
OPENAI_MODEL = config("OPENAI_MODEL", default="gpt-4")
OPENAI_MAX_TOKENS = config("OPENAI_MAX_TOKENS", default=500, cast=int)
OPENAI_TEMPERATURE = config("OPENAI_TEMPERATURE", default=0.7, cast=float)

# Application Settings
MAX_CONVERSATION_HISTORY = config("MAX_CONVERSATION_HISTORY", default=10, cast=int)
SESSION_TIMEOUT_MINUTES = config("SESSION_TIMEOUT_MINUTES", default=30, cast=int)

# Booking System Settings
BOOKING_PENDING_TIMEOUT_MINUTES = config(
    "BOOKING_PENDING_TIMEOUT_MINUTES", default=30, cast=int
)
BOOKING_CANCELLATION_DEADLINE_HOURS = config(
    "BOOKING_CANCELLATION_DEADLINE_HOURS", default=24, cast=int
)
BOOKING_WEB_APP_URL = config("BOOKING_WEB_APP_URL")

# Rate Limiting Settings
RATE_LIMIT_ENABLED = config("RATE_LIMIT_ENABLED", default=True, cast=bool)
RATE_LIMIT_MAX_REQUESTS = config("RATE_LIMIT_MAX_REQUESTS", default=10, cast=int)
RATE_LIMIT_WINDOW_SECONDS = config("RATE_LIMIT_WINDOW_SECONDS", default=60, cast=int)

# Security Headers (applied in all environments)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"

# Session Security
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_NAME = "whatsapp_ai_sessionid"

# CSRF Security
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_NAME = "whatsapp_ai_csrftoken"
