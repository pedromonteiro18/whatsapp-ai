"""
Celery configuration for WhatsApp AI Chatbot.

This module configures Celery for asynchronous task processing,
including background jobs for message handling and AI processing.
"""

import os

from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "backend.whatsapp_ai_chatbot.settings.development"
)

app = Celery("whatsapp_ai_chatbot")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Configure Celery Beat schedule for periodic tasks
app.conf.beat_schedule = {
    "cleanup-expired-conversations": {
        "task": "backend.chatbot_core.tasks.cleanup_expired_conversations",
        "schedule": crontab(hour="*/6", minute="0"),  # Every 6 hours
        "options": {
            "expires": 3600,  # Task expires after 1 hour if not executed
        },
    },
    "expire-pending-bookings": {
        "task": "backend.booking_system.tasks.expire_pending_bookings",
        "schedule": 300.0,  # Every 5 minutes (in seconds)
        "options": {
            "expires": 240,  # Task expires after 4 minutes if not executed
        },
    },
    "send-reminder-24h": {
        "task": "backend.booking_system.tasks.send_reminder_24h",
        "schedule": crontab(minute="0"),  # Every hour at minute 0
        "options": {
            "expires": 3000,  # Task expires after 50 minutes if not executed
        },
    },
    "send-reminder-1h": {
        "task": "backend.booking_system.tasks.send_reminder_1h",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
        "options": {
            "expires": 840,  # Task expires after 14 minutes if not executed
        },
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
