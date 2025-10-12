"""
Celery tasks for booking system background jobs.

This module implements periodic background tasks for the booking system:
1. expire_pending_bookings: Automatically cancel expired pending bookings
2. send_reminder_24h: Send 24-hour advance reminders for confirmed bookings
3. send_reminder_1h: Send 1-hour advance reminders for confirmed bookings

All tasks are configured to run periodically via Celery Beat.
"""

import logging
from datetime import timedelta
from typing import Any

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from .models import Booking
from .notifications import NotificationService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def expire_pending_bookings(self: Any) -> dict[str, Any]:
    """
    Automatically expire pending bookings that have passed their expiration time.

    This task runs every 5 minutes to find and cancel bookings that:
    - Have status='pending'
    - Have expires_at < current time

    For each expired booking, it:
    1. Updates booking status to 'cancelled'
    2. Decrements the TimeSlot.booked_count (atomic transaction)
    3. Logs the expiration event

    Returns:
        dict: Summary with counts of expired bookings and errors

    Raises:
        Retries on database errors up to 3 times with 60s delay
    """
    try:
        now = timezone.now()
        expired_count = 0
        error_count = 0

        # Find all expired pending bookings
        expired_bookings = Booking.objects.filter(
            status="pending", expires_at__lt=now
        ).select_related("time_slot")

        logger.info(
            "Found %d expired pending bookings to process", expired_bookings.count()
        )

        # Process each expired booking in its own transaction
        for booking in expired_bookings:
            try:
                with transaction.atomic():
                    # Update booking status
                    booking.status = "cancelled"
                    booking.cancelled_at = now
                    booking.save(update_fields=["status", "cancelled_at"])

                    # Decrement time slot booked count
                    time_slot = booking.time_slot
                    time_slot.booked_count -= booking.participants
                    time_slot.save(update_fields=["booked_count"])

                    logger.info(
                        "Expired booking %s for activity %s (participants: %d)",
                        booking.id,
                        booking.activity.name,
                        booking.participants,
                    )
                    expired_count += 1

            except Exception as e:
                error_count += 1
                logger.error(
                    "Error expiring booking %s: %s", booking.id, str(e), exc_info=True
                )

        result = {
            "expired_count": expired_count,
            "error_count": error_count,
            "processed_at": now.isoformat(),
        }

        logger.info(
            "Booking expiration task completed: %d expired, %d errors",
            expired_count,
            error_count,
        )

        return result

    except Exception as e:
        logger.error(
            "Critical error in expire_pending_bookings task: %s", str(e), exc_info=True
        )
        # Retry on database connection errors or other critical failures
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=2)
def send_reminder_24h(self: Any) -> dict[str, Any]:
    """
    Send 24-hour reminder notifications for upcoming confirmed bookings.

    This task runs every hour to find and remind users about bookings that:
    - Have status='confirmed'
    - Have time_slot.start_time between 23-25 hours from now
    - Haven't been reminded yet (metadata.reminded_24h != True)

    Uses a time window to account for task execution delays and prevent
    missing reminders due to timing issues.

    Returns:
        dict: Summary with counts of sent reminders and errors

    Note:
        Uses metadata tracking for idempotency - won't send duplicate reminders
    """
    try:
        now = timezone.now()
        reminder_start = now + timedelta(hours=23)
        reminder_end = now + timedelta(hours=25)
        sent_count = 0
        error_count = 0

        # Find confirmed bookings in the 24-hour reminder window
        # that haven't been reminded yet
        bookings_to_remind = Booking.objects.filter(
            status="confirmed",
            time_slot__start_time__gte=reminder_start,
            time_slot__start_time__lte=reminder_end,
        ).select_related("activity", "time_slot")

        logger.info(
            "Found %d bookings in 24-hour reminder window", bookings_to_remind.count()
        )

        for booking in bookings_to_remind:
            # Check if already reminded (idempotency)
            if booking.metadata.get("reminded_24h"):
                logger.debug(
                    "Booking %s already has 24h reminder sent, skipping", booking.id
                )
                continue

            try:
                # Send reminder notification
                success = NotificationService.send_booking_reminder_24h(booking)

                if success:
                    # Mark as reminded in metadata
                    booking.metadata["reminded_24h"] = True
                    booking.metadata["reminded_24h_at"] = now.isoformat()
                    booking.save(update_fields=["metadata"])

                    logger.info(
                        "Sent 24h reminder for booking %s (activity: %s)",
                        booking.id,
                        booking.activity.name,
                    )
                    sent_count += 1
                else:
                    error_count += 1
                    logger.warning(
                        "Failed to send 24h reminder for booking %s", booking.id
                    )

            except Exception as e:
                error_count += 1
                logger.error(
                    "Error sending 24h reminder for booking %s: %s",
                    booking.id,
                    str(e),
                    exc_info=True,
                )

        result = {
            "sent_count": sent_count,
            "error_count": error_count,
            "processed_at": now.isoformat(),
        }

        logger.info(
            "24-hour reminder task completed: %d sent, %d errors",
            sent_count,
            error_count,
        )

        return result

    except Exception as e:
        logger.error(
            "Critical error in send_reminder_24h task: %s", str(e), exc_info=True
        )
        # Retry on database connection errors
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=2)
def send_reminder_1h(self: Any) -> dict[str, Any]:
    """
    Send 1-hour reminder notifications for upcoming confirmed bookings.

    This task runs every 15 minutes to find and remind users about bookings that:
    - Have status='confirmed'
    - Have time_slot.start_time between 45-75 minutes from now
    - Haven't been reminded yet (metadata.reminded_1h != True)

    Uses a wider time window to account for the more frequent execution
    and ensure no reminders are missed.

    Returns:
        dict: Summary with counts of sent reminders and errors

    Note:
        Uses metadata tracking for idempotency - won't send duplicate reminders
    """
    try:
        now = timezone.now()
        reminder_start = now + timedelta(minutes=45)
        reminder_end = now + timedelta(minutes=75)
        sent_count = 0
        error_count = 0

        # Find confirmed bookings in the 1-hour reminder window
        # that haven't been reminded yet
        bookings_to_remind = Booking.objects.filter(
            status="confirmed",
            time_slot__start_time__gte=reminder_start,
            time_slot__start_time__lte=reminder_end,
        ).select_related("activity", "time_slot")

        logger.info(
            "Found %d bookings in 1-hour reminder window", bookings_to_remind.count()
        )

        for booking in bookings_to_remind:
            # Check if already reminded (idempotency)
            if booking.metadata.get("reminded_1h"):
                logger.debug(
                    "Booking %s already has 1h reminder sent, skipping", booking.id
                )
                continue

            try:
                # Send reminder notification
                success = NotificationService.send_booking_reminder_1h(booking)

                if success:
                    # Mark as reminded in metadata
                    booking.metadata["reminded_1h"] = True
                    booking.metadata["reminded_1h_at"] = now.isoformat()
                    booking.save(update_fields=["metadata"])

                    logger.info(
                        "Sent 1h reminder for booking %s (activity: %s)",
                        booking.id,
                        booking.activity.name,
                    )
                    sent_count += 1
                else:
                    error_count += 1
                    logger.warning(
                        "Failed to send 1h reminder for booking %s", booking.id
                    )

            except Exception as e:
                error_count += 1
                logger.error(
                    "Error sending 1h reminder for booking %s: %s",
                    booking.id,
                    str(e),
                    exc_info=True,
                )

        result = {
            "sent_count": sent_count,
            "error_count": error_count,
            "processed_at": now.isoformat(),
        }

        logger.info(
            "1-hour reminder task completed: %d sent, %d errors",
            sent_count,
            error_count,
        )

        return result

    except Exception as e:
        logger.error(
            "Critical error in send_reminder_1h task: %s", str(e), exc_info=True
        )
        # Retry on database connection errors
        raise self.retry(exc=e)
