"""Models for the booking system."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from django.db import models

if TYPE_CHECKING:
    from django.db.models.fields.related_descriptors import RelatedManager


class Activity(models.Model):
    """Resort activity offering."""

    CATEGORY_CHOICES = [
        ("watersports", "Watersports"),
        ("spa", "Spa"),
        ("dining", "Dining"),
        ("adventure", "Adventure"),
        ("wellness", "Wellness"),
    ]

    id: UUID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name: str = models.CharField(max_length=200)
    slug: str = models.SlugField(unique=True, max_length=200)
    description: str = models.TextField()
    category: str = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    price: Decimal = models.DecimalField(max_digits=10, decimal_places=2)
    currency: str = models.CharField(max_length=3, default="USD")
    duration_minutes: int = models.IntegerField()
    capacity_per_slot: int = models.IntegerField()
    location: str = models.CharField(max_length=200)
    requirements: str = models.TextField(blank=True)
    is_active: bool = models.BooleanField(default=True)
    created_at: datetime = models.DateTimeField(auto_now_add=True)
    updated_at: datetime = models.DateTimeField(auto_now=True)
    metadata: dict = models.JSONField(default=dict)

    if TYPE_CHECKING:
        # Type hints for reverse relations
        images: "RelatedManager[ActivityImage]"
        time_slots: "RelatedManager[TimeSlot]"
        bookings: "RelatedManager[Booking]"

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

    id: UUID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    activity: Activity = models.ForeignKey(
        Activity, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="activities/")
    alt_text: str = models.CharField(max_length=200)
    is_primary: bool = models.BooleanField(default=False)
    order: int = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Activity Image"
        verbose_name_plural = "Activity Images"
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return f"{self.activity.name} - Image {self.order}"


class TimeSlot(models.Model):
    """Available time slots for activities."""

    id: UUID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    activity: Activity = models.ForeignKey(
        Activity, on_delete=models.CASCADE, related_name="time_slots"
    )
    start_time: datetime = models.DateTimeField()
    end_time: datetime = models.DateTimeField()
    capacity: int = models.IntegerField()
    booked_count: int = models.IntegerField(default=0)
    is_available: bool = models.BooleanField(default=True)
    created_at: datetime = models.DateTimeField(auto_now_add=True)

    if TYPE_CHECKING:
        # Type hints for reverse relations
        bookings: "RelatedManager[Booking]"
        # Django auto-generated _id field for ForeignKey
        activity_id: UUID

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

    id: UUID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_phone: str = models.CharField(max_length=50, db_index=True)
    activity: Activity = models.ForeignKey(
        Activity, on_delete=models.CASCADE, related_name="bookings"
    )
    time_slot: TimeSlot = models.ForeignKey(
        TimeSlot, on_delete=models.CASCADE, related_name="bookings"
    )
    status: str = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True
    )
    participants: int = models.IntegerField(default=1)
    special_requests: str = models.TextField(blank=True)
    total_price: Decimal = models.DecimalField(max_digits=10, decimal_places=2)

    # Timestamps
    created_at: datetime = models.DateTimeField(auto_now_add=True)
    confirmed_at: Optional[datetime] = models.DateTimeField(null=True, blank=True)
    cancelled_at: Optional[datetime] = models.DateTimeField(null=True, blank=True)
    expires_at: datetime = models.DateTimeField(db_index=True)

    # Metadata
    booking_source: str = models.CharField(
        max_length=20, choices=BOOKING_SOURCE_CHOICES, default="whatsapp"
    )
    metadata: dict = models.JSONField(default=dict)

    if TYPE_CHECKING:
        # Django auto-generated _id fields for ForeignKeys
        activity_id: UUID
        time_slot_id: UUID

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

    id: UUID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_phone: str = models.CharField(max_length=50, unique=True, db_index=True)
    preferred_categories: list = models.JSONField(default=list)
    preferred_times: list = models.JSONField(default=list)
    budget_range: dict = models.JSONField(default=dict)
    interests: str = models.TextField(blank=True)
    last_updated: datetime = models.DateTimeField(auto_now=True)
    metadata: dict = models.JSONField(default=dict)

    class Meta:
        verbose_name = "User Preference"
        verbose_name_plural = "User Preferences"

    def __str__(self) -> str:
        return f"Preferences for {self.user_phone}"
