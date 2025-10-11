"""Django admin configuration for booking system."""

from django.contrib import admin
from django.utils.html import format_html

from .models import Activity, ActivityImage, Booking, TimeSlot, UserPreference


class ActivityImageInline(admin.TabularInline):
    """Inline admin for activity images."""

    model = ActivityImage
    extra = 1
    fields = ("image", "alt_text", "is_primary", "order")
    ordering = ("order",)


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    """Admin interface for Activity model."""

    list_display = (
        "name",
        "category",
        "price_display",
        "duration_display",
        "capacity_per_slot",
        "is_active",
        "created_at",
    )
    list_filter = ("category", "is_active", "created_at")
    search_fields = ("name", "description", "location")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("id", "created_at", "updated_at")
    inlines = [ActivityImageInline]

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "id",
                    "name",
                    "slug",
                    "description",
                    "category",
                    "is_active",
                )
            },
        ),
        (
            "Pricing & Duration",
            {"fields": ("price", "currency", "duration_minutes")},
        ),
        (
            "Capacity & Location",
            {"fields": ("capacity_per_slot", "location", "requirements")},
        ),
        (
            "Metadata",
            {
                "fields": ("metadata", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def price_display(self, obj):
        """Display formatted price."""
        return f"{obj.currency} {obj.price}"

    price_display.short_description = "Price"

    def duration_display(self, obj):
        """Display formatted duration."""
        hours = obj.duration_minutes // 60
        minutes = obj.duration_minutes % 60
        if hours > 0:
            return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
        return f"{minutes}m"

    duration_display.short_description = "Duration"


@admin.register(ActivityImage)
class ActivityImageAdmin(admin.ModelAdmin):
    """Admin interface for ActivityImage model."""

    list_display = ("activity", "alt_text", "is_primary", "order", "image_preview")
    list_filter = ("is_primary", "activity")
    search_fields = ("activity__name", "alt_text")
    ordering = ("activity", "order")

    def image_preview(self, obj):
        """Display image thumbnail."""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 100px;" />',
                obj.image.url,
            )
        return "-"

    image_preview.short_description = "Preview"


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    """Admin interface for TimeSlot model."""

    list_display = (
        "activity",
        "start_time",
        "end_time",
        "capacity",
        "booked_count",
        "availability_status",
        "is_available",
    )
    list_filter = ("activity", "is_available", "start_time")
    search_fields = ("activity__name",)
    readonly_fields = ("id", "booked_count", "created_at")
    date_hierarchy = "start_time"

    fieldsets = (
        (
            "Time Slot Information",
            {"fields": ("id", "activity", "start_time", "end_time")},
        ),
        (
            "Capacity",
            {"fields": ("capacity", "booked_count", "is_available")},
        ),
        ("Metadata", {"fields": ("created_at",), "classes": ("collapse",)}),
    )

    def availability_status(self, obj):
        """Display availability status with color."""
        available = obj.capacity - obj.booked_count
        if available <= 0:
            color = "red"
            status = "Full"
        elif available <= obj.capacity * 0.2:
            color = "orange"
            status = f"{available} left"
        else:
            color = "green"
            status = f"{available} available"

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>', color, status
        )

    availability_status.short_description = "Availability"


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """Admin interface for Booking model."""

    list_display = (
        "id",
        "user_phone",
        "activity",
        "time_slot",
        "status_display",
        "participants",
        "total_price",
        "booking_source",
        "created_at",
    )
    list_filter = ("status", "booking_source", "created_at", "activity")
    search_fields = ("user_phone", "activity__name", "id")
    readonly_fields = (
        "id",
        "created_at",
        "confirmed_at",
        "cancelled_at",
        "expires_at",
    )
    date_hierarchy = "created_at"
    actions = ["confirm_bookings", "cancel_bookings"]

    fieldsets = (
        (
            "Booking Information",
            {
                "fields": (
                    "id",
                    "user_phone",
                    "activity",
                    "time_slot",
                    "status",
                )
            },
        ),
        (
            "Details",
            {
                "fields": (
                    "participants",
                    "special_requests",
                    "total_price",
                    "booking_source",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "confirmed_at",
                    "cancelled_at",
                    "expires_at",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {"fields": ("metadata",), "classes": ("collapse",)},
        ),
    )

    def status_display(self, obj):
        """Display status with color coding."""
        colors = {
            "pending": "orange",
            "confirmed": "green",
            "cancelled": "red",
            "completed": "blue",
            "no_show": "gray",
        }
        color = colors.get(obj.status, "black")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_display.short_description = "Status"

    @admin.action(description="Confirm selected bookings")
    def confirm_bookings(self, request, queryset):
        """Admin action to confirm multiple bookings."""
        updated = 0
        for booking in queryset.filter(status="pending"):
            booking.status = "confirmed"
            booking.save()
            updated += 1

        self.message_user(request, f"Successfully confirmed {updated} booking(s).")

    @admin.action(description="Cancel selected bookings")
    def cancel_bookings(self, request, queryset):
        """Admin action to cancel multiple bookings."""
        updated = 0
        for booking in queryset.exclude(status__in=["cancelled", "completed"]):
            booking.status = "cancelled"
            booking.save()
            updated += 1

        self.message_user(request, f"Successfully cancelled {updated} booking(s).")


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    """Admin interface for UserPreference model."""

    list_display = ("user_phone", "categories_display", "last_updated")
    search_fields = ("user_phone", "interests")
    readonly_fields = ("id", "last_updated")

    fieldsets = (
        (
            "User Information",
            {"fields": ("id", "user_phone")},
        ),
        (
            "Preferences",
            {
                "fields": (
                    "preferred_categories",
                    "preferred_times",
                    "budget_range",
                    "interests",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": ("metadata", "last_updated"),
                "classes": ("collapse",),
            },
        ),
    )

    def categories_display(self, obj):
        """Display preferred categories as comma-separated list."""
        if obj.preferred_categories:
            return ", ".join(obj.preferred_categories)
        return "-"

    categories_display.short_description = "Preferred Categories"
