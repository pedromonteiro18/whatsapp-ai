"""WhatsApp notification service for booking lifecycle events."""

import logging
from datetime import datetime
from typing import cast

from decouple import config

from backend.whatsapp.client import WhatsAppClient, WhatsAppClientError

from .models import Booking

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for sending WhatsApp notifications about booking events.

    This service handles all user-facing notifications for the booking
    lifecycle: creation, confirmation, and cancellation. It uses the
    existing WhatsAppClient for message delivery with built-in retry logic.

    All methods gracefully handle failures - notification errors are logged
    but do not raise exceptions, ensuring booking operations succeed even
    if notifications fail.
    """

    # Web app base URL for booking links
    WEB_APP_URL: str = cast(
        str, config("BOOKING_WEB_APP_URL", default="https://your-resort.com")
    )

    @staticmethod
    def _format_datetime(dt: datetime) -> str:
        """
        Format datetime in user-friendly format.

        Args:
            dt: Datetime to format

        Returns:
            Formatted string like "Monday, October 14, 2025 at 2:30 PM"
        """
        return dt.strftime("%A, %B %d, %Y at %I:%M %p")

    @staticmethod
    def _format_phone_number(phone: str) -> str:
        """
        Ensure phone number has correct WhatsApp format.

        Args:
            phone: Phone number (with or without whatsapp: prefix)

        Returns:
            Phone number with whatsapp: prefix
        """
        if not phone.startswith("whatsapp:"):
            return f"whatsapp:{phone}"
        return phone

    @staticmethod
    def send_booking_created(booking: Booking) -> bool:
        """
        Send notification when a new booking is created.

        Informs the user that their booking is pending and will expire
        in 30 minutes if not confirmed. Includes a link to confirm.

        Args:
            booking: The newly created Booking instance

        Returns:
            True if notification sent successfully, False otherwise
        """
        try:
            # Format booking details
            activity_name: str = booking.activity.name
            formatted_date: str = NotificationService._format_datetime(
                booking.time_slot.start_time
            )
            duration: int = booking.activity.duration_minutes
            participants: int = booking.participants
            total_price = booking.total_price
            booking_url: str = (
                f"{NotificationService.WEB_APP_URL}/bookings/{booking.id}"
            )

            # Compose message
            message = (
                f"🎯 *Booking Created*\n\n"
                f"Your booking is pending confirmation:\n\n"
                f"*Activity:* {activity_name}\n"
                f"*Date & Time:* {formatted_date}\n"
                f"*Duration:* {duration} minutes\n"
                f"*Participants:* {participants}\n"
                f"*Total Price:* ${total_price}\n\n"
                f"⏰ *Important:* This booking will expire in 30 minutes if not confirmed.\n\n"
                f"Confirm your booking here:\n{booking_url}"
            )

            # Send via WhatsApp
            client = WhatsAppClient()
            phone = NotificationService._format_phone_number(booking.user_phone)
            client.send_message(to=phone, message=message)

            logger.info(
                "Booking created notification sent successfully for booking %s",
                booking.id,
            )
            return True

        except WhatsAppClientError as e:
            logger.error(
                "Failed to send booking created notification for booking %s: %s",
                booking.id,
                str(e),
            )
            return False
        except Exception as e:  # noqa: BLE001
            logger.error(
                "Unexpected error sending booking created notification for booking %s: %s",
                booking.id,
                str(e),
            )
            return False

    @staticmethod
    def send_booking_confirmed(booking: Booking) -> bool:
        """
        Send notification when a booking is confirmed.

        Provides complete activity details including location, requirements,
        and cancellation policy.

        Args:
            booking: The confirmed Booking instance

        Returns:
            True if notification sent successfully, False otherwise
        """
        try:
            # Format booking details
            activity_name = booking.activity.name
            formatted_date = NotificationService._format_datetime(
                booking.time_slot.start_time
            )
            duration = booking.activity.duration_minutes
            location = booking.activity.location
            participants = booking.participants
            requirements = booking.activity.requirements

            # Build requirements section if present
            requirements_section = ""
            if requirements:
                requirements_section = f"\n*Requirements:* {requirements}\n"

            # Compose message
            message = (
                f"✅ *Booking Confirmed*\n\n"
                f"Your booking has been confirmed!\n\n"
                f"*Activity:* {activity_name}\n"
                f"*Date & Time:* {formatted_date}\n"
                f"*Duration:* {duration} minutes\n"
                f"*Location:* {location}\n"
                f"*Participants:* {participants}"
                f"{requirements_section}\n"
                f"*Cancellation Policy:* Free cancellation up to 24 hours before the activity.\n\n"
                f"See you there! 🌴"
            )

            # Send via WhatsApp
            client = WhatsAppClient()
            phone = NotificationService._format_phone_number(booking.user_phone)
            client.send_message(to=phone, message=message)

            logger.info(
                "Booking confirmed notification sent successfully for booking %s",
                booking.id,
            )
            return True

        except WhatsAppClientError as e:
            logger.error(
                "Failed to send booking confirmed notification for booking %s: %s",
                booking.id,
                str(e),
            )
            return False
        except Exception as e:  # noqa: BLE001
            logger.error(
                "Unexpected error sending booking confirmed notification for booking %s: %s",
                booking.id,
                str(e),
            )
            return False

    @staticmethod
    def send_booking_cancelled(booking: Booking, reason: str = "") -> bool:
        """
        Send notification when a booking is cancelled.

        Confirms the cancellation and optionally includes the reason.
        Encourages the user to book again.

        Args:
            booking: The cancelled Booking instance
            reason: Optional cancellation reason

        Returns:
            True if notification sent successfully, False otherwise
        """
        try:
            # Format booking details
            activity_name = booking.activity.name
            formatted_date = NotificationService._format_datetime(
                booking.time_slot.start_time
            )
            activities_url = f"{NotificationService.WEB_APP_URL}/activities"

            # Build reason section if provided
            reason_section = ""
            if reason:
                reason_section = f"\n*Reason:* {reason}\n"

            # Compose message
            message = (
                f"❌ *Booking Cancelled*\n\n"
                f"Your booking has been cancelled:\n\n"
                f"*Activity:* {activity_name}\n"
                f"*Date & Time:* {formatted_date}"
                f"{reason_section}\n"
                f"We hope to see you again soon! Browse activities:\n{activities_url}"
            )

            # Send via WhatsApp
            client = WhatsAppClient()
            phone = NotificationService._format_phone_number(booking.user_phone)
            client.send_message(to=phone, message=message)

            logger.info(
                "Booking cancelled notification sent successfully for booking %s",
                booking.id,
            )
            return True

        except WhatsAppClientError as e:
            logger.error(
                "Failed to send booking cancelled notification for booking %s: %s",
                booking.id,
                str(e),
            )
            return False
        except Exception as e:  # noqa: BLE001
            logger.error(
                "Unexpected error sending booking cancelled notification for booking %s: %s",
                booking.id,
                str(e),
            )
            return False

    @staticmethod
    def send_booking_reminder_24h(booking: Booking) -> bool:
        """
        Send 24-hour reminder notification for confirmed booking.

        Reminds the user about their upcoming activity and provides
        key details to prepare for the experience.

        Args:
            booking: The confirmed Booking instance

        Returns:
            True if notification sent successfully, False otherwise
        """
        try:
            # Format booking details
            activity_name = booking.activity.name
            formatted_date = NotificationService._format_datetime(
                booking.time_slot.start_time
            )
            duration = booking.activity.duration_minutes
            location = booking.activity.location
            participants = booking.participants
            booking_url = f"{NotificationService.WEB_APP_URL}/bookings/{booking.id}"

            # Compose message
            message = (
                f"⏰ *Reminder: Activity Tomorrow*\n\n"
                f"Your activity is coming up in 24 hours!\n\n"
                f"*Activity:* {activity_name}\n"
                f"*Date & Time:* {formatted_date}\n"
                f"*Duration:* {duration} minutes\n"
                f"*Location:* {location}\n"
                f"*Participants:* {participants}\n\n"
                f"📋 *Preparation Tips:*\n"
                f"• Arrive 15 minutes early\n"
                f"• Check weather conditions\n"
                f"• Review requirements below\n\n"
                f"View booking details:\n{booking_url}\n\n"
                f"_You can cancel free of charge until 24 hours before the activity._"
            )

            # Send via WhatsApp
            client = WhatsAppClient()
            phone = NotificationService._format_phone_number(booking.user_phone)
            client.send_message(to=phone, message=message)

            logger.info("24-hour reminder sent successfully for booking %s", booking.id)
            return True

        except WhatsAppClientError as e:
            logger.error(
                "Failed to send 24-hour reminder for booking %s: %s", booking.id, str(e)
            )
            return False
        except Exception as e:  # noqa: BLE001
            logger.error(
                "Unexpected error sending 24-hour reminder for booking %s: %s",
                booking.id,
                str(e),
            )
            return False

    @staticmethod
    def send_booking_reminder_1h(booking: Booking) -> bool:
        """
        Send 1-hour reminder notification for confirmed booking.

        Final reminder with emphasis on timing and location.
        Helps users arrive on time.

        Args:
            booking: The confirmed Booking instance

        Returns:
            True if notification sent successfully, False otherwise
        """
        try:
            # Format booking details
            activity_name = booking.activity.name
            formatted_date = NotificationService._format_datetime(
                booking.time_slot.start_time
            )
            location = booking.activity.location
            participants = booking.participants
            requirements = booking.activity.requirements

            # Build requirements section if present
            requirements_section = ""
            if requirements:
                requirements_section = f"\n\n*Don't forget:* {requirements}"

            # Compose message with urgency
            message = (
                f"🚨 *Final Reminder: 1 Hour Away!*\n\n"
                f"Your activity starts in approximately 1 hour!\n\n"
                f"*Activity:* {activity_name}\n"
                f"*Time:* {formatted_date}\n"
                f"*Location:* {location}\n"
                f"*Participants:* {participants}"
                f"{requirements_section}\n\n"
                f"🏃 *Start heading to the location now!*\n"
                f"Please arrive 10-15 minutes early.\n\n"
                f"See you soon! 🌴✨"
            )

            # Send via WhatsApp
            client = WhatsAppClient()
            phone = NotificationService._format_phone_number(booking.user_phone)
            client.send_message(to=phone, message=message)

            logger.info("1-hour reminder sent successfully for booking %s", booking.id)
            return True

        except WhatsAppClientError as e:
            logger.error(
                "Failed to send 1-hour reminder for booking %s: %s", booking.id, str(e)
            )
            return False
        except Exception as e:  # noqa: BLE001
            logger.error(
                "Unexpected error sending 1-hour reminder for booking %s: %s",
                booking.id,
                str(e),
            )
            return False
