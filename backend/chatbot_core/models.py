"""
Database models for the WhatsApp AI Chatbot.

This module contains the core data models for managing conversations,
messages, AI configuration, and webhook logs.
"""

import uuid
from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    from django.db.models import Manager


class Conversation(models.Model):
    """
    Represents a conversation session with a WhatsApp user.

    Tracks conversation state and provides a container for messages.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_phone = models.CharField(
        max_length=50,
        db_index=True,
        help_text="User's phone number in WhatsApp format (e.g., whatsapp:+14155238886)",
    )
    started_at = models.DateTimeField(auto_now_add=True, db_index=True)
    last_activity = models.DateTimeField(auto_now=True, db_index=True)
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this conversation is currently active",
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata about the conversation",
    )

    if TYPE_CHECKING:
        # Type hints for reverse relations
        messages: "Manager[Message]"
        webhook_logs: "Manager[WebhookLog]"

    class Meta:
        ordering = ["-last_activity"]
        indexes = [
            models.Index(fields=["user_phone", "-last_activity"]),
            models.Index(fields=["is_active", "-last_activity"]),
        ]
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"

    def __str__(self):
        return f"Conversation with {self.user_phone} (started {self.started_at})"

    def get_message_count(self):
        """Get the total number of messages in this conversation."""
        return self.messages.count()

    def get_recent_messages(self, limit=10):
        """Get the most recent messages in this conversation."""
        return self.messages.order_by("-timestamp")[:limit]

    def mark_inactive(self):
        """Mark this conversation as inactive."""
        self.is_active = False
        self.save(update_fields=["is_active"])


class Message(models.Model):
    """
    Represents a single message in a conversation.

    Can be from either the user or the AI assistant.
    """

    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant"),
        ("system", "System"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
        help_text="The conversation this message belongs to",
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        help_text="Who sent this message",
    )
    content = models.TextField(help_text="The message content")
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata (tokens used, model version, etc.)",
    )

    class Meta:
        ordering = ["timestamp"]
        indexes = [
            models.Index(fields=["conversation", "timestamp"]),
            models.Index(fields=["role", "timestamp"]),
        ]
        verbose_name = "Message"
        verbose_name_plural = "Messages"

    def __str__(self) -> str:
        content: str = str(self.content)
        content_preview = content[:50] + "..." if len(content) > 50 else content
        return f"{self.role}: {content_preview}"


class AIConfiguration(models.Model):
    """
    Stores AI provider configuration settings.

    Supports multiple AI providers with encrypted API keys.
    """

    PROVIDER_CHOICES = [
        ("openai", "OpenAI"),
        ("anthropic", "Anthropic"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique name for this configuration",
    )
    provider = models.CharField(
        max_length=20,
        choices=PROVIDER_CHOICES,
        help_text="AI provider (OpenAI, Anthropic, etc.)",
    )
    api_key = models.CharField(
        max_length=255,
        help_text="API key for the provider (stored encrypted in production)",
    )
    model_name = models.CharField(
        max_length=100,
        help_text="Model name (e.g., gpt-4, claude-3-sonnet)",
    )
    max_tokens = models.IntegerField(
        default=500,
        help_text="Maximum tokens for responses",
    )
    temperature = models.FloatField(
        default=0.7,
        help_text="Temperature for response generation (0.0-2.0)",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this configuration is currently active",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional provider-specific settings",
    )

    class Meta:
        ordering = ["-is_active", "name"]
        verbose_name = "AI Configuration"
        verbose_name_plural = "AI Configurations"

    def __str__(self):
        return f"{self.name} ({self.provider} - {self.model_name})"


class WebhookLog(models.Model):
    """
    Logs all incoming webhook requests for audit and debugging.

    Stores request details, processing time, and any errors.
    """

    STATUS_CHOICES = [
        ("success", "Success"),
        ("error", "Error"),
        ("pending", "Pending"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    method = models.CharField(max_length=10, help_text="HTTP method (GET, POST)")
    path = models.CharField(max_length=255, help_text="Request path")
    headers = models.JSONField(
        default=dict,
        help_text="Request headers",
    )
    body = models.TextField(
        blank=True,
        help_text="Request body",
    )
    response_status = models.IntegerField(
        null=True,
        blank=True,
        help_text="HTTP response status code",
    )
    processing_time_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="Time taken to process the request in milliseconds",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        db_index=True,
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error message if processing failed",
    )
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="webhook_logs",
        help_text="Associated conversation if applicable",
    )

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["-timestamp"]),
            models.Index(fields=["status", "-timestamp"]),
        ]
        verbose_name = "Webhook Log"
        verbose_name_plural = "Webhook Logs"

    def __str__(self):
        return f"{self.method} {self.path} - {self.status} ({self.timestamp})"
