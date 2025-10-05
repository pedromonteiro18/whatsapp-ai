"""
Django admin configuration for chatbot_core models.
"""

from django.contrib import admin

from .models import AIConfiguration, Conversation, Message, WebhookLog


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = [
        "user_phone",
        "started_at",
        "last_activity",
        "is_active",
        "message_count",
    ]
    list_filter = ["is_active", "started_at", "last_activity"]
    search_fields = ["user_phone"]
    readonly_fields = ["id", "started_at", "last_activity"]
    date_hierarchy = "started_at"

    def message_count(self, obj):
        return obj.get_message_count()

    message_count.short_description = "Messages"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["conversation", "role", "content_preview", "timestamp"]
    list_filter = ["role", "timestamp"]
    search_fields = ["content", "conversation__user_phone"]
    readonly_fields = ["id", "timestamp"]
    date_hierarchy = "timestamp"

    def content_preview(self, obj):
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content

    content_preview.short_description = "Content"


@admin.register(AIConfiguration)
class AIConfigurationAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "provider",
        "model_name",
        "max_tokens",
        "temperature",
        "is_active",
    ]
    list_filter = ["provider", "is_active"]
    search_fields = ["name", "model_name"]
    readonly_fields = ["id", "created_at", "updated_at"]

    def get_readonly_fields(self, request, obj=None):
        """Make api_key read-only after creation for security."""
        if obj:  # Editing an existing object
            return self.readonly_fields + ["api_key"]
        return self.readonly_fields


@admin.register(WebhookLog)
class WebhookLogAdmin(admin.ModelAdmin):
    list_display = [
        "timestamp",
        "method",
        "path",
        "status",
        "response_status",
        "processing_time_ms",
    ]
    list_filter = ["status", "method", "timestamp"]
    search_fields = ["path", "error_message"]
    readonly_fields = [
        "id",
        "timestamp",
        "method",
        "path",
        "headers",
        "body",
        "response_status",
        "processing_time_ms",
        "status",
        "error_message",
        "conversation",
    ]
    date_hierarchy = "timestamp"

    def has_add_permission(self, request):
        """Webhook logs should only be created by the system."""
        return False

    def has_change_permission(self, request, obj=None):
        """Webhook logs should be read-only."""
        return False
