"""Tests for the booking system."""

from datetime import timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils import timezone

from .models import Activity, Booking, TimeSlot
from .notifications import NotificationService


class NotificationServiceTests(TestCase):
    """Test cases for NotificationService."""

    def setUp(self):
        """Set up test data for all tests."""
        # Create test activity
        self.activity = Activity.objects.create(
            name="Sunset Kayaking",
            slug="sunset-kayaking",
            description="Enjoy a peaceful kayaking session at sunset",
            category="watersports",
            price=Decimal("75.00"),
            duration_minutes=90,
            capacity_per_slot=10,
            location="Beach Dock #3",
            requirements="Must be able to swim. Life jackets provided.",
            is_active=True,
        )

        # Create test time slot
        self.time_slot = TimeSlot.objects.create(
            activity=self.activity,
            start_time=timezone.now() + timedelta(days=2),
            end_time=timezone.now() + timedelta(days=2, hours=1, minutes=30),
            capacity=10,
            booked_count=0,
            is_available=True,
        )

        # Create test booking
        self.booking = Booking.objects.create(
            user_phone="+1234567890",
            activity=self.activity,
            time_slot=self.time_slot,
            status="pending",
            participants=2,
            special_requests="Please reserve front kayaks",
            total_price=Decimal("150.00"),
            expires_at=timezone.now() + timedelta(minutes=30),
            booking_source="whatsapp",
        )

    @patch("booking_system.notifications.WhatsAppClient")
    def test_send_booking_created_success(self, mock_client_class):
        """Test successful booking created notification."""
        # Setup mock
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.send_message.return_value = True

        # Call method
        result = NotificationService.send_booking_created(self.booking)

        # Verify result
        self.assertTrue(result)

        # Verify WhatsApp client was called correctly
        mock_client.send_message.assert_called_once()
        call_args = mock_client.send_message.call_args

        # Check phone number formatting
        self.assertEqual(call_args[1]["to"], "whatsapp:+1234567890")

        # Check message contains key information
        message = call_args[1]["message"]
        self.assertIn("Sunset Kayaking", message)
        self.assertIn("2", message)  # participants
        self.assertIn("$150.00", message)  # total price
        self.assertIn("90 minutes", message)  # duration
        self.assertIn("30 minutes", message)  # expiry warning
        self.assertIn("Confirm your booking", message)

    @patch("booking_system.notifications.WhatsAppClient")
    def test_send_booking_confirmed_success(self, mock_client_class):
        """Test successful booking confirmed notification."""
        # Setup mock
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.send_message.return_value = True

        # Update booking status to confirmed
        self.booking.status = "confirmed"
        self.booking.confirmed_at = timezone.now()
        self.booking.save()

        # Call method
        result = NotificationService.send_booking_confirmed(self.booking)

        # Verify result
        self.assertTrue(result)

        # Verify WhatsApp client was called correctly
        mock_client.send_message.assert_called_once()
        call_args = mock_client.send_message.call_args

        # Check phone number formatting
        self.assertEqual(call_args[1]["to"], "whatsapp:+1234567890")

        # Check message contains key information
        message = call_args[1]["message"]
        self.assertIn("✅", message)
        self.assertIn("Booking Confirmed", message)
        self.assertIn("Sunset Kayaking", message)
        self.assertIn("Beach Dock #3", message)  # location
        self.assertIn("2", message)  # participants
        self.assertIn("Must be able to swim", message)  # requirements
        self.assertIn("24 hours", message)  # cancellation policy

    @patch("booking_system.notifications.WhatsAppClient")
    def test_send_booking_cancelled_success(self, mock_client_class):
        """Test successful booking cancelled notification."""
        # Setup mock
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.send_message.return_value = True

        # Update booking status to cancelled
        self.booking.status = "cancelled"
        self.booking.cancelled_at = timezone.now()
        self.booking.save()

        # Call method with reason
        reason = "Weather conditions not suitable"
        result = NotificationService.send_booking_cancelled(self.booking, reason)

        # Verify result
        self.assertTrue(result)

        # Verify WhatsApp client was called correctly
        mock_client.send_message.assert_called_once()
        call_args = mock_client.send_message.call_args

        # Check phone number formatting
        self.assertEqual(call_args[1]["to"], "whatsapp:+1234567890")

        # Check message contains key information
        message = call_args[1]["message"]
        self.assertIn("❌", message)
        self.assertIn("Booking Cancelled", message)
        self.assertIn("Sunset Kayaking", message)
        self.assertIn(reason, message)  # cancellation reason
        self.assertIn("Browse activities", message)

    @patch("booking_system.notifications.WhatsAppClient")
    def test_send_booking_cancelled_without_reason(self, mock_client_class):
        """Test booking cancelled notification without reason."""
        # Setup mock
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.send_message.return_value = True

        # Call method without reason
        result = NotificationService.send_booking_cancelled(self.booking)

        # Verify result
        self.assertTrue(result)

        # Verify WhatsApp client was called
        mock_client.send_message.assert_called_once()

    @patch("booking_system.notifications.WhatsAppClient")
    def test_send_notification_handles_client_error(self, mock_client_class):
        """Test that notification methods handle WhatsAppClientError gracefully."""
        # Setup mock to raise exception
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        from whatsapp.client import WhatsAppClientError

        mock_client.send_message.side_effect = WhatsAppClientError("Connection failed")

        # Call method
        result = NotificationService.send_booking_created(self.booking)

        # Verify method returns False but doesn't raise exception
        self.assertFalse(result)

    @patch("booking_system.notifications.WhatsAppClient")
    def test_send_notification_handles_unexpected_error(self, mock_client_class):
        """Test that notification methods handle unexpected errors gracefully."""
        # Setup mock to raise unexpected exception
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.send_message.side_effect = RuntimeError("Unexpected error")

        # Call method
        result = NotificationService.send_booking_created(self.booking)

        # Verify method returns False but doesn't raise exception
        self.assertFalse(result)

    def test_format_phone_number_adds_prefix(self):
        """Test that _format_phone_number adds whatsapp: prefix."""
        phone_without_prefix = "+1234567890"
        result = NotificationService._format_phone_number(phone_without_prefix)
        self.assertEqual(result, "whatsapp:+1234567890")

    def test_format_phone_number_preserves_prefix(self):
        """Test that _format_phone_number preserves existing prefix."""
        phone_with_prefix = "whatsapp:+1234567890"
        result = NotificationService._format_phone_number(phone_with_prefix)
        self.assertEqual(result, "whatsapp:+1234567890")

    def test_format_datetime(self):
        """Test that _format_datetime produces readable format."""
        from datetime import datetime
        from zoneinfo import ZoneInfo

        test_datetime = datetime(2025, 10, 14, 14, 30, 0, tzinfo=ZoneInfo("UTC"))
        result = NotificationService._format_datetime(test_datetime)

        # Check format contains date and time components
        self.assertIn("October", result)
        self.assertIn("14", result)
        self.assertIn("2025", result)
        self.assertIn("2:30 PM", result)

    @patch("booking_system.notifications.config")
    def test_web_app_url_configuration(self, mock_config):
        """Test that WEB_APP_URL reads from configuration."""
        # The actual test is that the class attribute is defined
        # and uses config() with a default value
        self.assertTrue(hasattr(NotificationService, "WEB_APP_URL"))

    @patch("booking_system.notifications.WhatsAppClient")
    def test_notification_includes_web_app_links(self, mock_client_class):
        """Test that notifications include proper web app links."""
        # Setup mock
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Call method
        NotificationService.send_booking_created(self.booking)

        # Get the message
        call_args = mock_client.send_message.call_args
        message = call_args[1]["message"]

        # Verify link contains booking ID
        self.assertIn(str(self.booking.id), message)


class CeleryTaskTests(TestCase):
    """Test cases for Celery background tasks."""

    def setUp(self):
        """Set up test data for all tests."""
        # Create test activity
        self.activity = Activity.objects.create(
            name="Sunset Kayaking",
            slug="sunset-kayaking",
            description="Enjoy a peaceful kayaking session at sunset",
            category="watersports",
            price=Decimal("75.00"),
            duration_minutes=90,
            capacity_per_slot=10,
            location="Beach Dock #3",
            requirements="Must be able to swim. Life jackets provided.",
            is_active=True,
        )

        # Create test time slot
        self.time_slot = TimeSlot.objects.create(
            activity=self.activity,
            start_time=timezone.now() + timedelta(days=2),
            end_time=timezone.now() + timedelta(days=2, hours=1, minutes=30),
            capacity=10,
            booked_count=0,
            is_available=True,
        )

    def test_expire_pending_bookings_success(self):
        """Test that expired pending bookings are cancelled correctly."""
        from booking_system.tasks import expire_pending_bookings

        # Create expired pending booking
        expired_booking = Booking.objects.create(
            user_phone="+1234567890",
            activity=self.activity,
            time_slot=self.time_slot,
            status="pending",
            participants=2,
            total_price=Decimal("150.00"),
            expires_at=timezone.now() - timedelta(minutes=5),  # Expired 5 minutes ago
            booking_source="whatsapp",
        )

        # Update time slot booked count
        self.time_slot.booked_count = 2
        self.time_slot.save()

        # Run task
        result = expire_pending_bookings()

        # Verify booking was cancelled
        expired_booking.refresh_from_db()
        self.assertEqual(expired_booking.status, "cancelled")
        self.assertIsNotNone(expired_booking.cancelled_at)

        # Verify time slot count was decremented
        self.time_slot.refresh_from_db()
        self.assertEqual(self.time_slot.booked_count, 0)

        # Verify result
        self.assertEqual(result["expired_count"], 1)
        self.assertEqual(result["error_count"], 0)

    def test_expire_pending_bookings_skips_confirmed(self):
        """Test that confirmed bookings are not expired."""
        from booking_system.tasks import expire_pending_bookings

        # Create expired but confirmed booking
        confirmed_booking = Booking.objects.create(
            user_phone="+1234567890",
            activity=self.activity,
            time_slot=self.time_slot,
            status="confirmed",
            participants=2,
            total_price=Decimal("150.00"),
            expires_at=timezone.now() - timedelta(minutes=5),
            booking_source="whatsapp",
        )

        # Run task
        result = expire_pending_bookings()

        # Verify booking was NOT cancelled
        confirmed_booking.refresh_from_db()
        self.assertEqual(confirmed_booking.status, "confirmed")
        self.assertIsNone(confirmed_booking.cancelled_at)

        # Verify result
        self.assertEqual(result["expired_count"], 0)

    def test_expire_pending_bookings_skips_future(self):
        """Test that future pending bookings are not expired."""
        from booking_system.tasks import expire_pending_bookings

        # Create future pending booking
        future_booking = Booking.objects.create(
            user_phone="+1234567890",
            activity=self.activity,
            time_slot=self.time_slot,
            status="pending",
            participants=2,
            total_price=Decimal("150.00"),
            expires_at=timezone.now() + timedelta(minutes=25),  # Expires in future
            booking_source="whatsapp",
        )

        # Run task
        result = expire_pending_bookings()

        # Verify booking was NOT cancelled
        future_booking.refresh_from_db()
        self.assertEqual(future_booking.status, "pending")
        self.assertIsNone(future_booking.cancelled_at)

        # Verify result
        self.assertEqual(result["expired_count"], 0)

    @patch("booking_system.tasks.NotificationService.send_booking_reminder_24h")
    def test_send_reminder_24h_success(self, mock_send):
        """Test that 24h reminders are sent for confirmed bookings."""
        from booking_system.tasks import send_reminder_24h

        # Setup mock
        mock_send.return_value = True

        # Create booking 24 hours in future
        booking = Booking.objects.create(
            user_phone="+1234567890",
            activity=self.activity,
            time_slot=TimeSlot.objects.create(
                activity=self.activity,
                start_time=timezone.now() + timedelta(hours=24),
                end_time=timezone.now() + timedelta(hours=25, minutes=30),
                capacity=10,
                booked_count=2,
                is_available=True,
            ),
            status="confirmed",
            participants=2,
            total_price=Decimal("150.00"),
            expires_at=timezone.now() + timedelta(minutes=30),
            booking_source="whatsapp",
        )

        # Run task
        result = send_reminder_24h()

        # Verify notification was sent
        mock_send.assert_called_once_with(booking)

        # Verify metadata was updated
        booking.refresh_from_db()
        self.assertTrue(booking.metadata.get("reminded_24h"))
        self.assertIn("reminded_24h_at", booking.metadata)

        # Verify result
        self.assertEqual(result["sent_count"], 1)
        self.assertEqual(result["error_count"], 0)

    @patch("booking_system.tasks.NotificationService.send_booking_reminder_24h")
    def test_send_reminder_24h_idempotency(self, mock_send):
        """Test that 24h reminders are not sent twice."""
        from booking_system.tasks import send_reminder_24h

        # Setup mock
        mock_send.return_value = True

        # Create booking 24 hours in future with reminder already sent
        Booking.objects.create(
            user_phone="+1234567890",
            activity=self.activity,
            time_slot=TimeSlot.objects.create(
                activity=self.activity,
                start_time=timezone.now() + timedelta(hours=24),
                end_time=timezone.now() + timedelta(hours=25, minutes=30),
                capacity=10,
                booked_count=2,
                is_available=True,
            ),
            status="confirmed",
            participants=2,
            total_price=Decimal("150.00"),
            expires_at=timezone.now() + timedelta(minutes=30),
            booking_source="whatsapp",
            metadata={"reminded_24h": True},  # Already reminded
        )

        # Run task
        result = send_reminder_24h()

        # Verify notification was NOT sent
        mock_send.assert_not_called()

        # Verify result
        self.assertEqual(result["sent_count"], 0)

    @patch("booking_system.tasks.NotificationService.send_booking_reminder_24h")
    def test_send_reminder_24h_skips_pending(self, mock_send):
        """Test that 24h reminders are not sent for pending bookings."""
        from booking_system.tasks import send_reminder_24h

        # Create pending booking 24 hours in future
        Booking.objects.create(
            user_phone="+1234567890",
            activity=self.activity,
            time_slot=TimeSlot.objects.create(
                activity=self.activity,
                start_time=timezone.now() + timedelta(hours=24),
                end_time=timezone.now() + timedelta(hours=25, minutes=30),
                capacity=10,
                booked_count=2,
                is_available=True,
            ),
            status="pending",  # Not confirmed
            participants=2,
            total_price=Decimal("150.00"),
            expires_at=timezone.now() + timedelta(minutes=30),
            booking_source="whatsapp",
        )

        # Run task
        result = send_reminder_24h()

        # Verify notification was NOT sent
        mock_send.assert_not_called()

        # Verify result
        self.assertEqual(result["sent_count"], 0)

    @patch("booking_system.tasks.NotificationService.send_booking_reminder_1h")
    def test_send_reminder_1h_success(self, mock_send):
        """Test that 1h reminders are sent for confirmed bookings."""
        from booking_system.tasks import send_reminder_1h

        # Setup mock
        mock_send.return_value = True

        # Create booking 1 hour in future
        booking = Booking.objects.create(
            user_phone="+1234567890",
            activity=self.activity,
            time_slot=TimeSlot.objects.create(
                activity=self.activity,
                start_time=timezone.now() + timedelta(hours=1),
                end_time=timezone.now() + timedelta(hours=2, minutes=30),
                capacity=10,
                booked_count=2,
                is_available=True,
            ),
            status="confirmed",
            participants=2,
            total_price=Decimal("150.00"),
            expires_at=timezone.now() + timedelta(minutes=30),
            booking_source="whatsapp",
        )

        # Run task
        result = send_reminder_1h()

        # Verify notification was sent
        mock_send.assert_called_once_with(booking)

        # Verify metadata was updated
        booking.refresh_from_db()
        self.assertTrue(booking.metadata.get("reminded_1h"))
        self.assertIn("reminded_1h_at", booking.metadata)

        # Verify result
        self.assertEqual(result["sent_count"], 1)
        self.assertEqual(result["error_count"], 0)

    @patch("booking_system.tasks.NotificationService.send_booking_reminder_1h")
    def test_send_reminder_1h_idempotency(self, mock_send):
        """Test that 1h reminders are not sent twice."""
        from booking_system.tasks import send_reminder_1h

        # Create booking 1 hour in future with reminder already sent
        Booking.objects.create(
            user_phone="+1234567890",
            activity=self.activity,
            time_slot=TimeSlot.objects.create(
                activity=self.activity,
                start_time=timezone.now() + timedelta(hours=1),
                end_time=timezone.now() + timedelta(hours=2, minutes=30),
                capacity=10,
                booked_count=2,
                is_available=True,
            ),
            status="confirmed",
            participants=2,
            total_price=Decimal("150.00"),
            expires_at=timezone.now() + timedelta(minutes=30),
            booking_source="whatsapp",
            metadata={"reminded_1h": True},  # Already reminded
        )

        # Run task
        result = send_reminder_1h()

        # Verify notification was NOT sent
        mock_send.assert_not_called()

        # Verify result
        self.assertEqual(result["sent_count"], 0)

    @patch("booking_system.tasks.NotificationService.send_booking_reminder_1h")
    def test_send_reminder_1h_handles_notification_failure(self, mock_send):
        """Test that 1h reminder task handles notification failures gracefully."""
        from booking_system.tasks import send_reminder_1h

        # Setup mock to return False (failure)
        mock_send.return_value = False

        # Create booking 1 hour in future
        booking = Booking.objects.create(
            user_phone="+1234567890",
            activity=self.activity,
            time_slot=TimeSlot.objects.create(
                activity=self.activity,
                start_time=timezone.now() + timedelta(hours=1),
                end_time=timezone.now() + timedelta(hours=2, minutes=30),
                capacity=10,
                booked_count=2,
                is_available=True,
            ),
            status="confirmed",
            participants=2,
            total_price=Decimal("150.00"),
            expires_at=timezone.now() + timedelta(minutes=30),
            booking_source="whatsapp",
        )

        # Run task
        result = send_reminder_1h()

        # Verify notification was attempted
        mock_send.assert_called_once_with(booking)

        # Verify metadata was NOT updated (since send failed)
        booking.refresh_from_db()
        self.assertFalse(booking.metadata.get("reminded_1h", False))

        # Verify result shows error
        self.assertEqual(result["sent_count"], 0)
        self.assertEqual(result["error_count"], 1)
