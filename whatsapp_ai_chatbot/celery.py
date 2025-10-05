"""
Celery configuration for WhatsApp AI Chatbot.

This module configures Celery for asynchronous task processing,
including background jobs for message handling and AI processing.
"""

import os

from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "whatsapp_ai_chatbot.settings")

app = Celery("whatsapp_ai_chatbot")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Configure Celery Beat schedule for periodic tasks
app.conf.beat_schedule = {
    "cleanup-expired-conversations": {
        "task": "chatbot_core.tasks.cleanup_expired_conversations",
        "schedule": crontab(hour="*/6", minute="0"),  # Every 6 hours
        "options": {
            "expires": 3600,  # Task expires after 1 hour if not executed
        },
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
