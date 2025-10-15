"""DRF serializers for booking system."""

import re

from rest_framework import serializers

from .models import Activity, ActivityImage, Booking, TimeSlot, UserPreference
from .services import BookingService


class ActivityImageSerializer(serializers.ModelSerializer):
    """Serializer for ActivityImage model."""

    class Meta:
        model = ActivityImage
        fields = ["id", "image", "alt_text", "is_primary", "order"]
        read_only_fields = ["id"]


class ActivitySerializer(serializers.ModelSerializer):
    """Serializer for Activity model with nested images."""

    images = ActivityImageSerializer(many=True, read_only=True)
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "category",
            "price",
            "currency",
            "duration_minutes",
            "capacity_per_slot",
            "location",
            "requirements",
            "is_active",
            "created_at",
            "updated_at",
            "images",
            "primary_image",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_primary_image(self, obj):
        """Get the primary image URL or first image if no primary set."""
        primary = obj.images.filter(is_primary=True).first()
        if primary:
            return ActivityImageSerializer(primary).data

        first_image = obj.images.first()
        if first_image:
            return ActivityImageSerializer(first_image).data

        return None


class TimeSlotSerializer(serializers.ModelSerializer):
    """Serializer for TimeSlot model."""

    available_capacity = serializers.SerializerMethodField()
    activity_name = serializers.CharField(source="activity.name", read_only=True)

    class Meta:
        model = TimeSlot
        fields = [
            "id",
            "activity",
            "activity_name",
            "start_time",
            "end_time",
            "capacity",
            "booked_count",
            "available_capacity",
            "is_available",
            "created_at",
        ]
        read_only_fields = ["id", "booked_count", "created_at"]

    def get_available_capacity(self, obj):
        """Calculate available capacity."""
        return obj.capacity - obj.booked_count


class BookingSerializer(serializers.ModelSerializer):
    """Serializer for Booking model with nested relations."""

    activity = ActivitySerializer(read_only=True)
    time_slot = TimeSlotSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "user_phone",
            "activity",
            "time_slot",
            "status",
            "participants",
            "special_requests",
            "total_price",
            "created_at",
            "confirmed_at",
            "cancelled_at",
            "expires_at",
            "booking_source",
            "metadata",
        ]
        read_only_fields = [
            "id",
            "status",
            "total_price",
            "created_at",
            "confirmed_at",
            "cancelled_at",
            "expires_at",
        ]

    def validate_participants(self, value):
        """Validate participants is positive."""
        if value < 1:
            raise serializers.ValidationError(
                "Number of participants must be at least 1"
            )
        return value

    def validate(self, data):
        """Validate booking data."""
        # This validation is for updates, not creation
        # Creation validation is in BookingCreateSerializer
        return data


class BookingCreateSerializer(serializers.Serializer):
    """Serializer for creating new bookings."""

    activity_id = serializers.UUIDField(required=True)
    time_slot_id = serializers.UUIDField(required=True)
    participants = serializers.IntegerField(required=True, min_value=1)
    special_requests = serializers.CharField(
        required=False, allow_blank=True, max_length=1000
    )
    booking_source = serializers.ChoiceField(choices=["whatsapp", "web"], default="web")

    def validate_participants(self, value):
        """Validate participants is positive."""
        if value < 1:
            raise serializers.ValidationError(
                "Number of participants must be at least 1"
            )
        return value

    def validate(self, data):
        """Validate booking creation data."""
        time_slot_id = data.get("time_slot_id")
        participants = data.get("participants")

        # Check availability using BookingService
        is_available, available_capacity = BookingService.check_availability(
            str(time_slot_id), participants
        )

        if not is_available:
            raise serializers.ValidationError(
                {
                    "time_slot_id": (
                        f"Time slot not available. "
                        f"Only {available_capacity} spots remaining."
                    )
                }
            )

        return data

    def create(self, validated_data):
        """Create booking using BookingService."""
        user_phone = self.context["request"].user_phone
        return BookingService.create_booking(
            user_phone=user_phone,
            activity_id=str(validated_data["activity_id"]),
            time_slot_id=str(validated_data["time_slot_id"]),
            participants=validated_data["participants"],
            special_requests=validated_data.get("special_requests", ""),
            booking_source=validated_data.get("booking_source", "web"),
        )

    def update(self, instance, validated_data):
        """Update not supported for booking creation."""
        raise NotImplementedError("Bookings cannot be updated via this serializer")


class UserPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for UserPreference model."""

    class Meta:
        model = UserPreference
        fields = [
            "id",
            "user_phone",
            "preferred_categories",
            "preferred_times",
            "budget_range",
            "interests",
            "last_updated",
            "metadata",
        ]
        read_only_fields = ["id", "last_updated"]


# Authentication Serializers


class RequestOTPSerializer(serializers.Serializer):
    """Serializer for OTP request."""

    phone_number = serializers.CharField(required=True, max_length=50)

    def validate_phone_number(self, value):
        """Validate phone number format (E.164)."""
        # E.164 format: +[country code][number]
        # Example: +12345678900
        pattern = r"^\+[1-9]\d{1,14}$"

        if not re.match(pattern, value):
            raise serializers.ValidationError(
                "Phone number must be in E.164 format (e.g., +12345678900)"
            )

        return value


class VerifyOTPSerializer(serializers.Serializer):
    """Serializer for OTP verification."""

    phone_number = serializers.CharField(required=True, max_length=50)
    otp = serializers.CharField(required=True, min_length=6, max_length=6)

    def validate_phone_number(self, value):
        """Validate phone number format (E.164)."""
        pattern = r"^\+[1-9]\d{1,14}$"

        if not re.match(pattern, value):
            raise serializers.ValidationError(
                "Phone number must be in E.164 format (e.g., +12345678900)"
            )

        return value

    def validate_otp(self, value):
        """Validate OTP is 6 digits."""
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain only digits")

        return value


class RecommendationSerializer(serializers.Serializer):
    """Serializer for AI-powered activity recommendations."""

    activity = ActivitySerializer(read_only=True)
    reasoning = serializers.CharField(
        read_only=True, help_text="AI-generated explanation for this recommendation"
    )
    score = serializers.IntegerField(
        read_only=True,
        min_value=0,
        max_value=100,
        help_text="Confidence score (0-100) for this recommendation",
    )
