"""Models for the booking system."""

import uuid

from django.db import models


class Activity(models.Model):
    """Resort activity offering."""

    CATEGORY_CHOICES = [
        ("watersports", "Watersports"),
        ("spa", "Spa"),
        ("dining", "Dining"),
        ("adventure", "Adventure"),
        ("wellness", "Wellness"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    duration_minutes = models.IntegerField()
    capacity_per_slot = models.IntegerField()
    location = models.CharField(max_length=200)
    requirements = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict)

    class Meta:
        verbose_name = "Activity"
        verbose_name_plural = "Activities"
        indexes = [
            models.Index(fields=["category", "is_active"]),
            models.Index(fields=["is_active", "-created_at"]),
        ]

    def __str__(self) -> str:
        return str(self.name)


class ActivityImage(models.Model):
    """Images for activities."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    activity = models.ForeignKey(
        Activity, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="activities/")
    alt_text = models.CharField(max_length=200)
    is_primary = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Activity Image"
        verbose_name_plural = "Activity Images"
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return f"{self.activity.name} - Image {self.order}"


class TimeSlot(models.Model):
    """Available time slots for activities."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    activity = models.ForeignKey(
        Activity, on_delete=models.CASCADE, related_name="time_slots"
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    capacity = models.IntegerField()
    booked_count = models.IntegerField(default=0)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Time Slot"
        verbose_name_plural = "Time Slots"
        indexes = [
            models.Index(fields=["activity", "start_time"]),
            models.Index(fields=["start_time", "is_available"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(booked_count__lte=models.F("capacity")),
                name="booked_count_within_capacity",
            ),
            models.UniqueConstraint(
                fields=["activity", "start_time"],
                name="unique_activity_timeslot",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.activity.name} - {self.start_time}"


class Booking(models.Model):
    """User booking for an activity."""

    STATUS_CHOICES = [
        ("pending", "Awaiting Confirmation"),
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
        ("completed", "Completed"),
        ("no_show", "No Show"),
    ]

    BOOKING_SOURCE_CHOICES = [
        ("whatsapp", "WhatsApp"),
        ("web", "Web"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_phone = models.CharField(max_length=50, db_index=True)
    activity = models.ForeignKey(
        Activity, on_delete=models.CASCADE, related_name="bookings"
    )
    time_slot = models.ForeignKey(
        TimeSlot, on_delete=models.CASCADE, related_name="bookings"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True
    )
    participants = models.IntegerField(default=1)
    special_requests = models.TextField(blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(db_index=True)

    # Metadata
    booking_source = models.CharField(
        max_length=20, choices=BOOKING_SOURCE_CHOICES, default="whatsapp"
    )
    metadata = models.JSONField(default=dict)

    class Meta:
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"
        indexes = [
            models.Index(fields=["user_phone", "-created_at"]),
            models.Index(fields=["status", "time_slot"]),
            models.Index(fields=["expires_at", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.user_phone} - {self.activity.name} - {self.status}"


class UserPreference(models.Model):
    """User preferences for AI recommendations."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_phone = models.CharField(max_length=50, unique=True, db_index=True)
    preferred_categories = models.JSONField(default=list)
    preferred_times = models.JSONField(default=list)
    budget_range = models.JSONField(default=dict)
    interests = models.TextField(blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict)

    class Meta:
        verbose_name = "User Preference"
        verbose_name_plural = "User Preferences"

    def __str__(self) -> str:
        return f"Preferences for {self.user_phone}"
