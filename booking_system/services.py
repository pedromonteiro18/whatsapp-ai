"""Business logic for booking system."""

# pylint: disable=no-member
# Django models have 'objects' and 'DoesNotExist' added dynamically

import logging
from datetime import timedelta
from decimal import Decimal
from typing import Optional, Tuple

from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from .models import Activity, Booking, TimeSlot
from .notifications import NotificationService

logger = logging.getLogger(__name__)


class BookingService:
    """Business logic for booking operations."""

    @staticmethod
    def check_availability(
        time_slot_id: str, participants: int = 1
    ) -> Tuple[bool, int]:
        """
        Check if a time slot has availability for the requested number of participants.

        Args:
            time_slot_id: UUID of the time slot
            participants: Number of participants (default: 1)

        Returns:
            Tuple of (is_available: bool, available_capacity: int)

        Raises:
            TimeSlot.DoesNotExist: If time slot not found
        """
        try:
            time_slot = TimeSlot.objects.select_related("activity").get(id=time_slot_id)
        except TimeSlot.DoesNotExist:
            return False, 0

        # Check if time slot is in the past
        if time_slot.start_time < timezone.now():
            return False, 0

        # Check if activity is active
        if not time_slot.activity.is_active:
            return False, 0

        # Check if time slot is marked as available
        if not time_slot.is_available:
            return False, 0

        # Calculate available capacity
        available_capacity = time_slot.capacity - time_slot.booked_count

        # Check if enough capacity for participants
        is_available = available_capacity >= participants

        return is_available, available_capacity

    @staticmethod
    @transaction.atomic
    def create_booking(  # pylint: disable=too-many-arguments
        user_phone: str,
        activity_id: str,
        time_slot_id: str,
        participants: int = 1,
        special_requests: str = "",
        booking_source: str = "whatsapp",
    ) -> Booking:
        """
        Create a new booking with atomic transaction.

        Args:
            user_phone: User's phone number
            activity_id: UUID of the activity
            time_slot_id: UUID of the time slot
            participants: Number of participants (default: 1)
            special_requests: Optional special requests
            booking_source: Source of booking ('whatsapp' or 'web')

        Returns:
            Created Booking instance

        Raises:
            Activity.DoesNotExist: If activity not found
            TimeSlot.DoesNotExist: If time slot not found
            ValueError: If time slot is not available or validation fails
        """
        # Get activity and time slot with select_for_update to prevent race conditions
        try:
            activity = Activity.objects.get(id=activity_id)
        except Activity.DoesNotExist as exc:
            raise ValueError(f"Activity with id {activity_id} not found") from exc

        try:
            time_slot = TimeSlot.objects.select_for_update().get(id=time_slot_id)
        except TimeSlot.DoesNotExist as exc:
            raise ValueError(f"Time slot with id {time_slot_id} not found") from exc

        # Validate activity is active
        if not activity.is_active:
            raise ValueError("Activity is not currently active")

        # Validate time slot is in the future
        if time_slot.start_time < timezone.now():
            raise ValueError("Cannot book time slots in the past")

        # Validate time slot belongs to the activity
        if time_slot.activity_id != activity.id:
            raise ValueError("Time slot does not belong to the specified activity")

        # Check availability
        is_available, available_capacity = BookingService.check_availability(
            time_slot_id, participants
        )

        if not is_available:
            raise ValueError(
                f"Time slot not available. Only {available_capacity} spots remaining"
            )

        # Validate participants
        if participants < 1:
            raise ValueError("Number of participants must be at least 1")

        # Calculate total price
        total_price = activity.price * Decimal(participants)

        # Set expiration time (30 minutes from now for pending bookings)
        expires_at = timezone.now() + timedelta(minutes=30)

        # Create booking
        booking = Booking.objects.create(
            user_phone=user_phone,
            activity=activity,
            time_slot=time_slot,
            status="pending",
            participants=participants,
            special_requests=special_requests,
            total_price=total_price,
            expires_at=expires_at,
            booking_source=booking_source,
        )

        # Increment booked count
        time_slot.booked_count += participants
        time_slot.save(update_fields=["booked_count"])

        # Send notification (non-blocking - log failures but don't raise)
        try:
            NotificationService.send_booking_created(booking)
        except Exception as e:  # noqa: BLE001
            logger.error(
                "Failed to send booking created notification for booking %s: %s",
                booking.id,
                str(e),
            )

        return booking

    @staticmethod
    @transaction.atomic
    def confirm_booking(booking_id: str, user_phone: str) -> Booking:
        """
        Confirm a pending booking.

        Args:
            booking_id: UUID of the booking
            user_phone: User's phone number for authorization

        Returns:
            Updated Booking instance

        Raises:
            Booking.DoesNotExist: If booking not found
            ValueError: If booking cannot be confirmed (wrong user, wrong status, etc.)
        """
        try:
            booking = Booking.objects.select_for_update().get(id=booking_id)
        except Booking.DoesNotExist as exc:
            raise ValueError(f"Booking with id {booking_id} not found") from exc

        # Validate booking belongs to user
        if booking.user_phone != user_phone:
            raise ValueError("You are not authorized to confirm this booking")

        # Validate booking is in pending status
        if booking.status != "pending":
            raise ValueError(
                f"Booking cannot be confirmed. Current status: {booking.status}"
            )

        # Check if booking has expired
        if booking.expires_at < timezone.now():
            raise ValueError("Booking has expired and cannot be confirmed")

        # Update booking status
        booking.status = "confirmed"
        booking.confirmed_at = timezone.now()
        booking.save(update_fields=["status", "confirmed_at"])

        # Send notification (non-blocking - log failures but don't raise)
        try:
            NotificationService.send_booking_confirmed(booking)
        except Exception as e:  # noqa: BLE001
            logger.error(
                "Failed to send booking confirmed notification for booking %s: %s",
                booking.id,
                str(e),
            )

        return booking

    @staticmethod
    @transaction.atomic
    def cancel_booking(booking_id: str, user_phone: str, reason: str = "") -> Booking:
        """
        Cancel a booking and release the time slot capacity.

        Args:
            booking_id: UUID of the booking
            user_phone: User's phone number for authorization
            reason: Optional cancellation reason

        Returns:
            Updated Booking instance

        Raises:
            Booking.DoesNotExist: If booking not found
            ValueError: If booking cannot be cancelled
        """
        try:
            booking = (
                Booking.objects.select_for_update()
                .select_related("time_slot")
                .get(id=booking_id)
            )
        except Booking.DoesNotExist as exc:
            raise ValueError(f"Booking with id {booking_id} not found") from exc

        # Validate booking belongs to user
        if booking.user_phone != user_phone:
            raise ValueError("You are not authorized to cancel this booking")

        # Validate booking can be cancelled
        if booking.status in ["cancelled", "completed"]:
            raise ValueError(
                f"Booking cannot be cancelled. Current status: {booking.status}"
            )

        # Check cancellation deadline (24 hours before activity)
        cancellation_deadline = booking.time_slot.start_time - timedelta(hours=24)
        if timezone.now() > cancellation_deadline:
            raise ValueError(
                "Cancellation deadline has passed. "
                "Bookings must be cancelled at least 24 hours before the activity."
            )

        # Get time slot with lock
        time_slot = TimeSlot.objects.select_for_update().get(id=booking.time_slot_id)

        # Update booking status
        booking.status = "cancelled"
        booking.cancelled_at = timezone.now()
        if reason:
            booking.metadata["cancellation_reason"] = reason
        booking.save(update_fields=["status", "cancelled_at", "metadata"])

        # Decrement booked count
        time_slot.booked_count -= booking.participants
        time_slot.save(update_fields=["booked_count"])

        # Send notification (non-blocking - log failures but don't raise)
        try:
            NotificationService.send_booking_cancelled(booking, reason)
        except Exception as e:  # noqa: BLE001
            logger.error(
                "Failed to send booking cancelled notification for booking %s: %s",
                booking.id,
                str(e),
            )

        return booking

    @staticmethod
    def get_user_bookings(
        user_phone: str, status: Optional[str] = None
    ) -> "QuerySet[Booking]":
        """
        Get all bookings for a user, optionally filtered by status.

        Args:
            user_phone: User's phone number
            status: Optional status filter ('pending', 'confirmed', 'cancelled', etc.)

        Returns:
            QuerySet of Booking instances ordered by created_at descending
        """
        queryset = Booking.objects.select_related("activity", "time_slot").filter(
            user_phone=user_phone
        )

        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by("-created_at")
